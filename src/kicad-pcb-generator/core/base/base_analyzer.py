"""
Base analyzer class for standardizing analysis operations.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TypeVar, Generic
import logging
from datetime import datetime

from .results.analysis_result import AnalysisResult, AnalysisType

logger = logging.getLogger(__name__)

T = TypeVar('T')

class BaseAnalyzer(ABC, Generic[T]):
    """Base class for all analyzer classes."""
    
    def __init__(self, name: str = ""):
        """Initialize the base analyzer.
        
        Args:
            name: Name of the analyzer
        """
        self.name = name or self.__class__.__name__
        self._cache: Dict[str, Any] = {}
        self._analysis_history: List[AnalysisResult] = []
        self._enabled_analyses: Dict[str, bool] = {}
        
    def analyze(self, target: T, analysis_type: AnalysisType = AnalysisType.CUSTOM) -> AnalysisResult:
        """Perform analysis on a target.
        
        Args:
            target: Target to analyze
            analysis_type: Type of analysis to perform
            
        Returns:
            Analysis result
        """
        try:
            # Check if analysis is enabled
            if not self._enabled_analyses.get(analysis_type.value, True):
                return AnalysisResult(
                    success=False,
                    analysis_type=analysis_type,
                    message=f"Analysis type '{analysis_type.value}' is disabled"
                )
            
            # Validate target
            validation_result = self._validate_target(target)
            if not validation_result.success:
                return validation_result
            
            # Perform analysis
            result = self._perform_analysis(target, analysis_type)
            
            # Store in history
            self._analysis_history.append(result)
            
            # Clear cache if needed
            if result.success:
                self._clear_cache()
            
            logger.info(f"Analysis '{analysis_type.value}' completed for {self.name}")
            return result
            
        except Exception as e:
            logger.error(f"Error during analysis '{analysis_type.value}' in {self.name}: {e}")
            result = AnalysisResult(
                success=False,
                analysis_type=analysis_type,
                message=f"Error during analysis: {e}",
                errors=[str(e)]
            )
            self._analysis_history.append(result)
            return result
    
    def batch_analyze(self, targets: List[T], analysis_type: AnalysisType = AnalysisType.CUSTOM) -> List[AnalysisResult]:
        """Perform analysis on multiple targets.
        
        Args:
            targets: List of targets to analyze
            analysis_type: Type of analysis to perform
            
        Returns:
            List of analysis results
        """
        results = []
        for target in targets:
            result = self.analyze(target, analysis_type)
            results.append(result)
        return results
    
    def enable_analysis(self, analysis_type: AnalysisType) -> None:
        """Enable a specific analysis type.
        
        Args:
            analysis_type: Type of analysis to enable
        """
        self._enabled_analyses[analysis_type.value] = True
        logger.debug(f"Enabled analysis type '{analysis_type.value}' for {self.name}")
    
    def disable_analysis(self, analysis_type: AnalysisType) -> None:
        """Disable a specific analysis type.
        
        Args:
            analysis_type: Type of analysis to disable
        """
        self._enabled_analyses[analysis_type.value] = False
        logger.debug(f"Disabled analysis type '{analysis_type.value}' for {self.name}")
    
    def is_analysis_enabled(self, analysis_type: AnalysisType) -> bool:
        """Check if an analysis type is enabled.
        
        Args:
            analysis_type: Type of analysis to check
            
        Returns:
            True if analysis is enabled
        """
        return self._enabled_analyses.get(analysis_type.value, True)
    
    def get_analysis_history(self, limit: Optional[int] = None) -> List[AnalysisResult]:
        """Get analysis history.
        
        Args:
            limit: Maximum number of results to return
            
        Returns:
            List of analysis results
        """
        if limit is None:
            return self._analysis_history.copy()
        return self._analysis_history[-limit:]
    
    def clear_history(self) -> None:
        """Clear analysis history."""
        self._analysis_history.clear()
        logger.debug(f"Cleared analysis history for {self.name}")
    
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
    
    @abstractmethod
    def _validate_target(self, target: T) -> AnalysisResult:
        """Validate target before analysis.
        
        Args:
            target: Target to validate
            
        Returns:
            Validation result
        """
        pass
    
    @abstractmethod
    def _perform_analysis(self, target: T, analysis_type: AnalysisType) -> AnalysisResult:
        """Perform the actual analysis.
        
        Args:
            target: Target to analyze
            analysis_type: Type of analysis to perform
            
        Returns:
            Analysis result
        """
        pass
    
    def _clear_cache(self) -> None:
        """Clear cache after successful analysis."""
        # Override in subclasses if needed
        pass 