import sys
import os
import json
import csv
import logging
import pcbnew
from kicad_pcb_generator.audio.validation.schematic.validator import EnhancedAudioSchematicValidator
from kicad_pcb_generator.audio.validation.ui.validation_result_display import EnhancedValidationResultDisplay

# Configure logging
logging.basicConfig(filename='validation.log', level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

def load_kicad_project(project_path):
    """Load KiCad schematic and board from the given project path."""
    try:
        board_file = os.path.join(project_path, os.path.basename(project_path) + '.kicad_pcb')
        sch_file = os.path.join(project_path, os.path.basename(project_path) + '.kicad_sch')
        board = pcbnew.LoadBoard(board_file)
        # For schematic, use a mock or KiCad's API if available
        schematic = None  # Replace with actual schematic loading if available
        return schematic, board
    except Exception as e:
        logging.error(f"Failed to load KiCad project: {e}")
        raise

def run_validation(schematic, board):
    """Run the full validation pipeline and return results."""
    try:
        validator = EnhancedAudioSchematicValidator()
        results = validator.validate_schematic(schematic, board)
        return results
    except Exception as e:
        logging.error(f"Validation failed: {e}")
        raise

def output_results(results, output_json='validation_results.json', output_csv='validation_results.csv'):
    """Output results to JSON and CSV files."""
    try:
        # JSON output
        with open(output_json, 'w') as f_json:
            json.dump([result.__dict__ for result in results], f_json, indent=2)
        # CSV output
        with open(output_csv, 'w', newline='') as f_csv:
            writer = csv.writer(f_csv)
            writer.writerow(['Severity', 'Message', 'Component', 'Net', 'Suggestion', 'Documentation', 'Example', 'Affected Components', 'Affected Nets', 'Details'])
            for result in results:
                writer.writerow([
                    result.severity.value,
                    result.message,
                    result.component_ref,
                    result.net_name,
                    result.suggestion,
                    result.documentation_ref,
                    result.example_solution,
                    ','.join(result.affected_components) if result.affected_components else '',
                    ','.join(result.affected_nets) if result.affected_nets else '',
                    result.detailed_message
                ])
    except Exception as e:
        logging.error(f"Failed to output results: {e}")
        raise

def main():
    if len(sys.argv) < 2:
        logging.error("Usage: python run_validation.py <KiCad_project_path>")
        sys.exit(1)
    project_path = sys.argv[1]
    schematic, board = load_kicad_project(project_path)
    results = run_validation(schematic, board)
    output_results(results)
    # Display results in the UI
    try:
        display = EnhancedValidationResultDisplay()
        display.display_results(results)
    except Exception as e:
        logging.error(f"Failed to display results in UI: {e}")
    logging.info(f"Validation complete. Results saved to validation_results.json and validation_results.csv.")

if __name__ == "__main__":
    main() 