"""Cache manager for validation results."""
import hashlib
import json
from typing import Dict, List, Optional, Any, TypeVar, Generic, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from ...utils.logging.logger import Logger
from ..base.base_manager import BaseManager
from ..base.results.manager_result import ManagerResult
import time

if TYPE_CHECKING:
    from ..base.results.manager_result import ManagerResult

T = TypeVar('T')

@dataclass
class CacheItem:
    """Data structure for cache items."""
    id: str
    key: str
    value: Any
    hash_value: str
    created_at: Optional[str] = None
    accessed_at: Optional[str] = None
    ttl: Optional[int] = None  # Time to live in seconds
    access_count: int = 0
    size_bytes: int = 0

class CacheManager(BaseManager[CacheItem]):
    """Manages caching for validation results."""
    
    def __init__(self, logger: Optional[Logger] = None):
        """Initialize cache manager.
        
        Args:
            logger: Optional logger instance
        """
        super().__init__(logger=logger or Logger(__name__))
        self._current_hash: Optional[str] = None
        self._cache_stats = {
            "hits": 0,
            "misses": 0,
            "total_size": 0
        }
    
    def _validate_data(self, item: CacheItem) -> bool:
        """Validate cache item data."""
        if not item.id or not isinstance(item.id, str):
            self.logger.error("Cache item must have a valid string ID")
            return False
        
        if not item.key or not isinstance(item.key, str):
            self.logger.error("Cache item must have a valid string key")
            return False
        
        if item.value is None:
            self.logger.error("Cache item must have a non-None value")
            return False
        
        if not item.hash_value or not isinstance(item.hash_value, str):
            self.logger.error("Cache item must have a valid hash value")
            return False
        
        if item.ttl is not None and (not isinstance(item.ttl, int) or item.ttl < 0):
            self.logger.error("Cache item TTL must be a non-negative integer")
            return False
        
        if not isinstance(item.access_count, int) or item.access_count < 0:
            self.logger.error("Cache item access count must be a non-negative integer")
            return False
        
        if not isinstance(item.size_bytes, int) or item.size_bytes < 0:
            self.logger.error("Cache item size must be a non-negative integer")
            return False
        
        return True
    
    def _cleanup_item(self, item: CacheItem) -> None:
        """Clean up cache item resources."""
        try:
            # Update cache statistics
            self._cache_stats["total_size"] -= item.size_bytes
            
            self.logger.debug(f"Cleaned up cache item: {item.id}")
        except (KeyError, TypeError, AttributeError) as e:
            self.logger.warning(f"Data processing error during cache item cleanup: {str(e)}")
        except Exception as e:
            self.logger.warning(f"Unexpected error during cache item cleanup: {str(e)}")
    
    def _clear_cache(self) -> None:
        """Clear cache manager cache."""
        try:
            # Reset cache statistics
            self._cache_stats = {
                "hits": 0,
                "misses": 0,
                "total_size": 0
            }
            self._current_hash = None
            
            self.logger.debug("Cleared cache manager cache")
        except (KeyError, TypeError, AttributeError) as e:
            self.logger.warning(f"Data processing error clearing cache manager cache: {str(e)}")
        except Exception as e:
            self.logger.warning(f"Unexpected error clearing cache manager cache: {str(e)}")
    
    def create_cache_item(self, 
                         key: str, 
                         value: Any, 
                         ttl: Optional[int] = None) -> ManagerResult[CacheItem]:
        """Create a new cache item."""
        try:
            # Calculate hash for the key-value pair
            hash_value = self.calculate_hash({"key": key, "value": value})
            
            # Calculate size
            size_bytes = len(json.dumps(value).encode('utf-8'))
            
            cache_id = f"cache_{hash_value[:8]}"
            cache_item = CacheItem(
                id=cache_id,
                key=key,
                value=value,
                hash_value=hash_value,
                ttl=ttl,
                size_bytes=size_bytes
            )
            
            result = self.create(cache_item)
            if result.success:
                # Update cache statistics
                self._cache_stats["total_size"] += size_bytes
                self.logger.info(f"Created cache item: {cache_id}")
            
            return result
            
        except (json.JSONEncodeError, TypeError) as e:
            self.logger.error(f"Data serialization error creating cache item: {str(e)}")
            return ManagerResult[CacheItem](
                success=False,
                error_message=f"Data serialization error: {str(e)}",
                data=None
            )
        except (ValueError, AttributeError) as e:
            self.logger.error(f"Data processing error creating cache item: {str(e)}")
            return ManagerResult[CacheItem](
                success=False,
                error_message=f"Data processing error: {str(e)}",
                data=None
            )
        except Exception as e:
            self.logger.error(f"Unexpected error creating cache item: {str(e)}")
            return ManagerResult[CacheItem](
                success=False,
                error_message=f"Unexpected error: {str(e)}",
                data=None
            )
    
    def get_cache_item(self, key: str) -> ManagerResult[CacheItem]:
        """Get a cache item by key."""
        try:
            # Find cache item by key
            for item in self._items.values():
                if item.key == key:
                    # Update access statistics
                    item.access_count += 1
                    self._cache_stats["hits"] += 1
                    
                    # Check TTL
                    if item.ttl is not None:
                        current_time = time.time()
                        item_created = float(item.created_at) if item.created_at else 0
                        
                        if current_time - item_created > item.ttl:
                            # Item has expired, remove it
                            self.logger.debug(f"Cache item {key} has expired, removing")
                            self.delete(item.id)
                            self._cache_stats["misses"] += 1
                            return ManagerResult[CacheItem](
                                success=False,
                                error_message=f"Cache item expired: {key}",
                                data=None
                            )
                    
                    return ManagerResult[CacheItem](
                        success=True,
                        data=item
                    )
            
            # Cache miss
            self._cache_stats["misses"] += 1
            return ManagerResult[CacheItem](
                success=False,
                error_message=f"Cache item not found: {key}",
                data=None
            )
            
        except (KeyError, TypeError, AttributeError) as e:
            self.logger.error(f"Data processing error getting cache item {key}: {str(e)}")
            return ManagerResult[CacheItem](
                success=False,
                error_message=f"Data processing error: {str(e)}",
                data=None
            )
        except Exception as e:
            self.logger.error(f"Unexpected error getting cache item {key}: {str(e)}")
            return ManagerResult[CacheItem](
                success=False,
                error_message=f"Unexpected error: {str(e)}",
                data=None
            )
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "total_items": len(self._items),
            "hits": self._cache_stats["hits"],
            "misses": self._cache_stats["misses"],
            "hit_rate": self._cache_stats["hits"] / (self._cache_stats["hits"] + self._cache_stats["misses"]) if (self._cache_stats["hits"] + self._cache_stats["misses"]) > 0 else 0,
            "total_size_mb": self._cache_stats["total_size"] / (1024 * 1024),
            "average_item_size": self._cache_stats["total_size"] / len(self._items) if self._items else 0
        }
    
    def calculate_hash(self, obj: Any) -> str:
        """Calculate hash for an object.
        
        Args:
            obj: Object to hash
            
        Returns:
            Hash string
        """
        try:
            # Convert object to JSON string
            obj_str = json.dumps(obj, sort_keys=True)
            # Calculate hash
            return hashlib.sha256(obj_str.encode()).hexdigest()
        except (json.JSONEncodeError, TypeError) as e:
            self.logger.error(f"Data serialization error calculating hash: {str(e)}")
            return ""
        except Exception as e:
            self.logger.error(f"Unexpected error calculating hash: {str(e)}")
            return ""
    
    def get_cached(self, obj: Any) -> Optional[T]:
        """Get cached results if available.
        
        Args:
            obj: Object to get cache for
            
        Returns:
            Cached results if available, None otherwise
        """
        obj_hash = self.calculate_hash(obj)
        if obj_hash == self._current_hash:
            # Find cache item by hash
            for item in self._items.values():
                if item.hash_value == obj_hash:
                    self.logger.debug("Using cached results")
                    return item.value
        return None
    
    def cache_results(self, obj: Any, results: T) -> None:
        """Cache results for an object.
        
        Args:
            obj: Object to cache results for
            results: Results to cache
        """
        try:
            obj_hash = self.calculate_hash(obj)
            self._current_hash = obj_hash
            
            # Create cache item
            cache_item = CacheItem(
                id=f"cache_{obj_hash[:8]}",
                key=str(obj_hash),
                value=results,
                hash_value=obj_hash,
                size_bytes=len(json.dumps(results).encode('utf-8'))
            )
            
            # Add to cache
            self.create(cache_item)
            self.logger.debug("Cached results")
            
        except (json.JSONEncodeError, TypeError) as e:
            self.logger.error(f"Data serialization error caching results: {str(e)}")
        except (ValueError, AttributeError) as e:
            self.logger.error(f"Data processing error caching results: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error caching results: {str(e)}")
    
    def clear_cache(self) -> None:
        """Clear the cache."""
        try:
            self.clear()
            self._current_hash = None
            self.logger.debug("Cleared cache")
        except (KeyError, TypeError, AttributeError) as e:
            self.logger.error(f"Data processing error clearing cache: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error clearing cache: {str(e)}")
    
    @lru_cache(maxsize=32)
    def get_cached_property(self, obj: Any, property_name: str) -> Optional[Any]:
        """Get cached property value.
        
        Args:
            obj: Object to get property for
            property_name: Name of property
            
        Returns:
            Cached property value if available, None otherwise
        """
        obj_hash = self.calculate_hash(obj)
        for item in self._items.values():
            if item.hash_value == obj_hash:
                return getattr(item.value, property_name, None)
        return None 