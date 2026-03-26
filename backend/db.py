# -*- coding: utf-8 -*-
"""MySQL 连接与配置（默认 localhost:3306, root/123456）"""

import os

MYSQL_CONFIG = {
    "host": os.environ.get("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.environ.get("MYSQL_PORT", "3306")),
    "user": os.environ.get("MYSQL_USER", "root"),
    "password": os.environ.get("MYSQL_PASSWORD", "123456"),
    "database": os.environ.get("MYSQL_DATABASE", "news_recommend"),
    "charset": "utf8mb4",
    "cursorclass": None,
    "connect_timeout": int(os.environ.get("MYSQL_CONNECT_TIMEOUT", "5")),
    "read_timeout": int(os.environ.get("MYSQL_READ_TIMEOUT", "30")),
    "write_timeout": int(os.environ.get("MYSQL_WRITE_TIMEOUT", "30")),
}


def get_cursor_class():
    try:
        import pymysql.cursors
        return pymysql.cursors.DictCursor
    except ImportError:
        return None


def get_connection():
    try:
        import pymysql
    except ImportError:
        return None
    cfg = {**MYSQL_CONFIG, "cursorclass": get_cursor_class()}
    try:
        return pymysql.connect(**cfg)
    except Exception:
        return None
