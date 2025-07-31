"""
Admin authentication and authorization.
"""

from fastapi import Depends, HTTPException, status, Request, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.core.security import decode_access_token
from app.models.user import User


security = HTTPBearer(auto_error=False)


async def get_admin_user_from_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """Get admin user from JWT token."""
    if not credentials:
        return None
    
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("user_id")
        if not user_id:
            return None
        
        user = await User.get_or_none(id=user_id)
        if not user or not user.is_active:
            return None
        
        return user
    except Exception:
        return None


async def get_admin_user_from_session(request: Request) -> Optional[User]:
    """Get admin user from session cookie."""
    token = request.cookies.get("admin_token")
    if not token:
        return None
    
    try:
        payload = decode_access_token(token)
        user_id = payload.get("user_id")
        if not user_id:
            return None
        
        user = await User.get_or_none(id=user_id)
        if not user or not user.is_active:
            return None
        
        return user
    except Exception:
        return None


async def require_admin(request: Request) -> User:
    """Require admin authentication for admin panel."""
    # First try session cookie
    user = await get_admin_user_from_session(request)
    
    # If no session, try authorization header
    if not user:
        credentials = await security(request)
        if credentials:
            user = await get_admin_user_from_token(credentials)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required"
        )
    
    # For now, any active user can access admin panel
    # In production, you might want to check for is_superuser
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account disabled"
        )
    
    return user


async def require_superuser(request: Request) -> User:
    """Require superuser access."""
    user = await require_admin(request)
    
    if not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser access required"
        )
    
    return user