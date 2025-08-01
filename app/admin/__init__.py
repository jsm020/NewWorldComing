"""
FastAPI Admin panel - Django admin ga o'xshash
Oddiy HTML/CSS/JS bilan yaratilgan custom admin panel
"""

from fastapi import APIRouter, Request, Form, Depends, HTTPException, status, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from typing import Optional, List
import os

from app.models.user import User, UserCreateIn, UserUpdateIn
from app.core.security import SecurityUtils, get_current_user
from app.core.utils import ResponseFormatter
from app.admin.registry import admin_registry


# Templates
templates = Jinja2Templates(directory="app/admin/templates")

# Router
admin_router = APIRouter(prefix="/admin", tags=["Admin Panel"])


async def get_admin_user(request: Request):
    """Admin foydalanuvchini olish."""
    try:
        # Session dan user_id olish
        user_id = request.session.get("user_id")
        if not user_id:
            return None
        
        # User olish
        user = await User.get_or_none(id=user_id, is_active=True)
        return user
    except:
        return None


async def get_current_admin_user(request: Request):
    """Admin user dependency - required admin user"""
    user = await get_admin_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            detail="Unauthorized",
            headers={"Location": "/admin/login"}
        )
    return user


# Admin login page
@admin_router.get("/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """Admin login sahifasi."""
    return templates.TemplateResponse("login.html", {"request": request})


@admin_router.post("/login")
async def admin_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """Admin login with Two Factor Authentication support."""
    # Foydalanuvchini topish
    user = await User.filter(username=username).first()
    if not user:
        return templates.TemplateResponse(
            "login.html", 
            {"request": request, "error": "Username yoki parol noto'g'ri"}
        )
    
    # Superuser va faollikni tekshirish
    if not user.is_superuser or not user.is_active:
        return templates.TemplateResponse(
            "login.html", 
            {"request": request, "error": "Admin huquqi yo'q"}
        )
    
    # Parolni tekshirish
    if not SecurityUtils.verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "login.html", 
            {"request": request, "error": "Username yoki parol noto'g'ri"}
        )
    
    # IP address va user agent olish
    ip_address = request.client.host
    user_agent = request.headers.get("user-agent", "Unknown")
    
    try:
        # 2FA modellarini import qilish
        from app.models.admin_security import AdminSecurity, DeviceBlock
        from app.services.telegram_bot import get_telegram_service
        
        # Device block tekshirish (vaqt tekshiruvisiz)
        device_blocked = await DeviceBlock.filter(
            user=user.id,
            ip_address=ip_address,
            is_active=True
        ).exists()
        
        if device_blocked:
            return templates.TemplateResponse(
                "login.html", 
                {"request": request, "error": "Bu qurilma bloklangan"}
            )
        
        # 2FA tekshirish - qayta yoqamiz
        admin_security = await AdminSecurity.get_or_none(user=user)
        
        if admin_security and admin_security.telegram_enabled and admin_security.require_confirmation:
            # 2FA talab qilinadi
            telegram_service = await get_telegram_service(user.id)
            
            if telegram_service:
                # Telegram confirmation yuborish
                verification_code = await telegram_service.send_login_confirmation(
                    user_id=user.id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    location="Unknown"
                )
                
                if verification_code:
                    # Pure Telegram 2FA - faqat Telegram orqali tasdiqlash
                    # Foydalanuvchi Telegram'da confirm/deny qiladi
                    return templates.TemplateResponse(
                        "login_waiting.html", 
                        {
                            "request": request, 
                            "verification_code": verification_code,
                            "message": "Telegram'da login tasdiqlash xabari yuborildi. Telegram bot'dan javob bering."
                        }
                    )
                else:
                    return templates.TemplateResponse(
                        "login.html", 
                        {"request": request, "error": "2FA xabar yuborishda xatolik."}
                    )
            else:
                return templates.TemplateResponse(
                    "login.html", 
                    {"request": request, "error": "2FA sozlanmagan."}
                )
        
        # 2FA yo'q yoki xatolik bo'lgan holda oddiy login
        request.session["user_id"] = user.id
        user.last_login = datetime.now()
        await user.save()
        return RedirectResponse(url="/admin/dashboard", status_code=302)
        
    except Exception as e:
        print(f"Login xatolik: {e}")
        return templates.TemplateResponse(
            "login.html", 
            {"request": request, "error": f"Xatolik: {str(e)}"}
        )
@admin_router.post("/verify-2fa")
async def verify_2fa(
    request: Request,
    verification_code: str = Form(...),
    username: str = Form(...)
):
    """Two Factor Authentication verification check."""
    try:
        from app.models.admin_security import PendingVerification, LoginAttempt
        
        # Verification topish
        verification = await PendingVerification.get_or_none(
            verification_code=verification_code,
            is_used=False
        ).select_related('user')
        
        if not verification:
            return templates.TemplateResponse(
                "login_2fa.html", 
                {
                    "request": request, 
                    "verification_code": verification_code,
                    "username": username,
                    "error": "Verification kod topilmadi"
                }
            )
        
        # Vaqt tekshiruvisiz davom etamiz
        # Login attempt ni tekshirish
        attempt = await LoginAttempt.get(id=verification.attempt_id)
        
        if attempt.status == "confirmed":
            # Tasdiqlangan
            await verification.update_from_dict({"is_used": True})
            
            # Session yaratish
            request.session["user_id"] = verification.user.id
            
            # Last login yangilash
            user = await User.get(id=verification.user.id)
            user.last_login = datetime.now()
            await user.save()
            
            return RedirectResponse(url="/admin/dashboard", status_code=302)
            
        elif attempt.status == "denied":
            # Rad etilgan
            await verification.update_from_dict({"is_used": True})
            return templates.TemplateResponse(
                "login.html", 
                {"request": request, "error": "Login rad etildi va qurilma bloklandi"}
            )
        else:
            # Hali kutilmoqda
            return templates.TemplateResponse(
                "login_2fa.html", 
                {
                    "request": request, 
                    "verification_code": verification_code,
                    "username": username,
                    "message": "Hali Telegram dan javob kutilmoqda..."
                }
            )
        
    except Exception as e:
        return templates.TemplateResponse(
            "login_2fa.html", 
            {
                "request": request, 
                "verification_code": verification_code,
                "username": username,
                "error": f"Xatolik: {str(e)}"
            }
        )


@admin_router.get("/logout")
async def admin_logout(request: Request):
    """Admin logout."""
    request.session.clear()
    return RedirectResponse(url="/admin/login", status_code=302)


# Admin dashboard
@admin_router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, admin_user = Depends(get_current_admin_user)):
    """Admin dashboard."""
    try:
        # Statistikalar
        total_users = await User.all().count()
        active_users = await User.filter(is_active=True).count()
        superusers = await User.filter(is_superuser=True).count()
        
        # Yangi foydalanuvchilar (oxirgi 7 kun)
        from datetime import timedelta
        week_ago = datetime.now() - timedelta(days=7)
        new_users_week = await User.filter(created_at__gte=week_ago).count()
        
        stats = {
            "total_users": total_users,
            "active_users": active_users,
            "superusers": superusers,
            "new_users_week": new_users_week
        }
        
        # Ro'yxatdan o'tgan model'lar
        registered_models = admin_registry.get_registered_models()
        
        return templates.TemplateResponse(
            "dashboard.html", 
            {
                "request": request, 
                "admin_user": admin_user,
                "stats": stats,
                "registered_models": registered_models
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Users list
@admin_router.get("/users", response_class=HTMLResponse)
async def admin_users_list(
    request: Request, 
    admin_user = Depends(get_current_admin_user),
    page: int = 1,
    per_page: int = 20,
    search: Optional[str] = None
):
    """Foydalanuvchilar ro'yxati."""
    try:
        offset = (page - 1) * per_page
        
        # Search
        if search:
            users = await User.filter(
                username__icontains=search
            ).offset(offset).limit(per_page)
            total = await User.filter(username__icontains=search).count()
        else:
            users = await User.all().offset(offset).limit(per_page)
            total = await User.all().count()
        
        # Pagination
        total_pages = (total + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < total_pages
        
        pagination = {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_prev": has_prev,
            "has_next": has_next,
            "prev_page": page - 1 if has_prev else None,
            "next_page": page + 1 if has_next else None
        }
        
        return templates.TemplateResponse(
            "users_list.html", 
            {
                "request": request,
                "admin_user": admin_user,
                "users": users,
                "pagination": pagination,
                "search": search or ""
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# User qo'shish sahifasi
@admin_router.get("/users/add", response_class=HTMLResponse)
async def admin_add_user_page(request: Request, admin_user = Depends(get_current_admin_user)):
    """User qo'shish sahifasi."""
    return templates.TemplateResponse(
        "add_user.html", 
        {
            "request": request,
            "admin_user": admin_user,
        }
    )


# User qo'shish (POST)
@admin_router.post("/users/add", response_class=HTMLResponse)
async def admin_add_user_submit(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    is_active: bool = Form(False),
    is_superuser: bool = Form(False),
    admin_user = Depends(get_current_admin_user)
):
    """User qo'shish (form submit)."""
    errors = []
    
    try:
        # Username mavjudligini tekshirish
        existing_user = await User.filter(username=username).first()
        if existing_user:
            errors.append("Bu username allaqachon mavjud")
        
        # Email mavjudligini tekshirish
        existing_email = await User.filter(email=email).first()
        if existing_email:
            errors.append("Bu email allaqachon mavjud")
        
        # Parol uzunligini tekshirish
        if len(password) < 6:
            errors.append("Parol kamida 6 ta belgidan iborat bo'lishi kerak")
        
        if errors:
            return templates.TemplateResponse(
                "add_user.html", 
                {
                    "request": request,
                    "admin_user": admin_user,
                    "errors": errors,
                    "form_data": {
                        "username": username,
                        "email": email,
                        "first_name": first_name,
                        "last_name": last_name,
                        "is_active": is_active,
                        "is_superuser": is_superuser
                    }
                }
            )
        
        # Yangi foydalanuvchi yaratish
        user = await User.create(
            username=username,
            email=email,
            password_hash=SecurityUtils.hash_password(password),
            first_name=first_name or None,
            last_name=last_name or None,
            is_active=is_active,
            is_superuser=is_superuser
        )
        
        # Muvaffaqiyat xabari bilan users list ga qaytarish
        return RedirectResponse(
            url="/admin/users?success=user_created", 
            status_code=302
        )
        
    except Exception as e:
        errors.append(f"Xatolik: {str(e)}")
        return templates.TemplateResponse(
            "add_user.html", 
            {
                "request": request,
                "admin_user": admin_user,
                "errors": errors,
                "form_data": {
                    "username": username,
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                    "is_active": is_active,
                    "is_superuser": is_superuser
                }
            }
        )


# User detail/edit
@admin_router.get("/users/{user_id}", response_class=HTMLResponse)
async def admin_user_detail(
    request: Request, 
    user_id: int,
    admin_user = Depends(get_current_admin_user)
):
    """Foydalanuvchi batafsil."""
    try:
        user = await User.get_or_none(id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
        
        return templates.TemplateResponse(
            "user_detail.html", 
            {
                "request": request,
                "admin_user": admin_user,
                "user": user
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# API endpoints for AJAX
@admin_router.delete("/api/users/{user_id}")
async def admin_delete_user(
    user_id: int,
    admin_user = Depends(get_current_admin_user)
):
    """Foydalanuvchini o'chirish."""
    try:
        user = await User.get_or_none(id=user_id)
        if not user:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Foydalanuvchi topilmadi"}
            )
        
        # O'zini o'chirishga ruxsat bermaslik
        if user.id == admin_user.id:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "O'zingizni o'chira olmaysiz"}
            )
        
        await user.delete()
        
        return JSONResponse(
            content={"success": True, "message": "Foydalanuvchi o'chirildi"}
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )


@admin_router.patch("/api/users/{user_id}/toggle-active")
async def admin_toggle_user_active(
    user_id: int,
    admin_user = Depends(get_current_admin_user)
):
    """Foydalanuvchi faolligini o'zgartirish."""
    try:
        user = await User.get_or_none(id=user_id)
        if not user:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Foydalanuvchi topilmadi"}
            )
        
        # O'zini deaktiv qilishga ruxsat bermaslik
        if user.id == admin_user.id and user.is_active:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "O'zingizni deaktiv qila olmaysiz"}
            )
        
        user.is_active = not user.is_active
        await user.save()
        
        status_text = "faollashtirildi" if user.is_active else "deaktivlashtirildi"
        
        return JSONResponse(
            content={
                "success": True, 
                "message": f"Foydalanuvchi {status_text}",
                "is_active": user.is_active
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )


@admin_router.post("/api/users")
async def admin_create_user(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    is_active: bool = Form(True),
    is_superuser: bool = Form(False),
    admin_user = Depends(get_current_admin_user)
):
    """Admin orqali yangi foydalanuvchi yaratish."""
    try:
        # Username mavjudligini tekshirish
        existing_user = await User.filter(username=username).first()
        if existing_user:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Bu username allaqachon mavjud"}
            )
        
        # Email mavjudligini tekshirish
        existing_email = await User.filter(email=email).first()
        if existing_email:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Bu email allaqachon mavjud"}
            )
        
        # Parol uzunligini tekshirish
        if len(password) < 6:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Parol kamida 6 ta belgidan iborat bo'lishi kerak"}
            )
        
        # Yangi foydalanuvchi yaratish
        user = await User.create(
            username=username,
            email=email,
            password_hash=SecurityUtils.hash_password(password),
            first_name=first_name or None,
            last_name=last_name or None,
            is_active=is_active,
            is_superuser=is_superuser
        )
        
        return JSONResponse(
            content={
                "success": True, 
                "message": f"Foydalanuvchi '{username}' muvaffaqiyatli yaratildi",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "is_active": user.is_active,
                    "is_superuser": user.is_superuser
                }
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Xatolik: {str(e)}"}
        )


