"""
Pytest configuration and common fixtures.
"""
import os
import sys
from pathlib import Path
from typing import Generator

import pytest
import coverage
from datetime import datetime

# Add src directory to Python path
src_path = str(Path(__file__).parent.parent / "src")
sys.path.insert(0, src_path)

# Initialize coverage
cov = coverage.Coverage(
    branch=True,
    source=['kicad_pcb_generator'],
    omit=[
        '*/tests/*',
        '*/__init__.py',
        '*/migrations/*',
        '*/venv/*',
        '*/env/*',
        '*/site-packages/*'
    ]
)

@pytest.fixture
def test_data_dir() -> Path:
    """Get the test data directory.
    
    Returns:
        Path to test data directory
    """
    return Path(__file__).parent / "data"

@pytest.fixture
def temp_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary directory for testing.
    
    Args:
        tmp_path: Pytest temporary directory
        
    Yields:
        Path to temporary directory
    """
    # Create test directory structure
    (tmp_path / "components").mkdir()
    (tmp_path / "templates").mkdir()
    (tmp_path / "libraries").mkdir()
    
    yield tmp_path
    
    # Cleanup
    for item in tmp_path.iterdir():
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            for subitem in item.iterdir():
                if subitem.is_file():
                    subitem.unlink()
            item.rmdir()

@pytest.fixture
def mock_kicad_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock KiCad environment variables.
    
    Args:
        monkeypatch: Pytest monkeypatch fixture
    """
    # Mock KiCad environment variables
    monkeypatch.setenv("KICAD_DATA", "/usr/share/kicad")
    monkeypatch.setenv("KICAD_TEMPLATE_DIR", "/usr/share/kicad/template")
    monkeypatch.setenv("KICAD_USER_TEMPLATE_DIR", str(Path.home() / "kicad" / "template"))
    
    # Mock KiCad version
    monkeypatch.setattr("pcbnew.Version", lambda: "9.0.0")

@pytest.fixture
def mock_logger(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock logger configuration.
    
    Args:
        monkeypatch: Pytest monkeypatch fixture
    """
    import logging
    
    # Create test logger
    logger = logging.getLogger("test")
    logger.setLevel(logging.DEBUG)
    
    # Create console handler
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    # Mock logger
    monkeypatch.setattr("logging.getLogger", lambda name: logger)

@pytest.fixture(autouse=True)
def coverage_setup():
    """Setup coverage before each test."""
    cov.start()
    yield
    cov.stop()
    cov.save()

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Generate coverage report after tests complete."""
    if exitstatus == 0:  # Only generate report if tests passed
        # Create coverage directory if it doesn't exist
        coverage_dir = os.path.join(os.path.dirname(__file__), 'coverage')
        os.makedirs(coverage_dir, exist_ok=True)
        
        # Generate HTML report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        html_report_path = os.path.join(coverage_dir, f'coverage_report_{timestamp}')
        cov.html_report(directory=html_report_path)
        
        # Generate XML report for CI integration
        xml_report_path = os.path.join(coverage_dir, 'coverage.xml')
        cov.xml_report(outfile=xml_report_path)
        
        # Print coverage summary
        terminalreporter.write_sep('=', 'Coverage Report')
        terminalreporter.write(f'HTML report generated at: {html_report_path}\n')
        terminalreporter.write(f'XML report generated at: {xml_report_path}\n')
        
        # Print coverage statistics
        total_lines = cov.total()
        covered_lines = cov.covered()
        coverage_percentage = (covered_lines / total_lines * 100) if total_lines > 0 else 0
        
        terminalreporter.write(f'Total lines: {total_lines}\n')
        terminalreporter.write(f'Covered lines: {covered_lines}\n')
        terminalreporter.write(f'Coverage: {coverage_percentage:.2f}%\n')
        
        # Print missing lines for critical modules
        critical_modules = [
            'kicad_pcb_generator.audio.pcb.formats.kosmo_validation',
            'kicad_pcb_generator.ui.widgets.format_preview'
        ]
        
        for module in critical_modules:
            if module in cov.measured_files():
                missing = cov.get_missing(module)
                if missing:
                    terminalreporter.write(f'\nMissing lines in {module}:\n')
                    for line in missing:
                        terminalreporter.write(f'  Line {line}\n') 