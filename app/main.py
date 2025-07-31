"""
FastAPI asosiy ilova - xavfsizlik, middleware va to'liq konfiguratsiya bilan.
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from tortoise.contrib.fastapi import register_tortoise
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uvicorn
from typing import Optional

from app.core.utils import global_exception_handler, ResponseFormatter
from app.core.security import ALLOWED_ORIGINS, CSP_HEADER, limiter
from app.api import user, auth
from config.tortoise_config import TORTOISE_ORM


# FastAPI ilova yaratish
app = FastAPI(
    title="FastAPI + Tortoise ORM Template",
    description="""
    Bu Django o'rniga ishlatish uchun tayyor FastAPI shablon.
    
    ## Xususiyatlar:
    - **Tortoise ORM** - async ORM
    - **JWT Authentication** - xavfsiz autentifikatsiya
    - **Rate Limiting** - so'rovlarni cheklash
    - **Input Validation** - ma'lumotlarni tekshirish
    - **XSS & SQL Injection himoyasi**
    - **CORS konfiguratsiyasi**
    - **Comprehensive API documentation**
    
    ## Xavfsizlik:
    - Barcha inputlar sanitize qilinadi
    - JWT token autentifikatsiya
    - Rate limiting har bir endpoint uchun
    - SQL injection himoyasi
    - XSS himoyasi
    - CSRF himoyasi
    """,
    version="1.0.0",
    contact={
        "name": "Development Team",
        "email": "developer@example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Rate limiting setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Security Middleware
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Xavfsizlik headerlarini qo'shish."""
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = CSP_HEADER
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    return response


# CORS middleware - faqat ruxsat berilgan domenlarga
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Page-Count"],
)

# Trusted Host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.example.com"]
)

# Global exception handler
app.add_exception_handler(Exception, global_exception_handler)


# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """Tizim salomatligini tekshirish."""
    return ResponseFormatter.success(
        data={
            "status": "healthy",
            "version": "1.0.0",
            "framework": "FastAPI",
            "orm": "Tortoise ORM"
        },
        message="Tizim normal ishlayapti"
    )


# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """Bosh sahifa."""
    return ResponseFormatter.success(
        data={
            "name": "FastAPI + Tortoise ORM Template",
            "version": "1.0.0",
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health"
        },
        message="FastAPI + Tortoise ORM shabloni muvaffaqiyatli ishlayapti!"
    )


# API routerlarini ulash
app.include_router(auth.router, prefix="/api/v1")
app.include_router(user.router, prefix="/api/v1")


# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="FastAPI + Tortoise ORM Template",
        version="1.0.0",
        description="""
        ## Django o'rniga ishlatish uchun to'liq FastAPI shablon
        
        ### Qanday ishlatish:
        
        1. **Ro'yxatdan o'tish**: `POST /api/v1/auth/register`
        2. **Tizimga kirish**: `POST /api/v1/auth/login`
        3. **Token olish**: Response da `access_token` ni saqlang
        4. **API ishlatish**: Header ga `Authorization: Bearer <token>` qo'shing
        
        ### Xavfsizlik:
        - Barcha API'lar rate limited
        - JWT token autentifikatsiya
        - Input validation va sanitization
        - SQL injection va XSS himoyasi
        
        ### Model yaratish:
        ```python
        from tortoise import fields
        from tortoise.models import Model
        
        class YourModel(Model):
            id = fields.IntField(pk=True)
            name = fields.CharField(max_length=100)
            created_at = fields.DatetimeField(auto_now_add=True)
        ```
        
        ### API yaratish:
        ```python
        from fastapi import APIRouter, Depends
        from app.core.security import get_current_user
        
        router = APIRouter(prefix="/your-api", tags=["your-tag"])
        
        @router.get("/")
        async def get_items(current_user = Depends(get_current_user)):
            return {"items": []}
        ```
        """,
        routes=app.routes,
    )
    
    # Security scheme qo'shish
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token bilan autentifikatsiya"
        }
    }
    
    # Global security requirement
    for path in openapi_schema["paths"].values():
        for method in path.values():
            if method.get("tags") and "System" not in method["tags"]:
                method["security"] = [{"BearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# Tortoise ORM ni FastAPI bilan integratsiya
register_tortoise(
    app,
    config=TORTOISE_ORM,
    generate_schemas=True,  # Avtomatik schema yaratish
    add_exception_handlers=True,
)


# Development server
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )