"""Integration layer for template management system."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, TYPE_CHECKING
from datetime import datetime
from dataclasses import dataclass

import pcbnew
from .template_versioning import TemplateVersionManager, TemplateVersion
from .template_import_export import TemplateImportExportManager, TemplateFormat
from .rule_template import RuleTemplate, RuleTemplateData
from ..validation.base_validator import ValidationCategory
from ..base.base_manager import BaseManager
from ..base.results.manager_result import ManagerResult
from ...utils.semantic_version import SemanticVersion

if TYPE_CHECKING:
    from ..base.results.manager_result import ManagerResult

logger = logging.getLogger(__name__)

@dataclass
class TemplateIntegrationItem:
    """Data structure for template integration items."""
    id: str
    template_id: str
    version: str
    board: Optional[Any] = None
    metadata: Dict[str, Any] = None
    rule_templates: List[RuleTemplateData] = None
    status: str = "pending"  # pending, processing, completed, failed
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    validation_results: Dict[str, Any] = None

class TemplateIntegrationManager(BaseManager[TemplateIntegrationItem]):
    """Manages integration between template components."""
    
    def __init__(
        self,
        base_path: Union[str, Path],
        version_manager: Optional[TemplateVersionManager] = None,
        import_export_manager: Optional[TemplateImportExportManager] = None,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize template integration manager.
        
        Args:
            base_path: Base path for template data
            version_manager: Optional version manager instance
            import_export_manager: Optional import/export manager instance
            logger: Optional logger instance
        """
        super().__init__(logger=logger or logging.getLogger(__name__))
        self.base_path = Path(base_path)
        
        # Initialize managers
        self.version_manager = version_manager or TemplateVersionManager(
            str(self.base_path / "versions")
        )
        self.import_export_manager = import_export_manager or TemplateImportExportManager(
            str(self.base_path / "templates")
        )
        
        # Initialize rule template system
        self.rule_template = RuleTemplate(str(self.base_path / "rules"))
    
    def _validate_data(self, item: TemplateIntegrationItem) -> bool:
        """Validate template integration item data."""
        if not item.id or not isinstance(item.id, str):
            self.logger.error("Template integration item must have a valid string ID")
            return False
        
        if not item.template_id or not isinstance(item.template_id, str):
            self.logger.error("Template integration item must have a valid template ID")
            return False
        
        if not item.version or not isinstance(item.version, str):
            self.logger.error("Template integration item must have a valid version")
            return False
        
        if item.metadata and not isinstance(item.metadata, dict):
            self.logger.error("Template integration item must have valid metadata")
            return False
        
        if item.rule_templates and not isinstance(item.rule_templates, list):
            self.logger.error("Template integration item must have valid rule templates list")
            return False
        
        return True
    
    def _cleanup_item(self, item: TemplateIntegrationItem) -> None:
        """Clean up template integration item resources."""
        try:
            # Clean up any temporary files or resources
            if item.board:
                # Currently nothing to free explicitly. Placeholder retained for extensibility.
                self.logger.debug("Board cleanup placeholder for template integration '%s'", item.id)
            
            self.logger.debug(f"Cleaned up template integration item: {item.id}")
        except Exception as e:
            self.logger.warning(f"Error during template integration item cleanup: {str(e)}")
    
    def _clear_cache(self) -> None:
        """Clear template integration manager cache."""
        try:
            # Clear any cached template data or temporary files
            self.logger.debug("Cleared template integration manager cache")
        except Exception as e:
            self.logger.warning(f"Error clearing template integration manager cache: {str(e)}")
    
    def create_template_integration_job(self, 
                                       template_id: str, 
                                       version: str, 
                                       metadata: Dict[str, Any] = None,
                                       rule_templates: List[RuleTemplateData] = None) -> ManagerResult[TemplateIntegrationItem]:
        """Create a new template integration job."""
        try:
            integration_id = f"integration_{template_id}_{version}"
            integration_item = TemplateIntegrationItem(
                id=integration_id,
                template_id=template_id,
                version=version,
                metadata=metadata or {},
                rule_templates=rule_templates or [],
                status="pending",
                validation_results={}
            )
            
            result = self.create(integration_item)
            if result.success:
                self.logger.info(f"Created template integration job: {integration_id}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error creating template integration job: {str(e)}")
            return ManagerResult[TemplateIntegrationItem](
                success=False,
                error_message=str(e),
                data=None
            )
    
    def create_template_version(
        self,
        template_id: str,
        board: pcbnew.BOARD,
        metadata: Dict[str, Any],
        rule_templates: Optional[List[RuleTemplateData]] = None
    ) -> bool:
        """Create a new version of a template with integrated components.
        
        Args:
            template_id: Template ID
            board: KiCad board object
            metadata: Version metadata
            rule_templates: Optional list of rule templates
            
        Returns:
            True if successful
        """
        try:
            # Create version in version manager
            version = self.version_manager.add_version(
                template_id=template_id,
                template=board,
                change=metadata.get("change"),
                board=board
            )
            
            # Save rule templates if provided
            if rule_templates:
                for rule in rule_templates:
                    self.rule_template.create_rule_template(rule)
            
            # Export template
            export_path = self.base_path / "exports" / f"{template_id}_{version.version}"
            success = self.import_export_manager.export_templates(
                str(export_path),
                TemplateFormat.JSON,
                template_ids=[template_id]
            )
            
            if not success:
                self.logger.error(f"Failed to export template {template_id}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create template version: {e}")
            return False
    
    def process_template_integration_job(self, integration_id: str) -> ManagerResult[TemplateIntegrationItem]:
        """Process a template integration job."""
        try:
            # Get the integration item
            result = self.get(integration_id)
            if not result.success or not result.data:
                return ManagerResult[TemplateIntegrationItem](
                    success=False,
                    error_message=f"Template integration job not found: {integration_id}",
                    data=None
                )
            
            integration_item = result.data
            
            # Update status to processing
            integration_item.status = "processing"
            self.update(integration_item)
            
            # Validate template version
            validation_results = self.validate_template_version(
                integration_item.template_id,
                integration_item.version
            )
            
            # Update integration item with validation results
            integration_item.validation_results = validation_results
            integration_item.status = "completed" if validation_results.get("overall_status", False) else "failed"
            if not validation_results.get("overall_status", False):
                integration_item.error_message = "Template integration validation failed"
            
            # Update the item
            update_result = self.update(integration_item)
            if update_result.success:
                self.logger.info(f"Processed template integration job: {integration_id}")
            
            return update_result
            
        except Exception as e:
            self.logger.error(f"Error processing template integration job {integration_id}: {str(e)}")
            return ManagerResult[TemplateIntegrationItem](
                success=False,
                error_message=str(e),
                data=None
            )
    
    def get_template_version(
        self,
        template_id: str,
        version: str
    ) -> Optional[Dict[str, Any]]:
        """Get a specific version of a template with all components.
        
        Args:
            template_id: Template ID
            version: Version to get
            
        Returns:
            Dictionary containing template data and components
        """
        try:
            # Get version from version manager
            template_version = self.version_manager.get_version(template_id, version)
            if not template_version:
                return None
            
            # Get rule templates
            rule_templates = []
            for rule_name in template_version.metadata.get("rule_templates", []):
                rule = self.rule_template.get_rule_template(rule_name)
                if rule:
                    rule_templates.append(rule)
            
            return {
                "version": template_version,
                "board": template_version.board,
                "rule_templates": rule_templates,
                "metadata": template_version.metadata
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get template version: {e}")
            return None
    
    def import_template_version(
        self,
        file_path: Union[str, Path],
        format: TemplateFormat = TemplateFormat.JSON
    ) -> Optional[Dict[str, Any]]:
        """Import a template version with all components.
        
        Args:
            file_path: Path to import file
            format: Import format
            
        Returns:
            Dictionary containing imported template data
        """
        try:
            # Import template
            result = self.import_export_manager.import_templates(
                str(file_path),
                format
            )
            
            if not result.success:
                self.logger.error(f"Import failed: {result.errors}")
                return None
            
            # Get imported template
            template_id = result.imported_templates[0]
            template = self.import_export_manager._load_template(template_id)
            
            if not template:
                return None
            
            # Create version
            version = self.version_manager.add_version(
                template_id=template_id,
                template=template,
                change={"type": "import", "description": "Imported template"}
            )
            
            return {
                "template": template,
                "version": version,
                "metadata": template.metadata
            }
            
        except Exception as e:
            self.logger.error(f"Failed to import template version: {e}")
            return None
    
    def validate_template_version(
        self,
        template_id: str,
        version: str
    ) -> Dict[str, Any]:
        """Validate a template version with all components.
        
        Args:
            template_id: Template ID
            version: Version to validate
            
        Returns:
            Dictionary of validation results
        """
        try:
            # Get template version
            template_data = self.get_template_version(template_id, version)
            if not template_data:
                return {"error": "Template version not found"}
            
            validation_results = {
                "version": version,
                "board_validation": {},
                "rule_validation": {},
                "overall_status": True
            }
            
            # Validate board
            board = template_data["board"]
            if board:
                drc = pcbnew.DRC()
                drc.RunDRC()
                validation_results["board_validation"]["drc"] = not drc.HasErrors()
                
                erc = pcbnew.ERC()
                erc.RunERC()
                validation_results["board_validation"]["erc"] = not erc.HasErrors()
            
            # Validate rule templates
            for rule in template_data["rule_templates"]:
                rule_validation = self.rule_template.validate_rule_template(rule)
                validation_results["rule_validation"][rule.name] = rule_validation
            
            # Calculate overall status
            validation_results["overall_status"] = (
                validation_results["board_validation"].get("drc", False) and
                validation_results["board_validation"].get("erc", False) and
                all(validation_results["rule_validation"].values())
            )
            
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Failed to validate template version: {e}")
            return {"error": str(e)}
    
    def get_template_history(
        self,
        template_id: str
    ) -> List[Dict[str, Any]]:
        """Get complete history of a template with all components.
        
        Args:
            template_id: Template ID
            
        Returns:
            List of version history entries
        """
        try:
            # Get version history
            versions = self.version_manager.get_version_history(template_id)
            
            history = []
            for version in versions:
                # Get rule templates for this version
                rule_templates = []
                for rule_name in version.metadata.get("rule_templates", []):
                    rule = self.rule_template.get_rule_template(rule_name)
                    if rule:
                        rule_templates.append(rule)
                
                history.append({
                    "version": version.version,
                    "timestamp": version.timestamp,
                    "changes": version.changes,
                    "rule_templates": rule_templates,
                    "metadata": version.metadata,
                    "validation_status": version.validation_status
                })
            
            return history
            
        except Exception as e:
            self.logger.error(f"Failed to get template history: {e}")
            return [] 