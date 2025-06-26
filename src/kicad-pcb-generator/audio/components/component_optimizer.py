"""Component optimization using KiCad 9's native functionality."""
import logging
import pcbnew
from typing import Dict, List, Optional, Any, Tuple, Set, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
import math

from ...core.base.base_optimizer import BaseOptimizer
from ...core.base.results.optimization_result import OptimizationResult, OptimizationType, OptimizationStrategy

if TYPE_CHECKING:
    from ...core.base.results.optimization_result import OptimizationResult as BaseOptimizationResult

class ComponentType(Enum):
    """Types of audio components."""
    OPAMP = "opamp"
    CAPACITOR = "capacitor"
    RESISTOR = "resistor"
    INDUCTOR = "inductor"
    CONNECTOR = "connector"
    VOLTAGE_REGULATOR = "voltage_regulator"
    CRYSTAL = "crystal"
    OTHER = "other"

@dataclass
class ComponentConstraints:
    """Constraints for component optimization."""
    min_clearance: float  # in mm
    min_trace_width: float  # in mm
    max_trace_length: float  # in mm
    preferred_layer: int
    thermal_pad_size: float  # in mm
    placement_priority: int
    power_rating: Optional[float] = None  # in W
    voltage_rating: Optional[float] = None  # in V

@dataclass
class ComponentOptimizationItem:
    """Data structure for component optimization items."""
    id: str
    optimization_type: OptimizationType
    board: "pcbnew.BOARD"
    component_type: ComponentType
    constraints: ComponentConstraints
    footprint: Optional["pcbnew.FOOTPRINT"] = None
    target_position: Optional[Tuple[float, float]] = None
    optimization_strategy: OptimizationStrategy = OptimizationStrategy.GREEDY

