"""
2FA Verification Status Check API
"""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.models.admin_security import PendingVerification, LoginAttempt

router = APIRouter(prefix="/admin/2fa", tags=["2FA Status"])

@router.get("/status/{verification_code}")
async def check_verification_status(verification_code: str, request: Request):
    """Verification holatini tekshirish"""
    try:
        # Verification topish
        verification = await PendingVerification.get_or_none(
            verification_code=verification_code
        ).select_related('user')
        
        if not verification:
            return JSONResponse({
                "status": "not_found",
                "message": "Verification kod topilmadi"
            })
        
        # Login attempt ni tekshirish
        attempt = await LoginAttempt.get(id=verification.attempt_id)
        
        if attempt.status == "confirmed":
            # Tasdiqlangan - session yaratish
            request.session["user_id"] = verification.user.id
            
            # User last_login yangilash
            from app.models.user import User
            from datetime import datetime
            user = await User.get(id=verification.user.id)
            user.last_login = datetime.now()
            await user.save()
            
            return JSONResponse({
                "status": "confirmed",
                "message": "Login tasdiqlandi",
                "redirect": "/admin/dashboard"
            })
            
        elif attempt.status == "denied":
            return JSONResponse({
                "status": "denied",
                "message": "Login rad etildi"
            })
        else:
            return JSONResponse({
                "status": "pending",
                "message": "Hali javob kutilmoqda"
            })
            
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "message": f"Xatolik: {str(e)}"
        })
