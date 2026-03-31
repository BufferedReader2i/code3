#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
独立脚本：创建 user_profile 表并初始化用户画像数据。

Usage:
  python add_user_profile_table.py

此脚本用于：
1. 创建 user_profile 数据库表
2. 初始化所有用户的画像数据到数据库
"""

import json
from collections import Counter, defaultdict

from backend.db import get_connection

# 引入推荐服务以获取画像计算所需的数据
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services import RecommendationService


def create_user_profile_table():
    """创建 user_profile 表"""
    conn = get_connection()
    if not conn:
        print("错误：无法连接数据库")
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS `user_profile` (
                  `user_id` VARCHAR(64) NOT NULL PRIMARY KEY,
                  `categories_json` JSON NOT NULL,
                  `subcategories_json` JSON NOT NULL,
                  `history_count` INT NOT NULL DEFAULT 0,
                  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            print("表 user_profile 创建成功（或已存在）")
        conn.commit()
        return True
    except Exception as e:
        print(f"创建表时出错: {e}")
        return False
    finally:
        conn.close()


def compute_user_profile(service, user_id, recency_decay=0.85, smooth_threshold=3.0):
    """
    计算用户画像（从 services.py 中的逻辑提取）
    返回与数据库存储格式兼容的字典
    """
    ordered = service._get_ordered_history(user_id)
    ordered = [nid for nid in ordered if nid in service.rec.news_data]
    total = len(ordered)
    
    if total == 0:
        return {
            "categories": [],
            "subcategories": [],
            "history_count": 0
        }
    
    L = len(ordered)
    weights = [recency_decay ** (L - 1 - i) for i in range(L)]
    weight_sum = sum(weights)
    
    cat_weighted = defaultdict(float)
    subcat_weighted = defaultdict(float)
    
    # 批量获取用户对历史新闻的最新事件
    latest_events = service._get_latest_events_for_news(user_id, ordered)
    
    # 权重乘数
    EVENT_WEIGHTS = {
        "like": 1.5,
        "favorite": 2.0,
        "dislike": -0.2,
        "not_interested": -0.5,
    }
    DWELL_THRESHOLD_MS = 2000
    DWELL_BOOST = 1.2
    
    for nid, w in zip(ordered, weights):
        info = service.news_info.get(nid) or service.rec.news_data.get(nid, {})
        c = info.get("category", "N/A")
        s = info.get("subcategory", "N/A") or "N/A"
        
        # 根据事件类型调整权重
        latest = latest_events.get(nid)
        if latest:
            event_type = latest.get("event_type", "")
            if event_type in EVENT_WEIGHTS:
                w *= EVENT_WEIGHTS[event_type]
            dwell_ms = latest.get("dwell_ms", 0)
            if dwell_ms and dwell_ms > DWELL_THRESHOLD_MS:
                w *= DWELL_BOOST
        
        cat_weighted[c] += w
        subcat_weighted[s] += w
    
    global_cat = getattr(service, "_global_cat_dist", {}) or {}
    global_subcat = getattr(service, "_global_subcat_dist", {}) or {}
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
        "categories": categories,
        "subcategories": subcategories,
        "history_count": total
    }


def save_user_profile_to_db(user_id, profile):
    """保存用户画像到数据库"""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO user_profile (user_id, categories_json, subcategories_json, history_count)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    categories_json = VALUES(categories_json),
                    subcategories_json = VALUES(subcategories_json),
                    history_count = VALUES(history_count)
            """, (
                user_id,
                json.dumps(profile["categories"], ensure_ascii=False),
                json.dumps(profile["subcategories"], ensure_ascii=False),
                profile["history_count"]
            ))
        conn.commit()
        return True
    except Exception as e:
        print(f"保存用户 {user_id} 画像时出错: {e}")
        return False
    finally:
        conn.close()


def get_all_user_ids():
    """获取所有用户ID"""
    conn = get_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT username FROM users")
            return [row["username"] for row in cur.fetchall()]
    finally:
        conn.close()


def load_profile_from_db(user_id):
    """从数据库加载用户画像"""
    conn = get_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT categories_json, subcategories_json, history_count 
                FROM user_profile WHERE user_id = %s
            """, (user_id,))
            row = cur.fetchone()
            if row:
                return {
                    "user_id": user_id,
                    "categories": json.loads(row["categories_json"]),
                    "subcategories": json.loads(row["subcategories_json"]),
                    "history_count": row["history_count"]
                }
            return None
    finally:
        conn.close()


def init_all_profiles():
    """初始化所有用户的画像到数据库"""
    print("正在初始化推荐服务...")
    service = RecommendationService()
    
    print("获取所有用户...")
    user_ids = get_all_user_ids()
    print(f"找到 {len(user_ids)} 个用户")
    
    success_count = 0
    for i, user_id in enumerate(user_ids):
        print(f"处理用户 {i+1}/{len(user_ids)}: {user_id}")
        profile = compute_user_profile(service, user_id)
        if save_user_profile_to_db(user_id, profile):
            success_count += 1
    
    print(f"\n完成！成功保存 {success_count}/{len(user_ids)} 个用户画像")


def main():
    print("=" * 50)
    print("用户画像数据库初始化脚本")
    print("=" * 50)
    
    # 1. 创建表
    print("\n[1/2] 创建 user_profile 表...")
    if not create_user_profile_table():
        print("创建表失败，退出")
        return
    
    # 2. 初始化数据
    print("\n[2/2] 初始化用户画像数据...")
    init_all_profiles()
    
    print("\n完成！")


if __name__ == "__main__":
    main()
