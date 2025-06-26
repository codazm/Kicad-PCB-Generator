"""Advanced component placement system using KiCad 9's native functionality."""
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Set, Tuple, TYPE_CHECKING
import pcbnew

from ..base.base_manager import BaseManager
from ..base.results.manager_result import ManagerResult, ManagerOperation, ManagerStatus
from .manager import ComponentManager, ComponentData

if TYPE_CHECKING:
    from ..base.results.manager_result import ManagerResult

@dataclass
class PlacementGroup:
    """Component placement group configuration."""
    name: str
    components: List[str]  # List of component IDs
    alignment: str = "none"  # none, left, right, top, bottom, center
    distribution: str = "none"  # none, horizontal, vertical, grid
    spacing: float = 0.0  # Spacing between components
    rotation: float = 0.0  # Group rotation
    mirror: bool = False  # Group mirroring
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.metadata is None:
            self.metadata = {}

@dataclass
class PlacementItem:
    """Data structure for placement items."""
    group_name: str
    group: PlacementGroup
    board: pcbnew.BOARD
    component_manager: ComponentManager
    status: str = "pending"
    last_updated: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Validate required fields and set defaults."""
        if not self.group_name:
            raise ValueError("group_name is required")
        if not isinstance(self.group, PlacementGroup):
            raise ValueError("group must be a PlacementGroup instance")
        if not isinstance(self.board, pcbnew.BOARD):
            raise ValueError("board must be a pcbnew.BOARD instance")
        if not isinstance(self.component_manager, ComponentManager):
            raise ValueError("component_manager must be a ComponentManager instance")
        if self.metadata is None:
            self.metadata = {}

class PlacementManager(BaseManager[PlacementItem]):
    """Manages advanced component placement using KiCad 9's native functionality."""
    
    def __init__(self, board: pcbnew.BOARD, component_manager: ComponentManager, logger: Optional[logging.Logger] = None):
        """Initialize placement manager.
        
        Args:
            board: KiCad board object
            component_manager: Component manager instance
            logger: Optional logger instance
        """
        super().__init__()
        self.board = board
        self.component_manager = component_manager
        self.logger = logger or logging.getLogger(__name__)
        self.groups: Dict[str, PlacementGroup] = {}
    
    def _validate_data(self, data: PlacementItem) -> ManagerResult:
        """Validate placement item data.
        
        Args:
            data: Placement item to validate
            
        Returns:
            Manager result
        """
        try:
            # Basic validation
            if not isinstance(data, PlacementItem):
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Data must be a PlacementItem instance",
                    errors=["Invalid data type"]
                )
            
            # Validate group name
            if not data.group_name or not isinstance(data.group_name, str):
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Invalid group name",
                    errors=["group_name must be a non-empty string"]
                )
            
            # Validate group
            if not isinstance(data.group, PlacementGroup):
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Invalid group",
                    errors=["group must be a PlacementGroup instance"]
                )
            
            # Validate group name consistency
            if data.group.name != data.group_name:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Group name mismatch",
                    errors=["group.name must match group_name"]
                )
            
            # Validate components exist
            for comp_id in data.group.components:
                if not self.component_manager.get_component(comp_id):
                    return ManagerResult(
                        success=False,
                        operation=ManagerOperation.VALIDATE,
                        status=ManagerStatus.FAILED,
                        message="Invalid component",
                        errors=[f"Component {comp_id} not found in component manager"]
                    )
            
            # Validate alignment
            valid_alignments = ["none", "left", "right", "top", "bottom", "center"]
            if data.group.alignment not in valid_alignments:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Invalid alignment",
                    errors=[f"alignment must be one of {valid_alignments}"]
                )
            
            # Validate distribution
            valid_distributions = ["none", "horizontal", "vertical", "grid"]
            if data.group.distribution not in valid_distributions:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Invalid distribution",
                    errors=[f"distribution must be one of {valid_distributions}"]
                )
            
            # Validate spacing
            if data.group.spacing < 0:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Invalid spacing",
                    errors=["spacing must be non-negative"]
                )
            
            return ManagerResult(
                success=True,
                operation=ManagerOperation.VALIDATE,
                status=ManagerStatus.SUCCESS,
                message="Placement item validation successful"
            )
            
        except Exception as e:
            self.logger.error(f"Error validating placement item: {e}")
            return ManagerResult(
                success=False,
                operation=ManagerOperation.VALIDATE,
                status=ManagerStatus.FAILED,
                message=f"Validation error: {e}",
                errors=[str(e)]
            )
    
    def _cleanup_item(self, key: str) -> None:
        """Clean up resources for a placement item.
        
        Args:
            key: Key of the item to clean up
        """
        try:
            # Remove from groups if present
            if key in self.groups:
                del self.groups[key]
            
            self.logger.debug(f"Cleaned up placement item: {key}")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up placement item {key}: {e}")
    
    def add_placement_group(self, group: PlacementGroup) -> ManagerResult:
        """Add a placement group to the manager.
        
        Args:
            group: Placement group to add
            
        Returns:
            Manager result
        """
        try:
            # Create placement item
            item = PlacementItem(
                group_name=group.name,
                group=group,
                board=self.board,
                component_manager=self.component_manager,
                status="active"
            )
            
            # Add to manager
            result = self.create(group.name, item)
            
            if result.success:
                # Add to groups dictionary
                self.groups[group.name] = group
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error adding placement group {group.name}: {e}")
            return ManagerResult(
                success=False,
                operation=ManagerOperation.CREATE,
                status=ManagerStatus.FAILED,
                message=f"Error adding placement group: {e}",
                errors=[str(e)]
            )
    
    def create_group(self, group: PlacementGroup) -> bool:
        """Create a new component group.
        
        Args:
            group: Group configuration
            
        Returns:
            True if successful
        """
        result = self.add_placement_group(group)
        return result.success
    
    def update_group(self, group_name: str, **kwargs) -> bool:
        """Update an existing component group.
        
        Args:
            group_name: Group name
            **kwargs: Fields to update
            
        Returns:
            True if successful
        """
        try:
            if group_name not in self.groups:
                self.logger.error(f"Group {group_name} not found")
                return False
            
            # Get existing item
            result = self.read(group_name)
            if not result.success:
                return False
            
            # Update group
            group = self.groups[group_name]
            for key, value in kwargs.items():
                if hasattr(group, key):
                    setattr(group, key, value)
            
            # Validate components
            for comp_id in group.components:
                if not self.component_manager.get_component(comp_id):
                    self.logger.error(f"Component {comp_id} not found")
                    return False
            
            # Update item
            item = result.data
            item.group = group
            item.status = "updated"
            
            update_result = self.update(group_name, item)
            return update_result.success
            
        except Exception as e:
            self.logger.error(f"Failed to update group: {e}")
            return False
    
    def delete_group(self, group_name: str) -> bool:
        """Delete a component group.
        
        Args:
            group_name: Group name
            
        Returns:
            True if successful
        """
        result = self.delete(group_name)
        return result.success
    
    def align_components(self, group_name: str) -> bool:
        """Align components in a group.
        
        Args:
            group_name: Group name
            
        Returns:
            True if successful
        """
        try:
            if group_name not in self.groups:
                self.logger.error(f"Group {group_name} not found")
                return False
            
            group = self.groups[group_name]
            if group.alignment == "none":
                return True
            
            # Get component positions
            positions = []
            for comp_id in group.components:
                comp = self.component_manager.get_component(comp_id)
                if comp and comp.position:
                    positions.append(comp.position)
            
            if not positions:
                return True
            
            # Calculate alignment
            if group.alignment == "left":
                x = min(x for x, _ in positions)
                for comp_id in group.components:
                    comp = self.component_manager.get_component(comp_id)
                    if comp and comp.position:
                        _, y = comp.position
                        self.component_manager.update_component(comp_id, position=(x, y))
            
            elif group.alignment == "right":
                x = max(x for x, _ in positions)
                for comp_id in group.components:
                    comp = self.component_manager.get_component(comp_id)
                    if comp and comp.position:
                        _, y = comp.position
                        self.component_manager.update_component(comp_id, position=(x, y))
            
            elif group.alignment == "top":
                y = min(y for _, y in positions)
                for comp_id in group.components:
                    comp = self.component_manager.get_component(comp_id)
                    if comp and comp.position:
                        x, _ = comp.position
                        self.component_manager.update_component(comp_id, position=(x, y))
            
            elif group.alignment == "bottom":
                y = max(y for _, y in positions)
                for comp_id in group.components:
                    comp = self.component_manager.get_component(comp_id)
                    if comp and comp.position:
                        x, _ = comp.position
                        self.component_manager.update_component(comp_id, position=(x, y))
            
            elif group.alignment == "center":
                x = sum(x for x, _ in positions) / len(positions)
                y = sum(y for _, y in positions) / len(positions)
                for comp_id in group.components:
                    comp = self.component_manager.get_component(comp_id)
                    if comp and comp.position:
                        self.component_manager.update_component(comp_id, position=(x, y))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to align components: {e}")
            return False
    
    def distribute_components(self, group_name: str) -> bool:
        """Distribute components in a group.
        
        Args:
            group_name: Group name
            
        Returns:
            True if successful
        """
        try:
            if group_name not in self.groups:
                self.logger.error(f"Group {group_name} not found")
                return False
            
            group = self.groups[group_name]
            if group.distribution == "none":
                return True
            
            # Get component positions
            positions = []
            for comp_id in group.components:
                comp = self.component_manager.get_component(comp_id)
                if comp and comp.position:
                    positions.append(comp.position)
            
            if not positions:
                return True
            
            # Calculate distribution
            if group.distribution == "horizontal":
                x_min = min(x for x, _ in positions)
                x_max = max(x for x, _ in positions)
                spacing = (x_max - x_min) / (len(positions) - 1) if len(positions) > 1 else 0
                
                for i, comp_id in enumerate(group.components):
                    comp = self.component_manager.get_component(comp_id)
                    if comp and comp.position:
                        _, y = comp.position
                        x = x_min + i * spacing
                        self.component_manager.update_component(comp_id, position=(x, y))
            
            elif group.distribution == "vertical":
                y_min = min(y for _, y in positions)
                y_max = max(y for _, y in positions)
                spacing = (y_max - y_min) / (len(positions) - 1) if len(positions) > 1 else 0
                
                for i, comp_id in enumerate(group.components):
                    comp = self.component_manager.get_component(comp_id)
                    if comp and comp.position:
                        x, _ = comp.position
                        y = y_min + i * spacing
                        self.component_manager.update_component(comp_id, position=(x, y))
            
            elif group.distribution == "grid":
                # Calculate grid dimensions
                cols = int(len(positions) ** 0.5)
                rows = (len(positions) + cols - 1) // cols
                
                # Calculate spacing
                x_min = min(x for x, _ in positions)
                x_max = max(x for x, _ in positions)
                y_min = min(y for _, y in positions)
                y_max = max(y for _, y in positions)
                
                x_spacing = (x_max - x_min) / (cols - 1) if cols > 1 else 0
                y_spacing = (y_max - y_min) / (rows - 1) if rows > 1 else 0
                
                # Distribute in grid
                for i, comp_id in enumerate(group.components):
                    comp = self.component_manager.get_component(comp_id)
                    if comp and comp.position:
                        col = i % cols
                        row = i // cols
                        x = x_min + col * x_spacing
                        y = y_min + row * y_spacing
                        self.component_manager.update_component(comp_id, position=(x, y))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to distribute components: {e}")
            return False
    
    def rotate_group(self, group_name: str) -> bool:
        """Rotate a component group.
        
        Args:
            group_name: Group name
            
        Returns:
            True if successful
        """
        try:
            if group_name not in self.groups:
                self.logger.error(f"Group {group_name} not found")
                return False
            
            group = self.groups[group_name]
            if group.rotation == 0:
                return True
            
            # Get group center
            positions = []
            for comp_id in group.components:
                comp = self.component_manager.get_component(comp_id)
                if comp and comp.position:
                    positions.append(comp.position)
            
            if not positions:
                return True
            
            center_x = sum(x for x, _ in positions) / len(positions)
            center_y = sum(y for _, y in positions) / len(positions)
            
            # Rotate components
            import math
            angle_rad = math.radians(group.rotation)
            cos_a = math.cos(angle_rad)
            sin_a = math.sin(angle_rad)
            
            for comp_id in group.components:
                comp = self.component_manager.get_component(comp_id)
                if comp and comp.position:
                    x, y = comp.position
                    # Calculate new position after rotation
                    dx = x - center_x
                    dy = y - center_y
                    new_x = center_x + dx * cos_a - dy * sin_a
                    new_y = center_y + dx * sin_a + dy * cos_a
                    self.component_manager.update_component(comp_id, position=(new_x, new_y))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to rotate group: {e}")
            return False
    
    def mirror_group(self, group_name: str) -> bool:
        """Mirror a component group.
        
        Args:
            group_name: Group name
            
        Returns:
            True if successful
        """
        try:
            if group_name not in self.groups:
                self.logger.error(f"Group {group_name} not found")
                return False
            
            group = self.groups[group_name]
            if not group.mirror:
                return True
            
            # Get group center
            positions = []
            for comp_id in group.components:
                comp = self.component_manager.get_component(comp_id)
                if comp and comp.position:
                    positions.append(comp.position)
            
            if not positions:
                return True
            
            center_x = sum(x for x, _ in positions) / len(positions)
            
            # Mirror components
            for comp_id in group.components:
                comp = self.component_manager.get_component(comp_id)
                if comp and comp.position:
                    x, y = comp.position
                    # Calculate new position after mirroring
                    new_x = 2 * center_x - x
                    self.component_manager.update_component(comp_id, position=(new_x, y))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to mirror group: {e}")
            return False
    
    def swap_components(self, comp1_id: str, comp2_id: str) -> bool:
        """Swap positions of two components.
        
        Args:
            comp1_id: First component ID
            comp2_id: Second component ID
            
        Returns:
            True if successful
        """
        try:
            # Get components
            comp1 = self.component_manager.get_component(comp1_id)
            comp2 = self.component_manager.get_component(comp2_id)
            
            if not comp1 or not comp2:
                self.logger.error("One or both components not found")
                return False
            
            if not comp1.position or not comp2.position:
                self.logger.error("One or both components have no position")
                return False
            
            # Swap positions
            pos1 = comp1.position
            pos2 = comp2.position
            
            self.component_manager.update_component(comp1_id, position=pos2)
            self.component_manager.update_component(comp2_id, position=pos1)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to swap components: {e}")
            return False 