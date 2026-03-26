# -*- coding: utf-8 -*-
"""
MIND 数据导入 MySQL 脚本（单脚本完成建库、建表、导入）
连接：localhost:3306，用户 root，密码 123456
"""

import os
import re
import json
import argparse
from collections import defaultdict

# 默认数据目录与文件
DATA_DIR = os.environ.get("MIND_DATA_DIR", "datal")
NEWS_TSV = os.path.join(DATA_DIR, "news.tsv")
BEHAVIORS_TSV = os.path.join(DATA_DIR, "behaviors.tsv")

# MySQL 配置
MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "123456",
    "charset": "utf8mb4",
}
DB_NAME = "news_recommend"
NEWS_CHUNK_SIZE = 5000
BEHAVIOR_INSERT_BATCH_SIZE = 5000


def parse_entities_json(s):
    if not s or s.strip() in ("[]", ""):
        return []
    try:
        arr = json.loads(s)
        return [item.get("WikidataId") for item in arr if isinstance(item, dict) and item.get("WikidataId")]
    except Exception:
        return []


def get_connection(use_db=True):
    try:
        import pymysql
    except ImportError:
        raise SystemExit("请安装 pymysql: pip install pymysql")
    kwargs = {**MYSQL_CONFIG, "cursorclass": pymysql.cursors.DictCursor}
    if use_db:
        kwargs["database"] = DB_NAME
    return pymysql.connect(**kwargs)


