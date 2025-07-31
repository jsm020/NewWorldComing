
"""
    Tortoise ORM konfiguratsiyasi.

    - SQLite uchun: "sqlite://db.sqlite3"
    - PostgreSQL uchun: "postgres://user:password@localhost:5432/dbname"
    - MySQL uchun: "mysql://user:password@localhost:3306/dbname"

    Kerakli connection string-ni tanlang yoki .env orqali o'zgartiring.
    """

    import os

    DB_URL = os.getenv("DB_URL", "sqlite://db.sqlite3")  # Standart: SQLite, lekin istalgan connection string bo'lishi mumkin

    TORTOISE_ORM = {
        "connections": {"default": DB_URL},
        "apps": {
            "models": {
                "models": [
                    "app.models.user",  # Barcha modellaringiz shu ro'yxatda bo'lishi kerak
                    # "aerich.models",  # Agar migratsiya uchun aerich ishlatilsa, izohdan chiqaring
                ],
                "default_connection": "default",
            },
        },
    }
