#!/usr/bin/env python3
"""
KiCad PCB Generator Installation Script
This script helps users install the KiCad PCB Generator and its dependencies.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress

console = Console()

def check_python():
    """Check if Python version meets requirements."""
    required_version = (3, 8)
    current_version = sys.version_info[:2]
    
    if current_version < required_version:
        console.print(f"[red]Error: Python {required_version[0]}.{required_version[1]} or later is required.[/red]")
        console.print("Please download and install Python from https://www.python.org/downloads/")
        return False
    return True

def check_pip():
    """Check if pip is installed and up to date."""
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], check=True, capture_output=True)
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        return True
    except subprocess.CalledProcessError:
        console.print("[red]Error: pip is not installed or not working properly.[/red]")
        return False

def install_requirements():
    """Install required Python packages."""
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        return True
    except subprocess.CalledProcessError:
        console.print("[red]Error: Failed to install required packages.[/red]")
        return False

def check_kicad():
    """Check if KiCad is installed."""
    if platform.system() == "Windows":
        possible_paths = [
            r"C:\Program Files\KiCad\7.0",
            r"C:\Program Files\KiCad\6.0",
            r"C:\Program Files\KiCad\5.1"
        ]
    elif platform.system() == "Darwin":  # macOS
        possible_paths = [
            "/Applications/KiCad/KiCad.app",
            "/Applications/KiCad.app"
        ]
    else:  # Linux
        possible_paths = [
            "/usr/bin/kicad",
            "/usr/local/bin/kicad"
        ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return True
    
    console.print("[yellow]Warning: KiCad not found in common installation paths.[/yellow]")
    console.print("Please make sure KiCad is installed and in your system PATH.")
    console.print("Download KiCad from https://www.kicad.org/download/")
    return False

def main():
    """Main installation function."""
    console.print(Panel.fit(
        "[bold blue]KiCad PCB Generator Installation[/bold blue]\n"
        "This script will help you install the KiCad PCB Generator and its dependencies.",
        title="Welcome"
    ))
    
    with Progress() as progress:
        task = progress.add_task("[cyan]Installing...", total=4)
        
        # Check Python version
        if not check_python():
            return
        progress.update(task, advance=1)
        
        # Check pip
        if not check_pip():
            return
        progress.update(task, advance=1)
        
        # Check KiCad
        if not check_kicad():
            console.print("[yellow]Continuing installation, but KiCad must be installed before using the tool.[/yellow]")
        progress.update(task, advance=1)
        
        # Install requirements
        if not install_requirements():
            return
        progress.update(task, advance=1)
    
    # Install the package
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], check=True)
    except subprocess.CalledProcessError:
        console.print("[red]Error: Failed to install KiCad PCB Generator.[/red]")
        return
    
    console.print("\n[bold green]✓ Installation completed successfully![/bold green]")
    console.print("\n[bold]Next steps:[/bold]")
    console.print("1. Run the requirements checker: python scripts/check_requirements.py")
    console.print("2. Read the Quick Start Guide: docs/guides/quick_start.md")
    console.print("3. Try an example project: kicad-pcb-generator example audio-amplifier")
    
    console.print("\n[bold]Getting help:[/bold]")
    console.print("- Documentation: docs/README.md")
    console.print("- Discord community: https://discord.gg/kicad-pcb-generator")
    console.print("- GitHub issues: https://github.com/kicad-pcb-generator/kicad-pcb-generator/issues")

if __name__ == "__main__":
    main() 