# NewWorldComing Admin Panel

Bu loyihada zamonaviy va foydalanuvchiga qulay admin panel yaratildi. Admin panel FastAPI + Jinja2 Templates yordamida ishlab chiqilgan va to'liq responsive design ga ega.

## 🚀 Xususiyatlar

### 1. Dashboard
- **Statistika kartochkalari**: Jami foydalanuvchilar, maqolalar, sahifalar
- **So'nggi faollik**: Yangi foydalanuvchilar va maqolalar ro'yxati
- **Tezkor amallar**: Tizimning asosiy funksiyalariga tezkor kirish

### 2. Foydalanuvchilar boshqaruvi
- ✅ Foydalanuvchilar ro'yxati (pagination bilan)
- ✅ Qidirish funksiyasi
- ✅ Yangi foydalanuvchi yaratish
- ✅ Foydalanuvchi tahrirlash
- ✅ Foydalanuvchi o'chirish
- ✅ Admin/superuser huquqlari boshqaruvi
- ✅ Foydalanuvchi profili ko'rish

### 3. Kontent boshqaruvi
- ✅ Maqolalar modeli (Article)
- ✅ Sahifalar modeli (Page)
- ✅ Maqolalar ro'yxati va boshqaruv
- ✅ Status filtrlari (Nashr etilgan, Qoralama, Tanlangan)
- ✅ SEO sozlamalari (meta title, description)
- ✅ Media yuklash imkoniyati

### 4. Sozlamalar boshqaruvi
- ✅ Sayt sozlamalari (nom, tavsif, URL)
- ✅ Email sozlamalari (SMTP)
- ✅ Funksiya sozlamalari (ro'yxatdan o'tish, kommentlar)
- ✅ Ko'rinish sozlamalari (tema, CSS, JS)
- ✅ Tezkor amallar (cache tozalash, DB optimizatsiya)

### 5. Xavfsizlik
- ✅ JWT token autentifikatsiya
- ✅ Session-based admin login
- ✅ Role-based access control
- ✅ CSRF himoyasi
- ✅ Input sanitization

### 6. UI/UX Dizayn
- ✅ Bootstrap 5 ga asoslangan zamonaviy dizayn
- ✅ Responsive design (mobil, planshet, desktop)
- ✅ Dark sidebar navigation
- ✅ Beautiful gradient backgrounds
- ✅ Interactive elements
- ✅ Toast notifications
- ✅ Modal dialogs

## 📁 Tuzilma

```
app/
├── admin/                  # Admin panel
│   ├── __init__.py
│   ├── auth.py            # Admin autentifikatsiya
│   └── routes.py          # Admin marshrullari
├── models/                # Ma'lumotlar modellari
│   ├── user.py           # Foydalanuvchi modeli
│   ├── article.py        # Maqola modeli
│   ├── page.py           # Sahifa modeli
│   └── settings.py       # Sozlamalar modeli
├── templates/admin/       # Admin panel shablonlari
│   ├── base.html         # Asosiy shablon
│   ├── dashboard.html    # Dashboard
│   ├── login.html        # Login sahifasi
│   ├── settings.html     # Sozlamalar
│   └── users/            # Foydalanuvchilar shablonlari
│       ├── list.html
│       ├── create.html
│       └── detail.html
└── static/               # Statik fayllar
    ├── css/admin.css     # Admin panel CSS
    └── js/admin.js       # Admin panel JavaScript
```

## 🛠 Ishlatish

### 1. Admin paneliga kirish
```
http://localhost:8000/admin/login
```

### 2. Test foydalanuvchi yaratish
```bash
# API orqali foydalanuvchi yaratish
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "admin123"
  }'

# Foydalanuvchini superuser qilish
python -c "
import asyncio
from tortoise import Tortoise
from app.models.user import User
from config.tortoise_config import TORTOISE_ORM

async def make_admin():
    await Tortoise.init(config=TORTOISE_ORM)
    user = await User.get(username='admin')
    user.is_superuser = True
    await user.save()
    await Tortoise.close_connections()

asyncio.run(make_admin())
"
```

### 3. Standart sozlamalarni yaratish
```bash
python -c "
import asyncio
from tortoise import Tortoise
from app.models.settings import Setting, DEFAULT_SETTINGS
from config.tortoise_config import TORTOISE_ORM

async def create_defaults():
    await Tortoise.init(config=TORTOISE_ORM)
    for category, settings in DEFAULT_SETTINGS.items():
        for key, value in settings.items():
            existing = await Setting.get_or_none(key=key)
            if not existing:
                await Setting.create(
                    key=key, value=str(value), category=category,
                    is_public=key in ['site_name', 'site_description']
                )
    await Tortoise.close_connections()

asyncio.run(create_defaults())
"
```

## 🎨 Dizayn xususiyatlari

### Ranglar
- **Primary**: #007bff (ko'k)
- **Success**: #28a745 (yashil)
- **Warning**: #ffc107 (sariq)
- **Danger**: #dc3545 (qizil)
- **Dark**: #343a40 (qora kulrang)

### Responsive breakpoints
- **Mobile**: < 768px
- **Tablet**: 768px - 1024px
- **Desktop**: > 1024px

### Font iconlar
Bootstrap Icons to'plamidan foydalanilgan:
- `bi-speedometer2` - Dashboard
- `bi-people` - Foydalanuvchilar
- `bi-newspaper` - Maqolalar
- `bi-gear` - Sozlamalar

## 🔧 Kengaytirish

### Yangi model qo'shish
1. `app/models/` da yangi model yarating
2. `config/tortoise_config.py` ga qo'shing
3. Migration yarating: `aerich migrate --name "add_new_model"`
4. Admin routes va templates yarating

### Yangi sahifa qo'shish
1. `app/admin/routes.py` ga yangi route qo'shing
2. `app/templates/admin/` da yangi template yarating
3. Navigation menuga link qo'shing

### CSS/JS qo'shish
1. `app/static/css/admin.css` ga CSS qo'shing
2. `app/static/js/admin.js` ga JavaScript qo'shing
3. Template da `extra_css` yoki `extra_js` blokidan foydalaning

## 📱 Mobile Support

Admin panel mobil qurilmalarda to'liq ishlaydi:
- Responsive navigation
- Touch-friendly buttons
- Optimized forms
- Mobile-first design

## 🔒 Xavfsizlik

- JWT token autentifikatsiya
- Session-based admin access
- CSRF protection
- Input sanitization
- Role-based permissions
- Secure password hashing

## 🎯 Kelajakdagi yangilanishlar

- [ ] Rich text editor (TinyMCE/CKEditor)
- [ ] File upload management
- [ ] Email templates
- [ ] Backup/restore functionality
- [ ] Activity logs
- [ ] Multi-language support
- [ ] Dark/Light theme toggle
- [ ] Advanced user permissions
- [ ] API documentation integration
- [ ] Real-time notifications

## 📞 Yordam

Agar savollaringiz bo'lsa:
- 📧 Email: developer@example.com
- 📖 Documentation: `/admin/docs`
- 🐛 Issues: GitHub Issues

---

⭐ **Agar bu admin panel foydali bo'lsa, star bering!**