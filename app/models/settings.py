"""
Settings model for application configuration.
"""

from tortoise import fields
from tortoise.models import Model
from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime
import json


class Setting(Model):
    """
    Settings model for storing application configuration.
    """
    id = fields.IntField(pk=True)
    key = fields.CharField(max_length=100, unique=True)
    value = fields.TextField()
    description = fields.CharField(max_length=500, null=True)
    category = fields.CharField(max_length=50, default='general')
    is_public = fields.BooleanField(default=False)  # Whether setting can be accessed publicly
    data_type = fields.CharField(max_length=20, default='string')  # string, number, boolean, json
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "settings"
        ordering = ["category", "key"]

    def __str__(self):
        return f"{self.key}: {self.value[:50]}"

    def get_value(self):
        """Get typed value based on data_type."""
        if self.data_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes', 'on')
        elif self.data_type == 'number':
            try:
                return float(self.value) if '.' in self.value else int(self.value)
            except ValueError:
                return 0
        elif self.data_type == 'json':
            try:
                return json.loads(self.value)
            except json.JSONDecodeError:
                return {}
        else:
            return self.value

    def set_value(self, value: Any):
        """Set value with proper type conversion."""
        if self.data_type == 'json':
            self.value = json.dumps(value)
        else:
            self.value = str(value)


# Pydantic schemas
class SettingCreateIn(BaseModel):
    key: str
    value: str
    description: Optional[str] = None
    category: str = 'general'
    is_public: bool = False
    data_type: str = 'string'


class SettingUpdateIn(BaseModel):
    value: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_public: Optional[bool] = None
    data_type: Optional[str] = None


class SettingOut(BaseModel):
    id: int
    key: str
    value: str
    description: Optional[str]
    category: str
    is_public: bool
    data_type: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Common settings categories and default values
DEFAULT_SETTINGS = {
    'site': {
        'site_name': 'NewWorldComing',
        'site_description': 'A modern web application',
        'site_url': 'http://localhost:8000',
        'admin_email': 'admin@example.com',
        'timezone': 'UTC',
        'language': 'uz',
    },
    'features': {
        'registration_enabled': 'true',
        'comments_enabled': 'true',
        'file_uploads_enabled': 'true',
        'api_rate_limit': '100',
    },
    'appearance': {
        'theme': 'default',
        'logo_url': '',
        'favicon_url': '',
        'custom_css': '',
        'custom_js': '',
    },
    'email': {
        'smtp_host': '',
        'smtp_port': '587',
        'smtp_username': '',
        'smtp_password': '',
        'smtp_use_tls': 'true',
        'from_email': '',
    }
}