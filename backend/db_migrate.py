#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MySQL schema migration (idempotent).

Usage:
  python -m backend.db_migrate
or:
  python backend/db_migrate.py

This file is intentionally standalone so DB changes are easy to review.
"""

from __future__ import annotations

import json
import time
from typing import Optional

from backend.db import get_connection

import os


def _exec(conn, sql: str, args: Optional[tuple] = None) -> None:
    with conn.cursor() as cur:
        cur.execute(sql, args or ())


def _table_exists(conn, table_name: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
              AND table_name = %s
            """,
            (table_name,),
        )
        row = cur.fetchone()
        return int(row["cnt"] if isinstance(row, dict) else list(row.values())[0]) > 0


def migrate() -> None:
    conn = get_connection()
    if not conn:
        raise SystemExit("数据库不可用：请检查 pymysql 安装与 backend/db.py 配置")

    try:
        try:
            conn.ping(reconnect=True)
        except Exception:
            pass

        # ---------- Core tables (ensure exist) ----------
        _exec(
            conn,
            """
            CREATE TABLE IF NOT EXISTS `users` (
              `username` VARCHAR(64) NOT NULL PRIMARY KEY,
              `password_hash` VARCHAR(128) NOT NULL,
              `role` VARCHAR(16) NOT NULL DEFAULT 'user',
              `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              KEY `idx_role` (`role`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
        )

        _exec(
            conn,
            """
            CREATE TABLE IF NOT EXISTS `news` (
              `news_id` VARCHAR(64) NOT NULL PRIMARY KEY,
              `category` VARCHAR(64) NOT NULL DEFAULT '',
              `subcategory` VARCHAR(128) NOT NULL DEFAULT '',
              `title` TEXT,
              `abstract` TEXT,
              `body` LONGTEXT,
              `url` VARCHAR(512) DEFAULT '',
              `entity_ids` JSON,
              `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              KEY `idx_category` (`category`),
              KEY `idx_subcategory` (`subcategory`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
        )

        _exec(
            conn,
            """
            CREATE TABLE IF NOT EXISTS `user_history` (
              `user_id` VARCHAR(64) NOT NULL PRIMARY KEY,
              `news_ids` JSON NOT NULL,
              `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
        )

        # ---------- New tables for multi-feedback loop ----------
        _exec(
            conn,
            """
            CREATE TABLE IF NOT EXISTS `user_events` (
              `id` BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
              `user_id` VARCHAR(64) NOT NULL,
              `news_id` VARCHAR(64) NOT NULL,
              `event_type` VARCHAR(32) NOT NULL,
              `ts` BIGINT NOT NULL,
              `dwell_ms` INT NOT NULL DEFAULT 0,
              `extra_json` JSON,
              KEY `idx_user_ts` (`user_id`, `ts`),
              KEY `idx_news_ts` (`news_id`, `ts`),
              KEY `idx_type_ts` (`event_type`, `ts`),
              KEY `idx_user_type_ts` (`user_id`, `event_type`, `ts`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
        )

        _exec(
            conn,
            """
            CREATE TABLE IF NOT EXISTS `user_favorites` (
              `user_id` VARCHAR(64) NOT NULL,
              `news_id` VARCHAR(64) NOT NULL,
              `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY (`user_id`, `news_id`),
              KEY `idx_news` (`news_id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
        )

        # Keep status separate to avoid altering existing `news` schema in-place.
        _exec(
            conn,
            """
            CREATE TABLE IF NOT EXISTS `news_status` (
              `news_id` VARCHAR(64) NOT NULL PRIMARY KEY,
              `status` VARCHAR(16) NOT NULL DEFAULT 'active',
              `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              KEY `idx_status` (`status`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
        )

        _exec(
            conn,
            """
            CREATE TABLE IF NOT EXISTS `user_clusters` (
              `user_id` VARCHAR(64) NOT NULL PRIMARY KEY,
              `cluster_id` INT NOT NULL,
              `cluster_name` VARCHAR(64) NOT NULL DEFAULT '',
              `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              KEY `idx_cluster` (`cluster_id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
        )

        conn.commit()

        # ---------- Optional backfill: user_history -> user_events(click) ----------
        # Disabled by default to avoid scanning potentially huge user_events tables.
        # Enable explicitly with env: MYSQL_BACKFILL_EVENTS=1
        if os.environ.get("MYSQL_BACKFILL_EVENTS", "").strip() == "1":
            if _table_exists(conn, "user_history") and _table_exists(conn, "user_events"):
                now_ms = int(time.time() * 1000)
                with conn.cursor() as cur:
                    cur.execute("SELECT user_id, news_ids FROM user_history")
                    rows = cur.fetchall()
                batch = []
                # Keep order by assigning increasing timestamps.
                for r in rows:
                    uid = r["user_id"]
                    raw = r["news_ids"]
                    ids = raw if isinstance(raw, list) else json.loads(raw or "[]")
                    for i, nid in enumerate(ids):
                        batch.append((uid, nid, "click", now_ms - (len(ids) - i) * 1000, 0, json.dumps({})))
                if batch:
                    with conn.cursor() as cur:
                        cur.executemany(
                            """
                            INSERT INTO user_events (user_id, news_id, event_type, ts, dwell_ms, extra_json)
                            VALUES (%s,%s,%s,%s,%s,%s)
                            """,
                            batch,
                        )
                    conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
    print("DB migration finished.")

