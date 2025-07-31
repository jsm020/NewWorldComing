"""
Article model for content management system.
"""

from tortoise import fields
from tortoise.models import Model
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Article(Model):
    """
    Article model for blog posts and news articles.
    """
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=200)
    slug = fields.CharField(max_length=250, unique=True)
    content = fields.TextField()
    excerpt = fields.CharField(max_length=500, null=True)
    featured_image = fields.CharField(max_length=500, null=True)
    is_published = fields.BooleanField(default=False)
    is_featured = fields.BooleanField(default=False)
    author = fields.ForeignKeyField('models.User', related_name='articles')
    category = fields.CharField(max_length=100, null=True)
    tags = fields.CharField(max_length=500, null=True)  # Comma-separated tags
    meta_title = fields.CharField(max_length=200, null=True)
    meta_description = fields.CharField(max_length=300, null=True)
    view_count = fields.IntField(default=0)
    published_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "articles"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


# Pydantic schemas
class ArticleCreateIn(BaseModel):
    title: str
    slug: Optional[str] = None
    content: str
    excerpt: Optional[str] = None
    featured_image: Optional[str] = None
    is_published: bool = False
    is_featured: bool = False
    category: Optional[str] = None
    tags: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None


class ArticleUpdateIn(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    featured_image: Optional[str] = None
    is_published: Optional[bool] = None
    is_featured: Optional[bool] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None


class ArticleOut(BaseModel):
    id: int
    title: str
    slug: str
    content: str
    excerpt: Optional[str]
    featured_image: Optional[str]
    is_published: bool
    is_featured: bool
    category: Optional[str]
    tags: Optional[str]
    meta_title: Optional[str]
    meta_description: Optional[str]
    view_count: int
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True