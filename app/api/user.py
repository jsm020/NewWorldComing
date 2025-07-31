"""
User API endpoints - to'liq CRUD operatsiyalar, xavfsizlik va authentication bilan.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status, Request
from tortoise.exceptions import IntegrityError, DoesNotExist
from tortoise.contrib.pydantic import pydantic_model_creator
from typing import List, Optional
from datetime import datetime, date

from app.models.user import User, UserCreateIn, UserUpdateIn, UserLoginIn, UserOut
from app.core.utils import SecurityUtils, RateLimiter, ResponseFormatter, Utils
from app.core.security import get_current_user, validate_input_security, rate_limit


# Tortoise Pydantic modellari
User_Pydantic = pydantic_model_creator(User, name="User", exclude=("password_hash",))
UserIn_Pydantic = pydantic_model_creator(User, name="UserIn", exclude_readonly=True, exclude=("password_hash",))

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
@rate_limit(5, 60)  # 5 marta 1 daqiqada
async def register_user(request: Request, user_data: UserCreateIn):
    """Yangi foydalanuvchi ro'yxatdan o'tkazish."""
    
    # Rate limiting tekshiruvi
    if RateLimiter.is_rate_limited(request):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Juda ko'p so'rov. Biroz kuting."
        )
    
    try:
        # Input sanitization
        clean_username = validate_input_security(user_data.username)
        clean_email = validate_input_security(user_data.email)
        
        # Validation
        if not Utils.validate_email(clean_email):
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        # Parolni hash qilish
        password_hash = SecurityUtils.hash_password(user_data.password)
        
        # Foydalanuvchi yaratish
        user_dict = user_data.dict(exclude={"password"})
        user_dict.update({
            "username": clean_username,
            "email": clean_email,
            "password_hash": password_hash
        })
        
        # Birth_date ni to'g'ri format qilish
        if user_data.birth_date:
            try:
                birth_date = datetime.strptime(user_data.birth_date, "%Y-%m-%d").date()
                user_dict["birth_date"] = birth_date
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid birth_date format. Use YYYY-MM-DD")
        
        user_obj = await User.create(**user_dict)
        
        # Response
        user_out = await User_Pydantic.from_tortoise_orm(user_obj)
        return ResponseFormatter.success(
            data=user_out,
            message="Foydalanuvchi muvaffaqiyatli ro'yxatdan o'tdi"
        )
        
    except IntegrityError as e:
        error_msg = "Username yoki email allaqachon mavjud"
        if "username" in str(e):
            error_msg = "Bu username allaqachon ishlatilmoqda"
        elif "email" in str(e):
            error_msg = "Bu email allaqachon ro'yxatdan o'tgan"
        raise HTTPException(status_code=400, detail=error_msg)


@router.post("/login", response_model=dict)
@rate_limit(10, 60)  # 10 marta 1 daqiqada
async def login_user(request: Request, login_data: UserLoginIn):
    """Foydalanuvchi tizimga kirishi."""
    
    # Rate limiting
    if RateLimiter.is_rate_limited(request):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Juda ko'p urinish. Biroz kuting."
        )
    
    try:
        # Input sanitization
        clean_username = validate_input_security(login_data.username)
        
        # Foydalanuvchini topish
        user = await User.get(username=clean_username, is_active=True)
        
        # Parolni tekshirish
        if not SecurityUtils.verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Noto'g'ri username yoki parol"
            )
        
        # Last login yangilash
        user.last_login = datetime.utcnow()
        await user.save()
        
        # JWT token yaratish
        access_token = SecurityUtils.create_access_token(
            data={"sub": str(user.id), "username": user.username}
        )
        
        return ResponseFormatter.success(
            data={
                "access_token": access_token,
                "token_type": "bearer",
                "user": await User_Pydantic.from_tortoise_orm(user)
            },
            message="Muvaffaqiyatli tizimga kirildi"
        )
        
    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Noto'g'ri username yoki parol"
        )


@router.get("/", response_model=dict)
async def get_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Barcha foydalanuvchilar ro'yxati (pagination bilan)."""
    
    # Search qilish
    query = User.all()
    if search:
        clean_search = validate_input_security(search)
        query = query.filter(username__icontains=clean_search)
    
    # Pagination
    total_count = await query.count()
    pagination = Utils.calculate_pagination(page, per_page, total_count)
    
    # Ma'lumotlarni olish
    users = await query.offset(pagination["offset"]).limit(per_page)
    users_data = []
    for user in users:
        user_data = await User_Pydantic.from_tortoise_orm(user)
        users_data.append(user_data)
    
    return ResponseFormatter.paginated(
        data=users_data,
        pagination=pagination,
        message="Foydalanuvchilar ro'yxati"
    )


