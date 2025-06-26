"""
Template Configuration Manager

This module provides configuration management for template parameters,
replacing hardcoded values with configurable settings.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from ..core.base.base_config import BaseConfig


@dataclass
class TemplateConfigItem:
    """Data structure for template configuration parameters."""
    id: str
    name: str
    description: str
    category: str
    version: str
    author: str
    tags: List[str]
    parameters: Dict[str, Any]
    constraints: Dict[str, Any]
    dependencies: List[str]
    validation_rules: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class TemplateConfig(BaseConfig[TemplateConfigItem]):
    """Configuration for template management.
    
    Now inherits from BaseConfig for standardized configuration operations.
    """
    
    def __init__(self, name: str = "TemplateConfig", config_path: Optional[str] = None):
        """Initialize template configuration.
        
        Args:
            name: Configuration name
            config_path: Path to configuration file
        """
        super().__init__(name, config_path)
        self._setup_default_values()
        self._setup_validation_rules()
    
    def _setup_default_values(self) -> None:
        """Set up default configuration values."""
        self.set_default("default_category", "general")
        self.set_default("default_version", "1.0.0")
        self.set_default("default_author", "KiCad PCB Generator")
        self.set_default("max_template_name_length", 100)
        self.set_default("max_description_length", 500)
        self.set_default("max_tags_count", 10)
        self.set_default("max_parameters_count", 50)
        self.set_default("max_constraints_count", 20)
        self.set_default("max_dependencies_count", 10)
        self.set_default("max_validation_rules_count", 20)
        self.set_default("template_storage_path", "templates")
        self.set_default("backup_enabled", True)
        self.set_default("version_control_enabled", True)
        self.set_default("auto_validation_enabled", True)
        self.set_default("template_cache_enabled", True)
        self.set_default("template_cache_size", 50)
    
    def _setup_validation_rules(self) -> None:
        """Set up validation rules for configuration values."""
        self.add_validation_rule("default_category", {
            "type": "str",
            "required": True,
            "min_length": 1,
            "max_length": 50
        })
        self.add_validation_rule("default_version", {
            "type": "str",
            "required": True,
            "min_length": 1,
            "max_length": 20
        })
        self.add_validation_rule("default_author", {
            "type": "str",
            "required": True,
            "min_length": 1,
            "max_length": 100
        })
        self.add_validation_rule("max_template_name_length", {
            "type": "int",
            "required": True,
            "min": 10,
            "max": 200
        })
        self.add_validation_rule("max_description_length", {
            "type": "int",
            "required": True,
            "min": 50,
            "max": 1000
        })
        self.add_validation_rule("max_tags_count", {
            "type": "int",
            "required": True,
            "min": 1,
            "max": 50
        })
        self.add_validation_rule("max_parameters_count", {
            "type": "int",
            "required": True,
            "min": 1,
            "max": 100
        })
        self.add_validation_rule("max_constraints_count", {
            "type": "int",
            "required": True,
            "min": 1,
            "max": 50
        })
        self.add_validation_rule("max_dependencies_count", {
            "type": "int",
            "required": True,
            "min": 0,
            "max": 20
        })
        self.add_validation_rule("max_validation_rules_count", {
            "type": "int",
            "required": True,
            "min": 1,
            "max": 50
        })
        self.add_validation_rule("template_storage_path", {
            "type": "str",
            "required": True,
            "min_length": 1,
            "max_length": 200
        })
        self.add_validation_rule("backup_enabled", {
            "type": "bool",
            "required": True
        })
        self.add_validation_rule("version_control_enabled", {
            "type": "bool",
            "required": True
        })
        self.add_validation_rule("auto_validation_enabled", {
            "type": "bool",
            "required": True
        })
        self.add_validation_rule("template_cache_enabled", {
            "type": "bool",
            "required": True
        })
        self.add_validation_rule("template_cache_size", {
            "type": "int",
            "required": True,
            "min": 10,
            "max": 200
        })
    
    def _validate_config(self, config_data: Dict[str, Any]) -> ConfigResult:
        """Validate template configuration data.
        
        Args:
            config_data: Configuration data to validate
            
        Returns:
            Validation result
        """
        try:
            errors = []
            
            # Validate required fields
            required_fields = [
                "default_category", "default_version", "default_author",
                "max_template_name_length", "max_description_length",
                "max_tags_count", "max_parameters_count", "max_constraints_count",
                "max_dependencies_count", "max_validation_rules_count",
                "template_storage_path", "backup_enabled", "version_control_enabled",
                "auto_validation_enabled", "template_cache_enabled", "template_cache_size"
            ]
            
            for field in required_fields:
                if field not in config_data:
                    errors.append(f"Missing required field: {field}")
                    continue
                
                value = config_data[field]
                rule = self._validation_rules.get(field, {})
                
                # Type validation
                if rule.get("type") == "str" and not isinstance(value, str):
                    errors.append(f"Field {field} must be a string")
                elif rule.get("type") == "int" and not isinstance(value, int):
                    errors.append(f"Field {field} must be an integer")
                elif rule.get("type") == "bool" and not isinstance(value, bool):
                    errors.append(f"Field {field} must be a boolean")
                
                # String validation
                if rule.get("type") == "str":
                    if rule.get("min_length") and len(value) < rule["min_length"]:
                        errors.append(f"Field {field} must have minimum length {rule['min_length']}")
                    if rule.get("max_length") and len(value) > rule["max_length"]:
                        errors.append(f"Field {field} must have maximum length {rule['max_length']}")
                
                # Numeric validation
                if rule.get("type") == "int":
                    if rule.get("min") is not None and value < rule["min"]:
                        errors.append(f"Field {field} must be >= {rule['min']}")
                    if rule.get("max") is not None and value > rule["max"]:
                        errors.append(f"Field {field} must be <= {rule['max']}")
            
            if errors:
                return ConfigResult(
                    success=False,
                    status=ConfigStatus.INVALID,
                    message="Template configuration validation failed",
                    errors=errors,
                    config_type=self.name
                )
            
            return ConfigResult(
                success=True,
                status=ConfigStatus.VALID,
                message="Template configuration is valid",
                config_type=self.name
            )
            
        except Exception as e:
            return ConfigResult(
                success=False,
                status=ConfigStatus.ERROR,
                message=f"Error validating template configuration: {e}",
                errors=[str(e)],
                config_type=self.name
            )
    
    def _parse_config(self, config_data: Dict[str, Any]) -> ConfigResult:
        """Parse template configuration data.
        
        Args:
            config_data: Configuration data to parse
            
        Returns:
            Parsing result
        """
        try:
            # Create template config item
            template_item = TemplateConfigItem(
                id=config_data.get("id", "template_config"),
                name=config_data.get("name", "Template Configuration"),
                description=config_data.get("description", "Template management configuration"),
                category=config_data.get("category", self.get_default("default_category")),
                version=config_data.get("version", self.get_default("default_version")),
                author=config_data.get("author", self.get_default("default_author")),
                tags=config_data.get("tags", []),
                parameters=config_data.get("parameters", {}),
                constraints=config_data.get("constraints", {}),
                dependencies=config_data.get("dependencies", []),
                validation_rules=config_data.get("validation_rules", []),
                metadata=config_data.get("metadata", {})
            )
            
            # Add to sections
            self.add_section(ConfigSection(
                name="template_config",
                data=config_data,
                description="Template management configuration"
            ))
            
            return ConfigResult(
                success=True,
                status=ConfigStatus.LOADED,
                message="Template configuration parsed successfully",
                data=template_item,
                config_type=self.name
            )
            
        except Exception as e:
            return ConfigResult(
                success=False,
                status=ConfigStatus.ERROR,
                message=f"Error parsing template configuration: {e}",
                errors=[str(e)],
                config_type=self.name
            )
    
    def _prepare_config_data(self) -> Dict[str, Any]:
        """Prepare template configuration data for saving.
        
        Returns:
            Configuration data
        """
        template_section = self.get_section("template_config")
        if template_section:
            return template_section.data
        
        # Return default configuration
        return {
            "id": "template_config",
            "name": "Template Configuration",
            "description": "Template management configuration",
            "category": self.get_default("default_category"),
            "version": self.get_default("default_version"),
            "author": self.get_default("default_author"),
            "tags": [],
            "parameters": {},
            "constraints": {},
            "dependencies": [],
            "validation_rules": [],
            "metadata": {},
            "max_template_name_length": self.get_default("max_template_name_length"),
            "max_description_length": self.get_default("max_description_length"),
            "max_tags_count": self.get_default("max_tags_count"),
            "max_parameters_count": self.get_default("max_parameters_count"),
            "max_constraints_count": self.get_default("max_constraints_count"),
            "max_dependencies_count": self.get_default("max_dependencies_count"),
            "max_validation_rules_count": self.get_default("max_validation_rules_count"),
            "template_storage_path": self.get_default("template_storage_path"),
            "backup_enabled": self.get_default("backup_enabled"),
            "version_control_enabled": self.get_default("version_control_enabled"),
            "auto_validation_enabled": self.get_default("auto_validation_enabled"),
            "template_cache_enabled": self.get_default("template_cache_enabled"),
            "template_cache_size": self.get_default("template_cache_size")
        }
    
    def create_template_config(self,
                              name: str = "Template Configuration",
                              description: str = "Template management configuration",
                              category: str = None,
                              version: str = None,
                              author: str = None,
                              tags: List[str] = None,
                              parameters: Dict[str, Any] = None,
                              constraints: Dict[str, Any] = None,
                              dependencies: List[str] = None,
                              validation_rules: List[Dict[str, Any]] = None,
                              metadata: Dict[str, Any] = None) -> ConfigResult[TemplateConfigItem]:
        """Create new template configuration.
        
        Args:
            name: Template configuration name
            description: Template configuration description
            category: Template category
            version: Template version
            author: Template author
            tags: Template tags
            parameters: Template parameters
            constraints: Template constraints
            dependencies: Template dependencies
            validation_rules: Template validation rules
            metadata: Template metadata
            
        Returns:
            Configuration result
        """
        try:
            config_data = {
                "id": f"template_config_{len(self._config_history) + 1}",
                "name": name,
                "description": description,
                "category": category or self.get_default("default_category"),
                "version": version or self.get_default("default_version"),
                "author": author or self.get_default("default_author"),
                "tags": tags or [],
                "parameters": parameters or {},
                "constraints": constraints or {},
                "dependencies": dependencies or [],
                "validation_rules": validation_rules or [],
                "metadata": metadata or {},
                "max_template_name_length": self.get_default("max_template_name_length"),
                "max_description_length": self.get_default("max_description_length"),
                "max_tags_count": self.get_default("max_tags_count"),
                "max_parameters_count": self.get_default("max_parameters_count"),
                "max_constraints_count": self.get_default("max_constraints_count"),
                "max_dependencies_count": self.get_default("max_dependencies_count"),
                "max_validation_rules_count": self.get_default("max_validation_rules_count"),
                "template_storage_path": self.get_default("template_storage_path"),
                "backup_enabled": self.get_default("backup_enabled"),
                "version_control_enabled": self.get_default("version_control_enabled"),
                "auto_validation_enabled": self.get_default("auto_validation_enabled"),
                "template_cache_enabled": self.get_default("template_cache_enabled"),
                "template_cache_size": self.get_default("template_cache_size")
            }
            
            # Validate configuration
            validation_result = self._validate_config(config_data)
            if not validation_result.success:
                return validation_result
            
            # Parse configuration
            return self._parse_config(config_data)
            
        except Exception as e:
            return ConfigResult(
                success=False,
                status=ConfigStatus.ERROR,
                message=f"Error creating template configuration: {e}",
                errors=[str(e)],
                config_type=self.name
            ) 