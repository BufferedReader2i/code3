# -*- coding: utf-8 -*-
"""
MIND 个性化新闻推荐：单文件实现
包含：数据加载、用户画像、带注意力的神经模型、训练与保存
全量数据时按块加载行为，避免 MemoryError（16GB 内存可用）
"""

import argparse
import json
import re
import os
from collections import Counter, defaultdict

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


# ---------- 配置 ----------
DATA_DIR = "datal"
NEWS_FILE = os.path.join(DATA_DIR, "news.tsv")
BEHAVIORS_FILE = os.path.join(DATA_DIR, "behaviors.tsv")
ENTITY_EMBED_FILE = os.path.join(DATA_DIR, "entity_embedding.vec")

TITLE_MAX_LEN = 30
MAX_HISTORY = 50
NEWS_EMBED_DIM = 128
ENTITY_DIM = 100
VOCAB_MIN_FREQ = 2
MAX_NEWS = 120000
MAX_BEHAVIORS_TRAIN = 3000
BEHAVIOR_CHUNK_SIZE = 50000  # 全量时按块加载，避免 MemoryError（16GB 可保持 50000 或改为 30000）
BATCH_SIZE = 32
EPOCHS = 2
LR = 1e-3
SAVE_PATH = "mind_recommender.pt"
TRAIN_RATIO = 0.9
SPLIT_SEED = 42
LOG_INTERVAL = 50


def parse_entities_json(s):
    """从 MIND 的 entity JSON 字符串中解析出 WikidataId 列表"""
    if not s or s.strip() in ("[]", ""):
        return []
    try:
        arr = json.loads(s)
        return [item.get("WikidataId") for item in arr if isinstance(item, dict) and item.get("WikidataId")]
    except Exception:
        return []


def load_entity_embeddings(path):
    """加载 entity_embedding.vec：第一列 id，后面 100 维"""
    embeds = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 101:
                continue
            eid = parts[0]
            vec = [float(x) for x in parts[1:101]]
            embeds[eid] = np.array(vec, dtype=np.float32)
    return embeds


