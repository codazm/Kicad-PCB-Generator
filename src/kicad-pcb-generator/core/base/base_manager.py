"""
Base manager class for standardizing CRUD operations.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TypeVar, Generic
import logging

from .results.manager_result import ManagerResult, ManagerOperation, ManagerStatus

logger = logging.getLogger(__name__)

T = TypeVar('T')

class BaseManager(ABC, Generic[T]):
    """Base class for all manager classes."""
    
    def __init__(self):
        """Initialize the base manager."""
        self._items: Dict[str, T] = {}
        self._cache: Dict[str, Any] = {}
        
    def create(self, key: str, data: T) -> ManagerResult:
        """Create a new item.
        
        Args:
            key: Unique identifier for the item
            data: Item data
            
        Returns:
            Manager result
        """
        try:
            if key in self._items:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.CREATE,
                    status=ManagerStatus.FAILED,
                    message=f"Item with key '{key}' already exists",
                    errors=[f"Duplicate key: {key}"]
                )
            
            # Validate data
            validation_result = self._validate_data(data)
            if not validation_result.success:
                return validation_result
            
            # Store item
            self._items[key] = data
            self._clear_cache()
            
            logger.info(f"Created item with key '{key}'")
            return ManagerResult(
                success=True,
                operation=ManagerOperation.CREATE,
                status=ManagerStatus.SUCCESS,
                data=data,
                message=f"Successfully created item '{key}'",
                affected_items=1,
                item_ids=[key]
            )
            
        except Exception as e:
            logger.error(f"Error creating item '{key}': {e}")
            return ManagerResult(
                success=False,
                operation=ManagerOperation.CREATE,
                status=ManagerStatus.FAILED,
                message=f"Error creating item: {e}",
                errors=[str(e)]
            )
    
    def read(self, key: str) -> ManagerResult:
        """Read an item by key.
        
        Args:
            key: Unique identifier for the item
            
        Returns:
            Manager result
        """
        try:
            if key not in self._items:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.READ,
                    status=ManagerStatus.FAILED,
                    message=f"Item with key '{key}' not found",
                    errors=[f"Key not found: {key}"]
                )
            
            data = self._items[key]
            logger.debug(f"Read item with key '{key}'")
            return ManagerResult(
                success=True,
                operation=ManagerOperation.READ,
                status=ManagerStatus.SUCCESS,
                data=data,
                message=f"Successfully read item '{key}'",
                affected_items=1,
                item_ids=[key]
            )
            
        except Exception as e:
            logger.error(f"Error reading item '{key}': {e}")
            return ManagerResult(
                success=False,
                operation=ManagerOperation.READ,
                status=ManagerStatus.FAILED,
                message=f"Error reading item: {e}",
                errors=[str(e)]
            )
    
    def update(self, key: str, data: T) -> ManagerResult:
        """Update an existing item.
        
        Args:
            key: Unique identifier for the item
            data: Updated item data
            
        Returns:
            Manager result
        """
        try:
            if key not in self._items:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.UPDATE,
                    status=ManagerStatus.FAILED,
                    message=f"Item with key '{key}' not found",
                    errors=[f"Key not found: {key}"]
                )
            
            # Validate data
            validation_result = self._validate_data(data)
            if not validation_result.success:
                return validation_result
            
            # Update item
            self._items[key] = data
            self._clear_cache()
            
            logger.info(f"Updated item with key '{key}'")
            return ManagerResult(
                success=True,
                operation=ManagerOperation.UPDATE,
                status=ManagerStatus.SUCCESS,
                data=data,
                message=f"Successfully updated item '{key}'",
                affected_items=1,
                item_ids=[key]
            )
            
        except Exception as e:
            logger.error(f"Error updating item '{key}': {e}")
            return ManagerResult(
                success=False,
                operation=ManagerOperation.UPDATE,
                status=ManagerStatus.FAILED,
                message=f"Error updating item: {e}",
                errors=[str(e)]
            )
    
    def delete(self, key: str) -> ManagerResult:
        """Delete an item by key.
        
        Args:
            key: Unique identifier for the item
            
        Returns:
            Manager result
        """
        try:
            if key not in self._items:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.DELETE,
                    status=ManagerStatus.FAILED,
                    message=f"Item with key '{key}' not found",
                    errors=[f"Key not found: {key}"]
                )
            
            # Perform cleanup if needed
            self._cleanup_item(key)
            
            # Remove item
            del self._items[key]
            self._clear_cache()
            
            logger.info(f"Deleted item with key '{key}'")
            return ManagerResult(
                success=True,
                operation=ManagerOperation.DELETE,
                status=ManagerStatus.SUCCESS,
                message=f"Successfully deleted item '{key}'",
                affected_items=1,
                item_ids=[key]
            )
            
        except Exception as e:
            logger.error(f"Error deleting item '{key}': {e}")
            return ManagerResult(
                success=False,
                operation=ManagerOperation.DELETE,
                status=ManagerStatus.FAILED,
                message=f"Error deleting item: {e}",
                errors=[str(e)]
            )
    
    def list_all(self) -> ManagerResult:
        """List all items.
        
        Returns:
            Manager result with list of items
        """
        try:
            items = list(self._items.values())
            item_ids = list(self._items.keys())
            logger.debug(f"Listed {len(items)} items")
            return ManagerResult(
                success=True,
                operation=ManagerOperation.LIST,
                status=ManagerStatus.SUCCESS,
                data=items,
                message=f"Found {len(items)} items",
                affected_items=len(items),
                total_items=len(items),
                item_ids=item_ids
            )
            
        except Exception as e:
            logger.error(f"Error listing items: {e}")
            return ManagerResult(
                success=False,
                operation=ManagerOperation.LIST,
                status=ManagerStatus.FAILED,
                message=f"Error listing items: {e}",
                errors=[str(e)]
            )
    
    def exists(self, key: str) -> bool:
        """Check if an item exists.
        
        Args:
            key: Unique identifier for the item
            
        Returns:
            True if item exists
        """
        return key in self._items
    
    def count(self) -> int:
        """Get the number of items.
        
        Returns:
            Number of items
        """
        return len(self._items)
    
    def clear(self) -> None:
        """Clear all items."""
        self._items.clear()
        self._clear_cache()
        logger.info("Cleared all items")
    
    @abstractmethod
    def _validate_data(self, data: T) -> ManagerResult:
        """Validate data before storage.
        
        Args:
            data: Data to validate
            
        Returns:
            Validation result
        """
        pass
    
    def _cleanup_item(self, key: str) -> None:
        """Clean up resources for an item.
        
        Args:
            key: Item key to clean up
        """
        # Override in subclasses if needed
        pass
    
    def _clear_cache(self) -> None:
        """Clear cache after data changes."""
        # Override in subclasses if needed
        pass
    
    def get_cache(self, key: str) -> Optional[Any]:
        """Get cached value.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        return self._cache.get(key)
    
    def set_cache(self, key: str, value: Any) -> None:
        """Set cached value.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        self._cache[key] = value 