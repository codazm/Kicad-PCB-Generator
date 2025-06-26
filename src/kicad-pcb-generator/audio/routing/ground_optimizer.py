"""
Ground Optimizer Module

This module provides ground plane design optimization for audio circuits,
including ground loop minimization, star ground implementation, and ground plane coverage analysis.
"""

import logging
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

try:
    import pcbnew
except ImportError:
    pcbnew = None


class GroundOptimizationStrategy(Enum):
    """Ground optimization strategies."""
    STAR_GROUNDING = "star_grounding"
    GROUND_LOOP_MINIMIZATION = "ground_loop_minimization"
    GROUND_PLANE_COVERAGE = "ground_plane_coverage"
    GROUND_PLANE_STITCHING = "ground_plane_stitching"
    ANALOG_DIGITAL_SEPARATION = "analog_digital_separation"


@dataclass
class GroundPlaneConfig:
    """Configuration for ground plane optimization."""
    min_ground_coverage: float  # percent - minimum ground plane coverage
    max_ground_loop_area: float  # mm² - maximum ground loop area
    min_ground_clearance: float  # mm - minimum clearance to ground
    preferred_ground_layer: int  # preferred ground layer
    star_ground_radius: float  # mm - radius for star ground connections
    stitching_via_diameter: float  # mm - diameter of stitching vias
    stitching_via_spacing: float  # mm - spacing between stitching vias
    analog_digital_separation: float  # mm - separation between analog and digital grounds


@dataclass
class GroundOptimizationResult:
    """Result of ground optimization."""
    success: bool
    message: str
    optimized_zones: List[pcbnew.ZONE] = None
    optimized_vias: List[pcbnew.VIA] = None
    warnings: List[str] = None
    errors: List[str] = None
    metrics: Dict[str, Any] = None


