"""
Project manager for KiCad PCB Generator.
"""
import os
import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field
import logging

from .base.base_manager import BaseManager
from .base.results.manager_result import ManagerResult, ManagerOperation, ManagerStatus
from .base.base_config import BaseConfig
from .base.results.config_result import ConfigResult, ConfigStatus, ConfigFormat

logger = logging.getLogger(__name__)

@dataclass
class ProjectConfigItem:
    """Configuration item for a project."""
    name: str
    template: str
    description: str = ""
    version: str = "1.0.0"
    author: str = ""
    created_date: str = ""
    modified_date: str = ""
    settings: Dict[str, Any] = field(default_factory=dict)

class ProjectConfig(BaseConfig[ProjectConfigItem]):
    """Configuration manager for projects."""
    
    def __init__(self, config_data: Optional[Dict[str, Any]] = None):
        """Initialize project configuration.
        
        Args:
            config_data: Configuration data dictionary
        """
        super().__init__(config_data or {})
        self.logger = logging.getLogger(__name__)
        
    def _validate_config(self, config: ProjectConfigItem) -> ConfigResult:
        """Validate project configuration.
        
        Args:
            config: Configuration item to validate
            
        Returns:
            ConfigResult with validation status
        """
        try:
            # Validate name
            if not config.name or not isinstance(config.name, str):
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Project name must be a non-empty string",
                    data=config
                )
            
            # Validate template
            if not config.template or not isinstance(config.template, str):
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Template must be a non-empty string",
                    data=config
                )
            
            # Validate description
            if not isinstance(config.description, str):
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Description must be a string",
                    data=config
                )
            
            # Validate version
            if not config.version or not isinstance(config.version, str):
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Version must be a non-empty string",
                    data=config
                )
            
            # Validate author
            if not isinstance(config.author, str):
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Author must be a string",
                    data=config
                )
            
            # Validate dates
            if not isinstance(config.created_date, str):
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Created date must be a string",
                    data=config
                )
            
            if not isinstance(config.modified_date, str):
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Modified date must be a string",
                    data=config
                )
            
            # Validate settings
            if not isinstance(config.settings, dict):
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Settings must be a dictionary",
                    data=config
                )
            
            return ConfigResult(
                status=ConfigStatus.SUCCESS,
                message="Project configuration validated successfully",
                data=config
            )
            
        except Exception as e:
            self.logger.error(f"Error validating project configuration: {e}")
            return ConfigResult(
                status=ConfigStatus.ERROR,
                message=f"Configuration validation failed: {e}",
                data=config
            )
    
    def _parse_config(self, config_data: Dict[str, Any]) -> ProjectConfigItem:
        """Parse configuration data into ProjectConfigItem.
        
        Args:
            config_data: Configuration data dictionary
            
        Returns:
            ProjectConfigItem instance
        """
        try:
            return ProjectConfigItem(
                name=config_data.get('name', ''),
                template=config_data.get('template', ''),
                description=config_data.get('description', ''),
                version=config_data.get('version', '1.0.0'),
                author=config_data.get('author', ''),
                created_date=config_data.get('created_date', ''),
                modified_date=config_data.get('modified_date', ''),
                settings=config_data.get('settings', {})
            )
        except Exception as e:
            self.logger.error(f"Error parsing project configuration: {e}")
            raise ValueError(f"Invalid project configuration data: {e}")
    
    def _prepare_config_data(self, config: ProjectConfigItem) -> Dict[str, Any]:
        """Prepare configuration item for serialization.
        
        Args:
            config: Configuration item to prepare
            
        Returns:
            Dictionary representation of configuration
        """
        return {
            'name': config.name,
            'template': config.template,
            'description': config.description,
            'version': config.version,
            'author': config.author,
            'created_date': config.created_date,
            'modified_date': config.modified_date,
            'settings': config.settings
        }

