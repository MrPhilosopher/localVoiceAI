from fastapi import APIRouter, HTTPException, status, Query
from fastapi.responses import FileResponse
import os
from app.db.sqlite_db import get_sqlite_client

router = APIRouter()

@router.get("/script")
async def get_widget_script():
    """Return the chat widget script."""
    script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                              "static", "chat-widget.js")
    if not os.path.exists(script_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Widget script not found"
        )
    return FileResponse(script_path)

@router.get("/config")
async def get_widget_config(api_key: str = Query(...)):
    """Get the widget configuration for a tenant based on their API key."""
    db = get_sqlite_client()
    
    # Find the tenant with this API key
    response = db.table('tenants').select('*').eq('api_key', api_key).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid API key"
        )
    
    tenant = response.data[0]
    
    # Handle chat_widget_config being string or dict
    chat_config = tenant.get("chat_widget_config", {})
    if isinstance(chat_config, str):
        import json
        try:
            chat_config = json.loads(chat_config)
        except:
            chat_config = {}
    
    return {
        "tenant_id": tenant["id"],
        "name": tenant["name"],
        "theme_color": chat_config.get("theme_color", "#4f46e5"),
        "position": chat_config.get("position", "right"),
        "welcome_message": chat_config.get("welcome_message", "Hello! How can I help you today?")
    }