"""Manufacturing UI component for managing manufacturing features."""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Any, Optional, Callable
from ..core.manufacturing.panelization import PanelizationManager, PanelizationConfig
from ..core.manufacturing.visualization import VisualizationManager, VisualizationConfig
from ..core.manufacturing.output import OutputManager, OutputConfig
from ..utils.logging.logger import Logger
from ..utils.config.settings import Settings

class ManufacturingUI:
    """Manufacturing UI component for managing manufacturing features."""
    
    def __init__(self, parent: Optional[tk.Widget] = None, settings: Optional[Settings] = None):
        """Initialize the manufacturing UI.
        
        Args:
            parent: Parent widget
            settings: Optional settings instance
        """
        self.logger = Logger(__name__)
        self.settings = settings or Settings()
        
        # Create main frame
        self.frame = ttk.Frame(parent) if parent else ttk.Frame()
        
        # Create notebook for different manufacturing features
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs for different manufacturing features
        self.tabs = {}
        self._create_manufacturer_tab()
        self._create_panelization_tab()
        self._create_visualization_tab()
        self._create_output_tab()
        
        # Create buttons
        self._create_buttons()
        
        # Initialize managers
        self.panelization_manager = PanelizationManager()
        self.visualization_manager = VisualizationManager()
        self.output_manager = OutputManager()
    
    def _create_manufacturer_tab(self):
        """Create the manufacturer settings tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Manufacturer")
        self.tabs["manufacturer"] = tab
        
        # Create settings
        row = 0
        
        # Manufacturer selection
        ttk.Label(tab, text="Manufacturer:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.manufacturer = ttk.Combobox(tab, values=self.settings.get_available_manufacturers(), width=20)
        self.manufacturer.insert(0, self.settings.get("manufacturing.manufacturer", "jlcpcb"))
        self.manufacturer.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        self.manufacturer.bind('<<ComboboxSelected>>', self._on_manufacturer_change)
        row += 1
        
        # Board thickness
        ttk.Label(tab, text="Board Thickness (mm):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.board_thickness = ttk.Combobox(tab, width=10)
        self.board_thickness.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # Copper weight
        ttk.Label(tab, text="Copper Weight (oz):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.copper_weight = ttk.Combobox(tab, width=10)
        self.copper_weight.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # Solder mask color
        ttk.Label(tab, text="Solder Mask Color:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.solder_mask_color = ttk.Combobox(tab, width=10)
        self.solder_mask_color.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # Silkscreen color
        ttk.Label(tab, text="Silkscreen Color:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.silkscreen_color = ttk.Combobox(tab, width=10)
        self.silkscreen_color.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # Update manufacturer options
        self._update_manufacturer_options()
    
    def _on_manufacturer_change(self, event):
        """Handle manufacturer selection change."""
        manufacturer = self.manufacturer.get()
        try:
            self.settings.set_manufacturer(manufacturer)
            self._update_manufacturer_options()
        except Exception as e:
            self.logger.error(f"Error changing manufacturer: {str(e)}")
            messagebox.showerror("Error", f"Failed to change manufacturer: {str(e)}")
    
    def _update_manufacturer_options(self):
        """Update manufacturer-specific options."""
        try:
            options = self.settings.get_manufacturer_options()
            
            # Update board thickness options
            self.board_thickness['values'] = [f"{t:.1f}" for t in options['board_thickness']]
            self.board_thickness.set(str(self.settings.get("manufacturing.board_thickness", options['board_thickness'][0])))
            
            # Update copper weight options
            self.copper_weight['values'] = [f"{w:.1f}" for w in options['copper_weight']]
            self.copper_weight.set(str(self.settings.get("manufacturing.copper_weight", options['copper_weight'][0])))
            
            # Update solder mask color options
            self.solder_mask_color['values'] = options['solder_mask_colors']
            self.solder_mask_color.set(self.settings.get("manufacturing.solder_mask_color", options['solder_mask_colors'][0]))
            
            # Update silkscreen color options
            self.silkscreen_color['values'] = options['silkscreen_colors']
            self.silkscreen_color.set(self.settings.get("manufacturing.silkscreen_color", options['silkscreen_colors'][0]))
            
        except Exception as e:
            self.logger.error(f"Error updating manufacturer options: {str(e)}")
            messagebox.showerror("Error", f"Failed to update manufacturer options: {str(e)}")
    
    def _save_manufacturer_settings(self):
        """Save manufacturer settings."""
        try:
            self.settings.set("manufacturing.board_thickness", float(self.board_thickness.get()))
            self.settings.set("manufacturing.copper_weight", float(self.copper_weight.get()))
            self.settings.set("manufacturing.solder_mask_color", self.solder_mask_color.get())
            self.settings.set("manufacturing.silkscreen_color", self.silkscreen_color.get())
            self.settings.save_config()
        except Exception as e:
            self.logger.error(f"Error saving manufacturer settings: {str(e)}")
            messagebox.showerror("Error", f"Failed to save manufacturer settings: {str(e)}")
    
    def _create_panelization_tab(self):
        """Create the panelization tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Panelization")
        self.tabs["panelization"] = tab
        
        # Create settings
        row = 0
        
        # Rows
        ttk.Label(tab, text="Rows:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.rows = ttk.Spinbox(tab, from_=1, to=10, width=5)
        self.rows.insert(0, "2")
        self.rows.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # Columns
        ttk.Label(tab, text="Columns:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.columns = ttk.Spinbox(tab, from_=1, to=10, width=5)
        self.columns.insert(0, "2")
        self.columns.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # Spacing
        ttk.Label(tab, text="Spacing (mm):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.spacing = ttk.Spinbox(tab, from_=0.1, to=10.0, increment=0.1, width=5)
        self.spacing.insert(0, "5.0")
        self.spacing.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # Frame width
        ttk.Label(tab, text="Frame Width (mm):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.frame_width = ttk.Spinbox(tab, from_=0.1, to=10.0, increment=0.1, width=5)
        self.frame_width.insert(0, "2.0")
        self.frame_width.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # Options
        self.mouse_bites = tk.BooleanVar(value=True)
        ttk.Checkbutton(tab, text="Mouse Bites", variable=self.mouse_bites).grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        self.vcuts = tk.BooleanVar(value=True)
        ttk.Checkbutton(tab, text="V-Cuts", variable=self.vcuts).grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        self.tooling_holes = tk.BooleanVar(value=True)
        ttk.Checkbutton(tab, text="Tooling Holes", variable=self.tooling_holes).grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        self.fiducials = tk.BooleanVar(value=True)
        ttk.Checkbutton(tab, text="Fiducials", variable=self.fiducials).grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        row += 1
    
    def _create_visualization_tab(self):
        """Create the visualization tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Visualization")
        self.tabs["visualization"] = tab
        
        # Create settings
        row = 0
        
        # Style
        ttk.Label(tab, text="Style:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.style = ttk.Combobox(tab, values=["default", "modern", "classic"], width=10)
        self.style.insert(0, "default")
        self.style.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # Resolution
        ttk.Label(tab, text="Resolution (DPI):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.resolution = ttk.Spinbox(tab, from_=72, to=600, increment=72, width=5)
        self.resolution.insert(0, "300")
        self.resolution.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # Transparency
        self.transparency = tk.BooleanVar(value=True)
        ttk.Checkbutton(tab, text="Transparency", variable=self.transparency).grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # Highlight options
        highlight_frame = ttk.LabelFrame(tab, text="Highlight Options")
        highlight_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W+tk.E, padx=5, pady=5)
        row += 1
        
        highlight_row = 0
        self.highlight_pads = tk.BooleanVar(value=True)
        ttk.Checkbutton(highlight_frame, text="Pads", variable=self.highlight_pads).grid(row=highlight_row, column=0, sticky=tk.W, padx=5, pady=2)
        highlight_row += 1
        
        self.highlight_tracks = tk.BooleanVar(value=True)
        ttk.Checkbutton(highlight_frame, text="Tracks", variable=self.highlight_tracks).grid(row=highlight_row, column=0, sticky=tk.W, padx=5, pady=2)
        highlight_row += 1
        
        self.highlight_zones = tk.BooleanVar(value=True)
        ttk.Checkbutton(highlight_frame, text="Zones", variable=self.highlight_zones).grid(row=highlight_row, column=0, sticky=tk.W, padx=5, pady=2)
        highlight_row += 1
        
        self.highlight_vias = tk.BooleanVar(value=True)
        ttk.Checkbutton(highlight_frame, text="Vias", variable=self.highlight_vias).grid(row=highlight_row, column=0, sticky=tk.W, padx=5, pady=2)
        highlight_row += 1
        
        self.highlight_holes = tk.BooleanVar(value=True)
        ttk.Checkbutton(highlight_frame, text="Holes", variable=self.highlight_holes).grid(row=highlight_row, column=0, sticky=tk.W, padx=5, pady=2)
        highlight_row += 1
        
        self.highlight_silkscreen = tk.BooleanVar(value=True)
        ttk.Checkbutton(highlight_frame, text="Silkscreen", variable=self.highlight_silkscreen).grid(row=highlight_row, column=0, sticky=tk.W, padx=5, pady=2)
        highlight_row += 1
        
        self.highlight_soldermask = tk.BooleanVar(value=True)
        ttk.Checkbutton(highlight_frame, text="Soldermask", variable=self.highlight_soldermask).grid(row=highlight_row, column=0, sticky=tk.W, padx=5, pady=2)
        highlight_row += 1
        
        self.highlight_courtyard = tk.BooleanVar(value=True)
        ttk.Checkbutton(highlight_frame, text="Courtyard", variable=self.highlight_courtyard).grid(row=highlight_row, column=0, sticky=tk.W, padx=5, pady=2)
        highlight_row += 1
        
        self.highlight_fabrication = tk.BooleanVar(value=True)
        ttk.Checkbutton(highlight_frame, text="Fabrication", variable=self.highlight_fabrication).grid(row=highlight_row, column=0, sticky=tk.W, padx=5, pady=2)
        highlight_row += 1
        
        self.highlight_other = tk.BooleanVar(value=True)
        ttk.Checkbutton(highlight_frame, text="Other", variable=self.highlight_other).grid(row=highlight_row, column=0, sticky=tk.W, padx=5, pady=2)
        highlight_row += 1
    
    def _create_output_tab(self):
        """Create the output tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Output")
        self.tabs["output"] = tab
        
        # Create settings
        row = 0
        
        # Output directory
        ttk.Label(tab, text="Output Directory:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.output_dir = ttk.Entry(tab, width=40)
        self.output_dir.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Button(tab, text="Browse", command=self._browse_output_dir).grid(row=row, column=2, padx=5, pady=5)
        row += 1
        
        # Output options
        output_frame = ttk.LabelFrame(tab, text="Output Options")
        output_frame.grid(row=row, column=0, columnspan=3, sticky=tk.W+tk.E, padx=5, pady=5)
        row += 1
        
        output_row = 0
        self.generate_gerber = tk.BooleanVar(value=True)
        ttk.Checkbutton(output_frame, text="Gerber Files", variable=self.generate_gerber).grid(row=output_row, column=0, sticky=tk.W, padx=5, pady=2)
        output_row += 1
        
        self.generate_drill = tk.BooleanVar(value=True)
        ttk.Checkbutton(output_frame, text="Drill Files", variable=self.generate_drill).grid(row=output_row, column=0, sticky=tk.W, padx=5, pady=2)
        output_row += 1
        
        self.generate_3d = tk.BooleanVar(value=True)
        ttk.Checkbutton(output_frame, text="3D Models", variable=self.generate_3d).grid(row=output_row, column=0, sticky=tk.W, padx=5, pady=2)
        output_row += 1
        
        self.generate_pdf = tk.BooleanVar(value=True)
        ttk.Checkbutton(output_frame, text="PDF", variable=self.generate_pdf).grid(row=output_row, column=0, sticky=tk.W, padx=5, pady=2)
        output_row += 1
        
        self.generate_bom = tk.BooleanVar(value=True)
        ttk.Checkbutton(output_frame, text="BOM", variable=self.generate_bom).grid(row=output_row, column=0, sticky=tk.W, padx=5, pady=2)
        output_row += 1
        
        self.generate_pick_and_place = tk.BooleanVar(value=True)
        ttk.Checkbutton(output_frame, text="Pick and Place", variable=self.generate_pick_and_place).grid(row=output_row, column=0, sticky=tk.W, padx=5, pady=2)
        output_row += 1
    
    def _create_buttons(self):
        """Create the action buttons."""
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="Generate", command=self._generate).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self._cancel).pack(side=tk.RIGHT, padx=5)
    
    def _browse_output_dir(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir.delete(0, tk.END)
            self.output_dir.insert(0, directory)
    
    def _generate(self):
        """Generate manufacturing output."""
        try:
            # Get current tab
            current_tab = self.notebook.select()
            tab_name = self.notebook.tab(current_tab, "text")
            
            if tab_name == "Panelization":
                self._generate_panelization()
            elif tab_name == "Visualization":
                self._generate_visualization()
            elif tab_name == "Output":
                self._generate_output()
            
            messagebox.showinfo("Success", "Generation completed successfully!")
        except Exception as e:
            self.logger.error(f"Error during generation: {str(e)}")
            messagebox.showerror("Error", f"Error during generation: {str(e)}")
    
    def _generate_panelization(self):
        """Generate panelization."""
        config = PanelizationConfig(
            rows=int(self.rows.get()),
            columns=int(self.columns.get()),
            spacing=float(self.spacing.get()),
            frame_width=float(self.frame_width.get()),
            mouse_bites=self.mouse_bites.get(),
            vcuts=self.vcuts.get(),
            tooling_holes=self.tooling_holes.get(),
            fiducials=self.fiducials.get()
        )
        
        input_file = filedialog.askopenfilename(
            title="Select KiCad PCB File",
            filetypes=[("KiCad PCB Files", "*.kicad_pcb")]
        )
        if not input_file:
            return
        
        output_file = filedialog.asksaveasfilename(
            title="Save Panelized PCB",
            defaultextension=".kicad_pcb",
            filetypes=[("KiCad PCB Files", "*.kicad_pcb")]
        )
        if not output_file:
            return
        
        self.panelization_manager.panelize_board(input_file, output_file, config)
    
    def _generate_visualization(self):
        """Generate visualization."""
        config = VisualizationConfig(
            style=self.style.get(),
            resolution=int(self.resolution.get()),
            transparency=self.transparency.get(),
            highlight_pads=self.highlight_pads.get(),
            highlight_tracks=self.highlight_tracks.get(),
            highlight_zones=self.highlight_zones.get(),
            highlight_vias=self.highlight_vias.get(),
            highlight_holes=self.highlight_holes.get(),
            highlight_silkscreen=self.highlight_silkscreen.get(),
            highlight_soldermask=self.highlight_soldermask.get(),
            highlight_courtyard=self.highlight_courtyard.get(),
            highlight_fabrication=self.highlight_fabrication.get(),
            highlight_other=self.highlight_other.get()
        )
        
        input_file = filedialog.askopenfilename(
            title="Select KiCad PCB File",
            filetypes=[("KiCad PCB Files", "*.kicad_pcb")]
        )
        if not input_file:
            return
        
        output_file = filedialog.asksaveasfilename(
            title="Save Visualization",
            defaultextension=".png",
            filetypes=[("PNG Files", "*.png")]
        )
        if not output_file:
            return
        
        self.visualization_manager.generate_visualization(input_file, output_file, config)
    
    def _generate_output(self):
        """Generate manufacturing output."""
        config = OutputConfig(
            generate_gerber=self.generate_gerber.get(),
            generate_drill=self.generate_drill.get(),
            generate_3d=self.generate_3d.get(),
            generate_pdf=self.generate_pdf.get(),
            generate_bom=self.generate_bom.get(),
            generate_pick_and_place=self.generate_pick_and_place.get(),
            output_directory=self.output_dir.get()
        )
        
        input_file = filedialog.askopenfilename(
            title="Select KiCad PCB File",
            filetypes=[("KiCad PCB Files", "*.kicad_pcb")]
        )
        if not input_file:
            return
        
        self.output_manager.generate_output(input_file, config)
    
    def _cancel(self):
        """Cancel the operation."""
        self.frame.master.destroy()
    
    def show(self):
        """Show the manufacturing UI."""
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.frame.master.title("Manufacturing")
        self.frame.master.mainloop() 