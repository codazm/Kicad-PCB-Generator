# Validation System API Documentation

## Overview

The validation system provides a comprehensive framework for validating PCB designs, with special focus on audio-specific requirements. The system is built on a modular architecture that allows for easy extension and customization, with robust error handling and detailed reporting.

## Core Components

### Base Classes

#### `BaseValidator`

The foundation of the validation system, providing common functionality for all validators with enhanced error handling.

```python
class BaseValidator:
    def __init__(self, logger: Optional[Logger] = None):
        """Initialize the validator with optional logger."""
        self.logger = logger or logging.getLogger(__name__)
        self.enabled_rules = set()
        self.rule_configs = {}

    def enable_rule(self, rule: str) -> None:
        """Enable a validation rule with error handling."""
        try:
            if rule in self.available_rules:
                self.enabled_rules.add(rule)
                self.logger.info(f"Enabled validation rule: {rule}")
            else:
                raise ValueError(f"Unknown validation rule: {rule}")
        except (ValueError, KeyError) as e:
            self.logger.error(f"Error enabling rule {rule}: {e}")
            raise

    def disable_rule(self, rule: str) -> None:
        """Disable a validation rule with error handling."""
        try:
            if rule in self.enabled_rules:
                self.enabled_rules.remove(rule)
                self.logger.info(f"Disabled validation rule: {rule}")
            else:
                self.logger.warning(f"Rule {rule} was not enabled")
        except (ValueError, KeyError) as e:
            self.logger.error(f"Error disabling rule {rule}: {e}")
            raise

    def is_rule_enabled(self, rule: str) -> bool:
        """Check if a rule is enabled with error handling."""
        try:
            return rule in self.enabled_rules
        except (ValueError, KeyError) as e:
            self.logger.error(f"Error checking rule status {rule}: {e}")
            return False
```

#### `CommonValidatorMixin`

Provides shared validation functionality across different validator types with comprehensive error handling.

```python
class CommonValidatorMixin:
    def validate_rules(self, *args, **kwargs) -> ValidationResult:
        """Validate using registered rules with enhanced error handling."""
        try:
            result = ValidationResult()
            
            for rule in self.enabled_rules:
                try:
                    rule_result = self._execute_rule(rule, *args, **kwargs)
                    result.merge(rule_result)
                except (ValueError, KeyError, AttributeError) as e:
                    error_msg = f"Rule {rule} failed: {e}"
                    self.logger.error(error_msg)
                    result.add_issue(
                        message=error_msg,
                        severity=ValidationSeverity.ERROR,
                        category=ValidationCategory.VALIDATION_ERROR,
                        suggestion="Check rule configuration and input data"
                    )
                except Exception as e:
                    error_msg = f"Unexpected error in rule {rule}: {e}"
                    self.logger.error(error_msg)
                    result.add_issue(
                        message=error_msg,
                        severity=ValidationSeverity.CRITICAL,
                        category=ValidationCategory.SYSTEM_ERROR,
                        suggestion="Enable debug logging for detailed investigation"
                    )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            return ValidationResult(
                is_valid=False,
                issues=[ValidationIssue(
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Validation system error: {e}",
                    suggestion="Check system resources and restart if needed"
                )]
            )

    def get_rule_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about registered rules with error handling."""
        try:
            rule_info = {}
            for rule_name in self.available_rules:
                try:
                    rule_info[rule_name] = {
                        'description': self._get_rule_description(rule_name),
                        'parameters': self._get_rule_parameters(rule_name),
                        'enabled': rule_name in self.enabled_rules
                    }
                except (ValueError, KeyError) as e:
                    self.logger.warning(f"Could not get info for rule {rule_name}: {e}")
                    rule_info[rule_name] = {
                        'description': 'Rule information unavailable',
                        'parameters': {},
                        'enabled': rule_name in self.enabled_rules
                    }
            return rule_info
        except Exception as e:
            self.logger.error(f"Error getting rule information: {e}")
            return {}
```

### Validation Modules

#### Signal Integrity Validation

