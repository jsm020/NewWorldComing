
# app/models/user.py
# Tortoise ORM model: User

from tortoise import fields
from tortoise.models import Model
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class User(Model):
    """
    Foydalanuvchi modeli (User) - barcha Tortoise ORM fieldlarini namoyish qilish uchun
    """
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=50, unique=True)
    email = fields.CharField(max_length=255, unique=True)
    password_hash = fields.CharField(max_length=255)
    first_name = fields.CharField(max_length=50, null=True)
    last_name = fields.CharField(max_length=50, null=True)
    is_active = fields.BooleanField(default=True)
    is_superuser = fields.BooleanField(default=False)
    age = fields.IntField(null=True)
    balance = fields.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    bio = fields.TextField(null=True)
    rating = fields.FloatField(null=True)
    birth_date = fields.DateField(null=True)
    last_login = fields.DatetimeField(null=True)
    profile_picture = fields.CharField(max_length=500, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "users"

    def __str__(self):
        return f"User: {self.username}"

# Pydantic schema: input uchun (user yaratish va yangilash)
class UserCreateIn(BaseModel):
    username: str
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    age: Optional[int] = None
    bio: Optional[str] = None
    birth_date: Optional[str] = None  # YYYY-MM-DD format

class UserUpdateIn(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    age: Optional[int] = None
    bio: Optional[str] = None
    birth_date: Optional[str] = None
    is_active: Optional[bool] = None

class UserLoginIn(BaseModel):
    username: str
    password: str

# Pydantic schema: output uchun (xavfsiz - parolsiz)
class UserOut(BaseModel):
    id: int
    username: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    is_active: bool
    age: Optional[int]
    balance: float
    bio: Optional[str]
    rating: Optional[float]
    birth_date: Optional[str]
    profile_picture: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
