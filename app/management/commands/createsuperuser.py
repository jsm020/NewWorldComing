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
from app.models.admin_security import AdminSecurity
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
        
        # AdminSecurity yozuvini yaratish
        print("AdminSecurity konfiguratsiyasi yaratilmoqda...")
        
        # Telegram 2FA sozlash
        while True:
            enable_2fa = input("\nTelegram 2FA (Two-Factor Authentication) yoqasizmi? (y/n): ").strip().lower()
            if enable_2fa in ['y', 'yes', 'ha', '1']:
                # Telegram ma'lumotlarini so'rash
                print("\n=== Telegram Bot Sozlash ===")
                print("1. @BotFather ga borib yangi bot yarating")
                print("2. Bot token va Chat ID ni kiriting")
                
                bot_token = input("Telegram Bot Token: ").strip()
                if not bot_token:
                    print("Bot token bo'sh bo'lishi mumkin emas!")
                    continue
                
                chat_id = input("Telegram Chat ID: ").strip()
                if not chat_id:
                    print("Chat ID bo'sh bo'lishi mumkin emas!")
                    continue
                
                telegram_username = input("Telegram Username (@username): ").strip()
                
                # AdminSecurity yaratish - 2FA bilan
                admin_security = await AdminSecurity.create(
                    user=user,
                    telegram_enabled=True,
                    telegram_bot_token=bot_token,
                    telegram_chat_id=chat_id,
                    telegram_username=telegram_username,
                    require_confirmation=True,
                    auto_block_suspicious=True,
                    max_failed_attempts=3
                )
                
                print("✅ Telegram 2FA muvaffaqiyatli sozlandi!")
                print(f"Bot Token: {bot_token[:10]}...")
                print(f"Chat ID: {chat_id}")
                break
                
            elif enable_2fa in ['n', 'no', 'yo\'q', '0']:
                # AdminSecurity yaratish - 2FA siz
                admin_security = await AdminSecurity.create(
                    user=user,
                    telegram_enabled=False,
                    require_confirmation=False,
                    auto_block_suspicious=True,
                    max_failed_attempts=5
                )
                print("ℹ️  2FA o'chirilgan holda AdminSecurity yaratildi.")
                break
            else:
                print("Iltimos, 'y' yoki 'n' kiriting!")
        
        print(f"✅ Superuser '{username}' muvaffaqiyatli yaratildi!")
        print(f"ID: {user.id}")
        print(f"Email: {user.email}")
        print(f"Is superuser: {user.is_superuser}")
        print(f"2FA enabled: {admin_security.telegram_enabled}")
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
        
        users = await User.all().prefetch_related('admin_security')
        if not users:
            print("Hech qanday foydalanuvchi topilmadi.")
            return
        
        print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Superuser':<10} {'Active':<8} {'2FA':<5}")
        print("-" * 85)
        
        for user in users:
            admin_security = getattr(user, 'admin_security', None)
            has_2fa = "✓" if admin_security and admin_security[0].telegram_enabled else "✗"
            
            print(f"{user.id:<5} {user.username:<20} {user.email:<30} {'✓' if user.is_superuser else '✗':<10} {'✓' if user.is_active else '✗':<8} {has_2fa:<5}")
        
        print(f"\nJami: {len(users)} ta foydalanuvchi")
        
    except Exception as e:
        print(f"❌ Xatolik: {e}")
    finally:
        await Tortoise.close_connections()


