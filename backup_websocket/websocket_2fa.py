"""
WebSocket 2FA Real-time Verification
Telegram o'rniga web interface orqali 2FA
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Dict, List
import json
import asyncio
from datetime import datetime

from app.models.admin_security import LoginAttempt, PendingVerification, DeviceBlock
from app.models.user import User


# Templates
templates = Jinja2Templates(directory="app/admin/templates")

# Router
websocket_router = APIRouter(prefix="/admin/2fa", tags=["WebSocket 2FA"])

# Active WebSocket connections
active_connections: Dict[str, WebSocket] = {}


class ConnectionManager:
    """WebSocket connection manager"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, verification_code: str):
        """WebSocket connection ochish"""
        try:
            await websocket.accept()
            self.active_connections[verification_code] = websocket
            print(f"🔗 WebSocket connected: {verification_code} (Jami: {len(self.active_connections)})")
        except Exception as e:
            print(f"❌ WebSocket accept xatoligi {verification_code}: {e}")
            raise
    
    def disconnect(self, verification_code: str):
        """WebSocket connection yopish"""
        if verification_code in self.active_connections:
            del self.active_connections[verification_code]
            print(f"❌ WebSocket disconnected: {verification_code} (Qolgan: {len(self.active_connections)})")
    
    async def send_personal_message(self, verification_code: str, message: dict):
        """Maxsus connection ga xabar yuborish"""
        if verification_code in self.active_connections:
            try:
                await self.active_connections[verification_code].send_text(json.dumps(message))
                print(f"📤 Xabar yuborildi {verification_code}: {message.get('type', 'unknown')}")
                return True
            except Exception as e:
                print(f"❌ Xabar yuborishda xatolik {verification_code}: {e}")
                self.disconnect(verification_code)
                return False
        else:
            print(f"⚠️ Connection topilmadi: {verification_code}")
        return False
    
    async def broadcast_status(self, verification_code: str, status: str, message: str):
        """Status broadcast qilish"""
        await self.send_personal_message(verification_code, {
            "type": "status_update",
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })


# Global connection manager
manager = ConnectionManager()


@websocket_router.websocket("/ws/{verification_code}")
async def websocket_endpoint(websocket: WebSocket, verification_code: str):
    """WebSocket 2FA real-time connection"""
    print(f"🔗 WebSocket ulanish so'rovi: {verification_code}")
    
    try:
        await manager.connect(websocket, verification_code)
        print(f"✅ WebSocket muvaffaqiyatli ulandi: {verification_code}")
        
        # Initial status yuborish
        await manager.send_personal_message(verification_code, {
            "type": "connected",
            "message": "2FA WebSocket ulanishi faol",
            "verification_code": verification_code
        })
        print(f"📤 Initial xabar yuborildi: {verification_code}")
        
        # Connection ni kutish
        while True:
            # Har 5 soniyada status tekshirish
            await asyncio.sleep(5)
            
            # Database dan holat tekshirish
            verification = await PendingVerification.get_or_none(
                verification_code=verification_code,
                is_used=False
            )
            
            if verification:
                attempt = await LoginAttempt.get(id=verification.attempt_id)
                print(f"🔍 Status tekshirildi - {verification_code}: {attempt.status}")
                
                if attempt.status == "confirmed":
                    await manager.send_personal_message(verification_code, {
                        "type": "confirmed",
                        "message": "✅ Login tasdiqlandi! Sahifa avtomatik yangilanadi...",
                        "redirect": "/admin/dashboard"
                    })
                    break
                    
                elif attempt.status == "denied":
                    await manager.send_personal_message(verification_code, {
                        "type": "denied", 
                        "message": "❌ Login rad etildi. Qurilma bloklandi.",
                        "redirect": "/admin/login"
                    })
                    break
                    
                elif attempt.status == "pending":
                    await manager.send_personal_message(verification_code, {
                        "type": "waiting",
                        "message": "⏳ 2FA tasdiqlash kutilmoqda..."
                    })
            else:
                await manager.send_personal_message(verification_code, {
                    "type": "expired",
                    "message": "⏱️ Verification kod muddati tugadi",
                    "redirect": "/admin/login"
                })
                break
                
    except WebSocketDisconnect:
        print(f"❌ WebSocket disconnect: {verification_code}")
        manager.disconnect(verification_code)
    except Exception as e:
        print(f"❌ WebSocket xatolik {verification_code}: {e}")
        manager.disconnect(verification_code)


