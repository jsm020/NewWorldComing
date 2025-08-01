"""
Device Block Management - Admin panel uchun qo'shimcha funksiya
"""

# Admin __init__.py fayliga qo'shiladigan endpoint'lar

@admin_router.get("/security/blocks", response_class=HTMLResponse)
async def admin_device_blocks(request: Request, admin_user = Depends(get_current_admin_user)):
    """Bloklangan qurilmalar ro'yxati."""
    try:
        from app.models.admin_security import DeviceBlock
        
        blocks = await DeviceBlock.filter(is_active=True).all().select_related('user')
        
        return templates.TemplateResponse(
            "device_blocks.html", 
            {
                "request": request,
                "admin_user": admin_user,
                "blocks": blocks
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.post("/security/blocks/{block_id}/unblock")
async def admin_unblock_device(block_id: int, admin_user = Depends(get_current_admin_user)):
    """Qurilma blokini olib tashlash."""
    try:
        from app.models.admin_security import DeviceBlock
        
        block = await DeviceBlock.get_or_none(id=block_id)
        if not block:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Block topilmadi"}
            )
        
        # Blokni faolsizlashtirish
        block.is_active = False
        await block.save()
        
        return JSONResponse(
            content={"success": True, "message": "Qurilma bloki olib tashlandi"}
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )


@admin_router.delete("/security/blocks/{block_id}")
async def admin_delete_block(block_id: int, admin_user = Depends(get_current_admin_user)):
    """Block yozuvini butunlay o'chirish."""
    try:
        from app.models.admin_security import DeviceBlock
        
        block = await DeviceBlock.get_or_none(id=block_id)
        if not block:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "Block topilmadi"}
            )
        
        await block.delete()
        
        return JSONResponse(
            content={"success": True, "message": "Block yozuvi o'chirildi"}
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )
