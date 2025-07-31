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
# NewWorldComing# # FastAPI + Tortoise ORM Template

🚀 **Django o'rniga ishlatish uchun to'liq FastAPI shablon**

Bu shablon Django ORM o'rniga **Tortoise ORM** ishlatib, to'liq xavfsizlik choralari va best practice'lar bilan yaratilgan production-ready FastAPI template.

## 📋 Xususiyatlar

### 🔐 Xavfsizlik
- **SQL Injection himoyasi** - Tortoise ORM parametrizatsiya
- **XSS himoyasi** - Input sanitization va validation
- **CSRF himoyasi** - JWT token va security headers
- **Rate Limiting** - Har bir endpoint uchun so'rov cheklash
- **Authentication** - JWT token asosida
- **Input Validation** - Pydantic schema validation
- **Security Headers** - Barcha kerakli security headerlar

### 🛠 Texnik Stack
- **FastAPI** - Async web framework
- **Tortoise ORM** - Async ORM (Django ORM o'rniga)
- **SQLite/PostgreSQL/MySQL** - Database support
- **JWT** - Authentication
- **Pydantic** - Data validation
- **Uvicorn** - ASGI server

### 📁 Loyiha Tuzilmasi
```
├── app/
│   ├── api/                 # API endpoints
│   │   ├── auth.py         # Authentication endpoints
│   │   └── user.py         # User CRUD endpoints
│   ├── core/               # Core functionality
│   │   ├── security.py     # Security utilities
│   │   └── utils.py        # General utilities
│   ├── models/             # Database models
│   │   └── user.py         # User model
│   └── main.py             # FastAPI application
├── config/
│   └── tortoise_config.py  # Database configuration
├── tests/                  # Test files
│   └── test_auth.py        # Authentication tests
├── requirements.txt        # Dependencies
├── .env                    # Environment variables
└── README.md              # This file
```

## 🚀 Ishga Tushirish

### 1. Repository ni clone qilish
```bash
git clone <repository-url>
cd NewWorldComing
```

### 2. Virtual environment yaratish
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# yoki
.venv\Scripts\activate     # Windows
```

### 3. Kutubxonalarni o'rnatish
```bash
pip install -r requirements.txt
```

### 4. Environment variables sozlash
`.env` faylini tahrirlang:
```env
SECRET_KEY=your-super-secret-key-here
DB_TYPE=sqlite
DB_URL=sqlite://db.sqlite3
```

### 5. Ma'lumotlar bazasini yaratish
```bash
# Tortoise ORM migration
aerich init -t config.tortoise_config.TORTOISE_ORM --location ./migrations
aerich init-db
```

### 6. Serverni ishga tushirish
```bash
uvicorn app.main:app --reload
```

Server `http://localhost:8000` da ishga tushadi.

## 📖 API Documentation

### 🔗 API Endpoints

#### Swagger UI
- **Documentation**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

#### Health Check
```bash
GET /health
```

#### Authentication
```bash
POST /api/v1/auth/register    # Ro'yxatdan o'tish
POST /api/v1/auth/login       # Tizimga kirish
POST /api/v1/auth/logout      # Tizimdan chiqish
GET  /api/v1/auth/me          # Joriy user ma'lumotlari
POST /api/v1/auth/refresh-token  # Token yangilash
POST /api/v1/auth/change-password # Parol o'zgartirish
```

#### User Management
```bash
GET    /api/v1/users/         # Barcha userlar (pagination)
GET    /api/v1/users/{id}     # Bitta user
PUT    /api/v1/users/{id}     # User yangilash
DELETE /api/v1/users/{id}     # User o'chirish
GET    /api/v1/users/me/profile # Mening profilim
```

### 📝 API Ishlatish Misollari

#### 1. Ro'yxatdan o'tish
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com", 
    "password": "securepassword123",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

#### 2. Tizimga kirish
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "securepassword123"
  }'
```

#### 3. Token bilan API ishlatish
```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🛠 Yangi Model Yaratish

