from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime
import secrets
from app.db.sqlite_db import get_sqlite_client
from app.api.endpoints.auth import get_current_user
from app.models.tenant import Tenant, TenantCreate, TenantUpdate

router = APIRouter()

@router.post("/", response_model=Tenant)
async def create_tenant(tenant: TenantCreate, current_user = Depends(get_current_user)):
    # Use SQLite database
    db = get_sqlite_client()
    
    # Generate a unique API key for the tenant
    api_key = f"sk_{secrets.token_urlsafe(32)}"
    
    # Print debug info
    print(f"Creating tenant: {tenant.name} for user ID: {current_user['id']}")
    
    try:
        new_tenant = {
            "id": str(uuid4()),  # Generate UUID for the tenant
            "name": tenant.name,
            "description": tenant.description,
            "website_url": str(tenant.website_url) if tenant.website_url else None,
            "is_active": 1 if tenant.is_active else 0,  # SQLite uses integers for booleans
            "owner_id": current_user["id"],
            "api_key": api_key,
            "has_whatsapp_integration": 1 if tenant.has_whatsapp_integration else 0,
            "has_calendar_integration": 1 if tenant.has_calendar_integration else 0,
            "chat_widget_config": tenant.chat_widget_config,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        
        print(f"New tenant data: {new_tenant}")
        response = db.table('tenants').insert(new_tenant).execute()
        print(f"Tenant creation response: {response.data}")
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create tenant"
            )
            
        return response.data[0]
    except Exception as e:
        print(f"Error creating tenant: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create tenant: {str(e)}"
        )

@router.get("/", response_model=List[Tenant])
async def get_tenants(current_user = Depends(get_current_user)):
    # Use SQLite database
    db = get_sqlite_client()
    
    print(f"Getting tenants for user ID: {current_user['id']}")
    
    try:
        # Get all tenants owned by the current user
        response = db.table('tenants').select('*').eq('owner_id', current_user["id"]).execute()
        print(f"Found {len(response.data)} tenants")
        return response.data
    except Exception as e:
        print(f"Error getting tenants: {e}")
        # Return empty list on error
        return []

@router.get("/{tenant_id}", response_model=Tenant)
async def get_tenant(tenant_id: UUID, current_user = Depends(get_current_user)):
    # Use SQLite database
    db = get_sqlite_client()
    
    print(f"Getting tenant {tenant_id} for user ID: {current_user['id']}")
    
    try:
        # Get the tenant by ID and verify ownership
        response = db.table('tenants').select('*').eq('id', str(tenant_id)).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
            
        tenant = response.data[0]
        
        # Verify that the current user owns this tenant
        if tenant["owner_id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this tenant"
            )
            
        return tenant
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting tenant: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving tenant: {str(e)}"
        )

@router.put("/{tenant_id}", response_model=Tenant)
async def update_tenant(tenant_id: UUID, tenant_update: TenantUpdate, current_user = Depends(get_current_user)):
    # Use SQLite database
    db = get_sqlite_client()
    
    print(f"Updating tenant {tenant_id} for user ID: {current_user['id']}")
    
    try:
        # Get the tenant by ID and verify ownership
        response = db.table('tenants').select('*').eq('id', str(tenant_id)).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
            
        tenant = response.data[0]
        
        # Verify that the current user owns this tenant
        if tenant["owner_id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this tenant"
            )
        
        # Update the tenant
        update_data = tenant_update.dict(exclude_unset=True)
        if "website_url" in update_data and update_data["website_url"]:
            update_data["website_url"] = str(update_data["website_url"])
        
        # Convert boolean fields to integers for SQLite
        if "is_active" in update_data:
            update_data["is_active"] = 1 if update_data["is_active"] else 0
        if "has_whatsapp_integration" in update_data:
            update_data["has_whatsapp_integration"] = 1 if update_data["has_whatsapp_integration"] else 0
        if "has_calendar_integration" in update_data:
            update_data["has_calendar_integration"] = 1 if update_data["has_calendar_integration"] else 0
            
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        response = db.table('tenants').update(update_data).eq('id', str(tenant_id)).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update tenant"
            )
            
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating tenant: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating tenant: {str(e)}"
        )

@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(tenant_id: UUID, current_user = Depends(get_current_user)):
    # Use SQLite database
    db = get_sqlite_client()
    
    print(f"Deleting tenant {tenant_id} for user ID: {current_user['id']}")
    
    try:
        # Get the tenant by ID and verify ownership
        response = db.table('tenants').select('*').eq('id', str(tenant_id)).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
            
        tenant = response.data[0]
        
        # Verify that the current user owns this tenant
        if tenant["owner_id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this tenant"
            )
        
        # Delete the tenant
        db.table('tenants').delete().eq('id', str(tenant_id)).execute()
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting tenant: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting tenant: {str(e)}"
        )