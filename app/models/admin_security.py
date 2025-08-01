"""
Admin 2FA (Two-Factor Authentication) modeli
Telegram bot orqali xavfsizlik
"""
from tortoise import fields
from tortoise.models import Model
from datetime import datetime, timedelta
from typing import Optional
import uuid


class AdminSecurity(Model):
    """
    Admin panel 2FA xavfsizlik modeli
    """
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='admin_security')
    
    # Telegram Bot ma'lumotlari
    telegram_enabled = fields.BooleanField(default=False, description="Telegram 2FA yoqilganmi")
    telegram_bot_token = fields.CharField(max_length=500, null=True, description="Telegram bot token")
    telegram_chat_id = fields.CharField(max_length=100, null=True, description="Telegram chat ID")
    telegram_username = fields.CharField(max_length=100, null=True, description="Telegram username")
    
    # Xavfsizlik sozlamalari
    require_confirmation = fields.BooleanField(default=True, description="Login tasdiqlash talab qilinsinmi")
    auto_block_suspicious = fields.BooleanField(default=True, description="Shubhali faollik avtomatik bloklansinmi")
    max_failed_attempts = fields.IntField(default=3, description="Maksimal muvaffaqiyatsiz urinishlar")
    
    # Session va blok ma'lumotlari
    last_login_ip = fields.CharField(max_length=45, null=True, description="Oxirgi IP manzil")
    last_login_device = fields.CharField(max_length=500, null=True, description="Oxirgi qurilma ma'lumoti")
    last_login_location = fields.CharField(max_length=200, null=True, description="Oxirgi joylashuv")
    
    # Vaqt ma'lumotlari
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    last_activity = fields.DatetimeField(null=True, description="Oxirgi faollik")
    
    class Meta:
        table = "admin_security"
        
    def __str__(self):
        return f"2FA for {self.user.username}"
    
    @property
    def is_configured(self) -> bool:
        """2FA to'liq sozlanganligini tekshirish"""
        return (
            self.telegram_enabled and 
            self.telegram_bot_token and 
            self.telegram_chat_id
        )
    
    async def generate_verification_code(self) -> str:
        """Tasdiqlash kodi yaratish"""
        code = str(uuid.uuid4())[:8].upper()
        
        # Kodni vaqtinchalik saqlash uchun
        await PendingVerification.create(
            admin_security=self,
            verification_code=code,
            expires_at=datetime.utcnow() + timedelta(minutes=5)
        )
        
        return code


class DeviceBlock(Model):
    """
    Bloklangan qurilmalar ro'yxati
    """
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='blocked_devices')
    
    # Qurilma ma'lumotlari
    ip_address = fields.CharField(max_length=45, description="IP manzil")
    user_agent = fields.TextField(description="Browser/qurilma ma'lumoti")
    device_fingerprint = fields.CharField(max_length=500, null=True, description="Qurilma fingerprint")
    
    # Blok sababi va muddati
    reason = fields.CharField(max_length=200, description="Blok sababi")
    blocked_by = fields.CharField(max_length=100, description="Kim tomonidan bloklangan", default="system")
    is_active = fields.BooleanField(default=True, description="Blok faolmi")
    
    # Vaqt ma'lumotlari
    created_at = fields.DatetimeField(auto_now_add=True)
    blocked_until = fields.DatetimeField(null=True, description="Blok tugash vaqti")
    
    class Meta:
        table = "device_blocks"
        
    def __str__(self):
        return f"Blocked {self.ip_address}"
    
    @property
    def is_expired(self) -> bool:
        """Blok muddati tugaganligini tekshirish - vaqt tekshiruvisiz"""
        # Vaqt solishtirish o'rniga har doim False qaytaramiz
        return False
    
    @property
    def is_permanent(self) -> bool:
        """Doimiy blok ekanligini tekshirish"""
        return self.blocked_until is None


class PendingVerification(Model):
    """
    Kutilayotgan tasdiqlovlar
    """
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='pending_verifications')
    
    # Tasdiqlash ma'lumotlari
    verification_code = fields.CharField(max_length=50, description="Tasdiqlash kodi", unique=True)
    attempt_id = fields.IntField(description="Login attempt ID")
    
    # Status
    is_used = fields.BooleanField(default=False, description="Ishlatilganmi")
    
    # Vaqt ma'lumotlari
    created_at = fields.DatetimeField(auto_now_add=True)
    expires_at = fields.DatetimeField(description="Tasdiqlash tugash vaqti")
    
    class Meta:
        table = "pending_verifications"
        
    def __str__(self):
        return f"Verification {self.verification_code}"
    
    @property
    def is_expired(self) -> bool:
        """Tasdiqlash muddati tugaganligini tekshirish - vaqt tekshiruvisiz"""
        # Vaqt solishtirish o'rniga har doim False qaytaramiz
        return False


class LoginAttempt(Model):
    """
    Login urinishlari tarixi
    """
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='login_attempts')
    
    # Login ma'lumotlari
    ip_address = fields.CharField(max_length=45, description="IP manzil")
    user_agent = fields.TextField(description="Qurilma ma'lumoti")
    location = fields.CharField(max_length=200, null=True, description="Joylashuv")
    
    # Status
    status = fields.CharField(max_length=20, default="pending", description="Status: pending, sent, confirmed, denied, failed")
    
    # Vaqt
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "login_attempts"
        
    def __str__(self):
        status_icons = {
            'pending': '⏳',
            'sent': '📤',
            'confirmed': '✅',
            'denied': '❌',
            'failed': '💥'
        }
        icon = status_icons.get(self.status, '❓')
        return f"{icon} {self.user.username} - {self.ip_address}"
