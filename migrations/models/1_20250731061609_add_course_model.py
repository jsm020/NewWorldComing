from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "courses" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" VARCHAR(200) NOT NULL /* Kurs nomi */,
    "description" TEXT /* Kurs tavsifi */,
    "duration_hours" INT NOT NULL /* Kurs davomiyligi (soat) */,
    "price" VARCHAR(40) NOT NULL /* Narx */,
    "is_active" INT NOT NULL DEFAULT 1 /* Faol holati */,
    "instructor_name" VARCHAR(100) NOT NULL /* O'qituvchi ismi */,
    "start_date" DATE /* Boshlanish sanasi */,
    "max_students" INT NOT NULL DEFAULT 20 /* Maksimal talabalar soni */,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) /* Kurs modeli */;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "courses";"""
