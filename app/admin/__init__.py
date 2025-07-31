"""
Admin panel initialization.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

def setup_admin_panel(app: FastAPI):
    """Setup admin panel routes and templates."""
    
    # Mount static files
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    
    # Setup templates
    templates = Jinja2Templates(directory="app/templates")
    
    # Import and include admin routes
    from app.admin.routes import router as admin_router
    app.include_router(admin_router, prefix="/admin")
    
    return templates