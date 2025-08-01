"""
Datetime utilities - timezone bilan ishlash uchun
"""
from datetime import datetime, timezone, timedelta
from typing import Optional


def utc_now() -> datetime:
    """Timezone-aware UTC datetime"""
    return datetime.now(timezone.utc)


def make_aware(dt: datetime) -> datetime:
    """Datetime ni timezone-aware qilish"""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def make_naive(dt: datetime) -> datetime:
    """Datetime ni timezone-naive qilish"""
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt


def compare_datetime(dt1: datetime, dt2: datetime) -> bool:
    """Ikki datetime ni xavfsiz solishtirish"""
    # Ikkisini ham naive qilib solishtiramiz
    if dt1.tzinfo is not None:
        dt1 = make_naive(dt1)
    if dt2.tzinfo is not None:
        dt2 = make_naive(dt2)
    return dt1 > dt2


def is_expired(expires_at: Optional[datetime]) -> bool:
    """Vaqt tugaganligini tekshirish"""
    if expires_at is None:
        return False
    
    now = datetime.utcnow()  # naive datetime
    
    # expires_at ni ham naive qilamiz
    if expires_at.tzinfo is not None:
        expires_at = make_naive(expires_at)
    
    return now > expires_at


def add_minutes(dt: datetime, minutes: int) -> datetime:
    """Datetime ga daqiqa qo'shish"""
    return dt + timedelta(minutes=minutes)


def add_hours(dt: datetime, hours: int) -> datetime:
    """Datetime ga soat qo'shish"""
    return dt + timedelta(hours=hours)


def add_days(dt: datetime, days: int) -> datetime:
    """Datetime ga kun qo'shish"""
    return dt + timedelta(days=days)
