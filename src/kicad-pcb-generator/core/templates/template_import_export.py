"""
Template import/export functionality for KiCad PCB Generator.

This module provides functionality for importing and exporting templates
in various formats, with support for validation and versioning.
"""

from typing import Dict, List, Any, Optional, Union, TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime
import json
import yaml
import shutil
from pathlib import Path
import logging
from enum import Enum
import re

from ..base.base_manager import BaseManager
from ..base.results.manager_result import ManagerResult, ManagerOperation, ManagerStatus
from .rule_template import RuleTemplate, RuleTemplateData
from .template_versioning import TemplateVersionManager, TemplateVersion
from ..validation.rule_integration import RuleImportFormat
from ...utils.logging.logger import Logger

if TYPE_CHECKING:
    from ..base.results.manager_result import ManagerResult

class TemplateFormat(Enum):
    """Supported template formats."""
    YAML = "yaml"
    JSON = "json"
    KICAD = "kicad"

@dataclass
class TemplateImportResult:
    """Result of a template import operation."""
    success: bool
    imported_templates: List[str]
    skipped_templates: List[str]
    errors: List[str]
    warnings: List[str]

@dataclass
class TemplateImportExportItem:
    """Data structure for template import/export items."""
    template_id: str
    template: RuleTemplate
    format: TemplateFormat
    file_path: str
    import_export_type: str  # "import" or "export"
    status: str = "pending"
    timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Validate required fields and set defaults."""
        if not self.template_id:
            raise ValueError("template_id is required")
        if not isinstance(self.template, RuleTemplate):
            raise ValueError("template must be a RuleTemplate instance")
        if not isinstance(self.format, TemplateFormat):
            raise ValueError("format must be a TemplateFormat enum")
        if not self.file_path:
            raise ValueError("file_path is required")
        if self.import_export_type not in ["import", "export"]:
            raise ValueError("import_export_type must be 'import' or 'export'")
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}

class TemplateImportExportManager(BaseManager[TemplateImportExportItem]):
    """Manages template import and export operations."""
    
    def __init__(
        self,
        storage_path: Union[str, Path],
        version_manager: Optional[TemplateVersionManager] = None,
        logger: Optional[Logger] = None
    ):
        """Initialize the template import/export manager.
        
        Args:
            storage_path: Path to store template data
            version_manager: Optional version manager instance
            logger: Optional logger instance
        """
        super().__init__()
        self.logger = logger or Logger(__name__)
        self.storage_path = Path(storage_path)
        self.version_manager = version_manager
        
        # Create storage directories
        self.import_path = self.storage_path / "imports"
        self.export_path = self.storage_path / "exports"
        self.backup_path = self.storage_path / "backups"
        
        for path in [self.import_path, self.export_path, self.backup_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    def _validate_data(self, data: TemplateImportExportItem) -> ManagerResult:
        """Validate template import/export item data.
        
        Args:
            data: Template import/export item to validate
            
        Returns:
            Manager result
        """
        try:
            # Basic validation
            if not isinstance(data, TemplateImportExportItem):
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Data must be a TemplateImportExportItem instance",
                    errors=["Invalid data type"]
                )
            
            # Validate template ID
            if not data.template_id or not isinstance(data.template_id, str):
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Invalid template ID",
                    errors=["template_id must be a non-empty string"]
                )
            
            # Validate template
            if not isinstance(data.template, RuleTemplate):
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Invalid template",
                    errors=["template must be a RuleTemplate instance"]
                )
            
            # Validate format
            if not isinstance(data.format, TemplateFormat):
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Invalid format",
                    errors=["format must be a TemplateFormat enum"]
                )
            
            # Validate file path
            if not data.file_path or not isinstance(data.file_path, str):
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Invalid file path",
                    errors=["file_path must be a non-empty string"]
                )
            
            # Validate import/export type
            if data.import_export_type not in ["import", "export"]:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Invalid import/export type",
                    errors=["import_export_type must be 'import' or 'export'"]
                )
            
            # Validate template data
            validation_errors = self._validate_template_data(data.template)
            if validation_errors:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Template validation failed",
                    errors=validation_errors
                )
            
            return ManagerResult(
                success=True,
                operation=ManagerOperation.VALIDATE,
                status=ManagerStatus.SUCCESS,
                message="Template import/export item validation successful"
            )
            
        except Exception as e:
            self.logger.error(f"Error validating template import/export item: {e}")
            return ManagerResult(
                success=False,
                operation=ManagerOperation.VALIDATE,
                status=ManagerStatus.FAILED,
                message=f"Validation error: {e}",
                errors=[str(e)]
            )
    
    def _cleanup_item(self, key: str) -> None:
        """Clean up resources for a template import/export item.
        
        Args:
            key: Key of the item to clean up
        """
        try:
            # Remove related files if they exist
            item_result = self.read(key)
            if item_result.success and item_result.data:
                file_path = Path(item_result.data.file_path)
                if file_path.exists():
                    file_path.unlink()
            
            self.logger.debug(f"Cleaned up template import/export item: {key}")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up template import/export item {key}: {e}")
    
    def add_template_import_export(self, template_id: str, template: RuleTemplate, 
                                 format: TemplateFormat, file_path: str, 
                                 import_export_type: str) -> ManagerResult:
        """Add a template import/export item to the manager.
        
        Args:
            template_id: Template ID
            template: Template to import/export
            format: Import/export format
            file_path: File path for import/export
            import_export_type: Type of operation ("import" or "export")
            
        Returns:
            Manager result
        """
        try:
            # Create template import/export item
            item = TemplateImportExportItem(
                template_id=template_id,
                template=template,
                format=format,
                file_path=file_path,
                import_export_type=import_export_type,
                status="active"
            )
            
            # Add to manager
            result = self.create(template_id, item)
            
            if result.success:
                # Save template if it's an import
                if import_export_type == "import":
                    self._save_template(template)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error adding template import/export {template_id}: {e}")
            return ManagerResult(
                success=False,
                operation=ManagerOperation.CREATE,
                status=ManagerStatus.FAILED,
                message=f"Error adding template import/export: {e}",
                errors=[str(e)]
            )
    
    def import_templates(
        self,
        file_path: Union[str, Path],
        format: TemplateFormat,
        validate: bool = True
    ) -> TemplateImportResult:
        """Import templates from a file.
        
        Args:
            file_path: Path to import file
            format: Import format
            validate: Whether to validate templates before importing
            
        Returns:
            Import result
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return TemplateImportResult(
                    success=False,
                    imported_templates=[],
                    skipped_templates=[],
                    errors=[f"File not found: {file_path}"],
                    warnings=[]
                )
            
            # Read file
            with open(file_path, 'r') as f:
                if format == TemplateFormat.YAML:
                    data = yaml.safe_load(f)
                elif format == TemplateFormat.JSON:
                    data = json.load(f)
                elif format == TemplateFormat.KICAD:
                    data = self._parse_kicad_templates(f.read())
                else:
                    return TemplateImportResult(
                        success=False,
                        imported_templates=[],
                        skipped_templates=[],
                        errors=[f"Unsupported format: {format}"],
                        warnings=[]
                    )
            
            # Process templates
            imported_templates = []
            skipped_templates = []
            errors = []
            warnings = []
            
            for template_id, template_data in data.items():
                try:
                    # Convert data to RuleTemplate object
                    template = self._convert_to_template(template_id, template_data)
                    
                    # Validate template
                    if validate:
                        validation_errors = self._validate_template_data(template)
                        if validation_errors:
                            errors.extend(validation_errors)
                            skipped_templates.append(template_id)
                            continue
                    
                    # Add to manager
                    result = self.add_template_import_export(
                        template_id=template_id,
                        template=template,
                        format=format,
                        file_path=str(file_path),
                        import_export_type="import"
                    )
                    
                    if result.success:
                        imported_templates.append(template_id)
                        
                        # Create version if version manager exists
                        if self.version_manager:
                            version = self.version_manager.add_version(
                                template_id=template_id,
                                template=template,
                                change={
                                    "type": "import",
                                    "description": f"Imported from {file_path.name}"
                                }
                            )
                            if not version:
                                warnings.append(f"Failed to create version for template: {template_id}")
                    else:
                        skipped_templates.append(template_id)
                        warnings.append(f"Failed to save template: {template_id}")
                        
                except Exception as e:
                    errors.append(f"Error processing template {template_id}: {str(e)}")
                    skipped_templates.append(template_id)
            
            # Create backup
            if imported_templates:
                self._create_backup()
            
            return TemplateImportResult(
                success=len(errors) == 0,
                imported_templates=imported_templates,
                skipped_templates=skipped_templates,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            self.logger.error(f"Error importing templates: {e}")
            return TemplateImportResult(
                success=False,
                imported_templates=[],
                skipped_templates=[],
                errors=[f"Import error: {str(e)}"],
                warnings=[]
            )
    
    def export_templates(
        self,
        file_path: Union[str, Path],
        format: TemplateFormat,
        template_ids: Optional[List[str]] = None,
        version: Optional[str] = None
    ) -> bool:
        """Export templates to a file.
        
        Args:
            file_path: Path to export file
            format: Export format
            template_ids: List of template IDs to export, or None for all templates
            version: Optional version to export, or None for latest version
            
        Returns:
            True if successful
        """
        try:
            file_path = Path(file_path)
            
            # Get templates to export
            if template_ids:
                templates = {}
                for template_id in template_ids:
                    if version and self.version_manager:
                        # Get specific version
                        version_data = self.version_manager.get_version(template_id, version)
                        if version_data:
                            templates[template_id] = version_data.template
                    else:
                        # Get latest version
                        template = self._load_template(template_id)
                        if template:
                            templates[template_id] = template
            else:
                templates = self._load_all_templates()
            
            # Convert templates to data
            data = {}
            for template_id, template in templates.items():
                if template:
                    data[template_id] = {
                        'name': template.name,
                        'description': template.description,
                        'category': template.category,
                        'type': template.type,
                        'severity': template.severity,
                        'constraints': template.constraints,
                        'dependencies': template.dependencies,
                        'metadata': template.metadata
                    }
                    
                    # Add version info if available
                    if self.version_manager:
                        version_info = self.version_manager.get_version_info(template_id)
                        if version_info:
                            data[template_id]['version'] = version_info
            
            # Write file
            with open(file_path, 'w') as f:
                if format == TemplateFormat.YAML:
                    yaml.dump(data, f, default_flow_style=False)
                elif format == TemplateFormat.JSON:
                    json.dump(data, f, indent=2)
                elif format == TemplateFormat.KICAD:
                    f.write(self._format_kicad_templates(data))
                else:
                    raise ValueError(f"Unsupported format: {format}")
            
            # Add export items to manager
            for template_id, template in templates.items():
                self.add_template_import_export(
                    template_id=template_id,
                    template=template,
                    format=format,
                    file_path=str(file_path),
                    import_export_type="export"
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting templates: {e}")
            return False
    
    def _convert_to_template(self, template_id: str, data: Dict[str, Any]) -> RuleTemplate:
        """Convert data to RuleTemplate object.
        
        Args:
            template_id: Template ID
            data: Template data
            
        Returns:
            RuleTemplate object
        """
        return RuleTemplate(
            id=template_id,
            name=data['name'],
            description=data['description'],
            category=data['category'],
            type=data['type'],
            severity=data['severity'],
            constraints=data['constraints'],
            dependencies=data['dependencies'],
            metadata=data.get('metadata', {}),
            version=data.get('version', {})
        )
    
    def _validate_template_data(self, template: RuleTemplate) -> List[str]:
        """Validate template data.
        
        Args:
            template: Template to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check required fields
        if not template.name:
            errors.append("Template name is required")
        if not template.description:
            errors.append("Template description is required")
        if not template.category:
            errors.append("Template category is required")
        if not template.type:
            errors.append("Template type is required")
        if not template.severity:
            errors.append("Template severity is required")
        
        # Validate constraints
        for param, constraint in template.constraints.items():
            if not isinstance(constraint, dict):
                errors.append(f"Invalid constraint format for parameter {param}")
                continue
            
            if 'min_value' in constraint and 'max_value' in constraint:
                if constraint['min_value'] > constraint['max_value']:
                    errors.append(f"Invalid constraint range for parameter {param}")
            
            if 'allowed_values' in constraint and not isinstance(constraint['allowed_values'], list):
                errors.append(f"Invalid allowed values for parameter {param}")
            
            if 'regex_pattern' in constraint:
                try:
                    import re
                    re.compile(constraint['regex_pattern'])
                except re.error:
                    errors.append(f"Invalid regex pattern for parameter {param}")
        
        return errors
    
    def _create_backup(self) -> None:
        """Create a backup of current templates."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_path / f"backup_{timestamp}.json"
            
            # Export all templates to backup file
            self.export_templates(backup_file, TemplateFormat.JSON)
            
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
    
    def _parse_kicad_templates(self, content: str) -> Dict[str, Any]:
        """Parse KiCad format templates.
        
        Args:
            content: File content in KiCad PCB format
            
        Returns:
            Parsed template data
        """
        try:
            templates = {}
            lines = content.split('\n')
            current_template = None
            current_section = None
            section_data = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check for template start (kicad_pcb section)
                if line.startswith('(kicad_pcb'):
                    if current_template:
                        # Save previous template
                        templates[current_template['id']] = current_template
                    
                    # Start new template
                    current_template = {
                        'id': f"kicad_template_{len(templates) + 1}",
                        'name': 'KiCad PCB Template',
                        'description': 'Template imported from KiCad PCB file',
                        'category': 'pcb',
                        'type': 'kicad_pcb',
                        'severity': 'info',
                        'constraints': {},
                        'dependencies': [],
                        'metadata': {
                            'format': 'kicad_pcb',
                            'import_date': datetime.now().isoformat()
                        },
                        'kicad_data': {}
                    }
                    current_section = 'header'
                    section_data = []
                    continue
                
                if not current_template:
                    continue
                
                # Parse different sections
                if line.startswith('(title'):
                    # Extract title
                    title_match = re.match(r'\(title\s+"([^"]+)"\)')
                    if title_match:
                        current_template['name'] = title_match.group(1)
                elif line.startswith('(general'):
                    current_section = 'general'
                    section_data = []
                elif line.startswith('(setup'):
                    current_section = 'setup'
                    section_data = []
                elif line.startswith('(layers'):
                    current_section = 'layers'
                    section_data = []
                elif line.startswith('(net_class'):
                    current_section = 'net_class'
                    section_data = []
                elif line.startswith('(module'):
                    current_section = 'module'
                    section_data = []
                elif line.startswith(')'):
                    # End of section
                    if current_section and section_data:
                        current_template['kicad_data'][current_section] = section_data
                        current_section = None
                        section_data = []
                else:
                    # Add line to current section
                    if current_section:
                        section_data.append(line)
            
            # Save last template
            if current_template:
                templates[current_template['id']] = current_template
            
            # Extract constraints from KiCad data
            for template_id, template in templates.items():
                if 'setup' in template['kicad_data']:
                    setup_data = template['kicad_data']['setup']
                    constraints = {}
                    
                    for line in setup_data:
                        if 'trace_width' in line:
                            # Extract trace width constraints
                            width_match = re.search(r'trace_width\s+([0-9.]+)', line)
                            if width_match:
                                width = float(width_match.group(1))
                                constraints['trace_width'] = {
                                    'min_value': width * 0.5,
                                    'max_value': width * 2.0,
                                    'default_value': width
                                }
                        
                        if 'clearance' in line:
                            # Extract clearance constraints
                            clearance_match = re.search(r'clearance\s+([0-9.]+)', line)
                            if clearance_match:
                                clearance = float(clearance_match.group(1))
                                constraints['clearance'] = {
                                    'min_value': clearance * 0.5,
                                    'max_value': clearance * 2.0,
                                    'default_value': clearance
                                }
                    
                    template['constraints'] = constraints
            
            return templates
            
        except Exception as e:
            self.logger.error(f"Error parsing KiCad templates: {e}")
            return {}
    
    def _format_kicad_templates(self, data: Dict[str, Any]) -> str:
        """Format templates to KiCad format.
        
        Args:
            data: Template data
            
        Returns:
            Formatted string in KiCad PCB format
        """
        try:
            output_lines = []
            
            for template_id, template_data in data.items():
                # Start KiCad PCB section
                output_lines.append('(kicad_pcb (version 20211123) (generator pcbnew)')
                output_lines.append('')
                
                # Add basic PCB information
                output_lines.append(f'  (paper "A4")')
                output_lines.append(f'  (title "{template_data.get("name", "Generated Template")}")')
                output_lines.append(f'  (date "{datetime.now().strftime("%Y-%m-%d")}")')
                output_lines.append(f'  (rev "1.0")')
                output_lines.append(f'  (company "KiCad PCB Generator")')
                output_lines.append(f'  (host pcbnew "7.0.0")')
                output_lines.append('')
                
                # Add general section
                output_lines.append('  (general')
                output_lines.append('    (thickness 1.6)')
                output_lines.append('    (drawings 0)')
                output_lines.append('    (tracks 0)')
                output_lines.append('    (zones 0)')
                output_lines.append('    (modules 0)')
                output_lines.append('    (nets 0)')
                output_lines.append('  )')
                output_lines.append('')
                
                # Add page section
                output_lines.append('  (page "A4")')
                output_lines.append('')
                
                # Add layers section
                output_lines.append('  (layers')
                output_lines.append('    (0 "F.Cu" signal)')
                output_lines.append('    (1 "In1.Cu" signal)')
                output_lines.append('    (2 "In2.Cu" signal)')
                output_lines.append('    (3 "B.Cu" signal)')
                output_lines.append('    (4 "F.Adhes" user)')
                output_lines.append('    (5 "B.Adhes" user)')
                output_lines.append('    (6 "F.Paste" user)')
                output_lines.append('    (7 "B.Paste" user)')
                output_lines.append('    (8 "F.SilkS" user)')
                output_lines.append('    (9 "B.SilkS" user)')
                output_lines.append('    (10 "F.Mask" user)')
                output_lines.append('    (11 "B.Mask" user)')
                output_lines.append('    (12 "Edge.Cuts" user)')
                output_lines.append('    (13 "Eco1.User" user)')
                output_lines.append('    (14 "Eco2.User" user)')
                output_lines.append('    (15 "Margin" user)')
                output_lines.append('    (16 "F.CrtYd" user)')
                output_lines.append('    (17 "B.CrtYd" user)')
                output_lines.append('    (18 "F.Fab" user)')
                output_lines.append('    (19 "B.Fab" user)')
                output_lines.append('  )')
                output_lines.append('')
                
                # Add setup section with constraints
                output_lines.append('  (setup')
                constraints = template_data.get('constraints', {})
                
                # Trace width
                trace_width = constraints.get('trace_width', {}).get('default_value', 0.25)
                output_lines.append(f'    (last_trace_width {trace_width})')
                
                # Clearance
                clearance = constraints.get('clearance', {}).get('default_value', 0.2)
                output_lines.append(f'    (trace_clearance {clearance})')
                
                # Other default values
                output_lines.append('    (zone_clearance 0.508)')
                output_lines.append('    (zone_45_only no)')
                output_lines.append(f'    (trace_min {trace_width * 0.8})')
                output_lines.append(f'    (segment_width {trace_width})')
                output_lines.append('    (edge_width 0.1)')
                output_lines.append('    (via_size 0.8)')
                output_lines.append('    (via_drill 0.4)')
                output_lines.append('    (via_min_size 0.4)')
                output_lines.append('    (via_min_drill 0.3)')
                output_lines.append('    (uvia_size 0.3)')
                output_lines.append('    (uvia_drill 0.1)')
                output_lines.append('    (uvias_allowed no)')
                output_lines.append('    (uvia_min_size 0.2)')
                output_lines.append('    (uvia_min_drill 0.1)')
                output_lines.append('    (pcb_text_width 0.3)')
                output_lines.append('    (pcb_text_size 1.5 1.5)')
                output_lines.append('    (mod_edge_width 0.12)')
                output_lines.append('    (mod_text_size 1 1)')
                output_lines.append('    (mod_text_width 0.15)')
                output_lines.append('    (pad_size 1.5 1.5)')
                output_lines.append('    (pad_drill 0.6)')
                output_lines.append('    (pad_to_mask_clearance 0.051)')
                output_lines.append('    (solder_mask_min_width 0.25)')
                output_lines.append('    (aux_axis_origin 0 0)')
                output_lines.append('    (visible_elements "FFFFFF7F")')
                
                # Add plot parameters
                output_lines.append('    (pcbplotparams')
                output_lines.append('      (layerselection 0x00010_80000001)')
                output_lines.append('      (usegerberextensions false)')
                output_lines.append('      (usegerberattributes false)')
                output_lines.append('      (usegerberadvancedattributes false)')
                output_lines.append('      (creategerberjobfile false)')
                output_lines.append('      (excludeedgelayer true)')
                output_lines.append('      (linewidth 0.100000)')
                output_lines.append('      (plotframeref false)')
                output_lines.append('      (viasonmask false)')
                output_lines.append('      (mode 1)')
                output_lines.append('      (useauxorigin false)')
                output_lines.append('      (hpglpennumber 1)')
                output_lines.append('      (hpglpenspeed 20)')
                output_lines.append('      (hpglpendiameter 15.000000)')
                output_lines.append('      (hpglpenoverlay 2)')
                output_lines.append('      (psnegative false)')
                output_lines.append('      (psa4output false)')
                output_lines.append('      (plotreference true)')
                output_lines.append('      (plotvalue true)')
                output_lines.append('      (plotinvisibletext false)')
                output_lines.append('      (padsonsilk false)')
                output_lines.append('      (subtractmaskfromsilk false)')
                output_lines.append('      (outputformat 1)')
                output_lines.append('      (mirror false)')
                output_lines.append('      (drillshape 1)')
                output_lines.append('      (scaleselection 1)')
                output_lines.append('      (outputdirectory ""))')
                output_lines.append('  )')
                output_lines.append('')
                
                # Add basic nets
                output_lines.append('  (net 0 "")')
                output_lines.append('  (net 1 "GND")')
                output_lines.append('  (net 2 "+12V")')
                output_lines.append('  (net 3 "-12V")')
                output_lines.append('  (net 4 "AUDIO_IN")')
                output_lines.append('  (net 5 "AUDIO_OUT")')
                output_lines.append('')
                
                # Add net class
                output_lines.append('  (net_class Default "This is the default net class."')
                output_lines.append(f'    (clearance {clearance})')
                output_lines.append(f'    (trace_width {trace_width})')
                output_lines.append('    (via_dia 0.8)')
                output_lines.append('    (via_drill 0.4)')
                output_lines.append('    (uvia_dia 0.3)')
                output_lines.append('    (uvia_drill 0.1)')
                output_lines.append('    (add_net "GND")')
                output_lines.append('    (add_net "+12V")')
                output_lines.append('    (add_net "-12V")')
                output_lines.append('    (add_net "AUDIO_IN")')
                output_lines.append('    (add_net "AUDIO_OUT")')
                output_lines.append('  )')
                output_lines.append('')
                
                # Add template metadata as comment
                output_lines.append(f'  ;; Template: {template_data.get("name", "Unknown")}')
                output_lines.append(f'  ;; Description: {template_data.get("description", "No description")}')
                output_lines.append(f'  ;; Category: {template_data.get("category", "Unknown")}')
                output_lines.append(f'  ;; Type: {template_data.get("type", "Unknown")}')
                output_lines.append(f'  ;; Generated: {datetime.now().isoformat()}')
                output_lines.append('')
                
                # End KiCad PCB section
                output_lines.append(')')
                output_lines.append('')
            
            return '\n'.join(output_lines)
            
        except Exception as e:
            self.logger.error(f"Error formatting KiCad templates: {e}")
            return str(data)
    
    def _save_template(self, template: RuleTemplate) -> bool:
        """Save a template to storage.
        
        Args:
            template: Template to save
            
        Returns:
            True if successful
        """
        try:
            template_file = self.storage_path / f"{template.id}.json"
            with open(template_file, 'w') as f:
                json.dump(template.__dict__, f, indent=2, default=str)
            return True
        except Exception as e:
            self.logger.error(f"Error saving template: {e}")
            return False
    
    def _load_template(self, template_id: str) -> Optional[RuleTemplate]:
        """Load a template from storage.
        
        Args:
            template_id: Template ID
            
        Returns:
            Template if found
        """
        try:
            template_file = self.storage_path / f"{template_id}.json"
            if not template_file.exists():
                return None
            
            with open(template_file, 'r') as f:
                data = json.load(f)
                return RuleTemplate(**data)
        except Exception as e:
            self.logger.error(f"Error loading template: {e}")
            return None
    
    def _load_all_templates(self) -> Dict[str, RuleTemplate]:
        """Load all templates from storage.
        
        Returns:
            Dictionary of templates
        """
        templates = {}
        for template_file in self.storage_path.glob("*.json"):
            try:
                template_id = template_file.stem
                template = self._load_template(template_id)
                if template:
                    templates[template_id] = template
            except Exception as e:
                self.logger.error(f"Error loading template {template_file}: {e}")
        return templates 