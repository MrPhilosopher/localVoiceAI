from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from typing import List
from uuid import UUID, uuid4
from datetime import datetime
import os
import shutil
from app.db.sqlite_db import get_sqlite_client
from app.api.endpoints.auth import get_current_user
from app.models.document import Document, DocumentCreate, DocumentUpdate
from app.services.llm import process_document

router = APIRouter()

@router.post("/upload", response_model=Document)
async def upload_document(
    background_tasks: BackgroundTasks,
    tenant_id: UUID = Form(...),
    title: str = Form(...),
    description: str = Form(None),
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    # Use SQLite database
    db = get_sqlite_client()
    print(f"Uploading document for tenant {tenant_id}, user {current_user['id']}")
    
    try:
        # Verify tenant ownership
        tenant_response = db.table('tenants').select('*').eq('id', str(tenant_id)).execute()
        
        if not tenant_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
            
        tenant = tenant_response.data[0]
        
        # Verify that the current user owns this tenant
        if tenant["owner_id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to upload documents for this tenant"
            )
        
        # Determine file type
        file_extension = os.path.splitext(file.filename)[1].lower()
        valid_extensions = ['.pdf', '.txt', '.doc', '.docx', '.csv']
        
        if file_extension not in valid_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Supported types: {', '.join(valid_extensions)}"
            )
        
        # Save the file to the documents directory
        storage_path = f"documents/{tenant_id}/{file.filename}"
        print(f"Saving file to: {storage_path}")
        
        # Read file content and save to storage
        file_content = file.file.read()
        file_size = len(file_content)
        print(f"Received file: {file.filename}, size: {file_size} bytes")
        
        # Create a file-like object from the bytes
        from io import BytesIO
        file_like = BytesIO(file_content)
        
        # Save the file using the storage adapter
        db.storage.from_("documents").upload(
            path=storage_path,
            file=file_like
        )
        
        # Create document record
        document = DocumentCreate(
            title=title,
            description=description,
            file_path=storage_path,
            document_type=file_extension[1:],
            tenant_id=tenant_id
        )
        
        new_document = {
            "id": str(uuid4()),  # Generate a UUID for the document
            "title": document.title,
            "description": document.description,
            "file_path": document.file_path,
            "document_type": document.document_type,
            "tenant_id": str(document.tenant_id),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "is_processed": 0,  # Using integers for booleans in SQLite
            "embedding_status": "pending"
        }
        
        print(f"Creating document record: {new_document}")
        response = db.table('documents').insert(new_document).execute()
        print(f"Document creation response: {response.data}")
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create document record"
            )
        
        # Add document processing to background tasks
        document_id = response.data[0]['id']
        background_tasks.add_task(
            process_document,
            document_id=document_id,
            file_path=storage_path,
            document_type=document.document_type,
            tenant_id=str(tenant_id)
        )
        
        print(f"Added document processing to background tasks for document ID: {document_id}")
            
        return response.data[0]
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error uploading document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading document: {str(e)}"
        )

@router.get("/{tenant_id}", response_model=List[Document])
async def get_tenant_documents(tenant_id: UUID, current_user = Depends(get_current_user)):
    # Use SQLite database
    db = get_sqlite_client()
    print(f"Getting documents for tenant {tenant_id}, user {current_user['id']}")
    
    try:
        # Verify tenant ownership
        tenant_response = db.table('tenants').select('*').eq('id', str(tenant_id)).execute()
        
        if not tenant_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
            
        tenant = tenant_response.data[0]
        
        # Verify that the current user owns this tenant
        if tenant["owner_id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access documents for this tenant"
            )
        
        # Get all documents for this tenant
        response = db.table('documents').select('*').eq('tenant_id', str(tenant_id)).execute()
        print(f"Found {len(response.data)} documents")
        return response.data
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting documents: {e}")
        # Return empty list on error
        return []

@router.get("/status/{document_id}", response_model=Document)
async def get_document_status(document_id: UUID, current_user = Depends(get_current_user)):
    """
    Get the status of a document's processing
    """
    # Use SQLite database
    db = get_sqlite_client()
    print(f"Getting status for document {document_id}, user {current_user['id']}")
    
    try:
        # Get the document
        doc_response = db.table('documents').select('*').eq('id', str(document_id)).execute()
        
        if not doc_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        document = doc_response.data[0]
        
        # Get the tenant to verify ownership
        tenant_response = db.table('tenants').select('*').eq('id', document['tenant_id']).execute()
        
        if not tenant_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
            
        tenant = tenant_response.data[0]
        
        # Verify that the current user owns this tenant
        if tenant["owner_id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this document"
            )
        
        return document
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting document status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting document status: {str(e)}"
        )

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: UUID, current_user = Depends(get_current_user)):
    # Use SQLite database
    db = get_sqlite_client()
    print(f"Deleting document {document_id}, user {current_user['id']}")
    
    try:
        # Get the document
        doc_response = db.table('documents').select('*').eq('id', str(document_id)).execute()
        
        if not doc_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        document = doc_response.data[0]
        
        # Get the tenant to verify ownership
        tenant_response = db.table('tenants').select('*').eq('id', document['tenant_id']).execute()
        
        if not tenant_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
            
        tenant = tenant_response.data[0]
        
        # Verify that the current user owns this tenant
        if tenant["owner_id"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this document"
            )
        
        # Delete the file from storage if it exists
        try:
            db.storage.from_("documents").remove([document['file_path']])
            print(f"Deleted file from storage: {document['file_path']}")
        except Exception as storage_error:
            print(f"Error removing file from storage: {storage_error}")
            # Continue with deletion of database record
        
        # First delete any document chunks to avoid foreign key constraint errors
        try:
            db.table('document_chunks').delete().eq('document_id', str(document_id)).execute()
            print(f"Deleted document chunks for document {document_id}")
        except Exception as chunk_error:
            print(f"Error deleting document chunks: {chunk_error}")
            # Continue with document deletion
            
        # Delete the document record
        db.table('documents').delete().eq('id', str(document_id)).execute()
        print(f"Document {document_id} deleted successfully")
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting document: {str(e)}"
        )