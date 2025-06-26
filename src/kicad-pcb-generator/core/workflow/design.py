"""Design variant management system using KiCad 9's native functionality."""
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, TYPE_CHECKING
import pcbnew
from ..components.manager import ComponentManager, ComponentData
from ..board.layer_manager import LayerManager, LayerProperties
from ..base.base_manager import BaseManager
from ..base.results.manager_result import ManagerResult

if TYPE_CHECKING:
    from ..base.results.manager_result import ManagerResult

@dataclass
class DesignVariant:
    """PCB design variant configuration."""
    name: str
    description: str
    components: Dict[str, ComponentData]
    layer_stack: Optional[LayerProperties] = None
    rules: Dict[str, Any] = None
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        """Initialize default values."""
        if self.rules is None:
            self.rules = {}
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = self.created_at

@dataclass
class DesignItem:
    """Data structure for design items."""
    id: str
    variant: DesignVariant
    board_file: str
    status: str = "active"  # active, inactive, archived
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    error_message: Optional[str] = None
    validation_results: Dict[str, Any] = None

class DesignManager(BaseManager[DesignItem]):
    """Manages PCB design variants using KiCad 9's native functionality."""
    
    def __init__(self, board: pcbnew.BOARD, logger: Optional[logging.Logger] = None):
        """Initialize design manager.
        
        Args:
            board: KiCad board object
            logger: Optional logger instance
        """
        super().__init__(logger=logger or logging.getLogger(__name__))
        self.board = board
        self.component_manager = ComponentManager(str(board.GetFileName()), logger=self.logger)
        self.layer_manager = LayerManager(board, logger=self.logger)
        self.variants: Dict[str, DesignVariant] = {}
        
        # Initialize variants
        self._load_variants()
    
    def _validate_data(self, item: DesignItem) -> bool:
        """Validate design item data."""
        if not item.id or not isinstance(item.id, str):
            self.logger.error("Design item must have a valid string ID")
            return False
        
        if not item.variant or not isinstance(item.variant, DesignVariant):
            self.logger.error("Design item must have a valid DesignVariant")
            return False
        
        if not item.variant.name or not isinstance(item.variant.name, str):
            self.logger.error("Design variant must have a valid name")
            return False
        
        if not item.variant.description or not isinstance(item.variant.description, str):
            self.logger.error("Design variant must have a valid description")
            return False
        
        if not item.board_file or not isinstance(item.board_file, str):
            self.logger.error("Design item must have a valid board file path")
            return False
        
        if item.variant.components and not isinstance(item.variant.components, dict):
            self.logger.error("Design variant must have valid components dictionary")
            return False
        
        if item.variant.rules and not isinstance(item.variant.rules, dict):
            self.logger.error("Design variant must have valid rules dictionary")
            return False
        
        return True
    
    def _cleanup_item(self, item: DesignItem) -> None:
        """Clean up design item resources."""
        try:
            # Clean up any temporary files or resources
            if item.variant:
                # Currently nothing to clean for variants; placeholder for future resource management.
                self.logger.debug("DesignManager cleanup placeholder for variant '%s'", item.variant.name)
            
            self.logger.debug(f"Cleaned up design item: {item.id}")
        except Exception as e:
            self.logger.warning(f"Error during design item cleanup: {str(e)}")
    
    def _clear_cache(self) -> None:
        """Clear design manager cache."""
        try:
            # Clear any cached variant data or temporary files
            self.variants.clear()
            self.logger.debug("Cleared design manager cache")
        except Exception as e:
            self.logger.warning(f"Error clearing design manager cache: {str(e)}")
    
    def create_design_item(self, 
                          variant: DesignVariant, 
                          board_file: str) -> ManagerResult[DesignItem]:
        """Create a new design item."""
        try:
            design_id = f"design_{variant.name}_{len(self._items) + 1}"
            design_item = DesignItem(
                id=design_id,
                variant=variant,
                board_file=board_file,
                status="active",
                validation_results={}
            )
            
            result = self.create(design_item)
            if result.success:
                self.logger.info(f"Created design item: {design_id}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error creating design item: {str(e)}")
            return ManagerResult[DesignItem](
                success=False,
                error_message=str(e),
                data=None
            )
    
    def process_design_item(self, design_id: str) -> ManagerResult[DesignItem]:
        """Process a design item."""
        try:
            # Get the design item
            result = self.get(design_id)
            if not result.success or not result.data:
                return ManagerResult[DesignItem](
                    success=False,
                    error_message=f"Design item not found: {design_id}",
                    data=None
                )
            
            design_item = result.data
            
            # Update status to processing
            design_item.status = "active"
            self.update(design_item)
            
            # Validate design variant
            validation_results = self.validate_design_variant(design_item.variant)
            
            # Update design item with validation results
            design_item.validation_results = validation_results
            design_item.status = "active" if validation_results.get("is_valid", False) else "inactive"
            if not validation_results.get("is_valid", False):
                design_item.error_message = "Design variant validation failed"
            
            # Update the item
            update_result = self.update(design_item)
            if update_result.success:
                self.logger.info(f"Processed design item: {design_id}")
            
            return update_result
            
        except Exception as e:
            self.logger.error(f"Error processing design item {design_id}: {str(e)}")
            return ManagerResult[DesignItem](
                success=False,
                error_message=str(e),
                data=None
            )
    
    def validate_design_variant(self, variant: DesignVariant) -> Dict[str, Any]:
        """Validate design variant."""
        validation_results = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Validate variant name
        if not variant.name or len(variant.name.strip()) == 0:
            validation_results["is_valid"] = False
            validation_results["errors"].append("Variant name cannot be empty")
        
        # Validate description
        if not variant.description or len(variant.description.strip()) == 0:
            validation_results["warnings"].append("Variant description is empty")
        
        # Validate components
        if variant.components:
            for comp_id, comp_data in variant.components.items():
                if not comp_id or not isinstance(comp_id, str):
                    validation_results["errors"].append(f"Invalid component ID: {comp_id}")
                if not comp_data or not isinstance(comp_data, ComponentData):
                    validation_results["errors"].append(f"Invalid component data for: {comp_id}")
        
        # Validate rules
        if variant.rules:
            for rule_name, rule_value in variant.rules.items():
                if not rule_name or not isinstance(rule_name, str):
                    validation_results["errors"].append(f"Invalid rule name: {rule_name}")
        
        # Update overall validity
        if validation_results["errors"]:
            validation_results["is_valid"] = False
        
        return validation_results
    
    def _load_variants(self) -> None:
        """Load design variants from board."""
        try:
            # Get variant data from board
            variant_data = self.board.GetDesignSettings().GetVariantData()
            if not variant_data:
                return
            
            # Load each variant
            for variant_name in variant_data.GetVariantNames():
                variant = DesignVariant(
                    name=variant_name,
                    description=variant_data.GetVariantDescription(variant_name),
                    components=self._load_variant_components(variant_name),
                    layer_stack=self._load_variant_layer_stack(variant_name),
                    rules=self._load_variant_rules(variant_name)
                )
                self.variants[variant_name] = variant
                
        except Exception as e:
            self.logger.error(f"Failed to load variants: {e}")
    
    def _load_variant_components(self, variant_name: str) -> Dict[str, ComponentData]:
        """Load components for a variant.
        
        Args:
            variant_name: Variant name
            
        Returns:
            Dictionary of components
        """
        components = {}
        try:
            # Get variant data
            variant_data = self.board.GetDesignSettings().GetVariantData()
            if not variant_data:
                return components
            
            # Get components for variant
            for component in self.board.GetModules():
                if variant_data.HasVariant(component.GetReference(), variant_name):
                    # Get component data
                    comp_data = ComponentData(
                        id=component.GetReference(),
                        type=component.GetTypeName(),
                        value=component.GetValue(),
                        footprint=component.GetFPID().GetLibItemName(),
                        position=(component.GetPosition().x, component.GetPosition().y),
                        orientation=component.GetOrientationDegrees(),
                        layer=component.GetLayerName()
                    )
                    components[comp_data.id] = comp_data
            
        except Exception as e:
            self.logger.error(f"Failed to load variant components: {e}")
        
        return components
    
    def _load_variant_layer_stack(self, variant_name: str) -> Optional[LayerProperties]:
        """Load layer stack for a variant.
        
        Args:
            variant_name: Variant name
            
        Returns:
            Layer properties if found
        """
        try:
            # Get variant data
            variant_data = self.board.GetDesignSettings().GetVariantData()
            if not variant_data:
                return None
            
            # Get layer stack for variant
            if variant_data.HasLayerStack(variant_name):
                return self.layer_manager.get_layer_properties(0)  # Get first layer as example
            
        except Exception as e:
            self.logger.error(f"Failed to load variant layer stack: {e}")
        
        return None
    
    def _load_variant_rules(self, variant_name: str) -> Dict[str, Any]:
        """Load rules for a variant.
        
        Args:
            variant_name: Variant name
            
        Returns:
            Dictionary of rules
        """
        rules = {}
        try:
            # Get variant data
            variant_data = self.board.GetDesignSettings().GetVariantData()
            if not variant_data:
                return rules
            
            # Get rules for variant
            if variant_data.HasRules(variant_name):
                rules = variant_data.GetRules(variant_name)
            
        except Exception as e:
            self.logger.error(f"Failed to load variant rules: {e}")
        
        return rules
    
    def create_variant(self, variant: DesignVariant) -> bool:
        """Create a new design variant.
        
        Args:
            variant: Variant configuration
            
        Returns:
            True if successful
        """
        try:
            if variant.name in self.variants:
                self.logger.error(f"Variant {variant.name} already exists")
                return False
            
            # Create variant in board
            variant_data = self.board.GetDesignSettings().GetVariantData()
            variant_data.AddVariant(variant.name, variant.description)
            
            # Add components
            for comp_id, comp_data in variant.components.items():
                variant_data.AddComponent(comp_id, variant.name)
            
            # Add layer stack
            if variant.layer_stack:
                variant_data.SetLayerStack(variant.name, variant.layer_stack.to_dict())
            
            # Add rules
            if variant.rules:
                variant_data.SetRules(variant.name, variant.rules)
            
            # Save variant
            self.variants[variant.name] = variant
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create variant: {e}")
            return False
    
    def update_variant(self, variant_name: str, **kwargs) -> bool:
        """Update an existing design variant.
        
        Args:
            variant_name: Variant name
            **kwargs: Fields to update
            
        Returns:
            True if successful
        """
        try:
            if variant_name not in self.variants:
                self.logger.error(f"Variant {variant_name} not found")
                return False
            
            # Get variant data
            variant_data = self.board.GetDesignSettings().GetVariantData()
            if not variant_data:
                return False
            
            # Update variant
            variant = self.variants[variant_name]
            for key, value in kwargs.items():
                if hasattr(variant, key):
                    setattr(variant, key, value)
            
            # Update in board
            variant_data.SetVariantDescription(variant_name, variant.description)
            
            # Update components
            for comp_id, comp_data in variant.components.items():
                variant_data.AddComponent(comp_id, variant_name)
            
            # Update layer stack
            if variant.layer_stack:
                variant_data.SetLayerStack(variant_name, variant.layer_stack.to_dict())
            
            # Update rules
            if variant.rules:
                variant_data.SetRules(variant_name, variant.rules)
            
            # Save variant
            variant.updated_at = datetime.now()
            self.variants[variant_name] = variant
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update variant: {e}")
            return False
    
    def delete_variant(self, variant_name: str) -> bool:
        """Delete a design variant.
        
        Args:
            variant_name: Variant name
            
        Returns:
            True if successful
        """
        try:
            if variant_name not in self.variants:
                self.logger.error(f"Variant {variant_name} not found")
                return False
            
            # Delete variant from board
            variant_data = self.board.GetDesignSettings().GetVariantData()
            if variant_data:
                variant_data.RemoveVariant(variant_name)
            
            # Remove from variants
            del self.variants[variant_name]
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete variant: {e}")
            return False
    
    def get_variant(self, variant_name: str) -> Optional[DesignVariant]:
        """Get a design variant by name.
        
        Args:
            variant_name: Variant name
            
        Returns:
            Variant if found
        """
        return self.variants.get(variant_name)
    
    def get_variants(self) -> Dict[str, DesignVariant]:
        """Get all design variants.
        
        Returns:
            Dictionary of variants
        """
        return self.variants
    
    def switch_variant(self, variant_name: str) -> bool:
        """Switch to a different design variant.
        
        Args:
            variant_name: Variant name
            
        Returns:
            True if successful
        """
        try:
            if variant_name not in self.variants:
                self.logger.error(f"Variant {variant_name} not found")
                return False
            
            # Get variant data
            variant_data = self.board.GetDesignSettings().GetVariantData()
            if not variant_data:
                return False
            
            # Switch variant
            variant_data.SetCurrentVariant(variant_name)
            
            # Update board
            self.board.SetDesignSettings(variant_data)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to switch variant: {e}")
            return False 
