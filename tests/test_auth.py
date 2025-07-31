import pytest
from httpx import AsyncClient
from app.main import app

import asyncio

@pytest.mark.asyncio
async def test_root():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/")
        assert resp.status_code == 200
        assert resp.json()["message"].startswith("FastAPI")

@pytest.mark.asyncio
async def test_register_and_login():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Register
        resp = await ac.post("/auth/register", json={"username": "testuser", "email": "test@example.com"})
        assert resp.status_code == 200 or resp.status_code == 400  # 400 if already exists
        # Login
        resp = await ac.post("/auth/login", json={"username": "testuser", "email": "test@example.com"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()
