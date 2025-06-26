"""
Example demonstrating the validation system for audio PCB design.

This example shows how to:
1. Create and configure validators
2. Run validation on a PCB design
3. Handle validation results
4. Use audio-specific validation features
"""

import os
from typing import Dict, List, Any
import pcbnew
from kicad_pcb_generator.core.validation import (
    BaseValidator,
    ValidationResult,
    ValidationSeverity,
    ValidationCategory
)
from kicad_pcb_generator.audio.validation import AudioValidator
from kicad_pcb_generator.utils.logging import Logger

def setup_validators() -> Dict[str, BaseValidator]:
    """Set up and configure validators."""
    # Create logger
    logger = Logger(__name__)

    # Create audio validator
    audio_validator = AudioValidator()
    
    # Enable specific rules
    audio_validator.enable_rule("check_audio_components")
    audio_validator.enable_rule("check_signal_paths")
    audio_validator.enable_rule("check_power_supply")
    audio_validator.enable_rule("check_grounding")
    audio_validator.enable_rule("check_impedance")
    audio_validator.enable_rule("check_crosstalk")

    return {
        "audio": audio_validator
    }

def validate_board(board_path: str, validators: Dict[str, BaseValidator]) -> Dict[str, ValidationResult]:
    """Validate a PCB board using all validators."""
    # Load the board
    board = pcbnew.LoadBoard(board_path)
    
    # Run validation
    results = {}
    for name, validator in validators.items():
        try:
            results[name] = validator.validate(board)
        except Exception as e:
            print(f"Error in {name} validation: {e}")
            results[name] = ValidationResult()
            results[name].add_issue(
                message=f"Validation failed: {str(e)}",
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.DESIGN_RULES
            )
    
    return results

def print_validation_results(results: Dict[str, ValidationResult]) -> None:
    """Print validation results in a readable format."""
    for validator_name, result in results.items():
        print(f"\n=== {validator_name.upper()} Validation Results ===")
        
        if result.is_valid:
            print("✓ All validations passed")
        else:
            print("✗ Validation issues found")
        
        # Print issues by severity
        for severity in ValidationSeverity:
            issues = result.get_issues(severity=severity)
            if issues:
                print(f"\n{severity.value.upper()} Issues:")
                for issue in issues:
                    print(f"  - {issue.message}")
                    if issue.suggestion:
                        print(f"    Suggestion: {issue.suggestion}")
                    if issue.documentation_ref:
                        print(f"    Documentation: {issue.documentation_ref}")

def print_audio_metrics(result: ValidationResult) -> None:
    """Print audio-specific metrics."""
    if not isinstance(result, AudioValidationResult):
        return
    
    print("\n=== Audio Metrics ===")
    
    # Print audio metrics
    if result.audio_metrics:
        print("\nAudio Performance:")
        for name, value in result.audio_metrics.items():
            print(f"  {name}: {value}")
    
    # Print signal paths
    if result.signal_paths:
        print("\nSignal Paths:")
        for path in result.signal_paths:
            print(f"  Path: {path['name']}")
            print(f"    Length: {path['length']} mm")
            print(f"    Impedance: {path.get('impedance', 'N/A')} Ω")
    
    # Print power metrics
    if result.power_metrics:
        print("\nPower Metrics:")
        for name, value in result.power_metrics.items():
            print(f"  {name}: {value}")
    
    # Print ground metrics
    if result.ground_metrics:
        print("\nGround Metrics:")
        for name, value in result.ground_metrics.items():
            print(f"  {name}: {value}")

def main():
    """Main function demonstrating the validation system."""
    # Get the board path from command line or use default
    board_path = os.getenv("BOARD_PATH", "example_board.kicad_pcb")
    
    # Set up validators
    validators = setup_validators()
    
    # Run validation
    results = validate_board(board_path, validators)
    
    # Print results
    print_validation_results(results)
    
    # Print audio-specific metrics
    if "audio" in results:
        print_audio_metrics(results["audio"])

if __name__ == "__main__":
    main() 
