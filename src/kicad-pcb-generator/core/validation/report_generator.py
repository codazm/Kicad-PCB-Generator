"""Validation report generator for the KiCad PCB Generator."""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json
import csv
import os
from enum import Enum
from ..validation.validation_results import (
    ValidationResult,
    ValidationCategory,
    ValidationSeverity,
    AudioValidationResult,
    SafetyValidationResult,
    ManufacturingValidationResult
)
from ...utils.logging.logger import Logger

class ReportFormat(str, Enum):
    """Report format options."""
    JSON = "json"
    CSV = "csv"
    HTML = "html"
    MARKDOWN = "markdown"

@dataclass
class ValidationSummary:
    """Summary of validation results."""
    total_issues: int
    critical_issues: int
    errors: int
    warnings: int
    info: int
    categories: Dict[str, int]
    timestamp: datetime

class ValidationReportGenerator:
    """Generator for validation reports."""
    
    def __init__(self, logger: Optional[Logger] = None):
        """Initialize the report generator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or Logger(__name__)
    
    def generate_report(self, results: List[ValidationResult], format: ReportFormat = ReportFormat.JSON) -> str:
        """Generate a validation report.
        
        Args:
            results: List of validation results
            format: Report format
            
        Returns:
            Report content as string
        """
        try:
            # Generate summary
            summary = self._generate_summary(results)
            
            # Generate report based on format
            if format == ReportFormat.JSON:
                return self._generate_json_report(results, summary)
            elif format == ReportFormat.CSV:
                return self._generate_csv_report(results, summary)
            elif format == ReportFormat.HTML:
                return self._generate_html_report(results, summary)
            elif format == ReportFormat.MARKDOWN:
                return self._generate_markdown_report(results, summary)
            else:
                raise ValueError(f"Unsupported report format: {format}")
                
        except (ValueError, TypeError, AttributeError) as e:
            self.logger.error(f"Data processing error generating report: {str(e)}")
            raise
        except (json.JSONEncodeError, OSError) as e:
            self.logger.error(f"I/O error generating report: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error generating report: {str(e)}")
            raise
    
    def _generate_summary(self, results: List[ValidationResult]) -> ValidationSummary:
        """Generate a summary of validation results.
        
        Args:
            results: List of validation results
            
        Returns:
            ValidationSummary instance
        """
        summary = ValidationSummary(
            total_issues=len(results),
            critical_issues=0,
            errors=0,
            warnings=0,
            info=0,
            categories={},
            timestamp=datetime.now()
        )
        
        for result in results:
            # Count by severity
            if result.severity == ValidationSeverity.CRITICAL:
                summary.critical_issues += 1
            elif result.severity == ValidationSeverity.ERROR:
                summary.errors += 1
            elif result.severity == ValidationSeverity.WARNING:
                summary.warnings += 1
            elif result.severity == ValidationSeverity.INFO:
                summary.info += 1
            
            # Count by category
            category = result.category.value
            summary.categories[category] = summary.categories.get(category, 0) + 1
        
        return summary
    
    def _generate_json_report(self, results: List[ValidationResult], summary: ValidationSummary) -> str:
        """Generate a JSON report.
        
        Args:
            results: List of validation results
            summary: Validation summary
            
        Returns:
            JSON report as string
        """
        report = {
            "summary": {
                "total_issues": summary.total_issues,
                "critical_issues": summary.critical_issues,
                "errors": summary.errors,
                "warnings": summary.warnings,
                "info": summary.info,
                "categories": summary.categories,
                "timestamp": summary.timestamp.isoformat()
            },
            "results": [result.to_dict() for result in results]
        }
        
        return json.dumps(report, indent=2)
    
    def _generate_csv_report(self, results: List[ValidationResult], summary: ValidationSummary) -> str:
        """Generate a CSV report.
        
        Args:
            results: List of validation results
            summary: Validation summary
            
        Returns:
            CSV report as string
        """
        output = []
        
        # Add summary
        output.append(["Summary"])
        output.append(["Total Issues", summary.total_issues])
        output.append(["Critical Issues", summary.critical_issues])
        output.append(["Errors", summary.errors])
        output.append(["Warnings", summary.warnings])
        output.append(["Info", summary.info])
        output.append([])
        
        # Add category counts
        output.append(["Category Counts"])
        for category, count in summary.categories.items():
            output.append([category, count])
        output.append([])
        
        # Add results
        output.append(["Category", "Severity", "Message", "Location", "Details"])
        for result in results:
            output.append([
                result.category.value,
                result.severity.value,
                result.message,
                str(result.location) if result.location else "",
                json.dumps(result.details) if result.details else ""
            ])
        
        # Convert to CSV
        with open("temp_report.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(output)
        
        with open("temp_report.csv", "r") as f:
            content = f.read()
        
        os.remove("temp_report.csv")
        return content
    
    def _generate_html_report(self, results: List[ValidationResult], summary: ValidationSummary) -> str:
        """Generate an HTML report.
        
        Args:
            results: List of validation results
            summary: Validation summary
            
        Returns:
            HTML report as string
        """
        html = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 20px; }",
            ".summary { background-color: #f5f5f5; padding: 20px; border-radius: 5px; }",
            ".results { margin-top: 20px; }",
            ".result { margin: 10px 0; padding: 10px; border-left: 5px solid; }",
            ".critical { border-color: #ff0000; }",
            ".error { border-color: #ff4444; }",
            ".warning { border-color: #ffaa00; }",
            ".info { border-color: #00aa00; }",
            "</style>",
            "</head>",
            "<body>",
            "<h1>Validation Report</h1>",
            "<div class='summary'>",
            f"<h2>Summary</h2>",
            f"<p>Total Issues: {summary.total_issues}</p>",
            f"<p>Critical Issues: {summary.critical_issues}</p>",
            f"<p>Errors: {summary.errors}</p>",
            f"<p>Warnings: {summary.warnings}</p>",
            f"<p>Info: {summary.info}</p>",
            "<h3>Category Counts</h3>",
            "<ul>"
        ]
        
        for category, count in summary.categories.items():
            html.append(f"<li>{category}: {count}</li>")
        
        html.extend([
            "</ul>",
            f"<p>Generated: {summary.timestamp.isoformat()}</p>",
            "</div>",
            "<div class='results'>",
            "<h2>Results</h2>"
        ])
        
        for result in results:
            severity_class = result.severity.value.lower()
            html.extend([
                f"<div class='result {severity_class}'>",
                f"<h3>{result.category.value} - {result.severity.value}</h3>",
                f"<p>{result.message}</p>"
            ])
            
            if result.location:
                html.append(f"<p>Location: {result.location}</p>")
            
            if result.details:
                html.append(f"<p>Details: {json.dumps(result.details, indent=2)}</p>")
            
            html.append("</div>")
        
        html.extend([
            "</div>",
            "</body>",
            "</html>"
        ])
        
        return "\n".join(html)
    
    def _generate_markdown_report(self, results: List[ValidationResult], summary: ValidationSummary) -> str:
        """Generate a Markdown report.
        
        Args:
            results: List of validation results
            summary: Validation summary
            
        Returns:
            Markdown report as string
        """
        md = [
            "# Validation Report",
            "",
            "## Summary",
            f"- Total Issues: {summary.total_issues}",
            f"- Critical Issues: {summary.critical_issues}",
            f"- Errors: {summary.errors}",
            f"- Warnings: {summary.warnings}",
            f"- Info: {summary.info}",
            "",
            "### Category Counts",
        ]
        
        for category, count in summary.categories.items():
            md.append(f"- {category}: {count}")
        
        md.extend([
            "",
            f"Generated: {summary.timestamp.isoformat()}",
            "",
            "## Results",
            ""
        ])
        
        for result in results:
            md.extend([
                f"### {result.category.value} - {result.severity.value}",
                f"{result.message}",
                ""
            ])
            
            if result.location:
                md.append(f"Location: {result.location}")
            
            if result.details:
                md.append(f"Details: {json.dumps(result.details, indent=2)}")
            
            md.append("")
        
        return "\n".join(md) 