"""
Telegram Bot Webhook Handler - 2FA uchun
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
import json

from app.services.telegram_bot import get_telegram_service
from app.models.admin_security import PendingVerification, LoginAttempt


router = APIRouter(prefix="/telegram", tags=["Telegram Bot"])


@router.post("/webhook")
async def telegram_webhook(request: Request):
    """Telegram bot webhook handler with ngrok support"""
    try:
        print(f"📨 Webhook so'rov keldi: {request.headers}")
        
        # Telegram dan kelayotgan ma'lumotni olish
        data = await request.json()
        print(f"📨 Webhook data: {data}")
        
        # Message mavjudligini tekshirish
        if "message" not in data:
            print("📭 Message yo'q, o'tkazib yuborish")
            return {"ok": True}
        
        message = data["message"]
        
        # Text mavjudligini tekshirish
        if "text" not in message:
            return {"ok": True}
        
        text = message["text"].strip()
        chat_id = str(message["chat"]["id"])
        
        # Command'larni tekshirish
        if text.startswith("/confirm_"):
            # Confirm command
            verification_code = text.replace("/confirm_", "")
            result = await handle_confirmation(verification_code, "confirm", chat_id)
            
        elif text.startswith("/deny_"):
            # Deny command
            verification_code = text.replace("/deny_", "")
            result = await handle_confirmation(verification_code, "deny", chat_id)
            
        else:
            # Unknown command
            return {"ok": True}
        
        # Response yuborish
        if result["success"]:
            await send_response_message(chat_id, result["message"])
        else:
            await send_response_message(chat_id, f"❌ Xatolik: {result['message']}")
        
        return {"ok": True}
        
    except Exception as e:
        print(f"❌ Webhook xatolik: {e}")
        return {"ok": True}


async def handle_confirmation(verification_code: str, action: str, chat_id: str) -> Dict[str, Any]:
    """Login tasdiqlash yoki rad etishni boshqarish"""
    try:
        # Verification kodini topish
        verification = await PendingVerification.get_or_none(
            verification_code=verification_code,
            is_used=False
        ).select_related('user')
        
        if not verification:
            return {"success": False, "message": "Verification kod topilmadi yoki allaqachon ishlatilgan"}
        
        # Foydalanuvchiga tegishli ekanligini tekshirish
        from app.models.admin_security import AdminSecurity
        admin_security = await AdminSecurity.get_or_none(user=verification.user)
        
        if not admin_security or admin_security.telegram_chat_id != chat_id:
            return {"success": False, "message": "Bu verification kod sizga tegishli emas"}
        
        # Login attempt ni topish
        attempt = await LoginAttempt.get(id=verification.attempt_id)
        
        if action == "confirm":
            # Tasdiqlash
            await attempt.update_from_dict({"status": "confirmed"})
            await verification.update_from_dict({"is_used": True})
            
            return {
                "success": True, 
                "message": "✅ Login tasdiqlandi! Admin panelga kirishingiz mumkin."
            }
            
        elif action == "deny":
            # Rad etish
            await attempt.update_from_dict({"status": "denied"})
            await verification.update_from_dict({"is_used": True})
            
            # Qurilmani bloklash
            from app.models.admin_security import DeviceBlock
            from datetime import datetime, timedelta
            
            await DeviceBlock.create(
                user=verification.user,
                ip_address=attempt.ip_address,
                user_agent=attempt.user_agent,
                reason="User denied login attempt",
                blocked_until=datetime.now() + timedelta(hours=24),
                is_active=True
            )
            
            return {
                "success": True, 
                "message": "❌ Login rad etildi va qurilma 24 soatga bloklandi."
            }
        else:
            return {"success": False, "message": "Noto'g'ri action"}
            
    except Exception as e:
        print(f"❌ Confirmation handle da xatolik: {e}")
        return {"success": False, "message": f"Xatolik: {str(e)}"}


async def send_response_message(chat_id: str, message: str):
    """Telegram ga javob xabar yuborish"""
    try:
        # Bot service orqali xabar yuborish
        from app.models.admin_security import AdminSecurity
        admin_security = await AdminSecurity.filter(telegram_chat_id=chat_id).first()
        
        if admin_security and admin_security.telegram_bot_token:
            telegram_service = await get_telegram_service_by_token(admin_security.telegram_bot_token)
            if telegram_service:
                await telegram_service.send_message(chat_id, message)
    except Exception as e:
        print(f"❌ Response message yuborishda xatolik: {e}")


async def get_telegram_service_by_token(bot_token: str):
    """Bot token orqali TelegramBotService yaratish"""
    try:
        from app.services.telegram_bot import TelegramBotService
        return TelegramBotService(bot_token)
    except Exception as e:
        print(f"❌ Telegram service yaratishda xatolik: {e}")
        return None