### 1. Model yaratish (`app/models/product.py`)
```python
from tortoise import fields
from tortoise.models import Model

class Product(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100)
    price = fields.DecimalField(max_digits=10, decimal_places=2)
    description = fields.TextField(null=True)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "products"
```

### 2. Pydantic Schema yaratish
```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProductIn(BaseModel):
    name: str
    price: float
    description: Optional[str] = None

class ProductOut(BaseModel):
    id: int
    name: str
    price: float
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

### 3. API yaratish (`app/api/product.py`)
```python
from fastapi import APIRouter, Depends, HTTPException
from tortoise.contrib.pydantic import pydantic_model_creator
from app.models.product import Product
from app.core.security import get_current_user

router = APIRouter(prefix="/products", tags=["products"])
Product_Pydantic = pydantic_model_creator(Product, name="Product")

@router.get("/", response_model=dict)
async def get_products(current_user = Depends(get_current_user)):
    products = await Product_Pydantic.from_queryset(Product.all())
    return {"success": True, "data": products}

@router.post("/", response_model=dict)
async def create_product(
    product_data: ProductIn,
    current_user = Depends(get_current_user)
):
    product = await Product.create(**product_data.dict())
    product_out = await Product_Pydantic.from_tortoise_orm(product)
    return {"success": True, "data": product_out}
```

### 4. Router ni main.py ga qo'shish
```python
from app.api import product

app.include_router(product.router, prefix="/api/v1")
```

### 5. Model ni konfiguratsiyaga qo'shish
`config/tortoise_config.py` da:
```python
"models": [
    "app.models.user",
    "app.models.product",  # Yangi model
    "aerich.models",
],
```

## 🔐 Xavfsizlik Best Practices

### 1. Input Validation
```python
from app.core.security import validate_input_security

# Har bir input ni sanitize qiling
clean_input = validate_input_security(user_input)
```

### 2. Authentication Check
```python
from app.core.security import get_current_user

@router.get("/protected")
async def protected_endpoint(current_user = Depends(get_current_user)):
    # Faqat autentifikatsiyadan o'tgan userlar kirishi mumkin
    return {"user_id": current_user["user_id"]}
```

### 3. Rate Limiting
```python
from app.core.security import rate_limit

@router.post("/sensitive-action")
@rate_limit(5, 60)  # 5 marta 1 daqiqada
async def sensitive_action():
    # Rate limited endpoint
    pass
```

### 4. IDOR Himoyasi
```python
from app.core.utils import SecurityUtils

# Faqat egasi yoki admin kirishi mumkin
if not SecurityUtils.is_owner_or_admin(current_user_id, resource_owner_id):
    raise HTTPException(status_code=403, detail="Access denied")
```

## 🧪 Testlar

### Testlarni ishga tushirish
```bash
pytest tests/ -v
```

### Yangi test yozish
```python
@pytest.mark.asyncio
async def test_new_feature():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/new-endpoint")
        assert response.status_code == 200
```

## 🔧 Production uchun Tayyorlash

### 1. Environment Variables
```env
SECRET_KEY=production-secret-key-32-chars-min
DB_TYPE=postgres
DB_HOST=your-postgres-host
DB_NAME=your-database-name
DB_USER=your-username
DB_PASSWORD=your-password
DEBUG=false
ENVIRONMENT=production
```

### 2. Docker bilan Deploy
`Dockerfile` yaratish:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3. Database Migration
```bash
aerich migrate --name "initial"
aerich upgrade
```

## 🤝 Contributing

1. Fork qiling
2. Feature branch yarating (`git checkout -b feature/amazing-feature`)
3. Commit qiling (`git commit -m 'Add amazing feature'`)
4. Push qiling (`git push origin feature/amazing-feature`)
5. Pull Request oching

## 📞 Yordam

Agar savollaringiz bo'lsa:

- 📧 Email: developer@example.com
- 📖 Documentation: `/docs`
- 🐛 Issues: GitHub Issues

## 📄 License

MIT License - batafsil ma'lumot uchun `LICENSE` faylini ko'ring.

---

⭐ **Agar bu shablon foydali bo'lsa, star bering!**

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