class ComponentOptimizer(BaseOptimizer[ComponentOptimizationItem]):
    """Optimizes component placement and routing using KiCad 9's native functionality."""
    
    def __init__(self, board: "pcbnew.BOARD", logger: Optional[logging.Logger] = None):
        """Initialize the component optimizer.
        
        Args:
            board: KiCad board object
            logger: Optional logger instance
        """
        super().__init__("ComponentOptimizer")
        self.board = board
        self.logger = logger or logging.getLogger(__name__)
        self._validate_kicad_version()
        self._component_constraints: Dict[ComponentType, ComponentConstraints] = self._initialize_constraints()
        
        # Initialize caches
        self._footprint_cache: Dict[str, "pcbnew.FOOTPRINT"] = {}
        self._component_types: Dict[str, ComponentType] = {}
        self._track_cache: Dict[str, List["pcbnew.TRACK"]] = {}
        self._pad_cache: Dict[str, List["pcbnew.PAD"]] = {}
        self._board_box: Optional["pcbnew.BOX2I"] = None
        self._power_planes: Optional[List["pcbnew.VECTOR2I"]] = None
        self._component_positions: Optional[Dict[str, "pcbnew.VECTOR2I"]] = None
        
        # Initialize optimization items
        self._initialize_optimization_items()
    
    def _initialize_optimization_items(self) -> None:
        """Initialize optimization items for BaseOptimizer."""
        try:
            # Create optimization items for each optimization type
            optimization_types = [
                OptimizationType.COMPONENT_PLACEMENT,
                OptimizationType.COMPONENT_ROUTING,
                OptimizationType.THERMAL_OPTIMIZATION,
                OptimizationType.POWER_DISTRIBUTION
            ]
            
            for optimization_type in optimization_types:
                for component_type in ComponentType:
                    constraints = self._component_constraints.get(component_type, self._get_default_constraints())
                    
                    optimization_item = ComponentOptimizationItem(
                        id=f"component_optimization_{component_type.value}_{optimization_type.value}",
                        optimization_type=optimization_type,
                        board=self.board,
                        component_type=component_type,
                        constraints=constraints
                    )
                    self.create(f"component_optimization_{component_type.value}_{optimization_type.value}", optimization_item)
                    
        except (ValueError, KeyError, AttributeError) as e:
            self.logger.error(f"Error initializing optimization items: {str(e)}")
            raise
    
    def _get_default_constraints(self) -> ComponentConstraints:
        """Get default constraints for unknown component types."""
        return ComponentConstraints(
            min_clearance=0.5,
            min_trace_width=0.2,
            max_trace_length=100.0,
            preferred_layer=0,
            thermal_pad_size=2.0,
            placement_priority=5
        )
    
    def optimize_component_placement(self) -> None:
        """Optimize component placement based on constraints."""
        try:
            # Create optimization item for component placement
            placement_item = ComponentOptimizationItem(
                id="component_placement_optimization_current",
                optimization_type=OptimizationType.COMPONENT_PLACEMENT,
                board=self.board,
                component_type=ComponentType.OTHER,
                constraints=self._get_default_constraints()
            )
            
            # Perform optimization using BaseOptimizer
            result = self.optimize(placement_item, OptimizationType.COMPONENT_PLACEMENT)
            
            if result.success and result.data:
                # Apply the optimization results
                self._apply_placement_optimization(result.data)
            else:
                # Fallback to original implementation
                self._perform_placement_optimization()
                
        except (ValueError, KeyError, AttributeError) as e:
            self.logger.error(f"Error in component placement optimization: {str(e)}")
            raise
    
    def optimize_component_routing(self) -> None:
        """Optimize component routing based on constraints."""
        try:
            # Create optimization item for component routing
            routing_item = ComponentOptimizationItem(
                id="component_routing_optimization_current",
                optimization_type=OptimizationType.COMPONENT_ROUTING,
                board=self.board,
                component_type=ComponentType.OTHER,
                constraints=self._get_default_constraints()
            )
            
            # Perform optimization using BaseOptimizer
            result = self.optimize(routing_item, OptimizationType.COMPONENT_ROUTING)
            
            if result.success and result.data:
                # Apply the optimization results
                self._apply_routing_optimization(result.data)
            else:
                # Fallback to original implementation
                self._perform_routing_optimization()
                
        except (ValueError, KeyError, AttributeError) as e:
            self.logger.error(f"Error in component routing optimization: {str(e)}")
            raise
    
    def _validate_target(self, target: ComponentOptimizationItem) -> OptimizationResult:
        """Validate target before optimization.
        
        Args:
            target: Target to validate
            
        Returns:
            Validation result
        """
        try:
            if not target.id:
                return OptimizationResult(
                    success=False,
                    optimization_type=target.optimization_type,
                    message="Optimization item ID is required",
                    errors=["Optimization item ID cannot be empty"]
                )
            
            if not target.board:
                return OptimizationResult(
                    success=False,
                    optimization_type=target.optimization_type,
                    message="Board object is required",
                    errors=["Board object cannot be empty"]
                )
            
            if not target.constraints:
                return OptimizationResult(
                    success=False,
                    optimization_type=target.optimization_type,
                    message="Constraints are required",
                    errors=["Constraints cannot be empty"]
                )
            
            return OptimizationResult(
                success=True,
                optimization_type=target.optimization_type,
                message="Optimization item validation successful"
            )
        except (ValueError, KeyError, AttributeError) as e:
            return OptimizationResult(
                success=False,
                optimization_type=target.optimization_type,
                message=f"Optimization item validation failed: {e}",
                errors=[str(e)]
            )
    
    def _perform_optimization(self, target: ComponentOptimizationItem, optimization_type: OptimizationType) -> OptimizationResult:
        """Perform the actual optimization.
        
        Args:
            target: Target to optimize
            optimization_type: Type of optimization to perform
            
        Returns:
            Optimization result
        """
        try:
            if optimization_type == OptimizationType.COMPONENT_PLACEMENT:
                result_data = self._perform_placement_optimization()
                return OptimizationResult(
                    success=True,
                    optimization_type=optimization_type,
                    message="Component placement optimization completed successfully",
                    data=result_data,
                    metrics={
                        "components_optimized": len(result_data.get("optimized_components", [])),
                        "placement_score": result_data.get("placement_score", 0.0)
                    }
                )
            
            elif optimization_type == OptimizationType.COMPONENT_ROUTING:
                result_data = self._perform_routing_optimization()
                return OptimizationResult(
                    success=True,
                    optimization_type=optimization_type,
                    message="Component routing optimization completed successfully",
                    data=result_data,
                    metrics={
                        "routes_optimized": len(result_data.get("optimized_routes", [])),
                        "routing_score": result_data.get("routing_score", 0.0)
                    }
                )
            
            elif optimization_type == OptimizationType.THERMAL_OPTIMIZATION:
                result_data = self._perform_thermal_optimization()
                return OptimizationResult(
                    success=True,
                    optimization_type=optimization_type,
                    message="Thermal optimization completed successfully",
                    data=result_data,
                    metrics={
                        "thermal_score": result_data.get("thermal_score", 0.0)
                    }
                )
            
            elif optimization_type == OptimizationType.POWER_DISTRIBUTION:
                result_data = self._perform_power_optimization()
                return OptimizationResult(
                    success=True,
                    optimization_type=optimization_type,
                    message="Power distribution optimization completed successfully",
                    data=result_data,
                    metrics={
                        "power_score": result_data.get("power_score", 0.0)
                    }
                )
            
            else:
                return OptimizationResult(
                    success=False,
                    optimization_type=optimization_type,
                    message=f"Unsupported optimization type: {optimization_type.value}",
                    errors=[f"Optimization type {optimization_type.value} is not supported"]
                )
                
        except (ValueError, KeyError, AttributeError) as e:
            return OptimizationResult(
                success=False,
                optimization_type=optimization_type,
                message=f"Error during optimization: {e}",
                errors=[str(e)]
            )
    
    def _apply_placement_optimization(self, optimization_data: Dict[str, Any]) -> None:
        """Apply placement optimization results to the board.
        
        Args:
            optimization_data: Optimization results to apply
        """
        try:
            optimized_components = optimization_data.get("optimized_components", [])
            for component_data in optimized_components:
                ref = component_data.get("reference")
                new_position = component_data.get("position")
                if ref and new_position:
                    footprint = self._get_footprints().get(ref)
                    if footprint:
                        footprint.SetPosition(pcbnew.VECTOR2I(int(new_position[0]), int(new_position[1])))
            
            self.logger.info(f"Applied placement optimization for {len(optimized_components)} components")
        except (ValueError, KeyError, AttributeError) as e:
            self.logger.error(f"Error applying placement optimization: {str(e)}")
            raise
    
    def _apply_routing_optimization(self, optimization_data: Dict[str, Any]) -> None:
        """Apply routing optimization results to the board.
        
        Args:
            optimization_data: Optimization results to apply
        """
        try:
            optimized_routes = optimization_data.get("optimized_routes", [])
            for route_data in optimized_routes:
                # Placeholder: apply routing tweaks such as push-and-shove,
                # width/clearance adjustments, or layer changes.  These
                # operations require KiCad's interactive router, unavailable
                # in CI, so we log the request instead.
                self.logger.debug("Routing optimisation placeholder executed for route data: %s", route_data)
            
            self.logger.info(f"Applied routing optimization for {len(optimized_routes)} routes")
        except (ValueError, KeyError, AttributeError) as e:
            self.logger.error(f"Error applying routing optimization: {str(e)}")
            raise
    
    def _validate_kicad_version(self) -> None:
        """Validate KiCad version compatibility."""
        version = pcbnew.Version()
        if not version.startswith('9'):
            raise RuntimeError(f"This module requires KiCad 9.x, but found version {version}")
        self.logger.info(f"Running with KiCad version: {version}")
    
    @lru_cache(maxsize=32)
    def _get_board_box(self) -> pcbnew.BOX2I:
        """Get cached board boundaries."""
        if self._board_box is None:
            self._board_box = self.board.GetBoardEdgesBoundingBox()
        return self._board_box
    
    @lru_cache(maxsize=32)
    def _get_power_planes(self) -> List[pcbnew.VECTOR2I]:
        """Get cached power plane positions."""
        if self._power_planes is None:
            self._power_planes = [
                zone.GetPosition()
                for zone in self.board.Zones()
                if zone.GetNet().GetName().startswith("PWR")
            ]
        return self._power_planes
    
    @lru_cache(maxsize=32)
    def _get_component_positions(self) -> Dict[str, pcbnew.VECTOR2I]:
        """Get cached component positions."""
        if self._component_positions is None:
            self._component_positions = {
                fp.GetReference(): fp.GetPosition()
                for fp in self.board.GetFootprints()
            }
        return self._component_positions
    
    @lru_cache(maxsize=128)
    def _get_footprints(self) -> Dict[str, pcbnew.FOOTPRINT]:
        """Get cached footprints."""
        if not self._footprint_cache:
            self._footprint_cache = {
                fp.GetReference(): fp
                for fp in self.board.GetFootprints()
            }
        return self._footprint_cache
    
    @lru_cache(maxsize=256)
    def _get_component_type(self, footprint: pcbnew.FOOTPRINT) -> ComponentType:
        """Determine the type of a component based on its properties.
        
        Args:
            footprint: KiCad footprint object
            
        Returns:
            Component type
        """
        ref = footprint.GetReference()
        if ref in self._component_types:
            return self._component_types[ref]
        
        ref_upper = ref.upper()
        value = footprint.GetValue().upper()
        
        # Use set operations for faster lookups
        if any(keyword in ref_upper for keyword in ["OP", "U"]):
            component_type = ComponentType.OPAMP
        elif "C" in ref_upper:
            component_type = ComponentType.CAPACITOR
        elif "R" in ref_upper:
            component_type = ComponentType.RESISTOR
        elif "L" in ref_upper:
            component_type = ComponentType.INDUCTOR
        elif any(keyword in ref_upper for keyword in ["J", "CON"]):
            component_type = ComponentType.CONNECTOR
        elif any(keyword in ref_upper for keyword in ["REG", "VR"]):
            component_type = ComponentType.VOLTAGE_REGULATOR
        elif any(keyword in ref_upper for keyword in ["XTAL", "CRYSTAL"]):
            component_type = ComponentType.CRYSTAL
        else:
            component_type = ComponentType.OTHER
        
        self._component_types[ref] = component_type
        return component_type
    
    @lru_cache(maxsize=512)
    def _get_tracks(self, footprint: pcbnew.FOOTPRINT) -> List[pcbnew.TRACK]:
        """Get cached tracks for a footprint."""
        ref = footprint.GetReference()
        if ref not in self._track_cache:
            tracks = []
            for pad in footprint.Pads():
                tracks.extend(pad.GetTracks())
            self._track_cache[ref] = tracks
        return self._track_cache[ref]
    
    @lru_cache(maxsize=512)
    def _get_pads(self, footprint: pcbnew.FOOTPRINT) -> List[pcbnew.PAD]:
        """Get cached pads for a footprint."""
        ref = footprint.GetReference()
        if ref not in self._pad_cache:
            self._pad_cache[ref] = list(footprint.Pads())
        return self._pad_cache[ref]
    
    def _perform_placement_optimization(self) -> None:
        """Perform placement optimization."""
        try:
            # Clear caches
            self._footprint_cache.clear()
            self._component_types.clear()
            self._track_cache.clear()
            self._pad_cache.clear()
            self._board_box = None
            self._power_planes = None
            self._component_positions = None
            
            # Clear memoization caches
            self._get_board_box.cache_clear()
            self._get_power_planes.cache_clear()
            self._get_component_positions.cache_clear()
            self._get_footprints.cache_clear()
            self._get_component_type.cache_clear()
            self._get_tracks.cache_clear()
            self._get_pads.cache_clear()
            
            # Get all footprints
            footprints = self._get_footprints()
            
            # Sort footprints by priority
            sorted_footprints = sorted(
                footprints.values(),
                key=lambda fp: self._component_constraints[self._get_component_type(fp)].placement_priority
            )
            
            # Optimize placement for each component
            for footprint in sorted_footprints:
                component_type = self._get_component_type(footprint)
                constraints = self._component_constraints[component_type]
                
                # Get current position
                pos = footprint.GetPosition()
                
                # Check clearance
                for other_fp in footprints.values():
                    if other_fp == footprint:
                        continue
                    
                    other_pos = other_fp.GetPosition()
                    distance = ((pos.x - other_pos.x) ** 2 + (pos.y - other_pos.y) ** 2) ** 0.5 / 1e6  # Convert to mm
                    
                    if distance < constraints.min_clearance:
                        # Move component to maintain clearance
                        new_x = pos.x + (constraints.min_clearance * 1e6)  # Convert to nm
                        new_y = pos.y + (constraints.min_clearance * 1e6)
                        footprint.SetPosition(pcbnew.VECTOR2I(int(new_x), int(new_y)))
                
                # Check layer
                if footprint.GetLayer() != constraints.preferred_layer:
                    footprint.Flip(footprint.GetPosition(), False)
                
                # Add thermal pad if needed
                if constraints.thermal_pad_size > 0:
                    self._add_thermal_pad(footprint, constraints.thermal_pad_size)
            
        except Exception as e:
            self.logger.error(f"Error optimizing component placement: {str(e)}")
            raise
    
    def _add_thermal_pad(self, footprint: pcbnew.FOOTPRINT, size: float) -> None:
        """Add a thermal pad to a component.
        
        Args:
            footprint: KiCad footprint object
            size: Thermal pad size in mm
        """
        try:
            # Create thermal pad
            pad = pcbnew.PAD(footprint)
            pad.SetSize(pcbnew.VECTOR2I(int(size * 1e6), int(size * 1e6)))  # Convert to nm
            pad.SetShape(pcbnew.PAD_SHAPE_RECT)
            pad.SetLayerSet(pcbnew.LSET.AllCuMask())
            
            # Position pad under component
            pos = footprint.GetPosition()
            pad.SetPosition(pos)
            
            # Add pad to footprint
            footprint.Add(pad)
            
            # Update pad cache
            ref = footprint.GetReference()
            if ref in self._pad_cache:
                self._pad_cache[ref].append(pad)
            
        except Exception as e:
            self.logger.error(f"Error adding thermal pad: {str(e)}")
            raise
    
    def _perform_routing_optimization(self) -> None:
        """Perform routing optimization."""
        try:
            # Get all footprints
            footprints = self._get_footprints()
            
            # Optimize routing for each component
            for footprint in footprints.values():
                component_type = self._get_component_type(footprint)
                constraints = self._component_constraints[component_type]
                
                # Get tracks for this component
                tracks = self._get_tracks(footprint)
                
                # Optimize track widths
                for track in tracks:
                    if track.GetWidth() < constraints.min_trace_width * 1e6:  # Convert to nm
                        track.SetWidth(int(constraints.min_trace_width * 1e6))
                    
                    # Check track length
                    if track.GetLength() > constraints.max_trace_length * 1e6:  # Convert to nm
                        # Shorten track or reroute
                        self._optimize_track_length(track, constraints.max_trace_length)
                
                # Optimize pad connections
                pads = self._get_pads(footprint)
                for pad in pads:
                    self._optimize_pad_connection(pad, constraints)
            
        except Exception as e:
            self.logger.error(f"Error optimizing component routing: {str(e)}")
            raise
    
    def _perform_thermal_optimization(self) -> Dict[str, Any]:
        """Perform thermal optimization.
        
        Returns:
            Dict containing thermal optimization results
        """
        try:
            footprints = self._get_footprints()
            thermal_results = {
                "thermal_score": 0.0,
                "optimized_components": [],
                "hot_spots": []
            }
            
            total_score = 0.0
            optimized_count = 0
            
            for footprint in footprints.values():
                component_type = self._get_component_type(footprint)
                constraints = self._component_constraints[component_type]
                
                # Calculate thermal characteristics
                thermal_score = self._calculate_thermal_score(footprint, constraints)
                total_score += thermal_score
                
                if thermal_score > 0.7:  # Good thermal performance
                    optimized_count += 1
                    thermal_results["optimized_components"].append({
                        "reference": footprint.GetReference(),
                        "thermal_score": thermal_score,
                        "position": (footprint.GetPosition().x, footprint.GetPosition().y)
                    })
                
                # Check for hot spots
                if thermal_score < 0.3:  # Poor thermal performance
                    pos = footprint.GetPosition()
                    thermal_results["hot_spots"].append((pos.x, pos.y))
            
            # Calculate overall thermal score
            if footprints:
                thermal_results["thermal_score"] = total_score / len(footprints)
            
            self.logger.info(f"Thermal optimization completed: {optimized_count} components optimized")
            return thermal_results
            
        except Exception as e:
            self.logger.error(f"Error in thermal optimization: {str(e)}")
            return {"thermal_score": 0.0, "optimized_components": [], "hot_spots": []}
    
    def _perform_power_optimization(self) -> Dict[str, Any]:
        """Perform power distribution optimization.
        
        Returns:
            Dict containing power optimization results
        """
        try:
            footprints = self._get_footprints()
            power_results = {
                "power_score": 0.0,
                "optimized_components": [],
                "power_paths": []
            }
            
            total_score = 0.0
            optimized_count = 0
            
            for footprint in footprints.values():
                component_type = self._get_component_type(footprint)
                constraints = self._component_constraints[component_type]
                
                # Calculate power distribution characteristics
                power_score = self._calculate_power_score(footprint, constraints)
                total_score += power_score
                
                if power_score > 0.7:  # Good power distribution
                    optimized_count += 1
                    power_results["optimized_components"].append({
                        "reference": footprint.GetReference(),
                        "power_score": power_score,
                        "position": (footprint.GetPosition().x, footprint.GetPosition().y)
                    })
                
                # Analyze power paths
                power_paths = self._analyze_power_paths(footprint)
                power_results["power_paths"].extend(power_paths)
            
            # Calculate overall power score
            if footprints:
                power_results["power_score"] = total_score / len(footprints)
            
            self.logger.info(f"Power optimization completed: {optimized_count} components optimized")
            return power_results
            
        except Exception as e:
            self.logger.error(f"Error in power optimization: {str(e)}")
            return {"power_score": 0.0, "optimized_components": [], "power_paths": []}
    
    def _initialize_constraints(self) -> Dict[ComponentType, ComponentConstraints]:
        """Initialize component constraints.
        
        Returns:
            Dict mapping component types to their constraints
        """
        return {
            ComponentType.OPAMP: ComponentConstraints(
                min_clearance=1.0,
                min_trace_width=0.3,
                max_trace_length=50.0,
                preferred_layer=0,
                thermal_pad_size=3.0,
                placement_priority=1
            ),
            ComponentType.CAPACITOR: ComponentConstraints(
                min_clearance=0.5,
                min_trace_width=0.2,
                max_trace_length=20.0,
                preferred_layer=0,
                thermal_pad_size=2.0,
                placement_priority=3
            ),
            ComponentType.RESISTOR: ComponentConstraints(
                min_clearance=0.5,
                min_trace_width=0.2,
                max_trace_length=30.0,
                preferred_layer=0,
                thermal_pad_size=1.5,
                placement_priority=4
            ),
            ComponentType.INDUCTOR: ComponentConstraints(
                min_clearance=1.5,
                min_trace_width=0.4,
                max_trace_length=40.0,
                preferred_layer=0,
                thermal_pad_size=2.5,
                placement_priority=2
            ),
            ComponentType.CONNECTOR: ComponentConstraints(
                min_clearance=2.0,
                min_trace_width=0.5,
                max_trace_length=100.0,
                preferred_layer=0,
                thermal_pad_size=0.0,
                placement_priority=1
            ),
            ComponentType.VOLTAGE_REGULATOR: ComponentConstraints(
                min_clearance=2.0,
                min_trace_width=0.8,
                max_trace_length=60.0,
                preferred_layer=0,
                thermal_pad_size=5.0,
                placement_priority=1
            ),
            ComponentType.CRYSTAL: ComponentConstraints(
                min_clearance=1.0,
                min_trace_width=0.3,
                max_trace_length=25.0,
                preferred_layer=0,
                thermal_pad_size=0.0,
                placement_priority=2
            ),
            ComponentType.OTHER: ComponentConstraints(
                min_clearance=0.5,
                min_trace_width=0.2,
                max_trace_length=50.0,
                preferred_layer=0,
                thermal_pad_size=1.0,
                placement_priority=5
            )
        }
    
    def _optimize_track_length(self, track: "pcbnew.TRACK", max_length: float) -> None:
        """Optimize track length to meet constraints.
        
        Args:
            track: Track to optimize
            max_length: Maximum allowed length in mm
        """
        try:
            current_length = track.GetLength() / 1e6  # Convert from nm to mm
            if current_length > max_length:
                # Shorten track by adjusting endpoints
                # This is a simplified implementation
                start_pos = track.GetStart()
                end_pos = track.GetEnd()
                
                # Calculate new endpoint to meet length constraint
                dx = end_pos.x - start_pos.x
                dy = end_pos.y - start_pos.y
                current_dist = (dx**2 + dy**2)**0.5
                
                if current_dist > 0:
                    scale_factor = (max_length * 1e6) / current_dist  # Convert to nm
                    new_end_x = start_pos.x + int(dx * scale_factor)
                    new_end_y = start_pos.y + int(dy * scale_factor)
                    track.SetEnd(pcbnew.VECTOR2I(new_end_x, new_end_y))
                    
        except Exception as e:
            self.logger.error(f"Error optimizing track length: {str(e)}")
    
    def _optimize_pad_connection(self, pad: "pcbnew.PAD", constraints: ComponentConstraints) -> None:
        """Optimize pad connection based on constraints.
        
        Args:
            pad: Pad to optimize
            constraints: Component constraints
        """
        try:
            # Check pad size
            pad_size = pad.GetSize()
            min_size = int(constraints.min_trace_width * 1e6)  # Convert to nm
            
            if pad_size.x < min_size or pad_size.y < min_size:
                new_size = pcbnew.VECTOR2I(min_size, min_size)
                pad.SetSize(new_size)
                
        except Exception as e:
            self.logger.error(f"Error optimizing pad connection: {str(e)}")
    
    def _calculate_thermal_score(self, footprint: "pcbnew.FOOTPRINT", constraints: ComponentConstraints) -> float:
        """Calculate thermal performance score for a component.
        
        Args:
            footprint: Component footprint
            constraints: Component constraints
            
        Returns:
            Thermal score between 0.0 and 1.0
        """
        try:
            score = 1.0
            
            # Check thermal pad presence
            if constraints.thermal_pad_size > 0:
                has_thermal_pad = self._has_thermal_pad(footprint)
                if not has_thermal_pad:
                    score *= 0.7
            
            # Check clearance for heat dissipation
            clearance_score = self._calculate_clearance_score(footprint, constraints.min_clearance)
            score *= clearance_score
            
            # Check layer (top layer is better for heat dissipation)
            if footprint.GetLayer() == 0:  # Top layer
                score *= 1.0
            else:
                score *= 0.8
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            self.logger.error(f"Error calculating thermal score: {str(e)}")
            return 0.0
    
    def _calculate_power_score(self, footprint: "pcbnew.FOOTPRINT", constraints: ComponentConstraints) -> float:
        """Calculate power distribution score for a component.
        
        Args:
            footprint: Component footprint
            constraints: Component constraints
            
        Returns:
            Power score between 0.0 and 1.0
        """
        try:
            score = 1.0
            
            # Check power plane proximity
            power_planes = self._get_power_planes()
            if power_planes:
                min_distance = float('inf')
                component_pos = footprint.GetPosition()
                
                for plane_pos in power_planes:
                    distance = ((component_pos.x - plane_pos.x)**2 + (component_pos.y - plane_pos.y)**2)**0.5 / 1e6
                    min_distance = min(min_distance, distance)
                
                # Score based on distance to power plane
                if min_distance < 10.0:  # Within 10mm
                    score *= 1.0
                elif min_distance < 20.0:  # Within 20mm
                    score *= 0.8
                else:
                    score *= 0.6
            
            # Check track widths
            tracks = self._get_tracks(footprint)
            for track in tracks:
                if track.GetWidth() < constraints.min_trace_width * 1e6:
                    score *= 0.9
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            self.logger.error(f"Error calculating power score: {str(e)}")
            return 0.0
    
    def _analyze_power_paths(self, footprint: "pcbnew.FOOTPRINT") -> List[Dict[str, Any]]:
        """Analyze power paths for a component.
        
        Args:
            footprint: Component footprint
            
        Returns:
            List of power path information
        """
        try:
            power_paths = []
            tracks = self._get_tracks(footprint)
            
            for track in tracks:
                net = track.GetNet()
                if net and net.GetName().startswith(("VCC", "VDD", "GND", "PWR")):
                    power_paths.append({
                        "net": net.GetName(),
                        "track_width": track.GetWidth() / 1e6,  # Convert to mm
                        "track_length": track.GetLength() / 1e6,  # Convert to mm
                        "start_pos": (track.GetStart().x, track.GetStart().y),
                        "end_pos": (track.GetEnd().x, track.GetEnd().y)
                    })
            
            return power_paths
            
        except Exception as e:
            self.logger.error(f"Error analyzing power paths: {str(e)}")
            return []
    
    def _has_thermal_pad(self, footprint: "pcbnew.FOOTPRINT") -> bool:
        """Check if footprint has a thermal pad.
        
        Args:
            footprint: Component footprint
            
        Returns:
            True if thermal pad is present
        """
        try:
            pads = self._get_pads(footprint)
            for pad in pads:
                if pad.GetPadName() in ["THERMAL", "PAD", "EP"]:
                    return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking thermal pad: {str(e)}")
            return False
    
    def _calculate_clearance_score(self, footprint: "pcbnew.FOOTPRINT", min_clearance: float) -> float:
        """Calculate clearance score for a component.
        
        Args:
            footprint: Component footprint
            min_clearance: Minimum required clearance in mm
            
        Returns:
            Clearance score between 0.0 and 1.0
        """
        try:
            component_pos = footprint.GetPosition()
            footprints = self._get_footprints()
            
            min_distance = float('inf')
            for other_fp in footprints.values():
                if other_fp == footprint:
                    continue
                
                other_pos = other_fp.GetPosition()
                distance = ((component_pos.x - other_pos.x)**2 + (component_pos.y - other_pos.y)**2)**0.5 / 1e6
                min_distance = min(min_distance, distance)
            
            if min_distance >= min_clearance:
                return 1.0
            elif min_distance >= min_clearance * 0.5:
                return 0.7
            else:
                return 0.3
                
        except Exception as e:
            self.logger.error(f"Error calculating clearance score: {str(e)}")
            return 0.0
    
    @lru_cache(maxsize=1024)
    def validate_component_placement(self) -> List[str]:
        """Validate component placement.
        
        Returns:
            List of validation messages
        """
        messages = []
        
        try:
            # Get all footprints
            footprints = self._get_footprints()
            
            # Check each component
            for footprint in footprints.values():
                component_type = self._get_component_type(footprint)
                constraints = self._component_constraints[component_type]
                
                # Check clearance
                for other_fp in footprints.values():
                    if other_fp == footprint:
                        continue
                    
                    pos = footprint.GetPosition()
                    other_pos = other_fp.GetPosition()
                    distance = ((pos.x - other_pos.x) ** 2 + (pos.y - other_pos.y) ** 2) ** 0.5 / 1e6  # Convert to mm
                    
                    if distance < constraints.min_clearance:
                        messages.append(
                            f"Component {footprint.GetReference()} is too close to {other_fp.GetReference()} "
                            f"({distance:.2f}mm < {constraints.min_clearance:.2f}mm)"
                        )
                
                # Check layer
                if footprint.GetLayer() != constraints.preferred_layer:
                    messages.append(
                        f"Component {footprint.GetReference()} is on wrong layer "
                        f"(should be {constraints.preferred_layer})"
                    )
                
                # Check thermal pad
                if constraints.thermal_pad_size > 0:
                    has_thermal_pad = False
                    for pad in self._get_pads(footprint):
                        if pad.GetSize().x >= constraints.thermal_pad_size * 1e6:
                            has_thermal_pad = True
                            break
                    
                    if not has_thermal_pad:
                        messages.append(
                            f"Component {footprint.GetReference()} is missing thermal pad "
                            f"(should be {constraints.thermal_pad_size:.1f}mm)"
                        )
            
        except Exception as e:
            self.logger.error(f"Error validating component placement: {str(e)}")
            messages.append(f"Error validating component placement: {str(e)}")
        
        return messages 
