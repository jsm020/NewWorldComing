
"""
Tortoise ORM konfiguratsiyasi - turli ma'lumotlar bazalari uchun.

Qo'llab-quvvatlanadigan ma'lumotlar bazalari:
- SQLite: "sqlite://db.sqlite3" 
- PostgreSQL: "postgres://user:password@localhost:5432/dbname"
- MySQL: "mysql://user:password@localhost:3306/dbname"

Environment variables orqali konfiguratsiya:
- DB_URL: Ma'lumotlar bazasi connection string
- DB_TYPE: Database turi (sqlite, postgres, mysql)
"""

import os
from decouple import config

# Environment variables
DB_TYPE = config('DB_TYPE', default='sqlite')
DB_HOST = config('DB_HOST', default='localhost')
DB_PORT = config('DB_PORT', default='5432')
DB_NAME = config('DB_NAME', default='newworld')
DB_USER = config('DB_USER', default='user')
DB_PASSWORD = config('DB_PASSWORD', default='password')

# Database URL generation
def get_database_url():
    """Ma'lumotlar bazasi URL ni yaratish."""
    if DB_TYPE == 'sqlite':
        return config('DB_URL', default='sqlite://db.sqlite3')
    elif DB_TYPE == 'postgres':
        return f"postgres://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    elif DB_TYPE == 'mysql':
        return f"mysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    else:
        return config('DB_URL', default='sqlite://db.sqlite3')

DB_URL = get_database_url()

# Tortoise ORM konfiguratsiyasi
TORTOISE_ORM = {
    "connections": {
        "default": DB_URL
    },
    "apps": {
        "models": {
            "models": [
                "app.models.user",           # User modeli
                # "app.models.product",      # Misol uchun product modeli
                # "app.models.order",        # Misol uchun order modeli
                "aerich.models",            # Migration uchun aerich
            ],
            "default_connection": "default",
        },
    },
    "use_tz": True,
    "timezone": "UTC",
}

# Test uchun alohida konfiguratsiya
TORTOISE_ORM_TEST = {
    "connections": {
        "default": "sqlite://:memory:"  # In-memory database for tests
    },
    "apps": {
        "models": {
            "models": [
                "app.models.user",
                "aerich.models",
            ],
            "default_connection": "default",
        },
    },
    "use_tz": True,
    "timezone": "UTC",
}

# Production konfiguratsiyasi
TORTOISE_ORM_PROD = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "host": DB_HOST,
                "port": int(DB_PORT),
                "user": DB_USER,
                "password": DB_PASSWORD,
                "database": DB_NAME,
                "ssl": "require",  # Production uchun SSL talab qilish
            }
        }
    },
    "apps": {
        "models": {
            "models": [
                "app.models.user",
                "aerich.models",
            ],
            "default_connection": "default",
        },
    },
    "use_tz": True,
    "timezone": "UTC",
}
