# Error Handling Guide

[Home](../README.md) > [Guides](README.md) > Error Handling Guide

> **Related Documentation:**
> - [User Guide](../user/user_guide.md) - Complete user manual
> - [Installation Guide](../user/INSTALLATION.md) - Installation instructions
> - [FAQ](../user/faq.md) - Common questions
> - [Troubleshooting Guide](troubleshooting.md) - Detailed troubleshooting
> - [Debug Guide](debug.md) - Advanced debugging techniques

## Overview

The KiCad PCB Generator features a comprehensive error handling system designed to provide clear, actionable feedback for all types of issues. This guide explains how to understand and resolve errors effectively.

## Error Categories

### 1. Configuration Errors (ValueError, KeyError, AttributeError)

**Description**: Issues with project settings, configuration files, or invalid parameters.

**Common Causes**:
- Invalid project configuration
- Missing required parameters
- Incorrect data types
- Malformed configuration files

**Example**:
```python
try:
    result = generator.generate_pcb("my_project", config=invalid_config)
except (ValueError, KeyError, AttributeError) as e:
    print(f"Configuration error: {e}")
    # Check project settings and configuration files
```

**Resolution**:
- Review project configuration files
- Check parameter types and values
- Validate configuration against schema
- Use the configuration validator

### 2. File Access Errors (FileNotFoundError, PermissionError)

**Description**: Problems with file operations, permissions, or missing files.

**Common Causes**:
- Missing project files
- Insufficient file permissions
- Incorrect file paths
- Locked files

**Example**:
```python
try:
    board = pcbnew.LoadBoard("missing_board.kicad_pcb")
except (FileNotFoundError, PermissionError) as e:
    print(f"File access error: {e}")
    # Check file existence and permissions
```

**Resolution**:
- Verify file paths and existence
- Check file permissions
- Ensure files aren't locked by other applications
- Use absolute paths if needed

### 3. Validation Errors

**Description**: Issues found during design validation and rule checking.

**Common Causes**:
- Design rule violations
- Signal integrity issues
- Component placement problems
- Routing constraints not met

**Example**:
```python
result = validator.validate_board(board)
if not result.success:
    for issue in result.get_issues():
        print(f"Validation issue: {issue.message}")
        if issue.suggestion:
            print(f"Suggestion: {issue.suggestion}")
```

**Resolution**:
- Review validation error messages
- Check design rules and constraints
- Fix component placement or routing
- Use the validation guide for specific issues

### 4. Component Errors

**Description**: Problems with component placement, routing, or library issues.

**Common Causes**:
- Missing component footprints
- Invalid component parameters
- Library path issues
- Component placement conflicts

**Example**:
```python
try:
    component = board.FindFootprintByReference("R1")
    if not component:
        raise ValueError("Component R1 not found")
except ValueError as e:
    print(f"Component error: {e}")
    # Check component library and placement
```

**Resolution**:
- Verify component libraries are loaded
- Check component footprints exist
- Review component placement
- Update component libraries

### 5. System Errors

**Description**: Unexpected issues requiring investigation.

**Common Causes**:
- Memory issues
- KiCad API problems
- System resource limitations
- Unexpected state

**Example**:
```python
try:
    result = complex_operation()
except Exception as e:
    print(f"System error: {e}")
    # Enable debug logging for investigation
```

**Resolution**:
- Enable debug logging
- Check system resources
- Restart the application
- Review system logs

## Error Message Structure

All error messages follow a consistent structure:

### Standard Error Format

```
[ERROR_TYPE] Operation: [OPERATION_NAME]
Issue: [DETAILED_DESCRIPTION]
Context: [ADDITIONAL_CONTEXT]
Suggestion: [ACTIONABLE_STEPS]
Documentation: [REFERENCE_LINK]
```

### Example Error Message

```
[CONFIGURATION_ERROR] Operation: PCB Generation
Issue: Invalid board size specified (width: -10mm, height: 50mm)
Context: Board size must be positive values
Suggestion: Set width to a positive value (e.g., 100mm)
Documentation: docs/reference/board_config.md#board-size
```

## Debugging Techniques

### 1. Enable Debug Logging

Set the log level to DEBUG for detailed information:

```bash
export KICAD_PCB_GENERATOR_LOG_LEVEL=DEBUG
python -m kicad_pcb_generator your_command
```

### 2. Use Error Context

All errors include context information to help with debugging:

```python
try:
    result = operation()
except Exception as e:
    print(f"Error context: {getattr(e, 'context', 'No context available')}")
    print(f"Error details: {e}")
```

### 3. Check Validation Results

Validation results include detailed information about issues:

```python
result = validator.validate_board(board)
if not result.is_valid:
    print(f"Validation failed with {len(result.issues)} issues:")
    for issue in result.issues:
        print(f"  - {issue.severity}: {issue.message}")
        if issue.suggestion:
            print(f"    Suggestion: {issue.suggestion}")
```

### 4. Use Error Categories

Filter errors by category for targeted debugging:

```python
# Get only critical errors
critical_issues = result.get_issues(severity=ValidationSeverity.CRITICAL)

# Get only configuration errors
config_issues = [issue for issue in result.issues 
                 if issue.category == ValidationCategory.CONFIGURATION]
```

## Common Error Patterns

### 1. Configuration File Issues

**Pattern**: `ValueError: Invalid configuration value`

