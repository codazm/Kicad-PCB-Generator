"""
Standardized analysis result structure.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

class AnalysisType(Enum):
    """Types of analysis operations."""
    SIGNAL_INTEGRITY = "signal_integrity"
    POWER_ANALYSIS = "power_analysis"
    THERMAL_ANALYSIS = "thermal_analysis"
    EMI_EMC = "emi_emc"
    NOISE_ANALYSIS = "noise_analysis"
    FREQUENCY_RESPONSE = "frequency_response"
    IMPEDANCE_ANALYSIS = "impedance_analysis"
    CROSSTALK_ANALYSIS = "crosstalk_analysis"
    STABILITY_ANALYSIS = "stability_analysis"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    CUSTOM = "custom"

class AnalysisSeverity(Enum):
    """Severity levels for analysis results."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class AnalysisResult:
    """Standardized result of an analysis operation."""
    success: bool
    analysis_type: AnalysisType = AnalysisType.CUSTOM
    message: str = ""
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    data: Optional[Any] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    severity: AnalysisSeverity = AnalysisSeverity.INFO
    target_id: Optional[str] = None
    analysis_duration: Optional[float] = None
    confidence_score: Optional[float] = None
    recommendations: List[str] = field(default_factory=list)
    
    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
        if self.severity == AnalysisSeverity.INFO:
            self.severity = AnalysisSeverity.ERROR
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)
        if self.severity == AnalysisSeverity.INFO:
            self.severity = AnalysisSeverity.WARNING
    
    def add_recommendation(self, recommendation: str) -> None:
        """Add a recommendation."""
        self.recommendations.append(recommendation)
    
    def set_metric(self, key: str, value: Any) -> None:
        """Set a metric value."""
        self.metrics[key] = value
    
    def get_metric(self, key: str, default: Any = None) -> Any:
        """Get a metric value."""
        return self.metrics.get(key, default)
    
    def has_errors(self) -> bool:
        """Check if the result has errors."""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if the result has warnings."""
        return len(self.warnings) > 0
    
    def is_critical(self) -> bool:
        """Check if the result is critical."""
        return self.severity == AnalysisSeverity.CRITICAL
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'success': self.success,
            'analysis_type': self.analysis_type.value,
            'message': self.message,
            'errors': self.errors,
            'warnings': self.warnings,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data,
            'metrics': self.metrics,
            'severity': self.severity.value,
            'target_id': self.target_id,
            'analysis_duration': self.analysis_duration,
            'confidence_score': self.confidence_score,
            'recommendations': self.recommendations
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisResult':
        """Create result from dictionary."""
        return cls(
            success=data.get('success', False),
            analysis_type=AnalysisType(data.get('analysis_type', 'custom')),
            message=data.get('message', ''),
            errors=data.get('errors', []),
            warnings=data.get('warnings', []),
            timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
            data=data.get('data'),
            metrics=data.get('metrics', {}),
            severity=AnalysisSeverity(data.get('severity', 'info')),
            target_id=data.get('target_id'),
            analysis_duration=data.get('analysis_duration'),
            confidence_score=data.get('confidence_score'),
            recommendations=data.get('recommendations', [])
        ) 