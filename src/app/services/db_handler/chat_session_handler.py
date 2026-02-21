"""
Chat session handler - manages chat session storage in MongoDB.
Inherits from MongoDBHandler for common CRUD operations.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from src.app.services.db_handler.mongodb_handler import MongoDBHandler
from src.app.core.config import settings
from src.app.utils.logger import setup_logger

logger = setup_logger(__name__)


class ChatSessionHandler(MongoDBHandler):
    """
    Handler for chat_sessions collection.
    
    Stores and retrieves chat conversation history from MongoDB.
    Each session contains messages with role (user/assistant), content, and timestamps.
    """
    
    def __init__(self):
        """
        Initialize chat session handler.
        
        Automatically uses connection settings from config.
        Collection name is hardcoded to "chat_sessions".
        """
        # Initialize parent with chat_sessions collection
        super().__init__(
            collection_name="chat_sessions",
            connection_string=settings.MONGODB_CONNECTION_STRING,
            database_name=settings.MONGODB_DATABASE_NAME
        )
    
    def create_session(self, chat_id: str, user_id: Optional[str] = None) -> str:
        """
        Create a new chat session.
        
        Args:
            chat_id: Unique identifier for the chat session
            user_id: Optional user identifier
            
        Returns:
            str: Inserted document ID
        """
        session_data = {
            "chat_id": chat_id,
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "messages": []
        }
        
        doc_id = self.insert_one(session_data)
        logger.info(f"Created chat session: {chat_id}")
        return doc_id
    
    def add_message(
        self,
        chat_id: str,
        content: str,
        role: str,
        mime_type: str = "TEXT",
        user_id: Optional[str] = None,
    ) -> bool:
        """
        Add a message to an existing chat session.
        
        Args:
            chat_id: Chat session identifier
            content: Message content
            role: Message role ("user" or "assistant")
            mime_type: Message mime type (default: "TEXT")
            
        Returns:
            bool: True if message was added successfully
        """
        message = {
            "content": content,
            "role": role,
            "mime_type": mime_type,
            "timestamp": datetime.utcnow()
        }
        
        # Check if session exists, create if not
        session = self.find_one({"chat_id": chat_id})
        if not session:
            logger.info(f"Session {chat_id} doesn't exist, creating...")
            self.create_session(chat_id, user_id=user_id)
        elif user_id and not session.get("user_id"):
            self.collection.update_one(
                {"chat_id": chat_id},
                {"$set": {"user_id": user_id, "updated_at": datetime.utcnow()}},
            )
        
        # Add message to the messages array
        result = self.collection.update_one(
            {"chat_id": chat_id},
            {
                "$push": {"messages": message},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        success = result.modified_count > 0
        if success:
            logger.debug(f"Added {role} message to session {chat_id}")
        
        return success

    def get_latest_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recently updated session for a specific user.

        Args:
            user_id: User identifier

        Returns:
            Dict or None: Latest session data excluding _id
        """
        session = self.collection.find_one(
            {"user_id": user_id},
            {"_id": 0},
            sort=[("updated_at", -1)],
        )
        return session
    
    def get_session(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a chat session with all messages.
        
        Args:
            chat_id: Chat session identifier
            
        Returns:
            Dict or None: Session data including all messages
        """
        session = self.find_one(
            {"chat_id": chat_id},
            {"_id": 0}  # Exclude MongoDB _id from response
        )
        
        if session:
            logger.info(f"Retrieved session {chat_id} with {len(session.get('messages', []))} messages")
        else:
            logger.warning(f"Session not found: {chat_id}")
        
        return session
    
    def get_messages(self, chat_id: str) -> List[Dict[str, Any]]:
        """
        Get all messages for a chat session.
        
        Args:
            chat_id: Chat session identifier
            
        Returns:
            List[Dict]: List of messages with content, role, mime_type
        """
        session = self.get_session(chat_id)
        
        if not session:
            return []
        
        return session.get("messages", [])
    
    def get_message_count(self, chat_id: str) -> int:
        """
        Get the number of messages in a chat session.
        
        Args:
            chat_id: Chat session identifier
            
        Returns:
            int: Number of messages
        """
        messages = self.get_messages(chat_id)
        return len(messages)
    
    def list_sessions(
        self,
        user_id: Optional[str] = None,
        limit: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List all chat sessions, optionally filtered by user_id.
        
        Args:
            user_id: Optional user identifier to filter by
            limit: Maximum number of sessions to return (0 = no limit)
            
        Returns:
            List[Dict]: List of session summaries
        """
        query = {"user_id": user_id} if user_id else {}
        
        sessions = self.find_many(
            query=query,
            projection={
                "_id": 0,
                "chat_id": 1,
                "user_id": 1,
                "created_at": 1,
                "updated_at": 1,
                "messages": {"$slice": 0}  # Don't include messages, just count
            },
            limit=limit
        )
        
        logger.info(f"Listed {len(sessions)} sessions")
        return sessions
    
    def delete_session(self, chat_id: str) -> bool:
        """
        Delete a chat session and all its messages.
        
        Args:
            chat_id: Chat session identifier
            
        Returns:
            bool: True if session was deleted
        """
        success = self.delete_one({"chat_id": chat_id})
        
        if success:
            logger.info(f"Deleted session: {chat_id}")
        else:
            logger.warning(f"Failed to delete session: {chat_id}")
        
        return success
    
    def clear_messages(self, chat_id: str) -> bool:
        """
        Clear all messages from a chat session but keep the session.
        
        Args:
            chat_id: Chat session identifier
            
        Returns:
            bool: True if messages were cleared
        """
        success = self.update_one(
            {"chat_id": chat_id},
            {
                "messages": [],
                "updated_at": datetime.utcnow()
            }
        )
        
        if success:
            logger.info(f"Cleared messages for session: {chat_id}")
        
        return success
    
    def session_exists(self, chat_id: str) -> bool:
        """
        Check if a chat session exists.
        
        Args:
            chat_id: Chat session identifier
            
        Returns:
            bool: True if session exists
        """
        session = self.find_one({"chat_id": chat_id}, {"_id": 1})
        return session is not None


# Convenience functions
def get_chat_session(chat_id: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to retrieve a chat session.
    
    Args:
        chat_id: Chat session identifier
        
    Returns:
        Dict or None: Session data
    """
    with ChatSessionHandler() as handler:
        return handler.get_session(chat_id)


def save_chat_message(chat_id: str, content: str, role: str) -> bool:
    """
    Convenience function to save a message to a chat session.
    
    Args:
        chat_id: Chat session identifier
        content: Message content
        role: Message role ("user" or "assistant")
        
    Returns:
        bool: True if saved successfully
    """
    with ChatSessionHandler() as handler:
        return handler.add_message(chat_id, content, role)
