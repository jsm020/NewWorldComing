#!/usr/bin/env python3
"""
Telegram Bot Webhook Setup Script
BotFather orqali webhook'ni sozlash va boshqarish
"""

import asyncio
import httpx
import sys
from typing import Optional, Dict, Any
import json


class TelegramWebhookManager:
    """Telegram webhook'ni boshqarish"""
    
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    async def get_webhook_info(self) -> Dict[str, Any]:
        """Joriy webhook ma'lumotlarini olish"""
        try:
            url = f"{self.base_url}/getWebhookInfo"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("result", {})
                else:
                    return {"error": f"HTTP {response.status_code}: {response.text}"}
                    
        except Exception as e:
            return {"error": str(e)}
    
    async def set_webhook(self, webhook_url: str) -> Dict[str, Any]:
        """Webhook URL'ni o'rnatish"""
        try:
            url = f"{self.base_url}/setWebhook"
            data = {
                "url": webhook_url,
                "allowed_updates": ["message"],  # Faqat message'larni qabul qilish
                "drop_pending_updates": True  # Eski update'larni o'chirish
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data)
                
                if response.status_code == 200:
                    result = response.json()
                    return result
                else:
                    return {"ok": False, "error": f"HTTP {response.status_code}: {response.text}"}
                    
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    async def delete_webhook(self) -> Dict[str, Any]:
        """Webhook'ni o'chirish (polling uchun)"""
        try:
            url = f"{self.base_url}/deleteWebhook"
            data = {
                "drop_pending_updates": True
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data)
                
                if response.status_code == 200:
                    result = response.json()
                    return result
                else:
                    return {"ok": False, "error": f"HTTP {response.status_code}: {response.text}"}
                    
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    async def get_bot_info(self) -> Dict[str, Any]:
        """Bot ma'lumotlarini olish"""
        try:
            url = f"{self.base_url}/getMe"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("result", {})
                else:
                    return {"error": f"HTTP {response.status_code}: {response.text}"}
                    
        except Exception as e:
            return {"error": str(e)}


async def main():
    """Asosiy funksiya"""
    print("🤖 Telegram Bot Webhook Setup")
    print("=" * 40)
    
    # Bot token so'rash
    bot_token = input("Telegram Bot Token kiriting: ").strip()
    
    if not bot_token:
        print("❌ Bot token kiritilmadi!")
        return
    
    manager = TelegramWebhookManager(bot_token)
    
    # Bot ma'lumotlarini tekshirish
    print("\n🔍 Bot ma'lumotlari tekshirilmoqda...")
    bot_info = await manager.get_bot_info()
    
    if "error" in bot_info:
        print(f"❌ Bot ma'lumotlarini ololmadim: {bot_info['error']}")
        return
    
    print(f"✅ Bot topildi: @{bot_info.get('username', 'Unknown')}")
    print(f"📝 Bot nomi: {bot_info.get('first_name', 'Unknown')}")
    
    # Joriy webhook holatini ko'rish
    print("\n📡 Joriy webhook holati...")
    webhook_info = await manager.get_webhook_info()
    
    if "error" not in webhook_info:
        current_url = webhook_info.get("url", "")
        if current_url:
            print(f"🌐 Joriy webhook URL: {current_url}")
            print(f"📊 Pending updates: {webhook_info.get('pending_update_count', 0)}")
            last_error = webhook_info.get('last_error_message', 'Yo\'q')
            print(f"📅 Oxirgi xatolik: {last_error}")
        else:
            print("📭 Webhook o'rnatilmagan (polling rejimida)")
    else:
        print(f"❌ Webhook ma'lumotlarini ololmadim: {webhook_info['error']}")
    
    # Amallarni ko'rsatish
    print("\n🛠️ Quyidagi amallardan birini tanlang:")
    print("1. Webhook o'rnatish")
    print("2. Webhook o'chirish (polling uchun)")
    print("3. Webhook holatini ko'rish")
    print("4. Chiqish")
    
    choice = input("\nTanlang (1-4): ").strip()
    
    if choice == "1":
        # Webhook o'rnatish
        print("\n🔧 Webhook o'rnatish...")
        
        # Default webhook URL
        default_url = "https://your-domain.com/api/v1/telegram/webhook"
        current_url = input(f"Webhook URL kiriting [{default_url}]: ").strip()
        
        if not current_url:
            current_url = default_url
        
        # Local server uchun ngrok URL so'rash
        if "localhost" in current_url or "127.0.0.1" in current_url:
            print("⚠️  Localhost URL webhook uchun ishlamaydi!")
            print("💡 ngrok yoki boshqa tunnel service ishlating:")
            print("   ngrok http 8000")
            ngrok_url = input("ngrok URL kiriting (masalan: https://abc123.ngrok.io): ").strip()
            if ngrok_url:
                current_url = f"{ngrok_url.rstrip('/')}/api/v1/telegram/webhook"
        
        result = await manager.set_webhook(current_url)
        
        if result.get("ok"):
            print(f"✅ Webhook muvaffaqiyatli o'rnatildi: {current_url}")
        else:
            print(f"❌ Webhook o'rnatishda xatolik: {result.get('description', result.get('error', 'Unknown'))}")
    
    elif choice == "2":
        # Webhook o'chirish
        print("\n🗑️ Webhook o'chirilmoqda...")
        result = await manager.delete_webhook()
        
        if result.get("ok"):
            print("✅ Webhook muvaffaqiyatli o'chirildi")
            print("🔄 Endi bot polling rejimida ishlaydi")
        else:
            print(f"❌ Webhook o'chirishda xatolik: {result.get('description', result.get('error', 'Unknown'))}")
    
    elif choice == "3":
        # Webhook holatini ko'rish
        print("\n📊 Webhook holati:")
        webhook_info = await manager.get_webhook_info()
        
        if "error" not in webhook_info:
            print(json.dumps(webhook_info, indent=2, ensure_ascii=False))
        else:
            print(f"❌ Xatolik: {webhook_info['error']}")
    
    elif choice == "4":
        print("👋 Dastur tugadi")
        return
    
    else:
        print("❌ Noto'g'ri tanlov!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Dastur to'xtatildi")
    except Exception as e:
        print(f"❌ Xatolik: {e}")
