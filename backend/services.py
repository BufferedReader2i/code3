# -*- coding: utf-8 -*-
"""
推荐服务：仅做推理。模型在外用 mind_neural_recommender.py 训练并保存，此处只加载 checkpoint + 从 MySQL 读数据。
"""

import os
import json
import math
import time
import torch
import random
from collections import Counter, defaultdict

from backend.db import get_connection

# 模型与资源路径（训练在项目根目录单独跑）
DATA_DIR = os.environ.get("MIND_DATA_DIR", "datal")
ENTITY_VEC = os.path.join(DATA_DIR, "entity_embedding.vec")
REC_CKPT = "mind_recommender.pt"
REC_OLD_CKPT = "recommender_model.pth"
USE_MIND = os.path.isfile(REC_CKPT)
MAX_HISTORY = 50  # 与 mind 模型一致，用于后端合并历史

if USE_MIND:
    from mind_neural_recommender import MindRecommenderSystem
else:
    from recommender_model import NewsRecommenderSystem
    from text_classifier import TextCNN


class RecommendationService:
    def __init__(self):
        self.news_info = {}
        self.news_list = []
        self.session_clicks = defaultdict(list)
        self._use_distilbert = False
        self._clf_tokenizer = None
        self._clf_model = None
        self._clf_id2label = None
        self._clf_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        conn = get_connection()
        use_db = conn is not None

        if USE_MIND:
            self.rec = MindRecommenderSystem()
            self.rec.load_entity_embeddings(ENTITY_VEC)
            self.rec.load(REC_CKPT)
            if use_db:
                self._load_user_history_from_db(conn)
            if use_db:
                self._load_news_from_db(conn)
            else:
                self._news_info_from_rec()
            self.news_list = list(self.rec.news_data.keys())[:2000] if not self.news_list else [n for n in self.news_list if n in self.rec.news_data][:2000]
            self._init_classifier_distilbert()
        else:
            self.rec = NewsRecommenderSystem()
            self.rec.load_entity_embeddings(ENTITY_VEC)
            news_tsv = os.path.join(DATA_DIR, "news.tsv")
            beh_tsv = os.path.join(DATA_DIR, "behaviors.tsv")
            if os.path.isfile(news_tsv) and os.path.isfile(beh_tsv):
                self.rec.load_data(news_tsv, beh_tsv)
            self.rec.load_model(REC_OLD_CKPT)
            if use_db:
                self._load_news_from_db(conn)
                self._load_user_history_from_db_old(conn)
            else:
                self._news_info_from_rec_old()
            self.news_list = list(self.rec.news_data.keys())[:1000] if not self.news_list else [n for n in self.news_list if n in self.rec.news_data][:1000]
            self._init_classifier_distilbert()
            if not self._use_distilbert:
                ckpt = torch.load("textcnn_model.pth", map_location="cpu", weights_only=False)
                self.classifier_label_encoder = ckpt["label_encoder"]
                self.classifier = self.rec.model.news_encoder.textcnn
                self.classifier.eval()
        if conn:
            conn.close()
        if USE_MIND and self.news_list:
            self._build_category_index()
        if self.news_list:
            self._build_global_dist()

    def _build_category_index(self):
        """按类别建索引，便于按用户兴趣拉取候选（保证 autos 等兴趣类能进候选集）。"""
        self._category_to_ids = defaultdict(list)
        for nid in self.news_list:
            if nid not in self.rec.news_data:
                continue
            cat = self.news_info.get(nid, {}).get("category") or self.rec.news_data[nid].get("category", "N/A")
            self._category_to_ids[cat].append(nid)

    def _build_global_dist(self):
        """全局类别/子类分布，用于相对兴趣与平滑。"""
        cat_cnt, subcat_cnt = Counter(), Counter()
        for nid in self.news_list:
            info = self.news_info.get(nid) or self.rec.news_data.get(nid, {})
            c = info.get("category", "N/A")
            s = info.get("subcategory", "N/A") or "N/A"
            cat_cnt[c] += 1
            subcat_cnt[s] += 1
        total_c, total_s = max(1, sum(cat_cnt.values())), max(1, sum(subcat_cnt.values()))
        self._global_cat_dist = {k: v / total_c for k, v in cat_cnt.items()}
        self._global_subcat_dist = {k: v / total_s for k, v in subcat_cnt.items()}

    def _get_ordered_history(self, user_id):
        """统一返回有序历史：从旧到新，用于按位置做时间衰减。"""
        if USE_MIND:
            return self._get_combined_history(user_id)
        hist = list(self.rec.user_history.get(user_id, []))
        for nid in self.session_clicks.get(user_id, []):
            if nid not in hist:
                hist.append(nid)
        return hist[-MAX_HISTORY:] if len(hist) > MAX_HISTORY else hist

    def _get_user_interest_categories(self, user_id, top_k=5):
        """从合并历史中统计用户兴趣类别，返回 [(category, count), ...] 按阅读数降序。"""
        combined = self._get_combined_history(user_id)
        if not combined:
            return []
        cat_counter = Counter()
        for nid in combined:
            if nid in self.rec.news_data:
                cat = self.news_info.get(nid, {}).get("category") or self.rec.news_data[nid].get("category", "N/A")
                cat_counter[cat] += 1
        return cat_counter.most_common(top_k)

    def _get_same_category_news(self, category, exclude_ids, count=3):
        """从某类别中取最多 count 条，排除 exclude_ids，随机选取。"""
        if not category or not getattr(self, "_category_to_ids", None):
            return []
        exclude_ids = set(exclude_ids or [])
        pool = [nid for nid in self._category_to_ids.get(category, []) if nid in self.rec.news_data and nid not in exclude_ids]
        return random.sample(pool, min(count, len(pool))) if pool else []

    def _get_candidates_for_user(self, user_id, exclude_ids=None, max_candidates=500, per_category=80, per_category_strong=100):
        """按用户兴趣类别构建候选集；画像中强兴趣或相对兴趣>1 的类多拉一些候选。"""
        exclude_ids = set(exclude_ids or [])
        pool = set(n for n in self.news_list if n in self.rec.news_data and n not in exclude_ids)
        if not pool:
            return []
        category_index = getattr(self, "_category_to_ids", None) or defaultdict(list)
        profile = self.get_user_profile(user_id)
        cat_per = {}
        for c in profile.get("categories", []):
            name = c.get("name")
            if not name:
                continue
            if c.get("strength") == "strong" or (c.get("relative") and c["relative"] > 1):
                cat_per[name] = per_category_strong
            else:
                cat_per[name] = per_category
        interest_cats = self._get_user_interest_categories(user_id, top_k=5)
        candidates = []
        used = set()
        for cat, _ in interest_cats:
            cap = cat_per.get(cat, per_category)
            added = 0
            for nid in category_index.get(cat, []):
                if nid in pool and nid not in used and added < cap and len(candidates) < max_candidates:
                    candidates.append(nid)
                    used.add(nid)
                    added += 1
            if len(candidates) >= max_candidates:
                break
        for nid in self.news_list:
            if len(candidates) >= max_candidates:
                break
            if nid in pool and nid not in used:
                candidates.append(nid)
                used.add(nid)
        return candidates[:max_candidates]

    def _load_news_from_db(self, conn):
        with conn.cursor() as cur:
            cur.execute("SELECT news_id, category, subcategory, title, abstract FROM news")
            for row in cur.fetchall():
                nid = row["news_id"]
                self.news_info[nid] = {
                    "category": row["category"] or "N/A",
                    "subcategory": (row.get("subcategory") or "").strip() or "N/A",
                    "title": (row["title"] or "").strip() or nid,
                    "abstract": (row["abstract"] or "").strip(),
                }
                self.news_list.append(nid)

    def _news_info_from_rec(self):
        for nid, d in self.rec.news_data.items():
            title = d.get("title_words") or []
            title_str = " ".join(title) if isinstance(title, list) else str(title)
            self.news_info[nid] = {
                "category": d.get("category", "N/A"),
                "subcategory": d.get("subcategory", "N/A"),
                "title": title_str or nid,
                "abstract": "",
            }
            self.news_list.append(nid)

    def _load_user_history_from_db(self, conn):
        with conn.cursor() as cur:
            cur.execute("SELECT user_id, news_ids FROM user_history")
            for row in cur.fetchall():
                uid = row["user_id"]
                raw = row["news_ids"]
                ids = raw if isinstance(raw, list) else json.loads(raw or "[]")
                hist = [nid for nid in ids if nid in self.rec.news_data]
                if hist:
                    self.rec.user_history[uid] = [(hist, [])]

    def _get_combined_history(self, user_id):
        """后端合并：DB 历史 + 本次会话点击，去重保序，取最后 MAX_HISTORY 条。"""
        history_ids = []
        if user_id in self.rec.user_history and self.rec.user_history[user_id]:
            for hist_ids, _ in self.rec.user_history[user_id]:
                history_ids.extend(hist_ids)
        history_ids.extend(self.session_clicks.get(user_id, []))
        seen = set()
        unique = [x for x in reversed(history_ids) if x not in seen and not seen.add(x)][-MAX_HISTORY:]
        # 不过滤，保留所有新闻ID（包括不在 rec.news_data 中的搜索结果）
        return list(reversed(unique))

    def _recommend_with_combined_history(self, user_id, candidates, top_n=10, return_scores=False):
        """用合并后的历史调用模型推荐。return_scores=True 时返回 [(id, score), ...]，便于画像加分重排。"""
        candidates = [n for n in candidates if n in self.rec.news_data][:500]
        if not candidates:
            return [] if not return_scores else []
        combined = self._get_combined_history(user_id)
        if not combined:
            out = candidates[:top_n]
            return out if not return_scores else [(nid, 0.0) for nid in out]
        old = self.rec.user_history.get(user_id)
        try:
            self.rec.user_history[user_id] = [(combined, [])]
            result = self.rec.recommend(user_id, candidates, top_n=top_n, return_scores=return_scores)
            return result
        finally:
            if old is not None:
                self.rec.user_history[user_id] = old
            else:
                self.rec.user_history.pop(user_id, None)

    def _apply_profile_boost(self, user_id, id_score_list, boost_strong=0.15, boost_relative=0.05):
        """用用户画像对模型分加分后重排：强兴趣类别/子类加分，相对兴趣>1 再加分。"""
        if not id_score_list or not USE_MIND:
            return id_score_list
        profile = self.get_user_profile(user_id)
        cat_map = {c["name"]: c for c in profile.get("categories", [])}
        subcat_map = {s["name"]: s for s in profile.get("subcategories", [])}
        boosted = []
        for nid, score in id_score_list:
            info = self.news_info.get(nid) or self.rec.news_data.get(nid, {})
            c = info.get("category", "N/A")
            s = info.get("subcategory", "N/A") or "N/A"
            add = 0.0
            if c in cat_map:
                x = cat_map[c]
                if x.get("strength") == "strong":
                    add += boost_strong * (x.get("score") or 0)
                if x.get("relative") and x["relative"] > 1:
                    add += boost_relative * min(float(x["relative"]) - 1, 1.0)
            if s in subcat_map:
                x = subcat_map[s]
                if x.get("strength") == "strong":
                    add += 0.5 * boost_strong * (x.get("score") or 0)
            boosted.append((nid, float(score) + add))
        boosted.sort(key=lambda t: -t[1])
        return boosted

    def _load_user_history_from_db_old(self, conn):
        with conn.cursor() as cur:
            cur.execute("SELECT user_id, news_ids FROM user_history")
            for row in cur.fetchall():
                uid = row["user_id"]
                raw = row["news_ids"]
                ids = raw if isinstance(raw, list) else json.loads(raw or "[]")
                hist = [nid for nid in ids if nid in self.rec.news_data]
                if hist:
                    self.rec.user_history[uid] = hist

    def _news_info_from_rec_old(self):
        for nid, d in self.rec.news_data.items():
            self.news_info[nid] = {
                "category": d.get("category", "N/A"),
                "subcategory": d.get("subcategory", "N/A"),
                "title": d.get("text", nid)[:200],
                "abstract": "",
            }
            self.news_list.append(nid)

    def _init_classifier_distilbert(self):
        if not os.path.isfile("distilbert_news.pth"):
            return
        try:
            bundle = torch.load("distilbert_news.pth", map_location=self._clf_device, weights_only=False)
        except Exception:
            return
        try:
            from transformers import AutoConfig, AutoModelForSequenceClassification, AutoTokenizer
            tokenizer_dir = bundle.get("tokenizer_path") or "distilbert_tokenizer"
            if not os.path.isdir(tokenizer_dir):
                return
            self._clf_tokenizer = AutoTokenizer.from_pretrained(tokenizer_dir, local_files_only=True)
            num_classes = int(bundle.get("num_classes", 18))
            config = AutoConfig.from_pretrained(tokenizer_dir, local_files_only=True, num_labels=num_classes)
            self._clf_model = AutoModelForSequenceClassification.from_config(config)
            self._clf_model.load_state_dict(bundle["model"], strict=True)
            self._clf_model.to(self._clf_device).eval()
            # 优先用训练时保存的 label_classes（类别文字），否则 id2label，否则用数字
            label_classes = bundle.get("label_classes")
            if label_classes is not None:
                self._clf_id2label = {i: label_classes[i] for i in range(len(label_classes))}
            else:
                self._clf_id2label = bundle.get("id2label") or {i: str(i) for i in range(num_classes)}
            self._use_distilbert = True
        except Exception:
            pass

    def get_user_profile(self, user_id, recency_decay=0.85, smooth_threshold=3.0):
        """
        复杂用户画像：仅用历史顺序（无时间戳），不做实体。
        - 按位置时间衰减：越靠后（越新）权重越大，weight_i = decay^(L-1-i)。
        - 类别 + 子类两层；分数平滑（样本少时向全局先验靠拢）；相对兴趣（相对全局）；兴趣强度。
        - dislike 事件给予负权重，not_interested 事件给予更强的负权重。
        """
        ordered = self._get_ordered_history(user_id)
        ordered = [nid for nid in ordered if nid in self.rec.news_data]
        total = len(ordered)
        if total == 0:
            return {"user_id": user_id, "categories": [], "subcategories": [], "history_count": 0}

        L = len(ordered)
        weights = [recency_decay ** (L - 1 - i) for i in range(L)]
        weight_sum = sum(weights)

        cat_weighted = defaultdict(float)
        subcat_weighted = defaultdict(float)
        dislike_news = self._get_dislike_news(user_id)
        not_interested_news = self._get_not_interested_news(user_id)
        liked_news = self._get_liked_news(user_id)
        
        for nid, w in zip(ordered, weights):
            info = self.news_info.get(nid) or self.rec.news_data.get(nid, {})
            c = info.get("category", "N/A")
            s = info.get("subcategory", "N/A") or "N/A"
            liked_news = self._get_liked_news(user_id)
            if nid in liked_news:
                w *= 0.5
            elif nid in not_interested_news:
                w *= -0.5
            elif nid in dislike_news:
                w *= -0.2
            cat_weighted[c] += w
            subcat_weighted[s] += w

        global_cat = getattr(self, "_global_cat_dist", {}) or {}
        global_subcat = getattr(self, "_global_subcat_dist", {}) or {}
        alpha = 0.5 if weight_sum < 2 else (0.2 if weight_sum < smooth_threshold else 0.0)

        def _normalize_and_enrich(weighted, global_dist, top_n=15):
            raw_sum = max(1e-9, sum(weighted.values()))
            scored = []
            for name, w in sorted(weighted.items(), key=lambda x: -x[1])[:top_n]:
                raw = w / raw_sum
                smooth = (1 - alpha) * raw + alpha * global_dist.get(name, 0) if global_dist else raw
                smooth = round(smooth, 4)
                rel = round(raw / global_dist[name], 2) if global_dist.get(name, 0) > 0 else None
                strength = "strong" if w >= 1.5 and smooth >= 0.1 else "weak"
                scored.append({"name": name, "score": smooth, "relative": rel, "strength": strength})
            return scored

        categories = _normalize_and_enrich(cat_weighted, global_cat)
        subcategories = _normalize_and_enrich(subcat_weighted, global_subcat)

        return {
            "user_id": user_id,
            "categories": categories,
            "subcategories": subcategories,
            "history_count": total,
        }

    def _get_dislike_news(self, user_id):
        """获取用户 dislike 的新闻 ID 集合"""
        conn = get_connection()
        if not conn:
            return set()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT news_id FROM user_events WHERE user_id=%s AND event_type='dislike'",
                    (user_id,)
                )
                return {r["news_id"] for r in (cur.fetchall() or [])}
        finally:
            conn.close()

    def _get_liked_news(self, user_id):
        """获取用户 like 的新闻 ID 集合"""
        conn = get_connection()
        if not conn:
            return set()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT news_id FROM user_events WHERE user_id=%s AND event_type='like'",
                    (user_id,)
                )
                return {r["news_id"] for r in (cur.fetchall() or [])}
        finally:
            conn.close()

    def _get_not_interested_news(self, user_id):
        """获取用户 not_interested 的新闻 ID 集合"""
        conn = get_connection()
        if not conn:
            return set()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT news_id FROM user_events WHERE user_id=%s AND event_type='not_interested'",
                    (user_id,)
                )
                return {r["news_id"] for r in (cur.fetchall() or [])}
        finally:
            conn.close()

    def get_user_favorites(self, user_id, limit=100):
        """获取用户收藏的新闻列表"""
        conn = get_connection()
        if not conn:
            return []
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT e.news_id, n.title, n.abstract, n.category, n.subcategory
                    FROM user_events e
                    LEFT JOIN news n ON n.news_id = e.news_id
                    WHERE e.user_id=%s AND e.event_type='favorite'
                    GROUP BY e.news_id, n.title, n.abstract, n.category, n.subcategory
                    ORDER BY MAX(e.ts) DESC
                    LIMIT %s
                    """,
                    (user_id, int(limit))
                )
                rows = cur.fetchall() or []
            out = []
            for r in rows:
                out.append({
                    "id": r["news_id"],
                    "title": (r.get("title") or "").strip() or r["news_id"],
                    "abstract": (r.get("abstract") or "").strip(),
                    "category": r.get("category") or "N/A",
                    "subcategory": (r.get("subcategory") or "").strip() or "N/A",
                })
            return out
        finally:
            conn.close()

    def get_example_users(self):
        conn = get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT user_id FROM user_history ORDER BY user_id LIMIT 10")
                    out = [r["user_id"] for r in cur.fetchall()]
                if out:
                    return out
            finally:
                conn.close()
        hardcoded = ["U87243", "U598644", "U532401"]
        users = list(getattr(self.rec, "user_history", {}).keys())
        return list(dict.fromkeys(hardcoded + users))[:10]

    def _build_final_10(self, boosted, latest_news_id=None, latest_category=None):
        """最终 10 条 = 7 条来自推荐流程 + 3 条与最近一次访问同类别；不足则用推荐池补足。"""
        rec_pool = [nid for nid, _ in boosted][:30]
        rec_7 = random.sample(rec_pool, min(7, len(rec_pool)))
        exclude = set(rec_7)
        if latest_news_id:
            exclude.add(latest_news_id)
        if latest_category is None and latest_news_id:
            latest_category = self.news_info.get(latest_news_id, {}).get("category") or self.rec.news_data.get(latest_news_id, {}).get("category", "N/A")
        same_cat_3 = self._get_same_category_news(latest_category or "", exclude, 3) if latest_category else []
        final_ids = rec_7 + same_cat_3
        if len(final_ids) < 10:
            extra = [nid for nid in rec_pool if nid not in final_ids][: 10 - len(final_ids)]
            final_ids = final_ids + extra
        final_ids = final_ids[:10]
        random.shuffle(final_ids)
        return final_ids

    def get_initial_recommendations(self, user_id):
        if USE_MIND:
            candidates = self._get_candidates_for_user(user_id)
            id_scores = self._recommend_with_combined_history(user_id, candidates, top_n=500, return_scores=True)
            boosted = self._apply_profile_boost(user_id, id_scores)
            combined = self._get_combined_history(user_id)
            latest_id = combined[-1] if combined else None
            final_ids = self._build_final_10(boosted, latest_news_id=latest_id)
            return [
                {"id": nid, "title": self.news_info.get(nid, {}).get("title", "N/A"), "category": self.news_info.get(nid, {}).get("category", "N/A"), "abstract": self.news_info.get(nid, {}).get("abstract", "")}
                for nid in final_ids
            ]
        if user_id not in self.rec.user_history:
            return []
        history = self.rec.user_history[user_id][-20:]
        candidates = [n for n in self.news_list if n in self.rec.news_data]
        hist_texts = self.rec._encode_texts([self.rec.news_data[h]["text"] for h in history])
        hist_ids = torch.tensor([self.rec.news_data[h]["idx"] for h in history])
        hist_entities = self.rec._get_entity_embeds([self.rec.news_data[h]["entities"] for h in history])
        cand_texts = self.rec._encode_texts([self.rec.news_data[c]["text"] for c in candidates])
        cand_ids = torch.tensor([self.rec.news_data[c]["idx"] for c in candidates])
        cand_entities = self.rec._get_entity_embeds([self.rec.news_data[c]["entities"] for c in candidates])
        with torch.no_grad():
            scores = self.rec.model(hist_texts, hist_ids, hist_entities, cand_texts, cand_ids, cand_entities)
        ranked = sorted(zip(candidates, scores.tolist()), key=lambda x: x[1], reverse=True)[:30]
        rec_ids = [nid for nid, _ in ranked]
        rec_ids = random.sample(rec_ids, min(10, len(rec_ids)))
        return [
            {"id": nid, "title": self.news_info.get(nid, {}).get("title", "N/A"), "category": self.news_info.get(nid, {}).get("category", "N/A"), "abstract": self.news_info.get(nid, {}).get("abstract", "N/A")}
            for nid in rec_ids
        ]

    def classify_text(self, text):
        if self._use_distilbert and self._clf_tokenizer and self._clf_model:
            text = (text or "").strip()
            if not text:
                return "unknown", 0.0, {}
            enc = self._clf_tokenizer(text, truncation=True, padding="max_length", max_length=128, return_tensors="pt")
            enc = {k: v.to(self._clf_device) for k, v in enc.items()}
            with torch.no_grad():
                logits = self._clf_model(**enc).logits[0]
            probs = torch.softmax(logits, dim=0).cpu().numpy()
            pred_idx = int(logits.argmax().item())
            pred_label = self._clf_id2label.get(pred_idx, str(pred_idx))
            all_scores = {self._clf_id2label.get(i, str(i)): float(probs[i]) for i in range(len(probs))}
            return pred_label, float(probs[pred_idx]), all_scores
        if not USE_MIND and hasattr(self, "classifier"):
            tokens = text.lower().split()[:50]
            indices = [self.rec.vocab.get(w, 0) for w in tokens] + [0] * (50 - len(tokens))
            text_tensor = torch.tensor([indices])
            with torch.no_grad():
                logits = self.classifier(text_tensor)
                probs = torch.softmax(logits, dim=1)[0]
            pred_idx = torch.argmax(probs).item()
            pred_category = self.classifier_label_encoder.classes_[pred_idx]
            confidence = float(probs[pred_idx])
            all_scores = {self.classifier_label_encoder.classes_[i]: float(probs[i]) for i in range(len(self.classifier_label_encoder.classes_))}
            return pred_category, confidence, all_scores
        return "unknown", 0.0, {}

    def _persist_click_to_db(self, user_id, news_id):
        """将本次点击追加到 user_history 表该用户的 news_ids 列表末尾。"""
        conn = get_connection()
        if not conn:
            return
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE user_history SET news_ids = JSON_ARRAY_APPEND(news_ids, '$', %s) WHERE user_id = %s", (news_id, user_id))
                if cur.rowcount == 0:
                    cur.execute("INSERT INTO user_history (user_id, news_ids) VALUES (%s, %s)", (user_id, json.dumps([news_id])))
                conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

    def _persist_event_to_db(self, user_id, news_id, event_type, ts_ms=None, dwell_ms=0, extra=None):
        """写入 user_events 表。成功返回 True，失败返回 False。"""
        conn = get_connection()
        if not conn:
            return False
        try:
            ts_ms = int(ts_ms) if ts_ms is not None else int(time.time() * 1000)
            extra_json = json.dumps(extra or {}, ensure_ascii=False)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO user_events (user_id, news_id, event_type, ts, dwell_ms, extra_json)
                    VALUES (%s,%s,%s,%s,%s,%s)
                    """,
                    (user_id, news_id, str(event_type), ts_ms, int(dwell_ms or 0), extra_json),
                )
                conn.commit()
            return True
        except Exception:
            return False
        finally:
            conn.close()

    def get_user_events(self, user_id, limit=200):
        """返回事件列表（最新在前）。DB 不可用时返回空。"""
        conn = get_connection()
        if not conn:
            return []
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, user_id, news_id, event_type, ts, dwell_ms, extra_json
                    FROM user_events
                    WHERE user_id=%s
                    ORDER BY ts DESC, id DESC
                    LIMIT %s
                    """,
                    (user_id, int(limit)),
                )
                rows = cur.fetchall() or []
            out = []
            for r in rows:
                extra = {}
                try:
                    raw = r.get("extra_json")
                    extra = raw if isinstance(raw, dict) else json.loads(raw or "{}")
                except Exception:
                    extra = {}
                out.append(
                    {
                        "id": int(r["id"]),
                        "user_id": r["user_id"],
                        "news_id": r["news_id"],
                        "event_type": r["event_type"],
                        "ts": int(r["ts"]),
                        "dwell_ms": int(r.get("dwell_ms") or 0),
                        "extra": extra,
                    }
                )
            return out
        except Exception:
            return []
        finally:
            conn.close()

    def record_event(self, user_id, news_id, event_type, ts=None, dwell_ms=0, extra=None):
        """对外统一入口：记录事件，并对部分事件做兼容写入/副作用。返回是否成功写入 user_events。"""
        if event_type == "click":
            self.session_clicks[user_id].append(news_id)
            if USE_MIND:
                self._persist_click_to_db(user_id, news_id)
            return self._persist_event_to_db(user_id, news_id, "click", ts_ms=ts, dwell_ms=dwell_ms, extra=extra)
        if event_type in ("like", "dislike", "not_interested", "favorite", "unfavorite", "dwell"):
            return self._persist_event_to_db(user_id, news_id, event_type, ts_ms=ts, dwell_ms=dwell_ms, extra=extra)
        return self._persist_event_to_db(user_id, news_id, str(event_type), ts_ms=ts, dwell_ms=dwell_ms, extra=extra)

    def click_news(self, user_id, news_id):
        # click 事件：双写到 user_events（统计/画像/聚类复用）
        self.record_event(user_id, news_id, "click")
        self._persist_click_to_db(user_id, news_id)
        if USE_MIND:
            clicked_info = self.news_info.get(news_id, {})
            session_clicked = set(self.session_clicks.get(user_id, []))
            candidates = self._get_candidates_for_user(user_id, exclude_ids=session_clicked)
            id_scores = self._recommend_with_combined_history(user_id, candidates, top_n=500, return_scores=True)
            boosted = self._apply_profile_boost(user_id, id_scores)
            latest_cat = clicked_info.get("category", "N/A")
            final_ids = self._build_final_10(boosted, latest_news_id=news_id, latest_category=latest_cat)
            recommendations = [
                {"id": nid, "title": self.news_info.get(nid, {}).get("title", "N/A"), "category": self.news_info.get(nid, {}).get("category", "N/A"), "abstract": self.news_info.get(nid, {}).get("abstract", "")}
                for nid in final_ids
            ]
            return clicked_info, recommendations
        if user_id not in self.rec.user_history:
            return None, []
        history = self.rec.user_history[user_id][-20:]
        candidates = [n for n in self.news_list if n in self.rec.news_data]
        hist_texts = self.rec._encode_texts([self.rec.news_data[h]["text"] for h in history])
        hist_ids = torch.tensor([self.rec.news_data[h]["idx"] for h in history])
        hist_entities = self.rec._get_entity_embeds([self.rec.news_data[h]["entities"] for h in history])
        cand_texts = self.rec._encode_texts([self.rec.news_data[c]["text"] for c in candidates])
        cand_ids = torch.tensor([self.rec.news_data[c]["idx"] for c in candidates])
        cand_entities = self.rec._get_entity_embeds([self.rec.news_data[c]["entities"] for c in candidates])
        with torch.no_grad():
            scores = self.rec.model(hist_texts, hist_ids, hist_entities, cand_texts, cand_ids, cand_entities)
        ranked = sorted(zip(candidates, scores.tolist()), key=lambda x: x[1], reverse=True)[:100]
        clicked_info = self.news_info.get(news_id, {})
        self.rec.update_user_vector(user_id, news_id)
        self.rec.user_history[user_id].append(news_id)
        updated_history = self.rec.user_history[user_id][-20:]
        updated_hist_texts = self.rec._encode_texts([self.rec.news_data[h]["text"] for h in updated_history])
        updated_hist_ids = torch.tensor([self.rec.news_data[h]["idx"] for h in updated_history])
        updated_hist_entities = self.rec._get_entity_embeds([self.rec.news_data[h]["entities"] for h in updated_history])
        candidate_set = [nid for nid, _ in ranked]
        cand_texts_f = self.rec._encode_texts([self.rec.news_data[c]["text"] for c in candidate_set])
        cand_ids_f = torch.tensor([self.rec.news_data[c]["idx"] for c in candidate_set])
        cand_entities_f = self.rec._get_entity_embeds([self.rec.news_data[c]["entities"] for c in candidate_set])
        with torch.no_grad():
            scores_f = self.rec.model(updated_hist_texts, updated_hist_ids, updated_hist_entities, cand_texts_f, cand_ids_f, cand_entities_f)
        final_ranked = sorted(zip(candidate_set, scores_f.tolist()), key=lambda x: x[1], reverse=True)[:10]
        return clicked_info, [
            {"id": nid, "title": self.news_info.get(nid, {}).get("title", "N/A"), "category": self.news_info.get(nid, {}).get("category", "N/A"), "abstract": self.news_info.get(nid, {}).get("abstract", "N/A")}
            for nid, _ in final_ranked
        ]

    def get_user_history(self, user_id):
        if USE_MIND:
            combined = self._get_combined_history(user_id)
            return list(reversed(combined))[-20:]
        return self.rec.user_history.get(user_id, [])[-20:]

    def get_user_history_items(self, user_id, limit=100):
        """返回历史浏览列表，每条为 {id, title, category, abstract}，按时间倒序（最新在前）。"""
        ids = self.get_user_history(user_id)
        ids = list(reversed(ids))[:limit]
        out = []
        # 收集需要从数据库查询的新闻ID
        missing_ids = []
        results_map = {}
        for nid in ids:
            info = self.news_info.get(nid) or self.rec.news_data.get(nid, {})
            if info:
                title = info.get("title") or info.get("text") or nid
                if isinstance(title, list):
                    title = " ".join(title) if title else nid
                results_map[nid] = {
                    "id": nid,
                    "title": title[:500] if isinstance(title, str) else str(title)[:500],
                    "category": info.get("category", "N/A"),
                    "abstract": info.get("abstract", "") or "",
                }
            else:
                missing_ids.append(nid)
        # 从数据库批量查询缺失的新闻信息
        if missing_ids:
            conn = get_connection()
            if conn:
                try:
                    with conn.cursor() as cur:
                        placeholders = ",".join(["%s"] * len(missing_ids))
                        cur.execute(
                            f"SELECT news_id, title, abstract, category, subcategory FROM news WHERE news_id IN ({placeholders})",
                            tuple(missing_ids)
                        )
                        rows = cur.fetchall() or []
                        for r in rows:
                            results_map[r["news_id"]] = {
                                "id": r["news_id"],
                                "title": (r.get("title") or r["news_id"])[:500],
                                "category": r.get("category") or "N/A",
                                "abstract": (r.get("abstract") or "")[:500],
                            }
                finally:
                    conn.close()
        # 对于仍然找不到的新闻，使用ID作为占位
        for nid in missing_ids:
            if nid not in results_map:
                results_map[nid] = {
                    "id": nid,
                    "title": nid,
                    "category": "N/A",
                    "abstract": "",
                }
        # 按原始顺序返回
        for nid in ids:
            if nid in results_map:
                out.append(results_map[nid])
        return out

    def add_news(self, title, abstract="", body="", category="", subcategory=""):
        """管理员上传新闻：写入 MySQL，返回 news_id。"""
        category = (category or "N/A")[:64]
        subcategory = (subcategory or "N/A")[:128]
        conn = get_connection()
        if not conn:
            raise RuntimeError("数据库不可用")
        try:
            with conn.cursor() as cur:
                # 获取最大的数字ID
                cur.execute("SELECT MAX(CAST(SUBSTRING(news_id, 2) AS UNSIGNED)) FROM news WHERE news_id REGEXP '^N[0-9]+$'")
                result = cur.fetchone()
                max_id = result.get('MAX(CAST(SUBSTRING(news_id, 2) AS UNSIGNED))') if result else None
                max_id = max_id if max_id else 0
                
                # 循环查找下一个可用的ID，防止并发情况下的冲突
                candidate_id = f"N{max_id + 1}"
                while True:
                    cur.execute("SELECT 1 FROM news WHERE news_id = %s", (candidate_id,))
                    if not cur.fetchone():
                        # ID未被占用，可以使用
                        news_id = candidate_id
                        break
                    # 如果ID已被占用，尝试下一个ID
                    max_id += 1
                    candidate_id = f"N{max_id}"
                
                cur.execute(
                    "INSERT INTO news (news_id, category, subcategory, title, abstract, body, url, entity_ids) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                    (news_id, category, subcategory, (title or "")[:65535], (abstract or "")[:65535], (body or "")[:65535], "", json.dumps([])),
                )
            conn.commit()
            # 写入内存供本次会话使用
            self.news_info[news_id] = {"title": title, "abstract": abstract, "body": body, "category": category, "subcategory": subcategory}
            self.news_list.append(news_id)
            return news_id
        finally:
            conn.close()

    # ---------- Admin: news management ----------
    def admin_list_news(self, q=None, category=None, status=None, limit=100):
        conn = get_connection()
        if not conn:
            return []
        try:
            where = []
            args = []
            if q:
                where.append("(n.title LIKE %s OR n.abstract LIKE %s OR n.news_id LIKE %s)")
                like = f"%{q}%"
                args.extend([like, like, like])
            if category:
                where.append("n.category=%s")
                args.append(category)
            if status:
                where.append("COALESCE(s.status,'active')=%s")
                args.append(status)
            where_sql = ("WHERE " + " AND ".join(where)) if where else ""
            sql = f"""
                SELECT n.news_id, n.title, n.abstract, n.category, n.subcategory,
                       COALESCE(s.status,'active') AS status,
                       n.created_at,
                       COUNT(CASE WHEN e.event_type='dislike' THEN 1 END) AS dislike_count
                FROM news n
                LEFT JOIN news_status s ON s.news_id = n.news_id
                LEFT JOIN user_events e ON e.news_id = n.news_id
                {where_sql}
                GROUP BY n.news_id
                ORDER BY n.created_at DESC
                LIMIT %s
            """
            args.append(int(limit))
            with conn.cursor() as cur:
                cur.execute(sql, tuple(args))
                rows = cur.fetchall() or []
            out = []
            for r in rows:
                out.append(
                    {
                        "news_id": r["news_id"],
                        "title": (r.get("title") or "").strip(),
                        "category": r.get("category") or "N/A",
                        "subcategory": (r.get("subcategory") or "").strip() or "N/A",
                        "status": r.get("status") or "active",
                        "created_at": str(r.get("created_at")) if r.get("created_at") is not None else None,
                        "abstract": (r.get("abstract") or "").strip(),
                        "dislike_count": int(r.get("dislike_count") or 0),
                    }
                )
            return out
        finally:
            conn.close()

    def admin_list_flagged_news(self, limit=100):
        """获取 dislike_count > 2 的新闻列表"""
        conn = get_connection()
        if not conn:
            return []
        try:
            sql = """
                SELECT n.news_id, n.title, n.abstract, n.category, n.subcategory,
                       COALESCE(s.status,'active') AS status,
                       n.created_at,
                       COUNT(CASE WHEN e.event_type='dislike' THEN 1 END) AS dislike_count
                FROM news n
                LEFT JOIN news_status s ON s.news_id = n.news_id
                LEFT JOIN user_events e ON e.news_id = n.news_id
                GROUP BY n.news_id
                HAVING dislike_count > 2
                ORDER BY dislike_count DESC, n.created_at DESC
                LIMIT %s
            """
            with conn.cursor() as cur:
                cur.execute(sql, (int(limit),))
                rows = cur.fetchall() or []
            out = []
            for r in rows:
                out.append(
                    {
                        "news_id": r["news_id"],
                        "title": (r.get("title") or "").strip(),
                        "category": r.get("category") or "N/A",
                        "subcategory": (r.get("subcategory") or "").strip() or "N/A",
                        "status": r.get("status") or "active",
                        "created_at": str(r.get("created_at")) if r.get("created_at") is not None else None,
                        "abstract": (r.get("abstract") or "").strip(),
                        "dislike_count": int(r.get("dislike_count") or 0),
                    }
                )
            return out
        finally:
            conn.close()

    def admin_update_news(self, news_id, title=None, abstract=None, category=None, subcategory=None, status=None):
        conn = get_connection()
        if not conn:
            raise RuntimeError("数据库不可用")
        try:
            fields = []
            args = []
            if title is not None:
                fields.append("title=%s")
                args.append(title)
            if abstract is not None:
                fields.append("abstract=%s")
                args.append(abstract)
            if category is not None:
                fields.append("category=%s")
                args.append(category)
            if subcategory is not None:
                fields.append("subcategory=%s")
                args.append(subcategory)
            if fields:
                with conn.cursor() as cur:
                    cur.execute(f"UPDATE news SET {', '.join(fields)} WHERE news_id=%s", tuple(args + [news_id]))
            if status is not None:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO news_status (news_id, status) VALUES (%s,%s)
                        ON DUPLICATE KEY UPDATE status=VALUES(status)
                        """,
                        (news_id, status),
                    )
            conn.commit()
            # refresh in-memory cache (best-effort)
            if news_id in self.news_info:
                if title is not None:
                    self.news_info[news_id]["title"] = title
                if abstract is not None:
                    self.news_info[news_id]["abstract"] = abstract
                if category is not None:
                    self.news_info[news_id]["category"] = category
                if subcategory is not None:
                    self.news_info[news_id]["subcategory"] = subcategory
        finally:
            conn.close()

    def admin_delete_news(self, news_id):
        conn = get_connection()
        if not conn:
            raise RuntimeError("数据库不可用")
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM news WHERE news_id=%s", (news_id,))
                cur.execute("DELETE FROM news_status WHERE news_id=%s", (news_id,))
            conn.commit()
            if news_id in self.news_info:
                del self.news_info[news_id]
        finally:
            conn.close()

    # ---------- Admin: stats ----------
    def admin_stats_overview(self):
        conn = get_connection()
        if not conn:
            return {"dau": 0, "events_24h": 0, "dau_trend": [], "events_trend": [], "top_categories_7d": [], "top_news_7d": []}
        try:
            now_ms = int(time.time() * 1000)
            day_ms = 24 * 3600 * 1000
            start_24h = now_ms - day_ms
            start_7d = now_ms - 7 * day_ms
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(DISTINCT user_id) AS dau FROM user_events WHERE ts >= %s",
                    (start_24h,),
                )
                dau = int((cur.fetchone() or {}).get("dau") or 0)
                cur.execute(
                    "SELECT COUNT(*) AS cnt FROM user_events WHERE ts >= %s",
                    (start_24h,),
                )
                events_24h = int((cur.fetchone() or {}).get("cnt") or 0)
                cur.execute(
                    """
                    SELECT n.category AS category, COUNT(*) AS cnt
                    FROM user_events e
                    JOIN news n ON n.news_id = e.news_id
                    WHERE e.ts >= %s AND e.event_type IN ('click','like','favorite')
                    GROUP BY n.category
                    ORDER BY cnt DESC
                    LIMIT 10
                    """,
                    (start_7d,),
                )
                top_categories = [{"name": r["category"], "count": int(r["cnt"])} for r in (cur.fetchall() or [])]
                cur.execute(
                    """
                    SELECT e.news_id AS news_id, COUNT(*) AS cnt
                    FROM user_events e
                    WHERE e.ts >= %s AND e.event_type IN ('click','like','favorite')
                    GROUP BY e.news_id
                    ORDER BY cnt DESC
                    LIMIT 10
                    """,
                    (start_7d,),
                )
                rows = cur.fetchall() or []
            top_news = []
            for r in rows:
                nid = r["news_id"]
                info = self.news_info.get(nid) or {}
                top_news.append(
                    {
                        "news_id": nid,
                        "count": int(r["cnt"]),
                        "title": info.get("title") or nid,
                        "category": info.get("category") or "N/A",
                    }
                )
            # 查询过去7天的DAU趋势
            dau_trend = []
            with conn.cursor() as cur2:
                cur2.execute(
                    """
                    SELECT DATE(FROM_UNIXTIME(ts/1000)) AS day, COUNT(DISTINCT user_id) AS cnt
                    FROM user_events
                    WHERE ts >= %s
                    GROUP BY DATE(FROM_UNIXTIME(ts/1000))
                    ORDER BY day ASC
                    """,
                    (start_7d,),
                )
                for r in (cur2.fetchall() or []):
                    dau_trend.append({"date": str(r["day"]), "value": int(r["cnt"])})

            # 查询过去7天的事件量趋势
            events_trend = []
            with conn.cursor() as cur3:
                cur3.execute(
                    """
                    SELECT DATE(FROM_UNIXTIME(ts/1000)) AS day, COUNT(*) AS cnt
                    FROM user_events
                    WHERE ts >= %s
                    GROUP BY DATE(FROM_UNIXTIME(ts/1000))
                    ORDER BY day ASC
                    """,
                    (start_7d,),
                )
                for r in (cur3.fetchall() or []):
                    events_trend.append({"date": str(r["day"]), "value": int(r["cnt"])})

            return {
                "dau": dau,
                "events_24h": events_24h,
                "dau_trend": dau_trend,
                "events_trend": events_trend,
                "top_categories_7d": top_categories,
                "top_news_7d": top_news,
            }
        finally:
            conn.close()

    def admin_stats_trends(self, days=14):
        conn = get_connection()
        if not conn:
            return []
        try:
            now_ms = int(time.time() * 1000)
            day_ms = 24 * 3600 * 1000
            start_ms = now_ms - int(days) * day_ms
            with conn.cursor() as cur:
                # group by date (ms -> date) using FROM_UNIXTIME(ts/1000)
                cur.execute(
                    """
                    SELECT DATE(FROM_UNIXTIME(ts/1000)) AS day, COUNT(*) AS cnt
                    FROM user_events
                    WHERE ts >= %s
                    GROUP BY DATE(FROM_UNIXTIME(ts/1000))
                    ORDER BY day ASC
                    """,
                    (start_ms,),
                )
                rows = cur.fetchall() or []
            return [{"day": str(r["day"]), "events": int(r["cnt"])} for r in rows]
        finally:
            conn.close()

    # ---------- Search & explore ----------
    def get_all_categories(self):
        """获取所有不重复的类别列表"""
        conn = get_connection()
        if not conn:
            return []
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT DISTINCT category FROM news WHERE category IS NOT NULL AND category != 'N/A' ORDER BY category")
                rows = cur.fetchall() or []
            return [r["category"] for r in rows]
        finally:
            conn.close()

    def search_news(self, q=None, category=None, subcategory=None, limit=50):
        conn = get_connection()
        if not conn:
            return []
        try:
            where = []
            args = []
            if q:
                where.append("(title LIKE %s OR abstract LIKE %s OR news_id LIKE %s)")
                like = f"%{q}%"
                args.extend([like, like, like])
            if category:
                where.append("category=%s")
                args.append(category)
            if subcategory:
                where.append("subcategory=%s")
                args.append(subcategory)
            where_sql = ("WHERE " + " AND ".join(where)) if where else ""
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT news_id, title, abstract, category, subcategory
                    FROM news
                    {where_sql}
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    tuple(args + [int(limit)]),
                )
                rows = cur.fetchall() or []
            out = []
            for r in rows:
                out.append(
                    {
                        "news_id": r["news_id"],
                        "title": (r.get("title") or "").strip() or r["news_id"],
                        "abstract": (r.get("abstract") or "").strip(),
                        "category": r.get("category") or "N/A",
                        "subcategory": (r.get("subcategory") or "").strip() or "N/A",
                    }
                )
            return out
        finally:
            conn.close()

    def get_news_like_count(self, news_id):
        """获取新闻的点赞数"""
        conn = get_connection()
        if not conn:
            return 0
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) as cnt FROM user_events WHERE news_id=%s AND event_type='like'",
                    (news_id,),
                )
                row = cur.fetchone()
            return row["cnt"] if row else 0
        finally:
            conn.close()

    def get_user_liked(self, user_id, news_id):
        """检查用户是否已点赞该新闻"""
        conn = get_connection()
        if not conn:
            return False
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM user_events WHERE user_id=%s AND news_id=%s AND event_type='like' LIMIT 1",
                    (user_id, news_id),
                )
                row = cur.fetchone()
            return row is not None
        finally:
            conn.close()

    def get_news_detail(self, news_id, user_id=None):
        info = self.news_info.get(news_id)
        if info:
            # entity_ids may not be in memory cache; fetch from DB best-effort
            conn = get_connection()
            entity_ids = []
            url = ""
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("SELECT url, entity_ids, subcategory FROM news WHERE news_id=%s", (news_id,))
                        row = cur.fetchone()
                    if row:
                        url = row.get("url") or ""
                        raw = row.get("entity_ids")
                        if isinstance(raw, list):
                            entity_ids = raw
                        else:
                            try:
                                entity_ids = json.loads(raw or "[]")
                            except Exception:
                                entity_ids = []
                        if not info.get("subcategory") and row.get("subcategory"):
                            info["subcategory"] = row.get("subcategory")
                finally:
                    conn.close()
            # 获取点赞数和用户点赞状态
            like_count = self.get_news_like_count(news_id)
            user_liked = self.get_user_liked(user_id, news_id) if user_id else False
            return {
                "news_id": news_id,
                "title": info.get("title") or news_id,
                "abstract": info.get("abstract") or "",
                "category": info.get("category") or "N/A",
                "subcategory": info.get("subcategory") or "N/A",
                "url": url,
                "entity_ids": entity_ids or [],
                "like_count": like_count,
                "user_liked": user_liked,
            }
        conn = get_connection()
        if not conn:
            return None
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT news_id, title, abstract, category, subcategory, url, entity_ids FROM news WHERE news_id=%s",
                    (news_id,),
                )
                row = cur.fetchone()
            if not row:
                return None
            raw = row.get("entity_ids")
            if isinstance(raw, list):
                entity_ids = raw
            else:
                try:
                    entity_ids = json.loads(raw or "[]")
                except Exception:
                    entity_ids = []
            # 获取点赞数和用户点赞状态
            like_count = self.get_news_like_count(news_id)
            user_liked = self.get_user_liked(user_id, news_id) if user_id else False
            return {
                "news_id": row["news_id"],
                "title": (row.get("title") or "").strip() or row["news_id"],
                "abstract": (row.get("abstract") or "").strip(),
                "category": row.get("category") or "N/A",
                "subcategory": (row.get("subcategory") or "").strip() or "N/A",
                "url": row.get("url") or "",
                "entity_ids": entity_ids or [],
                "like_count": like_count,
                "user_liked": user_liked,
            }
        finally:
            conn.close()

    def similar_news(self, news_id, limit=12):
        base = self.get_news_detail(news_id)
        if not base:
            return []
        cat = base.get("category") or ""
        subcat = base.get("subcategory") or ""
        conn = get_connection()
        if not conn:
            # fallback: sample from memory of same category
            exclude = {news_id}
            ids = self._get_same_category_news(cat, exclude, count=min(limit, 20))
            return [self.get_news_detail(nid) for nid in ids if self.get_news_detail(nid)]
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT news_id, title, abstract, category, subcategory
                    FROM news
                    WHERE news_id != %s
                      AND (subcategory=%s OR category=%s)
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (news_id, subcat, cat, int(limit)),
                )
                rows = cur.fetchall() or []
            return [
                {
                    "news_id": r["news_id"],
                    "title": (r.get("title") or "").strip() or r["news_id"],
                    "abstract": (r.get("abstract") or "").strip(),
                    "category": r.get("category") or "N/A",
                    "subcategory": (r.get("subcategory") or "").strip() or "N/A",
                }
                for r in rows
            ]
        finally:
            conn.close()

    # ---------- Clustering (KMeans) ----------
    def _list_users_for_clustering(self, limit=5000):
        conn = get_connection()
        if not conn:
            return []
        try:
            with conn.cursor() as cur:
                # Prefer users with any events; fall back to user_history.
                cur.execute("SELECT DISTINCT user_id FROM user_events ORDER BY user_id LIMIT %s", (int(limit),))
                rows = cur.fetchall() or []
                users = [r["user_id"] for r in rows]
                if users:
                    return users
                cur.execute("SELECT user_id FROM user_history ORDER BY user_id LIMIT %s", (int(limit),))
                rows = cur.fetchall() or []
                return [r["user_id"] for r in rows]
        finally:
            conn.close()

    def _profile_to_sparse(self, user_id, top_cat=10, top_sub=10):
        p = self.get_user_profile(user_id)
        feats = {}
        for c in (p.get("categories") or [])[:top_cat]:
            name = c.get("name")
            if name:
                feats[f"c:{name}"] = float(c.get("score") or 0.0)
        for s in (p.get("subcategories") or [])[:top_sub]:
            name = s.get("name")
            if name:
                feats[f"s:{name}"] = float(s.get("score") or 0.0)
        return feats

    def _kmeans(self, vectors, k=6, iters=12, seed=42):
        """
        Minimal KMeans (no sklearn dependency).
        vectors: List[List[float]] shape (N, D)
        return: labels (N), centroids (k, D)
        """
        import random as _rnd

        n = len(vectors)
        if n == 0:
            return [], []
        d = len(vectors[0]) if vectors[0] else 0
        if d == 0:
            return [0] * n, [[0.0] * 0]
        _rnd.seed(seed)
        init_idx = list(range(n))
        _rnd.shuffle(init_idx)
        centroids = [vectors[i][:] for i in init_idx[: min(k, n)]]
        k_eff = len(centroids)

        def _dist2(a, b):
            s = 0.0
            for i in range(d):
                x = a[i] - b[i]
                s += x * x
            return s

        labels = [0] * n
        for _ in range(iters):
            changed = False
            for i in range(n):
                best_j = 0
                best_d = _dist2(vectors[i], centroids[0])
                for j in range(1, k_eff):
                    dd = _dist2(vectors[i], centroids[j])
                    if dd < best_d:
                        best_d = dd
                        best_j = j
                if labels[i] != best_j:
                    labels[i] = best_j
                    changed = True
            sums = [[0.0] * d for _ in range(k_eff)]
            cnts = [0] * k_eff
            for i in range(n):
                j = labels[i]
                cnts[j] += 1
                v = vectors[i]
                row = sums[j]
                for t in range(d):
                    row[t] += v[t]
            for j in range(k_eff):
                if cnts[j] == 0:
                    # re-init an empty cluster
                    centroids[j] = vectors[_rnd.randrange(n)][:]
                else:
                    inv = 1.0 / cnts[j]
                    centroids[j] = [x * inv for x in sums[j]]
            if not changed:
                break
        return labels, centroids

    def rebuild_user_clusters(self, k=6, user_limit=3000):
        users = self._list_users_for_clustering(limit=user_limit)
        if not users:
            return {"users": 0, "clusters": 0}
        sparse_list = [self._profile_to_sparse(uid) for uid in users]
        # build vocabulary of top features to keep D bounded
        global_cnt = Counter()
        for feats in sparse_list:
            for key in feats.keys():
                global_cnt[key] += 1
        vocab = [k for k, _ in global_cnt.most_common(200)]
        idx = {k: i for i, k in enumerate(vocab)}
        vectors = []
        for feats in sparse_list:
            v = [0.0] * len(vocab)
            for key, val in feats.items():
                j = idx.get(key)
                if j is not None:
                    v[j] = float(val)
            # L2 normalize
            norm = math.sqrt(sum(x * x for x in v)) or 1.0
            v = [x / norm for x in v]
            vectors.append(v)
        labels, centroids = self._kmeans(vectors, k=int(k), iters=15, seed=42)
        k_eff = (max(labels) + 1) if labels else 0
        # derive cluster names by centroid top category dims
        cluster_names = {}
        for cid in range(k_eff):
            cvec = centroids[cid]
            pairs = sorted(enumerate(cvec), key=lambda t: -t[1])[:8]
            cats = []
            for j, w in pairs:
                if w <= 0:
                    continue
                key = vocab[j]
                if key.startswith("c:"):
                    cats.append(key[2:])
                if len(cats) >= 2:
                    break
            cluster_names[cid] = "_".join(cats) if cats else f"cluster_{cid}"

        conn = get_connection()
        if not conn:
            return {"users": len(users), "clusters": k_eff}
        try:
            with conn.cursor() as cur:
                batch = []
                for uid, cid in zip(users, labels):
                    batch.append((uid, int(cid), cluster_names.get(int(cid), ""),))
                cur.executemany(
                    """
                    INSERT INTO user_clusters (user_id, cluster_id, cluster_name)
                    VALUES (%s,%s,%s)
                    ON DUPLICATE KEY UPDATE
                      cluster_id=VALUES(cluster_id),
                      cluster_name=VALUES(cluster_name)
                    """,
                    batch,
                )
                conn.commit()
            return {"users": len(users), "clusters": k_eff}
        finally:
            conn.close()

    def get_user_cluster(self, user_id):
        conn = get_connection()
        if not conn:
            return {"user_id": user_id, "cluster_id": None, "cluster_name": "", "updated_at": None}
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT user_id, cluster_id, cluster_name, updated_at FROM user_clusters WHERE user_id=%s",
                    (user_id,),
                )
                row = cur.fetchone()
            if not row:
                return {"user_id": user_id, "cluster_id": None, "cluster_name": "", "updated_at": None}
            return {
                "user_id": row["user_id"],
                "cluster_id": int(row["cluster_id"]),
                "cluster_name": row.get("cluster_name") or "",
                "updated_at": str(row.get("updated_at")) if row.get("updated_at") is not None else None,
            }
        finally:
            conn.close()

    def delete_user_subcategory(self, user_id, subcategory_name):
       """删除用户的兴趣标签（仅返回成功，实际删除在前端处理）"""
       pass

    def get_cluster_graph(self, user_id, same_cluster_limit=30):
        """返回用户聚类图谱数据：当前用户、所属兴趣群、同群其他用户及连边。"""
        row = self.get_user_cluster(user_id)
        cluster_id = row.get("cluster_id")
        cluster_name = row.get("cluster_name") or (f"兴趣群{cluster_id}" if cluster_id is not None else "")
        nodes = []
        links = []
        nodes.append({"id": user_id, "name": "当前用户", "category": 0})
        if cluster_id is None:
            return {"nodes": nodes, "links": links}
        cluster_node_id = f"cluster_{cluster_id}"
        nodes.append({"id": cluster_node_id, "name": cluster_name, "category": 1})
        links.append({"source": user_id, "target": cluster_node_id})
        conn = get_connection()
        if not conn:
            return {"nodes": nodes, "links": links}
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT user_id FROM user_clusters WHERE cluster_id=%s AND user_id!=%s ORDER BY user_id LIMIT %s",
                    (cluster_id, user_id, int(same_cluster_limit)),
                )
                rows = cur.fetchall() or []
            for r in rows:
                uid = r["user_id"]
                nodes.append({"id": uid, "name": uid, "category": 2})
                links.append({"source": uid, "target": cluster_node_id})
            return {"nodes": nodes, "links": links}
        finally:
            conn.close()
