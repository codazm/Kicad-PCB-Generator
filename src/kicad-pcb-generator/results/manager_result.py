"""
Standardized manager result structure.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

class ManagerOperation(Enum):
    """Types of manager operations."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"
    SEARCH = "search"
    VALIDATE = "validate"
    EXPORT = "export"
    IMPORT = "import"
    CUSTOM = "custom"

class ManagerStatus(Enum):
    """Manager operation status."""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    PENDING = "pending"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

@dataclass
class ManagerResult:
    """Standardized result of a manager operation."""
    success: bool
    operation: ManagerOperation = ManagerOperation.CUSTOM
    status: ManagerStatus = ManagerStatus.SUCCESS
    message: str = ""
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    data: Optional[Any] = None
    affected_items: int = 0
    total_items: int = 0
    operation_duration: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    item_ids: List[str] = field(default_factory=list)
    
    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
        if self.status == ManagerStatus.SUCCESS:
            self.status = ManagerStatus.FAILED
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)
        if self.status == ManagerStatus.SUCCESS:
            self.status = ManagerStatus.PARTIAL
    
    def add_item_id(self, item_id: str) -> None:
        """Add an affected item ID."""
        if item_id not in self.item_ids:
            self.item_ids.append(item_id)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata value."""
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value."""
        return self.metadata.get(key, default)
    
    def has_errors(self) -> bool:
        """Check if the result has errors."""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if the result has warnings."""
        return len(self.warnings) > 0
    
    def is_partial_success(self) -> bool:
        """Check if operation was partially successful."""
        return self.status == ManagerStatus.PARTIAL
    
    def get_success_rate(self) -> float:
        """Get success rate as percentage."""
        if self.total_items == 0:
            return 100.0 if self.success else 0.0
        return (self.affected_items / self.total_items) * 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'success': self.success,
            'operation': self.operation.value,
            'status': self.status.value,
            'message': self.message,
            'errors': self.errors,
            'warnings': self.warnings,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data,
            'affected_items': self.affected_items,
            'total_items': self.total_items,
            'operation_duration': self.operation_duration,
            'metadata': self.metadata,
            'item_ids': self.item_ids
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ManagerResult':
        """Create result from dictionary."""
        return cls(
            success=data.get('success', False),
            operation=ManagerOperation(data.get('operation', 'custom')),
            status=ManagerStatus(data.get('status', 'success')),
            message=data.get('message', ''),
            errors=data.get('errors', []),
            warnings=data.get('warnings', []),
            timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
            data=data.get('data'),
            affected_items=data.get('affected_items', 0),
            total_items=data.get('total_items', 0),
            operation_duration=data.get('operation_duration'),
            metadata=data.get('metadata', {}),
            item_ids=data.get('item_ids', [])
        ) 