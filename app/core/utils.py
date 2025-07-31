# 6. Sensitive data exposure: Pydantic schema-da maxfiy maydonlarni yashirish uchun yordamchi
from pydantic import BaseModel

class SafeUserOut(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    # Parol va boshqa maxfiy maydonlar yo'q!
    class Config:
        orm_mode = True

# 7. IDOR (faqat egasi yoki admin kirishi uchun util)
def is_owner_or_admin(current_user_id: int, resource_owner_id: int, is_admin: bool = False) -> bool:
    return is_admin or (current_user_id == resource_owner_id)

# 8. Fayl yuklash va path traversal xavfsizligi uchun util
import os
def secure_filename(filename: str) -> str:
    # Faqat harf, raqam va pastki chiziqdan iborat nomga ruxsat
    keepcharacters = ('.','_')
    return "".join(c for c in filename if c.isalnum() or c in keepcharacters).rstrip()

def is_safe_path(basedir: str, path: str) -> bool:
    # Fayl yo'li basedir ichida ekanligini tekshiradi
    return os.path.realpath(path).startswith(os.path.realpath(basedir))
# 5. Oddiy rate limiting (namuna, prod uchun Redis tavsiya etiladi)
from fastapi import Request
import time

_RATE_LIMIT = {}
RATE_LIMIT_WINDOW = 60  # soniya
RATE_LIMIT_MAX = 30    # 1 daqiqada 30 so'rov

def is_rate_limited(request: Request) -> bool:
    ip = request.client.host
    now = int(time.time())
    window = now // RATE_LIMIT_WINDOW
    key = f"{ip}:{window}"
    count = _RATE_LIMIT.get(key, 0)
    if count >= RATE_LIMIT_MAX:
        return True
    _RATE_LIMIT[key] = count + 1
    return False

from fastapi import Request, status
from fastapi.responses import JSONResponse
import re
import html
from passlib.context import CryptContext
import jwt
import os
from datetime import datetime, timedelta

# 1. Global exception handler (kutilmagan xatoliklar uchun)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Kutilmagan xatolik yuz berdi", "error": str(exc)},
    )

# 2. XSS va boshqa input hujumlariga qarshi sanitizatsiya
def sanitize_str(value: str) -> str:
    # HTML belgilarini escape qilish va xavfli belgilarni olib tashlash
    value = html.escape(value)
    value = re.sub(r'[<>"\'`]', '', value)
    return value.strip()

# 3. Parolni xavfsiz saqlash uchun xeshlash va tekshirish
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# 4. JWT token generatsiya va tekshirish (API uchun)
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
