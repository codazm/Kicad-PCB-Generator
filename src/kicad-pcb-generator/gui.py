"""Graphical user interface for audio PCB design tools."""
import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
import json
from pathlib import Path
import pcbnew
import webbrowser
from kicad_pcb_generator.audio.layout.converter import AudioLayoutConverter
from kicad_pcb_generator.audio.analysis.analyzer import AudioPCBAnalyzer
from kicad_pcb_generator.audio.components.stability import StabilityManager
from kicad_pcb_generator.audio.rules.design import AudioDesignRules
from kicad_pcb_generator.core.falstad_importer import FalstadImporter, FalstadImportError
from kicad_pcb_generator.core.validation.falstad_validator import ValidationError
from kicad_pcb_generator.core.project_manager import ProjectManager
from kicad_pcb_generator.core.templates.base import TemplateBase
from kicad_pcb_generator.core.templates.manager import TemplateManager

logger = logging.getLogger(__name__)

class ImportProgressWindow:
    """Progress window for import operations."""
    
    def __init__(self, parent):
        """Initialize progress window.
        
        Args:
            parent: Parent window
        """
        self.window = tk.Toplevel(parent)
        self.window.title("Import Progress")
        self.window.geometry("400x200")
        self.window.transient(parent)
        self.window.grab_set()
        
        # Progress bar
        self.progress = ttk.Progressbar(
            self.window,
            mode='determinate',
            length=300
        )
        self.progress.pack(pady=20)
        
        # Status label
        self.status = ttk.Label(self.window, text="")
        self.status.pack(pady=10)
        
        # Cancel button
        self.cancel_button = ttk.Button(
            self.window,
            text="Cancel",
            command=self.cancel
        )
        self.cancel_button.pack(pady=10)
        
        self.cancelled = False
        
    def update(self, value: int, status: str):
        """Update progress.
        
        Args:
            value: Progress value (0-100)
            status: Status message
        """
        self.progress['value'] = value
        self.status['text'] = status
        self.window.update()
        
    def cancel(self):
        """Cancel the operation."""
        self.cancelled = True
        self.window.destroy()

