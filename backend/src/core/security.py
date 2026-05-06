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


def verify_telegram_init_data(init_data: str) -> dict:
    """Verify Telegram WebApp initData"""
    try:
        parsed = dict(item.split("=", 1) for item in init_data.split("&"))
        check_hash = parsed.pop("hash", "")
        data_check = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))

        secret_key = hmac.new(b"WebAppData", settings.TELEGRAM_BOT_TOKEN.encode(), hashlib.sha256).digest()
        computed = hmac.new(secret_key, data_check.encode(), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(computed, check_hash):
            raise ValueError("Invalid hash")

        user_data = json.loads(parsed.get("user", "{}"))
        return user_data
    except Exception as e:
        logger.error("Telegram auth error", error=str(e))
        raise HTTPException(status_code=401, detail="Invalid Telegram auth data")


async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_token(credentials.credentials)
    return payload
