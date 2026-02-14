"""
Injury collection handler - manages physiotherapy injury documents.
Inherits from MongoDBHandler for common CRUD operations.
"""

from typing import List, Dict, Any, Optional
from pymongo.errors import PyMongoError
from src.app.services.db_handler.mongodb_handler import MongoDBHandler
from src.app.core.config import settings
from src.app.utils.logger import setup_logger

logger = setup_logger(__name__)


class InjuryHandler(MongoDBHandler):
    """
    Handler for injuries collection.
    
    Inherits common CRUD operations from MongoDBHandler and adds
    injury-specific business logic and validation.
    
    Automatically uses connection settings and collection name from config.
    """
    
    def __init__(self):
        """
        Initialize injury handler.
        
        Connection string, database name, and collection name are
        automatically loaded from settings.
        """
        # Initialize parent with collection name from settings
        super().__init__(
            collection_name=settings.MONGODB_COLLECTION_NAME,
            connection_string=settings.MONGODB_CONNECTION_STRING,
            database_name=settings.MONGODB_DATABASE_NAME
        )
    
    def _validate_injury(self, injury_data: Dict[str, Any]) -> None:
        """
        Validate injury document has required fields.
        
        Args:
            injury_data: Injury document to validate
            
        Raises:
            ValueError: If required fields are missing
        """
        required_fields = ["title", "content", "tags"]
        for field in required_fields:
            if field not in injury_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate tags is a list
        if not isinstance(injury_data["tags"], list):
            raise ValueError("Field 'tags' must be a list")
    
    def add_injury(self, injury_data: Dict[str, Any]) -> str:
        """
        Add a single injury document with validation.
        
        Args:
            injury_data: Dictionary containing injury information
                Required fields: title, content, tags
                
        Returns:
            str: Inserted document ID
            
        Example:
            ```python
            injury = {
                "title": "Tennis Elbow",
                "content": "Overuse injury of the elbow...",
                "tags": ["elbow", "overuse", "tendinitis"]
            }
            injury_id = handler.add_injury(injury)
            ```
        """
        # Validate before inserting
        self._validate_injury(injury_data)
        
        # Use inherited insert_one method
        injury_id = self.insert_one(injury_data)
        logger.info(f"Added injury: {injury_data.get('title')}")
        return injury_id
    
    def add_injuries_bulk(self, injuries: List[Dict[str, Any]]) -> List[str]:
        """
        Add multiple injury documents with validation.
        
        Args:
            injuries: List of injury dictionaries
            
        Returns:
            List[str]: List of inserted document IDs
        """
        # Validate all injuries before inserting
        for injury in injuries:
            self._validate_injury(injury)
        
        # Use inherited insert_many method
        inserted_ids = self.insert_many(injuries)
        logger.info(f"Added {len(inserted_ids)} injuries in bulk")
        return inserted_ids
    
    def get_all_injuries(self) -> List[Dict[str, Any]]:
        """
        Retrieve all injury documents formatted like SAMPLE_DOCUMENTS.
        
        Returns:
            List[Dict]: List of injury documents (title, content, tags only)
        """
        # Use inherited find_many with projection to exclude _id
        projection = {"_id": 0, "title": 1, "content": 1, "tags": 1}
        injuries = self.find_many(query={}, projection=projection)
        logger.info(f"Retrieved {len(injuries)} injuries")
        return injuries
    
    def get_injury_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific injury by title.
        
        Args:
            title: Title of the injury to find
            
        Returns:
            Dict or None: Injury document if found
        """
        projection = {"_id": 0, "title": 1, "content": 1, "tags": 1}
        injury = self.find_one({"title": title}, projection)
        
        if injury:
            logger.info(f"Found injury: {title}")
        else:
            logger.warning(f"Injury not found: {title}")
        
        return injury
    
    def get_injuries_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """
        Retrieve injuries filtered by tag.
        
        Args:
            tag: Tag to filter by
            
        Returns:
            List[Dict]: List of matching injury documents
        """
        projection = {"_id": 0, "title": 1, "content": 1, "tags": 1}
        injuries = self.find_many({"tags": tag}, projection)
        logger.info(f"Found {len(injuries)} injuries with tag '{tag}'")
        return injuries
    
    def update_injury(self, title: str, update_data: Dict[str, Any]) -> bool:
        """
        Update an existing injury document.
        
        Args:
            title: Title of the injury to update
            update_data: Dictionary with fields to update
            
        Returns:
            bool: True if updated successfully
        """
        # Use inherited update_one method
        success = self.update_one({"title": title}, update_data)
        
        if success:
            logger.info(f"Updated injury: {title}")
        else:
            logger.warning(f"No injury updated for title: {title}")
        
        return success
    
    def delete_injury(self, title: str) -> bool:
        """
        Delete an injury document by title.
        
        Args:
            title: Title of the injury to delete
            
        Returns:
            bool: True if deleted successfully
        """
        # Use inherited delete_one method
        success = self.delete_one({"title": title})
        
        if success:
            logger.info(f"Deleted injury: {title}")
        else:
            logger.warning(f"No injury deleted for title: {title}")
        
        return success
    
    def count_injuries(self) -> int:
        """
        Get the total count of injuries in the collection.
        
        Returns:
            int: Number of injury documents
        """
        # Use inherited count_documents method
        count = self.count_documents()
        logger.info(f"Total injuries: {count}")
        return count
    
    def clear_collection(self) -> int:
        """
        Delete all documents from the injuries collection.
        WARNING: This action cannot be undone!
        
        Returns:
            int: Number of documents deleted
        """
        # Use inherited delete_many method
        deleted_count = self.delete_many({})
        logger.warning(f"Cleared injuries collection: {deleted_count} documents deleted")
        return deleted_count


# Convenience functions
def get_injuries_from_mongodb() -> List[Dict[str, Any]]:
    """
    Convenience function to retrieve all injuries from MongoDB.
    Can be used as a drop-in replacement for get_sample_documents().
    
    Uses context manager to ensure proper connection cleanup.
    
    Returns:
        List[Dict]: List of injury documents
    """
    with InjuryHandler() as handler:
        return handler.get_all_injuries()
