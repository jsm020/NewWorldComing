"""
Authentication va User API testlari - xavfsizlik va funksionallik testlari.
"""

import pytest
import asyncio
from httpx import AsyncClient
from app.main import app
from config.tortoise_config import TORTOISE_ORM_TEST
from tortoise.contrib.test import init_db, teardown


@pytest.fixture(scope="session")
def event_loop():
    """Event loop fixture for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    """Test uchun ma'lumotlar bazasini sozlash."""
    await init_db(TORTOISE_ORM_TEST, create_db=True)
    yield
    await teardown()


@pytest.mark.asyncio
async def test_health_check():
    """Tizim salomatligini tekshirish."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "status" in data["data"]
        assert data["data"]["status"] == "healthy"


@pytest.mark.asyncio
async def test_root_endpoint():
    """Root endpoint testi."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "FastAPI" in data["message"]


@pytest.mark.asyncio
async def test_user_registration():
    """Foydalanuvchi ro'yxatdan o'tkazish testi."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        user_data = {
            "username": "testuser123",
            "email": "test123@example.com",
            "password": "securepassword123",
            "first_name": "Test",
            "last_name": "User"
        }
        
        response = await ac.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["success"] is True
        assert "user" in data["data"]
        assert "access_token" in data["data"]
        assert data["data"]["user"]["username"] == "testuser123"
        assert data["data"]["user"]["email"] == "test123@example.com"
        # Parol response da bo'lmasligi kerak
        assert "password" not in str(data["data"]["user"])


@pytest.mark.asyncio
async def test_user_registration_duplicate():
    """Takroriy ro'yxatdan o'tishni tekshirish."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        user_data = {
            "username": "duplicate_user",
            "email": "duplicate@example.com",
            "password": "password123"
        }
        
        # Birinchi marta ro'yxatdan o'tish
        response1 = await ac.post("/api/v1/auth/register", json=user_data)
        assert response1.status_code == 201
        
        # Ikkinchi marta ro'yxatdan o'tishga urinish
        response2 = await ac.post("/api/v1/auth/register", json=user_data)
        assert response2.status_code == 400
        
        data = response2.json()
        assert data["success"] is False
        assert "allaqachon" in data["detail"]


@pytest.mark.asyncio
async def test_user_login():
    """Foydalanuvchi tizimga kirishi testi."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Avval ro'yxatdan o'tish
        register_data = {
            "username": "logintest",
            "email": "logintest@example.com",
            "password": "loginpassword123"
        }
        await ac.post("/api/v1/auth/register", json=register_data)
        
        # Tizimga kirish
        login_data = {
            "username": "logintest",
            "password": "loginpassword123"
        }
        
        response = await ac.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert "user" in data["data"]
        assert data["data"]["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_invalid_login():
    """Noto'g'ri login ma'lumotlari testi."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        login_data = {
            "username": "nonexistentuser",
            "password": "wrongpassword"
        }
        
        response = await ac.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401
        
        data = response.json()
        assert data["success"] is False
        assert "noto'g'ri" in data["detail"].lower()


@pytest.mark.asyncio
async def test_protected_endpoint_without_token():
    """Token bo'lmagan holda himoyalangan endpoint ga kirish."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/auth/me")
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_with_token():
    """Token bilan himoyalangan endpoint ga kirish."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Ro'yxatdan o'tish va token olish
        register_data = {
            "username": "tokentest",
            "email": "tokentest@example.com", 
            "password": "tokenpassword123"
        }
        
        register_response = await ac.post("/api/v1/auth/register", json=register_data)
        token = register_response.json()["data"]["access_token"]
        
        # Token bilan protected endpoint ga kirish
        headers = {"Authorization": f"Bearer {token}"}
        response = await ac.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "username" in str(data["data"])


@pytest.mark.asyncio
async def test_input_sanitization():
    """Input sanitization testi (XSS himoyasi)."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        malicious_data = {
            "username": "<script>alert('xss')</script>",
            "email": "test@example.com",
            "password": "password123"
        }
        
        response = await ac.post("/api/v1/auth/register", json=malicious_data)
        # XSS kodi sanitize qilinishi yoki rad etilishi kerak
        assert response.status_code != 201 or "<script>" not in str(response.json())


@pytest.mark.asyncio
async def test_weak_password():
    """Zaif parol testi."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        weak_password_data = {
            "username": "weakpasstest",
            "email": "weak@example.com",
            "password": "123"  # Juda qisqa parol
        }
        
        response = await ac.post("/api/v1/auth/register", json=weak_password_data)
        assert response.status_code == 400
        
        data = response.json()
        assert data["success"] is False
        assert "parol" in data["detail"].lower()


@pytest.mark.asyncio
async def test_pagination():
    """Pagination testi."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Token olish uchun foydalanuvchi yaratish
        register_data = {
            "username": "paginationtest",
            "email": "pagination@example.com",
            "password": "password123"
        }
        
        register_response = await ac.post("/api/v1/auth/register", json=register_data)
        token = register_response.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Pagination parametrlari bilan so'rov
        response = await ac.get("/api/v1/users/?page=1&per_page=5", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "pagination" in data
        assert "data" in data
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["per_page"] == 5


# Rate limiting testini alohida qilish kerak, chunki u haqiqiy server kerak
@pytest.mark.skip(reason="Rate limiting requires running server")
async def test_rate_limiting():
    """Rate limiting testi."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Ko'p marta so'rov yuborish
        for i in range(10):
            response = await ac.post("/api/v1/auth/login", json={
                "username": "test",
                "password": "test"
            })
        
        # Rate limit ga yetganda 429 status code qaytishi kerak
        # Aniq test uchun real server va time delay kerak
