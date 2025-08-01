#!/usr/bin/env python3
"""
Telegram Bot Polling Service
Webhook o'rniga polling usuli
"""

import asyncio
import httpx
from typing import Optional, Dict, Any, List
import json
from datetime import datetime

from app.services.telegram_bot import TelegramBotService


class TelegramPollingService:
    """Telegram bot polling service"""
    
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.last_update_id = 0
        self.running = False
    
    async def get_updates(self, timeout: int = 30) -> List[Dict[str, Any]]:
        """Yangi update'larni olish"""
        try:
            url = f"{self.base_url}/getUpdates"
            params = {
                "offset": self.last_update_id + 1,
                "timeout": timeout,
                "allowed_updates": ["message"]
            }
            
            async with httpx.AsyncClient(timeout=timeout + 10) as client:
                response = await client.get(url, params=params)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("ok"):
                        return result.get("result", [])
                
                return []
                
        except Exception as e:
            print(f"❌ Get updates xatolik: {e}")
            return []
    
    async def process_update(self, update: Dict[str, Any]):
        """Update'ni qayta ishlash"""
        try:
            # Webhook handler'dan foydalanish
            from app.api.telegram_webhook import handle_confirmation
            
            if "message" not in update:
                return
            
            message = update["message"]
            text = message.get("text", "").strip()
            chat_id = str(message["chat"]["id"])
            
            print(f"📨 Yangi xabar: {text} dan {chat_id}")
            
            # Command'larni tekshirish
            if text.startswith("/confirm_"):
                verification_code = text.replace("/confirm_", "")
                result = await handle_confirmation(verification_code, "confirm", chat_id)
                
                # Javob yuborish
                service = TelegramBotService(self.bot_token)
                if result["success"]:
                    await service.send_message(chat_id, "✅ Login muvaffaqiyatli tasdiqlandi!")
                else:
                    await service.send_message(chat_id, f"❌ Xatolik: {result['message']}")
                    
            elif text.startswith("/deny_"):
                verification_code = text.replace("/deny_", "")
                result = await handle_confirmation(verification_code, "deny", chat_id)
                
                # Javob yuborish
                service = TelegramBotService(self.bot_token)
                if result["success"]:
                    await service.send_message(chat_id, "❌ Login rad etildi va qurilma bloklandi!")
                else:
                    await service.send_message(chat_id, f"❌ Xatolik: {result['message']}")
            
            elif text.startswith("/start"):
                service = TelegramBotService(self.bot_token)
                await service.send_message(
                    chat_id, 
                    "🤖 Salom! Men 2FA bot'iman.\n\n"
                    "Login tasdiqlash xabarlarini kutib turing."
                )
            
        except Exception as e:
            print(f"❌ Update process xatolik: {e}")
    
    async def start_polling(self):
        """Polling'ni boshlash"""
        print(f"🚀 Telegram bot polling boshlandi...")
        self.running = True
        
        while self.running:
            try:
                updates = await self.get_updates()
                
                for update in updates:
                    self.last_update_id = update.get("update_id", 0)
                    await self.process_update(update)
                
                if not updates:
                    await asyncio.sleep(1)  # Qisqa pauza
                    
            except KeyboardInterrupt:
                print("\n⏹️ Polling to'xtatildi")
                break
            except Exception as e:
                print(f"❌ Polling xatolik: {e}")
                await asyncio.sleep(5)  # Xatolik bo'lsa 5 soniya kutish
        
        self.running = False
    
    def stop_polling(self):
        """Polling'ni to'xtatish"""
        self.running = False


async def main():
    """Asosiy funksiya"""
    print("🤖 Telegram Bot Polling Service")
    print("=" * 40)
    
    # Bot token so'rash
    bot_token = input("Telegram Bot Token kiriting: ").strip()
    
    if not bot_token:
        print("❌ Bot token kiritilmadi!")
        return
    
    # Bot ma'lumotlarini tekshirish
    service = TelegramBotService(bot_token)
    test_result = await service.test_bot_connection()
    
    if not test_result["success"]:
        print(f"❌ Bot ulanishida xatolik: {test_result['message']}")
        return
    
    bot_info = test_result["bot_info"]
    print(f"✅ Bot topildi: @{bot_info.get('username', 'Unknown')}")
    print(f"📝 Bot nomi: {bot_info.get('first_name', 'Unknown')}")
    
    # Polling service'ni boshlash
    polling_service = TelegramPollingService(bot_token)
    
    try:
        await polling_service.start_polling()
    except KeyboardInterrupt:
        print("\n👋 Polling to'xtatildi")
    except Exception as e:
        print(f"❌ Xatolik: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Dastur to'xtatildi")
    except Exception as e:
        print(f"❌ Xatolik: {e}")