class ProjectManager(BaseManager[ProjectConfigItem]):
    """Manages KiCad PCB Generator projects.
    
    Now inherits from BaseManager for standardized CRUD operations.
    """
    
    def __init__(self, base_path: str = "."):
        """Initialize the project manager.
        
        Args:
            base_path: Base path for projects
        """
        super().__init__()
        self.base_path = Path(base_path)
        self.projects_dir = self.base_path / "projects"
        self.templates_dir = self.base_path / "templates"
        
        # Ensure directories exist
        self.projects_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)
        
        # Load existing projects
        self._load_projects()
    
    def _load_projects(self) -> None:
        """Load existing projects from disk."""
        try:
            for item in self.projects_dir.iterdir():
                if item.is_dir() and (item / "config" / "project.json").exists():
                    config = self.load_project(item.name)
                    # Use BaseManager's create method
                    self.create(config.name, config)
        except Exception as e:
            logger.error(f"Error loading projects: {e}")
    
    def create_project(self, name: str, template: str = "basic_audio_amp", 
                      description: str = "", author: str = "", board_config: Optional[Dict[str, Any]] = None) -> ProjectConfigItem:
        """Create a new project from a template.
        
        Args:
            name: Project name
            template: Template to use
            description: Project description
            author: Project author
            board_config: Optional board configuration (profile, dimensions, etc.)
            
        Returns:
            Project configuration
            
        Raises:
            ValueError: If project already exists
            FileNotFoundError: If template not found
        """
        project_path = self.projects_dir / name
        
        if project_path.exists():
            raise ValueError(f"Project '{name}' already exists")
        
        # Create project directory
        project_path.mkdir(parents=True)
        
        # Create project structure
        (project_path / "schematics").mkdir()
        (project_path / "pcb").mkdir()
        (project_path / "output").mkdir()
        (project_path / "config").mkdir()
        (project_path / "docs").mkdir()
        
        # Prepare settings with board configuration
        settings = {}
        if board_config:
            settings["board_config"] = board_config
        
        # Create project configuration
        config = ProjectConfigItem(
            name=name,
            template=template,
            description=description,
            author=author,
            created_date=self._get_current_date(),
            modified_date=self._get_current_date(),
            settings=settings
        )
        
        # Use BaseManager's create method
        result = self.create(name, config)
        if not result.success:
            raise ValueError(f"Failed to create project: {result.message}")
        
        # Save configuration to disk
        self._save_project_config(project_path, config)
        
        # Copy template files if template exists
        template_path = self.templates_dir / template
        if template_path.exists():
            self._copy_template_files(template_path, project_path)
        
        logger.info(f"Created project '{name}' from template '{template}'")
        if board_config:
            logger.info(f"Applied board configuration: {board_config}")
        return config
    
    def load_project(self, name: str) -> ProjectConfigItem:
        """Load an existing project.
        
        Args:
            name: Project name
            
        Returns:
            Project configuration
            
        Raises:
            FileNotFoundError: If project not found
        """
        project_path = self.projects_dir / name
        
        if not project_path.exists():
            raise FileNotFoundError(f"Project '{name}' not found")
        
        config_path = project_path / "config" / "project.json"
        if not config_path.exists():
            raise FileNotFoundError(f"Project configuration not found for '{name}'")
        
        with open(config_path, 'r') as f:
            data = json.load(f)
        
        return ProjectConfigItem(**data)
    
    def list_projects(self) -> List[str]:
        """List all available projects.
        
        Returns:
            List of project names
        """
        result = self.list_all()
        if result.success:
            return [project.name for project in result.data]
        return []
    
    def delete_project(self, name: str) -> None:
        """Delete a project.
        
        Args:
            name: Project name
            
        Raises:
            FileNotFoundError: If project not found
        """
        project_path = self.projects_dir / name
        
        if not project_path.exists():
            raise FileNotFoundError(f"Project '{name}' not found")
        
        # Use BaseManager's delete method
        result = self.delete(name)
        if not result.success:
            raise ValueError(f"Failed to delete project: {result.message}")
        
        # Remove from disk
        shutil.rmtree(project_path)
        logger.info(f"Deleted project '{name}'")
    
    def update_project_config(self, name: str, **kwargs) -> ProjectConfigItem:
        """Update project configuration.
        
        Args:
            name: Project name
            **kwargs: Configuration updates
            
        Returns:
            Updated project configuration
        """
        # Get existing project
        read_result = self.read(name)
        if not read_result.success:
            raise FileNotFoundError(f"Project '{name}' not found")
        
        config = read_result.data
        
        # Update fields
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        config.modified_date = self._get_current_date()
        
        # Use BaseManager's update method
        result = self.update(name, config)
        if not result.success:
            raise ValueError(f"Failed to update project: {result.message}")
        
        # Save updated configuration to disk
        project_path = self.projects_dir / name
        self._save_project_config(project_path, config)
        
        logger.info(f"Updated project configuration for '{name}'")
        return config
    
    def get_project_path(self, name: str) -> Path:
        """Get the path to a project.
        
        Args:
            name: Project name
            
        Returns:
            Project path
        """
        return self.projects_dir / name
    
    def _validate_data(self, data: ProjectConfigItem) -> ManagerResult:
        """Validate data before storage.
        
        Args:
            data: Data to validate
            
        Returns:
            Validation result
        """
        try:
            if not data.name:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Project name is required",
                    errors=["Project name cannot be empty"]
                )
            
            if not data.template:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Project template is required",
                    errors=["Project template cannot be empty"]
                )
            
            return ManagerResult(
                success=True,
                operation=ManagerOperation.VALIDATE,
                status=ManagerStatus.SUCCESS,
                message="Project validation successful"
            )
        except Exception as e:
            return ManagerResult(
                success=False,
                operation=ManagerOperation.VALIDATE,
                status=ManagerStatus.FAILED,
                message=f"Project validation failed: {e}",
                errors=[str(e)]
            )
    
    def _cleanup_item(self, key: str) -> None:
        """Clean up resources for a project.
        
        Args:
            key: Project name to clean up
        """
        # No specific cleanup needed for projects but keep hook for future.
        logger.debug("ProjectManager cleanup hook called for project '%s'", key)
    
    def _clear_cache(self) -> None:
        """Clear cache after data changes."""
        # Clear the cache - no additional disk operations needed
        super()._clear_cache()
    
    def _save_project_config(self, project_path: Path, config: ProjectConfigItem) -> None:
        """Save project configuration to file.
        
        Args:
            project_path: Project directory path
            config: Project configuration
        """
        config_path = project_path / "config" / "project.json"
        config_path.parent.mkdir(exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(asdict(config), f, indent=2)
    
    def _copy_template_files(self, template_path: Path, project_path: Path) -> None:
        """Copy template files to project directory.
        
        Args:
            template_path: Template directory path
            project_path: Project directory path
        """
        try:
            # Copy all files from template to project
            for item in template_path.rglob("*"):
                if item.is_file():
                    relative_path = item.relative_to(template_path)
                    target_path = project_path / relative_path
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, target_path)
            
            logger.info(f"Copied template files from '{template_path.name}'")
        except Exception as e:
            logger.warning(f"Failed to copy template files: {e}")
    
    def _get_current_date(self) -> str:
        """Get current date as string.
        
        Returns:
            Current date string
        """
        from datetime import datetime
        return datetime.now().isoformat() 