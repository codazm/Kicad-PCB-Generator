"""Performance optimization manager for the KiCad PCB Generator."""

import time
import threading
import functools
import weakref
from typing import Dict, List, Optional, Any, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging
import json
import pickle
from pathlib import Path
import hashlib
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing

from ..base.base_manager import BaseManager
from ..base.results.manager_result import ManagerResult, ManagerOperation, ManagerStatus


class OptimizationType(Enum):
    """Types of optimizations."""
    CACHING = "caching"
    PARALLELIZATION = "parallelization"
    ALGORITHM = "algorithm"
    MEMORY = "memory"
    NETWORK = "network"
    DATABASE = "database"


class OptimizationStatus(Enum):
    """Optimization status."""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    DISABLED = "disabled"


@dataclass
class OptimizationConfig:
    """Optimization configuration."""
    optimization_id: str
    optimization_type: OptimizationType
    enabled: bool = True
    priority: int = 1  # Higher number = higher priority
    max_workers: int = 4
    cache_size: int = 1000
    cache_ttl: int = 3600  # seconds
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OptimizationResult:
    """Optimization result."""
    optimization_id: str
    optimization_type: OptimizationType
    status: OptimizationStatus
    performance_improvement: float  # percentage
    execution_time: float
    memory_saved: int  # bytes
    timestamp: datetime
    details: str
    metadata: Dict[str, Any] = field(default_factory=dict)


T = TypeVar('T')


