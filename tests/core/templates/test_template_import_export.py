"""Tests for template import/export functionality."""
import pytest
import json
import yaml
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch

from kicad_pcb_generator.core.templates.template_import_export import (
    TemplateImportExportManager,
    TemplateFormat,
    TemplateImportResult
)
from kicad_pcb_generator.core.templates.rule_template import RuleTemplate, RuleTemplateData
from kicad_pcb_generator.core.templates.template_versioning import (
    TemplateVersionManager,
    TemplateVersion
)

@pytest.fixture
def storage_path(tmp_path):
    """Create temporary storage path."""
    return tmp_path

@pytest.fixture
def manager(storage_path):
    """Create template import/export manager."""
    return TemplateImportExportManager(storage_path)

@pytest.fixture
def template_data():
    """Create test template data."""
    return {
        'test_template': {
            'name': 'Test Template',
            'description': 'Test template description',
            'category': 'safety',
            'type': 'constraint',
            'severity': 'error',
            'constraints': {
                'min_width': {
                    'min_value': 0.2,
                    'max_value': 1.0,
                    'allowed_values': None,
                    'regex_pattern': None
                }
            },
            'dependencies': [],
            'metadata': {
                'author': 'Test Author',
                'version': '1.0.0'
            },
            'version': {
                'version': '1.0.0',
                'created_at': datetime.now().isoformat(),
                'created_by': 'Test Author',
                'changes': ['Initial version'],
                'deprecated': False,
                'deprecated_at': None,
                'deprecated_by': None
            }
        }
    }

def test_init(manager, storage_path):
    """Test manager initialization."""
    assert manager.storage_path == storage_path
    assert (storage_path / "imports").exists()
    assert (storage_path / "exports").exists()
    assert (storage_path / "backups").exists()

def test_import_templates_json(manager, template_data, tmp_path):
    """Test importing templates from JSON."""
    # Create test file
    file_path = tmp_path / "templates.json"
    with open(file_path, 'w') as f:
        json.dump(template_data, f)
    
    # Import templates
    result = manager.import_templates(file_path, TemplateFormat.JSON)
    
    # Check result
    assert result.success
    assert len(result.imported_templates) == 1
    assert result.imported_templates[0] == 'test_template'
    assert not result.skipped_templates
    assert not result.errors
    assert not result.warnings
    
    # Check template was saved
    template = manager._load_template('test_template')
    assert template is not None
    assert template.name == 'Test Template'
    assert template.description == 'Test template description'
    assert template.category == 'safety'
    assert template.type == 'constraint'
    assert template.severity == 'error'

def test_import_templates_yaml(manager, template_data, tmp_path):
    """Test importing templates from YAML."""
    # Create test file
    file_path = tmp_path / "templates.yaml"
    with open(file_path, 'w') as f:
        yaml.dump(template_data, f)
    
    # Import templates
    result = manager.import_templates(file_path, TemplateFormat.YAML)
    
    # Check result
    assert result.success
    assert len(result.imported_templates) == 1
    assert result.imported_templates[0] == 'test_template'
    assert not result.skipped_templates
    assert not result.errors
    assert not result.warnings

def test_import_templates_invalid_format(manager, tmp_path):
    """Test importing templates with invalid format."""
    # Create test file
    file_path = tmp_path / "templates.txt"
    with open(file_path, 'w') as f:
        f.write("invalid format")
    
    # Import templates
    result = manager.import_templates(file_path, TemplateFormat.KICAD)
    
    # Check result
    assert not result.success
    assert not result.imported_templates
    assert not result.skipped_templates
    assert len(result.errors) == 1
    assert "KiCad template format not implemented" in result.errors[0]

def test_import_templates_validation(manager, tmp_path):
    """Test template validation during import."""
    # Create invalid template data
    invalid_data = {
        'test_template': {
            'name': '',  # Missing required field
            'description': 'Test template description',
            'category': 'safety',
            'type': 'constraint',
            'severity': 'error',
            'constraints': {
                'min_width': {
                    'min_value': 1.0,  # Invalid range
                    'max_value': 0.2,
                    'allowed_values': None,
                    'regex_pattern': None
                }
            },
            'dependencies': [],
            'metadata': {}
        }
    }
    
    # Create test file
    file_path = tmp_path / "templates.json"
    with open(file_path, 'w') as f:
        json.dump(invalid_data, f)
    
    # Import templates
    result = manager.import_templates(file_path, TemplateFormat.JSON)
    
    # Check result
    assert not result.success
    assert not result.imported_templates
    assert len(result.skipped_templates) == 1
    assert len(result.errors) == 2
    assert "Template name is required" in result.errors
    assert "Invalid constraint range" in result.errors

