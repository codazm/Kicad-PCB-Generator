# Template Management System API Documentation

## Overview

The template management system provides a framework for creating, managing, and using templates for PCB designs. The system supports versioning, import/export capabilities, and integration with KiCad 9's native functionality.

## Core Components

### Template Management

#### `TemplateManager`

Manages PCB design templates and their versions.

```python
class TemplateManager:
    def __init__(self):
        """Initialize template manager."""
        self.config = TemplateConfig()

    def create_template(self, name: str, category: str,
                       description: str) -> Template:
        """Create a new template."""
        pass

    def get_template(self, template_id: str) -> Template:
        """Get a template by ID."""
        pass

    def list_templates(self, category: Optional[str] = None) -> List[Template]:
        """List available templates, optionally filtered by category."""
        pass

    def update_template(self, template_id: str,
                       updates: Dict[str, Any]) -> Template:
        """Update an existing template."""
        pass

    def delete_template(self, template_id: str) -> None:
        """Delete a template."""
        pass
```

### Version Management

#### `VersionManager`

Manages template versions and version history.

```python
class VersionManager:
    def __init__(self, template_manager: TemplateManager):
        """Initialize version manager."""
        self.template_manager = template_manager

    def create_version(self, template_id: str,
                      version: str,
                      changes: str) -> TemplateVersion:
        """Create a new version of a template."""
        pass

    def get_version(self, template_id: str,
                   version: str) -> TemplateVersion:
        """Get a specific version of a template."""
        pass

    def list_versions(self, template_id: str) -> List[TemplateVersion]:
        """List all versions of a template."""
        pass

    def compare_versions(self, template_id: str,
                        version1: str,
                        version2: str) -> Dict[str, Any]:
        """Compare two versions of a template."""
        pass
```

### Import/Export

#### `TemplateImportExport`

Manages template import and export functionality.

```python
class TemplateImportExport:
    def __init__(self, template_manager: TemplateManager):
        """Initialize import/export manager."""
        self.template_manager = template_manager

    def export_template(self, template_id: str,
                       output_path: str) -> None:
        """Export a template to a file."""
        pass

    def import_template(self, file_path: str) -> Template:
        """Import a template from a file."""
        pass

    def export_all_templates(self, output_dir: str) -> None:
        """Export all templates to a directory."""
        pass

    def import_templates(self, input_dir: str) -> List[Template]:
        """Import all templates from a directory."""
        pass
```

## Data Classes

### `Template`

```python
@dataclass
class Template:
    id: str
    name: str
    category: str
    description: str
    created_at: datetime
    updated_at: datetime
    current_version: str
    metadata: Dict[str, Any]
```

### `TemplateVersion`

```python
@dataclass
class TemplateVersion:
    template_id: str
    version: str
    created_at: datetime
    changes: str
    content: Dict[str, Any]
```

### `TemplateConfig`

```python
@dataclass
class TemplateConfig:
    default_category: str = "general"
    version_format: str = "semantic"
    export_format: str = "json"
```

## Usage Examples

### Template Management

```python
from kicad_pcb_generator.core.templates import TemplateManager

# Create template manager instance
manager = TemplateManager()

# Create a new template
template = manager.create_template(
    name="Audio Amplifier",
    category="audio",
    description="Template for audio amplifier PCB design"
)

# List templates in a category
audio_templates = manager.list_templates(category="audio")
for template in audio_templates:
    print(f"Template: {template.name}")
```

### Version Management

```python
from kicad_pcb_generator.core.templates import VersionManager

# Create version manager instance
version_manager = VersionManager(template_manager)

# Create a new version
version = version_manager.create_version(
    template_id="template1",
    version="1.1.0",
    changes="Added power supply section"
)

# Compare versions
diff = version_manager.compare_versions(
    template_id="template1",
    version1="1.0.0",
    version2="1.1.0"
)
print(f"Changes: {diff['changes']}")
```

### Import/Export

```python
from kicad_pcb_generator.core.templates import TemplateImportExport

# Create import/export manager instance
io_manager = TemplateImportExport(template_manager)

# Export a template
io_manager.export_template(
    template_id="template1",
    output_path="templates/audio_amplifier.json"
)

# Import a template
template = io_manager.import_template(
    file_path="templates/audio_amplifier.json"
)
```

## Best Practices

1. **Template Organization**
   - Use clear, descriptive names
   - Categorize templates appropriately
   - Include detailed descriptions
   - Maintain consistent metadata

2. **Version Control**
   - Use semantic versioning
   - Document changes clearly
   - Maintain version history
   - Test new versions before release

3. **Import/Export**
   - Use consistent file formats
   - Include validation on import
   - Maintain backup copies
   - Document import/export procedures

4. **Integration**
   - Follow KiCad 9 conventions
   - Maintain compatibility
   - Document dependencies
   - Test integration points 
