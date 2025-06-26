"""
Core board management functionality for KiCad PCB Generator.
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, TYPE_CHECKING, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

import pcbnew

from ..base.base_manager import BaseManager
from ..base.results.manager_result import ManagerResult, ManagerOperation, ManagerStatus

if TYPE_CHECKING:
    from ..base.results.analysis_result import AnalysisResult

@dataclass
class BoardItem:
    """Represents a board item (component, track, via, etc.)."""
    id: str
    type: str  # "component", "track", "via", "board"
    name: str
    position: Optional[Tuple[float, float]] = None
    layer: int = 0
    properties: Optional[Dict[str, Any]] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

class BoardManager(BaseManager[BoardItem]):
    """Manages PCB board creation and modification."""

    def __init__(self, project_path: Optional[Union[str, Path]] = None):
        """Initialize board manager.
        
        Args:
            project_path: Path to project directory. If None, creates a new project.
        """
        super().__init__()
        self.project_path = Path(project_path) if project_path else None
        self.board = None
        self.schematic = None
        self.logger = logging.getLogger(__name__)

    def create_board(self, template: str = "basic") -> None:
        """Create a new board from template.
        
        Args:
            template: Template to use for board creation.
        """
        try:
            # Create new board
            self.board = pcbnew.BOARD()
            
            # Set basic board properties
            self.board.SetBoardUse(BOARD_USE.AUDIO)
            self.board.SetCopperLayerCount(2)  # Basic 2-layer board
            
            # Add default layers
            self._setup_default_layers()
            
            # Apply template settings
            self._apply_template(template)
            
            # Create board item
            board_item = BoardItem(
                id="main_board",
                type="board",
                name=f"Board_{template}",
                properties={
                    "template": template,
                    "layers": 2,
                    "thickness": 1.6
                }
            )
            self.create("main_board", board_item)
            
            self.logger.info(f"Created new board from template: {template}")
        except Exception as e:
            self.logger.error(f"Error creating board: {e}")
            raise

    def load_board(self, board_path: Union[str, Path]) -> None:
        """Load existing board.
        
        Args:
            board_path: Path to .kicad_pcb file.
        """
        try:
            board_path = Path(board_path)
            if not board_path.exists():
                raise FileNotFoundError(f"Board file not found: {board_path}")
            
            self.board = pcbnew.LoadBoard(str(board_path))
            
            # Create board item
            board_item = BoardItem(
                id="loaded_board",
                type="board",
                name=board_path.stem,
                properties={
                    "file_path": str(board_path),
                    "layers": self.board.GetCopperLayerCount()
                }
            )
            self.create("loaded_board", board_item)
            
            self.logger.info(f"Loaded board from: {board_path}")
        except Exception as e:
            self.logger.error(f"Error loading board: {e}")
            raise

    def save_board(self, output_path: Optional[Union[str, Path]] = None) -> None:
        """Save board to file.
        
        Args:
            output_path: Path to save board file. If None, uses project path.
        """
        try:
            if not self.board:
                raise ValueError("No board loaded")
            
            if output_path is None:
                if not self.project_path:
                    raise ValueError("No project path specified")
                output_path = self.project_path / "board.kicad_pcb"
            
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            pcbnew.SaveBoard(str(output_path), self.board)
            self.logger.info(f"Saved board to: {output_path}")
        except Exception as e:
            self.logger.error(f"Error saving board: {e}")
            raise

    def _setup_default_layers(self) -> None:
        """Set up default board layers."""
        if not self.board:
            raise ValueError("No board loaded")
        
        # Set layer names
        self.board.SetLayerName("F.Cu", 0)
        self.board.SetLayerName("B.Cu", 1)
        self.board.SetLayerName("F.SilkS", 2)
        self.board.SetLayerName("B.SilkS", 3)
        self.board.SetLayerName("F.Mask", 4)
        self.board.SetLayerName("B.Mask", 5)
        self.board.SetLayerName("Edge.Cuts", 6)

    def _apply_template(self, template: str) -> None:
        """Apply template settings to board.
        
        Args:
            template: Template name to apply.
        """
        if not self.board:
            raise ValueError("No board loaded")
        
        # Basic template settings
        if template == "basic":
            # Set board size
            self.board.SetBoardThickness(1.6)  # 1.6mm standard thickness
            
            # Set design rules
            self.board.SetDesignSettings(
                min_track_width=0.2,  # 0.2mm minimum track width
                min_via_size=0.4,     # 0.4mm minimum via size
                min_via_drill=0.3,    # 0.3mm minimum via drill
                min_hole_to_hole=0.4  # 0.4mm minimum hole to hole
            )
            
            # Set grid
            self.board.SetGridOrigin(pcbnew.VECTOR2I(0, 0))
            self.board.SetGridSize(pcbnew.VECTOR2I(1000000, 1000000))  # 1mm grid
            
        else:
            raise ValueError(f"Unknown template: {template}")

    def add_component(self, component_name: str, position: tuple, layer: int = 0) -> None:
        """Add component to board.
        
        Args:
            component_name: Name of component to add.
            position: (x, y) position in mm.
            layer: Layer to place component on (0 = top, 1 = bottom).
        """
        if not self.board:
            raise ValueError("No board loaded")
        
        try:
            # Create component
            component = pcbnew.FOOTPRINT(self.board)
            component.SetReference(component_name)
            
            # Set position (convert mm to internal units)
            x, y = position
            component.SetPosition(pcbnew.VECTOR2I(int(x * 1000000), int(y * 1000000)))
            
            # Set layer
            component.SetLayer(layer)
            
            # Add to board
            self.board.Add(component)
            
            # Create board item
            component_item = BoardItem(
                id=component_name,
                type="component",
                name=component_name,
                position=position,
                layer=layer,
                properties={
                    "reference": component_name,
                    "footprint": "unknown"
                }
            )
            self.create(component_name, component_item)
            
            self.logger.info(f"Added component {component_name} at {position}")
        except Exception as e:
            self.logger.error(f"Error adding component: {e}")
            raise

    def add_track(self, start: tuple, end: tuple, width: float, layer: int = 0) -> None:
        """Add track to board.
        
        Args:
            start: (x, y) start position in mm.
            end: (x, y) end position in mm.
            width: Track width in mm.
            layer: Layer to place track on (0 = top, 1 = bottom).
        """
        if not self.board:
            raise ValueError("No board loaded")
        
        try:
            # Create track
            track = pcbnew.TRACK(self.board)
            
            # Set positions (convert mm to internal units)
            x1, y1 = start
            x2, y2 = end
            track.SetStart(pcbnew.VECTOR2I(int(x1 * 1000000), int(y1 * 1000000)))
            track.SetEnd(pcbnew.VECTOR2I(int(x2 * 1000000), int(y2 * 1000000)))
            
            # Set width
            track.SetWidth(int(width * 1000000))
            
            # Set layer
            track.SetLayer(layer)
            
            # Add to board
            self.board.Add(track)
            
            # Create board item
            track_id = f"track_{len(self._items)}"
            track_item = BoardItem(
                id=track_id,
                type="track",
                name=f"Track {track_id}",
                position=start,
                layer=layer,
                properties={
                    "start": start,
                    "end": end,
                    "width": width
                }
            )
            self.create(track_id, track_item)
            
            self.logger.info(f"Added track from {start} to {end}")
        except Exception as e:
            self.logger.error(f"Error adding track: {e}")
            raise

    def add_via(self, position: tuple, size: float, drill: float) -> None:
        """Add via to board.
        
        Args:
            position: (x, y) position in mm.
            size: Via size in mm.
            drill: Drill size in mm.
        """
        if not self.board:
            raise ValueError("No board loaded")
        
        try:
            # Create via
            via = pcbnew.VIA(self.board)
            
            # Set position (convert mm to internal units)
            x, y = position
            via.SetPosition(pcbnew.VECTOR2I(int(x * 1000000), int(y * 1000000)))
            
            # Set sizes
            via.SetWidth(int(size * 1000000))
            via.SetDrill(int(drill * 1000000))
            
            # Add to board
            self.board.Add(via)
            
            # Create board item
            via_id = f"via_{len(self._items)}"
            via_item = BoardItem(
                id=via_id,
                type="via",
                name=f"Via {via_id}",
                position=position,
                properties={
                    "size": size,
                    "drill": drill
                }
            )
            self.create(via_id, via_item)
            
            self.logger.info(f"Added via at {position}")
        except Exception as e:
            self.logger.error(f"Error adding via: {e}")
            raise
    
    def _validate_data(self, data: BoardItem) -> ManagerResult:
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
                    message="Board item ID is required",
                    errors=["Board item ID cannot be empty"]
                )
            
            if not data.type:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Board item type is required",
                    errors=["Board item type cannot be empty"]
                )
            
            if data.type not in ["component", "track", "via", "board"]:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Invalid board item type",
                    errors=["Type must be 'component', 'track', 'via', or 'board'"]
                )
            
            if not data.name:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Board item name is required",
                    errors=["Board item name cannot be empty"]
                )
            
            return ManagerResult(
                success=True,
                operation=ManagerOperation.VALIDATE,
                status=ManagerStatus.SUCCESS,
                message="Board item validation successful"
            )
        except Exception as e:
            return ManagerResult(
                success=False,
                operation=ManagerOperation.VALIDATE,
                status=ManagerStatus.FAILED,
                message=f"Board item validation failed: {e}",
                errors=[str(e)]
            )
    
    def _cleanup_item(self, key: str) -> None:
        """Clean up resources for a board item.
        
        Args:
            key: Board item ID to clean up
        """
        # Currently a no-op; placeholder for potential future board resource deallocation.
        self.logger.debug("BoardManager cleanup hook called for item '%s'", key)
    
    def _clear_cache(self) -> None:
        """Clear cache after data changes."""
        # Clear the cache - no additional operations needed
        super()._clear_cache() 
