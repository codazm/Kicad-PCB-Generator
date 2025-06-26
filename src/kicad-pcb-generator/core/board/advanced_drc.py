"""Advanced DRC features for KiCad PCB Generator."""
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any, Tuple, TYPE_CHECKING
from enum import Enum
import math
import pcbnew

from ..base.base_manager import BaseManager
from ..base.results.manager_result import ManagerResult, ManagerOperation, ManagerStatus
from ..validation.validation_rule import ValidationRule, RuleType, ValidationCategory, ValidationSeverity

if TYPE_CHECKING:
    from ..base.results.manager_result import ManagerResult

class RulePriority(Enum):
    """Priority levels for design rules."""
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    INFO = 4

@dataclass
class RuleTemplate:
    """Template for creating design rules."""
    name: str
    description: str
    rule_type: RuleType
    parameters: Dict[str, Any]
    thresholds: Dict[str, float]
    priority: RulePriority
    category: ValidationCategory
    enabled: bool = True
    severity: ValidationSeverity = ValidationSeverity.WARNING

@dataclass
class RuleConflict:
    """Information about conflicting rules."""
    rule1: str
    rule2: str
    description: str
    resolution: str
    priority: RulePriority

@dataclass
class DRCRuleItem:
    """Data structure for DRC rule items."""
    rule_name: str
    rule_type: RuleType
    category: ValidationCategory
    enabled: bool
    parameters: Dict[str, Any]
    thresholds: Dict[str, float]
    severity: ValidationSeverity
    priority: RulePriority
    template_name: Optional[str] = None
    validation_status: str = "pending"
    conflict_status: str = "none"
    
    def __post_init__(self):
        """Validate required fields."""
        if not self.rule_name:
            raise ValueError("rule_name is required")
        if not isinstance(self.rule_type, RuleType):
            raise ValueError("rule_type must be a RuleType enum")
        if not isinstance(self.category, ValidationCategory):
            raise ValueError("category must be a ValidationCategory enum")
        if not isinstance(self.severity, ValidationSeverity):
            raise ValueError("severity must be a ValidationSeverity enum")
        if not isinstance(self.priority, RulePriority):
            raise ValueError("priority must be a RulePriority enum")

