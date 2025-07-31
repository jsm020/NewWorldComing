"""
Page model for static pages management.
"""

from tortoise import fields
from tortoise.models import Model
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Page(Model):
    """
    Page model for static pages like About, Contact, etc.
    """
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=200)
    slug = fields.CharField(max_length=250, unique=True)
    content = fields.TextField()
    excerpt = fields.CharField(max_length=500, null=True)
    featured_image = fields.CharField(max_length=500, null=True)
    is_published = fields.BooleanField(default=True)
    is_homepage = fields.BooleanField(default=False)
    template = fields.CharField(max_length=100, default='default')
    author = fields.ForeignKeyField('models.User', related_name='pages')
    meta_title = fields.CharField(max_length=200, null=True)
    meta_description = fields.CharField(max_length=300, null=True)
    custom_css = fields.TextField(null=True)
    custom_js = fields.TextField(null=True)
    sort_order = fields.IntField(default=0)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "pages"
        ordering = ["sort_order", "title"]

    def __str__(self):
        return self.title


# Pydantic schemas
class PageCreateIn(BaseModel):
    title: str
    slug: Optional[str] = None
    content: str
    excerpt: Optional[str] = None
    featured_image: Optional[str] = None
    is_published: bool = True
    is_homepage: bool = False
    template: str = 'default'
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    custom_css: Optional[str] = None
    custom_js: Optional[str] = None
    sort_order: int = 0


class PageUpdateIn(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    featured_image: Optional[str] = None
    is_published: Optional[bool] = None
    is_homepage: Optional[bool] = None
    template: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    custom_css: Optional[str] = None
    custom_js: Optional[str] = None
    sort_order: Optional[int] = None


class PageOut(BaseModel):
    id: int
    title: str
    slug: str
    content: str
    excerpt: Optional[str]
    featured_image: Optional[str]
    is_published: bool
    is_homepage: bool
    template: str
    meta_title: Optional[str]
    meta_description: Optional[str]
    custom_css: Optional[str]
    custom_js: Optional[str]
    sort_order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True