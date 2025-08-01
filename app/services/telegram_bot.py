"""
Telegram Bot Service - 2FA uchun
"""
import httpx
import asyncio
from typing import Optional, Dict, Any
import json
from datetime import datetime, timedelta

from app.models.admin_security import AdminSecurity, LoginAttempt, DeviceBlock, PendingVerification


class TelegramBotService:
    """Telegram bot orqali 2FA xabarlarini yuborish"""
    
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        
    async def send_message(self, chat_id: str, message: str, parse_mode: str = "HTML") -> bool:
        """Telegram ga xabar yuborish"""
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": parse_mode
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=data)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('ok'):
                        print(f"✅ Telegram xabar yuborildi: {chat_id}")
                        return True
                    else:
                        print(f"❌ Telegram API xatosi: {result}")
                        return False
                else:
                    print(f"❌ HTTP xatolik {response.status_code}: {response.text}")
                    return False
                
        except Exception as e:
            print(f"❌ Telegram xabar yuborishda xatolik: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def send_login_confirmation(self, user_id: int, ip_address: str, 
                                    user_agent: str, location: str = "Unknown") -> Optional[str]:
        """Login tasdiqlash xabarini yuborish"""
        try:
            # User obyektini olish
            from app.models.user import User
            user = await User.get(id=user_id)
            
            # AdminSecurity dan bot ma'lumotlarini olish
            admin_security = await AdminSecurity.get(user=user)
            
            if not admin_security.telegram_enabled or not admin_security.telegram_chat_id:
                return None
                
            # Login attempt yaratish
            attempt = await LoginAttempt.create(
                user=user,
                ip_address=ip_address,
                user_agent=user_agent,
                location=location,
                status="pending"
            )
            
            # PendingVerification yaratish
            verification = await PendingVerification.create(
                user=user,
                verification_code=f"login_{attempt.id}",
                attempt_id=attempt.id,
                expires_at=datetime.now() + timedelta(minutes=5)
            )
            
            # Xabar matnini tayyorlash
            message = f"""
🔐 <b>Admin Panel Login Tasdiqi</b>

📅 <b>Vaqt:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
🌐 <b>IP Address:</b> <code>{ip_address}</code>
📱 <b>Qurilma:</b> <code>{user_agent[:50]}...</code>
📍 <b>Joylashuv:</b> {location}

❓ <b>Bu siz edingizmi?</b>

✅ Tasdiqlash uchun: /confirm_{verification.verification_code}
❌ Rad etish uchun: /deny_{verification.verification_code}

⚠️ <i>Agar bu siz bo'lmasangiz, darhol "Rad etish" tugmasini bosing!</i>
⏰ <i>Bu kod 5 daqiqada o'z kuchini yo'qotadi</i>
            """
            
            # Xabarni yuborish
            success = await self.send_message(admin_security.telegram_chat_id, message)
            
            if success:
                await attempt.update_from_dict({"status": "sent"})
                return verification.verification_code
            else:
                await attempt.update_from_dict({"status": "failed"})
                return None
                
        except Exception as e:
            print(f"❌ Login confirmation yuborishda xatolik: {e}")
            return None
    
    async def send_device_blocked_notification(self, user_id: int, ip_address: str, 
                                            user_agent: str, reason: str = "Suspicious activity"):
        """Qurilma bloklanganligi haqida xabar"""
        try:
            # User obyektini olish
            from app.models.user import User
            user = await User.get(id=user_id)
            
            admin_security = await AdminSecurity.get(user=user)
            
            if not admin_security.telegram_enabled or not admin_security.telegram_chat_id:
                return
                
            message = f"""
🚫 <b>Qurilma Bloklandi!</b>

📅 <b>Vaqt:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
🌐 <b>IP Address:</b> <code>{ip_address}</code>
📱 <b>Qurilma:</b> <code>{user_agent[:50]}...</code>
⚠️ <b>Sabab:</b> {reason}

🔒 <i>Bu qurilma xavfsizlik sabablariga ko'ra bloklandi</i>
💡 <i>Admin panel orqali blokni bekor qilishingiz mumkin</i>
            """
            
            await self.send_message(admin_security.telegram_chat_id, message)
            
        except Exception as e:
            print(f"❌ Block notification yuborishda xatolik: {e}")
    
    async def verify_login_confirmation(self, verification_code: str, action: str) -> Dict[str, Any]:
        """Login tasdiqlashni tekshirish"""
        try:
            # Verification kodini topish
            verification = await PendingVerification.get_or_none(
                verification_code=verification_code,
                is_used=False
            ).select_related('user')
            
            if not verification:
                return {"success": False, "message": "Verification kod topilmadi"}
                
            # Vaqt tekshiruvisiz davom etamiz
            # Login attempt ni topish
            attempt = await LoginAttempt.get(id=verification.attempt_id)
            
            if action == "confirm":
                # Tasdiqlash
                await attempt.update_from_dict({"status": "confirmed"})
                await verification.update_from_dict({"is_used": True})
                
                return {
                    "success": True, 
                    "message": "Login tasdiqlandi",
                    "user_id": verification.user.id,
                    "attempt_id": attempt.id
                }
                
            elif action == "deny":
                # Rad etish
                await attempt.update_from_dict({"status": "denied"})
                await verification.update_from_dict({"is_used": True})
                
                # Qurilmani bloklash
                await DeviceBlock.create(
                    user=verification.user,
                    ip_address=attempt.ip_address,
                    user_agent=attempt.user_agent,
                    reason="User denied login attempt",
                    blocked_until=datetime.now() + timedelta(hours=24)
                )
                
                return {
                    "success": True, 
                    "message": "Login rad etildi va qurilma bloklandi",
                    "blocked": True
                }
            else:
                return {"success": False, "message": "Noto'g'ri action"}
                
        except Exception as e:
            print(f"❌ Login verification da xatolik: {e}")
            return {"success": False, "message": f"Xatolik: {str(e)}"}
    
    async def test_bot_connection(self) -> Dict[str, Any]:
        """Bot ulanishini tekshirish"""
        try:
            url = f"{self.base_url}/getMe"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                
                if response.status_code == 200:
                    bot_info = response.json()
                    return {
                        "success": True,
                        "bot_info": bot_info.get("result", {}),
                        "message": "Bot muvaffaqiyatli ulandi"
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Bot ulanishida xatolik: {response.status_code}"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "message": f"Bot ulanishida xatolik: {str(e)}"
            }
    
    async def get_chat_id_from_username(self, username: str) -> Optional[str]:
        """Username dan chat_id olish (faqat public channels uchun)"""
        try:
            url = f"{self.base_url}/getChat"
            data = {"chat_id": f"@{username}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data)
                
                if response.status_code == 200:
                    chat_info = response.json()
                    return str(chat_info["result"]["id"])
                    
        except Exception:
            pass
        
        return None


async def get_telegram_service(user_id: int) -> Optional[TelegramBotService]:
    """User uchun Telegram service ni olish"""
    try:
        # User obyektini olish
        from app.models.user import User
        user = await User.get(id=user_id)
        
        admin_security = await AdminSecurity.get_or_none(user=user)
        
        if not admin_security or not admin_security.telegram_enabled or not admin_security.telegram_bot_token:
            return None
            
        return TelegramBotService(admin_security.telegram_bot_token)
        
    except Exception:
        return None


# Telegram webhook uchun handler
async def handle_telegram_webhook(update: Dict[str, Any]) -> Dict[str, Any]:
    """Telegram webhook ni handle qilish"""
    try:
        if "message" not in update:
            return {"success": False, "message": "Message not found"}
            
        message = update["message"]
        text = message.get("text", "")
        chat_id = str(message["chat"]["id"])
        
        # Confirm/Deny command larini tekshirish
        if text.startswith("/confirm_") or text.startswith("/deny_"):
            action = "confirm" if text.startswith("/confirm_") else "deny"
            verification_code = text.split("_", 1)[1]
            
            # Barcha admin lar dan bot service ni topish
            admin_securities = await AdminSecurity.filter(
                telegram_enabled=True,
                telegram_chat_id=chat_id
            )
            
            for admin_security in admin_securities:
                service = TelegramBotService(admin_security.telegram_bot_token)
                result = await service.verify_login_confirmation(verification_code, action)
                
                if result["success"]:
                    if action == "confirm":
                        response_text = "✅ Login muvaffaqiyatli tasdiqlandi!"
                    else:
                        response_text = "❌ Login rad etildi va qurilma bloklandi!"
                        
                    await service.send_message(chat_id, response_text)
                    return result
            
            # Verification topilmadi
            service = TelegramBotService("dummy_token")  # Faqat xabar yuborish uchun
            await service.send_message(chat_id, "❌ Verification kod topilmadi yoki muddati tugagan")
            
        return {"success": True, "message": "Webhook processed"}
        
    except Exception as e:
        return {"success": False, "message": f"Webhook error: {str(e)}"}