# Model CRUD endpointlari
@admin_router.get("/{model_name}", response_class=HTMLResponse)
async def model_list(
    request: Request,
    model_name: str,
    page: int = Query(1, ge=1),
    search: str = Query("", description="Qidiruv"),
    current_user=Depends(get_current_admin_user)
):
    """Model ro'yxati sahifasi"""
    try:
        # Registry dan model konfiguratsiyasini olish
        config = admin_registry.get_config(model_name)
        if not config:
            raise HTTPException(status_code=404, detail="Model topilmadi")
        
        # Model class
        model_class = config.model
        
        # Qidiruv va pagination
        per_page = config.list_per_page
        offset = (page - 1) * per_page
        
        # Base query
        query = model_class.all()
        
        # Search filter
        if search and config.search_fields:
            search_conditions = []
            for field in config.search_fields:
                search_conditions.append({f"{field}__icontains": search})
            
            # Apply search filters
            for i, condition in enumerate(search_conditions):
                if i == 0:
                    query = query.filter(**condition)
                else:
                    query = query.union(model_class.filter(**condition))
        
        # Get total count
        total = await query.count()
        
        # Get objects with pagination
        objects = await query.offset(offset).limit(per_page)
        
        # Convert objects to dicts with proper field access
        processed_objects = []
        for obj in objects:
            obj_dict = {}
            for field in config.list_display:
                try:
                    if hasattr(obj, field):
                        value = getattr(obj, field)
                        # Handle datetime fields
                        if hasattr(value, 'strftime'):
                            obj_dict[field] = value
                        else:
                            obj_dict[field] = value
                    else:
                        obj_dict[field] = None
                except:
                    obj_dict[field] = None
            
            # Add special properties if they exist
            if hasattr(obj, 'full_name'):
                obj_dict['full_name'] = obj.full_name
            if hasattr(obj, 'age'):
                obj_dict['age'] = obj.age
                
            # Store original object for access
            obj_dict['_original'] = obj
            processed_objects.append(obj_dict)
        
        # Calculate pagination
        total_pages = (total + per_page - 1) // per_page
        
        return templates.TemplateResponse(
            "model_list.html",
            {
                "request": request,
                "config": config,
                "model_name": model_name,
                "objects": processed_objects,
                "page": page,
                "total_pages": total_pages,
                "total": total,
                "search": search,
                "per_page": per_page
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": str(e)}
        )


@admin_router.get("/{model_name}/add", response_class=HTMLResponse)
async def model_add_form(
    request: Request,
    model_name: str,
    current_user=Depends(get_current_admin_user)
):
    """Model qo'shish sahifasi"""
    try:
        config = admin_registry.get_config(model_name)
        if not config or not config.can_add:
            raise HTTPException(status_code=404, detail="Model yoki ruxsat topilmadi")
        
        return templates.TemplateResponse(
            "model_add.html",
            {
                "request": request,
                "config": config,
                "model_name": model_name
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": str(e)}
        )


@admin_router.post("/{model_name}/add")
async def model_add_submit(
    request: Request,
    model_name: str,
    current_user=Depends(get_current_admin_user)
):
    """Model qo'shish submit"""
    try:
        config = admin_registry.get_config(model_name)
        if not config or not config.can_add:
            raise HTTPException(status_code=404, detail="Model yoki ruxsat topilmadi")
        
        # Form datalarini olish
        form_data = await request.form()
        data = dict(form_data)
        
        # Model yaratish
        model_class = config.model
        obj = await model_class.create(**data)
        
        return RedirectResponse(
            url=f"/admin/{model_name}?success=created",
            status_code=302
        )
    except Exception as e:
        return RedirectResponse(
            url=f"/admin/{model_name}/add?error={str(e)}",
            status_code=302
        )


@admin_router.get("/{model_name}/{object_id}", response_class=HTMLResponse)
async def model_detail(
    request: Request,
    model_name: str,
    object_id: int,
    current_user=Depends(get_current_admin_user)
):
    """Model detail sahifasi"""
    try:
        config = admin_registry.get_config(model_name)
        if not config:
            raise HTTPException(status_code=404, detail="Model topilmadi")
        
        # Object olish
        model_class = config.model
        obj = await model_class.get(id=object_id)
        
        return templates.TemplateResponse(
            "model_detail.html",
            {
                "request": request,
                "config": config,
                "model_name": model_name,
                "object": obj,
                "object_id": object_id
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": str(e)}
        )


@admin_router.get("/{model_name}/{object_id}/edit", response_class=HTMLResponse)
async def model_edit_form(
    request: Request,
    model_name: str,
    object_id: int,
    current_user=Depends(get_current_admin_user)
):
    """Model tahrirlash sahifasi"""
    try:
        config = admin_registry.get_config(model_name)
        if not config or not config.can_edit:
            raise HTTPException(status_code=404, detail="Model yoki ruxsat topilmadi")
        
        # Object olish
        model_class = config.model
        obj = await model_class.get(id=object_id)
        
        return templates.TemplateResponse(
            "model_edit.html",
            {
                "request": request,
                "config": config,
                "model_name": model_name,
                "object": obj,
                "object_id": object_id
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": str(e)}
        )


@admin_router.post("/{model_name}/{object_id}/edit")
async def model_edit_submit(
    request: Request,
    model_name: str,
    object_id: int,
    current_user=Depends(get_current_admin_user)
):
    """Model tahrirlash submit"""
    try:
        config = admin_registry.get_config(model_name)
        if not config or not config.can_edit:
            raise HTTPException(status_code=404, detail="Model yoki ruxsat topilmadi")
        
        # Object olish
        model_class = config.model
        obj = await model_class.get(id=object_id)
        
        # Form datalarini olish
        form_data = await request.form()
        data = dict(form_data)
        
        # Object yangilash
        for field, value in data.items():
            if hasattr(obj, field):
                setattr(obj, field, value)
        
        await obj.save()
        
        return RedirectResponse(
            url=f"/admin/{model_name}?success=updated",
            status_code=302
        )
    except Exception as e:
        return RedirectResponse(
            url=f"/admin/{model_name}/{object_id}/edit?error={str(e)}",
            status_code=302
        )


@admin_router.delete("/{model_name}/{object_id}")
async def model_delete(
    model_name: str,
    object_id: int,
    current_user=Depends(get_current_admin_user)
):
    """Model o'chirish API"""
    try:
        config = admin_registry.get_config(model_name)
        if not config or not config.can_delete:
            raise HTTPException(status_code=404, detail="Model yoki ruxsat topilmadi")
        
        # Object o'chirish
        model_class = config.model
        obj = await model_class.get(id=object_id)
        await obj.delete()
        
        return {"success": True, "message": "Muvaffaqiyatli o'chirildi"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Xatolik: {str(e)}"}
        )


def setup_admin_panel(app):
    """Admin panel ni asosiy ilovaga ulash."""
    # Admin konfiguratsiyalarini import qilish
    from app.admin import admin
    
    # Auto-discovery: barcha model'larni avtomatik ro'yxatdan o'tkazish
    from app.admin.autodiscovery import auto_register_models
    auto_register_models()
    
    # Static files uchun papka yaratish
    static_dir = "app/admin/static"
    templates_dir = "app/admin/templates"
    
    os.makedirs(static_dir, exist_ok=True)
    os.makedirs(templates_dir, exist_ok=True)
    
    # Static files mount
    app.mount("/admin/static", StaticFiles(directory=static_dir), name="admin_static")
    
    # Router ulash
    app.include_router(admin_router)
    
    # Root admin redirect
    @app.get("/admin")
    async def admin_root():
        return RedirectResponse(url="/admin/dashboard")
    
    return admin_router