```python
class SignalIntegrityTester:
    def test_signal_integrity(self) -> Dict[str, Any]:
        """Run signal integrity tests with comprehensive error handling."""
        try:
            results = {
                'passed': True,
                'tests': {},
                'errors': []
            }
            
            # Test impedance matching
            try:
                impedance_result = self.test_impedance()
                results['tests']['impedance'] = impedance_result
                if not impedance_result['passed']:
                    results['passed'] = False
            except (ValueError, KeyError) as e:
                error_msg = f"Impedance test failed: {e}"
                self.logger.error(error_msg)
                results['errors'].append(error_msg)
                results['passed'] = False
            
            # Test crosstalk
            try:
                crosstalk_result = self.test_crosstalk()
                results['tests']['crosstalk'] = crosstalk_result
                if not crosstalk_result['passed']:
                    results['passed'] = False
            except (ValueError, KeyError) as e:
                error_msg = f"Crosstalk test failed: {e}"
                self.logger.error(error_msg)
                results['errors'].append(error_msg)
                results['passed'] = False
            
            # Test reflections
            try:
                reflection_result = self.test_reflections()
                results['tests']['reflections'] = reflection_result
                if not reflection_result['passed']:
                    results['passed'] = False
            except (ValueError, KeyError) as e:
                error_msg = f"Reflection test failed: {e}"
                self.logger.error(error_msg)
                results['errors'].append(error_msg)
                results['passed'] = False
            
            return results
            
        except Exception as e:
            self.logger.error(f"Signal integrity testing failed: {e}")
            return {
                'passed': False,
                'tests': {},
                'errors': [f"Signal integrity testing error: {e}"]
            }

    def test_impedance(self) -> Dict[str, Any]:
        """Test impedance matching with error handling."""
        try:
            # Implementation details...
            return {'passed': True, 'details': 'Impedance matching OK'}
        except (ValueError, KeyError) as e:
            self.logger.error(f"Impedance test error: {e}")
            return {'passed': False, 'error': str(e)}
        except Exception as e:
            self.logger.error(f"Unexpected impedance test error: {e}")
            return {'passed': False, 'error': f"Unexpected error: {e}"}

    def test_crosstalk(self) -> Dict[str, Any]:
        """Test crosstalk between signals with error handling."""
        try:
            # Implementation details...
            return {'passed': True, 'details': 'Crosstalk within limits'}
        except (ValueError, KeyError) as e:
            self.logger.error(f"Crosstalk test error: {e}")
            return {'passed': False, 'error': str(e)}
        except Exception as e:
            self.logger.error(f"Unexpected crosstalk test error: {e}")
            return {'passed': False, 'error': f"Unexpected error: {e}"}

    def test_reflections(self) -> Dict[str, Any]:
        """Test signal reflections with error handling."""
        try:
            # Implementation details...
            return {'passed': True, 'details': 'Reflections acceptable'}
        except (ValueError, KeyError) as e:
            self.logger.error(f"Reflection test error: {e}")
            return {'passed': False, 'error': str(e)}
        except Exception as e:
            self.logger.error(f"Unexpected reflection test error: {e}")
            return {'passed': False, 'error': f"Unexpected error: {e}"}
```

#### Power/Ground Validation