@router.get("/{user_id}", response_model=dict)
async def get_user(
    user_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Bitta foydalanuvchi ma'lumotlarini olish."""
    
    try:
        user = await User.get(id=user_id)
        user_data = await User_Pydantic.from_tortoise_orm(user)
        
        return ResponseFormatter.success(
            data=user_data,
            message="Foydalanuvchi ma'lumotlari"
        )
        
    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Foydalanuvchi topilmadi"
        )


@router.put("/{user_id}", response_model=dict)
async def update_user(
    user_id: int,
    user_update: UserUpdateIn,
    current_user: dict = Depends(get_current_user)
):
    """Foydalanuvchi ma'lumotlarini yangilash."""
    
    try:
        user = await User.get(id=user_id)
        
        # IDOR himoyasi: faqat o'zi yoki admin
        if not SecurityUtils.is_owner_or_admin(
            int(current_user["user_id"]), 
            user.id,
            # Admin tekshiruvi (keyingi versiyalarda qo'shilishi mumkin)
            is_admin=False
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu amalni bajarish huquqingiz yo'q"
            )
        
        # Ma'lumotlarni yangilash
        update_data = user_update.dict(exclude_unset=True)
        
        # Input sanitization
        for key, value in update_data.items():
            if isinstance(value, str):
                update_data[key] = validate_input_security(value)
        
        # Email validatsiyasi
        if "email" in update_data:
            if not Utils.validate_email(update_data["email"]):
                raise HTTPException(status_code=400, detail="Invalid email format")
        
        # Birth_date formatini tekshirish
        if "birth_date" in update_data and update_data["birth_date"]:
            try:
                birth_date = datetime.strptime(update_data["birth_date"], "%Y-%m-%d").date()
                update_data["birth_date"] = birth_date
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid birth_date format. Use YYYY-MM-DD")
        
        # Yangilash
        await user.update_from_dict(update_data)
        await user.save()
        
        updated_user = await User_Pydantic.from_tortoise_orm(user)
        
        return ResponseFormatter.success(
            data=updated_user,
            message="Foydalanuvchi ma'lumotlari yangilandi"
        )
        
    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Foydalanuvchi topilmadi"
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email allaqachon ishlatilmoqda"
        )


@router.delete("/{user_id}", response_model=dict)
async def delete_user(
    user_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Foydalanuvchini o'chirish."""
    
    try:
        user = await User.get(id=user_id)
        
        # IDOR himoyasi: faqat o'zi yoki admin
        if not SecurityUtils.is_owner_or_admin(
            int(current_user["user_id"]), 
            user.id,
            is_admin=False
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu amalni bajarish huquqingiz yo'q"
            )
        
        # Soft delete (is_active = False) yoki hard delete
        # Bu misolda soft delete qilamiz
        user.is_active = False
        await user.save()
        
        return ResponseFormatter.success(
            message="Foydalanuvchi muvaffaqiyatli o'chirildi"
        )
        
    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Foydalanuvchi topilmadi"
        )


@router.get("/me/profile", response_model=dict)
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    """Joriy foydalanuvchi profili."""
    
    try:
        user = await User.get(id=current_user["user_id"])
        user_data = await User_Pydantic.from_tortoise_orm(user)
        
        return ResponseFormatter.success(
            data=user_data,
            message="Sizning profilingiz"
        )
        
    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Foydalanuvchi topilmadi"
        )
