#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Ensure admin user exists in MySQL.

Usage:
  python -m backend.ensure_admin
"""

from backend.db import get_connection
from backend.auth import hash_password


def main():
    conn = get_connection()
    if not conn:
        raise SystemExit("数据库不可用")
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (username, password_hash, role)
                VALUES (%s, %s, 'admin')
                ON DUPLICATE KEY UPDATE
                  role='admin',
                  password_hash=VALUES(password_hash)
                """,
                ("admin", hash_password("admin123")),
            )
        conn.commit()
        with conn.cursor() as cur:
            cur.execute("SELECT username, role FROM users WHERE username=%s", ("admin",))
            print(cur.fetchone())
    finally:
        conn.close()


if __name__ == "__main__":
    main()

