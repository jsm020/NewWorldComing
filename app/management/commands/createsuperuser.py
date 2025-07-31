#!/usr/bin/env python3
"""
Django's createsuperuser ga o'xshash komanda
Foydalanish: python -m app.management.commands.createsuperuser
"""

import asyncio
import getpass
import sys
from tortoise import Tortoise
from app.models.user import User
from app.core.security import SecurityUtils
from config.tortoise_config import TORTOISE_ORM


async def create_superuser():
    """Superuser yaratish Django uslubida."""
    print("=== FastAPI Superuser Yaratish ===\n")
    
    try:
        # Database ga ulanish
        await Tortoise.init(config=TORTOISE_ORM)
        await Tortoise.generate_schemas()
        
        # Username kiritish
        while True:
            username = input("Username: ").strip()
            if not username:
                print("Username bo'sh bo'lishi mumkin emas!")
                continue
            
            # Username mavjudligini tekshirish
            existing_user = await User.filter(username=username).first()
            if existing_user:
                print(f"'{username}' username allaqachon mavjud!")
                continue
            break
        
        # Email kiritish
        while True:
            email = input("Email address: ").strip()
            if not email:
                print("Email bo'sh bo'lishi mumkin emas!")
                continue
            
            # Email validatsiya (oddiy)
            if "@" not in email or "." not in email:
                print("Email noto'g'ri formatda!")
                continue
            
            # Email mavjudligini tekshirish
            existing_email = await User.filter(email=email).first()
            if existing_email:
                print(f"'{email}' email allaqachon mavjud!")
                continue
            break
        
        # Parol kiritish
        while True:
            password = getpass.getpass("Password: ")
            if len(password) < 6:
                print("Parol kamida 6 ta belgidan iborat bo'lishi kerak!")
                continue
            
            password_confirm = getpass.getpass("Password (again): ")
            if password != password_confirm:
                print("Parollar mos kelmadi!")
                continue
            break
        
        # Qo'shimcha ma'lumotlar
        first_name = input("First name (ixtiyoriy): ").strip() or None
        last_name = input("Last name (ixtiyoriy): ").strip() or None
        
        # Superuser yaratish
        print("\nSuperuser yaratilmoqda...")
        
        user = await User.create(
            username=username,
            email=email,
            password_hash=SecurityUtils.hash_password(password),
            first_name=first_name,
            last_name=last_name,
            is_active=True,
            is_superuser=True
        )
        
        print(f"✅ Superuser '{username}' muvaffaqiyatli yaratildi!")
        print(f"ID: {user.id}")
        print(f"Email: {user.email}")
        print(f"Is superuser: {user.is_superuser}")
        print(f"Yaratilgan vaqt: {user.created_at}")
        
    except Exception as e:
        print(f"❌ Xatolik yuz berdi: {e}")
        sys.exit(1)
    finally:
        await Tortoise.close_connections()


async def list_users():
    """Barcha foydalanuvchilarni ko'rsatish."""
    print("=== Barcha foydalanuvchilar ===\n")
    
    try:
        await Tortoise.init(config=TORTOISE_ORM)
        
        users = await User.all()
        if not users:
            print("Hech qanday foydalanuvchi topilmadi.")
            return
        
        print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Superuser':<10} {'Active':<8}")
        print("-" * 80)
        
        for user in users:
            print(f"{user.id:<5} {user.username:<20} {user.email:<30} {'✓' if user.is_superuser else '✗':<10} {'✓' if user.is_active else '✗':<8}")
        
        print(f"\nJami: {len(users)} ta foydalanuvchi")
        
    except Exception as e:
        print(f"❌ Xatolik: {e}")
    finally:
        await Tortoise.close_connections()


async def main():
    """Asosiy funksiya."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--list":
            await list_users()
            return
        elif sys.argv[1] == "--help":
            print("Foydalanish:")
            print("  python -m app.management.commands.createsuperuser        # Superuser yaratish")
            print("  python -m app.management.commands.createsuperuser --list # Foydalanuvchilarni ko'rsatish")
            print("  python -m app.management.commands.createsuperuser --help # Yordam")
            return
    
    await create_superuser()


if __name__ == "__main__":
    asyncio.run(main())