def load_news(news_path, entity_embeds):
    """加载 news.tsv：id, category, subcategory, title, abstract, url, title_entities, abstract_entities"""
    news_data = {}
    word_counter = Counter()
    with open(news_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            parts = line.strip().split("\t")
            if len(parts) < 6:
                continue
            nid = parts[0]
            category = parts[1]
            subcategory = parts[2]
            title = (parts[3] or "").strip()
            abstract = (parts[4] or "").strip()
            title_ent = parse_entities_json(parts[6]) if len(parts) > 6 else []
            abstract_ent = parse_entities_json(parts[7]) if len(parts) > 7 else []
            entity_ids = list(dict.fromkeys(title_ent + abstract_ent))[:10]
            text = (title + " " + abstract).lower()
            words = re.findall(r"\b\w+\b", text)[:TITLE_MAX_LEN]
            for w in words:
                word_counter[w] += 1
            news_data[nid] = {
                "idx": idx,
                "title_words": words,
                "category": category,
                "subcategory": subcategory,
                "entity_ids": entity_ids,
            }
    vocab = {"<pad>": 0, "<unk>": 1}
    for w, c in word_counter.items():
        if c >= VOCAB_MIN_FREQ:
            vocab[w] = len(vocab)
    return news_data, vocab


def load_behaviors(behaviors_path, news_data, max_lines=None):
    """
    加载 behaviors.tsv：impression_id, user_id, timestamp, history, impressions
    返回 [(user_id, history_ids, [(news_id, label), ...]), ...]
    全量时仅要求 impressions 非空（允许 history 为空）；有 max_lines 时要求 history 非空以利训练。
    """
    samples = []
    total_read = 0
    with open(behaviors_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if max_lines is not None and i >= max_lines:
                break
            total_read = i + 1
            if max_lines is None and total_read > 0 and total_read % 200000 == 0:
                print(f"  行为文件已读取 {total_read} 行，当前有效 {len(samples)} 条...")
            parts = line.strip().split("\t")
            if len(parts) < 5:
                continue
            user_id = parts[1]
            history_raw = (parts[3] or "").split()
            history_ids = [n for n in history_raw if n in news_data][-MAX_HISTORY:]
            imp_raw = (parts[4] or "").split()
            impressions = []
            for item in imp_raw:
                if "-" in item:
                    nid, lab = item.rsplit("-", 1)
                    if nid in news_data and lab in ("0", "1"):
                        impressions.append((nid, int(lab)))
            if not impressions:
                continue
            samples.append((user_id, history_ids, impressions))
    return samples, total_read


def iter_behavior_chunks(behaviors_path, news_data, chunk_size=BEHAVIOR_CHUNK_SIZE, max_lines=None):
    """
    按块迭代 behaviors，每块最多 chunk_size 行，避免全量加载导致 MemoryError。
    产出: (samples_list) 每块格式同 load_behaviors。
    """
    samples = []
    in_chunk = 0
    with open(behaviors_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if max_lines is not None and i >= max_lines:
                break
            parts = line.strip().split("\t")
            if len(parts) < 5:
                continue
            user_id = parts[1]
            history_raw = (parts[3] or "").split()
            history_ids = [n for n in history_raw if n in news_data][-MAX_HISTORY:]
            imp_raw = (parts[4] or "").split()
            impressions = []
            for item in imp_raw:
                if "-" in item:
                    nid, lab = item.rsplit("-", 1)
                    if nid in news_data and lab in ("0", "1"):
                        impressions.append((nid, int(lab)))
            if not history_ids or not impressions:
                continue
            samples.append((user_id, history_ids, impressions))
            in_chunk += 1
            if in_chunk >= chunk_size:
                yield samples
                samples = []
                in_chunk = 0
    if samples:
        yield samples


# ---------- 模型 ----------
class TitleEncoder(nn.Module):
    """标题编码：Embedding + 多尺度 CNN + 池化"""

    def __init__(self, vocab_size, embed_dim=100, num_filters=100, kernel_sizes=(3, 4, 5)):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.convs = nn.ModuleList(
            [nn.Conv1d(embed_dim, num_filters, k, padding=k // 2) for k in kernel_sizes]
        )
        self.out_dim = num_filters * len(kernel_sizes)

    def forward(self, x):
        x = self.embed(x)
        x = x.transpose(1, 2)
        xs = [F.relu(conv(x)).max(dim=2)[0] for conv in self.convs]
        return torch.cat(xs, dim=1)


class NewsEncoder(nn.Module):
    """新闻编码：标题 + 类别 + 子类 + 实体 -> news_embed_dim"""

    def __init__(self, vocab_size, num_categories, num_subcategories, news_embed_dim=128):
        super().__init__()
        self.title_encoder = TitleEncoder(vocab_size, embed_dim=100, num_filters=80, kernel_sizes=(3, 4, 5))
        title_dim = self.title_encoder.out_dim
        self.cat_embed = nn.Embedding(num_categories, 32, padding_idx=0)
        self.subcat_embed = nn.Embedding(num_subcategories, 32, padding_idx=0)
        self.entity_proj = nn.Linear(ENTITY_DIM, 32)
        proj_in = title_dim + 32 + 32 + 32
        self.fusion = nn.Sequential(
            nn.Linear(proj_in, news_embed_dim),
            nn.LayerNorm(news_embed_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
        )
        self.news_embed_dim = news_embed_dim

    def forward(self, title_ids, cat_ids, subcat_ids, entity_vecs):
        title_feat = self.title_encoder(title_ids)
        cat_feat = self.cat_embed(cat_ids)
        subcat_feat = self.subcat_embed(subcat_ids)
        entity_feat = self.entity_proj(entity_vecs)
        x = torch.cat([title_feat, cat_feat, subcat_feat, entity_feat], dim=1)
        return self.fusion(x)


class TargetAwareUserEncoder(nn.Module):
    """用户编码：以候选新闻为 query，对历史点击做 attention 聚合"""

    def __init__(self, news_embed_dim=128, num_heads=4):
        super().__init__()
        self.news_embed_dim = news_embed_dim
        self.num_heads = num_heads
        self.head_dim = news_embed_dim // num_heads
        self.query_proj = nn.Linear(news_embed_dim, news_embed_dim)
        self.key_proj = nn.Linear(news_embed_dim, news_embed_dim)
        self.value_proj = nn.Linear(news_embed_dim, news_embed_dim)
        self.out_proj = nn.Linear(news_embed_dim, news_embed_dim)

    def forward(self, history_embeds, candidate_embed, mask=None):
        B, L, D = history_embeds.shape
        q = self.query_proj(candidate_embed).unsqueeze(1)
        k = self.key_proj(history_embeds)
        v = self.value_proj(history_embeds)
        q = q.view(B, 1, self.num_heads, self.head_dim).transpose(1, 2)
        k = k.view(B, L, self.num_heads, self.head_dim).transpose(1, 2)
        v = v.view(B, L, self.num_heads, self.head_dim).transpose(1, 2)
        scores = (q @ k.transpose(-2, -1)) / (self.head_dim ** 0.5)
        if mask is not None:
            scores = scores.masked_fill(mask.unsqueeze(1).unsqueeze(2), float("-inf"))
        attn = F.softmax(scores, dim=-1)
        out = (attn @ v).transpose(1, 2).contiguous().view(B, self.news_embed_dim)
        return self.out_proj(out)


class NRMSModel(nn.Module):
    """NRMS：新闻编码 + 用户编码（target-aware attention）+ 点击预测"""

    def __init__(self, vocab_size, num_categories, num_subcategories, news_embed_dim=128):
        super().__init__()
        self.news_encoder = NewsEncoder(vocab_size, num_categories, num_subcategories, news_embed_dim)
        self.user_encoder = TargetAwareUserEncoder(news_embed_dim)
        self.news_embed_dim = news_embed_dim

    def forward(
        self,
        hist_title, hist_cat, hist_subcat, hist_entity,
        cand_title, cand_cat, cand_subcat, cand_entity,
        hist_mask,
    ):
        B, L, _ = hist_title.shape
        hist_title_flat = hist_title.reshape(B * L, -1)
        hist_cat_flat = hist_cat.reshape(B * L)
        hist_subcat_flat = hist_subcat.reshape(B * L)
        hist_entity_flat = hist_entity.reshape(B * L, -1)
        hist_embeds_flat = self.news_encoder(hist_title_flat, hist_cat_flat, hist_subcat_flat, hist_entity_flat)
        hist_embeds = hist_embeds_flat.reshape(B, L, self.news_embed_dim)
        cand_embeds = self.news_encoder(cand_title, cand_cat, cand_subcat, cand_entity)
        user_embeds = self.user_encoder(hist_embeds, cand_embeds, mask=hist_mask)
        logits = (user_embeds * cand_embeds).sum(dim=1)
        return logits


# ---------- 系统 ----------
class MindRecommenderSystem:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.entity_embeds = {}
        self.news_data = {}
        self.vocab = {}
        self.category2id = {}
        self.subcategory2id = {}
        self.user_history = defaultdict(list)
        self.model = None
        self.config = {}

    def load_entity_embeddings(self, path=ENTITY_EMBED_FILE):
        self.entity_embeds = load_entity_embeddings(path)
        

    def load_news(self, path=NEWS_FILE):
        self.news_data, self.vocab = load_news(path, self.entity_embeds)
        cats = set()
        subcats = set()
        for d in self.news_data.values():
            cats.add(d["category"])
            subcats.add(d["subcategory"])
        self.category2id = {"<pad>": 0, **{c: i + 1 for i, c in enumerate(sorted(cats))}}
        self.subcategory2id = {"<pad>": 0, **{s: i + 1 for i, s in enumerate(sorted(subcats))}}
        print(f"加载新闻: {len(self.news_data)} 条, 词表: {len(self.vocab)}")

    def load_behaviors(self, path=BEHAVIORS_FILE, max_lines=MAX_BEHAVIORS_TRAIN):
        samples, total_read = load_behaviors(path, self.news_data, max_lines=max_lines)
        for user_id, history_ids, impressions in samples:
            self.user_history[user_id].append((history_ids, impressions))
        n_impressions = sum(len(v) for v in self.user_history.values())
        print(f"加载行为: 文件共 {total_read} 行, 有效 {n_impressions} 条, 用户数 {len(self.user_history)}")

    def build_model(self):
        self.config = {
            "vocab_size": len(self.vocab),
            "num_categories": len(self.category2id),
            "num_subcategories": len(self.subcategory2id),
            "news_embed_dim": NEWS_EMBED_DIM,
        }
        self.model = NRMSModel(
            self.config["vocab_size"],
            self.config["num_categories"],
            self.config["num_subcategories"],
            NEWS_EMBED_DIM,
        ).to(self.device)

    def _tensorize_news_batch(self, news_ids):
        title_ids = []
        cat_ids = []
        subcat_ids = []
        entity_vecs = []
        for nid in news_ids:
            d = self.news_data.get(nid, {})
            words = (d.get("title_words") or [])[:TITLE_MAX_LEN]
            tid = [self.vocab.get(w, 1) for w in words] + [0] * (TITLE_MAX_LEN - len(words))
            title_ids.append(tid)
            cat_ids.append(self.category2id.get(d.get("category", ""), 0))
            subcat_ids.append(self.subcategory2id.get(d.get("subcategory", ""), 0))
            eids = d.get("entity_ids") or []
            vec = np.zeros(ENTITY_DIM, dtype=np.float32)
            for i, eid in enumerate(eids[:5]):
                if eid in self.entity_embeds:
                    vec += self.entity_embeds[eid]
            if len(eids) > 0:
                vec /= max(1, sum(1 for e in eids[:5] if e in self.entity_embeds))
            entity_vecs.append(vec)
        title_t = torch.tensor(title_ids, dtype=torch.long, device=self.device)
        cat_t = torch.tensor(cat_ids, dtype=torch.long, device=self.device)
        subcat_t = torch.tensor(subcat_ids, dtype=torch.long, device=self.device)
        entity_t = torch.tensor(np.array(entity_vecs), dtype=torch.float32, device=self.device)
        return title_t, cat_t, subcat_t, entity_t

    def get_user_profile(self, user_id, top_k_cat=5, top_k_entity=10):
        """用户画像：兴趣类别、兴趣实体、统计"""
        if user_id not in self.user_history or not self.user_history[user_id]:
            return {"categories": [], "entities": [], "history_count": 0}
        all_hist = []
        for hist_ids, _ in self.user_history[user_id]:
            all_hist.extend(hist_ids)
        seen = set()
        unique_hist = []
        for nid in reversed(all_hist):
            if nid not in seen and nid in self.news_data:
                seen.add(nid)
                unique_hist.append(nid)
        unique_hist = unique_hist[-MAX_HISTORY:]
        cat_counter = Counter()
        entity_counter = Counter()
        for nid in unique_hist:
            d = self.news_data[nid]
            cat_counter[d["category"]] += 1
            for eid in d["entity_ids"]:
                entity_counter[eid] += 1
        return {
            "categories": cat_counter.most_common(top_k_cat),
            "entities": entity_counter.most_common(top_k_entity),
            "history_count": len(unique_hist),
        }

    def _run_one_batch(self, batch, criterion):
        hist_title_list, hist_cat_list, hist_subcat_list, hist_entity_list = [], [], [], []
        cand_title_list, cand_cat_list, cand_subcat_list, cand_entity_list = [], [], [], []
        labels = []
        max_hist_len = 0
        for user_id, history_ids, impressions in batch:
            if not history_ids:
                continue
            pos_cands = [nid for nid, lab in impressions if lab == 1]
            neg_cands = [nid for nid, lab in impressions if lab == 0]
            if not pos_cands or not neg_cands:
                continue
            pos_nid = np.random.choice(pos_cands)
            neg_nid = np.random.choice(neg_cands)
            for cand_nid, label in [(pos_nid, 1), (neg_nid, 0)]:
                hist_title, hist_cat, hist_subcat, hist_entity = self._tensorize_news_batch(history_ids)
                cand_title, cand_cat, cand_subcat, cand_entity = self._tensorize_news_batch([cand_nid])
                hist_title_list.append(hist_title)
                hist_cat_list.append(hist_cat)
                hist_subcat_list.append(hist_subcat)
                hist_entity_list.append(hist_entity)
                cand_title_list.append(cand_title)
                cand_cat_list.append(cand_cat)
                cand_subcat_list.append(cand_subcat)
                cand_entity_list.append(cand_entity)
                labels.append(label)
                max_hist_len = max(max_hist_len, hist_title.size(0))
        if not labels:
            return None, 0
        B = len(labels)
        pad_hist_title = torch.zeros(B, max_hist_len, TITLE_MAX_LEN, dtype=torch.long, device=self.device)
        pad_hist_cat = torch.zeros(B, max_hist_len, dtype=torch.long, device=self.device)
        pad_hist_subcat = torch.zeros(B, max_hist_len, dtype=torch.long, device=self.device)
        pad_hist_entity = torch.zeros(B, max_hist_len, ENTITY_DIM, device=self.device)
        hist_mask = torch.ones(B, max_hist_len, dtype=torch.bool, device=self.device)
        for i in range(B):
            L = hist_title_list[i].size(0)
            pad_hist_title[i, :L, :] = hist_title_list[i]
            pad_hist_cat[i, :L] = hist_cat_list[i]
            pad_hist_subcat[i, :L] = hist_subcat_list[i]
            pad_hist_entity[i, :L, :] = hist_entity_list[i]
            hist_mask[i, :L] = False
        cand_title = torch.cat(cand_title_list, dim=0)
        cand_cat = torch.cat(cand_cat_list, dim=0)
        cand_subcat = torch.cat(cand_subcat_list, dim=0)
        cand_entity = torch.cat(cand_entity_list, dim=0)
        logits = self.model(
            pad_hist_title, pad_hist_cat, pad_hist_subcat, pad_hist_entity,
            cand_title, cand_cat, cand_subcat, cand_entity, hist_mask
        )
        loss = criterion(logits, torch.tensor(labels, dtype=torch.float32, device=self.device))
        return loss, B

    def _eval_test(self, test_samples, criterion, max_batches=200):
        self.model.eval()
        total_loss = 0.0
        total = 0
        with torch.no_grad():
            n_b = 0
            for start in range(0, len(test_samples), BATCH_SIZE):
                if n_b >= max_batches:
                    break
                batch = test_samples[start : start + BATCH_SIZE]
                loss, B = self._run_one_batch(batch, criterion)
                if loss is None:
                    continue
                total_loss += loss.item()
                total += B
                n_b += 1
        self.model.train()
        if total == 0:
            return 0.0, 0
        return total_loss / max(n_b, 1), total

    def train(self, epochs=EPOCHS, lr=LR, batch_size=BATCH_SIZE, max_behaviors=MAX_BEHAVIORS_TRAIN):
        if self.model is None:
            self.build_model()
        chunk_size = min(BEHAVIOR_CHUNK_SIZE, max_behaviors) if max_behaviors else BEHAVIOR_CHUNK_SIZE
        chunk_iter = iter_behavior_chunks(
            BEHAVIORS_FILE, self.news_data, chunk_size=chunk_size, max_lines=max_behaviors
        )
        first_chunk = next(chunk_iter, None)
        if not first_chunk:
            print("无有效行为数据，跳过训练")
            return
        rng = np.random.RandomState(SPLIT_SEED)
        n_test = max(1, int(len(first_chunk) * (1 - TRAIN_RATIO)))
        idx = rng.permutation(len(first_chunk))
        test_samples = [first_chunk[i] for i in idx[-n_test:]]
        train_first = [first_chunk[i] for i in idx[:-n_test]]
        print(f"数据划分: 首块训练 {len(train_first)} 条, 测试集 {len(test_samples)} 条 (比例 {TRAIN_RATIO:.0%} / {1-TRAIN_RATIO:.0%})")

        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        criterion = nn.BCEWithLogitsLoss()
        self.model.train()

        for epoch in range(epochs):
            epoch_loss = 0.0
            n_batch = 0
            step_i = 0
            np.random.shuffle(train_first)
            for start in range(0, len(train_first), batch_size):
                batch = train_first[start : start + batch_size]
                loss, B = self._run_one_batch(batch, criterion)
                if loss is None:
                    continue
                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                optimizer.step()
                epoch_loss += loss.item()
                n_batch += 1
                step_i += 1
                running_avg = epoch_loss / n_batch
                if step_i % LOG_INTERVAL == 0 or step_i == 1:
                    print(f"  Epoch {epoch+1}/{epochs} [chunk0 batch {step_i}] "
                          f"loss={loss.item():.4f} avg_loss={running_avg:.4f}")
            for chunk_idx, chunk in enumerate(chunk_iter):
                np.random.shuffle(chunk)
                for start in range(0, len(chunk), batch_size):
                    batch = chunk[start : start + batch_size]
                    loss, B = self._run_one_batch(batch, criterion)
                    if loss is None:
                        continue
                    optimizer.zero_grad()
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                    optimizer.step()
                    epoch_loss += loss.item()
                    n_batch += 1
                    step_i += 1
                    if step_i % LOG_INTERVAL == 0:
                        print(f"  Epoch {epoch+1}/{epochs} [chunk{chunk_idx+1} batch {step_i}] "
                              f"loss={loss.item():.4f} avg_loss={epoch_loss/n_batch:.4f}")
            train_avg = epoch_loss / max(n_batch, 1)
            test_loss, test_n = self._eval_test(test_samples, criterion)
            print(f"Epoch {epoch+1}/{epochs} 完成 | 训练损失: {train_avg:.4f} | 测试集损失: {test_loss:.4f} (样本数 {test_n})")
            if epoch < epochs - 1:
                chunk_iter = iter_behavior_chunks(
                    BEHAVIORS_FILE, self.news_data, chunk_size=chunk_size, max_lines=max_behaviors
                )
                _ = next(chunk_iter)

    def recommend(self, user_id, candidate_news_ids, top_n=10, return_scores=False):
        """对候选新闻打分并返回 top_n。return_scores=True 时返回 [(news_id, score), ...]，便于外部重排。"""
        cands = [nid for nid in candidate_news_ids if nid in self.news_data][:500]
        if not cands:
            return [] if not return_scores else []
        if not candidate_news_ids or user_id not in self.user_history:
            out = cands[:top_n]
            return out if not return_scores else [(nid, 0.0) for nid in out]
        history_ids = []
        for hist_ids, _ in self.user_history[user_id]:
            history_ids.extend(hist_ids)
        seen = set()
        history_ids = [x for x in reversed(history_ids) if x not in seen and not seen.add(x)][-MAX_HISTORY:]
        if not history_ids:
            out = cands[:top_n]
            return out if not return_scores else [(nid, 0.0) for nid in out]
        self.model.eval()
        with torch.no_grad():
            hist_title, hist_cat, hist_subcat, hist_entity = self._tensorize_news_batch(history_ids)
            hist_title = hist_title.unsqueeze(0).expand(len(cands), -1, -1)
            hist_cat = hist_cat.unsqueeze(0).expand(len(cands), -1)
            hist_subcat = hist_subcat.unsqueeze(0).expand(len(cands), -1)
            hist_entity = hist_entity.unsqueeze(0).expand(len(cands), -1, -1)
            cand_title, cand_cat, cand_subcat, cand_entity = self._tensorize_news_batch(cands)
            hist_mask = torch.zeros(1, len(history_ids), dtype=torch.bool, device=self.device)
            hist_mask = hist_mask.expand(len(cands), -1)
            logits = self.model(
                hist_title, hist_cat, hist_subcat, hist_entity,
                cand_title, cand_cat, cand_subcat, cand_entity, hist_mask
            )
            scores = logits.cpu().numpy().flatten()
        order = np.argsort(-scores)[:top_n]
        if return_scores:
            return [(cands[i], float(scores[i])) for i in order]
        return [cands[i] for i in order]

    def save(self, path=SAVE_PATH):
        state = {
            "model": self.model.state_dict(),
            "config": self.config,
            "vocab": self.vocab,
            "category2id": self.category2id,
            "subcategory2id": self.subcategory2id,
            "news_data": self.news_data,
            "entity_embeds": self.entity_embeds,
        }
        torch.save(state, path)
        print(f"已保存到 {path}")

    def load(self, path=SAVE_PATH):
        state = torch.load(path, map_location=self.device, weights_only=False)
        self.vocab = state["vocab"]
        self.category2id = state["category2id"]
        self.subcategory2id = state["subcategory2id"]
        self.news_data = state["news_data"]
        self.entity_embeds = state["entity_embeds"]
        self.config = state["config"]
        self.build_model()
        self.model.load_state_dict(state["model"])
        print(f"已从 {path} 加载")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MIND 神经新闻推荐训练")
    parser.add_argument("--full", action="store_true", help="全量数据训练（不限制 behavior 条数）")
    parser.add_argument("--epochs", type=int, default=EPOCHS, help=f"训练轮数，默认 {EPOCHS}")
    parser.add_argument("--save", type=str, default=SAVE_PATH, help=f"模型保存路径，默认 {SAVE_PATH}")
    args = parser.parse_args()

    system = MindRecommenderSystem()
    system.load_entity_embeddings()
    system.load_news()
    max_lines = None if args.full else MAX_BEHAVIORS_TRAIN
    system.load_behaviors(max_lines=max_lines)
    system.build_model()
    if system.user_history:
        print("用户画像示例:", system.get_user_profile(list(system.user_history.keys())[0]))
    print("开始训练...", "(全量数据)" if args.full else f"(约 {max_lines} 条行为)")
    system.train(epochs=args.epochs, max_behaviors=max_lines)
    system.save(args.save)
    if system.user_history:
        uid = list(system.user_history.keys())[0]
        cands = list(system.news_data.keys())[:100]
        rec = system.recommend(uid, cands, top_n=5)
        print("推荐示例:", rec)
