"""
Admin panel routes and controllers.
"""

from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from tortoise.models import Q
from typing import Optional
from datetime import datetime, timedelta

from app.admin.auth import require_admin, require_superuser, get_admin_user_from_session
from app.models.user import User, UserCreateIn, UserUpdateIn
from app.models.article import Article, ArticleCreateIn, ArticleUpdateIn
from app.models.page import Page, PageCreateIn, PageUpdateIn
from app.models.settings import Setting, SettingUpdateIn
from app.core.security import hash_password, create_access_token, verify_password
from app.core.utils import ResponseFormatter


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# Dashboard
@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request, admin_user: User = Depends(require_admin)):
    """Admin dashboard with statistics."""
    
    # Get statistics
    total_users = await User.all().count()
    total_articles = await Article.all().count()
    total_pages = await Page.all().count()
    published_articles = await Article.filter(is_published=True).count()
    
    # Recent activity
    recent_users = await User.all().order_by('-created_at').limit(5)
    recent_articles = await Article.all().order_by('-created_at').limit(5).prefetch_related('author')
    
    # Weekly stats (users registered in last 7 days)
    week_ago = datetime.now() - timedelta(days=7)
    weekly_users = await User.filter(created_at__gte=week_ago).count()
    
    stats = {
        'total_users': total_users,
        'total_articles': total_articles,
        'total_pages': total_pages,
        'published_articles': published_articles,
        'weekly_users': weekly_users,
        'recent_users': recent_users,
        'recent_articles': recent_articles,
    }
    
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {"request": request, "admin_user": admin_user, "stats": stats}
    )


# Login/Logout
@router.get("/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """Admin login page."""
    return templates.TemplateResponse("admin/login.html", {"request": request})


@router.post("/login")
async def admin_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    remember_me: bool = Form(False)
):
    """Process admin login."""
    user = await User.get_or_none(username=username)
    
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "admin/login.html",
            {"request": request, "error": "Invalid username or password"}
        )
    
    if not user.is_active:
        return templates.TemplateResponse(
            "admin/login.html",
            {"request": request, "error": "Account is disabled"}
        )
    
    # Create access token
    access_token = create_access_token(data={"user_id": user.id})
    
    # Redirect to dashboard
    response = RedirectResponse(url="/admin/", status_code=status.HTTP_302_FOUND)
    
    # Set cookie
    if remember_me:
        max_age = 7 * 24 * 60 * 60  # 7 days
    else:
        max_age = 24 * 60 * 60  # 1 day
    
    response.set_cookie(
        key="admin_token",
        value=access_token,
        max_age=max_age,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax"
    )
    
    return response


@router.get("/logout")
async def admin_logout():
    """Admin logout."""
    response = RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("admin_token")
    return response


# User Management
@router.get("/users", response_class=HTMLResponse)
async def admin_users_list(
    request: Request,
    page: int = 1,
    per_page: int = 20,
    search: Optional[str] = None,
    admin_user: User = Depends(require_admin)
):
    """List all users."""
    offset = (page - 1) * per_page
    
    query = User.all()
    if search:
        query = query.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    total = await query.count()
    users = await query.offset(offset).limit(per_page).order_by('-created_at')
    
    total_pages = (total + per_page - 1) // per_page
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_page': page - 1 if page > 1 else None,
        'next_page': page + 1 if page < total_pages else None
    }
    
    return templates.TemplateResponse(
        "admin/users/list.html",
        {
            "request": request,
            "admin_user": admin_user,
            "users": users,
            "pagination": pagination,
            "search": search
        }
    )


@router.get("/users/create", response_class=HTMLResponse)
async def admin_user_create_form(request: Request, admin_user: User = Depends(require_admin)):
    """Create user form."""
    return templates.TemplateResponse(
        "admin/users/create.html",
        {"request": request, "admin_user": admin_user}
    )


@router.post("/users/create")
async def admin_user_create(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    first_name: str = Form(""),
    last_name: str = Form(""),
    is_active: bool = Form(True),
    is_superuser: bool = Form(False),
    admin_user: User = Depends(require_admin)
):
    """Create new user."""
    try:
        # Check if user exists
        existing_user = await User.get_or_none(
            Q(username=username) | Q(email=email)
        )
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Username or email already exists"
            )
        
        # Create user
        user_data = {
            "username": username,
            "email": email,
            "password_hash": hash_password(password),
            "first_name": first_name or None,
            "last_name": last_name or None,
            "is_active": is_active,
            "is_superuser": is_superuser
        }
        
        user = await User.create(**user_data)
        
        return RedirectResponse(
            url=f"/admin/users/{user.id}",
            status_code=status.HTTP_302_FOUND
        )
        
    except Exception as e:
        return templates.TemplateResponse(
            "admin/users/create.html",
            {
                "request": request,
                "admin_user": admin_user,
                "error": str(e),
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


@router.get("/users/{user_id}", response_class=HTMLResponse)
async def admin_user_detail(
    request: Request,
    user_id: int,
    admin_user: User = Depends(require_admin)
):
    """User detail view."""
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's articles and pages
    user_articles = await Article.filter(author=user).order_by('-created_at').limit(10)
    user_pages = await Page.filter(author=user).order_by('-created_at').limit(10)
    
    return templates.TemplateResponse(
        "admin/users/detail.html",
        {
            "request": request,
            "admin_user": admin_user,
            "user": user,
            "user_articles": user_articles,
            "user_pages": user_pages
        }
    )


# Articles Management
@router.get("/articles", response_class=HTMLResponse)
async def admin_articles_list(
    request: Request,
    page: int = 1,
    per_page: int = 20,
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
    admin_user: User = Depends(require_admin)
):
    """List all articles."""
    offset = (page - 1) * per_page
    
    query = Article.all().prefetch_related('author')
    
    if search:
        query = query.filter(
            Q(title__icontains=search) |
            Q(content__icontains=search) |
            Q(category__icontains=search)
        )
    
    if status_filter == 'published':
        query = query.filter(is_published=True)
    elif status_filter == 'draft':
        query = query.filter(is_published=False)
    elif status_filter == 'featured':
        query = query.filter(is_featured=True)
    
    total = await query.count()
    articles = await query.offset(offset).limit(per_page).order_by('-created_at')
    
    total_pages = (total + per_page - 1) // per_page
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_page': page - 1 if page > 1 else None,
        'next_page': page + 1 if page < total_pages else None
    }
    
    return templates.TemplateResponse(
        "admin/content/articles.html",
        {
            "request": request,
            "admin_user": admin_user,
            "articles": articles,
            "pagination": pagination,
            "search": search,
            "status_filter": status_filter
        }
    )


# Settings Management
@router.get("/settings", response_class=HTMLResponse)
async def admin_settings(request: Request, admin_user: User = Depends(require_superuser)):
    """Settings management."""
    settings = await Setting.all().order_by('category', 'key')
    
    # Group settings by category
    settings_by_category = {}
    for setting in settings:
        if setting.category not in settings_by_category:
            settings_by_category[setting.category] = []
        settings_by_category[setting.category].append(setting)
    
    return templates.TemplateResponse(
        "admin/settings.html",
        {
            "request": request,
            "admin_user": admin_user,
            "settings_by_category": settings_by_category
        }
    )