class ValidationResultsWindow:
    """Window for displaying validation results."""
    
    def __init__(self, parent, errors: list):
        """Initialize validation results window.
        
        Args:
            parent: Parent window
            errors: List of validation errors
        """
        self.window = tk.Toplevel(parent)
        self.window.title("Validation Results")
        self.window.geometry("600x400")
        self.window.transient(parent)
        
        # Create treeview
        self.tree = ttk.Treeview(
            self.window,
            columns=("Severity", "Message", "Location"),
            show="headings"
        )
        
        # Configure columns
        self.tree.heading("Severity", text="Severity")
        self.tree.heading("Message", text="Message")
        self.tree.heading("Location", text="Location")
        
        self.tree.column("Severity", width=100)
        self.tree.column("Message", width=300)
        self.tree.column("Location", width=150)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(
            self.window,
            orient="vertical",
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add errors
        for error in errors:
            self.tree.insert(
                "",
                "end",
                values=(
                    error.severity,
                    error.message,
                    error.location or "N/A"
                )
            )

class AudioPCBDesignerGUI:
    """GUI for audio PCB design tools."""
    
    def __init__(self, root):
        """Initialize the GUI.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("Audio PCB Designer")
        self.root.geometry("1000x700")
        
        # Initialize managers
        self.project_manager = ProjectManager()
        self.template_manager = TemplateManager()
        
        # Create main notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs
        self.create_project_tab()
        self.create_convert_tab()
        self.create_analyze_tab()
        self.create_create_tab()
        self.create_import_tab()
        self.create_express_workflow_tab()
        self.create_templates_tab()
        self.create_help_tab()
        self.create_settings_tab()
        
        # Create status bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=2)
        
        # Initialize variables
        self.schematic_path = tk.StringVar()
        self.pcb_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.rules_path = tk.StringVar()
        self.falstad_path = tk.StringVar()
        self.strict_mode = tk.BooleanVar(value=True)
        self.preview_enabled = tk.BooleanVar(value=True)
        self.auto_validate = tk.BooleanVar(value=True)
        self.current_project = None

    def create_project_tab(self):
        """Create the project management tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Projects")
        
        # Project list frame
        list_frame = ttk.LabelFrame(tab, text="Recent Projects")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Project listbox
        self.project_listbox = tk.Listbox(list_frame, height=10)
        self.project_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar for project list
        project_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.project_listbox.yview)
        project_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.project_listbox.configure(yscrollcommand=project_scrollbar.set)
        
        # Project buttons frame
        project_buttons = ttk.Frame(tab)
        project_buttons.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(project_buttons, text="Open Project", command=self.open_project).pack(side=tk.LEFT, padx=5)
        ttk.Button(project_buttons, text="New Project", command=self.new_project).pack(side=tk.LEFT, padx=5)
        ttk.Button(project_buttons, text="Refresh List", command=self.refresh_project_list).pack(side=tk.LEFT, padx=5)
        
        # Load initial project list
        self.refresh_project_list()

    def create_templates_tab(self):
        """Create the template management tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Templates")
        
        # Template list frame
        template_frame = ttk.LabelFrame(tab, text="Available Templates")
        template_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Template treeview
        columns = ("Name", "Type", "Description", "Version")
        self.template_tree = ttk.Treeview(template_frame, columns=columns, show="headings")
        
        # Configure columns
        for col in columns:
            self.template_tree.heading(col, text=col)
            self.template_tree.column(col, width=150)
        
        self.template_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar for template tree
        template_scrollbar = ttk.Scrollbar(template_frame, orient=tk.VERTICAL, command=self.template_tree.yview)
        template_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.template_tree.configure(yscrollcommand=template_scrollbar.set)
        
        # Template buttons frame
        template_buttons = ttk.Frame(tab)
        template_buttons.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(template_buttons, text="Use Template", command=self.use_template).pack(side=tk.LEFT, padx=5)
        ttk.Button(template_buttons, text="Edit Template", command=self.edit_template).pack(side=tk.LEFT, padx=5)
        ttk.Button(template_buttons, text="Delete Template", command=self.delete_template).pack(side=tk.LEFT, padx=5)
        ttk.Button(template_buttons, text="Import Template", command=self.import_template).pack(side=tk.LEFT, padx=5)
        ttk.Button(template_buttons, text="Export Template", command=self.export_template).pack(side=tk.LEFT, padx=5)
        ttk.Button(template_buttons, text="Refresh", command=self.refresh_template_list).pack(side=tk.LEFT, padx=5)
        
        # Load initial template list
        self.refresh_template_list()

    def create_help_tab(self):
        """Create the help and documentation tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Help")
        
        # Help buttons frame
        help_buttons = ttk.Frame(tab)
        help_buttons.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(help_buttons, text="User Guide", command=self.show_user_guide).pack(side=tk.LEFT, padx=5)
        ttk.Button(help_buttons, text="Video Tutorials", command=self.show_video_tutorials).pack(side=tk.LEFT, padx=5)
        ttk.Button(help_buttons, text="FAQ", command=self.show_faq).pack(side=tk.LEFT, padx=5)
        ttk.Button(help_buttons, text="Online Documentation", command=self.open_online_docs).pack(side=tk.LEFT, padx=5)
        
        # Help content frame
        help_content = ttk.LabelFrame(tab, text="Quick Help")
        help_content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Help text widget
        self.help_text = scrolledtext.ScrolledText(help_content, wrap=tk.WORD, height=20)
        self.help_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Load default help content
        self.load_default_help_content()

    def create_convert_tab(self):
        """Create the schematic to PCB conversion tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Convert")
        
        # Schematic file selection
        ttk.Label(tab, text="Schematic File:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(tab, textvariable=self.schematic_path, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(tab, text="Browse", command=self.browse_schematic).grid(row=0, column=2, padx=5, pady=5)
        
        # Output file selection
        ttk.Label(tab, text="Output PCB File:").grid(row=1, column=0, padx=5, pady=5)
        ttk.Entry(tab, textvariable=self.output_path, width=50).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(tab, text="Browse", command=self.browse_output).grid(row=1, column=2, padx=5, pady=5)
        
        # Design rules file selection
        ttk.Label(tab, text="Design Rules File:").grid(row=2, column=0, padx=5, pady=5)
        ttk.Entry(tab, textvariable=self.rules_path, width=50).grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(tab, text="Browse", command=self.browse_rules).grid(row=2, column=2, padx=5, pady=5)
        
        # Convert button
        ttk.Button(tab, text="Convert", command=self.convert_schematic).grid(row=3, column=1, pady=20)
        
    def create_analyze_tab(self):
        """Create the PCB analysis tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Analyze")
        
        # PCB file selection
        ttk.Label(tab, text="PCB File:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(tab, textvariable=self.pcb_path, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(tab, text="Browse", command=self.browse_pcb).grid(row=0, column=2, padx=5, pady=5)
        
        # Analysis options
        self.thermal_var = tk.BooleanVar(value=True)
        self.signal_var = tk.BooleanVar(value=True)
        self.emi_var = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(tab, text="Thermal Analysis", variable=self.thermal_var).grid(row=1, column=1, padx=5, pady=5)
        ttk.Checkbutton(tab, text="Signal Integrity Analysis", variable=self.signal_var).grid(row=2, column=1, padx=5, pady=5)
        ttk.Checkbutton(tab, text="EMI/EMC Analysis", variable=self.emi_var).grid(row=3, column=1, padx=5, pady=5)
        
        # Output file selection
        ttk.Label(tab, text="Output Results File:").grid(row=4, column=0, padx=5, pady=5)
        ttk.Entry(tab, textvariable=self.output_path, width=50).grid(row=4, column=1, padx=5, pady=5)
        ttk.Button(tab, text="Browse", command=self.browse_output).grid(row=4, column=2, padx=5, pady=5)
        
        # Analyze button
        ttk.Button(tab, text="Analyze", command=self.analyze_pcb).grid(row=5, column=1, pady=20)
        
    def create_create_tab(self):
        """Create the new design tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Create")
        
        # Design type selection
        ttk.Label(tab, text="Design Type:").grid(row=0, column=0, padx=5, pady=5)
        self.design_type = ttk.Combobox(tab, values=["Amplifier", "DAC", "Mixer"])
        self.design_type.grid(row=0, column=1, padx=5, pady=5)
        self.design_type.set("Amplifier")
        
        # Output directory selection
        ttk.Label(tab, text="Output Directory:").grid(row=1, column=0, padx=5, pady=5)
        ttk.Entry(tab, textvariable=self.output_path, width=50).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(tab, text="Browse", command=self.browse_output_dir).grid(row=1, column=2, padx=5, pady=5)
        
        # Design rules file selection
        ttk.Label(tab, text="Design Rules File:").grid(row=2, column=0, padx=5, pady=5)
        ttk.Entry(tab, textvariable=self.rules_path, width=50).grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(tab, text="Browse", command=self.browse_rules).grid(row=2, column=2, padx=5, pady=5)
        
        # Create button
        ttk.Button(tab, text="Create Design", command=self.create_design).grid(row=3, column=1, pady=20)
        
    def create_import_tab(self):
        """Create the Falstad import tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Import")
        
        # Create left frame for controls
        left_frame = ttk.Frame(tab)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Falstad file selection
        ttk.Label(left_frame, text="Falstad Schematic:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(left_frame, textvariable=self.falstad_path, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(left_frame, text="Browse", command=self.browse_falstad).grid(row=0, column=2, padx=5, pady=5)
        
        # Output directory selection
        ttk.Label(left_frame, text="Output Directory:").grid(row=1, column=0, padx=5, pady=5)
        ttk.Entry(left_frame, textvariable=self.output_path, width=50).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(left_frame, text="Browse", command=self.browse_output_dir).grid(row=1, column=2, padx=5, pady=5)
        
        # Options frame
        options_frame = ttk.LabelFrame(left_frame, text="Options")
        options_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        
        # Strict mode checkbox
        ttk.Checkbutton(
            options_frame,
            text="Strict Validation Mode",
            variable=self.strict_mode
        ).grid(row=0, column=0, padx=5, pady=5)
        
        # Preview checkbox
        ttk.Checkbutton(
            options_frame,
            text="Enable Preview",
            variable=self.preview_enabled
        ).grid(row=0, column=1, padx=5, pady=5)
        
        # Auto-validate checkbox
        ttk.Checkbutton(
            options_frame,
            text="Auto-validate on Load",
            variable=self.auto_validate
        ).grid(row=0, column=2, padx=5, pady=5)
        
        # Import button
        ttk.Button(
            left_frame,
            text="Import",
            command=self.import_falstad
        ).grid(row=3, column=1, pady=20)
        
        # Create right frame for preview
        right_frame = ttk.LabelFrame(tab, text="Preview")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Preview canvas
        self.preview_canvas = tk.Canvas(right_frame, bg='white')
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Preview controls
        preview_controls = ttk.Frame(right_frame)
        preview_controls.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            preview_controls,
            text="Zoom In",
            command=lambda: self.zoom_preview(1.2)
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            preview_controls,
            text="Zoom Out",
            command=lambda: self.zoom_preview(0.8)
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            preview_controls,
            text="Reset View",
            command=self.reset_preview
        ).pack(side=tk.LEFT, padx=5)
        
    def create_express_workflow_tab(self):
        """Create the express workflow tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Express Workflow")
        
        # Main frame
        main_frame = ttk.Frame(tab)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="Express PCB Generation", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Input section
        input_frame = ttk.LabelFrame(main_frame, text="Input")
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Falstad file selection
        falstad_frame = ttk.Frame(input_frame)
        falstad_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(falstad_frame, text="Falstad Schematic:").pack(side=tk.LEFT)
        self.express_falstad_path = tk.StringVar()
        ttk.Entry(falstad_frame, textvariable=self.express_falstad_path, width=50).pack(side=tk.LEFT, padx=5)
        ttk.Button(falstad_frame, text="Browse", command=self.browse_express_falstad).pack(side=tk.LEFT, padx=5)
        
        # Project name
        project_frame = ttk.Frame(input_frame)
        project_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(project_frame, text="Project Name:").pack(side=tk.LEFT)
        self.express_project_name = tk.StringVar(value="express_project")
        ttk.Entry(project_frame, textvariable=self.express_project_name, width=30).pack(side=tk.LEFT, padx=5)
        
        # Board preset selection
        preset_frame = ttk.Frame(input_frame)
        preset_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(preset_frame, text="Board Preset:").pack(side=tk.LEFT)
        self.express_board_preset = tk.StringVar()
        self.express_preset_combo = ttk.Combobox(preset_frame, textvariable=self.express_board_preset, width=30)
        self.express_preset_combo.pack(side=tk.LEFT, padx=5)
        
        # Load board presets
        from kicad_pcb_generator.core.templates.board_presets import board_preset_registry
        presets = board_preset_registry.list_presets()
        preset_names = [preset.name for preset in presets.values()]
        self.express_preset_combo['values'] = preset_names
        if preset_names:
            self.express_preset_combo.set(preset_names[0])  # Default to first preset
        
        # Options section
        options_frame = ttk.LabelFrame(main_frame, text="Options")
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Export options
        export_frame = ttk.Frame(options_frame)
        export_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(export_frame, text="Export Formats:").pack(side=tk.LEFT)
        self.express_export_gerber = tk.BooleanVar(value=True)
        self.express_export_bom = tk.BooleanVar(value=True)
        self.express_export_step = tk.BooleanVar(value=False)
        
        ttk.Checkbutton(export_frame, text="Gerber", variable=self.express_export_gerber).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(export_frame, text="BOM", variable=self.express_export_bom).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(export_frame, text="STEP", variable=self.express_export_step).pack(side=tk.LEFT, padx=5)
        
        # Generation options
        gen_frame = ttk.Frame(options_frame)
        gen_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(gen_frame, text="Generation:").pack(side=tk.LEFT)
        self.express_auto_route = tk.BooleanVar(value=True)
        self.express_optimize = tk.BooleanVar(value=True)
        self.express_validate = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(gen_frame, text="Auto-route", variable=self.express_auto_route).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(gen_frame, text="Optimize", variable=self.express_optimize).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(gen_frame, text="Validate", variable=self.express_validate).pack(side=tk.LEFT, padx=5)
        
        # Action buttons
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(action_frame, text="Generate PCB", command=self.run_express_workflow, 
                  style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Preview Settings", command=self.preview_express_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Clear", command=self.clear_express_form).pack(side=tk.LEFT, padx=5)
        
        # Status and progress
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=10)
        
        self.express_status_var = tk.StringVar(value="Ready")
        ttk.Label(status_frame, textvariable=self.express_status_var).pack(side=tk.LEFT)
        
        self.express_progress = ttk.Progressbar(status_frame, mode='indeterminate')
        self.express_progress.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        # Results frame
        results_frame = ttk.LabelFrame(main_frame, text="Results")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.express_results_text = scrolledtext.ScrolledText(results_frame, height=8)
        self.express_results_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def browse_schematic(self):
        """Browse for schematic file."""
        filename = filedialog.askopenfilename(
            title="Select Schematic File",
            filetypes=[("KiCad Schematic", "*.kicad_sch")]
        )
        if filename:
            self.schematic_path.set(filename)
            
    def browse_pcb(self):
        """Browse for PCB file."""
        filename = filedialog.askopenfilename(
            title="Select PCB File",
            filetypes=[("KiCad PCB", "*.kicad_pcb")]
        )
        if filename:
            self.pcb_path.set(filename)
            
    def browse_output(self):
        """Browse for output file."""
        filename = filedialog.asksaveasfilename(
            title="Select Output File",
            defaultextension=".json"
        )
        if filename:
            self.output_path.set(filename)
            
    def browse_output_dir(self):
        """Browse for output directory."""
        dirname = filedialog.askdirectory(title="Select Output Directory")
        if dirname:
            self.output_path.set(dirname)
            
    def browse_rules(self):
        """Browse for design rules file."""
        filename = filedialog.askopenfilename(
            title="Select Design Rules File",
            filetypes=[("JSON", "*.json")]
        )
        if filename:
            self.rules_path.set(filename)
            
    def browse_express_falstad(self):
        """Browse for Falstad schematic file."""
        filename = filedialog.askopenfilename(
            title="Select Falstad Schematic",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            self.express_falstad_path.set(filename)

    def run_express_workflow(self):
        """Run the express workflow."""
        try:
            # Validate inputs
            if not self.express_falstad_path.get():
                messagebox.showerror("Error", "Please select a Falstad file")
                return
            
            if not self.express_project_name.get():
                messagebox.showerror("Error", "Please enter a project name")
                return
            
            # Start progress
            self.express_progress.start()
            self.express_status_var.set("Running express workflow...")
            
            # Import Falstad file
            self.express_results_text.insert(tk.END, "📁 Importing Falstad file...\n")
            importer = FalstadImporter()
            
            with open(self.express_falstad_path.get(), 'r') as f:
                falstad_data = json.load(f)
            
            netlist = importer.to_netlist(falstad_data)
            self.express_results_text.insert(tk.END, "✅ Falstad file imported successfully\n")
            
            # Create project
            self.express_results_text.insert(tk.END, "📋 Creating project...\n")
            
            # Mock args for CLI compatibility
            class MockArgs:
                def __init__(self):
                    self.falstad = self.express_falstad_path.get()
                    self.project = self.express_project_name.get()
                    self.board_preset = self.express_board_preset.get()
                    self.export = []
                    if self.express_export_gerber.get():
                        self.export.append("gerber")
                    if self.express_export_bom.get():
                        self.export.append("bom")
                    if self.express_export_step.get():
                        self.export.append("step")
                    self.config = None
            
            # Run the workflow
            from kicad_pcb_generator.cli import falstad2pcb
            falstad2pcb(MockArgs())
            
            self.express_results_text.insert(tk.END, "✅ Express workflow completed successfully\n")
            self.express_status_var.set("Express workflow completed")
            
            # Show success message
            messagebox.showinfo("Success", f"PCB generated successfully!\nProject: {self.express_project_name.get()}")
            
        except (FileNotFoundError, PermissionError) as e:
            self.express_status_var.set("File access error")
            self.express_results_text.insert(tk.END, f"✗ File access error: {str(e)}\n")
            messagebox.showerror("Error", f"File access error:\n{str(e)}")
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            self.express_status_var.set("Configuration error")
            self.express_results_text.insert(tk.END, f"✗ Configuration error: {str(e)}\n")
            messagebox.showerror("Error", f"Configuration error:\n{str(e)}")
        except Exception as e:
            self.express_status_var.set("Unexpected error")
            self.express_results_text.insert(tk.END, f"✗ Unexpected error: {str(e)}\n")
            messagebox.showerror("Error", f"Unexpected error:\n{str(e)}")
        
        finally:
            self.express_progress.stop()

    def preview_express_settings(self):
        """Preview the express workflow settings."""
        settings = {
            "Falstad File": self.express_falstad_path.get() or "Not selected",
            "Project Name": self.express_project_name.get() or "Not specified",
            "Board Preset": self.express_board_preset.get() or "Not selected",
            "Export Formats": []
        }
        
        if self.express_export_gerber.get():
            settings["Export Formats"].append("Gerber")
        if self.express_export_bom.get():
            settings["Export Formats"].append("BOM")
        if self.express_export_step.get():
            settings["Export Formats"].append("STEP")
        
        if not settings["Export Formats"]:
            settings["Export Formats"] = ["None selected"]
        
        # Create preview window
        preview_window = tk.Toplevel(self.root)
        preview_window.title("Express Workflow Settings Preview")
        preview_window.geometry("400x300")
        preview_window.transient(self.root)
        
        # Display settings
        text_widget = scrolledtext.ScrolledText(preview_window)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for key, value in settings.items():
            if isinstance(value, list):
                text_widget.insert(tk.END, f"{key}: {', '.join(value)}\n")
            else:
                text_widget.insert(tk.END, f"{key}: {value}\n")
        
        text_widget.config(state=tk.DISABLED)

    def clear_express_form(self):
        """Clear the express workflow form."""
        self.express_falstad_path.set("")
        self.express_project_name.set("express_project")
        self.express_board_preset.set("")
        self.express_export_gerber.set(True)
        self.express_export_bom.set(True)
        self.express_export_step.set(False)
        self.express_auto_route.set(True)
        self.express_optimize.set(True)
        self.express_validate.set(True)
        self.express_status_var.set("Ready")
        self.express_results_text.delete(1.0, tk.END)

    def zoom_preview(self, factor: float):
        """Zoom the preview canvas.
        
        Args:
            factor: Zoom factor
        """
        self.preview_canvas.scale("all", 0, 0, factor, factor)
        
    def reset_preview(self):
        """Reset the preview canvas view."""
        self.preview_canvas.delete("all")
        self.preview_canvas.scale("all", 0, 0, 1, 1)
        
    def update_preview(self, data: dict):
        """Update the preview canvas with schematic data.
        
        Args:
            data: Falstad schematic data
        """
        if not self.preview_enabled.get():
            return
            
        self.preview_canvas.delete("all")
        
        # Draw components
        for element in data.get("elements", []):
            x = float(element.get("x", 0)) * 50  # Scale for preview
            y = float(element.get("y", 0)) * 50
            comp_type = element.get("type", "").lower()
            
            # Draw component symbol
            if comp_type == "resistor":
                self.draw_resistor(x, y)
            elif comp_type == "capacitor":
                self.draw_capacitor(x, y)
            elif comp_type == "ground":
                self.draw_ground(x, y)
            # Add more component types as needed
            
        # Draw wires
        for wire in data.get("wires", []):
            x1 = float(wire.get("x1", 0)) * 50
            y1 = float(wire.get("y1", 0)) * 50
            x2 = float(wire.get("x2", 0)) * 50
            y2 = float(wire.get("y2", 0)) * 50
            
            self.preview_canvas.create_line(x1, y1, x2, y2, fill="black", width=2)
            
    def draw_resistor(self, x: float, y: float):
        """Draw a resistor symbol.
        
        Args:
            x: X coordinate
            y: Y coordinate
        """
        size = 20
        self.preview_canvas.create_rectangle(
            x - size/2, y - size/4,
            x + size/2, y + size/4,
            fill="white", outline="black"
        )
        
    def draw_capacitor(self, x: float, y: float):
        """Draw a capacitor symbol.
        
        Args:
            x: X coordinate
            y: Y coordinate
        """
        size = 20
        self.preview_canvas.create_line(
            x - size/2, y,
            x - size/4, y,
            fill="black", width=2
        )
        self.preview_canvas.create_line(
            x + size/4, y,
            x + size/2, y,
            fill="black", width=2
        )
        self.preview_canvas.create_line(
            x - size/4, y - size/4,
            x - size/4, y + size/4,
            fill="black", width=2
        )
        self.preview_canvas.create_line(
            x + size/4, y - size/4,
            x + size/4, y + size/4,
            fill="black", width=2
        )
        
    def draw_ground(self, x: float, y: float):
        """Draw a ground symbol.
        
        Args:
            x: X coordinate
            y: Y coordinate
        """
        size = 20
        self.preview_canvas.create_line(
            x, y,
            x, y + size/2,
            fill="black", width=2
        )
        self.preview_canvas.create_line(
            x - size/2, y + size/2,
            x + size/2, y + size/2,
            fill="black", width=2
        )
        self.preview_canvas.create_line(
            x - size/3, y + size/2 + size/4,
            x + size/3, y + size/2 + size/4,
            fill="black", width=2
        )
        self.preview_canvas.create_line(
            x - size/6, y + size/2 + size/2,
            x + size/6, y + size/2 + size/2,
            fill="black", width=2
        )
        
    def convert_schematic(self):
        """Convert schematic to PCB."""
        try:
            # Load schematic
            schematic = pcbnew.LoadSchematic(self.schematic_path.get())
            
            # Load design rules
            rules = self.load_design_rules(self.rules_path.get())
            
            # Create converter
            converter = AudioLayoutConverter()
            
            # Convert schematic
            result = converter.convert_schematic(schematic)
            
            if not result.success:
                messagebox.showerror("Error", "Conversion failed:\n" + "\n".join(result.errors))
                return
            
            # Save converted PCB
            output_path = self.output_path.get()
            if output_path:
                result.board.Save(output_path)
                self.status_var.set(f"PCB saved to: {output_path}")
            else:
                self.status_var.set("Schematic converted successfully")
            
            # Show warnings if any
            if result.warnings:
                messagebox.showwarning("Warnings", "\n".join(result.warnings))
                
        except (FileNotFoundError, PermissionError) as e:
            messagebox.showerror("Error", f"File access error: {str(e)}")
        except (ValueError, KeyError) as e:
            messagebox.showerror("Error", f"Configuration error: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")
            
    def analyze_pcb(self):
        """Analyze PCB design."""
        try:
            # Load PCB
            board = pcbnew.LoadBoard(self.pcb_path.get())
            
            # Create stability manager
            stability_manager = StabilityManager()
            
            # Create analyzer
            analyzer = AudioPCBAnalyzer(board, stability_manager)
            
            results = {}
            
            # Perform requested analyses
            if self.thermal_var.get():
                results['thermal'] = analyzer.analyze_thermal()
            
            if self.signal_var.get():
                results['signal_integrity'] = analyzer.analyze_signal_integrity()
            
            if self.emi_var.get():
                results['emi'] = analyzer.analyze_emi()
            
            # Save results
            output_path = self.output_path.get()
            if output_path:
                with open(output_path, 'w') as f:
                    json.dump(results, f, indent=2)
                self.status_var.set(f"Analysis results saved to: {output_path}")
            else:
                # Show results in a new window
                self.show_results(results)
                
        except (FileNotFoundError, PermissionError) as e:
            messagebox.showerror("Error", f"File access error: {str(e)}")
        except (ValueError, KeyError) as e:
            messagebox.showerror("Error", f"Configuration error: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")
            
    def create_design(self):
        """Create new audio PCB design."""
        try:
            # Create output directory
            output_dir = Path(self.output_path.get())
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Load design rules
            rules = self.load_design_rules(self.rules_path.get())
            
            # Create design based on type
            design_type = self.design_type.get().lower()
            if design_type == "amplifier":
                from kicad_pcb_generator.examples.audio_amplifier import create_audio_amplifier
                create_audio_amplifier()
            elif design_type == "dac":
                messagebox.showinfo("Info", "DAC design not implemented yet")
                return
            elif design_type == "mixer":
                messagebox.showinfo("Info", "Mixer design not implemented yet")
                return
            
            self.status_var.set(f"Successfully created {design_type} design in: {output_dir}")
            
        except (FileNotFoundError, PermissionError) as e:
            messagebox.showerror("Error", f"File access error: {str(e)}")
        except (ValueError, KeyError) as e:
            messagebox.showerror("Error", f"Configuration error: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")
            
    def save_settings(self):
        """Save settings to file."""
        try:
            settings = {
                'default_output': self.default_output.get(),
                'default_rules': self.default_rules.get()
            }
            
            with open('settings.json', 'w') as f:
                json.dump(settings, f, indent=2)
            
            self.status_var.set("Settings saved successfully")
            
        except (FileNotFoundError, PermissionError) as e:
            messagebox.showerror("Error", f"File access error: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")
            
    def load_design_rules(self, rules_file):
        """Load design rules from JSON file."""
        if not rules_file:
            return AudioDesignRules()
        
        with open(rules_file, 'r') as f:
            rules_dict = json.load(f)
        
        return AudioDesignRules(**rules_dict)
        
    def show_results(self, results):
        """Show analysis results in a new window."""
        window = tk.Toplevel(self.root)
        window.title("Analysis Results")
        window.geometry("600x400")
        
        # Create text widget with scrollbar
        text = tk.Text(window, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(window, command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Insert results
        text.insert(tk.END, json.dumps(results, indent=2))
        text.configure(state='disabled')

    # Project Management Methods
    def open_project(self):
        """Open an existing project."""
        try:
            # Get selected project from listbox
            selection = self.project_listbox.curselection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a project to open")
                return
            
            project_name = self.project_listbox.get(selection[0])
            
            # Open project using project manager
            result = self.project_manager.open_project(project_name)
            if result.success:
                self.current_project = result.data
                self.status_var.set(f"Opened project: {project_name}")
                
                # Update UI with project data
                self.load_project_data(result.data)
            else:
                messagebox.showerror("Error", f"Failed to open project: {result.message}")
                
        except (ValueError, KeyError) as e:
            messagebox.showerror("Error", f"Project data error: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error opening project: {str(e)}")

    def new_project(self):
        """Create a new project."""
        try:
            # Get project name from user
            project_name = tk.simpledialog.askstring("New Project", "Enter project name:")
            if not project_name:
                return
            
            # Create project using project manager
            result = self.project_manager.create_project(project_name)
            if result.success:
                self.current_project = result.data
                self.status_var.set(f"Created new project: {project_name}")
                
                # Refresh project list
                self.refresh_project_list()
            else:
                messagebox.showerror("Error", f"Failed to create project: {result.message}")
                
        except (ValueError, KeyError) as e:
            messagebox.showerror("Error", f"Project configuration error: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error creating project: {str(e)}")

    def refresh_project_list(self):
        """Refresh the list of recent projects."""
        try:
            # Clear current list
            self.project_listbox.delete(0, tk.END)
            
            # Get recent projects from project manager
            result = self.project_manager.list_recent_projects()
            if result.success and result.data:
                for project in result.data:
                    self.project_listbox.insert(tk.END, project.name)
            else:
                self.project_listbox.insert(tk.END, "No recent projects")
                
        except (ValueError, KeyError) as e:
            self.project_listbox.delete(0, tk.END)
            self.project_listbox.insert(tk.END, f"Project data error: {str(e)}")
        except Exception as e:
            self.project_listbox.delete(0, tk.END)
            self.project_listbox.insert(tk.END, f"Unexpected error loading projects: {str(e)}")

    def load_project_data(self, project_data):
        """Load project data into UI."""
        try:
            # Update file paths
            if project_data.get('schematic_path'):
                self.schematic_path.set(project_data['schematic_path'])
            if project_data.get('pcb_path'):
                self.pcb_path.set(project_data['pcb_path'])
            if project_data.get('output_path'):
                self.output_path.set(project_data['output_path'])
                
            # Update status
            self.status_var.set(f"Loaded project: {project_data.get('name', 'Unknown')}")
            
        except (ValueError, KeyError) as e:
            self.status_var.set(f"Project data error: {str(e)}")
        except Exception as e:
            self.status_var.set(f"Unexpected error loading project data: {str(e)}")

    # Template Management Methods
    def use_template(self):
        """Use a selected template."""
        try:
            # Get selected template
            selection = self.template_tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a template to use")
                return
            
            template_id = self.template_tree.item(selection[0])['values'][0]
            
            # Use template
            result = self.template_manager.use_template(template_id)
            if result.success:
                self.status_var.set(f"Applied template: {template_id}")
                
                # Update UI with template data
                self.load_template_data(result.data)
            else:
                messagebox.showerror("Error", f"Failed to use template: {result.message}")
                
        except (ValueError, KeyError) as e:
            messagebox.showerror("Error", f"Template data error: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error using template: {str(e)}")

    def edit_template(self):
        """Edit a selected template."""
        try:
            # Get selected template
            selection = self.template_tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a template to edit")
                return
            
            template_id = self.template_tree.item(selection[0])['values'][0]
            
            # Open template editor
            self.open_template_editor(template_id)
            
        except (ValueError, KeyError) as e:
            messagebox.showerror("Error", f"Template data error: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error editing template: {str(e)}")

    def delete_template(self):
        """Delete a selected template."""
        try:
            # Get selected template
            selection = self.template_tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a template to delete")
                return
            
            template_id = self.template_tree.item(selection[0])['values'][0]
            
            # Confirm deletion
            if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete template '{template_id}'?"):
                return
            
            # Delete template
            result = self.template_manager.delete_template(template_id)
            if result.success:
                self.status_var.set(f"Deleted template: {template_id}")
                
                # Refresh template list
                self.refresh_template_list()
            else:
                messagebox.showerror("Error", f"Failed to delete template: {result.message}")
                
        except (ValueError, KeyError) as e:
            messagebox.showerror("Error", f"Template data error: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error deleting template: {str(e)}")

    def import_template(self):
        """Import a template from file."""
        try:
            # Browse for template file
            filename = filedialog.askopenfilename(
                title="Select Template File",
                filetypes=[("JSON", "*.json"), ("All Files", "*.*")]
            )
            if not filename:
                return
            
            # Import template
            result = self.template_manager.import_template(filename)
            if result.success:
                self.status_var.set(f"Imported template: {result.data.name}")
                
                # Refresh template list
                self.refresh_template_list()
            else:
                messagebox.showerror("Error", f"Failed to import template: {result.message}")
                
        except (FileNotFoundError, PermissionError) as e:
            messagebox.showerror("Error", f"File access error: {str(e)}")
        except (ValueError, KeyError) as e:
            messagebox.showerror("Error", f"Template data error: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error importing template: {str(e)}")

    def export_template(self):
        """Export a selected template to file."""
        try:
            # Get selected template
            selection = self.template_tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a template to export")
                return
            
            template_id = self.template_tree.item(selection[0])['values'][0]
            
            # Browse for export location
            filename = filedialog.asksaveasfilename(
                title="Export Template",
                defaultextension=".json",
                filetypes=[("JSON", "*.json"), ("All Files", "*.*")]
            )
            if not filename:
                return
            
            # Export template
            result = self.template_manager.export_template(template_id, filename)
            if result.success:
                self.status_var.set(f"Exported template: {template_id}")
            else:
                messagebox.showerror("Error", f"Failed to export template: {result.message}")
                
        except (FileNotFoundError, PermissionError) as e:
            messagebox.showerror("Error", f"File access error: {str(e)}")
        except (ValueError, KeyError) as e:
            messagebox.showerror("Error", f"Template data error: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error exporting template: {str(e)}")

    def refresh_template_list(self):
        """Refresh the list of available templates."""
        try:
            # Clear current tree
            for item in self.template_tree.get_children():
                self.template_tree.delete(item)
            
            # Get templates from template manager
            result = self.template_manager.list_templates()
            if result.success and result.data:
                for template in result.data:
                    self.template_tree.insert("", "end", values=(
                        template.name,
                        template.type,
                        template.description,
                        template.version
                    ))
            else:
                self.template_tree.insert("", "end", values=("No templates available", "", "", ""))
                
        except (ValueError, KeyError) as e:
            self.template_tree.insert("", "end", values=(f"Template data error: {str(e)}", "", "", ""))
        except Exception as e:
            self.template_tree.insert("", "end", values=(f"Unexpected error loading templates: {str(e)}", "", "", ""))

    def load_template_data(self, template_data):
        """Load template data into UI."""
        try:
            # Update design type if available
            if template_data.get('type'):
                self.design_type.set(template_data['type'])
                
            # Update other UI elements as needed
            self.status_var.set(f"Applied template: {template_data.get('name', 'Unknown')}")
            
        except (ValueError, KeyError) as e:
            self.status_var.set(f"Template data error: {str(e)}")
        except Exception as e:
            self.status_var.set(f"Unexpected error loading template data: {str(e)}")

    def open_template_editor(self, template_id):
        """Open template editor window."""
        try:
            # Create template editor window
            editor_window = tk.Toplevel(self.root)
            editor_window.title(f"Edit Template: {template_id}")
            editor_window.geometry("800x600")
            
            # Get template data
            result = self.template_manager.get_template(template_id)
            if not result.success:
                messagebox.showerror("Error", f"Failed to load template: {result.message}")
                return
            
            template_data = result.data
            
            # Create editor interface
            self.create_template_editor_interface(editor_window, template_data)
            
        except (ValueError, KeyError) as e:
            messagebox.showerror("Error", f"Template data error: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error opening template editor: {str(e)}")

    def create_template_editor_interface(self, parent, template_data):
        """Create template editor interface."""
        try:
            # Create form fields
            ttk.Label(parent, text="Template Name:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
            name_var = tk.StringVar(value=template_data.get('name', ''))
            ttk.Entry(parent, textvariable=name_var, width=40).grid(row=0, column=1, sticky="ew", padx=5, pady=5)
            
            ttk.Label(parent, text="Template Type:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
            type_var = tk.StringVar(value=template_data.get('type', ''))
            ttk.Entry(parent, textvariable=type_var, width=40).grid(row=1, column=1, sticky="ew", padx=5, pady=5)
            
            ttk.Label(parent, text="Description:").grid(row=2, column=0, sticky="nw", padx=5, pady=5)
            desc_text = tk.Text(parent, height=4, width=40)
            desc_text.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
            desc_text.insert("1.0", template_data.get('description', ''))
            
            ttk.Label(parent, text="Configuration (JSON):").grid(row=3, column=0, sticky="nw", padx=5, pady=5)
            config_text = tk.Text(parent, height=10, width=40)
            config_text.grid(row=3, column=1, sticky="ew", padx=5, pady=5)
            config_text.insert("1.0", json.dumps(template_data.get('configuration', {}), indent=2))
            
            # Buttons
            button_frame = ttk.Frame(parent)
            button_frame.grid(row=4, column=0, columnspan=2, pady=20)
            
            ttk.Button(button_frame, text="Save", command=lambda: self.save_template_edits(
                parent, template_data['id'], name_var.get(), type_var.get(), 
                desc_text.get("1.0", tk.END).strip(), config_text.get("1.0", tk.END).strip()
            )).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(button_frame, text="Cancel", command=parent.destroy).pack(side=tk.LEFT, padx=5)
            
            # Configure grid weights
            parent.columnconfigure(1, weight=1)
            parent.rowconfigure(2, weight=1)
            parent.rowconfigure(3, weight=1)
            
        except (ValueError, KeyError) as e:
            messagebox.showerror("Error", f"Template data error: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error creating template editor: {str(e)}")

    def save_template_edits(self, parent, template_id, name, type_name, description, config_text):
        """Save template edits."""
        try:
            # Parse configuration JSON
            try:
                configuration = json.loads(config_text)
            except json.JSONDecodeError:
                messagebox.showerror("Error", "Invalid JSON in configuration")
                return
            
            # Update template
            updated_data = {
                'name': name,
                'type': type_name,
                'description': description,
                'configuration': configuration
            }
            
            result = self.template_manager.update_template(template_id, updated_data)
            if result.success:
                self.status_var.set(f"Updated template: {name}")
                parent.destroy()
                
                # Refresh template list
                self.refresh_template_list()
            else:
                messagebox.showerror("Error", f"Failed to update template: {result.message}")
                
        except json.JSONDecodeError as e:
            messagebox.showerror("Error", f"Invalid JSON configuration: {str(e)}")
        except (ValueError, KeyError) as e:
            messagebox.showerror("Error", f"Template data error: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error saving template: {str(e)}")

    # Help and Documentation Methods
    def show_user_guide(self):
        """Show user guide in a new window."""
        try:
            # Create user guide window
            guide_window = tk.Toplevel(self.root)
            guide_window.title("User Guide")
            guide_window.geometry("800x600")
            
            # Create text widget with scrollbar
            text = scrolledtext.ScrolledText(guide_window, wrap=tk.WORD)
            text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Load user guide content
            guide_content = self.load_user_guide_content()
            text.insert(tk.END, guide_content)
            text.configure(state='disabled')
            
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error showing user guide: {str(e)}")

    def show_video_tutorials(self):
        """Show video tutorials window."""
        try:
            # Create video tutorials window
            tutorials_window = tk.Toplevel(self.root)
            tutorials_window.title("Video Tutorials")
            tutorials_window.geometry("600x400")
            
            # Create listbox for tutorials
            tutorials_frame = ttk.Frame(tutorials_window)
            tutorials_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            ttk.Label(tutorials_frame, text="Available Tutorials:").pack(anchor="w")
            
            tutorials_listbox = tk.Listbox(tutorials_frame, height=15)
            tutorials_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            scrollbar = ttk.Scrollbar(tutorials_frame, orient=tk.VERTICAL, command=tutorials_listbox.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            tutorials_listbox.configure(yscrollcommand=scrollbar.set)
            
            # Add tutorial items
            tutorials = [
                "Getting Started with Audio PCB Design",
                "Creating Your First Amplifier",
                "Understanding Signal Integrity",
                "Optimizing Component Placement",
                "Advanced Routing Techniques",
                "Thermal Management Best Practices",
                "EMI/EMC Considerations",
                "Cost Optimization Strategies"
            ]
            
            for tutorial in tutorials:
                tutorials_listbox.insert(tk.END, tutorial)
            
            # Buttons frame
            button_frame = ttk.Frame(tutorials_window)
            button_frame.pack(fill=tk.X, padx=10, pady=10)
            
            ttk.Button(button_frame, text="Watch Tutorial", 
                      command=lambda: self.watch_tutorial(tutorials_listbox.get(tk.ACTIVE))).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Close", command=tutorials_window.destroy).pack(side=tk.RIGHT, padx=5)
            
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error showing video tutorials: {str(e)}")

    def show_faq(self):
        """Show FAQ window."""
        try:
            # Create FAQ window
            faq_window = tk.Toplevel(self.root)
            faq_window.title("Frequently Asked Questions")
            faq_window.geometry("700x500")
            
            # Create notebook for FAQ categories
            notebook = ttk.Notebook(faq_window)
            notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # General FAQ tab
            general_frame = ttk.Frame(notebook)
            notebook.add(general_frame, text="General")
            
            general_text = scrolledtext.ScrolledText(general_frame, wrap=tk.WORD)
            general_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            general_faq = """
Q: What is Audio PCB Designer?
A: Audio PCB Designer is a specialized tool for designing printed circuit boards for audio applications, with built-in validation and optimization features.

Q: What file formats are supported?
A: The tool supports KiCad schematic (.kicad_sch) and PCB (.kicad_pcb) files, as well as Falstad circuit simulator files.

Q: How do I get started?
A: Start by creating a new project or importing an existing schematic. Use the templates to get started quickly.

Q: What validation features are available?
A: The tool provides impedance validation, frequency response analysis, noise analysis, signal path analysis, power supply validation, and ground plane validation.

Q: Can I optimize my designs?
A: Yes, the tool includes optimization for component placement, routing, thermal management, EMI/EMC, and cost optimization.
            """
            general_text.insert(tk.END, general_faq)
            general_text.configure(state='disabled')
            
            # Technical FAQ tab
            technical_frame = ttk.Frame(notebook)
            notebook.add(technical_frame, text="Technical")
            
            technical_text = scrolledtext.ScrolledText(technical_frame, wrap=tk.WORD)
            technical_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            technical_faq = """
Q: What are the system requirements?
A: The tool requires Python 3.8+, KiCad 9+, and sufficient RAM for large designs.

Q: How accurate are the simulations?
A: Simulations use industry-standard models and provide good accuracy for audio frequency applications.

Q: Can I customize the design rules?
A: Yes, you can create custom design rule files in JSON format to match your specific requirements.

Q: How do I handle high-frequency signals?
A: Use the signal integrity analysis features and follow the routing guidelines provided by the tool.

Q: What about thermal considerations?
A: The thermal analysis feature helps identify hot spots and suggests optimal component placement.
            """
            technical_text.insert(tk.END, technical_faq)
            technical_text.configure(state='disabled')
            
            # Troubleshooting FAQ tab
            troubleshooting_frame = ttk.Frame(notebook)
            notebook.add(troubleshooting_frame, text="Troubleshooting")
            
            troubleshooting_text = scrolledtext.ScrolledText(troubleshooting_frame, wrap=tk.WORD)
            troubleshooting_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            troubleshooting_faq = """
Q: The tool won't start. What should I do?
A: Check that Python and KiCad are properly installed and in your PATH. Try running from the command line to see error messages.

Q: Import fails with validation errors. How do I fix this?
A: Check your schematic for disconnected components, missing power connections, or invalid component values.

Q: PCB generation fails. What's wrong?
A: Ensure all components have valid footprints assigned and that the design rules are appropriate for your board.

Q: Analysis results seem incorrect. How can I verify?
A: Compare with manual calculations or use external tools to validate the results.

Q: The GUI is slow or unresponsive. What can I do?
A: Close other applications to free up memory, or try running the command-line version for better performance.
            """
            troubleshooting_text.insert(tk.END, troubleshooting_faq)
            troubleshooting_text.configure(state='disabled')
            
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error showing FAQ: {str(e)}")

    def open_online_docs(self):
        """Open online documentation in browser."""
        try:
            webbrowser.open("https://github.com/your-repo/audio-pcb-designer/docs")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error opening online docs: {str(e)}")

    def watch_tutorial(self, tutorial_name):
        """Open tutorial video in browser."""
        try:
            # Map tutorial names to URLs
            tutorial_urls = {
                "Getting Started with Audio PCB Design": "https://youtube.com/watch?v=example1",
                "Creating Your First Amplifier": "https://youtube.com/watch?v=example2",
                "Understanding Signal Integrity": "https://youtube.com/watch?v=example3",
                "Optimizing Component Placement": "https://youtube.com/watch?v=example4",
                "Advanced Routing Techniques": "https://youtube.com/watch?v=example5",
                "Thermal Management Best Practices": "https://youtube.com/watch?v=example6",
                "EMI/EMC Considerations": "https://youtube.com/watch?v=example7",
                "Cost Optimization Strategies": "https://youtube.com/watch?v=example8"
            }
            
            url = tutorial_urls.get(tutorial_name, "https://youtube.com/results?search_query=audio+pcb+design")
            webbrowser.open(url)
            
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error opening tutorial: {str(e)}")

    def load_user_guide_content(self):
        """Load user guide content."""
        return """
AUDIO PCB DESIGNER - USER GUIDE

Welcome to Audio PCB Designer, a specialized tool for designing printed circuit boards for audio applications.

1. GETTING STARTED
   - Create a new project or open an existing one
   - Choose from available templates or start from scratch
   - Configure your design rules and preferences

2. PROJECT MANAGEMENT
   - Use the Projects tab to manage your designs
   - Open recent projects quickly
   - Create new projects with templates

3. SCHEMATIC TO PCB CONVERSION
   - Import your KiCad schematic (.kicad_sch)
   - Configure design rules for audio applications
   - Convert to PCB with automatic component placement

4. ANALYSIS AND VALIDATION
   - Thermal analysis for heat management
   - Signal integrity analysis for audio quality
   - EMI/EMC analysis for compliance
   - Power supply and ground plane validation

5. OPTIMIZATION
   - Component placement optimization
   - Routing optimization for signal quality
   - Thermal optimization for reliability
   - Cost optimization for production

6. TEMPLATE MANAGEMENT
   - Use pre-built templates for common audio circuits
   - Create and save your own templates
   - Share templates with the community

7. IMPORT/EXPORT
   - Import from Falstad circuit simulator
   - Export to various manufacturing formats
   - Generate reports and documentation

8. HELP AND SUPPORT
   - Access video tutorials
   - Browse the FAQ
   - View online documentation
   - Join the community

For more detailed information, visit our online documentation or watch the video tutorials.
        """

    def load_default_help_content(self):
        """Load default help content in the help tab."""
        try:
            default_content = """
QUICK HELP

Welcome to Audio PCB Designer!

Quick Start:
1. Go to the Projects tab to create or open a project
2. Use the Convert tab to convert schematics to PCBs
3. Use the Analyze tab to validate your designs
4. Use the Templates tab to access pre-built designs
5. Use the Help tab for documentation and tutorials

Common Tasks:
• Creating a new project: Projects tab → New Project
• Converting a schematic: Convert tab → Browse → Convert
• Analyzing a PCB: Analyze tab → Browse → Analyze
• Using a template: Templates tab → Select → Use Template

Need more help? Click the buttons above to access the full user guide, video tutorials, or FAQ.
            """
            self.help_text.insert(tk.END, default_content)
            self.help_text.configure(state='disabled')
            
        except (ValueError, KeyError) as e:
            self.help_text.insert(tk.END, f"Help content error: {str(e)}")
        except Exception as e:
            self.help_text.insert(tk.END, f"Unexpected error loading help content: {str(e)}")

def main():
    """Main entry point for the Audio PCB Designer GUI.
    
    This function initializes and starts the graphical user interface for the
    KiCad PCB Generator. The GUI provides a comprehensive interface for:
    
    Features:
        - Project management and creation
        - Schematic to PCB conversion
        - Audio circuit analysis and validation
        - Template management and editing
        - Falstad circuit import
        - Real-time design validation
        - Settings configuration
    
    The GUI is organized into tabs:
        - Projects: Manage and create PCB projects
        - Convert: Convert schematics to PCB layouts
        - Analyze: Analyze audio circuit performance
        - Create: Create new designs from templates
        - Import: Import circuits from various formats
        - Templates: Manage design templates
        - Help: Documentation and tutorials
        - Settings: Application configuration
    
    Example Usage:
        # Start the GUI
        python -m kicad_pcb_generator.gui
        
        # Or import and run programmatically
        from kicad_pcb_generator.gui import main
        main()
    """
    root = tk.Tk()
    app = AudioPCBDesignerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 