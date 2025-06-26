"""Configuration UI component for customizing settings."""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional, Callable
from ...utils.config.settings import Settings, ValidationSeverity
from ...utils.logging.logger import Logger

class ConfigUI:
    """Configuration UI component for customizing settings."""
    
    def __init__(self, parent: Optional[tk.Widget] = None, settings: Optional[Settings] = None):
        """Initialize the configuration UI.
        
        Args:
            parent: Parent widget
            settings: Optional settings instance
        """
        self.settings = settings or Settings()
        self.logger = Logger(__name__)
        
        # Create main frame
        self.frame = ttk.Frame(parent) if parent else ttk.Frame()
        
        # Create notebook for different setting categories
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs for different setting categories
        self.tabs = {}
        self._create_general_tab()
        self._create_audio_tab()
        self._create_manufacturing_tab()
        self._create_validation_tab()
        
        # Create buttons
        self._create_buttons()
    
    def _create_general_tab(self):
        """Create the general settings tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="General")
        self.tabs["general"] = tab
        
        # Create settings
        row = 0
        
        # Output directory
        ttk.Label(tab, text="Output Directory:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.output_dir = ttk.Entry(tab, width=40)
        self.output_dir.insert(0, self.settings.get("output_directory", ""))
        self.output_dir.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Button(tab, text="Browse", command=self._browse_output_dir).grid(row=row, column=2, padx=5, pady=5)
        row += 1
        
        # Default project name
        ttk.Label(tab, text="Default Project Name:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.project_name = ttk.Entry(tab, width=40)
        self.project_name.insert(0, self.settings.get("default_project_name", ""))
        self.project_name.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # Auto-save interval
        ttk.Label(tab, text="Auto-save Interval (minutes):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.auto_save = ttk.Spinbox(tab, from_=1, to=60, width=5)
        self.auto_save.insert(0, self.settings.get("auto_save_interval", 5))
        self.auto_save.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1
    
    def _create_audio_tab(self):
        """Create the audio settings tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Audio")
        self.tabs["audio"] = tab
        
        # Create settings
        row = 0
        
        # Audio layer names
        ttk.Label(tab, text="Audio Layer Names:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.audio_layers = ttk.Entry(tab, width=40)
        self.audio_layers.insert(0, ",".join(self.settings.get("audio.layers", [])))
        self.audio_layers.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # Minimum track width
        ttk.Label(tab, text="Minimum Track Width (mm):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.min_track_width = ttk.Spinbox(tab, from_=0.1, to=10.0, increment=0.1, width=5)
        self.min_track_width.insert(0, self.settings.get("audio.min_track_width", 0.2))
        self.min_track_width.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # Minimum clearance
        ttk.Label(tab, text="Minimum Clearance (mm):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.min_clearance = ttk.Spinbox(tab, from_=0.1, to=10.0, increment=0.1, width=5)
        self.min_clearance.insert(0, self.settings.get("audio.min_clearance", 0.2))
        self.min_clearance.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # Ground plane clearance
        ttk.Label(tab, text="Ground Plane Clearance (mm):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.ground_clearance = ttk.Spinbox(tab, from_=0.1, to=10.0, increment=0.1, width=5)
        self.ground_clearance.insert(0, self.settings.get("audio.ground_clearance", 0.3))
        self.ground_clearance.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1
    
    def _create_manufacturing_tab(self):
        """Create the manufacturing settings tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Manufacturing")
        self.tabs["manufacturing"] = tab
        
        # Create settings
        row = 0
        
        # Board size
        ttk.Label(tab, text="Maximum Board Size (mm):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.max_board_size = ttk.Spinbox(tab, from_=10, to=1000, increment=10, width=5)
        self.max_board_size.insert(0, self.settings.get("manufacturing.max_board_size", 100))
        self.max_board_size.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # Minimum hole size
        ttk.Label(tab, text="Minimum Hole Size (mm):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.min_hole_size = ttk.Spinbox(tab, from_=0.1, to=10.0, increment=0.1, width=5)
        self.min_hole_size.insert(0, self.settings.get("manufacturing.min_hole_size", 0.3))
        self.min_hole_size.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # Minimum via size
        ttk.Label(tab, text="Minimum Via Size (mm):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.min_via_size = ttk.Spinbox(tab, from_=0.1, to=10.0, increment=0.1, width=5)
        self.min_via_size.insert(0, self.settings.get("manufacturing.min_via_size", 0.4))
        self.min_via_size.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # Minimum drill size
        ttk.Label(tab, text="Minimum Drill Size (mm):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.min_drill_size = ttk.Spinbox(tab, from_=0.1, to=10.0, increment=0.1, width=5)
        self.min_drill_size.insert(0, self.settings.get("manufacturing.min_drill_size", 0.2))
        self.min_drill_size.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1
    
    def _create_validation_tab(self):
        """Create the validation settings tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Validation")
        self.tabs["validation"] = tab
        
        # Create a frame for the treeview and scrollbar
        tree_frame = ttk.Frame(tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create treeview for validation rules
        self.rule_tree = ttk.Treeview(tree_frame, columns=("enabled", "severity", "description"), show="headings")
        self.rule_tree.heading("enabled", text="Enabled")
        self.rule_tree.heading("severity", text="Severity")
        self.rule_tree.heading("description", text="Description")
        self.rule_tree.column("enabled", width=60)
        self.rule_tree.column("severity", width=80)
        self.rule_tree.column("description", width=300)
        self.rule_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.rule_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.rule_tree.configure(yscrollcommand=scrollbar.set)
        
        # Create frame for rule parameters
        param_frame = ttk.LabelFrame(tab, text="Rule Parameters")
        param_frame.pack(fill=tk.X, padx=5, pady=5)
        self.param_frame = param_frame
        
        # Load validation rules into treeview
        self._load_validation_rules()
        
        # Bind selection event
        self.rule_tree.bind("<<TreeviewSelect>>", self._on_rule_select)
    
    def _load_validation_rules(self):
        """Load validation rules into the treeview."""
        rules = self.settings.get_validation_rules()
        
        for rule_key, rule in rules.items():
            category, name = rule_key.split('.')
            self.rule_tree.insert("", tk.END, values=(
                "✓" if rule.enabled else "✗",
                rule.severity.value,
                rule.description
            ), tags=(category,))
    
    def _on_rule_select(self, event):
        """Handle selection of a validation rule."""
        selection = self.rule_tree.selection()
        if not selection:
            return
        
        # Clear parameter frame
        for widget in self.param_frame.winfo_children():
            widget.destroy()
        
        # Get selected rule
        item = selection[0]
        values = self.rule_tree.item(item)["values"]
        description = values[2]
        
        # Find rule in settings
        rules = self.settings.get_validation_rules()
        for rule_key, rule in rules.items():
            if rule.description == description:
                # Create parameter widgets
                row = 0
                for param_name, param_value in rule.parameters.items():
                    ttk.Label(self.param_frame, text=f"{param_name}:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
                    
                    if isinstance(param_value, bool):
                        var = tk.BooleanVar(value=param_value)
                        ttk.Checkbutton(self.param_frame, variable=var).grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
                    elif isinstance(param_value, (int, float)):
                        spinbox = ttk.Spinbox(self.param_frame, from_=0, to=1000, increment=0.1, width=10)
                        spinbox.insert(0, str(param_value))
                        spinbox.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
                    else:
                        entry = ttk.Entry(self.param_frame, width=20)
                        entry.insert(0, str(param_value))
                        entry.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
                    
                    row += 1
                
                # Add severity selector
                ttk.Label(self.param_frame, text="Severity:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
                severity_var = tk.StringVar(value=rule.severity.value)
                severity_combo = ttk.Combobox(self.param_frame, textvariable=severity_var, values=[s.value for s in ValidationSeverity])
                severity_combo.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
                row += 1
                
                # Add enable/disable checkbox
                enabled_var = tk.BooleanVar(value=rule.enabled)
                ttk.Checkbutton(self.param_frame, text="Enable Rule", variable=enabled_var).grid(
                    row=row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)
                break
    
    def _create_buttons(self):
        """Create buttons for saving and canceling."""
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="Save", command=self._save_settings).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Reset to Defaults", command=self._reset_settings).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self._cancel).pack(side=tk.RIGHT, padx=5)
    
    def _browse_output_dir(self):
        """Browse for output directory."""
        from tkinter import filedialog
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_dir.delete(0, tk.END)
            self.output_dir.insert(0, directory)
    
    def _save_settings(self):
        """Save the current settings."""
        try:
            # General settings
            self.settings.set("output_directory", self.output_dir.get())
            self.settings.set("default_project_name", self.project_name.get())
            self.settings.set("auto_save_interval", int(self.auto_save.get()))
            
            # Audio settings
            self.settings.set("audio.layers", [layer.strip() for layer in self.audio_layers.get().split(",")])
            self.settings.set("audio.min_track_width", float(self.min_track_width.get()))
            self.settings.set("audio.min_clearance", float(self.min_clearance.get()))
            self.settings.set("audio.ground_clearance", float(self.ground_clearance.get()))
            
            # Manufacturing settings
            self.settings.set("manufacturing.max_board_size", float(self.max_board_size.get()))
            self.settings.set("manufacturing.min_hole_size", float(self.min_hole_size.get()))
            self.settings.set("manufacturing.min_via_size", float(self.min_via_size.get()))
            self.settings.set("manufacturing.min_drill_size", float(self.min_drill_size.get()))
            
            # Save to file
            self.settings.save_config()
            
            messagebox.showinfo("Success", "Settings saved successfully.")
            self.frame.master.destroy()
            
        except Exception as e:
            self.logger.error(f"Error saving settings: {str(e)}")
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
    
    def _reset_settings(self):
        """Reset settings to defaults."""
        if messagebox.askyesno("Confirm Reset", "Are you sure you want to reset all settings to defaults?"):
            self.settings.reset_to_defaults()
            self._load_settings()
    
    def _cancel(self):
        """Cancel changes and close the window."""
        if messagebox.askyesno("Confirm Cancel", "Are you sure you want to cancel changes?"):
            self.frame.master.destroy()
    
    def _load_settings(self):
        """Load settings into the UI."""
        # General settings
        self.output_dir.delete(0, tk.END)
        self.output_dir.insert(0, self.settings.get("output_directory", ""))
        
        self.project_name.delete(0, tk.END)
        self.project_name.insert(0, self.settings.get("default_project_name", ""))
        
        self.auto_save.delete(0, tk.END)
        self.auto_save.insert(0, self.settings.get("auto_save_interval", 5))
        
        # Audio settings
        self.audio_layers.delete(0, tk.END)
        self.audio_layers.insert(0, ",".join(self.settings.get("audio.layers", [])))
        
        self.min_track_width.delete(0, tk.END)
        self.min_track_width.insert(0, self.settings.get("audio.min_track_width", 0.2))
        
        self.min_clearance.delete(0, tk.END)
        self.min_clearance.insert(0, self.settings.get("audio.min_clearance", 0.2))
        
        self.ground_clearance.delete(0, tk.END)
        self.ground_clearance.insert(0, self.settings.get("audio.ground_clearance", 0.3))
        
        # Manufacturing settings
        self.max_board_size.delete(0, tk.END)
        self.max_board_size.insert(0, self.settings.get("manufacturing.max_board_size", 100))
        
        self.min_hole_size.delete(0, tk.END)
        self.min_hole_size.insert(0, self.settings.get("manufacturing.min_hole_size", 0.3))
        
        self.min_via_size.delete(0, tk.END)
        self.min_via_size.insert(0, self.settings.get("manufacturing.min_via_size", 0.4))
        
        self.min_drill_size.delete(0, tk.END)
        self.min_drill_size.insert(0, self.settings.get("manufacturing.min_drill_size", 0.2))
        
        # Reload validation rules
        self.rule_tree.delete(*self.rule_tree.get_children())
        self._load_validation_rules()
    
    def show(self):
        """Show the configuration UI."""
        self.frame.master.title("Configuration")
        self.frame.master.resizable(False, False)
        self.frame.master.mainloop() 
