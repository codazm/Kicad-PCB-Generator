"""Performance management system for the KiCad PCB Generator."""

import logging
import time
import psutil
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import json
import os
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from pathlib import Path

from ..base.base_manager import BaseManager
from ..base.results.manager_result import ManagerResult, ManagerOperation, ManagerStatus

@dataclass
class PerformanceMetrics:
    """Performance metrics for a component or operation."""
    component_id: str
    operation: str
    execution_time: float
    memory_usage: float
    cpu_usage: float
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class PerformanceReport:
    """Performance report for a component or system."""
    component_id: str
    start_time: datetime
    end_time: datetime
    metrics: List[PerformanceMetrics]
    summary: Dict[str, float]
    recommendations: List[str]

class PerformanceSeverity(Enum):
    """Severity levels for performance issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class PerformanceManager(BaseManager[PerformanceMetrics]):
    """Manages performance monitoring and optimization for the KiCad PCB Generator.
    
    Now inherits from BaseManager for standardized CRUD operations on PerformanceMetrics objects.
    """
    
    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        max_workers: int = 4,
        metrics_dir: str = "performance_metrics"
    ):
        """Initialize the performance manager.
        
        Args:
            logger: Optional logger instance
            max_workers: Maximum number of worker threads
            metrics_dir: Directory to store performance metrics
        """
        super().__init__()
        self.logger = logger or logging.getLogger(__name__)
        self.max_workers = max_workers
        self.metrics_dir = Path(metrics_dir)
        
        # Initialize thread pool
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Initialize reports storage
        self._reports: Dict[str, PerformanceReport] = {}
        
        # Initialize monitoring
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        
        # Create metrics directory if it doesn't exist
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        # Performance thresholds
        self.thresholds = {
            'execution_time': {
                'warning': 1.0,  # seconds
                'error': 5.0,
                'critical': 10.0
            },
            'memory_usage': {
                'warning': 100 * 1024 * 1024,  # 100MB
                'error': 500 * 1024 * 1024,    # 500MB
                'critical': 1024 * 1024 * 1024  # 1GB
            },
            'cpu_usage': {
                'warning': 50.0,  # percentage
                'error': 80.0,
                'critical': 95.0
            }
        }
    
    def start_monitoring(self, interval: float = 1.0) -> None:
        """Start performance monitoring.
        
        Args:
            interval: Monitoring interval in seconds
        """
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_performance,
            args=(interval,),
            daemon=True
        )
        self._monitor_thread.start()
    
    def stop_monitoring(self) -> None:
        """Stop performance monitoring."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join()
            self._monitor_thread = None
    
    def _monitor_performance(self, interval: float) -> None:
        """Monitor system performance.
        
        Args:
            interval: Monitoring interval in seconds
        """
        process = psutil.Process()
        
        while self._monitoring:
            try:
                # Collect system metrics
                metrics = PerformanceMetrics(
                    component_id="system",
                    operation="monitoring",
                    execution_time=0.0,
                    memory_usage=process.memory_info().rss,
                    cpu_usage=process.cpu_percent(),
                    timestamp=datetime.now(),
                    metadata={}
                )
                
                # Store metrics using BaseManager
                self._store_metrics(metrics)
                
                # Check thresholds
                self._check_thresholds(metrics)
                
                time.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Error in performance monitoring: {str(e)}")
    
    def _check_thresholds(self, metrics: PerformanceMetrics) -> None:
        """Check performance metrics against thresholds.
        
        Args:
            metrics: Performance metrics to check
        """
        # Check execution time
        if metrics.execution_time > self.thresholds['execution_time']['critical']:
            self._log_performance_issue(
                metrics,
                PerformanceSeverity.CRITICAL,
                "Execution time exceeds critical threshold"
            )
        elif metrics.execution_time > self.thresholds['execution_time']['error']:
            self._log_performance_issue(
                metrics,
                PerformanceSeverity.ERROR,
                "Execution time exceeds error threshold"
            )
        elif metrics.execution_time > self.thresholds['execution_time']['warning']:
            self._log_performance_issue(
                metrics,
                PerformanceSeverity.WARNING,
                "Execution time exceeds warning threshold"
            )
        
        # Check memory usage
        if metrics.memory_usage > self.thresholds['memory_usage']['critical']:
            self._log_performance_issue(
                metrics,
                PerformanceSeverity.CRITICAL,
                "Memory usage exceeds critical threshold"
            )
        elif metrics.memory_usage > self.thresholds['memory_usage']['error']:
            self._log_performance_issue(
                metrics,
                PerformanceSeverity.ERROR,
                "Memory usage exceeds error threshold"
            )
        elif metrics.memory_usage > self.thresholds['memory_usage']['warning']:
            self._log_performance_issue(
                metrics,
                PerformanceSeverity.WARNING,
                "Memory usage exceeds warning threshold"
            )
        
        # Check CPU usage
        if metrics.cpu_usage > self.thresholds['cpu_usage']['critical']:
            self._log_performance_issue(
                metrics,
                PerformanceSeverity.CRITICAL,
                "CPU usage exceeds critical threshold"
            )
        elif metrics.cpu_usage > self.thresholds['cpu_usage']['error']:
            self._log_performance_issue(
                metrics,
                PerformanceSeverity.ERROR,
                "CPU usage exceeds error threshold"
            )
        elif metrics.cpu_usage > self.thresholds['cpu_usage']['warning']:
            self._log_performance_issue(
                metrics,
                PerformanceSeverity.WARNING,
                "CPU usage exceeds warning threshold"
            )
    
    def _log_performance_issue(
        self,
        metrics: PerformanceMetrics,
        severity: PerformanceSeverity,
        message: str
    ) -> None:
        """Log a performance issue.
        
        Args:
            metrics: Performance metrics
            severity: Issue severity
            message: Issue message
        """
        log_message = (
            f"Performance {severity.value}: {message} - "
            f"Component: {metrics.component_id}, "
            f"Operation: {metrics.operation}, "
            f"Execution Time: {metrics.execution_time:.2f}s, "
            f"Memory: {metrics.memory_usage / (1024 * 1024):.2f}MB, "
            f"CPU: {metrics.cpu_usage:.1f}%"
        )
        
        if severity == PerformanceSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif severity == PerformanceSeverity.ERROR:
            self.logger.error(log_message)
        elif severity == PerformanceSeverity.WARNING:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
    
    def measure_performance(
        self,
        component_id: str,
        operation: str,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Measure performance of a function.
        
        Args:
            component_id: Component identifier
            operation: Operation name
            func: Function to measure
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
        """
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        start_cpu = psutil.Process().cpu_percent()
        
        try:
            result = func(*args, **kwargs)
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss
            end_cpu = psutil.Process().cpu_percent()
            
            # Calculate metrics
            execution_time = end_time - start_time
            memory_usage = end_memory - start_memory
            cpu_usage = (start_cpu + end_cpu) / 2
            
            # Create metrics object
            metrics = PerformanceMetrics(
                component_id=component_id,
                operation=operation,
                execution_time=execution_time,
                memory_usage=memory_usage,
                cpu_usage=cpu_usage,
                timestamp=datetime.now(),
                metadata={
                    'function_name': func.__name__,
                    'args': str(args),
                    'kwargs': str(kwargs)
                }
            )
            
            # Store metrics using BaseManager
            self._store_metrics(metrics)
            
            return result
            
        except Exception as e:
            # Log error metrics
            end_time = time.time()
            execution_time = end_time - start_time
            
            error_metrics = PerformanceMetrics(
                component_id=component_id,
                operation=f"{operation}_error",
                execution_time=execution_time,
                memory_usage=0.0,
                cpu_usage=0.0,
                timestamp=datetime.now(),
                metadata={
                    'function_name': func.__name__,
                    'error': str(e),
                    'args': str(args),
                    'kwargs': str(kwargs)
                }
            )
            
            self._store_metrics(error_metrics)
            raise
    
    def _store_metrics(self, metrics: PerformanceMetrics) -> None:
        """Store performance metrics.
        
        Args:
            metrics: Performance metrics to store
        """
        try:
            # Use BaseManager's create method with composite key
            key = f"{metrics.component_id}:{metrics.operation}:{metrics.timestamp.isoformat()}"
            result = self.create(key, metrics)
            
            if result.success:
                # Save to disk
                self._save_metrics(metrics)
            else:
                self.logger.error(f"Failed to store metrics: {result.message}")
                
        except Exception as e:
            self.logger.error(f"Error storing metrics: {e}")
    
    def _save_metrics(self, metrics: PerformanceMetrics) -> None:
        """Save metrics to disk.
        
        Args:
            metrics: Metrics to save
        """
        try:
            # Create component directory
            component_dir = self.metrics_dir / metrics.component_id
            component_dir.mkdir(parents=True, exist_ok=True)
            
            # Create filename with timestamp
            timestamp_str = metrics.timestamp.strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{metrics.operation}_{timestamp_str}.json"
            filepath = component_dir / filename
            
            # Convert to dict for JSON serialization
            metrics_data = {
                'component_id': metrics.component_id,
                'operation': metrics.operation,
                'execution_time': metrics.execution_time,
                'memory_usage': metrics.memory_usage,
                'cpu_usage': metrics.cpu_usage,
                'timestamp': metrics.timestamp.isoformat(),
                'metadata': metrics.metadata
            }
            
            with open(filepath, 'w') as f:
                json.dump(metrics_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving metrics to disk: {e}")
    
    def get_metrics(
        self,
        component_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[PerformanceMetrics]:
        """Get performance metrics.
        
        Args:
            component_id: Optional component ID to filter by
            start_time: Optional start time to filter by
            end_time: Optional end time to filter by
            
        Returns:
            List of performance metrics
        """
        result = self.list_all()
        if not result.success:
            return []
        
        metrics = result.data
        
        # Filter by component ID
        if component_id:
            metrics = [m for m in metrics if m.component_id == component_id]
        
        # Filter by time range
        if start_time:
            metrics = [m for m in metrics if m.timestamp >= start_time]
        
        if end_time:
            metrics = [m for m in metrics if m.timestamp <= end_time]
        
        # Sort by timestamp
        return sorted(metrics, key=lambda m: m.timestamp)
    
    def generate_report(
        self,
        component_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> PerformanceReport:
        """Generate a performance report.
        
        Args:
            component_id: Component ID
            start_time: Optional start time
            end_time: Optional end time
            
        Returns:
            Performance report
        """
        metrics = self.get_metrics(component_id, start_time, end_time)
        
        if not metrics:
            return PerformanceReport(
                component_id=component_id,
                start_time=start_time or datetime.now(),
                end_time=end_time or datetime.now(),
                metrics=[],
                summary={},
                recommendations=[]
            )
        
        # Calculate summary statistics
        execution_times = [m.execution_time for m in metrics]
        memory_usages = [m.memory_usage for m in metrics]
        cpu_usages = [m.cpu_usage for m in metrics]
        
        summary = {
            'total_operations': len(metrics),
            'avg_execution_time': sum(execution_times) / len(execution_times),
            'max_execution_time': max(execution_times),
            'min_execution_time': min(execution_times),
            'avg_memory_usage': sum(memory_usages) / len(memory_usages),
            'max_memory_usage': max(memory_usages),
            'min_memory_usage': min(memory_usages),
            'avg_cpu_usage': sum(cpu_usages) / len(cpu_usages),
            'max_cpu_usage': max(cpu_usages),
            'min_cpu_usage': min(cpu_usages)
        }
        
        # Generate recommendations
        recommendations = self._generate_recommendations(metrics, summary)
        
        return PerformanceReport(
            component_id=component_id,
            start_time=start_time or min(m.timestamp for m in metrics),
            end_time=end_time or max(m.timestamp for m in metrics),
            metrics=metrics,
            summary=summary,
            recommendations=recommendations
        )
    
    def _generate_recommendations(
        self,
        metrics: List[PerformanceMetrics],
        summary: Dict[str, float]
    ) -> List[str]:
        """Generate performance recommendations.
        
        Args:
            metrics: Performance metrics
            summary: Summary statistics
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Check execution time
        if summary['avg_execution_time'] > self.thresholds['execution_time']['warning']:
            recommendations.append(
                f"Average execution time ({summary['avg_execution_time']:.2f}s) "
                f"exceeds warning threshold. Consider optimization."
            )
        
        if summary['max_execution_time'] > self.thresholds['execution_time']['error']:
            recommendations.append(
                f"Maximum execution time ({summary['max_execution_time']:.2f}s) "
                f"exceeds error threshold. Investigate performance bottlenecks."
            )
        
        # Check memory usage
        if summary['avg_memory_usage'] > self.thresholds['memory_usage']['warning']:
            recommendations.append(
                f"Average memory usage ({summary['avg_memory_usage'] / (1024 * 1024):.2f}MB) "
                f"exceeds warning threshold. Consider memory optimization."
            )
        
        if summary['max_memory_usage'] > self.thresholds['memory_usage']['error']:
            recommendations.append(
                f"Maximum memory usage ({summary['max_memory_usage'] / (1024 * 1024):.2f}MB) "
                f"exceeds error threshold. Investigate memory leaks."
            )
        
        # Check CPU usage
        if summary['avg_cpu_usage'] > self.thresholds['cpu_usage']['warning']:
            recommendations.append(
                f"Average CPU usage ({summary['avg_cpu_usage']:.1f}%) "
                f"exceeds warning threshold. Consider CPU optimization."
            )
        
        if summary['max_cpu_usage'] > self.thresholds['cpu_usage']['error']:
            recommendations.append(
                f"Maximum CPU usage ({summary['max_cpu_usage']:.1f}%) "
                f"exceeds error threshold. Investigate CPU bottlenecks."
            )
        
        # General recommendations
        if len(metrics) < 10:
            recommendations.append(
                "Limited performance data available. Collect more metrics for better analysis."
            )
        
        if not recommendations:
            recommendations.append("Performance is within acceptable thresholds.")
        
        return recommendations
    
    def clear_metrics(self, component_id: Optional[str] = None) -> None:
        """Clear performance metrics.
        
        Args:
            component_id: Optional component ID to clear metrics for
        """
        if component_id:
            # Clear specific component metrics
            keys_to_delete = []
            for key in self._items.keys():
                if key.startswith(f"{component_id}:"):
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                self.delete(key)
        else:
            # Clear all metrics
            self.clear_all()
    
    def clear_reports(self, component_id: Optional[str] = None) -> None:
        """Clear performance reports.
        
        Args:
            component_id: Optional component ID to clear reports for
        """
        if component_id:
            # Clear specific component reports
            keys_to_delete = [k for k in self._reports.keys() if k.startswith(component_id)]
            for key in keys_to_delete:
                del self._reports[key]
        else:
            # Clear all reports
            self._reports.clear()
    
    def _validate_data(self, data: PerformanceMetrics) -> ManagerResult:
        """Validate data before storage.
        
        Args:
            data: Data to validate
            
        Returns:
            Validation result
        """
        try:
            if not data.component_id:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Component ID is required",
                    errors=["Component ID cannot be empty"]
                )
            
            if not data.operation:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Operation is required",
                    errors=["Operation cannot be empty"]
                )
            
            if data.execution_time < 0:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Execution time cannot be negative",
                    errors=["Execution time must be non-negative"]
                )
            
            if data.memory_usage < 0:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Memory usage cannot be negative",
                    errors=["Memory usage must be non-negative"]
                )
            
            if data.cpu_usage < 0 or data.cpu_usage > 100:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="CPU usage must be between 0 and 100",
                    errors=["CPU usage must be between 0 and 100 percent"]
                )
            
            if not data.timestamp:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Timestamp is required",
                    errors=["Timestamp cannot be empty"]
                )
            
            return ManagerResult(
                success=True,
                operation=ManagerOperation.VALIDATE,
                status=ManagerStatus.SUCCESS,
                message="Performance metrics validation successful"
            )
        except Exception as e:
            return ManagerResult(
                success=False,
                operation=ManagerOperation.VALIDATE,
                status=ManagerStatus.FAILED,
                message=f"Performance metrics validation failed: {e}",
                errors=[str(e)]
            )
    
    def _cleanup_item(self, key: str) -> None:
        """Clean up resources for performance metrics.
        
        Args:
            key: Performance metrics key to clean up
        """
        # Remove from disk if it exists
        try:
            component_id, operation, timestamp_str = key.split(':', 2)
            component_dir = self.metrics_dir / component_id
            timestamp = datetime.fromisoformat(timestamp_str)
            timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{operation}_{timestamp_str}.json"
            filepath = component_dir / filename
            
            if filepath.exists():
                filepath.unlink()
        except Exception as e:
            self.logger.error(f"Error cleaning up metrics file: {e}")
    
    def _clear_cache(self) -> None:
        """Clear cache after data changes."""
        # Clear the cache - no additional disk operations needed
        super()._clear_cache()
    
    def __del__(self):
        """Cleanup when the manager is destroyed."""
        self.stop_monitoring()
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True) 