"""
Security utilities: JWT, password hashing, Telegram auth
"""
import hashlib
import hmac
import json
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.core.config import settings
from src.core.logger import logger
from urllib.parse import unquote, parse_qsl
from time import time

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as e:
        logger.error("JWT decode error", error=str(e))
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def verify_telegram_init_data(init_data: str, bot_token: str) -> dict:
    """
    Правильная проверка по документации Telegram.
    Возвращает данные пользователя или бросает ValueError.
    """
    # 1. Парсим initData как query string
    parsed = dict(parse_qsl(init_data, strict_parsing=True))
    
    hash_from_telegram = parsed.pop("hash", None)
    if not hash_from_telegram:
        raise ValueError("No hash in initData")
    
    # 2. Проверяем свежесть (не старше 24 часов)
    auth_date = int(parsed.get("auth_date", 0))
    if time() - auth_date > 86400:
        raise ValueError("initData expired")
    
    # 3. Сортируем оставшиеся поля по алфавиту и строим строку
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed.items())
    )
    
    # 4. HMAC — ключ это HMAC(bot_token, "WebAppData"), а НЕ сам токен!
    secret_key = hmac.new(
        b"WebAppData",          # <-- вот главная ошибка у большинства
        bot_token.encode(),
        hashlib.sha256
    ).digest()
    
    expected_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(expected_hash, hash_from_telegram):
        raise ValueError("Invalid Telegram auth data")
    
    # 5. Возвращаем распарсенного юзера
    user_data = json.loads(unquote(parsed["user"]))
    return user_data


async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_token(credentials.credentials)
    return payload