```python
class PowerGroundTester:
    def test_power_ground(self) -> Dict[str, Any]:
        """Run power and ground tests with comprehensive error handling."""
        try:
            results = {
                'passed': True,
                'tests': {},
                'errors': []
            }
            
            # Test power supply distribution
            try:
                power_result = self.test_power_supply()
                results['tests']['power_supply'] = power_result
                if not power_result['passed']:
                    results['passed'] = False
            except (ValueError, KeyError) as e:
                error_msg = f"Power supply test failed: {e}"
                self.logger.error(error_msg)
                results['errors'].append(error_msg)
                results['passed'] = False
            
            # Test ground plane coverage
            try:
                ground_result = self.test_ground_plane()
                results['tests']['ground_plane'] = ground_result
                if not ground_result['passed']:
                    results['passed'] = False
            except (ValueError, KeyError) as e:
                error_msg = f"Ground plane test failed: {e}"
                self.logger.error(error_msg)
                results['errors'].append(error_msg)
                results['passed'] = False
            
            # Test decoupling capacitor placement
            try:
                decoupling_result = self.test_decoupling()
                results['tests']['decoupling'] = decoupling_result
                if not decoupling_result['passed']:
                    results['passed'] = False
            except (ValueError, KeyError) as e:
                error_msg = f"Decoupling test failed: {e}"
                self.logger.error(error_msg)
                results['errors'].append(error_msg)
                results['passed'] = False
            
            return results
            
        except Exception as e:
            self.logger.error(f"Power/ground testing failed: {e}")
            return {
                'passed': False,
                'tests': {},
                'errors': [f"Power/ground testing error: {e}"]
            }

    def test_power_supply(self) -> Dict[str, Any]:
        """Test power supply distribution with error handling."""
        try:
            # Implementation details...
            return {'passed': True, 'details': 'Power supply distribution OK'}
        except (ValueError, KeyError) as e:
            self.logger.error(f"Power supply test error: {e}")
            return {'passed': False, 'error': str(e)}
        except Exception as e:
            self.logger.error(f"Unexpected power supply test error: {e}")
            return {'passed': False, 'error': f"Unexpected error: {e}"}

    def test_ground_plane(self) -> Dict[str, Any]:
        """Test ground plane coverage with error handling."""
        try:
            # Implementation details...
            return {'passed': True, 'details': 'Ground plane coverage adequate'}
        except (ValueError, KeyError) as e:
            self.logger.error(f"Ground plane test error: {e}")
            return {'passed': False, 'error': str(e)}
        except Exception as e:
            self.logger.error(f"Unexpected ground plane test error: {e}")
            return {'passed': False, 'error': f"Unexpected error: {e}"}

    def test_decoupling(self) -> Dict[str, Any]:
        """Test decoupling capacitor placement with error handling."""
        try:
            # Implementation details...
            return {'passed': True, 'details': 'Decoupling capacitors properly placed'}
        except (ValueError, KeyError) as e:
            self.logger.error(f"Decoupling test error: {e}")
            return {'passed': False, 'error': str(e)}
        except Exception as e:
            self.logger.error(f"Unexpected decoupling test error: {e}")
            return {'passed': False, 'error': f"Unexpected error: {e}"}
```

#### EMI/EMC Validation

```python
class EMIEMCTester:
    def test_emi_emc(self) -> Dict[str, Any]:
        """Run EMI/EMC tests with comprehensive error handling."""
        try:
            results = {
                'passed': True,
                'tests': {},
                'errors': []
            }
            
            # Test electromagnetic emissions
            try:
                emissions_result = self.test_emissions()
                results['tests']['emissions'] = emissions_result
                if not emissions_result['passed']:
                    results['passed'] = False
            except (ValueError, KeyError) as e:
                error_msg = f"Emissions test failed: {e}"
                self.logger.error(error_msg)
                results['errors'].append(error_msg)
                results['passed'] = False
            
            # Test electromagnetic immunity
            try:
                immunity_result = self.test_immunity()
                results['tests']['immunity'] = immunity_result
                if not immunity_result['passed']:
                    results['passed'] = False
            except (ValueError, KeyError) as e:
                error_msg = f"Immunity test failed: {e}"
                self.logger.error(error_msg)
                results['errors'].append(error_msg)
                results['passed'] = False
            
            # Test shielding effectiveness
            try:
                shielding_result = self.test_shielding()
                results['tests']['shielding'] = shielding_result
                if not shielding_result['passed']:
                    results['passed'] = False
            except (ValueError, KeyError) as e:
                error_msg = f"Shielding test failed: {e}"
                self.logger.error(error_msg)
                results['errors'].append(error_msg)
                results['passed'] = False
            
            return results
            
        except Exception as e:
            self.logger.error(f"EMI/EMC testing failed: {e}")
            return {
                'passed': False,
                'tests': {},
                'errors': [f"EMI/EMC testing error: {e}"]
            }

    def test_emissions(self) -> Dict[str, Any]:
        """Test electromagnetic emissions with error handling."""
        try:
            # Implementation details...
            return {'passed': True, 'details': 'Emissions within limits'}
        except (ValueError, KeyError) as e:
            self.logger.error(f"Emissions test error: {e}")
            return {'passed': False, 'error': str(e)}
        except Exception as e:
            self.logger.error(f"Unexpected emissions test error: {e}")
            return {'passed': False, 'error': f"Unexpected error: {e}"}

    def test_immunity(self) -> Dict[str, Any]:
        """Test electromagnetic immunity with error handling."""
        try:
            # Implementation details...
            return {'passed': True, 'details': 'Immunity adequate'}
        except (ValueError, KeyError) as e:
            self.logger.error(f"Immunity test error: {e}")
            return {'passed': False, 'error': str(e)}
        except Exception as e:
            self.logger.error(f"Unexpected immunity test error: {e}")
            return {'passed': False, 'error': f"Unexpected error: {e}"}

    def test_shielding(self) -> Dict[str, Any]:
        """Test shielding effectiveness with error handling."""
        try:
            # Implementation details...
            return {'passed': True, 'details': 'Shielding effective'}
        except (ValueError, KeyError) as e:
            self.logger.error(f"Shielding test error: {e}")
            return {'passed': False, 'error': str(e)}
        except Exception as e:
            self.logger.error(f"Unexpected shielding test error: {e}")
            return {'passed': False, 'error': f"Unexpected error: {e}"}
```

