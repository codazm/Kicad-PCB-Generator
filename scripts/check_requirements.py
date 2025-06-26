#!/usr/bin/env python3
"""
System Requirements Checker for KiCad PCB Generator
This script checks if your system meets the requirements to run the KiCad PCB Generator.
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path
import psutil
import rich
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress

console = Console()

def check_python_version():
    """Check if Python version meets requirements."""
    required_version = (3, 8)
    current_version = sys.version_info[:2]
    
    return {
        "name": "Python Version",
        "required": f">= {required_version[0]}.{required_version[1]}",
        "current": f"{current_version[0]}.{current_version[1]}",
        "status": current_version >= required_version
    }

def check_kicad():
    """Check KiCad installation."""
    kicad_path = None
    version = None
    
    # Check if KiCad is in PATH
    try:
        if platform.system() == "Windows":
            version_cmd = ["kicad", "--version"]
        else:
            version_cmd = ["kicad", "--version"]
        
        result = subprocess.run(version_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError, OSError) as e:
        # KiCad not found or failed to run
        pass
    
    return {
        "name": "KiCad Installation",
        "required": "Installed and in PATH",
        "current": f"Found at {kicad_path}" if kicad_path else "Not found",
        "version": version if version else "Unknown",
        "status": kicad_path is not None
    }

def check_system_resources():
    """Check system resources (RAM, disk space)."""
    # Check RAM
    ram = psutil.virtual_memory()
    ram_gb = ram.total / (1024**3)
    ram_required = 4  # 4GB minimum
    
    # Check disk space
    disk = psutil.disk_usage('/')
    disk_gb = disk.free / (1024**3)
    disk_required = 1  # 1GB minimum
    
    return {
        "name": "System Resources",
        "ram": {
            "required": f"{ram_required}GB",
            "current": f"{ram_gb:.1f}GB",
            "status": ram_gb >= ram_required
        },
        "disk": {
            "required": f"{disk_required}GB",
            "current": f"{disk_gb:.1f}GB",
            "status": disk_gb >= disk_required
        }
    }

def check_display():
    """Check display resolution."""
    try:
        if platform.system() == "Windows":
            import ctypes
            user32 = ctypes.windll.user32
            width = user32.GetSystemMetrics(0)
            height = user32.GetSystemMetrics(1)
        elif platform.system() == "Darwin":  # macOS
            from AppKit import NSScreen
            screen = NSScreen.mainScreen()
            frame = screen.frame()
            width = int(frame.size.width)
            height = int(frame.size.height)
        else:  # Linux
            import Xlib.display
            display = Xlib.display.Display()
            screen = display.screen()
            width = screen.width_in_pixels
            height = screen.height_in_pixels
    except (ImportError, OSError, AttributeError) as e:
        # Display detection failed, use default values
        width, height = 0, 0
    
    min_width = 1280
    min_height = 720
    
    return {
        "name": "Display Resolution",
        "required": f"{min_width}x{min_height}",
        "current": f"{width}x{height}",
        "status": width >= min_width and height >= min_height
    }

def check_python_packages():
    """Check required Python packages."""
    required_packages = {
        "numpy": "1.24.0",
        "scipy": "1.10.0",
        "pandas": "2.0.0",
        "pyyaml": "6.0",
        "jsonschema": "4.17.0",
        "python-dotenv": "1.0.0",
        "click": "8.1.0",
        "rich": "13.0.0",
        "pydantic": "2.0.0",
        "typer": "0.9.0"
    }
    
    results = []
    for package, required_version in required_packages.items():
        try:
            import importlib
            module = importlib.import_module(package)
            current_version = getattr(module, "__version__", "unknown")
            results.append({
                "name": package,
                "required": f">= {required_version}",
                "current": current_version,
                "status": current_version != "unknown"  # We'll assume it's installed if we can import it
            })
        except ImportError:
            results.append({
                "name": package,
                "required": f">= {required_version}",
                "current": "Not installed",
                "status": False
            })
    
    return results

def main():
    """Main function to run all checks."""
    console.print(Panel.fit(
        "[bold blue]KiCad PCB Generator System Requirements Checker[/bold blue]\n"
        "This script will check if your system meets the requirements to run the KiCad PCB Generator.",
        title="Welcome"
    ))
    
    with Progress() as progress:
        task = progress.add_task("[cyan]Checking system requirements...", total=4)
        
        # Check Python version
        python_check = check_python_version()
        progress.update(task, advance=1)
        
        # Check KiCad
        kicad_check = check_kicad()
        progress.update(task, advance=1)
        
        # Check system resources
        resources_check = check_system_resources()
        progress.update(task, advance=1)
        
        # Check display
        display_check = check_display()
        progress.update(task, advance=1)
        
        # Check Python packages
        package_checks = check_python_packages()
    
    # Display results
    console.print("\n[bold]System Requirements Check Results:[/bold]\n")
    
    # Basic requirements table
    basic_table = Table(show_header=True, header_style="bold magenta")
    basic_table.add_column("Requirement")
    basic_table.add_column("Required")
    basic_table.add_column("Current")
    basic_table.add_column("Status")
    
    basic_table.add_row(
        python_check["name"],
        python_check["required"],
        python_check["current"],
        "[green]✓[/green]" if python_check["status"] else "[red]✗[/red]"
    )
    
    basic_table.add_row(
        kicad_check["name"],
        kicad_check["required"],
        f"{kicad_check['current']} (Version: {kicad_check['version']})",
        "[green]✓[/green]" if kicad_check["status"] else "[red]✗[/red]"
    )
    
    basic_table.add_row(
        "RAM",
        resources_check["ram"]["required"],
        resources_check["ram"]["current"],
        "[green]✓[/green]" if resources_check["ram"]["status"] else "[red]✗[/red]"
    )
    
    basic_table.add_row(
        "Disk Space",
        resources_check["disk"]["required"],
        resources_check["disk"]["current"],
        "[green]✓[/green]" if resources_check["disk"]["status"] else "[red]✗[/red]"
    )
    
    basic_table.add_row(
        display_check["name"],
        display_check["required"],
        display_check["current"],
        "[green]✓[/green]" if display_check["status"] else "[red]✗[/red]"
    )
    
    console.print(basic_table)
    
    # Python packages table
    console.print("\n[bold]Required Python Packages:[/bold]\n")
    package_table = Table(show_header=True, header_style="bold magenta")
    package_table.add_column("Package")
    package_table.add_column("Required Version")
    package_table.add_column("Current Version")
    package_table.add_column("Status")
    
    for check in package_checks:
        package_table.add_row(
            check["name"],
            check["required"],
            check["current"],
            "[green]✓[/green]" if check["status"] else "[red]✗[/red]"
        )
    
    console.print(package_table)
    
    # Summary
    all_checks = [
        python_check["status"],
        kicad_check["status"],
        resources_check["ram"]["status"],
        resources_check["disk"]["status"],
        display_check["status"]
    ] + [check["status"] for check in package_checks]
    
    if all(all_checks):
        console.print("\n[bold green]✓ All requirements are met! You can run the KiCad PCB Generator.[/bold green]")
    else:
        console.print("\n[bold red]✗ Some requirements are not met. Please address the issues above before running the KiCad PCB Generator.[/bold red]")
        console.print("\n[bold]Next steps:[/bold]")
        console.print("1. Install or update Python if needed")
        console.print("2. Install KiCad if not found")
        console.print("3. Install missing Python packages using: pip install -r requirements.txt")
        console.print("4. Ensure you have enough system resources")
        console.print("\nFor more help, see the installation guide: docs/user/installation.md")

if __name__ == "__main__":
    main() 
