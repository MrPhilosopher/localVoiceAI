from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import List, Dict, Any
from uuid import UUID
from datetime import datetime
from app.db.sqlite_db import get_sqlite_client
from app.api.endpoints.auth import get_current_user
from app.models.chat import Conversation, Message, ConversationCreate
from app.services.llm import process_chat_message

router = APIRouter()

@router.post("/conversation", response_model=Conversation)
async def create_conversation(conversation: ConversationCreate):
    db = get_sqlite_client()
    
    # Verify tenant exists
    tenant_response = db.table('tenants').select('*').eq('id', str(conversation.tenant_id)).execute()
    
    if not tenant_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    new_conversation = {
        "tenant_id": str(conversation.tenant_id),
        "session_id": conversation.session_id,
        "customer_identifier": conversation.customer_identifier,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "is_active": 1  # Using integers for booleans in SQLite
    }
    
    response = db.table('conversations').insert(new_conversation).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create conversation"
        )
    
    return {**response.data[0], "messages": []}

@router.post("/message/{conversation_id}", response_model=Message)
async def send_message(
    conversation_id: UUID,
    message: Dict[str, Any] = Body(...),
):
    db = get_sqlite_client()
    
    # Get the conversation
    conversation_response = db.table('conversations').select('*').eq('id', str(conversation_id)).execute()
    
    if not conversation_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    conversation = conversation_response.data[0]
    
    if not conversation["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Conversation is not active"
        )
    
    # Create and save the user message
    user_message = {
        "conversation_id": str(conversation_id),
        "content": message["content"],
        "role": "user",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    user_msg_response = db.table('messages').insert(user_message).execute()
    
    if not user_msg_response.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to save user message"
        )
    
    # Get the tenant for this conversation
    tenant_id = conversation["tenant_id"]
    tenant_response = db.table('tenants').select('*').eq('id', tenant_id).execute()
    
    if not tenant_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    tenant = tenant_response.data[0]
    
    # Get conversation history
    history_response = db.table('messages').select('*').eq('conversation_id', str(conversation_id)).execute()
    conversation_history = history_response.data
    
    # Process the message with the AI
    try:
        ai_response = await process_chat_message(
            message["content"],
            conversation_history,
            tenant_id,
            conversation["session_id"]
        )
        
        # Save the AI response
        assistant_message = {
            "conversation_id": str(conversation_id),
            "content": ai_response,
            "role": "assistant",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        assistant_msg_response = db.table('messages').insert(assistant_message).execute()
        
        if not assistant_msg_response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to save assistant message"
            )
        
        # Update conversation last activity time
        db.table('conversations').update({"updated_at": datetime.utcnow().isoformat()}).eq('id', str(conversation_id)).execute()
        
        return assistant_msg_response.data[0]
    
    except Exception as e:
        print(f"Error processing message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}"
        )

@router.get("/conversation/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: UUID):
    db = get_sqlite_client()
    
    # Get the conversation
    conversation_response = db.table('conversations').select('*').eq('id', str(conversation_id)).execute()
    
    if not conversation_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    conversation = conversation_response.data[0]
    
    # Get all messages for this conversation
    messages_response = db.table('messages').select('*').eq('conversation_id', str(conversation_id)).execute()
    messages = messages_response.data
    
    return {**conversation, "messages": messages}

@router.get("/conversations/{tenant_id}", response_model=List[Conversation])
async def get_tenant_conversations(
    tenant_id: UUID,
    current_user = Depends(get_current_user)
):
    db = get_sqlite_client()
    
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
            detail="Not authorized to access conversations for this tenant"
        )
    
    # Get all conversations for this tenant
    conversations_response = db.table('conversations').select('*').eq('tenant_id', str(tenant_id)).execute()
    conversations = conversations_response.data
    
    # For each conversation, get its messages
    result = []
    for conv in conversations:
        messages_response = db.table('messages').select('*').eq('conversation_id', conv['id']).execute()
        result.append({**conv, "messages": messages_response.data})
    
    return result