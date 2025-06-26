"""Board size presets for common audio PCB standards."""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from enum import Enum


class BoardProfile(Enum):
    """Common audio PCB board profiles."""
    # Eurorack standards
    EURORACK_3U = "eurorack_3u"
    EURORACK_6U = "eurorack_6u"
    EURORACK_1U = "eurorack_1u"
    
    # Guitar pedal standards
    PEDAL_STANDARD = "pedal_standard"
    PEDAL_MINI = "pedal_mini"
    PEDAL_LARGE = "pedal_large"
    
    # Studio equipment
    RACK_1U = "rack_1u"
    RACK_2U = "rack_2u"
    RACK_3U = "rack_3u"
    
    # Custom sizes
    CUSTOM = "custom"


@dataclass
class BoardPreset:
    """Board size preset configuration."""
    name: str
    description: str
    width_mm: float
    height_mm: float
    max_thickness_mm: float
    min_track_width_mm: float
    min_via_diameter_mm: float
    min_clearance_mm: float
    max_component_height_mm: float
    mounting_holes: Optional[Tuple[float, float, float, float]] = None  # (x1, y1, x2, y2) in mm
    edge_clearance_mm: float = 2.0
    manufacturing_constraints: Optional[Dict] = None


class BoardPresetRegistry:
    """Registry for board size presets."""
    
    def __init__(self):
        self._presets: Dict[BoardProfile, BoardPreset] = {}
        self._initialize_presets()
    
    def _initialize_presets(self) -> None:
        """Initialize all board presets."""
        
        # Eurorack 3U (most common)
        self._presets[BoardProfile.EURORACK_3U] = BoardPreset(
            name="Eurorack 3U",
            description="Standard Eurorack 3U module (128.5mm x 128.5mm)",
            width_mm=128.5,
            height_mm=128.5,
            max_thickness_mm=1.6,
            min_track_width_mm=0.2,
            min_via_diameter_mm=0.3,
            min_clearance_mm=0.2,
            max_component_height_mm=25.0,
            mounting_holes=(3.5, 3.5, 125.0, 125.0),
            edge_clearance_mm=2.0,
            manufacturing_constraints={
                "min_hole_size": 0.3,
                "max_hole_size": 3.5,
                "copper_weight": 1,
                "solder_mask": True,
                "silkscreen": True
            }
        )
        
        # Eurorack 6U
        self._presets[BoardProfile.EURORACK_6U] = BoardPreset(
            name="Eurorack 6U",
            description="Standard Eurorack 6U module (128.5mm x 256.5mm)",
            width_mm=128.5,
            height_mm=256.5,
            max_thickness_mm=1.6,
            min_track_width_mm=0.2,
            min_via_diameter_mm=0.3,
            min_clearance_mm=0.2,
            max_component_height_mm=25.0,
            mounting_holes=(3.5, 3.5, 125.0, 253.0),
            edge_clearance_mm=2.0,
            manufacturing_constraints={
                "min_hole_size": 0.3,
                "max_hole_size": 3.5,
                "copper_weight": 1,
                "solder_mask": True,
                "silkscreen": True
            }
        )
        
        # Eurorack 1U
        self._presets[BoardProfile.EURORACK_1U] = BoardPreset(
            name="Eurorack 1U",
            description="Standard Eurorack 1U module (128.5mm x 42.5mm)",
            width_mm=128.5,
            height_mm=42.5,
            max_thickness_mm=1.6,
            min_track_width_mm=0.2,
            min_via_diameter_mm=0.3,
            min_clearance_mm=0.2,
            max_component_height_mm=15.0,
            mounting_holes=(3.5, 3.5, 125.0, 39.0),
            edge_clearance_mm=2.0,
            manufacturing_constraints={
                "min_hole_size": 0.3,
                "max_hole_size": 3.5,
                "copper_weight": 1,
                "solder_mask": True,
                "silkscreen": True
            }
        )
        
        # Standard guitar pedal
        self._presets[BoardProfile.PEDAL_STANDARD] = BoardPreset(
            name="Standard Guitar Pedal",
            description="Standard guitar pedal enclosure (125mm x 60mm)",
            width_mm=125.0,
            height_mm=60.0,
            max_thickness_mm=1.6,
            min_track_width_mm=0.2,
            min_via_diameter_mm=0.3,
            min_clearance_mm=0.2,
            max_component_height_mm=20.0,
            mounting_holes=(3.5, 3.5, 121.5, 56.5),
            edge_clearance_mm=2.0,
            manufacturing_constraints={
                "min_hole_size": 0.3,
                "max_hole_size": 3.5,
                "copper_weight": 1,
                "solder_mask": True,
                "silkscreen": True
            }
        )
        
        # Mini guitar pedal
        self._presets[BoardProfile.PEDAL_MINI] = BoardPreset(
            name="Mini Guitar Pedal",
            description="Mini guitar pedal enclosure (90mm x 40mm)",
            width_mm=90.0,
            height_mm=40.0,
            max_thickness_mm=1.6,
            min_track_width_mm=0.15,
            min_via_diameter_mm=0.25,
            min_clearance_mm=0.15,
            max_component_height_mm=15.0,
            mounting_holes=(3.5, 3.5, 86.5, 36.5),
            edge_clearance_mm=1.5,
            manufacturing_constraints={
                "min_hole_size": 0.25,
                "max_hole_size": 3.5,
                "copper_weight": 1,
                "solder_mask": True,
                "silkscreen": True
            }
        )
        
        # Large guitar pedal
        self._presets[BoardProfile.PEDAL_LARGE] = BoardPreset(
            name="Large Guitar Pedal",
            description="Large guitar pedal enclosure (150mm x 80mm)",
            width_mm=150.0,
            height_mm=80.0,
            max_thickness_mm=1.6,
            min_track_width_mm=0.2,
            min_via_diameter_mm=0.3,
            min_clearance_mm=0.2,
            max_component_height_mm=25.0,
            mounting_holes=(3.5, 3.5, 146.5, 76.5),
            edge_clearance_mm=2.0,
            manufacturing_constraints={
                "min_hole_size": 0.3,
                "max_hole_size": 3.5,
                "copper_weight": 1,
                "solder_mask": True,
                "silkscreen": True
            }
        )
        
        # Rack 1U
        self._presets[BoardProfile.RACK_1U] = BoardPreset(
            name="Rack 1U",
            description="Standard 19\" rack 1U module (483mm x 44mm)",
            width_mm=483.0,
            height_mm=44.0,
            max_thickness_mm=1.6,
            min_track_width_mm=0.2,
            min_via_diameter_mm=0.3,
            min_clearance_mm=0.2,
            max_component_height_mm=15.0,
            mounting_holes=(3.5, 3.5, 479.5, 40.5),
            edge_clearance_mm=2.0,
            manufacturing_constraints={
                "min_hole_size": 0.3,
                "max_hole_size": 3.5,
                "copper_weight": 1,
                "solder_mask": True,
                "silkscreen": True
            }
        )
        
        # Rack 2U
        self._presets[BoardProfile.RACK_2U] = BoardPreset(
            name="Rack 2U",
            description="Standard 19\" rack 2U module (483mm x 88mm)",
            width_mm=483.0,
            height_mm=88.0,
            max_thickness_mm=1.6,
            min_track_width_mm=0.2,
            min_via_diameter_mm=0.3,
            min_clearance_mm=0.2,
            max_component_height_mm=25.0,
            mounting_holes=(3.5, 3.5, 479.5, 84.5),
            edge_clearance_mm=2.0,
            manufacturing_constraints={
                "min_hole_size": 0.3,
                "max_hole_size": 3.5,
                "copper_weight": 1,
                "solder_mask": True,
                "silkscreen": True
            }
        )
        
        # Rack 3U
        self._presets[BoardProfile.RACK_3U] = BoardPreset(
            name="Rack 3U",
            description="Standard 19\" rack 3U module (483mm x 132mm)",
            width_mm=483.0,
            height_mm=132.0,
            max_thickness_mm=1.6,
            min_track_width_mm=0.2,
            min_via_diameter_mm=0.3,
            min_clearance_mm=0.2,
            max_component_height_mm=35.0,
            mounting_holes=(3.5, 3.5, 479.5, 128.5),
            edge_clearance_mm=2.0,
            manufacturing_constraints={
                "min_hole_size": 0.3,
                "max_hole_size": 3.5,
                "copper_weight": 1,
                "solder_mask": True,
                "silkscreen": True
            }
        )
    
    def get_preset(self, profile: BoardProfile) -> Optional[BoardPreset]:
        """Get a board preset by profile.
        
        Args:
            profile: Board profile enum
            
        Returns:
            Board preset or None if not found
        """
        return self._presets.get(profile)
    
    def get_preset_by_name(self, name: str) -> Optional[BoardPreset]:
        """Get a board preset by name.
        
        Args:
            name: Preset name (case-insensitive)
            
        Returns:
            Board preset or None if not found
        """
        name_lower = name.lower()
        for preset in self._presets.values():
            if preset.name.lower() == name_lower:
                return preset
        return None
    
    def list_presets(self) -> Dict[BoardProfile, BoardPreset]:
        """Get all available presets.
        
        Returns:
            Dictionary of all presets
        """
        return self._presets.copy()
    
    def get_preset_names(self) -> Dict[str, str]:
        """Get a mapping of profile values to display names.
        
        Returns:
            Dictionary mapping profile values to display names
        """
        return {profile.value: preset.name for profile, preset in self._presets.items()}
    
    def validate_board_size(self, width_mm: float, height_mm: float, profile: BoardProfile) -> bool:
        """Validate if board dimensions match a preset.
        
        Args:
            width_mm: Board width in mm
            height_mm: Board height in mm
            profile: Expected board profile
            
        Returns:
            True if dimensions match preset within tolerance
        """
        preset = self.get_preset(profile)
        if not preset:
            return False
        
        # Allow 1mm tolerance for manufacturing variations
        tolerance = 1.0
        width_match = abs(width_mm - preset.width_mm) <= tolerance
        height_match = abs(height_mm - preset.height_mm) <= tolerance
        
        return width_match and height_match
    
    def get_manufacturing_constraints(self, profile: BoardProfile) -> Optional[Dict]:
        """Get manufacturing constraints for a profile.
        
        Args:
            profile: Board profile
            
        Returns:
            Manufacturing constraints dictionary or None
        """
        preset = self.get_preset(profile)
        return preset.manufacturing_constraints if preset else None


# Global registry instance
board_preset_registry = BoardPresetRegistry() 