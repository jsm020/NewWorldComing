"""
Security utilities for the FastAPI application.
Xavfsizlik choralar: SQL Injection, XSS, CSRF himoyasi va autentifikatsiya.
"""

import hashlib
import secrets
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from decouple import config
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import html


# JWT konfiguratsiyasi
SECRET_KEY = config('SECRET_KEY', default='your-secret-key-change-it-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# JWT Bearer
security = HTTPBearer()


class SecurityUtils:
    """Xavfsizlik uchun yordamchi funksiyalar."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Parolni hash qilish (bcrypt bilan)."""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Parolni tekshirish."""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """JWT token yaratish."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """JWT tokenni tekshirish."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    def sanitize_input(input_string: str) -> str:
        """XSS himoyasi uchun input sanitization."""
        if not input_string:
            return ""
        # HTML taglarini escape qilish
        sanitized = html.escape(input_string)
        # Script taglarini olib tashlash
        sanitized = re.sub(r'<script.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        # On-event handlerlarni olib tashlash
        sanitized = re.sub(r'on\w+="[^"]*"', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r"on\w+='[^']*'", '', sanitized, flags=re.IGNORECASE)
        return sanitized.strip()
    
    @staticmethod
    def validate_sql_input(input_string: str) -> bool:
        """SQL Injection himoyasi uchun input validatsiya."""
        if not input_string:
            return True
        
        # Xavfli SQL kalit so'zlarni tekshirish
        dangerous_patterns = [
            r'\b(DROP|DELETE|UPDATE|INSERT|ALTER|CREATE|TRUNCATE)\b',
            r'(--|#|/\*|\*/)',
            r'(\bunion\b|\bselect\b|\bwhere\b)',
            r'(\'|"|;|\|)',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, input_string, re.IGNORECASE):
                return False
        return True
    
    @staticmethod
    def generate_csrf_token() -> str:
        """CSRF token yaratish."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_secure_filename(filename: str) -> str:
        """Xavfsiz fayl nomi yaratish."""
        # Faqat ruxsat berilgan belgilarni qoldirish
        filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        # Uzunlikni cheklash
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:250] + ('.' + ext if ext else '')
        return filename


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """JWT tokendan foydalanuvchini olish."""
    token = credentials.credentials
    payload = SecurityUtils.verify_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"user_id": user_id, "payload": payload}


def validate_input_security(input_data: str) -> str:
    """Input ma'lumotlarni xavfsizlik tekshiruvidan o'tkazish."""
    if not SecurityUtils.validate_sql_input(input_data):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid input: potential SQL injection detected"
        )
    return SecurityUtils.sanitize_input(input_data)


# Rate limiting dekorator
def rate_limit(times: int, seconds: int):
    """Rate limiting dekorator."""
    def decorator(func):
        return limiter.limit(f"{times}/{seconds}second")(func)
    return decorator


# CORS konfiguratsiyasi uchun
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]

# Content Security Policy
CSP_HEADER = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: https:; "
    "font-src 'self' https:; "
    "connect-src 'self'; "
    "frame-ancestors 'none';"
)

# Convenience functions (aliases for SecurityUtils methods)
def hash_password(password: str) -> str:
    """Parolni hash qilish."""
    return SecurityUtils.hash_password(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Parolni tekshirish."""
    return SecurityUtils.verify_password(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """JWT token yaratish."""
    return SecurityUtils.create_access_token(data, expires_delta)

def decode_access_token(token: str) -> Dict[str, Any]:
    """JWT tokenni tekshirish (alias for verify_token)."""
    return SecurityUtils.verify_token(token)

def verify_token(token: str) -> Dict[str, Any]:
    """JWT tokenni tekshirish."""
    return SecurityUtils.verify_token(token)
