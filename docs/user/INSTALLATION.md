# Installation Guide

This guide will help you install the KiCad PCB Generator on your system.

## Prerequisites

Before installing the KiCad PCB Generator, you need to have:

1. **Python 3.8 or later** installed on your system
   - Download from [python.org](https://www.python.org/downloads/)
   - Make sure to check "Add Python to PATH" during installation

2. **KiCad 9.0 or later** installed on your system
   - Download from [kicad.org](https://www.kicad.org/download/)
   - Follow the installation instructions for your operating system

## System Requirements Check

Before proceeding with the installation, you can check if your system meets all requirements by running:

```bash
python scripts/check_requirements.py
```

This will check:
- Python version
- KiCad installation
- Available RAM (4GB minimum)
- Free disk space (1GB minimum)
- Display resolution (1280x720 minimum)
- Required Python packages

The requirements checker provides detailed feedback and suggestions for any issues found.

## Installation Steps

### 1. Install KiCad PCB Generator

#### Using pip (Recommended)
```bash
pip install kicad-pcb-generator
```

#### From Source
```bash
git clone https://github.com/kicad-pcb-generator/kicad-pcb-generator.git
cd kicad-pcb-generator
pip install -e .
```

### 2. Install GUI (Optional)
If you want to use the graphical interface:
```bash
pip install kicad-pcb-generator[gui]
```

### 3. Verify Installation
Open a terminal/command prompt and run:
```bash
kicad-pcb-generator --version
```

### 4. Run System Check
After installation, verify everything is working:
```bash
python scripts/check_requirements.py
```

## Enhanced Error Handling

The KiCad PCB Generator now features comprehensive error handling and logging:

### Error Reporting
- **Specific Error Types**: All errors are categorized with specific exception types
- **Detailed Messages**: Error messages include context and actionable suggestions
- **Comprehensive Logging**: All operations are logged with appropriate levels
- **Debug Information**: Enhanced debugging capabilities for troubleshooting

### Example Error Handling
```python
try:
    result = generator.generate_pcb("my_project")
    if not result.success:
        for error in result.errors:
            print(f"Error: {error}")
            # Each error includes context and suggestions
except (ValueError, KeyError) as e:
    print(f"Configuration error: {e}")
    # Specific error types for better debugging
except Exception as e:
    print(f"Unexpected error: {e}")
    # Fallback for unexpected issues
```

## Troubleshooting

### Common Issues

1. **KiCad not found**
   - Make sure KiCad is installed and in your system PATH
   - On Windows, try restarting your computer after installing KiCad
   - On macOS, make sure KiCad is in your Applications folder
   - Run `python scripts/check_requirements.py` for detailed diagnostics

2. **Python dependencies fail to install**
   - Make sure you have the latest pip: `pip install --upgrade pip`
   - On Windows, you might need Visual C++ Build Tools
   - On Linux, you might need development packages: `sudo apt-get install python3-dev`
   - Check the detailed error messages for specific package issues

3. **GUI doesn't start**
   - Make sure you installed the GUI dependencies: `pip install kicad-pcb-generator[gui]`
   - Check if wxPython is installed: `pip install wxPython`
   - Run the requirements checker for GUI-specific issues

4. **Validation errors**
   - Check the detailed error messages for specific validation issues
   - Review the [Validation Guide](../api/validation.md) for validation requirements
   - Use the enhanced error reporting to identify and fix issues

### Getting Help

If you encounter any issues:
1. Run the requirements checker: `python scripts/check_requirements.py`
2. Check the [FAQ](faq.md) for common problems
3. Search the [documentation](search.html) for solutions
4. Review the enhanced error messages for specific guidance
5. Join our [Discord community](https://discord.gg/kicad-pcb-generator) for help
6. Open an [issue on GitHub](https://github.com/kicad-pcb-generator/kicad-pcb-generator/issues)

### Debug Mode

For advanced troubleshooting, you can enable debug logging:
```bash
export KICAD_PCB_GENERATOR_LOG_LEVEL=DEBUG
python -m kicad_pcb_generator your_command
```

## Next Steps

After installation:
1. Read the [Quick Start Guide](../guides/quick_start.md)
2. Try the [example projects](../examples/README.md)
3. Check out the [User Guide](user_guide.md) for detailed instructions
4. Review the [Error Handling Guide](../guides/error_handling.md) for debugging tips

## System Requirements

- **Operating System**: Windows 10/11, macOS 10.15+, or Linux
- **Python**: 3.8 or later
- **KiCad**: 9.0 or later
- **RAM**: 4GB minimum (8GB recommended)
- **Storage**: 1GB free space
- **Display**: 1280x720 minimum resolution

## What's New in v1.0.0

- ✅ **Robust Error Handling**: All error handlers now use specific exception types
- ✅ **Standardized Logging**: Comprehensive logging system across all modules
- ✅ **Enhanced Debugging**: Improved error messages with context and suggestions
- ✅ **Requirements Checker**: Automated system requirements validation
- ✅ **Code Quality**: Fixed duplicate functions, wildcard imports, and code organization 