def create_database_and_tables(conn):
    with conn.cursor() as cur:
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.commit()
    conn.select_db(DB_NAME)
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS `news` (
                `news_id` VARCHAR(32) NOT NULL PRIMARY KEY,
                `category` VARCHAR(64) NOT NULL DEFAULT '',
                `subcategory` VARCHAR(128) NOT NULL DEFAULT '',
                `title` TEXT,
                `abstract` TEXT,
                `url` VARCHAR(512) DEFAULT '',
                `entity_ids` JSON COMMENT 'WikidataId list',
                `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                KEY `idx_category` (`category`),
                KEY `idx_subcategory` (`subcategory`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS `user_history` (
                `user_id` VARCHAR(32) NOT NULL PRIMARY KEY,
                `news_ids` JSON NOT NULL COMMENT '用户历史点击的新闻 ID 列表，按时间顺序',
                `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        conn.commit()
    print("数据库与表已创建/已存在。")


def import_news(conn, news_tsv, limit=None):
    if not os.path.isfile(news_tsv):
        print(f"跳过新闻导入：未找到 {news_tsv}")
        return 0
    conn.select_db(DB_NAME)
    total = 0
    chunk = []
    with open(news_tsv, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if limit and idx >= limit:
                break
            parts = line.strip().split("\t")
            if len(parts) < 6:
                continue
            news_id = parts[0][:32]
            category = (parts[1] or "")[:64]
            subcategory = (parts[2] or "")[:128]
            title = (parts[3] or "")[:65535]
            abstract = (parts[4] or "")[:65535]
            url = (parts[5] or "")[:512]
            title_ent = parse_entities_json(parts[6]) if len(parts) > 6 else []
            abstract_ent = parse_entities_json(parts[7]) if len(parts) > 7 else []
            entity_ids = json.dumps(list(dict.fromkeys(title_ent + abstract_ent))[:20])
            chunk.append((news_id, category, subcategory, title, abstract, url, entity_ids))
            if len(chunk) >= NEWS_CHUNK_SIZE:
                with conn.cursor() as cur:
                    cur.executemany(
                        """INSERT IGNORE INTO `news` (`news_id`,`category`,`subcategory`,`title`,`abstract`,`url`,`entity_ids`)
                           VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                        chunk,
                    )
                    conn.commit()
                total += len(chunk)
                print(f"  新闻已导入 {total} 条...")
                chunk = []
        if chunk:
            with conn.cursor() as cur:
                cur.executemany(
                    """INSERT IGNORE INTO `news` (`news_id`,`category`,`subcategory`,`title`,`abstract`,`url`,`entity_ids`)
                       VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                    chunk,
                )
                conn.commit()
            total += len(chunk)
    print(f"新闻导入完成：共 {total} 条（分块 INSERT IGNORE）。")
    return total


def import_behaviors(conn, behaviors_tsv, news_ids_set, limit=None):
    if not os.path.isfile(behaviors_tsv):
        print(f"跳过行为导入：未找到 {behaviors_tsv}")
        return 0
    from datetime import datetime
    print("行为导入：先完整读取文件并按用户整理点击顺序，读完后才会分批写入 MySQL，请耐心等待...")
    user_events = defaultdict(list)
    line_count = 0
    with open(behaviors_tsv, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if limit and i >= limit:
                break
            line_count += 1
            if line_count % 50000 == 0:
                print(f"  行为文件已读取 {line_count} 行...")
            parts = line.strip().split("\t")
            if len(parts) < 4:
                continue
            user_id = parts[1].strip()[:32]
            ts_str = parts[2].strip()
            history_raw = (parts[3] or "").split()
            try:
                dt = datetime.strptime(ts_str, "%m/%d/%Y %I:%M:%S %p")
                t = dt.timestamp()
            except Exception:
                t = float(i)
            for h in history_raw:
                if h in news_ids_set:
                    user_events[user_id].append((h, t - 10000))
    print("文件读取完毕，正在按用户去重排序...")
    user_seq = {}
    for uid, events in user_events.items():
        seen = {}
        for nid, tm in sorted(events, key=lambda x: x[1]):
            seen[nid] = tm
        order = sorted(seen.items(), key=lambda x: x[1])
        user_seq[uid] = [nid for nid, _ in order]
    conn.select_db(DB_NAME)
    with conn.cursor() as cur:
        cur.execute("DELETE FROM `user_history`")
        conn.commit()
    print("开始写入 MySQL（user_history，每用户一行）...")
    batch = []
    total = 0
    for uid, nids in user_seq.items():
        if not nids:
            continue
        batch.append((uid, json.dumps(nids)))
        if len(batch) >= BEHAVIOR_INSERT_BATCH_SIZE:
            with conn.cursor() as cur:
                cur.executemany(
                    "INSERT INTO `user_history` (`user_id`,`news_ids`) VALUES (%s,%s)",
                    batch,
                )
                conn.commit()
            total += len(batch)
            print(f"  用户历史已导入 {total} 个用户...")
            batch = []
    if batch:
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO `user_history` (`user_id`,`news_ids`) VALUES (%s,%s)",
                batch,
            )
            conn.commit()
    print(f"用户历史导入完成：共 {len(user_seq)} 个用户（每用户一行，news_ids 为历史新闻 ID 列表）。")
    return total


def main():
    parser = argparse.ArgumentParser(description="MIND 数据导入 MySQL")
    parser.add_argument("--news-limit", type=int, default=None, help="最多导入新闻条数，默认全部")
    parser.add_argument("--behaviors-limit", type=int, default=None, help="最多导入行为行数，默认全部")
    parser.add_argument("--skip-news", action="store_true", help="跳过新闻导入")
    parser.add_argument("--skip-behaviors", action="store_true", help="跳过行为导入")
    args = parser.parse_args()

    print("连接 MySQL...")
    conn = get_connection(use_db=False)
    try:
        create_database_and_tables(conn)
        news_ids_set = set()
        if not args.skip_news:
            import_news(conn, NEWS_TSV, limit=args.news_limit)
            conn.select_db(DB_NAME)
            with conn.cursor() as cur:
                cur.execute("SELECT news_id FROM news")
                news_ids_set = {r["news_id"] for r in cur.fetchall()}
        else:
            conn.select_db(DB_NAME)
            with conn.cursor() as cur:
                cur.execute("SELECT news_id FROM news")
                news_ids_set = {r["news_id"] for r in cur.fetchall()}
        if not args.skip_behaviors:
            import_behaviors(conn, BEHAVIORS_TSV, news_ids_set, limit=args.behaviors_limit)
    finally:
        conn.close()
    print("全部完成。")


if __name__ == "__main__":
    main()
