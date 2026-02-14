"""
Base MongoDB handler with common CRUD operations.
Provides a foundation for collection-specific handlers.
"""

from typing import List, Dict, Any, Optional
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from abc import ABC
from src.app.core.config import settings
from src.app.utils.logger import setup_logger

logger = setup_logger(__name__)


class MongoDBHandler(ABC):
    """
    Base class for MongoDB collection handlers.
    
    Provides common CRUD operations that can be used by all collection handlers.
    Child classes should set collection_name in their __init__.
    
    Best Practices:
    - Child classes inherit connection management and common operations
    - Collection-specific business logic goes in child classes
    - Consistent error handling and logging across all handlers
    - Resource cleanup with close() method
    """
    
    def __init__(
        self,
        collection_name: str,
        connection_string: str = settings.MONGODB_CONNECTION_STRING,
        database_name: str = settings.MONGODB_DATABASE_NAME
    ):
        """
        Initialize MongoDB connection.
        
        Args:
            collection_name: Name of the MongoDB collection
            connection_string: MongoDB connection string
            database_name: Database name
        """
        try:
            self.client = MongoClient(connection_string)
            self.db = self.client[database_name]
            self.collection = self.db[collection_name]
            self.collection_name = collection_name
            self.database_name = database_name
            logger.info(f"Connected to MongoDB: {database_name}.{collection_name}")
        except PyMongoError as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def insert_one(self, document: Dict[str, Any]) -> str:
        """
        Insert a single document.
        
        Args:
            document: Document to insert
            
        Returns:
            str: Inserted document ID
        """
        try:
            result = self.collection.insert_one(document)
            logger.debug(f"Inserted document with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except PyMongoError as e:
            logger.error(f"Failed to insert document: {e}")
            raise
    
    def insert_many(self, documents: List[Dict[str, Any]]) -> List[str]:
        """
        Insert multiple documents.
        
        Args:
            documents: List of documents to insert
            
        Returns:
            List[str]: List of inserted document IDs
        """
        try:
            if not documents:
                logger.warning("No documents to insert")
                return []
            
            result = self.collection.insert_many(documents)
            inserted_ids = [str(id) for id in result.inserted_ids]
            logger.info(f"Inserted {len(inserted_ids)} documents")
            return inserted_ids
        except PyMongoError as e:
            logger.error(f"Failed to bulk insert documents: {e}")
            raise
    
    def find_one(
        self,
        query: Dict[str, Any],
        projection: Optional[Dict[str, int]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find a single document.
        
        Args:
            query: Query filter
            projection: Fields to include/exclude
            
        Returns:
            Dict or None: Found document
        """
        try:
            document = self.collection.find_one(query, projection)
            return document
        except PyMongoError as e:
            logger.error(f"Failed to find document: {e}")
            return None
    
    def find_many(
        self,
        query: Dict[str, Any] = {},
        projection: Optional[Dict[str, int]] = None,
        limit: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Find multiple documents.
        
        Args:
            query: Query filter (empty dict returns all)
            projection: Fields to include/exclude
            limit: Maximum number of documents to return (0 = no limit)
            
        Returns:
            List[Dict]: List of found documents
        """
        try:
            cursor = self.collection.find(query, projection)
            if limit > 0:
                cursor = cursor.limit(limit)
            return list(cursor)
        except PyMongoError as e:
            logger.error(f"Failed to find documents: {e}")
            return []
    
    def update_one(
        self,
        query: Dict[str, Any],
        update: Dict[str, Any]
    ) -> bool:
        """
        Update a single document.
        
        Args:
            query: Query filter to find document
            update: Update operations
            
        Returns:
            bool: True if document was modified
        """
        try:
            result = self.collection.update_one(query, {"$set": update})
            return result.modified_count > 0
        except PyMongoError as e:
            logger.error(f"Failed to update document: {e}")
            return False
    
    def update_many(
        self,
        query: Dict[str, Any],
        update: Dict[str, Any]
    ) -> int:
        """
        Update multiple documents.
        
        Args:
            query: Query filter to find documents
            update: Update operations
            
        Returns:
            int: Number of documents modified
        """
        try:
            result = self.collection.update_many(query, {"$set": update})
            logger.info(f"Updated {result.modified_count} documents")
            return result.modified_count
        except PyMongoError as e:
            logger.error(f"Failed to update documents: {e}")
            return 0
    
    def delete_one(self, query: Dict[str, Any]) -> bool:
        """
        Delete a single document.
        
        Args:
            query: Query filter to find document
            
        Returns:
            bool: True if document was deleted
        """
        try:
            result = self.collection.delete_one(query)
            return result.deleted_count > 0
        except PyMongoError as e:
            logger.error(f"Failed to delete document: {e}")
            return False
    
    def delete_many(self, query: Dict[str, Any] = {}) -> int:
        """
        Delete multiple documents.
        
        Args:
            query: Query filter (empty dict deletes all)
            
        Returns:
            int: Number of documents deleted
        """
        try:
            result = self.collection.delete_many(query)
            logger.info(f"Deleted {result.deleted_count} documents")
            return result.deleted_count
        except PyMongoError as e:
            logger.error(f"Failed to delete documents: {e}")
            return 0
    
    def count_documents(self, query: Dict[str, Any] = {}) -> int:
        """
        Count documents matching query.
        
        Args:
            query: Query filter (empty dict counts all)
            
        Returns:
            int: Number of matching documents
        """
        try:
            count = self.collection.count_documents(query)
            return count
        except PyMongoError as e:
            logger.error(f"Failed to count documents: {e}")
            return 0
    
    def close(self):
        """Close MongoDB connection."""
        try:
            self.client.close()
            logger.info(f"MongoDB connection closed for {self.database_name}.{self.collection_name}")
        except PyMongoError as e:
            logger.error(f"Error closing MongoDB connection: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures connection is closed."""
        self.close()