class AdvancedDRCManager(BaseManager[DRCRuleItem]):
    """Manages advanced DRC features for KiCad PCB Generator."""
    
    def __init__(self, board: Optional[pcbnew.BOARD] = None):
        """Initialize the DRC manager.
        
        Args:
            board: Optional KiCad board object
        """
        super().__init__()
        self.board = board
        self.logger = logging.getLogger(__name__)
        self.rules: Dict[str, ValidationRule] = {}
        self.templates: Dict[str, RuleTemplate] = {}
        self.conflicts: List[RuleConflict] = []
        self._init_default_templates()
    
    def _validate_data(self, data: DRCRuleItem) -> ManagerResult:
        """Validate DRC rule item data.
        
        Args:
            data: DRC rule item to validate
            
        Returns:
            Manager result
        """
        try:
            # Basic validation
            if not isinstance(data, DRCRuleItem):
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Data must be a DRCRuleItem instance",
                    errors=["Invalid data type"]
                )
            
            # Validate rule name
            if not data.rule_name or not isinstance(data.rule_name, str):
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Invalid rule name",
                    errors=["rule_name must be a non-empty string"]
                )
            
            # Validate parameters
            if not isinstance(data.parameters, dict):
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Invalid parameters",
                    errors=["parameters must be a dictionary"]
                )
            
            # Validate thresholds
            if not isinstance(data.thresholds, dict):
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Invalid thresholds",
                    errors=["thresholds must be a dictionary"]
                )
            
            # Validate template name if provided
            if data.template_name and data.template_name not in self.templates:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Invalid template name",
                    errors=[f"Template '{data.template_name}' not found"]
                )
            
            return ManagerResult(
                success=True,
                operation=ManagerOperation.VALIDATE,
                status=ManagerStatus.SUCCESS,
                message="DRC rule item validation successful"
            )
            
        except Exception as e:
            self.logger.error(f"Error validating DRC rule item: {e}")
            return ManagerResult(
                success=False,
                operation=ManagerOperation.VALIDATE,
                status=ManagerStatus.FAILED,
                message=f"Validation error: {e}",
                errors=[str(e)]
            )
    
    def _cleanup_item(self, key: str) -> None:
        """Clean up resources for a DRC rule item.
        
        Args:
            key: Key of the item to clean up
        """
        try:
            # Remove from rules dictionary if present
            if key in self.rules:
                del self.rules[key]
            
            # Remove from conflicts if present
            self.conflicts = [conflict for conflict in self.conflicts 
                            if conflict.rule1 != key and conflict.rule2 != key]
            
            self.logger.debug(f"Cleaned up DRC rule item: {key}")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up DRC rule item {key}: {e}")
    
    def add_drc_rule(self, rule_name: str, rule_type: RuleType, category: ValidationCategory,
                    parameters: Dict[str, Any], thresholds: Dict[str, float],
                    severity: ValidationSeverity = ValidationSeverity.WARNING,
                    priority: RulePriority = RulePriority.MEDIUM,
                    template_name: Optional[str] = None) -> ManagerResult:
        """Add a DRC rule to the manager.
        
        Args:
            rule_name: Name of the rule
            rule_type: Type of the rule
            category: Category of the rule
            parameters: Rule parameters
            thresholds: Rule thresholds
            severity: Rule severity
            priority: Rule priority
            template_name: Optional template name
            
        Returns:
            Manager result
        """
        try:
            # Create DRC rule item
            item = DRCRuleItem(
                rule_name=rule_name,
                rule_type=rule_type,
                category=category,
                enabled=True,
                parameters=parameters,
                thresholds=thresholds,
                severity=severity,
                priority=priority,
                template_name=template_name
            )
            
            # Add to manager
            result = self.create(rule_name, item)
            
            if result.success:
                # Create and add validation rule
                validation_rule = ValidationRule(
                    rule_type=rule_type,
                    category=category,
                    enabled=True,
                    parameters=parameters,
                    thresholds=thresholds,
                    severity=severity
                )
                self.rules[rule_name] = validation_rule
                
                # Check for conflicts
                conflicts = self._check_rule_conflicts(validation_rule)
                if conflicts:
                    self.conflicts.extend(conflicts)
                    self.logger.warning(f"Rule conflicts detected: {conflicts}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error adding DRC rule {rule_name}: {e}")
            return ManagerResult(
                success=False,
                operation=ManagerOperation.CREATE,
                status=ManagerStatus.FAILED,
                message=f"Error adding DRC rule: {e}",
                errors=[str(e)]
            )
    
    def _init_default_templates(self) -> None:
        """Initialize default rule templates."""
        # Track width template
        self.templates["track_width"] = RuleTemplate(
            name="Track Width",
            description="Controls minimum and maximum track widths",
            rule_type=RuleType.DESIGN_RULES,
            parameters={
                "min_width": 0.1,  # mm
                "max_width": 5.0,  # mm
                "preferred_width": 0.2  # mm
            },
            thresholds={
                "min_width": 0.1,  # mm
                "max_width": 5.0  # mm
            },
            priority=RulePriority.HIGH,
            category=ValidationCategory.DESIGN_RULES
        )
        
        # Via size template
        self.templates["via_size"] = RuleTemplate(
            name="Via Size",
            description="Controls minimum and maximum via sizes",
            rule_type=RuleType.DESIGN_RULES,
            parameters={
                "min_diameter": 0.2,  # mm
                "max_diameter": 1.0,  # mm
                "min_drill": 0.1,  # mm
                "max_drill": 0.8  # mm
            },
            thresholds={
                "min_diameter": 0.2,  # mm
                "max_diameter": 1.0  # mm
            },
            priority=RulePriority.HIGH,
            category=ValidationCategory.DESIGN_RULES
        )
        
        # Clearance template
        self.templates["clearance"] = RuleTemplate(
            name="Clearance",
            description="Controls minimum clearance between objects",
            rule_type=RuleType.DESIGN_RULES,
            parameters={
                "min_clearance": 0.1,  # mm
                "preferred_clearance": 0.2  # mm
            },
            thresholds={
                "min_clearance": 0.1  # mm
            },
            priority=RulePriority.CRITICAL,
            category=ValidationCategory.DESIGN_RULES
        )
        
        # Impedance template
        self.templates["impedance"] = RuleTemplate(
            name="Impedance",
            description="Controls trace impedance requirements",
            rule_type=RuleType.DESIGN_RULES,
            parameters={
                "target_impedance": 50.0,  # ohms
                "tolerance": 5.0  # ohms
            },
            thresholds={
                "min_impedance": 45.0,  # ohms
                "max_impedance": 55.0  # ohms
            },
            priority=RulePriority.HIGH,
            category=ValidationCategory.DESIGN_RULES
        )
        
        # Thermal template
        self.templates["thermal"] = RuleTemplate(
            name="Thermal",
            description="Controls thermal management requirements",
            rule_type=RuleType.DESIGN_RULES,
            parameters={
                "max_temperature": 85.0,  # °C
                "min_clearance": 1.0,  # mm
                "max_power_density": 0.5  # W/mm²
            },
            thresholds={
                "max_temperature": 85.0,  # °C
                "min_clearance": 1.0  # mm
            },
            priority=RulePriority.HIGH,
            category=ValidationCategory.DESIGN_RULES
        )
        
        # Audio Manufacturing template
        self.templates["audio_manufacturing"] = RuleTemplate(
            name="Audio Manufacturing",
            description="Audio-specific DRC rules including impedance, EMI/EMC, and thermal constraints",
            rule_type=RuleType.AUDIO,
            parameters={
                "max_signal_length": 150.0,  # mm
                "min_isolation": 0.5,        # mm minimum isolation between ground zones
                "target_impedance": 50.0,    # ohms
                "tolerance": 3.0,            # ohms impedance tolerance
                "max_crosstalk": -60.0,      # dB maximum acceptable crosstalk
                "max_parallel_length": 50.0,  # mm maximum parallel segment length
                "require_thermal_pad": True,
                "require_test_points": True,
                "min_test_points": 5,
            },
            thresholds={
                "max_signal_length": 150.0  # mm
            },
            priority=RulePriority.MEDIUM,
            category=ValidationCategory.AUDIO_SPECIFIC,
        )
    
    def create_rule_from_template(self, template_name: str, **kwargs) -> Optional[ValidationRule]:
        """Create a rule from a template.
        
        Args:
            template_name: Name of the template to use
            **kwargs: Additional parameters to override template defaults
            
        Returns:
            Created validation rule or None if template not found
        """
        if template_name not in self.templates:
            self.logger.error(f"Template {template_name} not found")
            return None
        
        template = self.templates[template_name]
        
        # Create rule with template defaults
        rule = ValidationRule(
            rule_type=template.rule_type,
            category=template.category,
            enabled=template.enabled,
            parameters=template.parameters.copy(),
            thresholds=template.thresholds.copy(),
            severity=template.severity
        )
        
        # Override with provided parameters
        for key, value in kwargs.items():
            if key in rule.parameters:
                rule.parameters[key] = value
            if key in rule.thresholds:
                rule.thresholds[key] = value
        
        return rule
    
    def add_rule(self, rule: ValidationRule) -> bool:
        """Add a validation rule.
        
        Args:
            rule: Rule to add
            
        Returns:
            True if rule was added successfully
        """
        try:
            # Check for conflicts
            conflicts = self._check_rule_conflicts(rule)
            if conflicts:
                self.conflicts.extend(conflicts)
                self.logger.warning(f"Rule conflicts detected: {conflicts}")
            
            # Add rule
            self.rules[rule.rule_type.name] = rule
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding rule: {str(e)}")
            return False
    
    def _check_rule_conflicts(self, rule: ValidationRule) -> List[RuleConflict]:
        """Check for conflicts with existing rules.
        
        Args:
            rule: Rule to check
            
        Returns:
            List of rule conflicts
        """
        conflicts = []
        
        for existing_rule in self.rules.values():
            if existing_rule.rule_type == rule.rule_type:
                # Check parameter conflicts
                for param, value in rule.parameters.items():
                    if param in existing_rule.parameters:
                        if value < existing_rule.parameters[param]:
                            conflicts.append(RuleConflict(
                                rule1=rule.rule_type.name,
                                rule2=existing_rule.rule_type.name,
                                description=f"Parameter {param} value {value} is less than {existing_rule.parameters[param]}",
                                resolution="Use the higher value",
                                priority=RulePriority.HIGH
                            ))
                
                # Check threshold conflicts
                for threshold, value in rule.thresholds.items():
                    if threshold in existing_rule.thresholds:
                        if value < existing_rule.thresholds[threshold]:
                            conflicts.append(RuleConflict(
                                rule1=rule.rule_type.name,
                                rule2=existing_rule.rule_type.name,
                                description=f"Threshold {threshold} value {value} is less than {existing_rule.thresholds[threshold]}",
                                resolution="Use the higher value",
                                priority=RulePriority.HIGH
                            ))
        
        return conflicts
    
    def resolve_conflicts(self) -> None:
        """Resolve rule conflicts by applying resolutions."""
        for conflict in self.conflicts:
            if conflict.rule1 in self.rules and conflict.rule2 in self.rules:
                rule1 = self.rules[conflict.rule1]
                rule2 = self.rules[conflict.rule2]
                
                # Apply resolution based on priority
                if rule1.priority.value < rule2.priority.value:
                    # Rule1 has higher priority
                    self._apply_resolution(rule2, rule1)
                else:
                    # Rule2 has higher priority
                    self._apply_resolution(rule1, rule2)
        
        # Clear resolved conflicts
        self.conflicts = []
    
    def _apply_resolution(self, target_rule: ValidationRule, source_rule: ValidationRule) -> None:
        """Apply resolution to resolve conflict.
        
        Args:
            target_rule: Rule to modify
            source_rule: Rule with higher priority
        """
        # Update parameters
        for param, value in source_rule.parameters.items():
            if param in target_rule.parameters:
                target_rule.parameters[param] = max(
                    target_rule.parameters[param],
                    value
                )
        
        # Update thresholds
        for threshold, value in source_rule.thresholds.items():
            if threshold in target_rule.thresholds:
                target_rule.thresholds[threshold] = max(
                    target_rule.thresholds[threshold],
                    value
                )
    
    def validate_board(self) -> Dict[str, List[str]]:
        """Validate board against all rules.
        
        Returns:
            Dictionary of validation results by category
        """
        if not self.board:
            self.logger.error("No board available for validation")
            return {"error": ["No board available"]}
        
        try:
            results = {}
            
            # Run DRC
            drc = pcbnew.DRC()
            drc.SetBoard(self.board)
            drc.RunDRC()
            
            # Get DRC issues
            for marker in drc.GetMarkers():
                category = pcbnew.LayerName(marker.GetLayer())
                if category not in results:
                    results[category] = []
                
                results[category].append(
                    f"{marker.GetMessage()} at ({marker.GetPosition().x/1e6:.2f}, "
                    f"{marker.GetPosition().y/1e6:.2f})"
                )
            
            # Apply custom rules
            for rule in self.rules.values():
                if not rule.enabled:
                    continue
                
                if rule.category not in results:
                    results[rule.category] = []
                
                # Validate based on rule type
                if rule.rule_type == RuleType.DESIGN_RULES:
                    self._validate_design_rules(rule, results)
                elif rule.rule_type == RuleType.COMPONENT_PLACEMENT:
                    self._validate_component_placement(rule, results)
                elif rule.rule_type == RuleType.ROUTING:
                    self._validate_routing(rule, results)
                elif rule.rule_type == RuleType.MANUFACTURING:
                    self._validate_manufacturing(rule, results)
                elif rule.rule_type == RuleType.POWER:
                    self._validate_power(rule, results)
                elif rule.rule_type == RuleType.GROUND:
                    self._validate_ground(rule, results)
                elif rule.rule_type == RuleType.SIGNAL:
                    self._validate_signal(rule, results)
                elif rule.rule_type == RuleType.AUDIO:
                    self._validate_audio(rule, results)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error validating board: {str(e)}")
            return {"error": [str(e)]}
    
    def _validate_design_rules(self, rule: ValidationRule, results: Dict[str, List[str]]) -> None:
        """Validate design rules.
        
        Args:
            rule: Rule to validate
            results: Dictionary to store results
        """
        try:
            # Get design settings
            settings = self.board.GetDesignSettings()
            
            # Check track width
            if "min_width" in rule.parameters:
                track_width = settings.GetTrackWidth() / 1e6  # Convert to mm
                if track_width < rule.parameters["min_width"]:
                    results[rule.category].append(
                        f"Track width {track_width:.2f}mm is below minimum "
                        f"{rule.parameters['min_width']}mm"
                    )
            
            # Check via size
            if "min_diameter" in rule.parameters:
                via_size = settings.GetViasMinSize() / 1e6  # Convert to mm
                if via_size < rule.parameters["min_diameter"]:
                    results[rule.category].append(
                        f"Via size {via_size:.2f}mm is below minimum "
                        f"{rule.parameters['min_diameter']}mm"
                    )
            
            # Check clearance
            if "min_clearance" in rule.parameters:
                clearance = settings.GetMinClearance() / 1e6  # Convert to mm
                if clearance < rule.parameters["min_clearance"]:
                    results[rule.category].append(
                        f"Clearance {clearance:.2f}mm is below minimum "
                        f"{rule.parameters['min_clearance']}mm"
                    )
            
        except Exception as e:
            self.logger.error(f"Error validating design rules: {str(e)}")
            results[rule.category].append(f"Error: {str(e)}")
    
    def _validate_component_placement(self, rule: ValidationRule, results: Dict[str, List[str]]) -> None:
        """Validate component placement.
        
        Args:
            rule: Rule to validate
            results: Dictionary to store results
        """
        try:
            # Check component spacing
            if "min_spacing" in rule.parameters:
                for comp1 in self.board.GetFootprints():
                    for comp2 in self.board.GetFootprints():
                        if comp1 != comp2:
                            distance = self._calculate_distance(
                                comp1.GetPosition(),
                                comp2.GetPosition()
                            )
                            if distance < rule.parameters["min_spacing"]:
                                results[rule.category].append(
                                    f"Components {comp1.GetReference()} and "
                                    f"{comp2.GetReference()} are too close: "
                                    f"{distance:.2f}mm < {rule.parameters['min_spacing']}mm"
                                )
            
            # Check edge clearance
            if "edge_clearance" in rule.parameters:
                board_edges = self._get_board_edges()
                for comp in self.board.GetFootprints():
                    for edge in board_edges:
                        distance = self._calculate_distance_to_edge(
                            comp.GetPosition(),
                            edge
                        )
                        if distance < rule.parameters["edge_clearance"]:
                            results[rule.category].append(
                                f"Component {comp.GetReference()} is too close to board edge: "
                                f"{distance:.2f}mm < {rule.parameters['edge_clearance']}mm"
                            )
            
        except Exception as e:
            self.logger.error(f"Error validating component placement: {str(e)}")
            results[rule.category].append(f"Error: {str(e)}")
    
    def _validate_routing(self, rule: ValidationRule, results: Dict[str, List[str]]) -> None:
        """Validate routing.
        
        Args:
            rule: Rule to validate
            results: Dictionary to store results
        """
        try:
            # Check track width
            if "min_track_width" in rule.parameters:
                for track in self.board.GetTracks():
                    if track.IsTrack():
                        width = track.GetWidth() / 1e6  # Convert to mm
                        if width < rule.parameters["min_track_width"]:
                            results[rule.category].append(
                                f"Track width {width:.2f}mm is below minimum "
                                f"{rule.parameters['min_track_width']}mm at "
                                f"({track.GetStart().x/1e6:.2f}, {track.GetStart().y/1e6:.2f})"
                            )
            
            # Check via size
            if "min_via_size" in rule.parameters:
                for via in self.board.GetVias():
                    size = via.GetWidth() / 1e6  # Convert to mm
                    if size < rule.parameters["min_via_size"]:
                        results[rule.category].append(
                            f"Via size {size:.2f}mm is below minimum "
                            f"{rule.parameters['min_via_size']}mm at "
                            f"({via.GetPosition().x/1e6:.2f}, {via.GetPosition().y/1e6:.2f})"
                        )
            
            # Check track length
            if "max_length" in rule.parameters:
                for track in self.board.GetTracks():
                    if track.IsTrack():
                        length = track.GetLength() / 1e6  # Convert to mm
                        if length > rule.parameters["max_length"]:
                            results[rule.category].append(
                                f"Track length {length:.2f}mm exceeds maximum "
                                f"{rule.parameters['max_length']}mm at "
                                f"({track.GetStart().x/1e6:.2f}, {track.GetStart().y/1e6:.2f})"
                            )
            
        except Exception as e:
            self.logger.error(f"Error validating routing: {str(e)}")
            results[rule.category].append(f"Error: {str(e)}")
    
    def _validate_manufacturing(self, rule: ValidationRule, results: Dict[str, List[str]]) -> None:
        """Validate manufacturing rules.
        
        Args:
            rule: Rule to validate
            results: Dictionary to store results
        """
        try:
            # Check minimum feature size
            if "min_feature_size" in rule.parameters:
                for track in self.board.GetTracks():
                    if track.IsTrack():
                        width = track.GetWidth() / 1e6  # Convert to mm
                        if width < rule.parameters["min_feature_size"]:
                            results[rule.category].append(
                                f"Track width {width:.2f}mm is below minimum feature size "
                                f"{rule.parameters['min_feature_size']}mm at "
                                f"({track.GetStart().x/1e6:.2f}, {track.GetStart().y/1e6:.2f})"
                            )
            
            # Check board size
            if "max_board_size" in rule.parameters:
                board_edges = self._get_board_edges()
                width = abs(board_edges[1][0] - board_edges[0][0]) / 1e6  # Convert to mm
                height = abs(board_edges[2][1] - board_edges[0][1]) / 1e6  # Convert to mm
                if width > rule.parameters["max_board_size"] or height > rule.parameters["max_board_size"]:
                    results[rule.category].append(
                        f"Board size {width:.2f}x{height:.2f}mm exceeds maximum "
                        f"{rule.parameters['max_board_size']}mm"
                    )
            
            # Check annular ring
            if "min_annular_ring" in rule.parameters:
                for via in self.board.GetVias():
                    ring = (via.GetWidth() - via.GetDrill()) / 2e6  # Convert to mm
                    if ring < rule.parameters["min_annular_ring"]:
                        results[rule.category].append(
                            f"Via annular ring {ring:.2f}mm is below minimum "
                            f"{rule.parameters['min_annular_ring']}mm at "
                            f"({via.GetPosition().x/1e6:.2f}, {via.GetPosition().y/1e6:.2f})"
                        )
            
        except Exception as e:
            self.logger.error(f"Error validating manufacturing rules: {str(e)}")
            results[rule.category].append(f"Error: {str(e)}")
    
    def _validate_power(self, rule: ValidationRule, results: Dict[str, List[str]]) -> None:
        """Validate power rules.
        
        Args:
            rule: Rule to validate
            results: Dictionary to store results
        """
        try:
            # Check voltage drop
            if "max_voltage_drop" in rule.parameters:
                for track in self.board.GetTracks():
                    if track.IsTrack():
                        # Calculate voltage drop based on track length and width
                        length = track.GetLength() / 1e6  # Convert to mm
                        width = track.GetWidth() / 1e6  # Convert to mm
                        resistance = self._calculate_track_resistance(length, width)
                        current = 1.0  # Assume 1A for now
                        voltage_drop = resistance * current
                        
                        if voltage_drop > rule.parameters["max_voltage_drop"]:
                            results[rule.category].append(
                                f"Voltage drop {voltage_drop:.2f}V exceeds maximum "
                                f"{rule.parameters['max_voltage_drop']}V at "
                                f"({track.GetStart().x/1e6:.2f}, {track.GetStart().y/1e6:.2f})"
                            )
            
            # Check current density
            if "max_current_density" in rule.parameters:
                for track in self.board.GetTracks():
                    if track.IsTrack():
                        width = track.GetWidth() / 1e6  # Convert to mm
                        current = 1.0  # Assume 1A for now
                        current_density = current / (width * 0.035)  # 0.035mm is typical copper thickness
                        
                        if current_density > rule.parameters["max_current_density"]:
                            results[rule.category].append(
                                f"Current density {current_density:.2f}A/mm² exceeds maximum "
                                f"{rule.parameters['max_current_density']}A/mm² at "
                                f"({track.GetStart().x/1e6:.2f}, {track.GetStart().y/1e6:.2f})"
                            )
            
        except Exception as e:
            self.logger.error(f"Error validating power rules: {str(e)}")
            results[rule.category].append(f"Error: {str(e)}")
    
    def _validate_ground(self, rule: ValidationRule, results: Dict[str, List[str]]) -> None:
        """Validate ground rules.
        
        Args:
            rule: Rule to validate
            results: Dictionary to store results
        """
        try:
            # Check ground plane coverage
            if "min_coverage" in rule.parameters:
                total_area = self._calculate_board_area()
                ground_area = self._calculate_ground_area()
                coverage = ground_area / total_area
                
                if coverage < rule.parameters["min_coverage"]:
                    results[rule.category].append(
                        f"Ground plane coverage {coverage:.2%} is below minimum "
                        f"{rule.parameters['min_coverage']:.2%}"
                    )
            
            # Check ground via spacing
            if "max_via_spacing" in rule.parameters:
                for via1 in self.board.GetVias():
                    if via1.GetNetname() == "GND":
                        for via2 in self.board.GetVias():
                            if via2 != via1 and via2.GetNetname() == "GND":
                                distance = self._calculate_distance(
                                    via1.GetPosition(),
                                    via2.GetPosition()
                                )
                                if distance > rule.parameters["max_via_spacing"]:
                                    results[rule.category].append(
                                        f"Ground vias are too far apart: {distance:.2f}mm > "
                                        f"{rule.parameters['max_via_spacing']}mm at "
                                        f"({via1.GetPosition().x/1e6:.2f}, "
                                        f"{via1.GetPosition().y/1e6:.2f})"
                                    )
            
        except Exception as e:
            self.logger.error(f"Error validating ground rules: {str(e)}")
            results[rule.category].append(f"Error: {str(e)}")
    
    def _validate_signal(self, rule: ValidationRule, results: Dict[str, List[str]]) -> None:
        """Validate signal rules.
        
        Args:
            rule: Rule to validate
            results: Dictionary to store results
        """
        try:
            # Check impedance
            if "target_impedance" in rule.parameters:
                for track in self.board.GetTracks():
                    if track.IsTrack():
                        impedance = self._calculate_track_impedance(track)
                        tolerance = rule.parameters.get("tolerance", 5.0)
                        target = rule.parameters["target_impedance"]
                        
                        if abs(impedance - target) > tolerance:
                            results[rule.category].append(
                                f"Track impedance {impedance:.2f}Ω is outside tolerance "
                                f"{target}±{tolerance}Ω at "
                                f"({track.GetStart().x/1e6:.2f}, {track.GetStart().y/1e6:.2f})"
                            )
            
            # Check crosstalk
            if "max_crosstalk" in rule.parameters:
                for track1 in self.board.GetTracks():
                    if track1.IsTrack():
                        for track2 in self.board.GetTracks():
                            if track2 != track1 and track2.IsTrack():
                                crosstalk = self._calculate_crosstalk(track1, track2)
                                if crosstalk > rule.parameters["max_crosstalk"]:
                                    results[rule.category].append(
                                        f"Crosstalk {crosstalk:.2f}dB exceeds maximum "
                                        f"{rule.parameters['max_crosstalk']}dB between tracks at "
                                        f"({track1.GetStart().x/1e6:.2f}, {track1.GetStart().y/1e6:.2f}) and "
                                        f"({track2.GetStart().x/1e6:.2f}, {track2.GetStart().y/1e6:.2f})"
                                    )
            
        except Exception as e:
            self.logger.error(f"Error validating signal rules: {str(e)}")
            results[rule.category].append(f"Error: {str(e)}")
    
    def _validate_audio(self, rule: ValidationRule, results: Dict[str, List[str]]) -> None:
        """Validate audio rules.
        
        Args:
            rule: Rule to validate
            results: Dictionary to store results
        """
        try:
            # Check signal path length
            if "max_signal_length" in rule.parameters:
                for track in self.board.GetTracks():
                    if track.IsTrack():
                        length = track.GetLength() / 1e6  # Convert to mm
                        if length > rule.parameters["max_signal_length"]:
                            results[rule.category].append(
                                f"Signal path length {length:.2f}mm exceeds maximum "
                                f"{rule.parameters['max_signal_length']}mm at "
                                f"({track.GetStart().x/1e6:.2f}, {track.GetStart().y/1e6:.2f})"
                            )
            
            # Check ground plane isolation
            if "min_isolation" in rule.parameters:
                for zone1 in self.board.Zones():
                    if zone1.GetNetname() == "GND":
                        for zone2 in self.board.Zones():
                            if zone2 != zone1 and zone2.GetNetname() == "GND":
                                distance = self._calculate_zone_distance(zone1, zone2)
                                if distance < rule.parameters["min_isolation"]:
                                    results[rule.category].append(
                                        f"Ground plane isolation {distance:.2f}mm is below minimum "
                                        f"{rule.parameters['min_isolation']}mm between zones"
                                    )
            
            # Check impedance matching for audio traces
            if "target_impedance" in rule.parameters:
                target = rule.parameters["target_impedance"]
                tolerance = rule.parameters.get("tolerance", 5.0)
                for track in self.board.GetTracks():
                    if track.IsTrack():
                        impedance = self._calculate_track_impedance(track)
                        if abs(impedance - target) > tolerance:
                            results[rule.category].append(
                                f"Track impedance {impedance:.2f}Ω is outside target {target}±{tolerance}Ω at "
                                f"({track.GetStart().x/1e6:.2f}, {track.GetStart().y/1e6:.2f})"
                            )
            # Check inter-channel crosstalk
            if "max_crosstalk" in rule.parameters:
                max_xt = rule.parameters["max_crosstalk"]
                for track1 in self.board.GetTracks():
                    if not track1.IsTrack():
                        continue
                    for track2 in self.board.GetTracks():
                        if track2 == track1 or not track2.IsTrack():
                            continue
                        crosstalk = self._calculate_crosstalk(track1, track2)
                        if crosstalk > max_xt:
                            results[rule.category].append(
                                f"Crosstalk {crosstalk:.2f}dB exceeds maximum {max_xt}dB between tracks at "
                                f"({track1.GetStart().x/1e6:.2f}, {track1.GetStart().y/1e6:.2f}) and "
                                f"({track2.GetStart().x/1e6:.2f}, {track2.GetStart().y/1e6:.2f})"
                            )
            
            # ------------------------------------------------------------------
            # EMI / EMC – long parallel segments
            # ------------------------------------------------------------------
            if "max_parallel_length" in rule.parameters:
                max_pl = rule.parameters["max_parallel_length"]
                for track1 in self.board.GetTracks():
                    if not track1.IsTrack():
                        continue
                    for track2 in self.board.GetTracks():
                        if track2 == track1 or not track2.IsTrack():
                            continue
                        if track1.IsParallel(track2):
                            length = track1.GetLength() / 1e6  # mm
                            if length > max_pl:
                                results[rule.category].append(
                                    f"Parallel tracks length {length:.2f}mm exceeds maximum {max_pl}mm between tracks at "
                                    f"({track1.GetStart().x/1e6:.2f}, {track1.GetStart().y/1e6:.2f})"
                                )
            
            # ------------------------------------------------------------------
            # Thermal management – require thermal pads on power devices
            # ------------------------------------------------------------------
            if rule.parameters.get("require_thermal_pad", False):
                for fp in self.board.GetFootprints():
                    ref = fp.GetReference()
                    if not ref.startswith(("U", "Q", "VR")):
                        continue
                    has_thermal_pad = False
                    for pad in fp.Pads():
                        if pad.GetSize().x >= 2e6 or pad.GetSize().y >= 2e6:
                            has_thermal_pad = True
                            break
                    if not has_thermal_pad:
                        results[rule.category].append(
                            f"Component {ref} is missing a thermal pad at ({fp.GetPosition().x/1e6:.2f}, {fp.GetPosition().y/1e6:.2f})"
                        )
            
            # ------------------------------------------------------------------
            # Test point requirement
            # ------------------------------------------------------------------
            if rule.parameters.get("require_test_points", False):
                min_tp = rule.parameters.get("min_test_points", 1)
                tp_count = 0
                for fp in self.board.GetFootprints():
                    if fp.GetReference().startswith("TP"):
                        tp_count += 1
                if tp_count < min_tp:
                    results[rule.category].append(
                        f"Only {tp_count} test points found on board – minimum required is {min_tp}."
                    )
            
        except Exception as e:
            self.logger.error(f"Error validating audio rules: {str(e)}")
            results[rule.category].append(f"Error: {str(e)}")
    
    def _calculate_distance(self, pos1: pcbnew.VECTOR2I, pos2: pcbnew.VECTOR2I) -> float:
        """Calculate distance between two points.
        
        Args:
            pos1: First position
            pos2: Second position
            
        Returns:
            Distance in mm
        """
        dx = (pos2.x - pos1.x) / 1e6
        dy = (pos2.y - pos1.y) / 1e6
        return (dx * dx + dy * dy) ** 0.5
    
    def _calculate_distance_to_edge(self, pos: pcbnew.VECTOR2I, edge: Tuple[pcbnew.VECTOR2I, pcbnew.VECTOR2I]) -> float:
        """Calculate distance from point to edge.
        
        Args:
            pos: Point position
            edge: Edge defined by two points
            
        Returns:
            Distance in mm
        """
        x, y = pos.x / 1e6, pos.y / 1e6
        x1, y1 = edge[0].x / 1e6, edge[0].y / 1e6
        x2, y2 = edge[1].x / 1e6, edge[1].y / 1e6
        
        # Calculate distance from point to line segment
        A = x - x1
        B = y - y1
        C = x2 - x1
        D = y2 - y1
        
        dot = A * C + B * D
        len_sq = C * C + D * D
        
        if len_sq == 0:
            return self._calculate_distance(pos, edge[0])
        
        param = dot / len_sq
        
        if param < 0:
            return self._calculate_distance(pos, edge[0])
        elif param > 1:
            return self._calculate_distance(pos, edge[1])
        else:
            x = x1 + param * C
            y = y1 + param * D
            return ((pos.x/1e6 - x) ** 2 + (pos.y/1e6 - y) ** 2) ** 0.5
    
    def _get_board_edges(self) -> List[Tuple[pcbnew.VECTOR2I, pcbnew.VECTOR2I]]:
        """Get board edges.
        
        Returns:
            List of edges defined by two points
        """
        edges = []
        board_bbox = self.board.GetBoardEdgesBoundingBox()
        
        # Get corners
        corners = [
            pcbnew.VECTOR2I(board_bbox.GetLeft(), board_bbox.GetTop()),
            pcbnew.VECTOR2I(board_bbox.GetRight(), board_bbox.GetTop()),
            pcbnew.VECTOR2I(board_bbox.GetRight(), board_bbox.GetBottom()),
            pcbnew.VECTOR2I(board_bbox.GetLeft(), board_bbox.GetBottom())
        ]
        
        # Create edges
        for i in range(4):
            edges.append((corners[i], corners[(i + 1) % 4]))
        
        return edges
    
    def _calculate_board_area(self) -> float:
        """Calculate board area.
        
        Returns:
            Area in mm²
        """
        board_bbox = self.board.GetBoardEdgesBoundingBox()
        width = (board_bbox.GetRight() - board_bbox.GetLeft()) / 1e6
        height = (board_bbox.GetBottom() - board_bbox.GetTop()) / 1e6
        return width * height
    
    def _calculate_ground_area(self) -> float:
        """Calculate ground plane area.
        
        Returns:
            Area in mm²
        """
        area = 0.0
        for zone in self.board.Zones():
            if zone.GetNetname() == "GND":
                area += zone.GetArea() / 1e12  # Convert to mm²
        return area
    
    def _calculate_track_resistance(self, length: float, width: float) -> float:
        """Calculate track resistance.
        
        Args:
            length: Track length in mm
            width: Track width in mm
            
        Returns:
            Resistance in ohms
        """
        # Copper resistivity: 1.68e-8 ohm-m
        # Typical copper thickness: 0.035mm
        resistivity = 1.68e-8
        thickness = 0.035e-3
        return resistivity * length * 1e-3 / (width * 1e-3 * thickness)
    
    def _calculate_track_impedance(self, track: pcbnew.TRACK) -> float:
        """Calculate track impedance.
        
        Args:
            track: Track to calculate impedance for
            
        Returns:
            Impedance in ohms
        """
        # Get track properties
        width = track.GetWidth() / 1e6  # Convert to mm
        height = 0.035  # Typical substrate height in mm
        er = 4.5  # Typical dielectric constant
        
        # Calculate microstrip impedance
        # Simplified formula for microstrip
        return 87 / (er + 1.41) ** 0.5 * math.log(5.98 * height / (0.8 * width + 0.1 * height))
    
    def _calculate_crosstalk(self, track1: pcbnew.TRACK, track2: pcbnew.TRACK) -> float:
        """Calculate crosstalk between tracks.
        
        Args:
            track1: First track
            track2: Second track
            
        Returns:
            Crosstalk in dB
        """
        # Get track properties
        width1 = track1.GetWidth() / 1e6  # Convert to mm
        width2 = track2.GetWidth() / 1e6  # Convert to mm
        height = 0.035  # Typical substrate height in mm
        er = 4.5  # Typical dielectric constant
        
        # Calculate distance between tracks
        distance = self._calculate_distance(track1.GetStart(), track2.GetStart())
        
        # Calculate crosstalk
        # Simplified formula for crosstalk
        return 20 * math.log10(1 / (1 + (distance / height) ** 2))
    
    def _calculate_zone_distance(self, zone1: pcbnew.ZONE, zone2: pcbnew.ZONE) -> float:
        """Calculate distance between zones.
        
        Args:
            zone1: First zone
            zone2: Second zone
            
        Returns:
            Distance in mm
        """
        # Get zone outlines
        outline1 = zone1.GetOutline()
        outline2 = zone2.GetOutline()
        
        # Calculate minimum distance between outlines
        min_distance = float('inf')
        for i in range(outline1.PointCount()):
            p1 = outline1.CPoint(i)
            for j in range(outline2.PointCount()):
                p2 = outline2.CPoint(j)
                distance = self._calculate_distance(p1, p2)
                min_distance = min(min_distance, distance)
        
        return min_distance 