async def setup_2fa_for_existing_user():
    """Mavjud superuser uchun 2FA sozlash."""
    print("=== Mavjud Superuser uchun 2FA Sozlash ===\n")
    
    try:
        await Tortoise.init(config=TORTOISE_ORM)
        
        # Superuserlarni ko'rsatish
        superusers = await User.filter(is_superuser=True).prefetch_related('admin_security')
        if not superusers:
            print("Hech qanday superuser topilmadi!")
            return
        
        print("Mavjud superuserlar:")
        for i, user in enumerate(superusers, 1):
            admin_security = getattr(user, 'admin_security', None)
            has_2fa = "✓" if admin_security and admin_security[0].telegram_enabled else "✗"
            print(f"{i}. {user.username} (ID: {user.id}) - 2FA: {has_2fa}")
        
        # Tanlash
        while True:
            try:
                choice = int(input(f"\nQaysi foydalanuvchi uchun 2FA sozlaysiz? (1-{len(superusers)}): "))
                if 1 <= choice <= len(superusers):
                    selected_user = superusers[choice - 1]
                    break
                else:
                    print("Noto'g'ri tanlov!")
            except ValueError:
                print("Raqam kiriting!")
        
        # AdminSecurity mavjudligini tekshirish
        admin_security = await AdminSecurity.get_or_none(user=selected_user)
        
        if admin_security:
            print(f"\n'{selected_user.username}' uchun AdminSecurity mavjud.")
            status_text = "Yoqilgan" if admin_security.telegram_enabled else "O'chirilgan"
            print(f"2FA holati: {status_text}")
            
            update_choice = input("Yangilash istaysizmi? (y/n): ").strip().lower()
            if update_choice not in ['y', 'yes', 'ha', '1']:
                print("Bekor qilindi.")
                return
        else:
            print(f"\n'{selected_user.username}' uchun AdminSecurity yaratiladi.")
        
        # Telegram 2FA sozlash
        while True:
            enable_2fa = input("\nTelegram 2FA yoqasizmi? (y/n): ").strip().lower()
            if enable_2fa in ['y', 'yes', 'ha', '1']:
                print("\n=== Telegram Bot Sozlash ===")
                print("1. @BotFather ga borib yangi bot yarating")
                print("2. Bot token va Chat ID ni kiriting")
                
                bot_token = input("Telegram Bot Token: ").strip()
                if not bot_token:
                    print("Bot token bo'sh bo'lishi mumkin emas!")
                    continue
                
                chat_id = input("Telegram Chat ID: ").strip()
                if not chat_id:
                    print("Chat ID bo'sh bo'lishi mumkin emas!")
                    continue
                
                telegram_username = input("Telegram Username (@username): ").strip()
                
                if admin_security:
                    # Mavjudini yangilash
                    admin_security.telegram_enabled = True
                    admin_security.telegram_bot_token = bot_token
                    admin_security.telegram_chat_id = chat_id
                    admin_security.telegram_username = telegram_username
                    admin_security.require_confirmation = True
                    await admin_security.save()
                    print("✅ AdminSecurity muvaffaqiyatli yangilandi!")
                else:
                    # Yangi yaratish
                    admin_security = await AdminSecurity.create(
                        user=selected_user,
                        telegram_enabled=True,
                        telegram_bot_token=bot_token,
                        telegram_chat_id=chat_id,
                        telegram_username=telegram_username,
                        require_confirmation=True,
                        auto_block_suspicious=True,
                        max_failed_attempts=3
                    )
                    print("✅ AdminSecurity muvaffaqiyatli yaratildi!")
                
                print(f"Bot Token: {bot_token[:10]}...")
                print(f"Chat ID: {chat_id}")
                break
                
            elif enable_2fa in ['n', 'no', 'yo\'q', '0']:
                if admin_security:
                    admin_security.telegram_enabled = False
                    admin_security.require_confirmation = False
                    await admin_security.save()
                    print("✅ 2FA o'chirildi.")
                else:
                    admin_security = await AdminSecurity.create(
                        user=selected_user,
                        telegram_enabled=False,
                        require_confirmation=False,
                        auto_block_suspicious=True,
                        max_failed_attempts=5
                    )
                    print("✅ AdminSecurity yaratildi (2FA o'chirilgan).")
                break
            else:
                print("Iltimos, 'y' yoki 'n' kiriting!")
        
        print(f"\n✅ '{selected_user.username}' uchun sozlamalar saqlandi!")
        
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
        elif sys.argv[1] == "--setup-2fa":
            await setup_2fa_for_existing_user()
            return
        elif sys.argv[1] == "--help":
            print("Foydalanish:")
            print("  python -m app.management.commands.createsuperuser              # Superuser yaratish")
            print("  python -m app.management.commands.createsuperuser --list      # Foydalanuvchilarni ko'rsatish")
            print("  python -m app.management.commands.createsuperuser --setup-2fa # Mavjud user uchun 2FA sozlash")
            print("  python -m app.management.commands.createsuperuser --help      # Yordam")
            return
    
    await create_superuser()


if __name__ == "__main__":
    asyncio.run(main())
