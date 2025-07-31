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
CREATE TABLE IF NOT EXISTS "articles" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "title" VARCHAR(200) NOT NULL,
    "slug" VARCHAR(250) NOT NULL UNIQUE,
    "content" TEXT NOT NULL,
    "excerpt" VARCHAR(500),
    "featured_image" VARCHAR(500),
    "is_published" INT NOT NULL DEFAULT 0,
    "is_featured" INT NOT NULL DEFAULT 0,
    "category" VARCHAR(100),
    "tags" VARCHAR(500),
    "meta_title" VARCHAR(200),
    "meta_description" VARCHAR(300),
    "view_count" INT NOT NULL DEFAULT 0,
    "published_at" TIMESTAMP,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "author_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
) /* Article model for blog posts and news articles. */;
CREATE TABLE IF NOT EXISTS "pages" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "title" VARCHAR(200) NOT NULL,
    "slug" VARCHAR(250) NOT NULL UNIQUE,
    "content" TEXT NOT NULL,
    "excerpt" VARCHAR(500),
    "featured_image" VARCHAR(500),
    "is_published" INT NOT NULL DEFAULT 1,
    "is_homepage" INT NOT NULL DEFAULT 0,
    "template" VARCHAR(100) NOT NULL DEFAULT 'default',
    "meta_title" VARCHAR(200),
    "meta_description" VARCHAR(300),
    "custom_css" TEXT,
    "custom_js" TEXT,
    "sort_order" INT NOT NULL DEFAULT 0,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "author_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
) /* Page model for static pages like About, Contact, etc. */;
CREATE TABLE IF NOT EXISTS "settings" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "key" VARCHAR(100) NOT NULL UNIQUE,
    "value" TEXT NOT NULL,
    "description" VARCHAR(500),
    "category" VARCHAR(50) NOT NULL DEFAULT 'general',
    "is_public" INT NOT NULL DEFAULT 0,
    "data_type" VARCHAR(20) NOT NULL DEFAULT 'string',
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) /* Settings model for storing application configuration. */;
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSON NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