### Validation Results

#### `ValidationResult`

Base class for validation results with enhanced error reporting.

```python
class ValidationResult:
    def __init__(self, is_valid: bool = True, issues: List[ValidationIssue] = None):
        """Initialize validation result with error handling."""
        self.is_valid = is_valid
        self.issues = issues or []
        self.metadata = {}
        self.timestamp = datetime.now()

    def get_issues(self, severity: Optional[ValidationSeverity] = None) -> List[ValidationIssue]:
        """Get validation issues, optionally filtered by severity with error handling."""
        try:
            if severity is None:
                return self.issues.copy()
            else:
                return [issue for issue in self.issues if issue.severity == severity]
        except (ValueError, KeyError) as e:
            # Log error but return empty list to prevent cascading failures
            logging.getLogger(__name__).error(f"Error filtering issues by severity: {e}")
            return []

    def add_issue(self, message: str, severity: ValidationSeverity, 
                  category: ValidationCategory = ValidationCategory.GENERAL,
                  suggestion: Optional[str] = None,
                  documentation_ref: Optional[str] = None) -> None:
        """Add a validation issue with error handling."""
        try:
            issue = ValidationIssue(
                severity=severity,
                message=message,
                category=category,
                suggestion=suggestion,
                documentation_ref=documentation_ref
            )
            self.issues.append(issue)
            
            # Update validity based on severity
            if severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]:
                self.is_valid = False
                
        except (ValueError, KeyError, AttributeError) as e:
            logging.getLogger(__name__).error(f"Error adding validation issue: {e}")

    def merge(self, other: 'ValidationResult') -> None:
        """Merge another validation result with error handling."""
        try:
            if not isinstance(other, ValidationResult):
                raise ValueError("Can only merge ValidationResult objects")
            
            self.issues.extend(other.issues)
            
            # Update validity
            if not other.is_valid:
                self.is_valid = False
                
            # Merge metadata
            self.metadata.update(other.metadata)
            
        except (ValueError, KeyError, AttributeError) as e:
            logging.getLogger(__name__).error(f"Error merging validation results: {e}")
```

#### `ValidationIssue`

Represents a single validation issue with enhanced information.

