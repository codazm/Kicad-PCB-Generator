"""
Standardized configuration result structure.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

class ConfigFormat(Enum):
    """Configuration file formats."""
    JSON = "json"
    YAML = "yaml"
    INI = "ini"
    TOML = "toml"
    XML = "xml"

class ConfigStatus(Enum):
    """Configuration status."""
    VALID = "valid"
    INVALID = "invalid"
    LOADED = "loaded"
    SAVED = "saved"
    ERROR = "error"
    PENDING = "pending"

@dataclass
class ConfigSection:
    """Configuration section."""
    name: str
    data: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    required: bool = False
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    parent_section: Optional[str] = None
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from section."""
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set value in section."""
        self.data[key] = value
    
    def has_key(self, key: str) -> bool:
        """Check if section has key."""
        return key in self.data
    
    def remove_key(self, key: str) -> bool:
        """Remove key from section."""
        if key in self.data:
            del self.data[key]
            return True
        return False

@dataclass
class ConfigResult:
    """Standardized result of a configuration operation."""
    success: bool
    status: ConfigStatus = ConfigStatus.PENDING
    message: str = ""
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    data: Optional[Any] = None
    config_type: str = ""
    file_path: Optional[str] = None
    sections: Dict[str, ConfigSection] = field(default_factory=dict)
    validation_results: Dict[str, bool] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
        if self.status == ConfigStatus.VALID:
            self.status = ConfigStatus.ERROR
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)
    
    def add_section(self, section: ConfigSection) -> None:
        """Add a configuration section."""
        self.sections[section.name] = section
    
    def get_section(self, name: str) -> Optional[ConfigSection]:
        """Get a configuration section."""
        return self.sections.get(name)
    
    def remove_section(self, name: str) -> bool:
        """Remove a configuration section."""
        if name in self.sections:
            del self.sections[name]
            return True
        return False
    
    def set_validation_result(self, key: str, is_valid: bool) -> None:
        """Set validation result for a key."""
        self.validation_results[key] = is_valid
    
    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return all(self.validation_results.values()) if self.validation_results else True
    
    def has_errors(self) -> bool:
        """Check if the result has errors."""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if the result has warnings."""
        return len(self.warnings) > 0
    
    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata value."""
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value."""
        return self.metadata.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'success': self.success,
            'status': self.status.value,
            'message': self.message,
            'errors': self.errors,
            'warnings': self.warnings,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data,
            'config_type': self.config_type,
            'file_path': self.file_path,
            'sections': {name: {
                'name': section.name,
                'data': section.data,
                'description': section.description,
                'required': section.required,
                'validation_rules': section.validation_rules,
                'parent_section': section.parent_section
            } for name, section in self.sections.items()},
            'validation_results': self.validation_results,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConfigResult':
        """Create result from dictionary."""
        sections = {}
        if 'sections' in data:
            for name, section_data in data['sections'].items():
                sections[name] = ConfigSection(
                    name=section_data['name'],
                    data=section_data['data'],
                    description=section_data.get('description', ''),
                    required=section_data.get('required', False),
                    validation_rules=section_data.get('validation_rules', {}),
                    parent_section=section_data.get('parent_section')
                )
        
        return cls(
            success=data.get('success', False),
            status=ConfigStatus(data.get('status', 'pending')),
            message=data.get('message', ''),
            errors=data.get('errors', []),
            warnings=data.get('warnings', []),
            timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
            data=data.get('data'),
            config_type=data.get('config_type', ''),
            file_path=data.get('file_path'),
            sections=sections,
            validation_results=data.get('validation_results', {}),
            metadata=data.get('metadata', {})
        ) 