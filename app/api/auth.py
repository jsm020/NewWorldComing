from fastapi import APIRouter, HTTPException, Depends, status, Request
from app.models.user import User, UserIn, UserOut
from app.core.utils import hash_password, verify_password, create_access_token, sanitize_str, is_rate_limited
from tortoise.exceptions import IntegrityError, DoesNotExist

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserOut)
async def register(user: UserIn, request: Request):
    if is_rate_limited(request):
        raise HTTPException(status_code=429, detail="Too many requests")
    try:
        username = sanitize_str(user.username)
        email = sanitize_str(user.email)
        hashed_pw = hash_password(user.username + user.email)  # Demo uchun, realda user.password bo'ladi
        obj = await User.create(username=username, email=email, is_active=True)
        return await UserOut.from_tortoise_orm(obj)
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Username or email already exists")

@router.post("/login")
async def login(user: UserIn, request: Request):
    if is_rate_limited(request):
        raise HTTPException(status_code=429, detail="Too many requests")
    try:
        db_user = await User.get(username=user.username)
        # Demo uchun, realda verify_password(user.password, db_user.hashed_password) bo'ladi
        if db_user.email != user.email:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        access_token = create_access_token({"sub": db_user.username, "user_id": db_user.id})
        return {"access_token": access_token, "token_type": "bearer"}
    except DoesNotExist:
        raise HTTPException(status_code=401, detail="Invalid credentials")
