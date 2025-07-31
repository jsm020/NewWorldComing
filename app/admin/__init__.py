"""
FastAPI Admin panel - Django admin ga o'xshash
Oddiy HTML/CSS/JS bilan yaratilgan custom admin panel
"""

from fastapi import APIRouter, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from typing import Optional, List
import os

from app.models.user import User, UserCreateIn, UserUpdateIn
from app.core.security import SecurityUtils, get_current_user
from app.core.utils import ResponseFormatter


# Templates
templates = Jinja2Templates(directory="app/admin/templates")

# Router
admin_router = APIRouter(prefix="/admin", tags=["Admin Panel"])


async def get_admin_user(request: Request):
    """Admin foydalanuvchini olish."""
    try:
        # Session dan user_id olish
        user_id = request.session.get("admin_user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Login qiling")
        
        user = await User.get_or_none(id=user_id)
        if not user or not user.is_superuser or not user.is_active:
            raise HTTPException(status_code=403, detail="Admin huquqi yo'q")
        
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Login qiling")


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
    """Admin login."""
    try:
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
        
        # Session yaratish
        request.session["admin_user_id"] = user.id
        
        # Last login yangilash
        user.last_login = datetime.utcnow()
        await user.save()
        
        return RedirectResponse(url="/admin/dashboard", status_code=302)
        
    except Exception as e:
        return templates.TemplateResponse(
            "login.html", 
            {"request": request, "error": f"Xatolik: {str(e)}"}
        )


@admin_router.get("/logout")
async def admin_logout(request: Request):
    """Admin logout."""
    request.session.clear()
    return RedirectResponse(url="/admin/login", status_code=302)


# Admin dashboard
@admin_router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, admin_user = Depends(get_admin_user)):
    """Admin dashboard."""
    try:
        # Statistikalar
        total_users = await User.all().count()
        active_users = await User.filter(is_active=True).count()
        superusers = await User.filter(is_superuser=True).count()
        
        # Yangi foydalanuvchilar (oxirgi 7 kun)
        from datetime import timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        new_users_week = await User.filter(created_at__gte=week_ago).count()
        
        stats = {
            "total_users": total_users,
            "active_users": active_users,
            "superusers": superusers,
            "new_users_week": new_users_week
        }
        
        return templates.TemplateResponse(
            "dashboard.html", 
            {
                "request": request, 
                "admin_user": admin_user,
                "stats": stats
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Users list
@admin_router.get("/users", response_class=HTMLResponse)
async def admin_users_list(
    request: Request, 
    admin_user = Depends(get_admin_user),
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


# User detail/edit
@admin_router.get("/users/{user_id}", response_class=HTMLResponse)
async def admin_user_detail(
    request: Request, 
    user_id: int,
    admin_user = Depends(get_admin_user)
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
    admin_user = Depends(get_admin_user)
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
    admin_user = Depends(get_admin_user)
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


def setup_admin_panel(app):
    """Admin panel ni asosiy ilovaga ulash."""
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