def test_export_templates_json(manager, template_data, tmp_path):
    """Test exporting templates to JSON."""
    # Import test template
    file_path = tmp_path / "templates.json"
    with open(file_path, 'w') as f:
        json.dump(template_data, f)
    manager.import_templates(file_path, TemplateFormat.JSON)
    
    # Export templates
    export_path = tmp_path / "export.json"
    success = manager.export_templates(export_path, TemplateFormat.JSON)
    
    # Check result
    assert success
    assert export_path.exists()
    
    # Check exported data
    with open(export_path) as f:
        exported_data = json.load(f)
    assert 'test_template' in exported_data
    assert exported_data['test_template']['name'] == 'Test Template'

def test_export_templates_yaml(manager, template_data, tmp_path):
    """Test exporting templates to YAML."""
    # Import test template
    file_path = tmp_path / "templates.json"
    with open(file_path, 'w') as f:
        json.dump(template_data, f)
    manager.import_templates(file_path, TemplateFormat.JSON)
    
    # Export templates
    export_path = tmp_path / "export.yaml"
    success = manager.export_templates(export_path, TemplateFormat.YAML)
    
    # Check result
    assert success
    assert export_path.exists()
    
    # Check exported data
    with open(export_path) as f:
        exported_data = yaml.safe_load(f)
    assert 'test_template' in exported_data
    assert exported_data['test_template']['name'] == 'Test Template'

def test_export_templates_selection(manager, template_data, tmp_path):
    """Test exporting selected templates."""
    # Import test template
    file_path = tmp_path / "templates.json"
    with open(file_path, 'w') as f:
        json.dump(template_data, f)
    manager.import_templates(file_path, TemplateFormat.JSON)
    
    # Export selected template
    export_path = tmp_path / "export.json"
    success = manager.export_templates(
        export_path,
        TemplateFormat.JSON,
        template_ids=['test_template']
    )
    
    # Check result
    assert success
    assert export_path.exists()
    
    # Check exported data
    with open(export_path) as f:
        exported_data = json.load(f)
    assert 'test_template' in exported_data
    assert len(exported_data) == 1

def test_export_templates_invalid_format(manager, template_data, tmp_path):
    """Test exporting templates with invalid format."""
    # Import test template
    file_path = tmp_path / "templates.json"
    with open(file_path, 'w') as f:
        json.dump(template_data, f)
    manager.import_templates(file_path, TemplateFormat.JSON)
    
    # Export templates
    export_path = tmp_path / "export.txt"
    success = manager.export_templates(export_path, TemplateFormat.KICAD)
    
    # Check result
    assert not success

def test_backup_creation(manager, template_data, tmp_path):
    """Test backup creation during import."""
    # Create test file
    file_path = tmp_path / "templates.json"
    with open(file_path, 'w') as f:
        json.dump(template_data, f)
    
    # Import templates
    result = manager.import_templates(file_path, TemplateFormat.JSON)
    
    # Check backup was created
    backup_dirs = list(manager.backup_path.glob("backup_*"))
    assert len(backup_dirs) == 1
    assert backup_dirs[0].is_dir()
    
    # Check backup contains template
    template_files = list(backup_dirs[0].glob("*.json"))
    assert len(template_files) == 1

def test_import_templates_with_versioning(manager, template_data, tmp_path):
    """Test importing templates with versioning."""
    # Create test file
    file_path = tmp_path / "templates.json"
    with open(file_path, 'w') as f:
        json.dump(template_data, f)
    
    # Mock version creation
    version_manager = MagicMock(spec=TemplateVersionManager)
    version = MagicMock(spec=TemplateVersion)
    version_manager.add_version.return_value = version
    
    # Import templates
    result = manager.import_templates(file_path, TemplateFormat.JSON)
    
    # Check result
    assert result.success
    assert len(result.imported_templates) == 1
    assert result.imported_templates[0] == 'test_template'
    assert not result.skipped_templates
    assert not result.errors
    assert not result.warnings
    
    # Check version was created
    version_manager.add_version.assert_called_once()
    call_args = version_manager.add_version.call_args[1]
    assert call_args['template_id'] == 'test_template'
    assert call_args['change']['type'] == 'import'
    assert 'Imported from templates.json' in call_args['change']['description']
    
    # Check template was saved
    template = manager._load_template('test_template')
    assert template is not None
    assert template.name == 'Test Template'
    assert template.description == 'Test template description'
    assert template.category == 'safety'
    assert template.type == 'constraint'
    assert template.severity == 'error'

