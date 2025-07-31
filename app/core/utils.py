"""
Utility functions for the FastAPI application.
Umumiy yordamchi funksiyalar va xavfsizlik choralari.
"""

import re
import json
import uuid
import hashlib
import html
import os
import time
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Union
from decimal import Decimal
from email.utils import parseaddr
import secrets
import string
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt, JWTError
from fastapi import Request, status, HTTPException
from fastapi.responses import JSONResponse


# JWT va parol konfiguratsiyasi
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Rate limiting
_RATE_LIMIT = {}
RATE_LIMIT_WINDOW = 60  # soniya
RATE_LIMIT_MAX = 30    # 1 daqiqada 30 so'rov


class Utils:
    """Umumiy utility funksiyalar."""
    
    @staticmethod
    def generate_uuid() -> str:
        """UUID yaratish."""
        return str(uuid.uuid4())
    
    @staticmethod
    def generate_random_string(length: int = 8) -> str:
        """Tasodifiy string yaratish."""
        letters = string.ascii_lowercase + string.digits
        return ''.join(secrets.choice(letters) for _ in range(length))
    
    @staticmethod
    def slugify(text: str) -> str:
        """Textni URL-friendly slug ga aylantirish."""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '-', text)
        return text.strip('-')
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Email validatsiya."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def format_phone(phone: str) -> str:
        """Telefon raqamini formatlash."""
        phone = re.sub(r'\D', '', phone)
        if len(phone) == 9:  # Uzbek phone format
            phone = '+998' + phone
        elif len(phone) == 12 and phone.startswith('998'):
            phone = '+' + phone
        return phone
    
    @staticmethod
    def mask_email(email: str) -> str:
        """Emailni masklash (privacy uchun)."""
        if '@' not in email:
            return email
        username, domain = email.split('@', 1)
        if len(username) <= 2:
            masked_username = username
        else:
            masked_username = username[0] + '*' * (len(username) - 2) + username[-1]
        return f"{masked_username}@{domain}"
    
    @staticmethod
    def calculate_pagination(page: int, per_page: int, total_count: int) -> Dict[str, Any]:
        """Pagination ma'lumotlarini hisoblash."""
        total_pages = (total_count + per_page - 1) // per_page
        offset = (page - 1) * per_page
        
        return {
            "page": page,
            "per_page": per_page,
            "total_count": total_count,
            "total_pages": total_pages,
            "offset": offset,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        }


class SecurityUtils:
    """Xavfsizlik utility funksiyalar."""
    
    @staticmethod
    def sanitize_str(value: str) -> str:
        """XSS himoyasi uchun string sanitization."""
        if not value:
            return ""
        # HTML belgilarini escape qilish
        value = html.escape(value)
        # Xavfli belgilarni olib tashlash
        value = re.sub(r'[<>"\'`]', '', value)
        return value.strip()
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Parolni hash qilish."""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Parolni tekshirish."""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: timedelta = None):
        """JWT token yaratish."""
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def decode_access_token(token: str):
        """JWT tokenni decode qilish."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    @staticmethod
    def secure_filename(filename: str) -> str:
        """Xavfsiz fayl nomi yaratish."""
        keepcharacters = ('.', '_')
        return "".join(c for c in filename if c.isalnum() or c in keepcharacters).rstrip()
    
    @staticmethod
    def is_safe_path(basedir: str, path: str) -> bool:
        """Fayl yo'li xavfsizligini tekshirish."""
        return os.path.realpath(path).startswith(os.path.realpath(basedir))
    
    @staticmethod
    def is_owner_or_admin(current_user_id: int, resource_owner_id: int, is_admin: bool = False) -> bool:
        """IDOR himoyasi uchun."""
        return is_admin or (current_user_id == resource_owner_id)


class RateLimiter:
    """Rate limiting funksiyalar."""
    
    @staticmethod
    def is_rate_limited(request: Request) -> bool:
        """Rate limiting tekshiruvi."""
        ip = request.client.host
        now = int(time.time())
        window = now // RATE_LIMIT_WINDOW
        key = f"{ip}:{window}"
        count = _RATE_LIMIT.get(key, 0)
        if count >= RATE_LIMIT_MAX:
            return True
        _RATE_LIMIT[key] = count + 1
        return False


class ResponseFormatter:
    """API response formatlash."""
    
    @staticmethod
    def success(data: Any = None, message: str = "Success") -> Dict[str, Any]:
        """Muvaffaqiyatli response."""
        return {
            "success": True,
            "message": message,
            "data": data
        }
    
    @staticmethod
    def error(message: str = "Error", error_code: str = None, details: Any = None) -> Dict[str, Any]:
        """Xato response."""
        response = {
            "success": False,
            "message": message
        }
        if error_code:
            response["error_code"] = error_code
        if details:
            response["details"] = details
        return response
    
    @staticmethod
    def paginated(data: List[Any], pagination: Dict[str, Any], message: str = "Success") -> Dict[str, Any]:
        """Pagination bilan response."""
        return {
            "success": True,
            "message": message,
            "data": data,
            "pagination": pagination
        }


# Global exception handler
async def global_exception_handler(request: Request, exc: Exception):
    """Kutilmagan xatoliklar uchun global handler."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ResponseFormatter.error("Kutilmagan xatolik yuz berdi", "INTERNAL_ERROR", str(exc)),
    )


# Xavfsiz Pydantic schema misoli
class SafeUserOut(BaseModel):
    """Xavfsiz foydalanuvchi ma'lumotlari (parolsiz)."""
    id: int
    username: str
    email: str
    is_active: bool
    
    class Config:
        from_attributes = True