```python
class ValidationIssue:
    def __init__(self, severity: ValidationSeverity, message: str, 
                 category: ValidationCategory = ValidationCategory.GENERAL,
                 suggestion: Optional[str] = None,
                 documentation_ref: Optional[str] = None,
                 context: Optional[Dict[str, Any]] = None):
        """Initialize validation issue with comprehensive information."""
        self.severity = severity
        self.message = message
        self.category = category
        self.suggestion = suggestion
        self.documentation_ref = documentation_ref
        self.context = context or {}
        self.timestamp = datetime.now()

    def __str__(self) -> str:
        """String representation with enhanced formatting."""
        parts = [f"[{self.severity.value}] {self.message}"]
        
        if self.suggestion:
            parts.append(f"Suggestion: {self.suggestion}")
        
        if self.documentation_ref:
            parts.append(f"See: {self.documentation_ref}")
        
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            parts.append(f"Context: {context_str}")
        
        return " | ".join(parts)
```

## Usage Examples

### Basic Validation with Error Handling

```python
from kicad_pcb_generator.core.validation import SignalIntegrityTester, PowerGroundTester, EMIEMCTester
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_validation_tests():
    """Run all validation tests with comprehensive error handling."""
    
    try:
        # Create testers
        si_tester = SignalIntegrityTester()
        pg_tester = PowerGroundTester()
        emi_tester = EMIEMCTester()
        
        results = {}
        
        # Run signal integrity tests
        try:
            si_results = si_tester.test_signal_integrity()
            results['signal_integrity'] = si_results
            logger.info(f"Signal integrity passed: {si_results['passed']}")
        except Exception as e:
            logger.error(f"Signal integrity testing failed: {e}")
            results['signal_integrity'] = {'passed': False, 'error': str(e)}
        
        # Run power/ground tests
        try:
            pg_results = pg_tester.test_power_ground()
            results['power_ground'] = pg_results
            logger.info(f"Power/ground passed: {pg_results['passed']}")
        except Exception as e:
            logger.error(f"Power/ground testing failed: {e}")
            results['power_ground'] = {'passed': False, 'error': str(e)}
        
        # Run EMI/EMC tests
        try:
            emi_results = emi_tester.test_emi_emc()
            results['emi_emc'] = emi_results
            logger.info(f"EMI/EMC passed: {emi_results['passed']}")
        except Exception as e:
            logger.error(f"EMI/EMC testing failed: {e}")
            results['emi_emc'] = {'passed': False, 'error': str(e)}
        
        return results
        
    except Exception as e:
        logger.error(f"Validation testing failed: {e}")
        return {'error': str(e)}
```

### Audio-Specific Validation with Enhanced Error Reporting

```python
from kicad_pcb_generator.audio.validation import AudioPCBValidator
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_audio_board(board):
    """Validate audio board with comprehensive error handling and reporting."""
    
    try:
        # Create audio validator
        audio_validator = AudioPCBValidator()
        
        # Configure validation rules
        try:
            audio_validator.enable_rule("check_audio_components")
            audio_validator.enable_rule("check_signal_paths")
            audio_validator.enable_rule("check_power_supply")
            audio_validator.enable_rule("check_grounding")
            audio_validator.enable_rule("check_impedance")
            audio_validator.enable_rule("check_crosstalk")
            logger.info("Audio validation rules configured")
        except (ValueError, KeyError) as e:
            logger.error(f"Error configuring validation rules: {e}")
            raise
        
        # Validate board
        try:
            results = audio_validator.validate_board(board)
            logger.info("Audio board validation completed")
        except Exception as e:
            logger.error(f"Board validation failed: {e}")
            raise
        
        # Process results with detailed error reporting
        if not results.is_valid:
            logger.warning("Audio board validation issues found:")
            
            # Group issues by category
            for category in ValidationCategory:
                category_issues = [issue for issue in results.issues 
                                 if issue.category == category]
                if category_issues:
                    logger.warning(f"\n{category.value.upper()} Issues:")
                    for issue in category_issues:
                        logger.warning(f"  - {issue.severity.value}: {issue.message}")
                        if issue.suggestion:
                            logger.info(f"    Suggestion: {issue.suggestion}")
                        if issue.documentation_ref:
                            logger.info(f"    Documentation: {issue.documentation_ref}")
        else:
            logger.info("✓ Audio board validation passed")
        
        return results
        
    except (ValueError, KeyError) as e:
        logger.error(f"Configuration error in audio validation: {e}")
        raise
    except (FileNotFoundError, PermissionError) as e:
        logger.error(f"File access error in audio validation: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in audio validation: {e}")
        raise
```

