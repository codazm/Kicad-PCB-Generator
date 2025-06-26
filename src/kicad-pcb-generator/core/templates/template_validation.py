"""Template validation system for the KiCad PCB Generator."""
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import json
import logging
from pathlib import Path

from ..validation.base_validator import BaseValidator
from ..validation.validation_results import (
    ValidationResult,
    ValidationCategory,
    ValidationSeverity
)
from .template_versioning import TemplateVersionManager
from .rule_template import RuleTemplate
from ...utils.logging.logger import Logger
from ...utils.config.settings import Settings

class ValidationSeverity(Enum):
    """Validation severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

@dataclass
class ValidationResult:
    """Result of a validation check."""
    success: bool
    message: str
    severity: ValidationSeverity
    details: Optional[Dict[str, Any]] = None

@dataclass
class ValidationSummary:
    """Summary of validation results."""
    template_id: str
    version: Optional[str]
    timestamp: datetime
    overall_success: bool
    results: List[ValidationResult]
    metadata: Dict[str, Any]

class TemplateValidator(BaseValidator):
    """Validates templates and their versions.
    
    Now inherits from BaseValidator for standardized validation operations.
    """
    
    def __init__(
        self,
        storage_path: Union[str, Path],
        version_manager: Optional[TemplateVersionManager] = None,
        rule_template: Optional[RuleTemplate] = None,
        logger: Optional[Logger] = None
    ):
        """Initialize template validator.
        
        Args:
            storage_path: Path to store validation results
            version_manager: Optional version manager instance
            rule_template: Optional rule template instance
            logger: Optional logger instance
        """
        super().__init__(logger)
        self.settings = Settings()
        self.storage_path = Path(storage_path)
        self.version_manager = version_manager
        self.rule_template = rule_template
        
        # Create storage directory
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize validation rules
        self._init_validation_rules()
    
    def validate_template(
        self,
        template_id: str,
        version: Optional[str] = None,
        validate_rules: bool = True
    ) -> ValidationSummary:
        """Validate a template version.
        
        Args:
            template_id: Template ID
            version: Optional version to validate, or None for latest version
            validate_rules: Whether to validate associated rule templates
            
        Returns:
            Validation summary
        """
        try:
            # Get template version
            if version and self.version_manager:
                version_data = self.version_manager.get_version(template_id, version)
                if not version_data:
                    return ValidationSummary(
                        template_id=template_id,
                        version=version,
                        timestamp=datetime.now(),
                        overall_success=False,
                        results=[
                            ValidationResult(
                                success=False,
                                message=f"Version {version} not found",
                                severity=ValidationSeverity.ERROR
                            )
                        ],
                        metadata={}
                    )
                template = version_data.template
            else:
                # Get latest version
                template = self._load_template(template_id)
                if not template:
                    return ValidationSummary(
                        template_id=template_id,
                        version=version,
                        timestamp=datetime.now(),
                        overall_success=False,
                        results=[
                            ValidationResult(
                                success=False,
                                message="Template not found",
                                severity=ValidationSeverity.ERROR
                            )
                        ],
                        metadata={}
                    )
            
            # Run validation checks
            results = []
            
            # Validate template structure
            structure_result = self._validate_template_structure(template)
            results.append(structure_result)
            
            # Validate template content
            content_result = self._validate_template_content(template)
            results.append(content_result)
            
            # Validate rule templates if requested
            if validate_rules and self.rule_template:
                rule_results = self._validate_rule_templates(template)
                results.extend(rule_results)
            
            # Create validation summary
            summary = ValidationSummary(
                template_id=template_id,
                version=version,
                timestamp=datetime.now(),
                overall_success=all(r.success for r in results),
                results=results,
                metadata={
                    "template_name": template.get("name", ""),
                    "template_category": template.get("category", ""),
                    "template_type": template.get("type", ""),
                    "validation_rules": len(results)
                }
            )
            
            # Save validation results
            self._save_validation_results(summary)
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to validate template: {e}")
            return ValidationSummary(
                template_id=template_id,
                version=version,
                timestamp=datetime.now(),
                overall_success=False,
                results=[
                    ValidationResult(
                        success=False,
                        message=f"Validation error: {str(e)}",
                        severity=ValidationSeverity.ERROR
                    )
                ],
                metadata={}
            )
    
    def get_validation_history(
        self,
        template_id: str,
        version: Optional[str] = None
    ) -> List[ValidationSummary]:
        """Get validation history for a template version.
        
        Args:
            template_id: Template ID
            version: Optional version to get history for, or None for all versions
            
        Returns:
            List of validation summaries
        """
        try:
            history = []
            validation_dir = self.storage_path / template_id
            
            if not validation_dir.exists():
                return history
            
            # Get validation files
            if version:
                pattern = f"validation_{version}_*.json"
            else:
                pattern = "validation_*.json"
            
            for validation_file in validation_dir.glob(pattern):
                try:
                    with open(validation_file, 'r') as f:
                        data = json.load(f)
                        summary = self._load_validation_summary(data)
                        history.append(summary)
                except Exception as e:
                    self.logger.error(f"Failed to load validation file {validation_file}: {e}")
            
            # Sort by timestamp
            history.sort(key=lambda x: x.timestamp, reverse=True)
            return history
            
        except Exception as e:
            self.logger.error(f"Failed to get validation history: {e}")
            return []
    
    def _init_validation_rules(self) -> None:
        """Initialize validation rules."""
        self.validation_rules = {
            "structure": [
                self._check_required_fields,
                self._check_field_types,
                self._check_constraints
            ],
            "content": [
                self._check_name_format,
                self._check_description_length,
                self._check_category_validity,
                self._check_type_validity,
                self._check_severity_validity
            ]
        }
    
    def _validate_template_structure(self, template: Dict[str, Any]) -> ValidationResult:
        """Validate template structure.
        
        Args:
            template: Template to validate
            
        Returns:
            Validation result
        """
        try:
            for rule in self.validation_rules["structure"]:
                result = rule(template)
                if not result.success:
                    return result
            return ValidationResult(
                success=True,
                message="Template structure validation passed",
                severity=ValidationSeverity.INFO
            )
        except Exception as e:
            return ValidationResult(
                success=False,
                message=f"Template structure validation failed: {e}",
                severity=ValidationSeverity.ERROR
            )
    
    def _validate_template_content(self, template: Dict[str, Any]) -> ValidationResult:
        """Validate template content.
        
        Args:
            template: Template to validate
            
        Returns:
            Validation result
        """
        try:
            for rule in self.validation_rules["content"]:
                result = rule(template)
                if not result.success:
                    return result
            return ValidationResult(
                success=True,
                message="Template content validation passed",
                severity=ValidationSeverity.INFO
            )
        except Exception as e:
            return ValidationResult(
                success=False,
                message=f"Template content validation failed: {e}",
                severity=ValidationSeverity.ERROR
            )
    
    def _validate_rule_templates(self, template: Dict[str, Any]) -> List[ValidationResult]:
        """Validate rule templates associated with the template.
        
        Args:
            template: Template to validate
            
        Returns:
            List of validation results
        """
        results = []
        try:
            if "rules" in template:
                for rule in template["rules"]:
                    result = self._validate_rule_template(rule)
                    results.append(result)
        except Exception as e:
            results.append(ValidationResult(
                success=False,
                message=f"Rule template validation failed: {e}",
                severity=ValidationSeverity.ERROR
            ))
        return results
    
    def _validate_rule_template(self, rule: Dict[str, Any]) -> ValidationResult:
        """Validate a single rule template.
        
        Args:
            rule: Rule template to validate
            
        Returns:
            Validation result
        """
        try:
            # Check required fields
            required_fields = ["name", "type", "severity"]
            for field in required_fields:
                if field not in rule:
                    return ValidationResult(
                        success=False,
                        message=f"Rule template missing required field: {field}",
                        severity=ValidationSeverity.ERROR
                    )
            
            # Check field types
            if not isinstance(rule["name"], str):
                return ValidationResult(
                    success=False,
                    message="Rule template name must be a string",
                    severity=ValidationSeverity.ERROR
                )
            
            if not isinstance(rule["type"], str):
                return ValidationResult(
                    success=False,
                    message="Rule template type must be a string",
                    severity=ValidationSeverity.ERROR
                )
            
            if not isinstance(rule["severity"], str):
                return ValidationResult(
                    success=False,
                    message="Rule template severity must be a string",
                    severity=ValidationSeverity.ERROR
                )
            
            # Check severity validity
            valid_severities = ["error", "warning", "info"]
            if rule["severity"] not in valid_severities:
                return ValidationResult(
                    success=False,
                    message=f"Rule template severity must be one of: {', '.join(valid_severities)}",
                    severity=ValidationSeverity.ERROR
                )
            
            return ValidationResult(
                success=True,
                message=f"Rule template '{rule['name']}' validation passed",
                severity=ValidationSeverity.INFO
            )
            
        except Exception as e:
            return ValidationResult(
                success=False,
                message=f"Rule template validation failed: {e}",
                severity=ValidationSeverity.ERROR
            )
    
    def _check_required_fields(self, template: Dict[str, Any]) -> ValidationResult:
        """Check required fields.
        
        Args:
            template: Template to check
            
        Returns:
            Validation result
        """
        required_fields = ["name", "description", "category", "type"]
        missing_fields = []
        
        for field in required_fields:
            if field not in template or not template[field]:
                missing_fields.append(field)
        
        if missing_fields:
            return ValidationResult(
                success=False,
                message=f"Template missing required fields: {', '.join(missing_fields)}",
                severity=ValidationSeverity.ERROR
            )
        
        return ValidationResult(
            success=True,
            message="Required fields check passed",
            severity=ValidationSeverity.INFO
        )
    
    def _check_field_types(self, template: Dict[str, Any]) -> ValidationResult:
        """Check field types.
        
        Args:
            template: Template to check
            
        Returns:
            Validation result
        """
        field_types = {
            "name": str,
            "description": str,
            "category": str,
            "type": str,
            "version": str,
            "author": str
        }
        
        for field, expected_type in field_types.items():
            if field in template and not isinstance(template[field], expected_type):
                return ValidationResult(
                    success=False,
                    message=f"Field '{field}' must be of type {expected_type.__name__}",
                    severity=ValidationSeverity.ERROR
                )
        
        return ValidationResult(
            success=True,
            message="Field types check passed",
            severity=ValidationSeverity.INFO
        )
    
    def _check_constraints(self, template: Dict[str, Any]) -> ValidationResult:
        """Check constraints.
        
        Args:
            template: Template to check
            
        Returns:
            Validation result
        """
        # Check name length
        if "name" in template and len(template["name"]) > 100:
            return ValidationResult(
                success=False,
                message="Template name must be 100 characters or less",
                severity=ValidationSeverity.ERROR
            )
        
        # Check description length
        if "description" in template and len(template["description"]) > 1000:
            return ValidationResult(
                success=False,
                message="Template description must be 1000 characters or less",
                severity=ValidationSeverity.ERROR
            )
        
        return ValidationResult(
            success=True,
            message="Constraints check passed",
            severity=ValidationSeverity.INFO
        )
    
    def _check_name_format(self, template: Dict[str, Any]) -> ValidationResult:
        """Check name format.
        
        Args:
            template: Template to check
            
        Returns:
            Validation result
        """
        if "name" in template:
            name = template["name"]
            if not name.strip():
                return ValidationResult(
                    success=False,
                    message="Template name cannot be empty or whitespace",
                    severity=ValidationSeverity.ERROR
                )
            
            # Check for invalid characters
            invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
            for char in invalid_chars:
                if char in name:
                    return ValidationResult(
                        success=False,
                        message=f"Template name contains invalid character: {char}",
                        severity=ValidationSeverity.ERROR
                    )
        
        return ValidationResult(
            success=True,
            message="Name format check passed",
            severity=ValidationSeverity.INFO
        )
    
    def _check_description_length(self, template: Dict[str, Any]) -> ValidationResult:
        """Check description length.
        
        Args:
            template: Template to check
            
        Returns:
            Validation result
        """
        if "description" in template:
            description = template["description"]
            if len(description) < 10:
                return ValidationResult(
                    success=False,
                    message="Template description must be at least 10 characters long",
                    severity=ValidationSeverity.WARNING
                )
        
        return ValidationResult(
            success=True,
            message="Description length check passed",
            severity=ValidationSeverity.INFO
        )
    
    def _check_category_validity(self, template: Dict[str, Any]) -> ValidationResult:
        """Check category validity.
        
        Args:
            template: Template to check
            
        Returns:
            Validation result
        """
        if "category" in template:
            valid_categories = ["audio", "digital", "analog", "power", "mixed"]
            category = template["category"].lower()
            if category not in valid_categories:
                return ValidationResult(
                    success=False,
                    message=f"Template category must be one of: {', '.join(valid_categories)}",
                    severity=ValidationSeverity.ERROR
                )
        
        return ValidationResult(
            success=True,
            message="Category validity check passed",
            severity=ValidationSeverity.INFO
        )
    
    def _check_type_validity(self, template: Dict[str, Any]) -> ValidationResult:
        """Check type validity.
        
        Args:
            template: Template to check
            
        Returns:
            Validation result
        """
        if "type" in template:
            valid_types = ["component", "circuit", "board", "system"]
            template_type = template["type"].lower()
            if template_type not in valid_types:
                return ValidationResult(
                    success=False,
                    message=f"Template type must be one of: {', '.join(valid_types)}",
                    severity=ValidationSeverity.ERROR
                )
        
        return ValidationResult(
            success=True,
            message="Type validity check passed",
            severity=ValidationSeverity.INFO
        )
    
    def _check_severity_validity(self, template: Dict[str, Any]) -> ValidationResult:
        """Check severity validity.
        
        Args:
            template: Template to check
            
        Returns:
            Validation result
        """
        if "severity" in template:
            valid_severities = ["error", "warning", "info"]
            severity = template["severity"].lower()
            if severity not in valid_severities:
                return ValidationResult(
                    success=False,
                    message=f"Template severity must be one of: {', '.join(valid_severities)}",
                    severity=ValidationSeverity.ERROR
                )
        
        return ValidationResult(
            success=True,
            message="Severity validity check passed",
            severity=ValidationSeverity.INFO
        )
    
    def _load_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Load template from storage.
        
        Args:
            template_id: Template ID
            
        Returns:
            Template data or None
        """
        try:
            template_file = self.storage_path / f"{template_id}.json"
            if template_file.exists():
                with open(template_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load template {template_id}: {e}")
        return None
    
    def _save_validation_results(self, summary: ValidationSummary) -> None:
        """Save validation results to storage.
        
        Args:
            summary: Validation summary to save
        """
        try:
            validation_dir = self.storage_path / summary.template_id
            validation_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp_str = summary.timestamp.strftime("%Y%m%d_%H%M%S")
            version_str = summary.version or "latest"
            filename = f"validation_{version_str}_{timestamp_str}.json"
            filepath = validation_dir / filename
            
            data = self._format_validation_summary(summary)
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"Failed to save validation results: {e}")
    
    def _format_validation_summary(self, summary: ValidationSummary) -> Dict[str, Any]:
        """Format validation summary for storage.
        
        Args:
            summary: Validation summary to format
            
        Returns:
            Formatted data
        """
        return {
            "template_id": summary.template_id,
            "version": summary.version,
            "timestamp": summary.timestamp.isoformat(),
            "overall_success": summary.overall_success,
            "results": [
                {
                    "success": result.success,
                    "message": result.message,
                    "severity": result.severity.value,
                    "details": result.details
                }
                for result in summary.results
            ],
            "metadata": summary.metadata
        }
    
    def _load_validation_summary(self, data: Dict[str, Any]) -> ValidationSummary:
        """Load validation summary from data.
        
        Args:
            data: Data to load from
            
        Returns:
            Validation summary
        """
        results = [
            ValidationResult(
                success=result["success"],
                message=result["message"],
                severity=ValidationSeverity(result["severity"]),
                details=result.get("details")
            )
            for result in data["results"]
        ]
        
        return ValidationSummary(
            template_id=data["template_id"],
            version=data.get("version"),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            overall_success=data["overall_success"],
            results=results,
            metadata=data["metadata"]
        )
    
    def _validate_audio_specific(self) -> List[ValidationResult]:
        """Validate audio-specific rules using BaseValidator interface.
        
        Returns:
            List of validation results
        """
        results = []
        try:
            # Templates are not audio-specific; therefore this check is a no-op.
            self.logger.debug("Audio-specific validation skipped for template validation context")
        except Exception as e:
            self.logger.error(f"Error in audio-specific validation: {e}")
            results.append(self._create_result(
                category=ValidationCategory.AUDIO,
                message=f"Error in audio-specific validation: {e}",
                severity=ValidationSeverity.ERROR
            ))
        return results

if __name__ == "__main__":
    # Example usage
    validator = TemplateValidator("templates/validation")
    
    # Validate template
    summary = validator.validate_template("test_template", version="v1")
    logger.info(f"Validation successful: {summary.overall_success}")
    for result in summary.results:
        logger.info(f"{result.severity.value}: {result.message}")
    
    # Get validation history
    history = validator.get_validation_history("test_template")
    logger.info(f"Found {len(history)} validation records") 