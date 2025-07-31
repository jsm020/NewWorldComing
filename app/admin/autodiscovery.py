"""
Admin panel uchun auto-discovery moduli
Django kabi avtomatik model registratsiyasi
"""
import os
import importlib
import inspect
from typing import List, Type
from tortoise.models import Model
from app.admin.registry import admin_registry, AdminConfig


def discover_models() -> List[Type[Model]]:
    """
    app/models papkasidagi barcha Tortoise model'larni avtomatik topish
    """
    models = []
    models_dir = "app/models"
    
    if not os.path.exists(models_dir):
        return models
    
    # Barcha .py fayllarni scan qilish
    for filename in os.listdir(models_dir):
        if filename.endswith('.py') and not filename.startswith('__'):
            module_name = filename[:-3]  # .py ni olib tashlash
            
            try:
                # Modulni import qilish
                module = importlib.import_module(f"app.models.{module_name}")
                
                # Modul ichidan barcha Tortoise model'larni topish
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, Model) and 
                        obj != Model and
                        hasattr(obj, '_meta')):
                        models.append(obj)
                        
            except Exception as e:
                print(f"❌ {module_name} import xatolik: {e}")
    
    return models


def auto_register_models():
    """
    Topilgan barcha model'larni avtomatik admin panelga ro'yxatdan o'tkazish
    """
    models = discover_models()
    registered_count = 0
    
    for model in models:
        if not admin_registry.is_registered(model):
            # Standart konfiguratsiya yaratish
            config = create_smart_config(model)
            admin_registry.register(model, config)
            registered_count += 1
    
    print(f"🔍 Auto-discovery: {registered_count} yangi model topildi va ro'yxatdan o'tkazildi")
    print(f"📊 Jami admin panelda: {len(admin_registry.get_registered_models())} model")


def create_smart_config(model: Type[Model]) -> AdminConfig:
    """
    Model uchun aqlli konfiguratsiya yaratish
    """
    model_name = model.__name__
    
    # Model nomi va ko'plik shaklini aniqlash
    if model_name.endswith('y'):
        name_plural = model_name[:-1] + 'ies'  # Category -> Categories
    elif model_name.endswith('s'):
        name_plural = model_name + 'es'  # Class -> Classes
    else:
        name_plural = model_name + 's'  # Student -> Students
    
    # Icon'ni model nomiga qarab aniqlash
    icon_map = {
        'user': 'fas fa-users',
        'student': 'fas fa-graduation-cap',
        'teacher': 'fas fa-chalkboard-teacher',
        'course': 'fas fa-book',
        'post': 'fas fa-newspaper',
        'category': 'fas fa-tags',
        'product': 'fas fa-box',
        'order': 'fas fa-shopping-cart',
        'payment': 'fas fa-credit-card',
        'setting': 'fas fa-cog',
        'log': 'fas fa-file-alt',
    }
    
    icon = icon_map.get(model_name.lower(), 'fas fa-table')
    
    # Field'larni tahlil qilish
    fields = []
    search_fields = []
    list_display = ['id']
    
    # Model Meta'dan field'larni olish
    if hasattr(model, '_meta') and hasattr(model._meta, 'fields_map'):
        for field_name, field_obj in model._meta.fields_map.items():
            fields.append(field_name)
            
            # Search field'lar
            if any(x in field_name.lower() for x in ['name', 'title', 'email', 'username']):
                search_fields.append(field_name)
            
            # List display
            if field_name in ['name', 'title', 'email', 'username', 'first_name', 'is_active']:
                if field_name not in list_display:
                    list_display.append(field_name)
    
    # Agar search field yo'q bo'lsa, name field'larni qo'shish
    if not search_fields:
        for field in fields:
            if 'name' in field.lower():
                search_fields.append(field)
    
    # Common field'larni list_display'ga qo'shish
    common_fields = ['created_at', 'updated_at', 'is_active']
    for field in common_fields:
        if field in fields and field not in list_display:
            list_display.append(field)
    
    return AdminConfig(
        model=model,
        name=model_name,
        name_plural=name_plural,
        icon=icon,
        list_display=list_display[:6],  # Ko'pi bilan 6 ta field
        search_fields=search_fields[:3],  # Ko'pi bilan 3 ta search field
        fields=fields,
        can_add=True,
        can_edit=True,
        can_delete=True,
        can_view=True
    )


def refresh_admin_models():
    """
    Admin panel model'larni yangilash (development uchun)
    """
    print("🔄 Admin model'lar yangilanmoqda...")
    auto_register_models()