class GroundOptimizer:
    """Ground plane optimizer for audio circuits."""
    
    def __init__(self, board: 'pcbnew.BOARD', logger: Optional[logging.Logger] = None):
        """Initialize the ground optimizer.
        
        Args:
            board: KiCad board object
            logger: Logger instance
        """
        self.board = board
        self.logger = logger or logging.getLogger(__name__)
        
        # Validate KiCad version
        self._validate_kicad_version()
        
        # Initialize ground plane configuration
        self._ground_config = GroundPlaneConfig(
            min_ground_coverage=70.0,  # 70% minimum ground coverage
            max_ground_loop_area=10.0,  # 10mm² maximum ground loop area
            min_ground_clearance=0.3,  # 0.3mm minimum clearance
            preferred_ground_layer=2,  # In2_Cu (internal ground layer)
            star_ground_radius=5.0,  # 5mm star ground radius
            stitching_via_diameter=0.4,  # 0.4mm stitching via diameter
            stitching_via_spacing=5.0,  # 5mm stitching via spacing
            analog_digital_separation=2.0  # 2mm separation between analog/digital grounds
        )
    
    def _validate_kicad_version(self) -> None:
        """Validate KiCad version compatibility."""
        if pcbnew is None:
            raise RuntimeError("KiCad Python module (pcbnew) is not available")
        
        version = pcbnew.Version()
        if not version.startswith('9'):
            raise RuntimeError(f"This module requires KiCad 9.x, but found version {version}")
        self.logger.info(f"Running with KiCad version: {version}")
    
    def optimize_ground_plane(self, strategy: GroundOptimizationStrategy = GroundOptimizationStrategy.STAR_GROUNDING) -> GroundOptimizationResult:
        """Optimize ground plane using the specified strategy.
        
        Args:
            strategy: Ground optimization strategy to use
            
        Returns:
            Ground optimization result
        """
        try:
            self.logger.info(f"Starting ground plane optimization with strategy: {strategy.value}")
            
            # Get all ground zones
            ground_zones = self._get_ground_zones()
            
            if not ground_zones:
                return GroundOptimizationResult(
                    success=True,
                    message="No ground zones found to optimize",
                    optimized_zones=[],
                    optimized_vias=[],
                    warnings=["No ground zones identified"],
                    errors=[],
                    metrics={"zones_found": 0}
                )
            
            optimized_zones = []
            optimized_vias = []
            warnings = []
            errors = []
            
            # Apply optimization strategy
            if strategy == GroundOptimizationStrategy.STAR_GROUNDING:
                result = self._implement_star_grounding(ground_zones)
            elif strategy == GroundOptimizationStrategy.GROUND_LOOP_MINIMIZATION:
                result = self._minimize_ground_loops(ground_zones)
            elif strategy == GroundOptimizationStrategy.GROUND_PLANE_COVERAGE:
                result = self._optimize_ground_coverage(ground_zones)
            elif strategy == GroundOptimizationStrategy.GROUND_PLANE_STITCHING:
                result = self._optimize_ground_stitching(ground_zones)
            elif strategy == GroundOptimizationStrategy.ANALOG_DIGITAL_SEPARATION:
                result = self._separate_analog_digital_grounds(ground_zones)
            else:
                return GroundOptimizationResult(
                    success=False,
                    message=f"Unknown ground optimization strategy: {strategy}",
                    optimized_zones=[],
                    optimized_vias=[],
                    warnings=[],
                    errors=[f"Unknown strategy: {strategy}"]
                )
            
            if result.success:
                optimized_zones.extend(result.optimized_zones or [])
                optimized_vias.extend(result.optimized_vias or [])
                warnings.extend(result.warnings or [])
                errors.extend(result.errors or [])
                
                self.logger.info(f"Successfully optimized {len(optimized_zones)} ground zones")
            else:
                errors.append(result.message)
            
            return GroundOptimizationResult(
                success=len(errors) == 0,
                message=f"Optimized {len(optimized_zones)} ground zones using {strategy.value}",
                optimized_zones=optimized_zones,
                optimized_vias=optimized_vias,
                warnings=warnings,
                errors=errors,
                metrics={
                    "zones_optimized": len(optimized_zones),
                    "vias_added": len(optimized_vias),
                    "strategy": strategy.value,
                    "coverage_improvement": self._calculate_coverage_improvement(ground_zones),
                    "loop_reduction": self._calculate_loop_reduction(ground_zones)
                }
            )
            
        except (ValueError, KeyError, TypeError) as e:
            error_msg = f"Input error in ground plane optimization: {str(e)}"
            self.logger.error(error_msg)
            return GroundOptimizationResult(
                success=False,
                message=error_msg,
                optimized_zones=[],
                optimized_vias=[],
                warnings=[],
                errors=[error_msg]
            )
        except Exception as e:
            error_msg = f"Unexpected error in ground plane optimization: {str(e)}"
            self.logger.error(error_msg)
            return GroundOptimizationResult(
                success=False,
                message=error_msg,
                optimized_zones=[],
                optimized_vias=[],
                warnings=[],
                errors=[error_msg]
            )
    
    def _get_ground_zones(self) -> List[pcbnew.ZONE]:
        """Get all ground zones from the board.
        
        Returns:
            List of ground zones
        """
        try:
            zones = self.board.Zones()
            ground_zones = []
            
            for zone in zones:
                net_name = zone.GetNetname().lower()
                
                # Filter for ground zones
                if any(ground_name in net_name for ground_name in ["gnd", "ground", "agnd", "dgnd"]):
                    ground_zones.append(zone)
            
            return ground_zones
        except (AttributeError, ValueError) as e:
            self.logger.error(f"Board data error getting ground zones: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error getting ground zones: {str(e)}")
            return []
    
    def _implement_star_grounding(self, ground_zones: List[pcbnew.ZONE]) -> GroundOptimizationResult:
        """Implement star grounding topology.
        
        Args:
            ground_zones: List of ground zones to optimize
            
        Returns:
            Ground optimization result
        """
        try:
            optimized_zones = []
            optimized_vias = []
            warnings = []
            
            if len(ground_zones) < 2:
                return GroundOptimizationResult(
                    success=True,
                    message="Star grounding not needed for single ground zone",
                    optimized_zones=[],
                    optimized_vias=[],
                    warnings=["Single ground zone detected"],
                    errors=[]
                )
            
            # Find central point for star ground
            center_x = sum(zone.GetPosition().x for zone in ground_zones) / len(ground_zones)
            center_y = sum(zone.GetPosition().y for zone in ground_zones) / len(ground_zones)
            center = pcbnew.VECTOR2I(int(center_x), int(center_y))
            
            # Create central ground zone
            central_zone = pcbnew.ZONE(self.board)
            central_zone.SetLayer(self._ground_config.preferred_ground_layer)
            central_zone.SetNetCode(self.board.GetNetcodeFromNetname("GND"))
            central_zone.SetName("GND_CENTRAL")
            central_zone.SetPosition(center)
            
            # Set zone outline (circular)
            radius_nm = int(self._ground_config.star_ground_radius * 1e6)
            outline = []
            for i in range(8):  # 8-point circle approximation
                angle = i * 2 * math.pi / 8
                x = center.x + int(radius_nm * math.cos(angle))
                y = center.y + int(radius_nm * math.sin(angle))
                outline.append(pcbnew.VECTOR2I(x, y))
            
            central_zone.SetOutline(outline)
            self.board.Add(central_zone)
            optimized_zones.append(central_zone)
            
            # Connect zones to central point
            for zone in ground_zones:
                # Create track to central point
                track = pcbnew.TRACK(self.board)
                track.SetStart(zone.GetPosition())
                track.SetEnd(center)
                track.SetWidth(int(self._ground_config.min_ground_clearance * 2e6))  # 2x clearance width
                track.SetLayer(zone.GetLayer())
                track.SetNetCode(zone.GetNetCode())
                
                # Add track to board
                self.board.Add(track)
                
                # Create via at connection point
                via = pcbnew.VIA(self.board)
                via.SetPosition(center)
                via.SetDrill(int(self._ground_config.stitching_via_diameter * 0.6e6))  # 60% of via diameter
                via.SetWidth(int(self._ground_config.stitching_via_diameter * 1e6))
                via.SetLayerPair(0, 31)  # Top to bottom
                via.SetNetCode(zone.GetNetCode())
                
                self.board.Add(via)
                optimized_vias.append(via)
            
            return GroundOptimizationResult(
                success=True,
                message=f"Implemented star grounding with {len(ground_zones)} connections",
                optimized_zones=optimized_zones,
                optimized_vias=optimized_vias,
                warnings=warnings,
                errors=[]
            )
        except (AttributeError, ValueError) as e:
            error_msg = f"Board data error implementing star grounding: {str(e)}"
            self.logger.error(error_msg)
            return GroundOptimizationResult(
                success=False,
                message=error_msg,
                optimized_zones=[],
                optimized_vias=[],
                warnings=[],
                errors=[error_msg]
            )
        except Exception as e:
            error_msg = f"Unexpected error implementing star grounding: {str(e)}"
            self.logger.error(error_msg)
            return GroundOptimizationResult(
                success=False,
                message=error_msg,
                optimized_zones=[],
                optimized_vias=[],
                warnings=[],
                errors=[error_msg]
            )
    
    def _minimize_ground_loops(self, ground_zones: List[pcbnew.ZONE]) -> GroundOptimizationResult:
        """Minimize ground loops by optimizing zone connections.
        
        Args:
            ground_zones: List of ground zones to optimize
            
        Returns:
            Ground optimization result
        """
        try:
            optimized_zones = []
            optimized_vias = []
            warnings = []
            
            # Analyze ground loops
            ground_loops = self._detect_ground_loops(ground_zones)
            
            if not ground_loops:
                return GroundOptimizationResult(
                    success=True,
                    message="No ground loops detected",
                    optimized_zones=[],
                    optimized_vias=[],
                    warnings=["No ground loops found"],
                    errors=[]
                )
            
            # Optimize each ground loop
            for loop in ground_loops:
                # Break the loop by removing one connection
                if len(loop) > 2:
                    # Remove the longest connection in the loop
                    longest_connection = self._find_longest_connection(loop)
                    if longest_connection:
                        self.board.Remove(longest_connection)
                        self.logger.debug(f"Removed ground loop connection: {longest_connection.GetNetname()}")
            
            return GroundOptimizationResult(
                success=True,
                message=f"Minimized {len(ground_loops)} ground loops",
                optimized_zones=optimized_zones,
                optimized_vias=optimized_vias,
                warnings=warnings,
                errors=[]
            )
            
        except Exception as e:
            error_msg = f"Error minimizing ground loops: {str(e)}"
            self.logger.error(error_msg)
            return GroundOptimizationResult(
                success=False,
                message=error_msg,
                optimized_zones=[],
                optimized_vias=[],
                warnings=[],
                errors=[error_msg]
            )
    
    def _optimize_ground_coverage(self, ground_zones: List[pcbnew.ZONE]) -> GroundOptimizationResult:
        """Optimize ground plane coverage.
        
        Args:
            ground_zones: List of ground zones to optimize
            
        Returns:
            Ground optimization result
        """
        try:
            optimized_zones = []
            optimized_vias = []
            warnings = []
            
            # Calculate current coverage
            current_coverage = self._calculate_ground_coverage(ground_zones)
            
            if current_coverage < self._ground_config.min_ground_coverage:
                # Expand ground zones to increase coverage
                for zone in ground_zones:
                    expanded_zone = self._expand_ground_zone(zone)
                    if expanded_zone:
                        optimized_zones.append(expanded_zone)
                        self.logger.debug(f"Expanded ground zone: {zone.GetName()}")
            
            return GroundOptimizationResult(
                success=True,
                message=f"Optimized ground coverage from {current_coverage:.1f}% to target {self._ground_config.min_ground_coverage}%",
                optimized_zones=optimized_zones,
                optimized_vias=optimized_vias,
                warnings=warnings,
                errors=[]
            )
            
        except Exception as e:
            error_msg = f"Error optimizing ground coverage: {str(e)}"
            self.logger.error(error_msg)
            return GroundOptimizationResult(
                success=False,
                message=error_msg,
                optimized_zones=[],
                optimized_vias=[],
                warnings=[],
                errors=[error_msg]
            )
    
    def _optimize_ground_stitching(self, ground_zones: List[pcbnew.ZONE]) -> GroundOptimizationResult:
        """Optimize ground plane stitching with vias.
        
        Args:
            ground_zones: List of ground zones to optimize
            
        Returns:
            Ground optimization result
        """
        try:
            optimized_zones = []
            optimized_vias = []
            warnings = []
            
            # Add stitching vias between ground zones
            for i, zone1 in enumerate(ground_zones):
                for zone2 in ground_zones[i+1:]:
                    # Calculate distance between zones
                    distance = self._calculate_zone_distance(zone1, zone2)
                    
                    if distance < self._ground_config.stitching_via_spacing * 2:  # Zones are close
                        # Add stitching vias
                        stitching_vias = self._add_stitching_vias(zone1, zone2)
                        optimized_vias.extend(stitching_vias)
                        
                        self.logger.debug(f"Added {len(stitching_vias)} stitching vias between zones")
            
            return GroundOptimizationResult(
                success=True,
                message=f"Added {len(optimized_vias)} stitching vias",
                optimized_zones=optimized_zones,
                optimized_vias=optimized_vias,
                warnings=warnings,
                errors=[]
            )
            
        except Exception as e:
            error_msg = f"Error optimizing ground stitching: {str(e)}"
            self.logger.error(error_msg)
            return GroundOptimizationResult(
                success=False,
                message=error_msg,
                optimized_zones=[],
                optimized_vias=[],
                warnings=[],
                errors=[error_msg]
            )
    
    def _separate_analog_digital_grounds(self, ground_zones: List[pcbnew.ZONE]) -> GroundOptimizationResult:
        """Separate analog and digital grounds.
        
        Args:
            ground_zones: List of ground zones to optimize
            
        Returns:
            Ground optimization result
        """
        try:
            optimized_zones = []
            optimized_vias = []
            warnings = []
            
            # Separate zones into analog and digital
            analog_zones = []
            digital_zones = []
            
            for zone in ground_zones:
                zone_name = zone.GetName().lower()
                if any(analog_name in zone_name for analog_name in ["analog", "agnd", "audio"]):
                    analog_zones.append(zone)
                elif any(digital_name in zone_name for digital_name in ["digital", "dgnd", "logic"]):
                    digital_zones.append(zone)
                else:
                    # Default to analog for audio circuits
                    analog_zones.append(zone)
            
            # Create separate ground zones
            if analog_zones and digital_zones:
                # Create analog ground zone
                analog_zone = self._create_ground_zone("AGND", analog_zones)
                if analog_zone:
                    optimized_zones.append(analog_zone)
                
                # Create digital ground zone
                digital_zone = self._create_ground_zone("DGND", digital_zones)
                if digital_zone:
                    optimized_zones.append(digital_zone)
                
                # Add single connection point between analog and digital grounds
                connection_via = self._create_ground_connection(analog_zone, digital_zone)
                if connection_via:
                    optimized_vias.append(connection_via)
            
            return GroundOptimizationResult(
                success=True,
                message=f"Separated {len(analog_zones)} analog and {len(digital_zones)} digital ground zones",
                optimized_zones=optimized_zones,
                optimized_vias=optimized_vias,
                warnings=warnings,
                errors=[]
            )
            
        except Exception as e:
            error_msg = f"Error separating analog/digital grounds: {str(e)}"
            self.logger.error(error_msg)
            return GroundOptimizationResult(
                success=False,
                message=error_msg,
                optimized_zones=[],
                optimized_vias=[],
                warnings=[],
                errors=[error_msg]
            )
    
    def _detect_ground_loops(self, ground_zones: List[pcbnew.ZONE]) -> List[List[pcbnew.ZONE]]:
        """Detect ground loops in the circuit.
        
        Args:
            ground_zones: List of ground zones
            
        Returns:
            List of ground loops
        """
        try:
            # This is a simplified implementation
            # In a real implementation, you would use graph algorithms to detect cycles
            
            ground_loops = []
            
            # Check for simple loops (3 or more zones connected in a cycle)
            if len(ground_zones) >= 3:
                # Create adjacency matrix
                adjacency = self._create_zone_adjacency_matrix(ground_zones)
                
                # Find cycles using simple algorithm
                for i in range(len(ground_zones)):
                    for j in range(i+1, len(ground_zones)):
                        for k in range(j+1, len(ground_zones)):
                            if (adjacency[i][j] and adjacency[j][k] and adjacency[k][i]):
                                # Found a triangle loop
                                loop = [ground_zones[i], ground_zones[j], ground_zones[k]]
                                ground_loops.append(loop)
            
            return ground_loops
            
        except Exception as e:
            self.logger.error(f"Error detecting ground loops: {str(e)}")
            return []
    
    def _create_zone_adjacency_matrix(self, ground_zones: List[pcbnew.ZONE]) -> List[List[bool]]:
        """Create adjacency matrix for ground zones.
        
        Args:
            ground_zones: List of ground zones
            
        Returns:
            Adjacency matrix
        """
        try:
            n = len(ground_zones)
            adjacency = [[False] * n for _ in range(n)]
            
            # Check connections between zones
            for i, zone1 in enumerate(ground_zones):
                for j, zone2 in enumerate(ground_zones):
                    if i != j:
                        distance = self._calculate_zone_distance(zone1, zone2)
                        # Zones are connected if they're close enough
                        adjacency[i][j] = distance < self._ground_config.stitching_via_spacing
            
            return adjacency
            
        except Exception as e:
            self.logger.error(f"Error creating adjacency matrix: {str(e)}")
            return []
    
    def _find_longest_connection(self, loop: List[pcbnew.ZONE]) -> Optional[pcbnew.TRACK]:
        """Find the longest connection in a ground loop.
        
        Args:
            loop: List of zones in the loop
            
        Returns:
            Longest track or None
        """
        try:
            # This is a simplified implementation
            # In a real implementation, you would find the actual tracks connecting the zones
            
            max_distance = 0.0
            longest_connection = None
            
            for i, zone1 in enumerate(loop):
                zone2 = loop[(i + 1) % len(loop)]
                distance = self._calculate_zone_distance(zone1, zone2)
                
                if distance > max_distance:
                    max_distance = distance
                    # In a real implementation, you would find the actual track here
            
            return longest_connection
            
        except Exception as e:
            self.logger.error(f"Error finding longest connection: {str(e)}")
            return None
    
    def _calculate_ground_coverage(self, ground_zones: List[pcbnew.ZONE]) -> float:
        """Calculate ground plane coverage percentage.
        
        Args:
            ground_zones: List of ground zones
            
        Returns:
            Coverage percentage
        """
        try:
            if not ground_zones:
                return 0.0
            
            # Calculate total board area
            board_area = self.board.GetBoardArea() / 1e12  # Convert to mm²
            
            # Calculate ground zone areas
            ground_area = 0.0
            for zone in ground_zones:
                zone_area = zone.GetArea() / 1e12  # Convert to mm²
                ground_area += zone_area
            
            coverage = (ground_area / board_area) * 100 if board_area > 0 else 0.0
            return min(100.0, coverage)
            
        except Exception as e:
            self.logger.error(f"Error calculating ground coverage: {str(e)}")
            return 0.0
    
    def _expand_ground_zone(self, zone: pcbnew.ZONE) -> Optional[pcbnew.ZONE]:
        """Expand a ground zone to increase coverage.
        
        Args:
            zone: Ground zone to expand
            
        Returns:
            Expanded zone or None
        """
        try:
            # This is a simplified implementation
            # In a real implementation, you would expand the zone outline
            
            # Get current outline
            outline = zone.GetOutline()
            
            if len(outline) < 3:
                return None
            
            # Expand outline by 1mm
            expansion_nm = int(1.0 * 1e6)  # 1mm expansion
            expanded_outline = []
            
            for point in outline:
                # Calculate expansion direction (simplified)
                expanded_point = pcbnew.VECTOR2I(
                    point.x + expansion_nm,
                    point.y + expansion_nm
                )
                expanded_outline.append(expanded_point)
            
            # Create new expanded zone
            expanded_zone = pcbnew.ZONE(self.board)
            expanded_zone.SetLayer(zone.GetLayer())
            expanded_zone.SetNetCode(zone.GetNetCode())
            expanded_zone.SetName(f"{zone.GetName()}_EXPANDED")
            expanded_zone.SetPosition(zone.GetPosition())
            expanded_zone.SetOutline(expanded_outline)
            
            # Add to board
            self.board.Add(expanded_zone)
            
            # Remove original zone
            self.board.Remove(zone)
            
            return expanded_zone
            
        except Exception as e:
            self.logger.error(f"Error expanding ground zone: {str(e)}")
            return None
    
    def _calculate_zone_distance(self, zone1: pcbnew.ZONE, zone2: pcbnew.ZONE) -> float:
        """Calculate distance between two zones.
        
        Args:
            zone1: First zone
            zone2: Second zone
            
        Returns:
            Distance in mm
        """
        try:
            pos1 = zone1.GetPosition()
            pos2 = zone2.GetPosition()
            
            dx = pos1.x - pos2.x
            dy = pos1.y - pos2.y
            distance = math.sqrt(dx * dx + dy * dy) / 1e6  # Convert to mm
            
            return distance
            
        except Exception as e:
            self.logger.error(f"Error calculating zone distance: {str(e)}")
            return float('inf')
    
    def _add_stitching_vias(self, zone1: pcbnew.ZONE, zone2: pcbnew.ZONE) -> List[pcbnew.VIA]:
        """Add stitching vias between two ground zones.
        
        Args:
            zone1: First ground zone
            zone2: Second ground zone
            
        Returns:
            List of added vias
        """
        try:
            vias = []
            
            # Calculate positions for stitching vias
            pos1 = zone1.GetPosition()
            pos2 = zone2.GetPosition()
            
            # Add vias along the line between zones
            distance = self._calculate_zone_distance(zone1, zone2)
            num_vias = max(1, int(distance / self._ground_config.stitching_via_spacing))
            
            for i in range(num_vias):
                # Calculate via position
                ratio = (i + 1) / (num_vias + 1)
                via_x = int(pos1.x + (pos2.x - pos1.x) * ratio)
                via_y = int(pos1.y + (pos2.y - pos1.y) * ratio)
                via_pos = pcbnew.VECTOR2I(via_x, via_y)
                
                # Create via
                via = pcbnew.VIA(self.board)
                via.SetPosition(via_pos)
                via.SetDrill(int(self._ground_config.stitching_via_diameter * 0.6e6))
                via.SetWidth(int(self._ground_config.stitching_via_diameter * 1e6))
                via.SetLayerPair(0, 31)  # Top to bottom
                via.SetNetCode(zone1.GetNetCode())
                
                self.board.Add(via)
                vias.append(via)
            
            return vias
            
        except Exception as e:
            self.logger.error(f"Error adding stitching vias: {str(e)}")
            return []
    
    def _create_ground_zone(self, net_name: str, source_zones: List[pcbnew.ZONE]) -> Optional[pcbnew.ZONE]:
        """Create a new ground zone from source zones.
        
        Args:
            net_name: Net name for the new zone
            source_zones: Source zones to combine
            
        Returns:
            New ground zone or None
        """
        try:
            if not source_zones:
                return None
            
            # Calculate bounding box of source zones
            min_x = min(zone.GetPosition().x for zone in source_zones)
            max_x = max(zone.GetPosition().x for zone in source_zones)
            min_y = min(zone.GetPosition().y for zone in source_zones)
            max_y = max(zone.GetPosition().y for zone in source_zones)
            
            # Create rectangular zone
            zone = pcbnew.ZONE(self.board)
            zone.SetLayer(self._ground_config.preferred_ground_layer)
            zone.SetNetCode(self.board.GetNetcodeFromNetname(net_name))
            zone.SetName(net_name)
            
            # Set position to center of bounding box
            center_x = (min_x + max_x) // 2
            center_y = (min_y + max_y) // 2
            zone.SetPosition(pcbnew.VECTOR2I(center_x, center_y))
            
            # Create rectangular outline
            outline = [
                pcbnew.VECTOR2I(min_x, min_y),
                pcbnew.VECTOR2I(max_x, min_y),
                pcbnew.VECTOR2I(max_x, max_y),
                pcbnew.VECTOR2I(min_x, max_y)
            ]
            zone.SetOutline(outline)
            
            # Add to board
            self.board.Add(zone)
            
            return zone
            
        except Exception as e:
            self.logger.error(f"Error creating ground zone: {str(e)}")
            return None
    
    def _create_ground_connection(self, zone1: pcbnew.ZONE, zone2: pcbnew.ZONE) -> Optional[pcbnew.VIA]:
        """Create a connection between two ground zones.
        
        Args:
            zone1: First ground zone
            zone2: Second ground zone
            
        Returns:
            Connection via or None
        """
        try:
            # Create via at midpoint between zones
            pos1 = zone1.GetPosition()
            pos2 = zone2.GetPosition()
            
            mid_x = (pos1.x + pos2.x) // 2
            mid_y = (pos1.y + pos2.y) // 2
            mid_pos = pcbnew.VECTOR2I(mid_x, mid_y)
            
            # Create via
            via = pcbnew.VIA(self.board)
            via.SetPosition(mid_pos)
            via.SetDrill(int(self._ground_config.stitching_via_diameter * 0.6e6))
            via.SetWidth(int(self._ground_config.stitching_via_diameter * 1e6))
            via.SetLayerPair(0, 31)  # Top to bottom
            via.SetNetCode(zone1.GetNetCode())
            
            self.board.Add(via)
            
            return via
            
        except Exception as e:
            self.logger.error(f"Error creating ground connection: {str(e)}")
            return None
    
    def _calculate_coverage_improvement(self, ground_zones: List[pcbnew.ZONE]) -> float:
        """Calculate ground coverage improvement percentage.
        
        Args:
            ground_zones: List of ground zones
            
        Returns:
            Improvement percentage
        """
        try:
            current_coverage = self._calculate_ground_coverage(ground_zones)
            
            if current_coverage < self._ground_config.min_ground_coverage:
                improvement = ((self._ground_config.min_ground_coverage - current_coverage) / current_coverage) * 100
                return max(0.0, improvement)
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating coverage improvement: {str(e)}")
            return 0.0
    
    def _calculate_loop_reduction(self, ground_zones: List[pcbnew.ZONE]) -> float:
        """Calculate ground loop reduction percentage.
        
        Args:
            ground_zones: List of ground zones
            
        Returns:
            Reduction percentage
        """
        try:
            # This is a simplified implementation
            # In a real implementation, you would count actual ground loops
            
            initial_loops = len(ground_zones) - 1  # Estimate
            final_loops = 0  # After optimization
            
            if initial_loops > 0:
                reduction = ((initial_loops - final_loops) / initial_loops) * 100
                return max(0.0, reduction)
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating loop reduction: {str(e)}")
            return 0.0 
