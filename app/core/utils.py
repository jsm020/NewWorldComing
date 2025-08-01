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
import asyncio
from getpass import getpass
import bcrypt
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
from tortoise import Tortoise

from config.tortoise_config import TORTOISE_ORM


# JWT va parol konfiguratsiyasi
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Rate limiting
_RATE_LIMIT = {}
RATE_LIMIT_WINDOW = 60  # soniya
RATE_LIMIT_MAX = 30    # 1 daqiqada 30 so'rov


async def create_superuser():
    """
    Django-style superuser yaratish commandi
    """
    # Tortoise ORM ni ishga tushirish
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()
    
    # Import qilish (circular import oldini olish uchun)
    from app.models.user import User
    from app.models.admin_security import AdminSecurity
    from app.services.telegram_bot import TelegramBotService
    
    print("🚀 SuperUser yaratish boshlandi...")
    print("=" * 50)
    
    # Foydalanuvchi ma'lumotlarini olish
    while True:
        username = input("👤 Username kiriting: ").strip()
        if username:
            # Mavjudligini tekshirish
            existing_user = await User.get_or_none(username=username)
            if existing_user:
                print(f"❌ '{username}' username allaqachon mavjud!")
                continue
            break
        print("❌ Username bo'sh bo'lishi mumkin emas!")
    
    while True:
        email = input("📧 Email kiriting: ").strip()
        if email and "@" in email:
            # Mavjudligini tekshirish  
            existing_email = await User.get_or_none(email=email)
            if existing_email:
                print(f"❌ '{email}' email allaqachon mavjud!")
                continue
            break
        print("❌ To'g'ri email kiriting!")
    
    while True:
        password = getpass("🔐 Parol kiriting: ")
        if len(password) >= 8:
            password_confirm = getpass("🔐 Parolni takrorlang: ")
            if password == password_confirm:
                break
            print("❌ Parollar mos emas!")
        else:
            print("❌ Parol kamida 8 ta belgidan iborat bo'lishi kerak!")
    
    full_name = input("👥 To'liq ism (ixtiyoriy): ").strip()
    
    try:
        # Parolni hash qilish
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        # Superuser yaratish
        user = await User.create(
            username=username,
            email=email,
            password_hash=hashed_password.decode('utf-8'),
            full_name=full_name or username,
            is_active=True,
            is_superuser=True,
            role='admin'
        )
        
        print(f"✅ SuperUser '{username}' muvaffaqiyatli yaratildi!")
        print("=" * 50)
        
        # 2FA sozlash taklifi
        print("\n🔐 2-Etapli Himoya (2FA) Sozlash")
        print("=" * 50)
        
        enable_2fa = input("❓ 2-etapli himoyani yoqmoqchimisiz? (ha/yo'q): ").strip().lower()
        
        if enable_2fa in ['ha', 'yes', 'y', '1', 'true']:
            print("\n📱 Telegram Bot orqali 2FA sozlash")
            print("-" * 30)
            
            # Bot token olish
            bot_token = None
            while True:
                bot_token = input("🤖 Telegram Bot Token kiriting: ").strip()
                if bot_token:
                    # Bot tokenini tekshirish
                    print("🔄 Bot ulanishini tekshiryapman...")
                    telegram_service = TelegramBotService(bot_token)
                    test_result = await telegram_service.test_bot_connection()
                    
                    if test_result["success"]:
                        bot_info = test_result["bot_info"]
                        print(f"✅ Bot ulanishi muvaffaqiyatli!")
                        print(f"🤖 Bot nomi: @{bot_info.get('username', 'Unknown')}")
                        print(f"📝 Bot tavsifi: {bot_info.get('first_name', 'Unknown')}")
                        break
                    else:
                        print(f"❌ Bot ulanishida xatolik: {test_result['message']}")
                        retry = input("🔄 Qayta urinib ko'rasizmi? (ha/yo'q): ").strip().lower()
                        if retry not in ['ha', 'yes', 'y', '1', 'true']:
                            print("⏩ 2FA sozlash bekor qilindi")
                            bot_token = None
                            break
                else:
                    print("❌ Bot token bo'sh bo'lishi mumkin emas!")
            
            if bot_token:
                # Chat ID olish
                print("\n💬 Telegram Chat ID sozlash")
                print("-" * 30)
                print("📋 Quyidagi usullardan birini tanlang:")
                print("1️⃣  Chat ID ni qo'lda kiriting")
                print("2️⃣  Bot ga '/start' xabar yuboring va ID avtomatik olinadi")
                
                chat_id_method = input("🔢 Usulni tanlang (1/2): ").strip()
                
                chat_id = None
                
                if chat_id_method == "1":
                    # Qo'lda kiritish
                    while True:
                        chat_id_input = input("💬 Chat ID kiriting: ").strip()
                        if chat_id_input:
                            # Chat ID ni tekshirish
                            print("🔄 Chat ID ni tekshiryapman...")
                            test_message = "🔐 2FA Test - Chat ulanishi muvaffaqiyatli!"
                            success = await telegram_service.send_message(chat_id_input, test_message)
                            
                            if success:
                                chat_id = chat_id_input
                                print("✅ Chat ID muvaffaqiyatli tekshirildi!")
                                break
                            else:
                                print("❌ Chat ID noto'g'ri yoki bot xabar yubora olmaydi")
                                retry = input("🔄 Qayta urinib ko'rasizmi? (ha/yo'q): ").strip().lower()
                                if retry not in ['ha', 'yes', 'y', '1', 'true']:
                                    break
                        else:
                            print("❌ Chat ID bo'sh bo'lishi mumkin emas!")
                
                elif chat_id_method == "2":
                    # Bot updates orqali olish
                    print(f"📱 @{bot_info.get('username', 'your_bot')} ga '/start' xabar yuboring...")
                    print("⏰ 30 soniya kutishim kerak...")
                    
                    # Sodda polling (real loyihada webhook ishlatish kerak)
                    for i in range(6):  # 30 soniya = 6 x 5 soniya
                        try:
                            url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
                            import httpx
                            async with httpx.AsyncClient() as client:
                                response = await client.get(url)
                                if response.status_code == 200:
                                    updates = response.json().get("result", [])
                                    
                                    # Eng oxirgi '/start' xabarini topish
                                    for update in reversed(updates):
                                        if "message" in update:
                                            message = update["message"]
                                            if message.get("text", "").strip() == "/start":
                                                chat_id = str(message["chat"]["id"])
                                                username_tg = message["from"].get("username", "Unknown")
                                                print(f"✅ Chat ID topildi: {chat_id}")
                                                print(f"👤 Foydalanuvchi: @{username_tg}")
                                                
                                                # Test xabar yuborish
                                                test_message = "🔐 2FA Test - Chat ulanishi muvaffaqiyatli!"
                                                await telegram_service.send_message(chat_id, test_message)
                                                break
                                    
                                    if chat_id:
                                        break
                                        
                        except Exception as e:
                            print(f"🔄 Xatolik: {e}")
                        
                        if i < 5:  # Oxirgi iteratsiya emas
                            print(f"⏳ Kutishda... ({(i+1)*5}/30 soniya)")
                            await asyncio.sleep(5)
                    
                    if not chat_id:
                        print("❌ Chat ID avtomatik olinmadi")
                        print("💡 Qo'lda kiritib ko'ring yoki keyinroq sozlang")
                
                # AdminSecurity yaratish
                if chat_id:
                    try:
                        admin_security = await AdminSecurity.create(
                            user_id=user.id,
                            telegram_enabled=True,
                            telegram_bot_token=bot_token,
                            telegram_chat_id=chat_id,
                            require_confirmation=True,
                            auto_block_suspicious=True,
                            max_failed_attempts=3
                        )
                        
                        print("\n🎉 2FA muvaffaqiyatli sozlandi!")
                        print("=" * 50)
                        print("✅ Telegram bot ulandi")
                        print("✅ Chat ID sozlandi")
                        print("✅ Avtomatik tasdiqlov yoqildi")
                        print("✅ Shubhali faollikni bloklash yoqildi")
                        print("✅ Maksimal urinishlar: 3 marta")
                        
                        # Oxirgi test xabari
                        welcome_message = f"""
🎉 <b>2FA Muvaffaqiyatli Sozlandi!</b>

👤 <b>Admin:</b> {username}
📧 <b>Email:</b> {email}
🔐 <b>2FA:</b> Faol

🛡️ <b>Xavfsizlik sozlamalari:</b>
✅ Telegram tasdiqlov
✅ Avtomatik bloklash
✅ Maksimal urinishlar: 3

💡 <i>Endi admin panelga kirishda Telegram orqali tasdiqlash talab qilinadi</i>
                        """
                        
                        await telegram_service.send_message(chat_id, welcome_message)
                        
                    except Exception as e:
                        print(f"❌ 2FA sozlashda xatolik: {e}")
                        print("⚠️  SuperUser yaratildi, lekin 2FA sozlanmadi")
                else:
                    print("⚠️  Chat ID olinmadi, 2FA keyinroq sozlanishi mumkin")
            else:
                print("⚠️  Bot token olinmadi, 2FA keyinroq sozlanishi mumkin")
        else:
            print("⏩ 2FA sozlash bekor qilindi")
            print("💡 Keyinroq admin panel orqali sozlashingiz mumkin")
        
        print("\n🎉 SuperUser yaratish jarayoni tugallandi!")
        print("=" * 50)
        print(f"👤 Username: {username}")
        print(f"📧 Email: {email}")
        print(f"🔐 2FA: {'Faol' if enable_2fa in ['ha', 'yes', 'y', '1', 'true'] and 'chat_id' in locals() and chat_id else 'Faol emas'}")
        print("🌐 Admin panel: http://localhost:8000/admin")
        
    except Exception as e:
        print(f"❌ SuperUser yaratishda xatolik: {e}")
    finally:
        await Tortoise.close_connections()


def run_create_superuser():
    """Sync wrapper for create_superuser"""
    asyncio.run(create_superuser())

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
        expire = datetime.now() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
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
