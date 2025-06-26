"""
Standardized optimization result structure.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

class OptimizationStrategy(Enum):
    """Optimization strategies."""
    GREEDY = "greedy"
    GENETIC = "genetic"
    SIMULATED_ANNEALING = "simulated_annealing"
    PARTICLE_SWARM = "particle_swarm"
    GRADIENT_DESCENT = "gradient_descent"
    EVOLUTIONARY = "evolutionary"
    CUSTOM = "custom"

class OptimizationType(Enum):
    """Types of optimization operations."""
    COMPONENT_PLACEMENT = "component_placement"
    ROUTING_OPTIMIZATION = "routing_optimization"
    POWER_DISTRIBUTION = "power_distribution"
    GROUND_PLANE = "ground_plane"
    THERMAL_OPTIMIZATION = "thermal_optimization"
    EMI_EMC_OPTIMIZATION = "emi_emc_optimization"
    SIGNAL_INTEGRITY = "signal_integrity"
    COST_OPTIMIZATION = "cost_optimization"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    CUSTOM = "custom"

class OptimizationStatus(Enum):
    """Optimization status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    CONVERGED = "converged"

@dataclass
class OptimizationResult:
    """Standardized result of an optimization operation."""
    success: bool
    optimization_type: OptimizationType = OptimizationType.CUSTOM
    strategy: OptimizationStrategy = OptimizationStrategy.GREEDY
    status: OptimizationStatus = OptimizationStatus.COMPLETED
    message: str = ""
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    optimized_target: Optional[Any] = None
    original_target: Optional[Any] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    iterations: int = 0
    improvement_score: float = 0.0
    convergence_reached: bool = False
    optimization_duration: Optional[float] = None
    target_id: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)
    convergence_history: List[float] = field(default_factory=list)
    
    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
        if self.status == OptimizationStatus.RUNNING:
            self.status = OptimizationStatus.FAILED
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)
    
    def add_recommendation(self, recommendation: str) -> None:
        """Add a recommendation."""
        self.recommendations.append(recommendation)
    
    def set_metric(self, key: str, value: Any) -> None:
        """Set a metric value."""
        self.metrics[key] = value
    
    def get_metric(self, key: str, default: Any = None) -> Any:
        """Get a metric value."""
        return self.metrics.get(key, default)
    
    def add_convergence_point(self, score: float) -> None:
        """Add a convergence history point."""
        self.convergence_history.append(score)
    
    def has_errors(self) -> bool:
        """Check if the result has errors."""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if the result has warnings."""
        return len(self.warnings) > 0
    
    def is_converged(self) -> bool:
        """Check if optimization converged."""
        return self.convergence_reached or self.status == OptimizationStatus.CONVERGED
    
    def get_improvement_percentage(self) -> float:
        """Get improvement as percentage."""
        return self.improvement_score * 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'success': self.success,
            'optimization_type': self.optimization_type.value,
            'strategy': self.strategy.value,
            'status': self.status.value,
            'message': self.message,
            'errors': self.errors,
            'warnings': self.warnings,
            'timestamp': self.timestamp.isoformat(),
            'optimized_target': self.optimized_target,
            'original_target': self.original_target,
            'metrics': self.metrics,
            'iterations': self.iterations,
            'improvement_score': self.improvement_score,
            'convergence_reached': self.convergence_reached,
            'optimization_duration': self.optimization_duration,
            'target_id': self.target_id,
            'recommendations': self.recommendations,
            'convergence_history': self.convergence_history
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OptimizationResult':
        """Create result from dictionary."""
        return cls(
            success=data.get('success', False),
            optimization_type=OptimizationType(data.get('optimization_type', 'custom')),
            strategy=OptimizationStrategy(data.get('strategy', 'greedy')),
            status=OptimizationStatus(data.get('status', 'completed')),
            message=data.get('message', ''),
            errors=data.get('errors', []),
            warnings=data.get('warnings', []),
            timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
            optimized_target=data.get('optimized_target'),
            original_target=data.get('original_target'),
            metrics=data.get('metrics', {}),
            iterations=data.get('iterations', 0),
            improvement_score=data.get('improvement_score', 0.0),
            convergence_reached=data.get('convergence_reached', False),
            optimization_duration=data.get('optimization_duration'),
            target_id=data.get('target_id'),
            recommendations=data.get('recommendations', []),
            convergence_history=data.get('convergence_history', [])
        ) 
