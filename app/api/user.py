from fastapi import APIRouter, HTTPException
from tortoise.exceptions import IntegrityError, DoesNotExist
from app.models.user import User, UserIn, UserOut

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserOut)
async def create_user(user: UserIn):
    try:
        obj = await User.create(**user.dict())
        return await UserOut.from_tortoise_orm(obj)
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Username or email already exists")

@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: int):
    try:
        user = await User.get(id=user_id)
        return await UserOut.from_tortoise_orm(user)
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="User not found")
