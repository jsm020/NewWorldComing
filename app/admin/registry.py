"""
Django-style Admin Registry
Model'larni admin panelga ro'yxatdan o'tkazish tizimi
"""

from typing import Dict, Type, Optional, List, Any, Callable
from tortoise.models import Model
from tortoise import Tortoise
from dataclasses import dataclass, field
from datetime import datetime
import inspect


@dataclass
class AdminFieldConfig:
    """Admin maydon konfiguratsiyasi."""
    name: str
    label: str
    field_type: str
    required: bool = False
    readonly: bool = False
    choices: Optional[List[tuple]] = None
    help_text: Optional[str] = None
    widget: Optional[str] = None


@dataclass
class AdminConfig:
    """Model uchun admin konfiguratsiyasi."""
    model: Type[Model]
    name: str
    name_plural: str
    icon: str = "fas fa-table"
    
    # Display options  
    list_display: List[str] = field(default_factory=lambda: ['id'])
    list_filter: List[str] = field(default_factory=list)
    search_fields: List[str] = field(default_factory=list)
    ordering: List[str] = field(default_factory=list)
    
    # Form options
    fields: List[str] = field(default_factory=list)
    readonly_fields: List[str] = field(default_factory=list)
    
    # Permissions
    can_add: bool = True
    can_edit: bool = True
    can_delete: bool = True
    can_view: bool = True
    
    # Pagination
    list_per_page: int = 20
    
    # Pagination
    list_per_page: int = 20
    
    # Custom methods
    custom_actions: Dict[str, Callable] = None
    
    def __post_init__(self):
        if self.list_display is None:
            self.list_display = ['id']
        if self.search_fields is None:
            self.search_fields = []
        if self.list_filter is None:
            self.list_filter = []
        if self.ordering is None:
            self.ordering = ['-id']
        if self.custom_actions is None:
            self.custom_actions = {}


class AdminRegistry:
    """Admin panel model registry."""
    
    def __init__(self):
        self._registry: Dict[str, AdminConfig] = {}
        self._auto_discovered: bool = False
    
    def register(self, model: Type[Model], config: AdminConfig = None):
        """Model'ni admin panelga ro'yxatdan o'tkazish."""
        if config is None:
            config = self._create_default_config(model)
        
        model_name = model.__name__.lower()
        config.model = model
        self._registry[model_name] = config
        
        print(f"✅ {model.__name__} admin panelga ro'yxatdan o'tdi")
    
    def unregister(self, model: Type[Model]):
        """Model'ni admin paneldan olib tashlash."""
        model_name = model.__name__.lower()
        if model_name in self._registry:
            del self._registry[model_name]
            print(f"❌ {model.__name__} admin paneldan olib tashlandi")
    
    def get_registered_models(self) -> Dict[str, AdminConfig]:
        """Ro'yxatdan o'tgan model'lar."""
        return self._registry.copy()
    
    def get_model_config(self, model_name: str) -> Optional[AdminConfig]:
        """Model konfiguratsiyasini olish."""
        return self._registry.get(model_name.lower())
    
    def get_config(self, model_name: str) -> Optional[AdminConfig]:
        """Model konfiguratsiyasini olish (alias for get_model_config)."""
        return self.get_model_config(model_name)
    
    def is_registered(self, model: Type[Model]) -> bool:
        """Model ro'yxatdan o'tganmi?"""
        return model.__name__.lower() in self._registry
    
    def _create_default_config(self, model: Type[Model]) -> AdminConfig:
        """Model uchun standart konfiguratsiya yaratish."""
        model_name = model.__name__
        
        # Model fields ni olish
        fields = []
        search_fields = []
        list_display = ['id']
        
        # Tortoise model'dan field'larni olish
        if hasattr(model, '_meta'):
            for field_name, field in model._meta.fields_map.items():
                fields.append(field_name)
                
                # String field'larni search uchun qo'shish
                if hasattr(field, 'max_length') or field_name in ['username', 'email', 'name', 'title']:
                    search_fields.append(field_name)
                    if len(list_display) < 5:  # Faqat 5 ta field
                        list_display.append(field_name)
        
        return AdminConfig(
            model=model,
            name=model_name,
            name_plural=f"{model_name}lar",
            list_display=list_display,
            search_fields=search_fields,
            fields=fields
        )
    
    async def auto_discover(self):
        """Barcha model'larni avtomatik topish va ro'yxatdan o'tkazish."""
        if self._auto_discovered:
            return
        
        print("🔍 Model'larni avtomatik qidirish...")
        
        # Tortoise dan barcha model'larni olish
        if Tortoise.apps:
            for app_name, app_models in Tortoise.apps.items():
                for model_name, model_class in app_models.items():
                    if not self.is_registered(model_class):
                        # Faqat asosiy model'larni ro'yxatdan o'tkazish
                        if not model_name.startswith('_'):
                            self.register(model_class)
        
        self._auto_discovered = True
        print(f"✅ {len(self._registry)} ta model avtomatik ro'yxatdan o'tdi")


# Global registry instance
admin_registry = AdminRegistry()


# Decorator for easy registration
def register_admin(config: AdminConfig = None):
    """Model'ni admin panelga ro'yxatdan o'tkazish uchun decorator."""
    def decorator(model_class):
        admin_registry.register(model_class, config)
        return model_class
    return decorator


# Django-style registration functions
def register(model: Type[Model], config: AdminConfig = None):
    """Django admin.site.register() ga o'xshash."""
    admin_registry.register(model, config)


def unregister(model: Type[Model]):
    """Django admin.site.unregister() ga o'xshash."""
    admin_registry.unregister(model)


# Helper functions
def get_model_fields(model: Type[Model]) -> List[AdminFieldConfig]:
    """Model field'larini AdminFieldConfig formatida olish."""
    fields = []
    
    if hasattr(model, '_meta'):
        for field_name, field in model._meta.fields_map.items():
            field_config = AdminFieldConfig(
                name=field_name,
                label=field_name.replace('_', ' ').title(),
                field_type=field.__class__.__name__,
                required=not getattr(field, 'null', True)
            )
            fields.append(field_config)
    
    return fields


def get_model_verbose_name(model: Type[Model]) -> str:
    """Model'ning o'qish uchun qulay nomini olish."""
    if hasattr(model, '_meta') and hasattr(model._meta, 'verbose_name'):
        return model._meta.verbose_name
    return model.__name__


def get_model_verbose_name_plural(model: Type[Model]) -> str:
    """Model'ning ko'plik shaklini olish."""
    if hasattr(model, '_meta') and hasattr(model._meta, 'verbose_name_plural'):
        return model._meta.verbose_name_plural
    return f"{get_model_verbose_name(model)}lar"
