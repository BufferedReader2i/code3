# -*- coding: utf-8 -*-
"""简单认证：密码哈希 + 内存 token 会话（无 JWT 依赖）"""

import hashlib
import secrets
import time
from typing import Optional, Tuple

# 内存存储：token -> (username, role, expiry)
_sessions: dict = {}
TOKEN_EXPIRE_HOURS = 24


def _hash_password(password: str, salt: str = "") -> str:
    if not salt:
        salt = "news_rec_salt"
    return hashlib.sha256((password + salt).encode()).hexdigest()


def verify_password(password: str, stored_hash: str) -> bool:
    return _hash_password(password) == stored_hash


def hash_password(password: str) -> str:
    return _hash_password(password)


def create_token(username: str, role: str) -> str:
    token = secrets.token_urlsafe(32)
    _sessions[token] = (username, role, time.time() + TOKEN_EXPIRE_HOURS * 3600)
    return token


def get_user_from_token(token: str) -> Optional[Tuple[str, str]]:
    if not token:
        return None
    t = _sessions.get(token)
    if not t or time.time() > t[2]:
        if t:
            _sessions.pop(token, None)
        return None
    return (t[0], t[1])


def logout_token(token: str) -> None:
    _sessions.pop(token, None)