### Advanced Error Handling and Recovery

```python
def robust_validation_workflow(board_path: str):
    """Robust validation workflow with comprehensive error handling and recovery."""
    
    logger = logging.getLogger(__name__)
    
    try:
        # Load board with error handling
        try:
            board = pcbnew.LoadBoard(board_path)
            logger.info(f"Board loaded: {board_path}")
        except (FileNotFoundError, PermissionError) as e:
            logger.error(f"Failed to load board {board_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error loading board: {e}")
            return False
        
        # Run validation with recovery
        validation_results = {}
        
        # Signal integrity validation
        try:
            si_validator = SignalIntegrityTester()
            si_results = si_validator.test_signal_integrity()
            validation_results['signal_integrity'] = si_results
            
            if not si_results['passed']:
                logger.warning("Signal integrity issues detected")
                for error in si_results.get('errors', []):
                    logger.warning(f"  - {error}")
                    
        except Exception as e:
            logger.error(f"Signal integrity validation failed: {e}")
            validation_results['signal_integrity'] = {
                'passed': False, 
                'error': str(e),
                'recoverable': True
            }
        
        # Power/ground validation
        try:
            pg_validator = PowerGroundTester()
            pg_results = pg_validator.test_power_ground()
            validation_results['power_ground'] = pg_results
            
            if not pg_results['passed']:
                logger.warning("Power/ground issues detected")
                for error in pg_results.get('errors', []):
                    logger.warning(f"  - {error}")
                    
        except Exception as e:
            logger.error(f"Power/ground validation failed: {e}")
            validation_results['power_ground'] = {
                'passed': False, 
                'error': str(e),
                'recoverable': True
            }
        
        # Audio-specific validation
        try:
            audio_validator = AudioPCBValidator()
            audio_results = audio_validator.validate_board(board)
            validation_results['audio'] = audio_results
            
            if not audio_results.is_valid:
                logger.warning("Audio-specific issues detected")
                for issue in audio_results.get_issues():
                    logger.warning(f"  - {issue.severity.value}: {issue.message}")
                    if issue.suggestion:
                        logger.info(f"    Suggestion: {issue.suggestion}")
                        
        except Exception as e:
            logger.error(f"Audio validation failed: {e}")
            validation_results['audio'] = {
                'passed': False, 
                'error': str(e),
                'recoverable': True
            }
        
        # Generate comprehensive report
        generate_validation_report(validation_results)
        
        # Determine overall success
        overall_success = all(
            result.get('passed', False) 
            for result in validation_results.values()
        )
        
        if overall_success:
            logger.info("✓ All validations passed")
        else:
            logger.warning("✗ Some validations failed")
            
        return overall_success
        
    except Exception as e:
        logger.error(f"Validation workflow failed: {e}")
        return False

def generate_validation_report(results: Dict[str, Any]):
    """Generate a comprehensive validation report."""
    
    logger = logging.getLogger(__name__)
    
    logger.info("\n" + "="*50)
    logger.info("VALIDATION REPORT")
    logger.info("="*50)
    
    for test_name, result in results.items():
        logger.info(f"\n{test_name.upper()}:")
        
        if result.get('passed', False):
            logger.info("  ✓ PASSED")
        else:
            logger.error("  ✗ FAILED")
            
            # Report errors
            for error in result.get('errors', []):
                logger.error(f"    - {error}")
            
            # Report test details
            for test_type, test_result in result.get('tests', {}).items():
                if not test_result.get('passed', False):
                    logger.warning(f"    {test_type}: {test_result.get('error', 'Failed')}")
    
    logger.info("\n" + "="*50)
```

This enhanced validation API provides comprehensive error handling, detailed reporting, and robust recovery mechanisms to ensure reliable PCB validation. 
