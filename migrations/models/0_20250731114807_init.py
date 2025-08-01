from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "users" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "username" VARCHAR(50) NOT NULL UNIQUE,
    "email" VARCHAR(255) NOT NULL UNIQUE,
    "password_hash" VARCHAR(255) NOT NULL,
    "first_name" VARCHAR(50),
    "last_name" VARCHAR(50),
    "is_active" INT NOT NULL DEFAULT 1,
    "is_superuser" INT NOT NULL DEFAULT 0,
    "age" INT,
    "balance" VARCHAR(40) NOT NULL DEFAULT 0,
    "bio" TEXT,
    "rating" REAL,
    "birth_date" DATE,
    "last_login" TIMESTAMP,
    "profile_picture" VARCHAR(500),
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) /* Foydalanuvchi modeli (User) - barcha Tortoise ORM fieldlarini namoyish qilish uchun */;
CREATE TABLE IF NOT EXISTS "admin_security" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "telegram_enabled" INT NOT NULL DEFAULT 0 /* Telegram 2FA yoqilganmi */,
    "telegram_bot_token" VARCHAR(500) /* Telegram bot token */,
    "telegram_chat_id" VARCHAR(100) /* Telegram chat ID */,
    "telegram_username" VARCHAR(100) /* Telegram username */,
    "require_confirmation" INT NOT NULL DEFAULT 1 /* Login tasdiqlash talab qilinsinmi */,
    "auto_block_suspicious" INT NOT NULL DEFAULT 1 /* Shubhali faollik avtomatik bloklansinmi */,
    "max_failed_attempts" INT NOT NULL DEFAULT 3 /* Maksimal muvaffaqiyatsiz urinishlar */,
    "last_login_ip" VARCHAR(45) /* Oxirgi IP manzil */,
    "last_login_device" VARCHAR(500) /* Oxirgi qurilma ma'lumoti */,
    "last_login_location" VARCHAR(200) /* Oxirgi joylashuv */,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "last_activity" TIMESTAMP /* Oxirgi faollik */,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
) /* Admin panel 2FA xavfsizlik modeli */;
CREATE TABLE IF NOT EXISTS "device_blocks" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "ip_address" VARCHAR(45) NOT NULL /* IP manzil */,
    "user_agent" TEXT NOT NULL /* Browser\/qurilma ma'lumoti */,
    "device_fingerprint" VARCHAR(500) /* Qurilma fingerprint */,
    "reason" VARCHAR(200) NOT NULL /* Blok sababi */,
    "blocked_by" VARCHAR(100) NOT NULL DEFAULT 'system' /* Kim tomonidan bloklangan */,
    "is_active" INT NOT NULL DEFAULT 1 /* Blok faolmi */,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "blocked_until" TIMESTAMP /* Blok tugash vaqti */,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
) /* Bloklangan qurilmalar ro'yxati */;
CREATE TABLE IF NOT EXISTS "login_attempts" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "ip_address" VARCHAR(45) NOT NULL /* IP manzil */,
    "user_agent" TEXT NOT NULL /* Qurilma ma'lumoti */,
    "location" VARCHAR(200) /* Joylashuv */,
    "status" VARCHAR(20) NOT NULL DEFAULT 'pending' /* Status: pending, sent, confirmed, denied, failed */,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
) /* Login urinishlari tarixi */;
CREATE TABLE IF NOT EXISTS "pending_verifications" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "verification_code" VARCHAR(50) NOT NULL UNIQUE /* Tasdiqlash kodi */,
    "attempt_id" INT NOT NULL /* Login attempt ID */,
    "is_used" INT NOT NULL DEFAULT 0 /* Ishlatilganmi */,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "expires_at" TIMESTAMP NOT NULL /* Tasdiqlash tugash vaqti */,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
) /* Kutilayotgan tasdiqlovlar */;
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSON NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
