from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.chat import Chat, ChatCreate, ChatUpdate, Message, MessageCreate, ChatWithMessages
from app.services import chat as chat_service

router = APIRouter()


@router.post("/", response_model=Chat, status_code=status.HTTP_201_CREATED)
def create_chat(
    chat: ChatCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new chat"""
    return chat_service.create_chat(db=db, chat=chat, user_id=current_user.id)


@router.get("/", response_model=List[Chat])
def get_chats(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all chats for the current user"""
    return chat_service.get_chats(
        db=db, 
        user_id=current_user.id, 
        skip=skip, 
        limit=limit,
        active_only=active_only
    )


@router.get("/{chat_id}", response_model=ChatWithMessages)
def get_chat(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific chat by ID"""
    db_chat = chat_service.get_chat(db=db, chat_id=chat_id, user_id=current_user.id)
    if db_chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Get messages for this chat
    messages = chat_service.get_messages(
        db=db, 
        chat_id=chat_id, 
        user_id=current_user.id
    )
    
    # Create a ChatWithMessages response
    chat_dict = db_chat.__dict__.copy()
    chat_dict["messages"] = messages
    
    return chat_dict


@router.put("/{chat_id}", response_model=Chat)
def update_chat(
    chat_id: int,
    chat_update: ChatUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a chat"""
    db_chat = chat_service.update_chat(
        db=db, 
        chat_id=chat_id, 
        user_id=current_user.id, 
        chat_update=chat_update
    )
    if db_chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    return db_chat


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat(
    chat_id: int,
    permanent: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a chat (soft delete by default, hard delete if permanent=True)"""
    if permanent:
        result = chat_service.hard_delete_chat(db=db, chat_id=chat_id, user_id=current_user.id)
    else:
        result = chat_service.delete_chat(db=db, chat_id=chat_id, user_id=current_user.id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Chat not found")
    return None


@router.post("/{chat_id}/messages", response_model=List[Message])
def add_message(
    chat_id: int,
    message: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add a message to a chat and get response"""
    # Check if chat exists and belongs to user
    db_chat = chat_service.get_chat(db=db, chat_id=chat_id, user_id=current_user.id)
    if db_chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Add the user message
    db_message = chat_service.add_message(db=db, chat_id=chat_id, message=message)
    if db_message is None:
        raise HTTPException(status_code=500, detail="Failed to add message")
    
    # For now, just echo back the same message if it's from the user
    response_messages = [db_message]
    if message.role == "user":
        # Create an assistant response that echoes back the user's message
        # Format the response as markdown
        markdown_content = message.content
        assistant_message = MessageCreate(
            role="assistant", 
            content=markdown_content.strip()
        )
        
        db_assistant_message = chat_service.add_message(db=db, chat_id=chat_id, message=assistant_message)
        if db_assistant_message:
            response_messages.append(db_assistant_message)
    
    return response_messages


@router.get("/{chat_id}/messages", response_model=List[Message])
def get_messages(
    chat_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all messages for a specific chat"""
    # Check if chat exists and belongs to user
    db_chat = chat_service.get_chat(db=db, chat_id=chat_id, user_id=current_user.id)
    if db_chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    return chat_service.get_messages(
        db=db, 
        chat_id=chat_id, 
        user_id=current_user.id,
        skip=skip,
        limit=limit
    ) 