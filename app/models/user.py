
# Tortoise ORM model: User
from tortoise import fields
from tortoise.models import Model
from pydantic import BaseModel, EmailStr

class User(Model):
    """
    Foydalanuvchi modeli (User)
    """
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=50, unique=True)
    email = fields.CharField(max_length=255, unique=True)
    is_active = fields.BooleanField(default=True)

    class Meta:
        table = "users"

# Pydantic schema: input uchun
class UserIn(BaseModel):
    username: str
    email: EmailStr

# Pydantic schema: output uchun
class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool

    class Config:
        orm_mode = True
