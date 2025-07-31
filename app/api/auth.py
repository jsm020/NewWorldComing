"""
Authentication API endpoints - login, register, logout, token management.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from tortoise.exceptions import IntegrityError, DoesNotExist
from tortoise.contrib.pydantic import pydantic_model_creator
from datetime import datetime, timedelta
from typing import Optional

from app.models.user import User, UserCreateIn, UserLoginIn
from app.core.utils import SecurityUtils, RateLimiter, ResponseFormatter
from app.core.security import get_current_user, validate_input_security, rate_limit


# Tortoise Pydantic modeli
User_Pydantic = pydantic_model_creator(User, name="User", exclude=("password_hash",))

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
@rate_limit(3, 60)  # 3 marta 1 daqiqada
async def register(request: Request, user_data: UserCreateIn):
    """Yangi foydalanuvchi ro'yxatdan o'tkazish."""
    
    # Rate limiting
    if RateLimiter.is_rate_limited(request):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Juda ko'p urinish. Biroz kuting."
        )
    
    try:
        # Input sanitization va validation
        clean_username = validate_input_security(user_data.username)
        clean_email = validate_input_security(user_data.email)
        
        # Username va email formatini tekshirish
        if len(clean_username) < 3 or len(clean_username) > 30:
            raise HTTPException(
                status_code=400, 
                detail="Username 3-30 ta belgi orasida bo'lishi kerak"
            )
        
        if "@" not in clean_email or "." not in clean_email:
            raise HTTPException(status_code=400, detail="Email formati noto'g'ri")
        
        # Parol kuchliligini tekshirish
        if len(user_data.password) < 6:
            raise HTTPException(
                status_code=400,
                detail="Parol kamida 6 ta belgidan iborat bo'lishi kerak"
            )
        
        # Parolni hash qilish
        password_hash = SecurityUtils.hash_password(user_data.password)
        
        # Foydalanuvchi yaratish
        user_dict = {
            "username": clean_username,
            "email": clean_email,
            "password_hash": password_hash,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "age": user_data.age,
            "bio": user_data.bio,
        }
        
        # Birth_date ni to'g'ri format qilish
        if user_data.birth_date:
            try:
                birth_date = datetime.strptime(user_data.birth_date, "%Y-%m-%d").date()
                user_dict["birth_date"] = birth_date
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail="Tug'ilgan sana formati noto'g'ri. YYYY-MM-DD formatida kiriting"
                )
        
        user_obj = await User.create(**user_dict)
        
        # Token yaratish
        access_token = SecurityUtils.create_access_token(
            data={"sub": str(user_obj.id), "username": user_obj.username}
        )
        
        # Response
        user_data = await User_Pydantic.from_tortoise_orm(user_obj)
        
        return ResponseFormatter.success(
            data={
                "user": user_data,
                "access_token": access_token,
                "token_type": "bearer",
                "message": "Ro'yxatdan o'tish muvaffaqiyatli yakunlandi"
            },
            message="Muvaffaqiyatli ro'yxatdan o'tdingiz"
        )
        
    except IntegrityError as e:
        error_msg = "Ma'lumot allaqachon mavjud"
        if "username" in str(e):
            error_msg = "Bu username allaqachon ishlatilmoqda"
        elif "email" in str(e):
            error_msg = "Bu email allaqachon ro'yxatdan o'tgan"
        
        raise HTTPException(status_code=400, detail=error_msg)


@router.post("/login", response_model=dict)
@rate_limit(5, 60)  # 5 marta 1 daqiqada
async def login(request: Request, login_data: UserLoginIn):
    """Foydalanuvchi tizimga kirishi."""
    
    # Rate limiting
    if RateLimiter.is_rate_limited(request):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Juda ko'p urinish. 1 daqiqa kuting."
        )
    
    try:
        # Input sanitization
        clean_username = validate_input_security(login_data.username)
        
        # Foydalanuvchini topish
        user = await User.get(username=clean_username)
        
        # Aktiv ekanligini tekshirish
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Hisobingiz faollashtirilmagan"
            )
        
        # Parolni tekshirish
        if not SecurityUtils.verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Username yoki parol noto'g'ri"
            )
        
        # Last login yangilash
        user.last_login = datetime.utcnow()
        await user.save()
        
        # Token yaratish
        access_token = SecurityUtils.create_access_token(
            data={"sub": str(user.id), "username": user.username}
        )
        
        # User ma'lumotlarini olish
        user_data = await User_Pydantic.from_tortoise_orm(user)
        
        return ResponseFormatter.success(
            data={
                "user": user_data,
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": 30 * 60  # 30 daqiqa
            },
            message="Muvaffaqiyatli tizimga kirdingiz"
        )
        
    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username yoki parol noto'g'ri"
        )


@router.post("/logout", response_model=dict)
async def logout(current_user: dict = Depends(get_current_user)):
    """Foydalanuvchi tizimdan chiqishi."""
    
    # Bu yerda token blacklistga qo'shish kerak (Redis yoki DB orqali)
    # Hozircha oddiy response qaytaramiz
    
    return ResponseFormatter.success(
        message="Muvaffaqiyatli tizimdan chiqdingiz"
    )


@router.get("/me", response_model=dict)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Joriy foydalanuvchi ma'lumotlari."""
    
    try:
        user = await User.get(id=current_user["user_id"])
        user_data = await User_Pydantic.from_tortoise_orm(user)
        
        return ResponseFormatter.success(
            data=user_data,
            message="Sizning ma'lumotlaringiz"
        )
        
    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Foydalanuvchi topilmadi"
        )


@router.post("/refresh-token", response_model=dict)
async def refresh_access_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Access tokenni yangilash."""
    
    try:
        # Eski tokenni dekod qilish
        payload = SecurityUtils.decode_access_token(credentials.credentials)
        
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token yaroqsiz yoki muddati tugagan"
            )
        
        # Foydalanuvchini tekshirish
        user = await User.get(id=payload["sub"])
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Hisobingiz faollashtirilmagan"
            )
        
        # Yangi token yaratish
        new_access_token = SecurityUtils.create_access_token(
            data={"sub": str(user.id), "username": user.username}
        )
        
        return ResponseFormatter.success(
            data={
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": 30 * 60
            },
            message="Token muvaffaqiyatli yangilandi"
        )
        
    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Foydalanuvchi topilmadi"
        )


@router.post("/change-password", response_model=dict)
async def change_password(
    old_password: str,
    new_password: str,
    current_user: dict = Depends(get_current_user)
):
    """Parolni o'zgartirish."""
    
    try:
        user = await User.get(id=current_user["user_id"])
        
        # Eski parolni tekshirish
        if not SecurityUtils.verify_password(old_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Eski parol noto'g'ri"
            )
        
        # Yangi parol kuchliligini tekshirish
        if len(new_password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Yangi parol kamida 6 ta belgidan iborat bo'lishi kerak"
            )
        
        # Yangi parolni hash qilish va saqlash
        new_password_hash = SecurityUtils.hash_password(new_password)
        user.password_hash = new_password_hash
        await user.save()
        
        return ResponseFormatter.success(
            message="Parol muvaffaqiyatli o'zgartirildi"
        )
        
    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Foydalanuvchi topilmadi"
        )
