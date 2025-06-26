"""Rule template system for KiCad PCB Generator."""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import logging

from .template_versioning import TemplateVersionManager, TemplateVersion
from ...utils.logging.logger import Logger

@dataclass
class RuleTemplateData:
    """Data for a rule template."""
    name: str
    description: str
    category: str
    type: str
    severity: str
    constraints: Dict[str, Any]
    dependencies: List[str]
    metadata: Dict[str, Any]

class RuleTemplate:
    """Manages rule templates."""
    
    def __init__(
        self,
        storage_path: Union[str, Path],
        version_manager: Optional[TemplateVersionManager] = None,
        logger: Optional[Logger] = None
    ):
        """Initialize rule template manager.
        
        Args:
            storage_path: Path to store rule templates
            version_manager: Optional version manager instance
            logger: Optional logger instance
        """
        self.logger = logger or Logger(__name__)
        self.storage_path = Path(storage_path)
        self.version_manager = version_manager
        
        # Create storage directory
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def create_rule_template(
        self,
        data: RuleTemplateData,
        template_id: Optional[str] = None
    ) -> Optional[str]:
        """Create a new rule template.
        
        Args:
            data: Template data
            template_id: Optional template ID, generated if not provided
            
        Returns:
            Template ID if successful
        """
        try:
            # Generate template ID if not provided
            if not template_id:
                template_id = self._generate_template_id(data.name)
            
            # Create template
            template = {
                'id': template_id,
                'name': data.name,
                'description': data.description,
                'category': data.category,
                'type': data.type,
                'severity': data.severity,
                'constraints': data.constraints,
                'dependencies': data.dependencies,
                'metadata': data.metadata,
                'created_at': datetime.now().isoformat(),
                'created_by': data.metadata.get('author', 'unknown')
            }
            
            # Save template
            template_file = self.storage_path / f"{template_id}.json"
            with open(template_file, 'w') as f:
                json.dump(template, f, indent=2)
            
            # Create version if version manager exists
            if self.version_manager:
                version = self.version_manager.add_version(
                    template_id=template_id,
                    template=template,
                    change={
                        "type": "create",
                        "description": "Initial version"
                    }
                )
                if not version:
                    self.logger.warning(f"Failed to create version for template: {template_id}")
            
            return template_id
            
        except Exception as e:
            self.logger.error(f"Failed to create rule template: {e}")
            return None
    
    def get_rule_template(
        self,
        template_id: str,
        version: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get a rule template.
        
        Args:
            template_id: Template ID
            version: Optional version to get, or None for latest version
            
        Returns:
            Template data if found
        """
        try:
            if version and self.version_manager:
                # Get specific version
                version_data = self.version_manager.get_version(template_id, version)
                if version_data:
                    return version_data.template
            
            # Get latest version
            template_file = self.storage_path / f"{template_id}.json"
            if not template_file.exists():
                return None
            
            with open(template_file, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            self.logger.error(f"Failed to get rule template: {e}")
            return None
    
    def update_rule_template(
        self,
        template_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update a rule template.
        
        Args:
            template_id: Template ID
            updates: Template updates
            
        Returns:
            True if successful
        """
        try:
            # Get current template
            template = self.get_rule_template(template_id)
            if not template:
                return False
            
            # Update template
            template.update(updates)
            template['updated_at'] = datetime.now().isoformat()
            template['updated_by'] = updates.get('metadata', {}).get('author', 'unknown')
            
            # Save template
            template_file = self.storage_path / f"{template_id}.json"
            with open(template_file, 'w') as f:
                json.dump(template, f, indent=2)
            
            # Create version if version manager exists
            if self.version_manager:
                version = self.version_manager.add_version(
                    template_id=template_id,
                    template=template,
                    change={
                        "type": "update",
                        "description": updates.get('description', 'Template updated')
                    }
                )
                if not version:
                    self.logger.warning(f"Failed to create version for template update: {template_id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update rule template: {e}")
            return False
    
    def delete_rule_template(self, template_id: str) -> bool:
        """Delete a rule template.
        
        Args:
            template_id: Template ID
            
        Returns:
            True if successful
        """
        try:
            template_file = self.storage_path / f"{template_id}.json"
            if not template_file.exists():
                return False
            
            # Get template for versioning
            template = self.get_rule_template(template_id)
            
            # Delete template
            template_file.unlink()
            
            # Create version if version manager exists
            if self.version_manager and template:
                version = self.version_manager.add_version(
                    template_id=template_id,
                    template=template,
                    change={
                        "type": "delete",
                        "description": "Template deleted"
                    }
                )
                if not version:
                    self.logger.warning(f"Failed to create version for template deletion: {template_id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete rule template: {e}")
            return False
    
    def list_rule_templates(
        self,
        category: Optional[str] = None,
        type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List rule templates.
        
        Args:
            category: Optional category filter
            type: Optional type filter
            
        Returns:
            List of template data
        """
        try:
            templates = []
            for template_file in self.storage_path.glob("*.json"):
                try:
                    with open(template_file, 'r') as f:
                        template = json.load(f)
                        
                        # Apply filters
                        if category and template['category'] != category:
                            continue
                        if type and template['type'] != type:
                            continue
                            
                        templates.append(template)
                        
                except Exception as e:
                    self.logger.error(f"Failed to load template {template_file}: {e}")
            
            return templates
            
        except Exception as e:
            self.logger.error(f"Failed to list rule templates: {e}")
            return []
    
    def _generate_template_id(self, name: str) -> str:
        """Generate a template ID from a name.
        
        Args:
            name: Template name
            
        Returns:
            Generated template ID
        """
        # Convert name to lowercase and replace spaces with underscores
        template_id = name.lower().replace(' ', '_')
        
        # Add timestamp to ensure uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{template_id}_{timestamp}"

if __name__ == "__main__":
    # Example usage
    rule_template = RuleTemplate("templates/rules")
    
    # Create template
    data = RuleTemplateData(
        name="Minimum Trace Width",
        description="Minimum trace width constraint",
        category="safety",
        type="constraint",
        severity="error",
        constraints={
            "min_width": {
                "min_value": 0.2,
                "max_value": 1.0
            }
        },
        dependencies=[],
        metadata={
            "author": "Test User",
            "tags": ["safety", "trace"]
        }
    )
    
    template_id = rule_template.create_rule_template(data)
    if template_id:
        logger.info(f"Created template: {template_id}")
        
        # Get template
        template = rule_template.get_rule_template(template_id)
        logger.info(f"Template: {template}")
        
        # Update template
        updates = {
            "description": "Updated description",
            "metadata": {
                "author": "Test User",
                "tags": ["safety", "trace", "updated"]
            }
        }
        if rule_template.update_rule_template(template_id, updates):
            logger.info("Template updated")
            
        # List templates
        templates = rule_template.list_rule_templates(category="safety")
        logger.info(f"Found {len(templates)} safety templates")
        
        # Delete template
        if rule_template.delete_rule_template(template_id):
            logger.info("Template deleted") 