"""
Base configuration class for standardizing configuration operations.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TypeVar, Generic, Union
import logging
import json
import yaml
from pathlib import Path
from datetime import datetime

from .results.config_result import ConfigResult, ConfigFormat, ConfigSection, ConfigStatus

logger = logging.getLogger(__name__)

T = TypeVar('T')

class BaseConfig(ABC, Generic[T]):
    """Base class for all configuration classes."""
    
    def __init__(self, name: str = "", config_path: Optional[str] = None):
        """Initialize the base configuration.
        
        Args:
            name: Name of the configuration
            config_path: Path to configuration file
        """
        self.name = name or self.__class__.__name__
        self.config_path = config_path
        self._sections: Dict[str, ConfigSection] = {}
        self._cache: Dict[str, Any] = {}
        self._config_history: List[ConfigResult] = []
        self._default_values: Dict[str, Any] = {}
        self._validation_rules: Dict[str, Any] = {}
        
    def load(self, file_path: Optional[str] = None, 
             config_format: ConfigFormat = ConfigFormat.JSON) -> ConfigResult:
        """Load configuration from file.
        
        Args:
            file_path: Path to configuration file
            config_format: Format of the configuration file
            
        Returns:
            Configuration result
        """
        try:
            path = file_path or self.config_path
            if not path:
                return ConfigResult(
                    success=False,
                    status=ConfigStatus.ERROR,
                    message="No configuration file path specified",
                    config_type=self.name
                )
            
            if not Path(path).exists():
                return ConfigResult(
                    success=False,
                    status=ConfigStatus.ERROR,
                    message=f"Configuration file not found: {path}",
                    config_type=self.name,
                    file_path=path
                )
            
            # Load configuration based on format
            config_data = self._load_file(path, config_format)
            
            # Validate configuration
            validation_result = self._validate_config(config_data)
            if not validation_result.success:
                return validation_result
            
            # Parse configuration
            result = self._parse_config(config_data)
            result.file_path = path
            
            # Store in history
            self._config_history.append(result)
            
            logger.info(f"Configuration loaded from {path}")
            return result
            
        except Exception as e:
            logger.error(f"Error loading configuration for {self.name}: {e}")
            result = ConfigResult(
                success=False,
                status=ConfigStatus.ERROR,
                message=f"Error loading configuration: {e}",
                errors=[str(e)],
                config_type=self.name,
                file_path=file_path
            )
            self._config_history.append(result)
            return result
    
    def save(self, file_path: Optional[str] = None,
             config_format: ConfigFormat = ConfigFormat.JSON) -> ConfigResult:
        """Save configuration to file.
        
        Args:
            file_path: Path to save configuration file
            config_format: Format of the configuration file
            
        Returns:
            Configuration result
        """
        try:
            path = file_path or self.config_path
            if not path:
                return ConfigResult(
                    success=False,
                    status=ConfigStatus.ERROR,
                    message="No configuration file path specified",
                    config_type=self.name
                )
            
            # Prepare configuration data
            config_data = self._prepare_config_data()
            
            # Save configuration based on format
            self._save_file(path, config_data, config_format)
            
            result = ConfigResult(
                success=True,
                status=ConfigStatus.SAVED,
                data=config_data,
                message=f"Configuration saved to {path}",
                config_type=self.name,
                file_path=path
            )
            
            # Store in history
            self._config_history.append(result)
            
            logger.info(f"Configuration saved to {path}")
            return result
            
        except Exception as e:
            logger.error(f"Error saving configuration for {self.name}: {e}")
            result = ConfigResult(
                success=False,
                status=ConfigStatus.ERROR,
                message=f"Error saving configuration: {e}",
                errors=[str(e)],
                config_type=self.name,
                file_path=file_path
            )
            self._config_history.append(result)
            return result
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.
        
        Args:
            key: Configuration key (can be nested with dots)
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        try:
            keys = key.split('.')
            value = self._sections
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
        except Exception as e:
            logger.warning(f"Error getting configuration key '{key}': {e}")
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """Set configuration value.
        
        Args:
            key: Configuration key (can be nested with dots)
            value: Value to set
            
        Returns:
            True if successful
        """
        try:
            keys = key.split('.')
            config = self._sections
            
            # Navigate to the parent of the target key
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # Set the value
            config[keys[-1]] = value
            self._clear_cache()
            
            logger.debug(f"Set configuration key '{key}' = {value}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting configuration key '{key}': {e}")
            return False
    
    def add_section(self, section: ConfigSection) -> None:
        """Add a configuration section.
        
        Args:
            section: Configuration section to add
        """
        self._sections[section.name] = section
        logger.debug(f"Added configuration section '{section.name}'")
    
    def get_section(self, name: str) -> Optional[ConfigSection]:
        """Get a configuration section.
        
        Args:
            name: Section name
            
        Returns:
            Configuration section or None
        """
        return self._sections.get(name)
    
    def remove_section(self, name: str) -> bool:
        """Remove a configuration section.
        
        Args:
            name: Section name
            
        Returns:
            True if successful
        """
        if name in self._sections:
            del self._sections[name]
            self._clear_cache()
            logger.debug(f"Removed configuration section '{name}'")
            return True
        return False
    
    def set_default(self, key: str, value: Any) -> None:
        """Set default value for a configuration key.
        
        Args:
            key: Configuration key
            value: Default value
        """
        self._default_values[key] = value
    
    def get_default(self, key: str) -> Any:
        """Get default value for a configuration key.
        
        Args:
            key: Configuration key
            
        Returns:
            Default value
        """
        return self._default_values.get(key)
    
    def add_validation_rule(self, key: str, rule: Dict[str, Any]) -> None:
        """Add validation rule for a configuration key.
        
        Args:
            key: Configuration key
            rule: Validation rule
        """
        self._validation_rules[key] = rule
    
    def validate(self) -> ConfigResult:
        """Validate current configuration.
        
        Returns:
            Validation result
        """
        try:
            config_data = self._prepare_config_data()
            return self._validate_config(config_data)
        except Exception as e:
            logger.error(f"Error validating configuration for {self.name}: {e}")
            return ConfigResult(
                success=False,
                status=ConfigStatus.ERROR,
                message=f"Error validating configuration: {e}",
                errors=[str(e)],
                config_type=self.name
            )
    
    def reset_to_defaults(self) -> ConfigResult:
        """Reset configuration to default values.
        
        Returns:
            Configuration result
        """
        try:
            self._sections.clear()
            self._clear_cache()
            
            # Restore default values
            for key, value in self._default_values.items():
                self.set(key, value)
            
            result = ConfigResult(
                success=True,
                status=ConfigStatus.VALID,
                message="Configuration reset to defaults",
                config_type=self.name
            )
            
            self._config_history.append(result)
            logger.info(f"Configuration reset to defaults for {self.name}")
            return result
            
        except Exception as e:
            logger.error(f"Error resetting configuration for {self.name}: {e}")
            result = ConfigResult(
                success=False,
                status=ConfigStatus.ERROR,
                message=f"Error resetting configuration: {e}",
                errors=[str(e)],
                config_type=self.name
            )
            self._config_history.append(result)
            return result
    
    def get_config_history(self, limit: Optional[int] = None) -> List[ConfigResult]:
        """Get configuration history.
        
        Args:
            limit: Maximum number of results to return
            
        Returns:
            List of configuration results
        """
        if limit is None:
            return self._config_history.copy()
        return self._config_history[-limit:]
    
    def clear_history(self) -> None:
        """Clear configuration history."""
        self._config_history.clear()
        logger.debug(f"Cleared configuration history for {self.name}")
    
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
    
    def _load_file(self, file_path: str, config_format: ConfigFormat) -> Dict[str, Any]:
        """Load configuration from file.
        
        Args:
            file_path: Path to configuration file
            config_format: Format of the configuration file
            
        Returns:
            Configuration data
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            if config_format == ConfigFormat.JSON:
                return json.load(f)
            elif config_format == ConfigFormat.YAML:
                return yaml.safe_load(f)
            else:
                raise ValueError(f"Unsupported configuration format: {config_format}")
    
    def _save_file(self, file_path: str, config_data: Dict[str, Any], 
                   config_format: ConfigFormat) -> None:
        """Save configuration to file.
        
        Args:
            file_path: Path to save configuration file
            config_data: Configuration data to save
            config_format: Format of the configuration file
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            if config_format == ConfigFormat.JSON:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            elif config_format == ConfigFormat.YAML:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
            else:
                raise ValueError(f"Unsupported configuration format: {config_format}")
    
    @abstractmethod
    def _validate_config(self, config_data: Dict[str, Any]) -> ConfigResult:
        """Validate configuration data.
        
        Args:
            config_data: Configuration data to validate
            
        Returns:
            Validation result
        """
        pass
    
    @abstractmethod
    def _parse_config(self, config_data: Dict[str, Any]) -> ConfigResult:
        """Parse configuration data.
        
        Args:
            config_data: Configuration data to parse
            
        Returns:
            Parsing result
        """
        pass
    
    @abstractmethod
    def _prepare_config_data(self) -> Dict[str, Any]:
        """Prepare configuration data for saving.
        
        Returns:
            Configuration data
        """
        pass
    
    def _clear_cache(self) -> None:
        """Clear cache after configuration changes."""
        # Override in subclasses if needed
        pass 