**Resolution**:
```python
# Validate configuration before use
config_validator = ConfigurationValidator()
validation_result = config_validator.validate(config)
if not validation_result.success:
    for error in validation_result.errors:
        print(f"Config error: {error}")
```

### 2. File Path Issues

**Pattern**: `FileNotFoundError: No such file or directory`

**Resolution**:
```python
import os
from pathlib import Path

# Use Path for robust path handling
file_path = Path("project/schematic.kicad_sch")
if not file_path.exists():
    print(f"File not found: {file_path}")
    print(f"Current directory: {Path.cwd()}")
    print(f"Available files: {list(Path.cwd().glob('*.kicad_sch'))}")
```

### 3. Component Library Issues

**Pattern**: `KeyError: Component library not found`

**Resolution**:
```python
# Check available libraries
available_libraries = board.GetFootprintLibraries()
print(f"Available libraries: {available_libraries}")

# Check specific library
if "Audio_Components" not in available_libraries:
    print("Audio_Components library not loaded")
    # Load the library
    board.AddFootprintLibrary("Audio_Components")
```

### 4. Validation Rule Issues

**Pattern**: `ValidationError: Rule violation detected`

**Resolution**:
```python
# Get detailed rule information
rule_info = validator.get_rule_info()
for rule_name, rule_details in rule_info.items():
    print(f"Rule: {rule_name}")
    print(f"  Description: {rule_details['description']}")
    print(f"  Parameters: {rule_details['parameters']}")

# Check specific rule
if validator.is_rule_enabled("check_audio_components"):
    print("Audio component validation is enabled")
```

## Best Practices

### 1. Always Check Return Values

```python
result = operation()
if not result.success:
    for error in result.errors:
        print(f"Error: {error}")
    return
```

### 2. Use Specific Exception Types

```python
try:
    result = operation()
except (ValueError, KeyError) as e:
    # Handle configuration errors
    print(f"Configuration error: {e}")
except (FileNotFoundError, PermissionError) as e:
    # Handle file access errors
    print(f"File access error: {e}")
except Exception as e:
    # Handle unexpected errors
    print(f"Unexpected error: {e}")
    # Enable debug logging for investigation
```

### 3. Provide Context in Error Messages

```python
def operation_with_context():
    try:
        result = complex_operation()
    except Exception as e:
        # Add context to the error
        raise RuntimeError(f"Failed during {operation_name}: {e}") from e
```

### 4. Use Validation Results Effectively

```python
def handle_validation_results(result):
    if result.is_valid:
        print("✓ Validation passed")
        return True
    
    print("✗ Validation failed")
    
    # Group issues by severity
    for severity in ValidationSeverity:
        issues = result.get_issues(severity=severity)
        if issues:
            print(f"\n{severity.value.upper()} Issues:")
            for issue in issues:
                print(f"  - {issue.message}")
                if issue.suggestion:
                    print(f"    Fix: {issue.suggestion}")
    
    return False
```

## Getting Help

### 1. Check Error Documentation

Each error type includes documentation references:
- Configuration errors: See configuration guides
- File errors: See file management guides
- Validation errors: See validation guides
- Component errors: See component guides

### 2. Use Debug Tools

- Enable debug logging for detailed information
- Use the requirements checker for system issues
- Review validation reports for design issues
- Check component libraries for missing parts

### 3. Community Support

- Check the [FAQ](../user/faq.md) for common issues
- Search the [documentation](../README.md) for solutions
- Join our community for additional help
- Open an issue with detailed error information

## Error Handling Checklist

When encountering errors:

- [ ] **Identify the error type** (configuration, file, validation, component, system)
- [ ] **Read the complete error message** including context and suggestions
- [ ] **Check the documentation reference** for detailed information
- [ ] **Enable debug logging** if needed for more details
- [ ] **Follow the suggested resolution steps**
- [ ] **Verify the fix** by re-running the operation
- [ ] **Report persistent issues** with complete error information

## Example: Complete Error Handling

```python
from kicad_pcb_generator.core.pcb import PCBGenerator
from kicad_pcb_generator.audio.validation import AudioPCBValidator
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

def generate_audio_pcb(project_name: str, config: dict):
    """Generate an audio PCB with comprehensive error handling."""
    
    try:
        # Create generator
        generator = PCBGenerator()
        
        # Generate PCB
        result = generator.generate_pcb(project_name, config=config)
        
        if not result.success:
            print("PCB generation failed:")
            for error in result.errors:
                print(f"  - {error}")
            return False
        
        # Validate the generated PCB
        validator = AudioPCBValidator()
        validation_result = validator.validate_board(result.board)
        
        if not validation_result.is_valid:
            print("Validation issues found:")
            for issue in validation_result.get_issues():
                print(f"  - {issue.severity}: {issue.message}")
                if issue.suggestion:
                    print(f"    Suggestion: {issue.suggestion}")
            return False
        
        print("✓ PCB generated and validated successfully")
        return True
        
    except (ValueError, KeyError) as e:
        print(f"Configuration error: {e}")
        print("Check your project configuration and parameters")
        return False
        
    except (FileNotFoundError, PermissionError) as e:
        print(f"File access error: {e}")
        print("Check file paths and permissions")
        return False
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        print("Enable debug logging for detailed investigation")
        logging.getLogger().setLevel(logging.DEBUG)
        return False
```

This comprehensive error handling approach ensures that users can quickly identify and resolve issues with clear, actionable guidance. 