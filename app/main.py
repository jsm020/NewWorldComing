# app/main.py
# FastAPI asosiy ilova

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.utils import global_exception_handler
from tortoise.contrib.fastapi import register_tortoise
from app.api import user
from app.api import auth
from config.tortoise_config import TORTOISE_ORM



app = FastAPI()

# CORS middleware: faqat kerakli domenlarga ruxsat berish
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:3000"],  # kerakli domenlarni yozing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global error handler
app.add_exception_handler(Exception, global_exception_handler)


# User va Auth routerlarini ulash
app.include_router(user.router)
app.include_router(auth.router)

@app.get("/")
async def root():
    """
    Root endpoint. Loyihaning ishlayotganini tekshirish uchun.
    """
    return {"message": "FastAPI + Tortoise ORM base template ishlayapti"}

# Tortoise ORM ni FastAPI bilan integratsiya qilish
# DB_URL ni .env yoki muhit o'zgaruvchisi orqali o'zgartirish mumkin (Postgres, SQLite va boshqalar uchun)
register_tortoise(
    app,
    config=TORTOISE_ORM,
    generate_schemas=True,  # Dastlabki ishga tushirishda sxemalarni avtomatik yaratadi
    add_exception_handlers=True,
)