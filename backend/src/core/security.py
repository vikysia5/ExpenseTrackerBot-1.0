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
    if "sub" in to_encode and not isinstance(to_encode["sub"], str):
        to_encode["sub"] = str(to_encode["sub"])
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
    logger.info("Verifying Telegram init_data", bot_token_len=len(bot_token) if bot_token else 0)
    
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN not configured")
    
    # 1. Парсим initData как query string
    try:
        parsed = dict(parse_qsl(init_data, strict_parsing=False))
        logger.info("Parsed init_data", keys=list(parsed.keys()))
    except Exception as e:
        logger.error("Failed to parse init_data", error=str(e))
        raise ValueError(f"Invalid init_data format: {e}")
    
    hash_from_telegram = parsed.pop("hash", None)
    if not hash_from_telegram:
        logger.error("No hash in initData")
        raise ValueError("No hash in initData")
    
    logger.info("Hash from Telegram", hash_len=len(hash_from_telegram))
    
    # 2. Проверяем свежесть (не старше 24 часов)
    auth_date = int(parsed.get("auth_date", 0))
    current_time = time()
    time_diff = current_time - auth_date
    logger.info("Time check", auth_date=auth_date, current_time=current_time, diff=time_diff)
    
    if time_diff > 86400:
        logger.error("initData expired", diff_seconds=time_diff)
        raise ValueError("initData expired")
    
    # 3. Сортируем оставшиеся поля по алфавиту и строим строку
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed.items())
    )
    logger.info("Data check string", string_len=len(data_check_string), first_100=data_check_string[:100])
    
    # 4. HMAC — секретный ключ из WebAppData и bot_token
    secret_key = hmac.new(
        b"WebAppData",
        bot_token.encode(),
        hashlib.sha256
    ).digest()
    
    expected_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    logger.info("Hash comparison", expected=expected_hash[:20]+"...", received=hash_from_telegram[:20]+"...", match=hmac.compare_digest(expected_hash, hash_from_telegram))
    
    if not hmac.compare_digest(expected_hash, hash_from_telegram):
        logger.error("Telegram hash mismatch", expected=expected_hash, received=hash_from_telegram)
        raise ValueError("Invalid Telegram auth data")
    
    # 5. Возвращаем распарсенного юзера
    try:
        user_data = json.loads(unquote(parsed["user"]))
        logger.info("Telegram user parsed", user_id=user_data.get("id"))
        return user_data
    except Exception as e:
        logger.error("Failed to parse user from init_data", error=str(e))
        raise ValueError(f"Invalid user data: {e}")


async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_token(credentials.credentials)
    return payload
