# ISHLATISH YO'RIQNOMASI

## 1. Muhit va kutubxonalarni tayyorlash

Python 3.9+ o'rnatilgan bo'lishi kerak.

Terminalda:
```
pip install -r requirements.txt
```

## 2. Ma'lumotlar bazasi sozlash

Standart holatda SQLite ishlaydi. Agar PostgreSQL yoki boshqa DB ishlatmoqchi bo'lsangiz, muhit o'zgaruvchisini belgilang:

```
export DB_URL="postgres://user:password@localhost:5432/dbname"
```

## 3. Ilovani ishga tushirish

```
uvicorn app.main:app --reload
```

Brauzerda yoki Postman orqali:
- `GET /` — Loyihaning ishlashini tekshirish
- `POST /auth/register` — Foydalanuvchi ro'yxatdan o'tkazish
- `POST /auth/login` — Login va JWT olish
- `GET /users/{user_id}` — Foydalanuvchini olish

## 4. Testlarni ishga tushirish

```
pip install pytest httpx
pytest tests/
```

## 5. Yangi model yoki endpoint qo'shish

1. `app/models/` papkasida yangi model yozing (README yuqorisidagi namunaga qarang)
2. `config/tortoise_config.py` faylida modelni ro'yxatga qo'shing
3. `app/api/` papkasida yangi endpoint yozing va `main.py` ga routerini ulang

## 6. Xavfsizlik va kengaytirish

Loyihada asosiy xavfsizlik util'lari va kengaytirish uchun barcha imkoniyatlar mavjud (README yuqorisiga qarang).

Savollar yoki kengaytirish uchun: koddagi komment va util'larni o'qing yoki yangi fayl qo'shing.
## Xavfsizlik va kengaytiriladigan arxitektura

Loyihada asosiy xavfsizlik util'lari va kengaytirish uchun quyidagilar mavjud:

- **Input sanitizatsiya:** XSS va boshqa hujumlarga qarshi (`sanitize_str`)
- **Parol xeshlash:** Parollarni xavfsiz saqlash va tekshirish (`hash_password`, `verify_password`)
- **JWT autentifikatsiya:** Token generatsiya va tekshirish (`create_access_token`, `decode_access_token`)
- **CORS:** Faqat kerakli domenlarga ruxsat (`main.py`)
- **Rate limiting:** Oddiy IP bo‘yicha cheklov (`is_rate_limited`)
- **Sensitive data exposure:** Pydantic schema orqali maxfiy maydonlarni yashirish (`SafeUserOut`)
- **IDOR:** Faqat egasi yoki admin kirishi uchun util (`is_owner_or_admin`)
- **Fayl yuklash xavfsizligi:** Fayl nomi va yo‘lini tekshirish (`secure_filename`, `is_safe_path`)

Loyihani kengaytirish uchun har bir modul (api, model, util) alohida papkada va mustaqil ishlaydi. Yangi model, endpoint yoki util qo‘shish uchun shunchaki mos papkaga yangi fayl qo‘shing va `config/tortoise_config.py` yoki `main.py` da ro‘yxatga kiriting.
## Tortoise ORM modelini yozish

Yangi model yaratish uchun `app/models/` papkasida yangi fayl oching va quyidagiga o‘xshash tarzda yozing:

```
from tortoise import fields
from tortoise.models import Model

class Book(Model):
   id = fields.IntField(pk=True)
   title = fields.CharField(max_length=100)
   author = fields.CharField(max_length=100)
   published = fields.DateField(null=True)

   class Meta:
      table = "books"
```

Modelni ro‘yxatga qo‘shish uchun `config/tortoise_config.py` faylida `"models": [ ... ]` ro‘yxatiga yangi model modulini qo‘shing:

```
"models": [
   "app.models.user",
   "app.models.book",  # yangi model
]
```

Pydantic schema va endpointlar uchun ham shunga o‘xshash tarzda yangi fayl va kod yozing.
# NewWorldComing# README.md

## FastAPI + Tortoise ORM asosiy shablon

### Ishga tushirish

1. Kutubxonalarni o‘rnating:
   ```
   pip install -r requirements.txt
   ```

2. Ilovani ishga tushiring:
   ```
   uvicorn app.main:app --reload
   ```

3. Tortoise ORM konfiguratsiyasi va migratsiya uchun keyingi bosqichlarda kodlar qo‘shiladi.

### Ma'lumotlar bazasini ulash

Loyiha SQLite bilan ishlashga tayyor. Agar PostgreSQL yoki boshqa DB ishlatmoqchi bo‘lsangiz, `DB_URL` muhit o‘zgaruvchisini quyidagicha belgilang:

**PostgreSQL uchun:**
```
export DB_URL="postgres://user:password@localhost:5432/dbname"
```

**MySQL uchun:**
```
export DB_URL="mysql://user:password@localhost:3306/dbname"
```

**Ishga tushirish:**
```
uvicorn app.main:app --reload
```

**Eslatma:**
`config/tortoise_config.py` faylida barcha asosiy sozlamalar va izohlar bor.