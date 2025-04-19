from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from app.models.chat import Chat, Message
from app.schemas.chat import ChatCreate, MessageCreate, ChatUpdate


def create_chat(db: Session, chat: ChatCreate, user_id: int) -> Chat:
    """Create a new chat for a user."""
    db_chat = Chat(**chat.dict(), user_id=user_id)
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)
    return db_chat


def get_chat(db: Session, chat_id: int, user_id: int) -> Optional[Chat]:
    """Get a specific chat by ID for a user."""
    return db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user_id).first()


def get_chats(
    db: Session, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 100,
    active_only: bool = True
) -> List[Chat]:
    """Get all chats for a user."""
    query = db.query(Chat).filter(Chat.user_id == user_id)
    
    if active_only:
        query = query.filter(Chat.is_active == True)
    
    return query.order_by(Chat.updated_at.desc()).offset(skip).limit(limit).all()


def update_chat(db: Session, chat_id: int, user_id: int, chat_update: ChatUpdate) -> Optional[Chat]:
    """Update a chat."""
    db_chat = get_chat(db, chat_id, user_id)
    if not db_chat:
        return None
    
    update_data = chat_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_chat, field, value)
    
    db.commit()
    db.refresh(db_chat)
    return db_chat


def delete_chat(db: Session, chat_id: int, user_id: int) -> bool:
    """Delete a chat (soft delete)."""
    db_chat = get_chat(db, chat_id, user_id)
    if not db_chat:
        return False
    
    db_chat.is_active = False
    db.commit()
    return True


def hard_delete_chat(db: Session, chat_id: int, user_id: int) -> bool:
    """Hard delete a chat and all its messages."""
    db_chat = get_chat(db, chat_id, user_id)
    if not db_chat:
        return False
    
    db.delete(db_chat)
    db.commit()
    return True


def add_message(db: Session, chat_id: int, message: MessageCreate) -> Optional[Message]:
    """Add a message to a chat."""
    # First verify chat exists
    db_chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not db_chat:
        return None
    
    # Create and add the message
    db_message = Message(**message.dict(), chat_id=chat_id)
    db.add(db_message)
    
    # Update the chat's updated_at timestamp
    db_chat.updated_at = func.now()
    
    # If this is a user message and the chat has a generic title or no title,
    # update the title with the first part of the message
    if message.role == 'user' and (db_chat.title is None or db_chat.title == "New Chat"):
        # Get message count for this chat
        message_count = db.query(Message).filter(Message.chat_id == chat_id).count()
        
        # Only update title if this is the first or second message (first user message)
        if message_count <= 1:  # The current message being added isn't counted yet
            # Use up to the first 30 characters for the title
            new_title = message.content[:30].strip()
            # Add ellipsis if the message was truncated
            if len(message.content) > 30:
                new_title += "..."
            db_chat.title = new_title
    
    db.commit()
    db.refresh(db_message)
    return db_message


def get_messages(
    db: Session, 
    chat_id: int, 
    user_id: int,
    skip: int = 0, 
    limit: int = 100
) -> List[Message]:
    """Get messages for a specific chat."""
    # First verify chat exists and belongs to user
    db_chat = db.query(Chat).filter(
        Chat.id == chat_id, 
        Chat.user_id == user_id
    ).first()
    
    if not db_chat:
        return []
    
    return db.query(Message).filter(
        Message.chat_id == chat_id
    ).order_by(Message.created_at).offset(skip).limit(limit).all()


def get_message_by_id(db: Session, message_id: int) -> Optional[Message]:
    """Get a specific message by ID."""
    return db.query(Message).filter(Message.id == message_id).first() 