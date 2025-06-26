"""Memory optimization and management system for the KiCad PCB Generator."""

import gc
import psutil
import threading
import time
import weakref
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging
import sys
import tracemalloc
from pathlib import Path
import json

from ..base.base_manager import BaseManager
from ..base.results.manager_result import ManagerResult, ManagerOperation, ManagerStatus


class MemorySeverity(Enum):
    """Memory issue severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class MemoryMetrics:
    """Memory usage metrics for a component or operation."""
    component_id: str
    operation: str
    memory_usage: int  # bytes
    memory_peak: int   # peak memory usage
    object_count: int  # number of objects
    gc_collections: int  # garbage collection count
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryLeak:
    """Memory leak detection result."""
    component_id: str
    operation: str
    memory_increase: int  # bytes
    object_increase: int  # number of objects
    duration: float  # seconds
    severity: MemorySeverity
    timestamp: datetime
    details: str
    recommendations: List[str] = field(default_factory=list)


class MemoryOptimizer(BaseManager[MemoryMetrics]):
    """Advanced memory optimization and leak detection system.
    
    Provides memory monitoring, optimization, and leak detection capabilities
    for the KiCad PCB Generator.
    """
    
    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        enable_tracemalloc: bool = True,
        memory_threshold: int = 100 * 1024 * 1024,  # 100MB
        leak_threshold: int = 10 * 1024 * 1024,     # 10MB
        gc_threshold: int = 1000  # objects
    ):
        """Initialize the memory optimizer.
        
        Args:
            logger: Optional logger instance
            enable_tracemalloc: Enable tracemalloc for detailed memory tracking
            memory_threshold: Memory usage threshold for warnings
            leak_threshold: Memory leak detection threshold
            gc_threshold: Garbage collection threshold
        """
        super().__init__()
        self.logger = logger or logging.getLogger(__name__)
        self.memory_threshold = memory_threshold
        self.leak_threshold = leak_threshold
        self.gc_threshold = gc_threshold
        
        # Initialize tracemalloc if enabled
        self.tracemalloc_enabled = enable_tracemalloc
        if enable_tracemalloc:
            tracemalloc.start()
            self.logger.info("Tracemalloc enabled for detailed memory tracking")
        
        # Memory monitoring state
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._baseline_memory: Optional[int] = None
        self._baseline_objects: Optional[int] = None
        
        # Memory leak detection
        self._memory_history: List[MemoryMetrics] = []
        self._leak_detections: List[MemoryLeak] = []
        self._object_refs: Dict[str, weakref.ref] = {}
        
        # Performance optimization settings
        self.gc_settings = {
            'threshold0': 700,   # Generation 0 threshold
            'threshold1': 10,    # Generation 1 threshold  
            'threshold2': 10     # Generation 2 threshold
        }
        
        # Initialize optimized garbage collection
        self._optimize_gc()
        
        self.logger.info("Memory optimizer initialized")
    
    def _optimize_gc(self) -> None:
        """Optimize garbage collection settings."""
        try:
            # Set optimized GC thresholds
            gc.set_threshold(
                self.gc_settings['threshold0'],
                self.gc_settings['threshold1'],
                self.gc_settings['threshold2']
            )
            
            # Enable debug flags for better memory tracking
            gc.set_debug(gc.DEBUG_STATS | gc.DEBUG_LEAK)
            
            self.logger.debug("Garbage collection optimized")
        except Exception as e:
            self.logger.warning(f"Failed to optimize garbage collection: {e}")
    
    def start_monitoring(self, interval: float = 5.0) -> None:
        """Start memory monitoring.
        
        Args:
            interval: Monitoring interval in seconds
        """
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_memory,
            args=(interval,),
            daemon=True
        )
        self._monitor_thread.start()
        
        # Set baseline
        self._set_baseline()
        
        self.logger.info("Memory monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop memory monitoring."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join()
            self._monitor_thread = None
        
        self.logger.info("Memory monitoring stopped")
    
    def _set_baseline(self) -> None:
        """Set baseline memory usage."""
        process = psutil.Process()
        self._baseline_memory = process.memory_info().rss
        self._baseline_objects = len(gc.get_objects())
        
        self.logger.debug(f"Memory baseline set: {self._baseline_memory / (1024*1024):.2f}MB")
    
    def _monitor_memory(self, interval: float) -> None:
        """Monitor memory usage.
        
        Args:
            interval: Monitoring interval in seconds
        """
        process = psutil.Process()
        
        while self._monitoring:
            try:
                # Collect current memory metrics
                current_memory = process.memory_info().rss
                current_objects = len(gc.get_objects())
                gc_collections = gc.get_count()
                
                # Create metrics
                metrics = MemoryMetrics(
                    component_id="system",
                    operation="monitoring",
                    memory_usage=current_memory,
                    memory_peak=process.memory_info().rss,
                    object_count=current_objects,
                    gc_collections=sum(gc_collections),
                    timestamp=datetime.now(),
                    metadata={
                        'gc_generation0': gc_collections[0],
                        'gc_generation1': gc_collections[1],
                        'gc_generation2': gc_collections[2]
                    }
                )
                
                # Store metrics
                self._store_metrics(metrics)
                
                # Check for memory issues
                self._check_memory_issues(metrics)
                
                # Check for memory leaks
                self._detect_memory_leaks(metrics)
                
                time.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Error in memory monitoring: {e}")
    
    def _check_memory_issues(self, metrics: MemoryMetrics) -> None:
        """Check for memory usage issues.
        
        Args:
            metrics: Current memory metrics
        """
        # Check memory threshold
        if metrics.memory_usage > self.memory_threshold:
            self._log_memory_issue(
                metrics,
                MemorySeverity.WARNING,
                f"Memory usage ({metrics.memory_usage / (1024*1024):.2f}MB) exceeds threshold"
            )
        
        # Check object count threshold
        if metrics.object_count > self.gc_threshold:
            self._log_memory_issue(
                metrics,
                MemorySeverity.WARNING,
                f"Object count ({metrics.object_count}) exceeds threshold"
            )
        
        # Check for memory growth
        if self._baseline_memory:
            memory_increase = metrics.memory_usage - self._baseline_memory
            if memory_increase > self.leak_threshold:
                self._log_memory_issue(
                    metrics,
                    MemorySeverity.ERROR,
                    f"Memory increase ({memory_increase / (1024*1024):.2f}MB) exceeds leak threshold"
                )
    
    def _detect_memory_leaks(self, metrics: MemoryMetrics) -> None:
        """Detect potential memory leaks.
        
        Args:
            metrics: Current memory metrics
        """
        if len(self._memory_history) < 2:
            self._memory_history.append(metrics)
            return
        
        # Compare with previous measurement
        prev_metrics = self._memory_history[-1]
        memory_increase = metrics.memory_usage - prev_metrics.memory_usage
        object_increase = metrics.object_count - prev_metrics.object_count
        time_diff = (metrics.timestamp - prev_metrics.timestamp).total_seconds()
        
        # Check for sustained memory growth
        if memory_increase > self.leak_threshold and time_diff > 30:  # 30 seconds
            leak = MemoryLeak(
                component_id=metrics.component_id,
                operation=metrics.operation,
                memory_increase=memory_increase,
                object_increase=object_increase,
                duration=time_diff,
                severity=MemorySeverity.WARNING,
                timestamp=metrics.timestamp,
                details=f"Memory increased by {memory_increase / (1024*1024):.2f}MB over {time_diff:.1f}s",
                recommendations=[
                    "Check for circular references",
                    "Review object lifecycle management",
                    "Consider explicit garbage collection"
                ]
            )
            
            self._leak_detections.append(leak)
            self.logger.warning(f"Potential memory leak detected: {leak.details}")
        
        self._memory_history.append(metrics)
        
        # Keep only recent history
        if len(self._memory_history) > 100:
            self._memory_history = self._memory_history[-50:]
    
    def _log_memory_issue(
        self,
        metrics: MemoryMetrics,
        severity: MemorySeverity,
        message: str
    ) -> None:
        """Log memory issue.
        
        Args:
            metrics: Memory metrics
            severity: Issue severity
            message: Issue message
        """
        log_message = f"Memory {severity.value}: {message}"
        
        if severity == MemorySeverity.CRITICAL:
            self.logger.critical(log_message)
        elif severity == MemorySeverity.ERROR:
            self.logger.error(log_message)
        elif severity == MemorySeverity.WARNING:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
    
    def measure_memory(
        self,
        component_id: str,
        operation: str,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Measure memory usage of a function.
        
        Args:
            component_id: Component identifier
            operation: Operation name
            func: Function to measure
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
        """
        process = psutil.Process()
        
        # Collect garbage before measurement
        gc.collect()
        
        # Measure memory before
        memory_before = process.memory_info().rss
        objects_before = len(gc.get_objects())
        gc_before = gc.get_count()
        
        try:
            result = func(*args, **kwargs)
            
            # Measure memory after
            memory_after = process.memory_info().rss
            objects_after = len(gc.get_objects())
            gc_after = gc.get_count()
            
            # Create metrics
            metrics = MemoryMetrics(
                component_id=component_id,
                operation=operation,
                memory_usage=memory_after - memory_before,
                memory_peak=memory_after,
                object_count=objects_after - objects_before,
                gc_collections=sum(gc_after) - sum(gc_before),
                timestamp=datetime.now(),
                metadata={
                    'function_name': func.__name__,
                    'memory_before': memory_before,
                    'memory_after': memory_after,
                    'objects_before': objects_before,
                    'objects_after': objects_after
                }
            )
            
            # Store metrics
            self._store_metrics(metrics)
            
            return result
            
        except Exception as e:
            # Log error metrics
            memory_after = process.memory_info().rss
            objects_after = len(gc.get_objects())
            
            error_metrics = MemoryMetrics(
                component_id=component_id,
                operation=f"{operation}_error",
                memory_usage=memory_after - memory_before,
                memory_peak=memory_after,
                object_count=objects_after - objects_before,
                gc_collections=0,
                timestamp=datetime.now(),
                metadata={
                    'function_name': func.__name__,
                    'error': str(e),
                    'memory_before': memory_before,
                    'memory_after': memory_after
                }
            )
            
            self._store_metrics(error_metrics)
            raise
    
    def optimize_memory(self) -> None:
        """Perform memory optimization."""
        try:
            # Force garbage collection
            collected = gc.collect()
            self.logger.info(f"Garbage collection collected {collected} objects")
            
            # Clear memory caches
            self._clear_memory_caches()
            
            # Optimize object references
            self._optimize_references()
            
            self.logger.info("Memory optimization completed")
            
        except Exception as e:
            self.logger.error(f"Error during memory optimization: {e}")
    
    def _clear_memory_caches(self) -> None:
        """Clear memory caches."""
        # Clear internal caches
        self._clear_cache()
        
        # Clear weak references
        self._object_refs.clear()
        
        # Clear memory history (keep recent)
        if len(self._memory_history) > 10:
            self._memory_history = self._memory_history[-10:]
        
        self.logger.debug("Memory caches cleared")
    
    def _optimize_references(self) -> None:
        """Optimize object references."""
        # Remove dead weak references
        dead_refs = []
        for key, ref in self._object_refs.items():
            if ref() is None:
                dead_refs.append(key)
        
        for key in dead_refs:
            del self._object_refs[key]
        
        if dead_refs:
            self.logger.debug(f"Removed {len(dead_refs)} dead references")
    
    def get_memory_report(self) -> Dict[str, Any]:
        """Get comprehensive memory report.
        
        Returns:
            Memory report dictionary
        """
        process = psutil.Process()
        current_memory = process.memory_info().rss
        current_objects = len(gc.get_objects())
        gc_stats = gc.get_stats()
        
        # Calculate memory growth
        memory_growth = 0
        if self._baseline_memory:
            memory_growth = current_memory - self._baseline_memory
        
        # Get tracemalloc statistics if enabled
        tracemalloc_stats = None
        if self.tracemalloc_enabled:
            try:
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc_stats = {
                    'current_memory': current,
                    'peak_memory': peak,
                    'current_memory_mb': current / (1024 * 1024),
                    'peak_memory_mb': peak / (1024 * 1024)
                }
            except Exception as e:
                self.logger.warning(f"Failed to get tracemalloc stats: {e}")
        
        return {
            'current_memory_mb': current_memory / (1024 * 1024),
            'current_objects': current_objects,
            'memory_growth_mb': memory_growth / (1024 * 1024),
            'baseline_memory_mb': self._baseline_memory / (1024 * 1024) if self._baseline_memory else 0,
            'gc_stats': gc_stats,
            'tracemalloc_stats': tracemalloc_stats,
            'leak_detections': len(self._leak_detections),
            'memory_threshold_mb': self.memory_threshold / (1024 * 1024),
            'leak_threshold_mb': self.leak_threshold / (1024 * 1024),
            'gc_threshold': self.gc_threshold,
            'monitoring_active': self._monitoring
        }
    
    def _store_metrics(self, metrics: MemoryMetrics) -> None:
        """Store memory metrics.
        
        Args:
            metrics: Memory metrics to store
        """
        try:
            # Use BaseManager's create method with composite key
            key = f"{metrics.component_id}:{metrics.operation}:{metrics.timestamp.isoformat()}"
            result = self.create(key, metrics)
            
            if not result.success:
                self.logger.error(f"Failed to store memory metrics: {result.message}")
                
        except Exception as e:
            self.logger.error(f"Error storing memory metrics: {e}")
    
    def _cleanup_item(self, key: str) -> None:
        """Clean up resources for memory metrics.
        
        Args:
            key: Memory metrics key to clean up
        """
        # No specific cleanup needed for memory metrics
        pass
    
    def _clear_cache(self) -> None:
        """Clear cache after data changes."""
        super()._clear_cache()
    
    def __del__(self):
        """Cleanup when the optimizer is destroyed."""
        self.stop_monitoring()
        if self.tracemalloc_enabled:
            tracemalloc.stop() 