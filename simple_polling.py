#!/usr/bin/env python3
"""
Simple Telegram Polling Script for 2FA
"""

import asyncio
import httpx
import sys
import os
from pathlib import Path

# Token
BOT_TOKEN = "8430332525:AAG-tqPwmTeymZ4wASPmvQZHw_YwF1d-QFQ"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

last_update_id = 0

async def get_updates():
    """Yangi update'larni olish"""
    global last_update_id
    try:
        url = f"{BASE_URL}/getUpdates"
        params = {
            "offset": last_update_id + 1,
            "timeout": 30,
            "allowed_updates": ["message"]
        }
        
        async with httpx.AsyncClient(timeout=35) as client:
            response = await client.get(url, params=params)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    return result.get("result", [])
            
            return []
            
    except Exception as e:
        print(f"❌ Get updates xatolik: {e}")
        return []

async def send_message(chat_id, text):
    """Xabar yuborish"""
    try:
        url = f"{BASE_URL}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data)
            return response.status_code == 200
            
    except Exception as e:
        print(f"❌ Send message xatolik: {e}")
        return False

async def handle_confirmation(verification_code, action, chat_id):
    """Database'da tasdiqlash"""
    import sqlite3
    
    try:
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        
        # Verification topish
        cursor.execute(
            "SELECT attempt_id, user_id FROM pending_verifications WHERE verification_code = ? AND is_used = 0",
            (verification_code,)
        )
        result = cursor.fetchone()
        
        if not result:
            return {"success": False, "message": "Verification kod topilmadi"}
        
        attempt_id, user_id = result
        
        if action == "confirm":
            # Tasdiqlash
            cursor.execute("UPDATE login_attempts SET status = 'confirmed' WHERE id = ?", (attempt_id,))
            cursor.execute("UPDATE pending_verifications SET is_used = 1 WHERE verification_code = ?", (verification_code,))
            conn.commit()
            conn.close()
            
            return {"success": True, "message": "✅ Login tasdiqlandi! Admin panelga kirishingiz mumkin."}
            
        elif action == "deny":
            # Rad etish
            cursor.execute("UPDATE login_attempts SET status = 'denied' WHERE id = ?", (attempt_id,))
            cursor.execute("UPDATE pending_verifications SET is_used = 1 WHERE verification_code = ?", (verification_code,))
            conn.commit()
            conn.close()
            
            return {"success": True, "message": "❌ Login rad etildi va qurilma bloklandi."}
        else:
            conn.close()
            return {"success": False, "message": "Noto'g'ri action"}
            
    except Exception as e:
        return {"success": False, "message": f"Xatolik: {str(e)}"}

async def process_update(update):
    """Update'ni qayta ishlash"""
    global last_update_id
    
    try:
        last_update_id = update.get("update_id", 0)
        
        if "message" not in update:
            return
        
        message = update["message"]
        text = message.get("text", "").strip()
        chat_id = str(message["chat"]["id"])
        
        print(f"📨 Yangi xabar: {text} dan {chat_id}")
        
        if text.startswith("/confirm_"):
            verification_code = text.replace("/confirm_", "")
            result = await handle_confirmation(verification_code, "confirm", chat_id)
            
            if result["success"]:
                await send_message(chat_id, "✅ Login muvaffaqiyatli tasdiqlandi!")
            else:
                await send_message(chat_id, f"❌ Xatolik: {result['message']}")
                
        elif text.startswith("/deny_"):
            verification_code = text.replace("/deny_", "")
            result = await handle_confirmation(verification_code, "deny", chat_id)
            
            if result["success"]:
                await send_message(chat_id, "❌ Login rad etildi va qurilma bloklandi!")
            else:
                await send_message(chat_id, f"❌ Xatolik: {result['message']}")
        
        elif text.startswith("/start"):
            await send_message(
                chat_id, 
                "🤖 Salom! Men 2FA bot'iman.\n\n"
                "Login tasdiqlash xabarlarini kutib turing."
            )
        
    except Exception as e:
        print(f"❌ Update process xatolik: {e}")

async def main():
    """Asosiy polling tsikli"""
    print("🚀 Telegram bot polling boshlandi...")
    
    while True:
        try:
            updates = await get_updates()
            
            for update in updates:
                await process_update(update)
            
            if not updates:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            print("\n⏹️ Polling to'xtatildi")
            break
        except Exception as e:
            print(f"❌ Polling xatolik: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Dastur to'xtatildi")