def test_import_templates_without_versioning(manager, template_data, tmp_path):
    """Test importing templates without versioning."""
    # Create manager without version manager
    manager = TemplateImportExportManager(str(tmp_path))
    
    # Create test file
    file_path = tmp_path / "templates.json"
    with open(file_path, 'w') as f:
        json.dump(template_data, f)
    
    # Import templates
    result = manager.import_templates(file_path, TemplateFormat.JSON)
    
    # Check result
    assert result.success
    assert len(result.imported_templates) == 1
    assert result.imported_templates[0] == 'test_template'
    
    # Check template was saved
    template = manager._load_template('test_template')
    assert template is not None
    assert template.name == 'Test Template'
    assert template.description == 'Test template description'
    assert template.category == 'safety'
    assert template.type == 'constraint'
    assert template.severity == 'error'

def test_export_templates_with_version(manager, template_data, tmp_path):
    """Test exporting templates with specific version."""
    # Import test template
    file_path = tmp_path / "templates.json"
    with open(file_path, 'w') as f:
        json.dump(template_data, f)
    manager.import_templates(file_path, TemplateFormat.JSON)
    
    # Mock version data
    version_manager = MagicMock(spec=TemplateVersionManager)
    version_data = MagicMock()
    version_data.template = MagicMock(spec=RuleTemplate)
    version_data.template.name = "Test Template"
    version_manager.get_version.return_value = version_data
    
    # Export specific version
    export_path = tmp_path / "export.json"
    success = manager.export_templates(
        export_path,
        TemplateFormat.JSON,
        template_ids=['test_template'],
        version='v1'
    )
    
    # Check result
    assert success
    assert export_path.exists()
    
    # Check version manager was called
    version_manager.get_version.assert_called_once_with('test_template', 'v1')
    
    # Check exported data
    with open(export_path) as f:
        exported_data = json.load(f)
    assert 'test_template' in exported_data
    assert exported_data['test_template']['name'] == 'Test Template'

def test_export_templates_with_version_info(manager, template_data, tmp_path):
    """Test exporting templates with version info."""
    # Import test template
    file_path = tmp_path / "templates.json"
    with open(file_path, 'w') as f:
        json.dump(template_data, f)
    manager.import_templates(file_path, TemplateFormat.JSON)
    
    # Mock version info
    version_manager = MagicMock(spec=TemplateVersionManager)
    version_info = {
        'version': 'v1',
        'created_at': datetime.now().isoformat(),
        'created_by': 'test_user',
        'changes': [{'type': 'create', 'description': 'Initial version'}]
    }
    version_manager.get_version_info.return_value = version_info
    
    # Export templates
    export_path = tmp_path / "export.json"
    success = manager.export_templates(export_path, TemplateFormat.JSON)
    
    # Check result
    assert success
    assert export_path.exists()
    
    # Check exported data
    with open(export_path) as f:
        exported_data = json.load(f)
    assert 'test_template' in exported_data
    assert exported_data['test_template']['version'] == version_info

def test_import_templates_version_creation_failure(manager, template_data, tmp_path):
    """Test handling version creation failure during import."""
    # Create test file
    file_path = tmp_path / "templates.json"
    with open(file_path, 'w') as f:
        json.dump(template_data, f)
    
    # Mock version creation failure
    version_manager = MagicMock(spec=TemplateVersionManager)
    version_manager.add_version.return_value = None
    
    # Import templates
    result = manager.import_templates(file_path, TemplateFormat.JSON)
    
    # Check result
    assert result.success  # Import still succeeds
    assert len(result.imported_templates) == 1
    assert len(result.warnings) == 1
    assert "Failed to create version" in result.warnings[0]
    
    # Check template was saved
    template = manager._load_template('test_template')
    assert template is not None
    assert template.name == 'Test Template'
    assert template.description == 'Test template description'
    assert template.category == 'safety'
    assert template.type == 'constraint'
    assert template.severity == 'error'

def test_export_templates_version_not_found(manager, template_data, tmp_path):
    """Test exporting templates with non-existent version."""
    # Import test template
    file_path = tmp_path / "templates.json"
    with open(file_path, 'w') as f:
        json.dump(template_data, f)
    manager.import_templates(file_path, TemplateFormat.JSON)
    
    # Mock version not found
    version_manager = MagicMock(spec=TemplateVersionManager)
    version_manager.get_version.return_value = None
    
    # Export specific version
    export_path = tmp_path / "export.json"
    success = manager.export_templates(
        export_path,
        TemplateFormat.JSON,
        template_ids=['test_template'],
        version='nonexistent'
    )
    
    # Check result
    assert success  # Export still succeeds with latest version
    assert export_path.exists()
    
    # Check exported data
    with open(export_path) as f:
        exported_data = json.load(f)
    assert 'test_template' in exported_data
    assert exported_data['test_template']['name'] == 'Test Template'

if __name__ == "__main__":
    pytest.main() 