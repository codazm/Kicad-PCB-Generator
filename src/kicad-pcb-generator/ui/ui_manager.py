"""Advanced UI features using KiCad 9's native functionality."""
import logging
import pcbnew
from typing import Dict, List, Optional, Any, Tuple, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum

from ..core.base.base_manager import BaseManager
from ..core.base.base_config import BaseConfig
from ..core.base.results.manager_result import ManagerResult, ManagerOperation, ManagerStatus
from ..core.base.results.config_result import ConfigResult, ConfigStatus, ConfigSection

if TYPE_CHECKING:
    from ..core.base.results.analysis_result import AnalysisResult

class UIFeature(Enum):
    """Types of UI features."""
    ANALYSIS_VISUALIZATION = "analysis_visualization"
    COMPONENT_PLACEMENT = "component_placement"
    ROUTING_GUIDANCE = "routing_guidance"
    REAL_TIME_VALIDATION = "real_time_validation"
    INTERACTIVE_FILTERING = "interactive_filtering"

@dataclass
class UISettingsItem:
    """Data structure for UI settings items."""
    id: str
    highlight_color: Tuple[int, int, int]  # RGB
    warning_color: Tuple[int, int, int]  # RGB
    error_color: Tuple[int, int, int]  # RGB
    highlight_width: int  # pixels
    show_grid: bool
    show_ratsnest: bool
    show_pad_numbers: bool
    show_pad_names: bool
    show_track_width: bool
    show_track_length: bool
    show_component_values: bool
    show_component_references: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class UISettings(BaseConfig[UISettingsItem]):
    """Settings for UI features.
    
    Now inherits from BaseConfig for standardized configuration operations.
    """
    
    def __init__(self, name: str = "UISettings", config_path: Optional[str] = None):
        """Initialize UI settings.
        
        Args:
            name: Configuration name
            config_path: Path to configuration file
        """
        super().__init__(name, config_path)
        self._setup_default_values()
        self._setup_validation_rules()
    
    def _setup_default_values(self) -> None:
        """Set up default configuration values."""
        self.set_default("highlight_color", (255, 0, 0))  # Red
        self.set_default("warning_color", (255, 165, 0))  # Orange
        self.set_default("error_color", (255, 0, 0))  # Red
        self.set_default("highlight_width", 2)  # pixels
        self.set_default("show_grid", True)
        self.set_default("show_ratsnest", True)
        self.set_default("show_pad_numbers", True)
        self.set_default("show_pad_names", True)
        self.set_default("show_track_width", True)
        self.set_default("show_track_length", True)
        self.set_default("show_component_values", True)
        self.set_default("show_component_references", True)
    
    def _setup_validation_rules(self) -> None:
        """Set up validation rules for configuration values."""
        self.add_validation_rule("highlight_color", {
            "type": "tuple",
            "required": True,
            "length": 3,
            "element_type": "int",
            "min": 0,
            "max": 255
        })
        self.add_validation_rule("warning_color", {
            "type": "tuple",
            "required": True,
            "length": 3,
            "element_type": "int",
            "min": 0,
            "max": 255
        })
        self.add_validation_rule("error_color", {
            "type": "tuple",
            "required": True,
            "length": 3,
            "element_type": "int",
            "min": 0,
            "max": 255
        })
        self.add_validation_rule("highlight_width", {
            "type": "int",
            "required": True,
            "min": 1,
            "max": 10
        })
        self.add_validation_rule("show_grid", {
            "type": "bool",
            "required": True
        })
        self.add_validation_rule("show_ratsnest", {
            "type": "bool",
            "required": True
        })
        self.add_validation_rule("show_pad_numbers", {
            "type": "bool",
            "required": True
        })
        self.add_validation_rule("show_pad_names", {
            "type": "bool",
            "required": True
        })
        self.add_validation_rule("show_track_width", {
            "type": "bool",
            "required": True
        })
        self.add_validation_rule("show_track_length", {
            "type": "bool",
            "required": True
        })
        self.add_validation_rule("show_component_values", {
            "type": "bool",
            "required": True
        })
        self.add_validation_rule("show_component_references", {
            "type": "bool",
            "required": True
        })
    
    def _validate_config(self, config_data: Dict[str, Any]) -> ConfigResult:
        """Validate UI settings configuration data.
        
        Args:
            config_data: Configuration data to validate
            
        Returns:
            Validation result
        """
        try:
            errors = []
            
            # Validate required fields
            required_fields = [
                "highlight_color", "warning_color", "error_color", "highlight_width",
                "show_grid", "show_ratsnest", "show_pad_numbers", "show_pad_names",
                "show_track_width", "show_track_length", "show_component_values",
                "show_component_references"
            ]
            
            for field in required_fields:
                if field not in config_data:
                    errors.append(f"Missing required field: {field}")
                    continue
                
                value = config_data[field]
                rule = self._validation_rules.get(field, {})
                
                # Type validation
                if rule.get("type") == "tuple" and not isinstance(value, tuple):
                    errors.append(f"Field {field} must be a tuple")
                elif rule.get("type") == "int" and not isinstance(value, int):
                    errors.append(f"Field {field} must be an integer")
                elif rule.get("type") == "bool" and not isinstance(value, bool):
                    errors.append(f"Field {field} must be a boolean")
                
                # Tuple validation
                if rule.get("type") == "tuple":
                    if rule.get("length") and len(value) != rule["length"]:
                        errors.append(f"Field {field} must have length {rule['length']}")
                    elif rule.get("element_type") == "int":
                        for i, element in enumerate(value):
                            if not isinstance(element, int):
                                errors.append(f"Field {field}[{i}] must be an integer")
                            elif rule.get("min") is not None and element < rule["min"]:
                                errors.append(f"Field {field}[{i}] must be >= {rule['min']}")
                            elif rule.get("max") is not None and element > rule["max"]:
                                errors.append(f"Field {field}[{i}] must be <= {rule['max']}")
                
                # Range validation for integers
                if rule.get("type") == "int":
                    if rule.get("min") is not None and value < rule["min"]:
                        errors.append(f"Field {field} must be >= {rule['min']}")
                    if rule.get("max") is not None and value > rule["max"]:
                        errors.append(f"Field {field} must be <= {rule['max']}")
            
            if errors:
                return ConfigResult(
                    success=False,
                    status=ConfigStatus.INVALID,
                    message="UI settings validation failed",
                    errors=errors,
                    config_type=self.name
                )
            
            return ConfigResult(
                success=True,
                status=ConfigStatus.VALID,
                message="UI settings are valid",
                config_type=self.name
            )
            
        except Exception as e:
            return ConfigResult(
                success=False,
                status=ConfigStatus.ERROR,
                message=f"Error validating UI settings: {e}",
                errors=[str(e)],
                config_type=self.name
            )
    
    def _parse_config(self, config_data: Dict[str, Any]) -> ConfigResult:
        """Parse UI settings configuration data.
        
        Args:
            config_data: Configuration data to parse
            
        Returns:
            Parsing result
        """
        try:
            # Create UI settings item
            ui_item = UISettingsItem(
                id=config_data.get("id", "ui_settings"),
                highlight_color=config_data.get("highlight_color", (255, 0, 0)),
                warning_color=config_data.get("warning_color", (255, 165, 0)),
                error_color=config_data.get("error_color", (255, 0, 0)),
                highlight_width=config_data.get("highlight_width", 2),
                show_grid=config_data.get("show_grid", True),
                show_ratsnest=config_data.get("show_ratsnest", True),
                show_pad_numbers=config_data.get("show_pad_numbers", True),
                show_pad_names=config_data.get("show_pad_names", True),
                show_track_width=config_data.get("show_track_width", True),
                show_track_length=config_data.get("show_track_length", True),
                show_component_values=config_data.get("show_component_values", True),
                show_component_references=config_data.get("show_component_references", True)
            )
            
            # Add to sections
            self.add_section(ConfigSection(
                name="ui_settings",
                data=config_data,
                description="UI display and interaction settings"
            ))
            
            return ConfigResult(
                success=True,
                status=ConfigStatus.LOADED,
                message="UI settings parsed successfully",
                data=ui_item,
                config_type=self.name
            )
            
        except Exception as e:
            return ConfigResult(
                success=False,
                status=ConfigStatus.ERROR,
                message=f"Error parsing UI settings: {e}",
                errors=[str(e)],
                config_type=self.name
            )
    
    def _prepare_config_data(self) -> Dict[str, Any]:
        """Prepare UI settings configuration data for saving.
        
        Returns:
            Configuration data
        """
        ui_section = self.get_section("ui_settings")
        if ui_section:
            return ui_section.data
        
        # Return default configuration
        return {
            "id": "ui_settings",
            "highlight_color": self.get_default("highlight_color"),
            "warning_color": self.get_default("warning_color"),
            "error_color": self.get_default("error_color"),
            "highlight_width": self.get_default("highlight_width"),
            "show_grid": self.get_default("show_grid"),
            "show_ratsnest": self.get_default("show_ratsnest"),
            "show_pad_numbers": self.get_default("show_pad_numbers"),
            "show_pad_names": self.get_default("show_pad_names"),
            "show_track_width": self.get_default("show_track_width"),
            "show_track_length": self.get_default("show_track_length"),
            "show_component_values": self.get_default("show_component_values"),
            "show_component_references": self.get_default("show_component_references")
        }
    
    def create_ui_settings(self,
                          highlight_color: Tuple[int, int, int] = (255, 0, 0),
                          warning_color: Tuple[int, int, int] = (255, 165, 0),
                          error_color: Tuple[int, int, int] = (255, 0, 0),
                          highlight_width: int = 2,
                          show_grid: bool = True,
                          show_ratsnest: bool = True,
                          show_pad_numbers: bool = True,
                          show_pad_names: bool = True,
                          show_track_width: bool = True,
                          show_track_length: bool = True,
                          show_component_values: bool = True,
                          show_component_references: bool = True) -> ConfigResult[UISettingsItem]:
        """Create new UI settings.
        
        Args:
            highlight_color: RGB color for highlights
            warning_color: RGB color for warnings
            error_color: RGB color for errors
            highlight_width: Width of highlights in pixels
            show_grid: Whether to show grid
            show_ratsnest: Whether to show ratsnest
            show_pad_numbers: Whether to show pad numbers
            show_pad_names: Whether to show pad names
            show_track_width: Whether to show track width
            show_track_length: Whether to show track length
            show_component_values: Whether to show component values
            show_component_references: Whether to show component references
            
        Returns:
            Configuration result
        """
        try:
            config_data = {
                "id": f"ui_settings_{len(self._config_history) + 1}",
                "highlight_color": highlight_color,
                "warning_color": warning_color,
                "error_color": error_color,
                "highlight_width": highlight_width,
                "show_grid": show_grid,
                "show_ratsnest": show_ratsnest,
                "show_pad_numbers": show_pad_numbers,
                "show_pad_names": show_pad_names,
                "show_track_width": show_track_width,
                "show_track_length": show_track_length,
                "show_component_values": show_component_values,
                "show_component_references": show_component_references
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
                message=f"Error creating UI settings: {e}",
                errors=[str(e)],
                config_type=self.name
            )

