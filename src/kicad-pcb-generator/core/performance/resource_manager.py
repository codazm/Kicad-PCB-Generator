"""Resource management system for the KiCad PCB Generator."""

import os
import psutil
import threading
import time
import tempfile
import shutil
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging
from pathlib import Path
import json
import weakref
from contextlib import contextmanager

from ..base.base_manager import BaseManager
from ..base.results.manager_result import ManagerResult, ManagerOperation, ManagerStatus


class ResourceType(Enum):
    """Types of resources that can be managed."""
    FILE = "file"
    DIRECTORY = "directory"
    MEMORY = "memory"
    THREAD = "thread"
    NETWORK = "network"
    DATABASE = "database"
    CACHE = "cache"
    TEMPORARY = "temporary"


class ResourceStatus(Enum):
    """Resource status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    CLEANED = "cleaned"


@dataclass
class Resource:
    """Resource information."""
    resource_id: str
    resource_type: ResourceType
    path: Optional[str] = None
    size: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    status: ResourceStatus = ResourceStatus.ACTIVE
    metadata: Dict[str, Any] = field(default_factory=dict)
    cleanup_callback: Optional[Callable] = None


@dataclass
class ResourceMetrics:
    """Resource usage metrics."""
    resource_id: str
    resource_type: ResourceType
    usage_count: int
    total_size: int
    active_count: int
    error_count: int
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


class ResourceManager(BaseManager[Resource]):
    """Advanced resource management system.
    
    Provides resource tracking, cleanup, and optimization capabilities
    for the KiCad PCB Generator.
    """
    
    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        temp_dir: Optional[str] = None,
        max_temp_size: int = 100 * 1024 * 1024,  # 100MB
        cleanup_interval: float = 300.0,  # 5 minutes
        auto_cleanup: bool = True
    ):
        """Initialize the resource manager.
        
        Args:
            logger: Optional logger instance
            temp_dir: Temporary directory path
            max_temp_size: Maximum temporary file size
            cleanup_interval: Automatic cleanup interval in seconds
            auto_cleanup: Enable automatic cleanup
        """
        super().__init__()
        self.logger = logger or logging.getLogger(__name__)
        self.temp_dir = Path(temp_dir) if temp_dir else Path(tempfile.gettempdir()) / "kicad_pcb_generator"
        self.max_temp_size = max_temp_size
        self.cleanup_interval = cleanup_interval
        self.auto_cleanup = auto_cleanup
        
        # Create temporary directory
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Resource tracking
        self._active_resources: Dict[str, Resource] = {}
        self._resource_metrics: Dict[str, ResourceMetrics] = {}
        self._cleanup_callbacks: Dict[str, Callable] = {}
        
        # Cleanup thread
        self._cleanup_thread: Optional[threading.Thread] = None
        self._cleanup_running = False
        
        # Resource limits
        self.resource_limits = {
            ResourceType.FILE: 1000,      # Max files
            ResourceType.DIRECTORY: 100,  # Max directories
            ResourceType.MEMORY: 500 * 1024 * 1024,  # 500MB
            ResourceType.THREAD: 50,      # Max threads
            ResourceType.CACHE: 200 * 1024 * 1024,   # 200MB
            ResourceType.TEMPORARY: 100 * 1024 * 1024  # 100MB
        }
        
        # Start cleanup thread if auto_cleanup is enabled
        if auto_cleanup:
            self._start_cleanup_thread()
        
        self.logger.info("Resource manager initialized")
    
    def _start_cleanup_thread(self) -> None:
        """Start automatic cleanup thread."""
        if self._cleanup_running:
            return
        
        self._cleanup_running = True
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_worker,
            daemon=True
        )
        self._cleanup_thread.start()
        
        self.logger.debug("Resource cleanup thread started")
    
    def _stop_cleanup_thread(self) -> None:
        """Stop automatic cleanup thread."""
        self._cleanup_running = False
        if self._cleanup_thread:
            self._cleanup_thread.join()
            self._cleanup_thread = None
        
        self.logger.debug("Resource cleanup thread stopped")
    
    def _cleanup_worker(self) -> None:
        """Cleanup worker thread."""
        while self._cleanup_running:
            try:
                self.cleanup_resources()
                time.sleep(self.cleanup_interval)
            except Exception as e:
                self.logger.error(f"Error in cleanup worker: {e}")
    
    def register_resource(
        self,
        resource_id: str,
        resource_type: ResourceType,
        path: Optional[str] = None,
        size: Optional[int] = None,
        cleanup_callback: Optional[Callable] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ManagerResult[Resource]:
        """Register a new resource.
        
        Args:
            resource_id: Unique resource identifier
            resource_type: Type of resource
            path: Resource path (for file/directory resources)
            size: Resource size in bytes
            cleanup_callback: Optional cleanup callback function
            metadata: Additional metadata
            
        Returns:
            Manager result with resource information
        """
        try:
            # Check resource limits
            if not self._check_resource_limit(resource_type):
                return ManagerResult[Resource](
                    success=False,
                    error_message=f"Resource limit exceeded for {resource_type.value}",
                    data=None
                )
            
            # Create resource
            resource = Resource(
                resource_id=resource_id,
                resource_type=resource_type,
                path=path,
                size=size,
                metadata=metadata or {},
                cleanup_callback=cleanup_callback
            )
            
            # Store resource
            result = self.create(resource_id, resource)
            
            if result.success:
                # Track active resource
                self._active_resources[resource_id] = resource
                
                # Store cleanup callback
                if cleanup_callback:
                    self._cleanup_callbacks[resource_id] = cleanup_callback
                
                # Update metrics
                self._update_resource_metrics(resource_type, size or 0)
                
                self.logger.debug(f"Registered resource: {resource_id} ({resource_type.value})")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error registering resource {resource_id}: {e}")
            return ManagerResult[Resource](
                success=False,
                error_message=f"Failed to register resource: {e}",
                data=None
            )
    
    def unregister_resource(self, resource_id: str) -> ManagerResult[bool]:
        """Unregister a resource.
        
        Args:
            resource_id: Resource identifier
            
        Returns:
            Manager result indicating success
        """
        try:
            # Get resource
            resource = self._active_resources.get(resource_id)
            if not resource:
                return ManagerResult[bool](
                    success=False,
                    error_message=f"Resource not found: {resource_id}",
                    data=False
                )
            
            # Clean up resource
            self._cleanup_resource(resource)
            
            # Remove from tracking
            self._active_resources.pop(resource_id, None)
            self._cleanup_callbacks.pop(resource_id, None)
            
            # Delete from manager
            result = self.delete(resource_id)
            
            if result.success:
                self.logger.debug(f"Unregistered resource: {resource_id}")
            
            return ManagerResult[bool](
                success=result.success,
                error_message=result.message,
                data=result.success
            )
            
        except Exception as e:
            self.logger.error(f"Error unregistering resource {resource_id}: {e}")
            return ManagerResult[bool](
                success=False,
                error_message=f"Failed to unregister resource: {e}",
                data=False
            )
    
    def get_resource(self, resource_id: str) -> Optional[Resource]:
        """Get resource by ID.
        
        Args:
            resource_id: Resource identifier
            
        Returns:
            Resource object or None
        """
        return self._active_resources.get(resource_id)
    
    def list_resources(self, resource_type: Optional[ResourceType] = None) -> List[Resource]:
        """List all resources, optionally filtered by type.
        
        Args:
            resource_type: Optional resource type filter
            
        Returns:
            List of resources
        """
        resources = list(self._active_resources.values())
        
        if resource_type:
            resources = [r for r in resources if r.resource_type == resource_type]
        
        return resources
    
    def cleanup_resources(self, resource_type: Optional[ResourceType] = None) -> int:
        """Clean up resources.
        
        Args:
            resource_type: Optional resource type to clean up
            
        Returns:
            Number of resources cleaned up
        """
        cleaned_count = 0
        
        try:
            resources_to_clean = []
            
            # Determine which resources to clean
            for resource in self._active_resources.values():
                if resource_type and resource.resource_type != resource_type:
                    continue
                
                # Check if resource should be cleaned
                if self._should_cleanup_resource(resource):
                    resources_to_clean.append(resource)
            
            # Clean up resources
            for resource in resources_to_clean:
                if self._cleanup_resource(resource):
                    cleaned_count += 1
                    self._active_resources.pop(resource.resource_id, None)
                    self._cleanup_callbacks.pop(resource.resource_id, None)
                    self.delete(resource.resource_id)
            
            if cleaned_count > 0:
                self.logger.info(f"Cleaned up {cleaned_count} resources")
            
        except Exception as e:
            self.logger.error(f"Error during resource cleanup: {e}")
        
        return cleaned_count
    
    def _should_cleanup_resource(self, resource: Resource) -> bool:
        """Check if a resource should be cleaned up.
        
        Args:
            resource: Resource to check
            
        Returns:
            True if resource should be cleaned up
        """
        # Check if resource is inactive
        if resource.status == ResourceStatus.INACTIVE:
            return True
        
        # Check if resource is in error state
        if resource.status == ResourceStatus.ERROR:
            return True
        
        # Check temporary file age
        if resource.resource_type == ResourceType.TEMPORARY:
            age = (datetime.now() - resource.created_at).total_seconds()
            if age > 3600:  # 1 hour
                return True
        
        # Check cache age
        if resource.resource_type == ResourceType.CACHE:
            age = (datetime.now() - resource.last_accessed).total_seconds()
            if age > 1800:  # 30 minutes
                return True
        
        return False
    
    def _cleanup_resource(self, resource: Resource) -> bool:
        """Clean up a specific resource.
        
        Args:
            resource: Resource to clean up
            
        Returns:
            True if cleanup was successful
        """
        try:
            # Call custom cleanup callback if available
            if resource.cleanup_callback:
                resource.cleanup_callback(resource)
            
            # Clean up based on resource type
            if resource.resource_type == ResourceType.FILE:
                if resource.path and Path(resource.path).exists():
                    Path(resource.path).unlink()
            
            elif resource.resource_type == ResourceType.DIRECTORY:
                if resource.path and Path(resource.path).exists():
                    shutil.rmtree(resource.path)
            
            elif resource.resource_type == ResourceType.TEMPORARY:
                if resource.path and Path(resource.path).exists():
                    Path(resource.path).unlink()
            
            # Update resource status
            resource.status = ResourceStatus.CLEANED
            
            self.logger.debug(f"Cleaned up resource: {resource.resource_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cleaning up resource {resource.resource_id}: {e}")
            resource.status = ResourceStatus.ERROR
            return False
    
    def _check_resource_limit(self, resource_type: ResourceType) -> bool:
        """Check if resource limit is exceeded.
        
        Args:
            resource_type: Resource type to check
            
        Returns:
            True if limit is not exceeded
        """
        limit = self.resource_limits.get(resource_type)
        if not limit:
            return True
        
        # Count current resources of this type
        current_count = len([r for r in self._active_resources.values() 
                           if r.resource_type == resource_type])
        
        return current_count < limit
    
    def _update_resource_metrics(self, resource_type: ResourceType, size: int) -> None:
        """Update resource metrics.
        
        Args:
            resource_type: Resource type
            size: Resource size
        """
        key = resource_type.value
        
        if key not in self._resource_metrics:
            self._resource_metrics[key] = ResourceMetrics(
                resource_id=key,
                resource_type=resource_type,
                usage_count=0,
                total_size=0,
                active_count=0,
                error_count=0,
                timestamp=datetime.now()
            )
        
        metrics = self._resource_metrics[key]
        metrics.usage_count += 1
        metrics.total_size += size
        metrics.active_count += 1
        metrics.timestamp = datetime.now()
    
    def get_resource_metrics(self) -> Dict[str, ResourceMetrics]:
        """Get resource usage metrics.
        
        Returns:
            Dictionary of resource metrics
        """
        return self._resource_metrics.copy()
    
    def get_resource_report(self) -> Dict[str, Any]:
        """Get comprehensive resource report.
        
        Returns:
            Resource report dictionary
        """
        total_resources = len(self._active_resources)
        total_size = sum(r.size or 0 for r in self._active_resources.values())
        
        # Count by type
        type_counts = {}
        for resource_type in ResourceType:
            type_counts[resource_type.value] = len([
                r for r in self._active_resources.values() 
                if r.resource_type == resource_type
            ])
        
        # Status counts
        status_counts = {}
        for status in ResourceStatus:
            status_counts[status.value] = len([
                r for r in self._active_resources.values() 
                if r.status == status
            ])
        
        return {
            'total_resources': total_resources,
            'total_size_mb': total_size / (1024 * 1024),
            'type_counts': type_counts,
            'status_counts': status_counts,
            'resource_limits': {k.value: v for k, v in self.resource_limits.items()},
            'temp_dir': str(self.temp_dir),
            'auto_cleanup': self.auto_cleanup,
            'cleanup_interval': self.cleanup_interval
        }
    
    @contextmanager
    def temporary_resource(
        self,
        resource_type: ResourceType,
        prefix: str = "temp",
        suffix: str = "",
        cleanup: bool = True
    ):
        """Context manager for temporary resources.
        
        Args:
            resource_type: Type of temporary resource
            prefix: File prefix
            suffix: File suffix
            cleanup: Whether to clean up on exit
            
        Yields:
            Resource object
        """
        resource = None
        try:
            if resource_type == ResourceType.FILE:
                # Create temporary file
                fd, path = tempfile.mkstemp(prefix=prefix, suffix=suffix, dir=self.temp_dir)
                os.close(fd)
                
                resource = Resource(
                    resource_id=f"{prefix}_{int(time.time())}",
                    resource_type=resource_type,
                    path=path,
                    size=0
                )
            
            elif resource_type == ResourceType.DIRECTORY:
                # Create temporary directory
                path = tempfile.mkdtemp(prefix=prefix, dir=self.temp_dir)
                
                resource = Resource(
                    resource_id=f"{prefix}_{int(time.time())}",
                    resource_type=resource_type,
                    path=path,
                    size=0
                )
            
            if resource:
                self.register_resource(
                    resource.resource_id,
                    resource.resource_type,
                    resource.path,
                    resource.size
                )
            
            yield resource
            
        finally:
            if resource and cleanup:
                self.unregister_resource(resource.resource_id)
    
    def _cleanup_item(self, key: str) -> None:
        """Clean up resources for a resource item.
        
        Args:
            key: Resource key to clean up
        """
        # Clean up is handled by _cleanup_resource method
        pass
    
    def _clear_cache(self) -> None:
        """Clear cache after data changes."""
        super()._clear_cache()
    
    def __del__(self):
        """Cleanup when the manager is destroyed."""
        self._stop_cleanup_thread()
        self.cleanup_resources() 