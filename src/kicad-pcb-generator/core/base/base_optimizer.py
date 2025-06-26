"""
Base optimizer class for standardizing optimization operations.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TypeVar, Generic, Tuple
import logging
from datetime import datetime

from .results.optimization_result import OptimizationResult, OptimizationStrategy, OptimizationType, OptimizationStatus

logger = logging.getLogger(__name__)

T = TypeVar('T')

class BaseOptimizer(ABC, Generic[T]):
    """Base class for all optimizer classes."""
    
    def __init__(self, name: str = ""):
        """Initialize the base optimizer.
        
        Args:
            name: Name of the optimizer
        """
        self.name = name or self.__class__.__name__
        self._cache: Dict[str, Any] = {}
        self._optimization_history: List[OptimizationResult] = []
        self._enabled_optimizations: Dict[str, bool] = {}
        self._strategies: Dict[str, OptimizationStrategy] = {}
        self._max_iterations: int = 1000
        self._convergence_threshold: float = 0.001
        
    def optimize(self, target: T, optimization_type: OptimizationType = OptimizationType.CUSTOM, 
                strategy: OptimizationStrategy = OptimizationStrategy.GREEDY,
                max_iterations: Optional[int] = None) -> OptimizationResult:
        """Perform optimization on a target.
        
        Args:
            target: Target to optimize
            optimization_type: Type of optimization to perform
            strategy: Optimization strategy to use
            max_iterations: Maximum number of iterations
            
        Returns:
            Optimization result
        """
        try:
            # Check if optimization is enabled
            if not self._enabled_optimizations.get(optimization_type.value, True):
                return OptimizationResult(
                    success=False,
                    optimization_type=optimization_type,
                    strategy=strategy,
                    message=f"Optimization type '{optimization_type.value}' is disabled"
                )
            
            # Validate target
            validation_result = self._validate_target(target)
            if not validation_result.success:
                return validation_result
            
            # Set iteration limit
            iterations = max_iterations or self._max_iterations
            
            # Perform optimization
            result = self._perform_optimization(target, optimization_type, strategy, iterations)
            
            # Store in history
            self._optimization_history.append(result)
            
            # Clear cache if needed
            if result.success:
                self._clear_cache()
            
            logger.info(f"Optimization '{optimization_type.value}' completed for {self.name}")
            return result
            
        except Exception as e:
            logger.error(f"Error during optimization '{optimization_type.value}' in {self.name}: {e}")
            result = OptimizationResult(
                success=False,
                optimization_type=optimization_type,
                strategy=strategy,
                message=f"Error during optimization: {e}",
                errors=[str(e)]
            )
            self._optimization_history.append(result)
            return result
    
    def batch_optimize(self, targets: List[T], optimization_type: OptimizationType = OptimizationType.CUSTOM,
                      strategy: OptimizationStrategy = OptimizationStrategy.GREEDY) -> List[OptimizationResult]:
        """Perform optimization on multiple targets.
        
        Args:
            targets: List of targets to optimize
            optimization_type: Type of optimization to perform
            strategy: Optimization strategy to use
            
        Returns:
            List of optimization results
        """
        results = []
        for target in targets:
            result = self.optimize(target, optimization_type, strategy)
            results.append(result)
        return results
    
    def enable_optimization(self, optimization_type: OptimizationType) -> None:
        """Enable a specific optimization type.
        
        Args:
            optimization_type: Type of optimization to enable
        """
        self._enabled_optimizations[optimization_type.value] = True
        logger.debug(f"Enabled optimization type '{optimization_type.value}' for {self.name}")
    
    def disable_optimization(self, optimization_type: OptimizationType) -> None:
        """Disable a specific optimization type.
        
        Args:
            optimization_type: Type of optimization to disable
        """
        self._enabled_optimizations[optimization_type.value] = False
        logger.debug(f"Disabled optimization type '{optimization_type.value}' for {self.name}")
    
    def is_optimization_enabled(self, optimization_type: OptimizationType) -> bool:
        """Check if an optimization type is enabled.
        
        Args:
            optimization_type: Type of optimization to check
            
        Returns:
            True if optimization is enabled
        """
        return self._enabled_optimizations.get(optimization_type.value, True)
    
    def set_strategy(self, optimization_type: OptimizationType, strategy: OptimizationStrategy) -> None:
        """Set optimization strategy for a type.
        
        Args:
            optimization_type: Type of optimization
            strategy: Strategy to use
        """
        self._strategies[optimization_type.value] = strategy
        logger.debug(f"Set strategy '{strategy.value}' for optimization type '{optimization_type.value}'")
    
    def get_strategy(self, optimization_type: OptimizationType) -> OptimizationStrategy:
        """Get optimization strategy for a type.
        
        Args:
            optimization_type: Type of optimization
            
        Returns:
            Optimization strategy
        """
        return self._strategies.get(optimization_type.value, OptimizationStrategy.GREEDY)
    
    def set_max_iterations(self, max_iterations: int) -> None:
        """Set maximum iterations for optimization.
        
        Args:
            max_iterations: Maximum number of iterations
        """
        self._max_iterations = max_iterations
    
    def set_convergence_threshold(self, threshold: float) -> None:
        """Set convergence threshold.
        
        Args:
            threshold: Convergence threshold
        """
        self._convergence_threshold = threshold
    
    def get_optimization_history(self, limit: Optional[int] = None) -> List[OptimizationResult]:
        """Get optimization history.
        
        Args:
            limit: Maximum number of results to return
            
        Returns:
            List of optimization results
        """
        if limit is None:
            return self._optimization_history.copy()
        return self._optimization_history[-limit:]
    
    def clear_history(self) -> None:
        """Clear optimization history."""
        self._optimization_history.clear()
        logger.debug(f"Cleared optimization history for {self.name}")
    
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
    
    def clear_cache(self) -> None:
        """Clear cache."""
        self._cache.clear()
    
    def calculate_improvement(self, original: T, optimized: T) -> float:
        """Calculate improvement score between original and optimized targets.
        
        Args:
            original: Original target
            optimized: Optimized target
            
        Returns:
            Improvement score (0.0 to 1.0)
        """
        try:
            return self._calculate_improvement_score(original, optimized)
        except Exception as e:
            logger.warning(f"Error calculating improvement score: {e}")
            return 0.0
    
    def check_convergence(self, current_score: float, previous_score: float) -> bool:
        """Check if optimization has converged.
        
        Args:
            current_score: Current optimization score
            previous_score: Previous optimization score
            
        Returns:
            True if converged
        """
        return abs(current_score - previous_score) < self._convergence_threshold
    
    @abstractmethod
    def _validate_target(self, target: T) -> OptimizationResult:
        """Validate target before optimization.
        
        Args:
            target: Target to validate
            
        Returns:
            Validation result
        """
        pass
    
    @abstractmethod
    def _perform_optimization(self, target: T, optimization_type: OptimizationType, 
                            strategy: OptimizationStrategy, max_iterations: int) -> OptimizationResult:
        """Perform the actual optimization.
        
        Args:
            target: Target to optimize
            optimization_type: Type of optimization to perform
            strategy: Optimization strategy to use
            max_iterations: Maximum number of iterations
            
        Returns:
            Optimization result
        """
        pass
    
    @abstractmethod
    def _calculate_improvement_score(self, original: T, optimized: T) -> float:
        """Calculate improvement score between original and optimized targets.
        
        Args:
            original: Original target
            optimized: Optimized target
            
        Returns:
            Improvement score (0.0 to 1.0)
        """
        pass
    
    def _clear_cache(self) -> None:
        """Clear cache after successful optimization."""
        # Override in subclasses if needed
        pass 