@dataclass
class UIItem:
    """Represents a UI item managed by UIManager."""
    id: str
    feature_type: UIFeature
    settings: UISettings
    board_item: Optional[Any] = None
    location: Optional[Tuple[float, float]] = None
    color: Optional[Tuple[int, int, int]] = None
    is_highlighted: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class UIManager(BaseManager[UIItem]):
    """Manages UI features using KiCad 9's native functionality."""
    
    def __init__(self, board: pcbnew.BOARD, frame: Optional[pcbnew.FRAME] = None, logger: Optional[logging.Logger] = None):
        """Initialize the UI manager.
        
        Args:
            board: KiCad board object
            frame: KiCad frame object (optional)
            logger: Optional logger instance
        """
        super().__init__()
        self.board = board
        self.frame = frame
        self.logger = logger or logging.getLogger(__name__)
        self._validate_kicad_version()
        self._settings = self._initialize_settings()
        self._active_highlights: List[pcbnew.BOARD_ITEM] = []
        
        # Initialize UI items
        self._initialize_ui_items()
    
    def _validate_kicad_version(self) -> None:
        """Validate KiCad version compatibility."""
        version = pcbnew.Version()
        if not version.startswith('9'):
            raise RuntimeError(f"This module requires KiCad 9.x, but found version {version}")
        self.logger.info(f"Running with KiCad version: {version}")
    
    def _initialize_settings(self) -> UISettings:
        """Initialize UI settings."""
        return UISettings(
            highlight_color=(255, 0, 0),  # Red
            warning_color=(255, 165, 0),  # Orange
            error_color=(255, 0, 0),  # Red
            highlight_width=2,  # pixels
            show_grid=True,
            show_ratsnest=True,
            show_pad_numbers=True,
            show_pad_names=True,
            show_track_width=True,
            show_track_length=True,
            show_component_values=True,
            show_component_references=True
        )
    
    def _initialize_ui_items(self) -> None:
        """Initialize UI items for BaseManager."""
        try:
            # Create default UI items for each feature type
            for feature_type in UIFeature:
                ui_item = UIItem(
                    id=f"ui_{feature_type.value}",
                    feature_type=feature_type,
                    settings=self._settings
                )
                self.create(f"ui_{feature_type.value}", ui_item)
                
        except Exception as e:
            self.logger.error(f"Error initializing UI items: {str(e)}")
            raise
    
    def highlight_item(self, item: pcbnew.BOARD_ITEM, color: Optional[Tuple[int, int, int]] = None) -> None:
        """Highlight a board item.
        
        Args:
            item: Board item to highlight
            color: Optional highlight color (RGB)
        """
        try:
            if color is None:
                color = self._settings.highlight_color
            
            # Set highlight color
            item.SetHighlighted(True)
            item.SetHighlightColor(color)
            
            # Add to active highlights
            self._active_highlights.append(item)
            
            # Create or update UI item
            item_id = f"highlight_{id(item)}"
            ui_item = UIItem(
                id=item_id,
                feature_type=UIFeature.ANALYSIS_VISUALIZATION,
                settings=self._settings,
                board_item=item,
                color=color,
                is_highlighted=True
            )
            self.create(item_id, ui_item)
            
            # Refresh display
            if self.frame:
                self.frame.Refresh()
            
        except Exception as e:
            self.logger.error(f"Error highlighting item: {str(e)}")
            raise
    
    def clear_highlights(self) -> None:
        """Clear all highlights."""
        try:
            for item in self._active_highlights:
                item.SetHighlighted(False)
            
            self._active_highlights.clear()
            
            # Clear highlight UI items
            for key, ui_item in self._items.items():
                if key.startswith("highlight_"):
                    self.delete(key)
            
            # Refresh display
            if self.frame:
                self.frame.Refresh()
            
        except Exception as e:
            self.logger.error(f"Error clearing highlights: {str(e)}")
            raise
    
    def show_analysis_results(self, results: List[Any]) -> None:
        """Show analysis results on the board.
        
        Args:
            results: List of analysis results
        """
        try:
            # Clear existing highlights
            self.clear_highlights()
            
            # Highlight items based on results
            for result in results:
                if hasattr(result, 'location'):
                    # Find items at location
                    items = self._find_items_at_location(result.location)
                    
                    # Highlight items based on severity
                    color = self._settings.warning_color if result.severity == "warning" else self._settings.error_color
                    for item in items:
                        self.highlight_item(item, color)
            
        except Exception as e:
            self.logger.error(f"Error showing analysis results: {str(e)}")
            raise
    
    def _find_items_at_location(self, location: Tuple[float, float]) -> List[pcbnew.BOARD_ITEM]:
        """Find board items at a specific location.
        
        Args:
            location: (x, y) location in mm
            
        Returns:
            List of board items at location
        """
        items = []
        
        try:
            # Convert location to board units
            x = int(location[0] * 1e6)  # Convert to nm
            y = int(location[1] * 1e6)
            
            # Get items at location
            for item in self.board.GetItems():
                if isinstance(item, (pcbnew.TRACK, pcbnew.FOOTPRINT, pcbnew.ZONE)):
                    pos = item.GetPosition()
                    if abs(pos.x - x) < 1e6 and abs(pos.y - y) < 1e6:  # 1mm tolerance
                        items.append(item)
            
        except Exception as e:
            self.logger.error(f"Error finding items at location: {str(e)}")
            raise
        
        return items
    
    def show_component_placement_suggestions(self, suggestions: List[Any]) -> None:
        """Show component placement suggestions.
        
        Args:
            suggestions: List of placement suggestions
        """
        try:
            # Clear existing highlights
            self.clear_highlights()
            
            # Show suggestions
            for i, suggestion in enumerate(suggestions):
                if hasattr(suggestion, 'location'):
                    # Create temporary footprint for suggestion
                    footprint = pcbnew.FOOTPRINT(self.board)
                    footprint.SetPosition(pcbnew.VECTOR2I(
                        int(suggestion.location[0] * 1e6),
                        int(suggestion.location[1] * 1e6)
                    ))
                    
                    # Create UI item for suggestion
                    suggestion_id = f"suggestion_{i}"
                    ui_item = UIItem(
                        id=suggestion_id,
                        feature_type=UIFeature.COMPONENT_PLACEMENT,
                        settings=self._settings,
                        board_item=footprint,
                        location=suggestion.location,
                        color=self._settings.highlight_color,
                        is_highlighted=True
                    )
                    self.create(suggestion_id, ui_item)
                    
                    # Highlight suggestion
                    self.highlight_item(footprint, self._settings.highlight_color)
            
        except Exception as e:
            self.logger.error(f"Error showing placement suggestions: {str(e)}")
            raise
    
    def show_routing_guidance(self, guidance: List[Any]) -> None:
        """Show routing guidance.
        
        Args:
            guidance: List of routing guidance items
        """
        try:
            # Clear existing highlights
            self.clear_highlights()
            
            # Show guidance
            for i, guide in enumerate(guidance):
                if hasattr(guide, 'start') and hasattr(guide, 'end'):
                    # Create temporary track for guidance
                    track = pcbnew.TRACK(self.board)
                    track.SetStart(pcbnew.VECTOR2I(
                        int(guide.start[0] * 1e6),
                        int(guide.start[1] * 1e6)
                    ))
                    track.SetEnd(pcbnew.VECTOR2I(
                        int(guide.end[0] * 1e6),
                        int(guide.end[1] * 1e6)
                    ))
                    
                    # Create UI item for guidance
                    guidance_id = f"guidance_{i}"
                    ui_item = UIItem(
                        id=guidance_id,
                        feature_type=UIFeature.ROUTING_GUIDANCE,
                        settings=self._settings,
                        board_item=track,
                        location=guide.start,
                        color=self._settings.highlight_color,
                        is_highlighted=True
                    )
                    self.create(guidance_id, ui_item)
                    
                    # Highlight guidance
                    self.highlight_item(track, self._settings.highlight_color)
            
        except Exception as e:
            self.logger.error(f"Error showing routing guidance: {str(e)}")
            raise
    
    def toggle_grid(self, show: Optional[bool] = None) -> None:
        """Toggle grid display.
        
        Args:
            show: Optional boolean to set grid state
        """
        try:
            if show is None:
                show = not self._settings.show_grid
            
            self._settings.show_grid = show
            
            # Update UI item
            grid_item = self.read("ui_grid")
            if grid_item.success:
                grid_item.data.settings.show_grid = show
                self.update("ui_grid", grid_item.data)
            
            # Apply to board
            if self.frame:
                self.frame.SetGridVisibility(show)
                self.frame.Refresh()
            
        except Exception as e:
            self.logger.error(f"Error toggling grid: {str(e)}")
            raise
    
    def toggle_ratsnest(self, show: Optional[bool] = None) -> None:
        """Toggle ratsnest display.
        
        Args:
            show: Optional boolean to set ratsnest state
        """
        try:
            if show is None:
                show = not self._settings.show_ratsnest
            
            self._settings.show_ratsnest = show
            
            # Update UI item
            ratsnest_item = self.read("ui_ratsnest")
            if ratsnest_item.success:
                ratsnest_item.data.settings.show_ratsnest = show
                self.update("ui_ratsnest", ratsnest_item.data)
            
            # Apply to board
            if self.frame:
                self.frame.SetRatsnestVisibility(show)
                self.frame.Refresh()
            
        except Exception as e:
            self.logger.error(f"Error toggling ratsnest: {str(e)}")
            raise
    
    def toggle_pad_info(self, show: Optional[bool] = None) -> None:
        """Toggle pad information display.
        
        Args:
            show: Optional boolean to set pad info state
        """
        try:
            if show is None:
                show = not (self._settings.show_pad_numbers and self._settings.show_pad_names)
            
            self._settings.show_pad_numbers = show
            self._settings.show_pad_names = show
            
            # Update UI item
            pad_item = self.read("ui_pad_info")
            if pad_item.success:
                pad_item.data.settings.show_pad_numbers = show
                pad_item.data.settings.show_pad_names = show
                self.update("ui_pad_info", pad_item.data)
            
            # Apply to board
            if self.frame:
                self.frame.SetPadNumbersVisibility(show)
                self.frame.SetPadNamesVisibility(show)
                self.frame.Refresh()
            
        except Exception as e:
            self.logger.error(f"Error toggling pad info: {str(e)}")
            raise
    
    def toggle_track_info(self, show: Optional[bool] = None) -> None:
        """Toggle track information display.
        
        Args:
            show: Optional boolean to set track info state
        """
        try:
            if show is None:
                show = not (self._settings.show_track_width and self._settings.show_track_length)
            
            self._settings.show_track_width = show
            self._settings.show_track_length = show
            
            # Update UI item
            track_item = self.read("ui_track_info")
            if track_item.success:
                track_item.data.settings.show_track_width = show
                track_item.data.settings.show_track_length = show
                self.update("ui_track_info", track_item.data)
            
            # Apply to board
            if self.frame:
                self.frame.SetTrackWidthVisibility(show)
                self.frame.SetTrackLengthVisibility(show)
                self.frame.Refresh()
            
        except Exception as e:
            self.logger.error(f"Error toggling track info: {str(e)}")
            raise
    
    def toggle_component_info(self, show: Optional[bool] = None) -> None:
        """Toggle component information display.
        
        Args:
            show: Optional boolean to set component info state
        """
        try:
            if show is None:
                show = not (self._settings.show_component_values and self._settings.show_component_references)
            
            self._settings.show_component_values = show
            self._settings.show_component_references = show
            
            # Update UI item
            component_item = self.read("ui_component_info")
            if component_item.success:
                component_item.data.settings.show_component_values = show
                component_item.data.settings.show_component_references = show
                self.update("ui_component_info", component_item.data)
            
            # Apply to board
            if self.frame:
                self.frame.SetComponentValuesVisibility(show)
                self.frame.SetComponentReferencesVisibility(show)
                self.frame.Refresh()
            
        except Exception as e:
            self.logger.error(f"Error toggling component info: {str(e)}")
            raise
    
    def _validate_data(self, data: UIItem) -> ManagerResult:
        """Validate data before storage.
        
        Args:
            data: Data to validate
            
        Returns:
            Validation result
        """
        try:
            if not data.id:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="UI item ID is required",
                    errors=["UI item ID cannot be empty"]
                )
            
            if not data.feature_type:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="UI feature type is required",
                    errors=["UI feature type cannot be empty"]
                )
            
            if not data.settings:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="UI settings are required",
                    errors=["UI settings cannot be empty"]
                )
            
            return ManagerResult(
                success=True,
                operation=ManagerOperation.VALIDATE,
                status=ManagerStatus.SUCCESS,
                message="UI item validation successful"
            )
        except Exception as e:
            return ManagerResult(
                success=False,
                operation=ManagerOperation.VALIDATE,
                status=ManagerStatus.FAILED,
                message=f"UI item validation failed: {e}",
                errors=[str(e)]
            )
    
    def _cleanup_item(self, key: str) -> None:
        """Clean up resources for a UI item.
        
        Args:
            key: UI item ID to clean up
        """
        # Clear highlights if this was a highlight item
        if key.startswith("highlight_"):
            # Find and remove the corresponding board item from active highlights
            for i, item in enumerate(self._active_highlights):
                if f"highlight_{id(item)}" == key:
                    item.SetHighlighted(False)
                    self._active_highlights.pop(i)
                    break
    
    def _clear_cache(self) -> None:
        """Clear cache after data changes."""
        # Clear the cache and refresh display
        super()._clear_cache()
        if self.frame:
            self.frame.Refresh() 