class OptimizationManager(BaseManager[OptimizationConfig]):
    """Advanced performance optimization manager.
    
    Provides caching, parallelization, and algorithm optimization
    for the KiCad PCB Generator.
    """
    
    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        cache_dir: Optional[str] = None,
        max_workers: int = None,
        enable_parallelization: bool = True,
        enable_caching: bool = True
    ):
        """Initialize the optimization manager.
        
        Args:
            logger: Optional logger instance
            cache_dir: Cache directory path
            max_workers: Maximum number of worker threads/processes
            enable_parallelization: Enable parallel processing
            enable_caching: Enable caching optimizations
        """
        super().__init__()
        self.logger = logger or logging.getLogger(__name__)
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".kicad_pcb_generator" / "cache"
        self.max_workers = max_workers or min(32, (multiprocessing.cpu_count() or 1) + 4)
        self.enable_parallelization = enable_parallelization
        self.enable_caching = enable_caching
        
        # Create cache directory
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Optimization configurations
        self._optimizations: Dict[str, OptimizationConfig] = {}
        self._optimization_results: Dict[str, OptimizationResult] = {}
        
        # Caching system
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, float] = {}
        self._cache_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Thread and process pools
        self._thread_pool: Optional[ThreadPoolExecutor] = None
        self._process_pool: Optional[ProcessPoolExecutor] = None
        
        # Performance tracking
        self._performance_history: List[Dict[str, Any]] = []
        self._optimization_stats: Dict[str, Dict[str, Any]] = {}
        
        # Initialize pools
        if enable_parallelization:
            self._initialize_pools()
        
        # Initialize default optimizations
        self._initialize_default_optimizations()
        
        self.logger.info("Optimization manager initialized")
    
    def _initialize_pools(self) -> None:
        """Initialize thread and process pools."""
        try:
            self._thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
            self._process_pool = ProcessPoolExecutor(max_workers=self.max_workers)
            self.logger.debug(f"Initialized pools with {self.max_workers} workers")
        except Exception as e:
            self.logger.warning(f"Failed to initialize pools: {e}")
    
    def _initialize_default_optimizations(self) -> None:
        """Initialize default optimization configurations."""
        default_optimizations = [
            OptimizationConfig(
                optimization_id="validation_caching",
                optimization_type=OptimizationType.CACHING,
                enabled=self.enable_caching,
                priority=1,
                cache_size=500,
                cache_ttl=1800,
                parameters={"strategy": "lru"}
            ),
            OptimizationConfig(
                optimization_id="analysis_parallelization",
                optimization_type=OptimizationType.PARALLELIZATION,
                enabled=self.enable_parallelization,
                priority=2,
                max_workers=self.max_workers,
                parameters={"chunk_size": 100}
            ),
            OptimizationConfig(
                optimization_id="memory_optimization",
                optimization_type=OptimizationType.MEMORY,
                enabled=True,
                priority=3,
                parameters={"gc_threshold": 1000}
            ),
            OptimizationConfig(
                optimization_id="algorithm_optimization",
                optimization_type=OptimizationType.ALGORITHM,
                enabled=True,
                priority=4,
                parameters={"timeout": 30}
            )
        ]
        
        for config in default_optimizations:
            self.register_optimization(config)
    
    def register_optimization(self, config: OptimizationConfig) -> ManagerResult[OptimizationConfig]:
        """Register an optimization configuration.
        
        Args:
            config: Optimization configuration
            
        Returns:
            Manager result with configuration
        """
        try:
            result = self.create(config.optimization_id, config)
            
            if result.success:
                self._optimizations[config.optimization_id] = config
                self.logger.debug(f"Registered optimization: {config.optimization_id}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error registering optimization {config.optimization_id}: {e}")
            return ManagerResult[OptimizationConfig](
                success=False,
                error_message=f"Failed to register optimization: {e}",
                data=None
            )
    
    def get_optimization(self, optimization_id: str) -> Optional[OptimizationConfig]:
        """Get optimization configuration.
        
        Args:
            optimization_id: Optimization identifier
            
        Returns:
            Optimization configuration or None
        """
        return self._optimizations.get(optimization_id)
    
    def enable_optimization(self, optimization_id: str) -> bool:
        """Enable an optimization.
        
        Args:
            optimization_id: Optimization identifier
            
        Returns:
            True if optimization was enabled
        """
        config = self._optimizations.get(optimization_id)
        if config:
            config.enabled = True
            self.update(optimization_id, config)
            self.logger.info(f"Enabled optimization: {optimization_id}")
            return True
        return False
    
    def disable_optimization(self, optimization_id: str) -> bool:
        """Disable an optimization.
        
        Args:
            optimization_id: Optimization identifier
            
        Returns:
            True if optimization was disabled
        """
        config = self._optimizations.get(optimization_id)
        if config:
            config.enabled = False
            self.update(optimization_id, config)
            self.logger.info(f"Disabled optimization: {optimization_id}")
            return True
        return False
    
    def optimize_function(
        self,
        func: Callable[..., T],
        optimization_type: OptimizationType,
        cache_key: Optional[str] = None,
        parallel: bool = False,
        **kwargs
    ) -> Callable[..., T]:
        """Apply optimizations to a function.
        
        Args:
            func: Function to optimize
            optimization_type: Type of optimization to apply
            cache_key: Optional cache key for caching optimization
            parallel: Whether to enable parallel execution
            **kwargs: Additional optimization parameters
            
        Returns:
            Optimized function
        """
        optimized_func = func
        
        # Apply caching optimization
        if optimization_type == OptimizationType.CACHING and self.enable_caching:
            optimized_func = self._apply_caching_optimization(optimized_func, cache_key)
        
        # Apply parallelization optimization
        if optimization_type == OptimizationType.PARALLELIZATION and parallel and self.enable_parallelization:
            optimized_func = self._apply_parallelization_optimization(optimized_func)
        
        # Apply memory optimization
        if optimization_type == OptimizationType.MEMORY:
            optimized_func = self._apply_memory_optimization(optimized_func)
        
        return optimized_func
    
    def _apply_caching_optimization(self, func: Callable[..., T], cache_key: Optional[str] = None) -> Callable[..., T]:
        """Apply caching optimization to a function.
        
        Args:
            func: Function to optimize
            cache_key: Optional cache key
            
        Returns:
            Cached function
        """
        @functools.wraps(func)
        def cached_func(*args, **kwargs):
            # Generate cache key
            key = cache_key or self._generate_cache_key(func, args, kwargs)
            
            # Check cache
            cached_result = self._get_cache(key)
            if cached_result is not None:
                self.logger.debug(f"Cache hit for function {func.__name__}")
                return cached_result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            self._set_cache(key, result)
            
            return result
        
        return cached_func
    
    def _apply_parallelization_optimization(self, func: Callable[..., T]) -> Callable[..., T]:
        """Apply parallelization optimization to a function.
        
        Args:
            func: Function to optimize
            
        Returns:
            Parallelized function
        """
        @functools.wraps(func)
        def parallel_func(*args, **kwargs):
            # Check if we have a thread pool
            if self._thread_pool is None:
                return func(*args, **kwargs)
            
            # Submit to thread pool
            future = self._thread_pool.submit(func, *args, **kwargs)
            return future.result()
        
        return parallel_func
    
    def _apply_memory_optimization(self, func: Callable[..., T]) -> Callable[..., T]:
        """Apply memory optimization to a function.
        
        Args:
            func: Function to optimize
            
        Returns:
            Memory-optimized function
        """
        @functools.wraps(func)
        def memory_optimized_func(*args, **kwargs):
            import gc
            
            # Collect garbage before execution
            gc.collect()
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Collect garbage after execution
            gc.collect()
            
            return result
        
        return memory_optimized_func
    
    def _generate_cache_key(self, func: Callable, args: tuple, kwargs: dict) -> str:
        """Generate cache key for function call.
        
        Args:
            func: Function
            args: Function arguments
            kwargs: Function keyword arguments
            
        Returns:
            Cache key
        """
        # Create key components
        key_components = [
            func.__name__,
            func.__module__,
            str(args),
            str(sorted(kwargs.items()))
        ]
        
        # Generate hash
        key_string = "|".join(key_components)
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    def _get_cache(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        try:
            # Check memory cache
            if key in self._cache:
                timestamp = self._cache_timestamps.get(key, 0)
                if time.time() - timestamp < 3600:  # 1 hour TTL
                    return self._cache[key]
                else:
                    # Remove expired cache entry
                    self._cache.pop(key, None)
                    self._cache_timestamps.pop(key, None)
            
            # Check disk cache
            cache_file = self.cache_dir / f"{key}.cache"
            if cache_file.exists():
                try:
                    with open(cache_file, 'rb') as f:
                        cached_data = pickle.load(f)
                    
                    # Check TTL
                    if time.time() - cached_data.get('timestamp', 0) < 3600:
                        # Load into memory cache
                        self._cache[key] = cached_data['value']
                        self._cache_timestamps[key] = cached_data['timestamp']
                        return cached_data['value']
                    else:
                        # Remove expired cache file
                        cache_file.unlink()
                except Exception as e:
                    self.logger.warning(f"Error loading cache file {key}: {e}")
                    cache_file.unlink()
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting cache for key {key}: {e}")
            return None
    
    def _set_cache(self, key: str, value: Any) -> None:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        try:
            # Store in memory cache
            self._cache[key] = value
            self._cache_timestamps[key] = time.time()
            
            # Store metadata
            self._cache_metadata[key] = {
                'size': len(pickle.dumps(value)),
                'created_at': time.time()
            }
            
            # Store in disk cache
            cache_file = self.cache_dir / f"{key}.cache"
            cached_data = {
                'value': value,
                'timestamp': time.time(),
                'metadata': self._cache_metadata[key]
            }
            
            with open(cache_file, 'wb') as f:
                pickle.dump(cached_data, f)
            
            # Clean up old cache entries if needed
            self._cleanup_cache()
            
        except Exception as e:
            self.logger.error(f"Error setting cache for key {key}: {e}")
    
    def _cleanup_cache(self) -> None:
        """Clean up old cache entries."""
        try:
            current_time = time.time()
            
            # Clean memory cache
            expired_keys = [
                key for key, timestamp in self._cache_timestamps.items()
                if current_time - timestamp > 3600  # 1 hour
            ]
            
            for key in expired_keys:
                self._cache.pop(key, None)
                self._cache_timestamps.pop(key, None)
                self._cache_metadata.pop(key, None)
            
            # Clean disk cache
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    if cache_file.stat().st_mtime < current_time - 3600:
                        cache_file.unlink()
                except Exception as e:
                    self.logger.warning(f"Error cleaning up cache file {cache_file}: {e}")
            
            if expired_keys:
                self.logger.debug(f"Cleaned up {len(expired_keys)} cache entries")
                
        except Exception as e:
            self.logger.error(f"Error during cache cleanup: {e}")
    
    def clear_cache(self) -> None:
        """Clear all cache entries."""
        try:
            # Clear memory cache
            self._cache.clear()
            self._cache_timestamps.clear()
            self._cache_metadata.clear()
            
            # Clear disk cache
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    cache_file.unlink()
                except Exception as e:
                    self.logger.warning(f"Error removing cache file {cache_file}: {e}")
            
            self.logger.info("Cache cleared")
            
        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Cache statistics dictionary
        """
        try:
            # Calculate memory cache stats
            memory_size = sum(
                metadata.get('size', 0) 
                for metadata in self._cache_metadata.values()
            )
            
            # Calculate disk cache stats
            disk_files = list(self.cache_dir.glob("*.cache"))
            disk_size = sum(f.stat().st_size for f in disk_files)
            
            return {
                'memory_entries': len(self._cache),
                'memory_size_mb': memory_size / (1024 * 1024),
                'disk_entries': len(disk_files),
                'disk_size_mb': disk_size / (1024 * 1024),
                'total_size_mb': (memory_size + disk_size) / (1024 * 1024),
                'cache_dir': str(self.cache_dir)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting cache stats: {e}")
            return {}
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Get comprehensive optimization report.
        
        Returns:
            Optimization report dictionary
        """
        return {
            'total_optimizations': len(self._optimizations),
            'active_optimizations': len([c for c in self._optimizations.values() if c.enabled]),
            'optimization_types': {
                opt_type.value: len([c for c in self._optimizations.values() if c.optimization_type == opt_type])
                for opt_type in OptimizationType
            },
            'cache_stats': self.get_cache_stats(),
            'pool_stats': {
                'max_workers': self.max_workers,
                'thread_pool_active': self._thread_pool is not None,
                'process_pool_active': self._process_pool is not None
            },
            'performance_history': len(self._performance_history),
            'optimization_results': len(self._optimization_results)
        }
    
    def _cleanup_item(self, key: str) -> None:
        """Clean up resources for an optimization configuration.
        
        Args:
            key: Optimization key to clean up
        """
        # Remove from optimizations dict
        self._optimizations.pop(key, None)
    
    def _clear_cache(self) -> None:
        """Clear cache after data changes."""
        super()._clear_cache()
    
    def __del__(self):
        """Cleanup when the manager is destroyed."""
        if self._thread_pool:
            self._thread_pool.shutdown(wait=True)
        if self._process_pool:
            self._process_pool.shutdown(wait=True) 