@websocket_router.get("/verify/{verification_code}", response_class=HTMLResponse)
async def websocket_2fa_page(request: Request, verification_code: str):
    """WebSocket 2FA verification sahifasi"""
    try:
        # Verification topish
        verification = await PendingVerification.get_or_none(
            verification_code=verification_code,
            is_used=False
        ).select_related('user')
        
        if not verification:
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "error": "Verification kod topilmadi yoki muddati tugagan"}
            )
        
        # Login attempt ma'lumotlari
        attempt = await LoginAttempt.get(id=verification.attempt_id)
        
        # Dynamic WebSocket URL yaratish
        host = request.headers.get("host", "localhost:8000")
        websocket_scheme = "wss" if request.url.scheme == "https" else "ws"
        websocket_url = f"{websocket_scheme}://{host}/admin/2fa/ws/{verification_code}"
        
        return templates.TemplateResponse(
            "websocket_2fa.html",
            {
                "request": request,
                "verification_code": verification_code,
                "user": verification.user,
                "attempt": attempt,
                "websocket_url": websocket_url
            }
        )
        
    except Exception as e:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": f"Xatolik: {str(e)}"}
        )


@websocket_router.post("/confirm/{verification_code}")
async def confirm_login(verification_code: str):
    """Login ni tasdiqlash"""
    try:
        # Verification topish
        verification = await PendingVerification.get_or_none(
            verification_code=verification_code,
            is_used=False
        )
        
        if not verification:
            return {"success": False, "message": "Verification kod topilmadi"}
        
        # Login attempt ni confirm qilish
        attempt = await LoginAttempt.get(id=verification.attempt_id)
        await attempt.update_from_dict({"status": "confirmed"})
        await verification.update_from_dict({"is_used": True})
        
        # WebSocket orqali status yuborish
        await manager.broadcast_status(verification_code, "confirmed", "✅ Login tasdiqlandi!")
        
        return {"success": True, "message": "Login tasdiqlandi"}
        
    except Exception as e:
        return {"success": False, "message": f"Xatolik: {str(e)}"}


@websocket_router.post("/deny/{verification_code}")
async def deny_login(verification_code: str):
    """Login ni rad etish"""
    try:
        # Verification topish
        verification = await PendingVerification.get_or_none(
            verification_code=verification_code,
            is_used=False
        ).select_related('user')
        
        if not verification:
            return {"success": False, "message": "Verification kod topilmadi"}
        
        # Login attempt ni deny qilish
        attempt = await LoginAttempt.get(id=verification.attempt_id)
        await attempt.update_from_dict({"status": "denied"})
        await verification.update_from_dict({"is_used": True})
        
        # Qurilmani bloklash
        await DeviceBlock.create(
            user=verification.user,
            ip_address=attempt.ip_address,
            user_agent=attempt.user_agent,
            reason="User denied login via WebSocket 2FA",
            blocked_until=datetime.now(),  # Timezone-free
            is_active=True
        )
        
        # WebSocket orqali status yuborish
        await manager.broadcast_status(verification_code, "denied", "❌ Login rad etildi va qurilma bloklandi!")
        
        return {"success": True, "message": "Login rad etildi"}
        
    except Exception as e:
        return {"success": False, "message": f"Xatolik: {str(e)}"}


@websocket_router.get("/admin-panel/{verification_code}", response_class=HTMLResponse)
async def admin_2fa_panel(request: Request, verification_code: str):
    """Admin uchun 2FA boshqaruv paneli"""
    try:
        # Verification topish
        verification = await PendingVerification.get_or_none(
            verification_code=verification_code,
            is_used=False
        ).select_related('user')
        
        if not verification:
            return templates.TemplateResponse(
                "error.html",
                {"request": request, "error": "Verification kod topilmadi"}
            )
        
        # Login attempt ma'lumotlari
        attempt = await LoginAttempt.get(id=verification.attempt_id)
        
        return templates.TemplateResponse(
            "admin_2fa_panel.html",
            {
                "request": request,
                "verification_code": verification_code,
                "user": verification.user,
                "attempt": attempt
            }
        )
        
    except Exception as e:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": f"Xatolik: {str(e)}"}
        )


# API endpoints
@websocket_router.get("/api/status/{verification_code}")
async def get_verification_status(verification_code: str):
    """Verification status API"""
    try:
        verification = await PendingVerification.get_or_none(
            verification_code=verification_code,
            is_used=False
        )
        
        if not verification:
            return {"status": "not_found", "message": "Verification kod topilmadi"}
        
        attempt = await LoginAttempt.get(id=verification.attempt_id)
        
        return {
            "status": attempt.status,
            "verification_code": verification_code,
            "is_used": verification.is_used,
            "expires_at": verification.expires_at.isoformat() if verification.expires_at else None
        }
        
    except Exception as e:
        return {"status": "error", "message": f"Xatolik: {str(e)}"}
