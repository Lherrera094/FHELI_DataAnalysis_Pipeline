#Plot theoretical equations 

import scipy.constants as sp
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QPushButton, QComboBox, 
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QGroupBox, QCheckBox, QMessageBox,
    QTabWidget, QScrollArea, QWidget, QListWidget, QListWidgetItem, QTextEdit, QDialogButtonBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator
import numpy as np
import h5py
import re
from datetime import datetime

# Physical constants (SI units)
PHYSICAL_CONSTANTS = {
    'c':    2.99792458e8,           # Speed of light [m/s]
    'μ0':   4*np.pi*1e-7,           # Vacuum permeability [N/A²]
    'ε0':   8.8541878128e-12,       # Vacuum permittivity [F/m]
    'e':    1.602176634e-19,        # Elementary charge [C]
    'me':   9.1093837015e-31,       # Electron mass [kg]
    'mp':   1.67262192369e-27,      # Proton mass [kg]
    'h':    6.62607015e-34,         # Planck constant [J·s]
    'ħ':    1.054571817e-34,        # Reduced Planck constant [J·s]
    'kB':   1.380649e-23,           # Boltzmann constant [J/K]
    'NA':   6.02214076e23,          # Avogadro constant [1/mol]
    'G':    6.67430e-11             # Gravitational constant [N·m²/kg²]
}

class TheoreticalWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Theoretical Analysis")
        self.setGeometry(850, 50, 700, 900)
        
        # Reference to main window for accessing HDF5 data
        self.parent_window = parent
        self.plot_window = None
        self.theory_plots = []  # Store multiple theory plot datasets
        
        # Main layout with tabs
        self.tab_widget = QTabWidget()
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.setup_equation_tab()
        self.setup_plots_tab()
        
        # Initialize
        self.update_equation_ui()
    
    def setup_equation_tab(self):
        """Setup the equation definition tab."""
        self.eq_tab = QWidget()
        self.tab_widget.addTab(self.eq_tab, "Equation Setup")
        tab_layout = QVBoxLayout(self.eq_tab)
        
        # Scroll area for equation setup
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self.eq_scroll_layout = QVBoxLayout(content)
        
        # Equation selection with variable mapping
        self.equation_group = QGroupBox("Equation Selection and Parameters")
        self.equation_layout = QFormLayout()
        
        self.equation_combo = QComboBox()
        equations = [
            ("Plasma Parameters", "Calculates key plasma characteristics", 
            {"T":"Period [g.p.]", "n_e": "Electron density [Norm.]", 
             "B0": "Magnetic field [Norm.]", "N_i": "System size [g.p.]",},
            ["f0","T_e"] ),
            ("n-B Diagram", "(3.83*k*B0)/(r0*w*μ0*e)",                          # n-B Diagram
             {"T":"Period (grid points)", "r_0":"Ant. Radius"},
             ["f0", "k"]),                                                       # Additional required parameters

            ("Gaussian Pulse", "A*exp(-(x-x0)**2/(2*σ**2))", 
             {"A": "amplitude", "σ": "width", "x0": "center"},
             ["x_min", "x_max"]),
            ("Sinusoidal Wave", "A*sin(2π*f*x)", 
             {"A": "amplitude", "f": "frequency"},
             ["x_min", "x_max"]),
            ("Exponential Decay", "A*exp(-x/τ)", 
             {"A": "amplitude", "τ": "decay_time"},
             ["x_min", "x_max"]),
            ("Plane Wave", "A*exp(1j*k*x)", 
             {"A": "amplitude", "k": "wavenumber"},
             ["x_min", "x_max"])
        ]
        
        self.equation_info = {}
        for name, formula, var_map, req_params in equations:
            self.equation_combo.addItem(name)
            self.equation_info[name] = {
                "formula": formula, 
                "var_map": var_map,
                "required_params": req_params
            }
        
        self.equation_combo.currentTextChanged.connect(self.update_equation_ui)
        self.equation_layout.addRow("Equation:", self.equation_combo)
        
        # Variable mapping table (will be populated dynamically)
        self.variable_mapping_group = QGroupBox("Parameter Sources")
        self.variable_mapping_layout = QFormLayout()
        self.variable_mapping_group.setLayout(self.variable_mapping_layout)
        self.equation_layout.addRow(self.variable_mapping_group)
        
        # Equation display
        self.equation_display = QLabel()
        self.equation_layout.addRow("Current Equation:", self.equation_display)
        
        self.equation_group.setLayout(self.equation_layout)
        self.eq_scroll_layout.addWidget(self.equation_group)
        
        # Top button layout for constants and extraction
        self.top_button_layout = QHBoxLayout()
        
        # Physical constants button
        self.constants_button = QPushButton("Show Physical Constants", self)
        self.constants_button.clicked.connect(self.show_physical_constants)
        self.top_button_layout.addWidget(self.constants_button)
        
        # Extract parameters button
        self.extract_button = QPushButton("Extract Parameters from HDF5")
        self.extract_button.clicked.connect(self.extract_variables_from_hdf5)
        self.top_button_layout.addWidget(self.extract_button)
        
        self.eq_scroll_layout.addLayout(self.top_button_layout)
        
        # Parameter input section - will be populated dynamically
        self.param_group = QGroupBox("User input parameters")
        self.param_layout = QFormLayout()
        self.param_group.setLayout(self.param_layout)
        self.eq_scroll_layout.addWidget(self.param_group)
        
        # Manual parameter override section
        self.manual_params_group = QGroupBox("Manual Parameter Overrides")
        self.manual_params_layout = QFormLayout()
        self.manual_params = {}  # Will be populated in update_equation_ui
        self.manual_params_group.setLayout(self.manual_params_layout)
        self.eq_scroll_layout.addWidget(self.manual_params_group)
        
        # HDF5 variable extraction status
        self.extraction_status = QLabel("No parameters extracted yet")
        self.eq_scroll_layout.addWidget(self.extraction_status)
        
        # Action buttons
        self.action_buttons = QHBoxLayout()
        
        self.add_button = QPushButton("Compute/Add Plot")
        self.add_button.clicked.connect(self.add_theory_plot)
        self.action_buttons.addWidget(self.add_button)
        
        self.clear_button = QPushButton("Clear Parameters")
        self.clear_button.clicked.connect(self.clear_parameters)
        self.action_buttons.addWidget(self.clear_button)
        
        self.eq_scroll_layout.addLayout(self.action_buttons)
        
        # Set scroll content
        scroll.setWidget(content)
        tab_layout.addWidget(scroll)
    
    def setup_plots_tab(self):
        """Setup the plots management tab."""
        self.plots_tab = QWidget()
        self.tab_widget.addTab(self.plots_tab, "Plot Managing")
        layout = QVBoxLayout(self.plots_tab)
        
        # Plot list
        self.plot_list_group = QGroupBox("Saved Theory Plots")
        self.plot_list_layout = QVBoxLayout()
        
        self.plot_list_widget = QListWidget()
        self.plot_list_widget.itemSelectionChanged.connect(self.on_plot_selected)
        self.plot_list_layout.addWidget(self.plot_list_widget)
        
        # Plot actions
        self.plot_action_buttons = QHBoxLayout()
        
        self.plot_selected_button = QPushButton("Plot Selected")
        self.plot_selected_button.clicked.connect(self.plot_selected)
        self.plot_action_buttons.addWidget(self.plot_selected_button)
        
        self.plot_all_button = QPushButton("Plot All")
        self.plot_all_button.clicked.connect(self.plot_all)
        self.plot_action_buttons.addWidget(self.plot_all_button)
        
        self.remove_button = QPushButton("Remove Selected")
        self.remove_button.clicked.connect(self.remove_selected)
        self.plot_action_buttons.addWidget(self.remove_button)
        
        self.save_button = QPushButton("Save All to HDF5")
        self.save_button.clicked.connect(self.save_all_to_hdf5)
        self.plot_action_buttons.addWidget(self.save_button)
        
        self.plot_list_layout.addLayout(self.plot_action_buttons)
        self.plot_list_group.setLayout(self.plot_list_layout)
        layout.addWidget(self.plot_list_group)
        
        # Plot info display
        self.plot_info_group = QGroupBox("Plot Information")
        self.plot_info_layout = QFormLayout()
        
        self.plot_info_label = QLabel("No plot selected")
        self.plot_info_label.setWordWrap(True)
        self.plot_info_layout.addRow(self.plot_info_label)
        
        self.plot_info_group.setLayout(self.plot_info_layout)
        layout.addWidget(self.plot_info_group)
    
    def show_physical_constants(self):
        """Display a dialog with physical constants."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Physical Constants")
        dialog.setFixedSize(400, 500)
        
        layout = QVBoxLayout()
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        
        # Format constants for display
        constants_text = "<h3>Physical Constants (SI units)</h3><ul>"
        for name, value in PHYSICAL_CONSTANTS.items():
            constants_text += f"<li><b>{name}</b> = {value:.4e}</li>"
        constants_text += "</ul>"
        
        text_edit.setHtml(constants_text)
        layout.addWidget(text_edit)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.close)
        layout.addWidget(close_button)
        
        dialog.setLayout(layout)
        dialog.exec_()

    def calculate_plasma_parameters(self):
        """Calculate and display key plasma parameters."""
        if not hasattr(self, 'extracted_vars') or not self.extracted_vars:
            self.extract_variables_from_hdf5()
            if not hasattr(self, 'extracted_vars') or not self.extracted_vars:
                QMessageBox.warning(self, "Error", "No parameters extracted or entered")
                return None

        # Get required parameters with defaults
        T =     self.extracted_vars.get('T', 100)                   # grid_periods
        n_e =   self.extracted_vars.get('n_e', 1e16)                # m^-3
        B =     self.extracted_vars.get('B0', 0.1)                  # Tesla
        
        #Convert normalized simulation values to real system
        f0 =                self.parse_scientific_input(self.f0_input.text())
        wavelenght =        sp.c/f0
        ang_f =             2*np.pi*f0
        grid_point_value =  wavelenght/T
        space_resolution =  (T/2)/wavelenght

        Eq_n_e =            PHYSICAL_CONSTANTS['ε0']*PHYSICAL_CONSTANTS['me']*((ang_f)**2) / (PHYSICAL_CONSTANTS['e']**2)
        Eq_B0 =             PHYSICAL_CONSTANTS['me']*ang_f / PHYSICAL_CONSTANTS['e']

        n_e =               n_e * Eq_n_e                            # m^-3
        n_i =   n_e                                                 # m^-3
        B   =               B * Eq_B0                               # T

        # Convert T_e from eV to Kelvin
        T_e =               self.parse_scientific_input(self.Te_input.text())
        T_e_K =             T_e * 11604.525                                     # 1 eV = 11604.525 K
        
        # Calculate all plasma parameters
        params = {
            #Simulation parameters
            'Grid_point_size':                  grid_point_value,
            'Spatial Resolution':               space_resolution,
            'Equivalent_ne':                    Eq_n_e,
            'Equivalent_B0':                    Eq_B0,

            #Input parameters
            'input_Antenna_frequency':          f0,
            'input_Angular_frequency':          ang_f,
            'input_Electron_density':           n_e,
            'input_Magnetic_field':             B,
            'input_Electron_temperature_eV':    T_e,
            'input_Electron_temperature_K':     T_e_K,
            'input_Ion_density':                n_i,

            #Plasma parameters calculation
            'plasma_frequency':                 np.sqrt((PHYSICAL_CONSTANTS['e']**2 * n_e) / 
                                                    (PHYSICAL_CONSTANTS['ε0'] * PHYSICAL_CONSTANTS['me'])),
            'electron_cyclotron_frequency':     (PHYSICAL_CONSTANTS['e'] * B) / PHYSICAL_CONSTANTS['me'],
            'ion_cyclotron_frequency':          (PHYSICAL_CONSTANTS['e'] * B) / PHYSICAL_CONSTANTS['mp'],
            'debye_length':                     np.sqrt((PHYSICAL_CONSTANTS['ε0'] * PHYSICAL_CONSTANTS['kB'] * T_e_K) / 
                                                    (n_e * PHYSICAL_CONSTANTS['e']**2)),
            'electron_plasma_beta':             (2 * PHYSICAL_CONSTANTS['μ0'] * n_e * PHYSICAL_CONSTANTS['kB'] * T_e_K) / (B**2),
            'alfven_speed':                     B / np.sqrt(PHYSICAL_CONSTANTS['μ0'] * n_i * PHYSICAL_CONSTANTS['mp']),
            'electron_thermal_velocity':        np.sqrt(2 * PHYSICAL_CONSTANTS['kB'] * T_e_K / PHYSICAL_CONSTANTS['me']),
            'ion_thermal_velocity':             np.sqrt(2 * PHYSICAL_CONSTANTS['kB'] * T_e_K / PHYSICAL_CONSTANTS['mp']),
            'plasma_parameter':                 (4/3) * np.pi * n_e * 
                                                    (np.sqrt((PHYSICAL_CONSTANTS['ε0'] * PHYSICAL_CONSTANTS['kB'] * T_e_K) / 
                                                    (n_e * PHYSICAL_CONSTANTS['e']**2)))**3,

            #Helicon parameters computations
            'helicon_k_H':                      ang_f*PHYSICAL_CONSTANTS['μ0']*PHYSICAL_CONSTANTS['me']*n_e / B,
            'helicon_k_TG':                     ang_f / ((PHYSICAL_CONSTANTS['e'] * B) / PHYSICAL_CONSTANTS['me']),
            'helicon_k_max':                    PHYSICAL_CONSTANTS['e']*np.sqrt(PHYSICAL_CONSTANTS['μ0']*n_e*ang_f / 
                                                    (PHYSICAL_CONSTANTS['e']*B - PHYSICAL_CONSTANTS['me']*ang_f) ),
            'helicon_k_min':                    (2*ang_f)*np.sqrt(PHYSICAL_CONSTANTS['μ0']*PHYSICAL_CONSTANTS['me']*n_e) / B
            
        }
        
        return params
    
    def show_plasma_parameters_dialog(self, params):
        """Show the plasma parameters in a dialog with save option."""
        # Format the results for display
        result_text = "<h3>Plasma Parameters</h3><table>"
        result_text += "<tr><th>Parameter</th><th>Value</th><th>Units</th></tr>"
        
        units_map = {
            'plasma_frequency':             '1/s',
            'electron_cyclotron_frequency': '1/s',
            'debye_length':                 'm',
            'electron_plasma_beta':         '',
            'alfven_speed':                 'm/s',
            'electron_thermal_velocity':    'm/s',
            'ion_thermal_velocity':         'm/s',
            'plasma_parameter':             '',
            'Grid_point_size':              'm',
            'Spatial Resolution':           'g.p.',
            'Equivalent_ne':                'm^3',
            'Equivalent_B0':                'T',
            'helicon_k_H':                  '1/m',
            'helicon_k_TG':                 '1/m',
            'helicon_k_max':                '1/m',
            'helicon_k_min':                '1/m'
        }
        
        for name, value in params.items():
            if name.startswith('input_'):
                continue  # Skip input parameters in main table
                
            if 'frequency' in name:
                # Convert to appropriate units
                if value > 1e6:
                    disp_value = value / 1e6
                    unit = 'MHz'
                elif value > 1e3:
                    disp_value = value / 1e3
                    unit = 'kHz'
                else:
                    disp_value = value
                    unit = 'Hz'
                result_text += f"<tr><td>{name.replace('_', ' ').title()}</td><td>{disp_value:.4g}</td><td>{unit}</td></tr>"
            else:
                result_text += f"<tr><td>{name.replace('_', ' ').title()}</td><td>{value:.4e}</td><td>{units_map.get(name, '')}</td></tr>"
        
        result_text += "</table>"
        
        # Add input parameters
        result_text += "<h4>Input Parameters</h4><ul>"
        result_text += f"<li>Electron density:\t    {params['input_Electron_density']:.4e} m⁻³</li>"
        result_text += f"<li>Magnetic field:\t      {params['input_Magnetic_field']:.4g} T</li>"
        result_text += f"<li>Electron temperature:\t{params['input_Electron_temperature_eV']:.4g} eV ({params['input_Electron_temperature_K']:.4g} K)</li>"
        result_text += f"<li>Ion density:\t         {params['input_Ion_density']:.4e} m⁻³</li>"
        result_text += f"<li>Antenna frequency:\t   {params['input_Antenna_frequency']:.4e} Hz</li>"
        result_text += f"<li>Angular frequency:\t   {params['input_Angular_frequency']:.4e} 1/s</li>"
        result_text += "</ul>"
        
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Plasma Parameters")
        dialog.setMinimumSize(600, 500)
        
        layout = QVBoxLayout()
        
        # Display text
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setHtml(result_text)
        layout.addWidget(text_edit)
        
        # Save button
        btn_box = QDialogButtonBox()
        save_btn = btn_box.addButton("Save to HDF5", QDialogButtonBox.AcceptRole)
        close_btn = btn_box.addButton(QDialogButtonBox.Close)
    
        def save_parameters():
            self.save_plasma_parameters(params)
            QMessageBox.information(dialog, "Success", "Parameters saved to HDF5 file")
    
        save_btn.clicked.connect(save_parameters)
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(btn_box)
        
        dialog.setLayout(layout)
        dialog.exec_()

    def save_plasma_parameters(self, params):
        """Save plasma parameters to HDF5 file."""
        if not self.parent_window or not self.parent_window.file_path:
            QMessageBox.warning(self, "Error", "No HDF5 file loaded")
            return False
        
        try:
            with h5py.File(self.parent_window.file_path, 'a') as file:
                # Create or clear existing group
                if 'Plasma_parameters' in file:
                    del file['Plasma_parameters']
                elif 'plasma_parameters' in file:
                    del file['plasma_parameters']
                
                # Create new group and subgroups
                plasma_group = file.create_group('Plasma_parameters')
                inputs_group = plasma_group.create_group('Input_values')
                results_group = plasma_group.create_group('Main_plasma_parameters')
                helicon_group = plasma_group.create_group('Helicon_parameters')
                
                # Save calculated parameters
                for name, value in params.items():
                    if name.startswith('input_'):
                        continue                        # Skip input parameters here
                    elif name.startswith('helicon_'):
                        continue                        # Skip input parameters here
                    results_group.attrs[name] = value
                
                # Save input parameters
                inputs_group.attrs['Electron_density'] =        params['input_Electron_density']
                inputs_group.attrs['Magnetic_field'] =          params['input_Magnetic_field']
                inputs_group.attrs['Electron_temperature_eV'] = params['input_Electron_temperature_eV']
                inputs_group.attrs['Electron_temperature_K'] =  params['input_Electron_temperature_K']
                inputs_group.attrs['Ion_density'] =             params['input_Ion_density']
                inputs_group.attrs['Antenna_frequency'] =       params['input_Antenna_frequency']
                inputs_group.attrs['Angular_frequency'] =       params['input_Angular_frequency']

                helicon_group.attrs['k_H'] =                    params['helicon_k_H']
                helicon_group.attrs['k_TG'] =                   params['helicon_k_TG']
                helicon_group.attrs['k_max'] =                  params['helicon_k_max']
                helicon_group.attrs['k_min'] =                  params['helicon_k_min']
                
                return True
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save parameters: {str(e)}")
            return False

    def parse_scientific_input(self, text):
        """Parse a string input that could be in scientific notation with decimals"""
        text = text.strip().lower()
        
        # Handle empty string
        if not text:
            return 0.0
            
        # Replace common alternative representations
        text = (text.replace(' ', '')
                .replace('×10', 'e')
                .replace('x10', 'e')
                .replace('*10', 'e')
                .replace('^', 'e'))
        
        # Handle cases like "1.23e+5" or "1.23e5"
        try:
            return float(text)
        except ValueError:
            # Try to handle more complex cases if needed
            try:
                # Handle cases where 'e' might be missing (like "1.23+5")
                if '+' in text and 'e' not in text:
                    mantissa, exponent = text.split('+')
                    return float(mantissa) * (10 ** float(exponent))
                elif '-' in text and 'e' not in text and text[0] != '-':
                    mantissa, exponent = text.split('-')
                    return float(mantissa) * (10 ** -float(exponent))
            except:
                if hasattr(self, 'last_focused_input'):
                    self.last_focused_input.setStyleSheet("background-color: #ffdddd;")
                return 0.0
                
        # If all parsing fails, return 0.0 or show a warning
        QMessageBox.warning(self, "Input Error", 
                        f"Could not parse input value: {text}\nUsing 0.0 instead.")
        return 0.0

    def update_equation_ui(self):
        """Update the UI based on the selected equation."""
        # Clear previous variable mappings
        for i in reversed(range(self.variable_mapping_layout.rowCount())):
            self.variable_mapping_layout.removeRow(i)
        
        # Clear manual parameters
        for i in reversed(range(self.manual_params_layout.rowCount())):
            self.manual_params_layout.removeRow(i)
        
        # Clear plot parameters
        for i in reversed(range(self.param_layout.rowCount())):
            self.param_layout.removeRow(i)
        
        eq_name = self.equation_combo.currentText()
        eq_info = self.equation_info[eq_name]
        
        # Update equation display with LaTeX formatting
        latex_equations = {
            "Plasma Parameters": r"$\omega_p, \omega_c, \lambda_D, \beta, v_A$.",
            "n-B Diagram": r"$n = \frac{3.83 \cdot k \cdot B_0}{r_0 \cdot \omega}$",
            "Gaussian Pulse": r"$A e^{-\frac{(x-x_0)^2}{2\sigma^2}}$",
            "Sinusoidal Wave": r"$A \sin(2\pi f x)$",
            "Exponential Decay": r"$A e^{-x/\tau}$",
            "Plane Wave": r"$A e^{i k x}$"
        }

        eq_name = self.equation_combo.currentText()
        
        self.equation_display.setText(latex_equations[eq_name])
        self.equation_display.setTextFormat(Qt.RichText)
        
        # Create variable mapping inputs with default paths
        self.variable_widgets = {}
        self.manual_params = {}
        default_paths = {
            "N_i":  "config/N_x",
            "N_x":  "config/N_x",
            "N_y":  "config/N_y",
            "N_z":  "config/N_z",
            "T":    "config/period",
            "r_0":  "config/ant_radius",
            "L_0":  "config/ant_lenght",
            "n_e":  "n_e",
            "B0":   "B0z"
        }
        
        for var, desc in eq_info["var_map"].items():
            # HDF5 path input with default value
            label = QLabel(f"{var} ({desc}):")
            hdf5_path = QLineEdit()
            hdf5_path.setPlaceholderText(f"HDF5 path for {desc}")
            
            # Set default path if available
            if var in default_paths:
                hdf5_path.setText(default_paths[var])
            
            self.variable_mapping_layout.addRow(label, hdf5_path)
            self.variable_widgets[var] = hdf5_path
            
            # Manual override input
            manual_label = QLabel(f"Manual {var}:")
            manual_input = QDoubleSpinBox()
            manual_input.setRange(-1e6, 1e6)
            manual_input.setValue(1.0 if var == "A" else 0.0 if var in ["x0", "center"] else 1.0)
            manual_input.setEnabled(not hdf5_path.text().strip())
            self.manual_params_layout.addRow(manual_label, manual_input)
            self.manual_params[var] = manual_input
            
            # Connect to enable/disable manual input when HDF5 path is empty
            hdf5_path.textChanged.connect(lambda text, mi=manual_input: mi.setEnabled(not text.strip()))
        
        # Add equation-specific parameters
        for param in eq_info["required_params"]:
            if param == "f0":
                self.f0_input = QLineEdit()
                self.f0_input.setValidator(QDoubleValidator())
                self.f0_input.setText("1.0e9")  # Default 1 GHz in scientific notation
                #self.param_layout.addRow("Frequency (ω) [Hz]:", self.w_input)
                self.param_layout.addRow("Frequency (f0) [Hz]:", self.f0_input)
            elif param == "k":
                self.k_input = QLineEdit()
                self.k_input.setValidator(QDoubleValidator())
                self.k_input.setText("1e3")  # Default 1e3 m^-1 in scientific notation
                self.param_layout.addRow("Wavenumber (k) [m⁻¹]:", self.k_input)
            elif param == "T_e":
                self.Te_input = QLineEdit()
                self.Te_input.setValidator(QDoubleValidator())
                self.Te_input.setText("1")  # Default 1e3 m^-1 in scientific notation
                self.param_layout.addRow("Electron Temperature (T_e) [eV]:", self.Te_input)
            elif param == "x_min":
                self.x_min = QLineEdit()
                self.x_min.setValidator(QDoubleValidator())
                self.x_min.setText("0")
                self.param_layout.addRow("X min:", self.x_min)
            elif param == "x_max":
                self.x_max = QLineEdit()
                self.x_max.setValidator(QDoubleValidator())
                self.x_max.setText("100")
                self.param_layout.addRow("X max:", self.x_max)
    
    def extract_variables_from_hdf5(self):
        """Extract variables from HDF5 file, including max values from datasets."""
        if not self.parent_window or not self.parent_window.file_path:
            QMessageBox.warning(self, "Error", "No HDF5 file loaded")
            return
        
        self.extracted_vars = {}
        missing_vars = []
        
        try:
            with h5py.File(self.parent_window.file_path, 'r') as file:
                for var, widget in self.variable_widgets.items():
                    path = widget.text().strip()
                    manual_input = self.manual_params[var]
                    
                    # If manual input is enabled, use that value
                    if manual_input.isEnabled():
                        self.extracted_vars[var] = manual_input.value()
                        continue
                    
                    if not path:
                        missing_vars.append(var)
                        continue
                    
                    # Try to get the value from the HDF5 file
                    try:
                        # Handle special syntax for max value extraction
                        if path.startswith('max:'):
                            # Extract max value from dataset
                            dataset_path = path[4:]  # Remove 'max:' prefix
                            dataset = file[dataset_path]
                            
                            if not isinstance(dataset, h5py.Dataset):
                                raise ValueError(f"{dataset_path} is not a dataset")
                                
                            data = dataset[()]
                            
                            # Handle different dimensionalities
                            if data.ndim == 1:
                                value = np.max(data)
                            elif data.ndim == 2:
                                value = np.max(data)
                            elif data.ndim == 3:
                                value = np.max(data)
                            else:
                                raise ValueError(f"Cannot handle {data.ndim}D data")
                                
                            self.extracted_vars[var] = float(value)
                        
                        # Handle attribute access (e.g., "config:amplitude")
                        elif ":" in path:
                            group_path, attr_name = path.split(":")
                            obj = file[group_path]
                            value = obj.attrs[attr_name]
                            self.extracted_vars[var] = float(value)
                        
                        # Handle direct dataset access
                        else:
                            obj = file[path]
                            if isinstance(obj, h5py.Dataset):
                                if obj.size == 1:
                                    value = obj[()]
                                else:
                                    # For multi-value datasets, extract max if small enough
                                    value = np.max(obj[()])
                                    
                                self.extracted_vars[var] = float(value)
                            else:
                                raise ValueError(f"{path} is not a dataset")
                        
                        widget.setStyleSheet("")  # Clear error styling
                        
                    except Exception as e:
                        missing_vars.append(var)
                        widget.setStyleSheet("background-color: #ffdddd;")
                        print(f"Error extracting {var} from {path}: {e}")
        
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not read HDF5 file: {str(e)}")
            return
        
        # Update status
        status_msg = []
        if self.extracted_vars:
            status_msg.append("Extracted parameters:")
            for var, value in self.extracted_vars.items():
                source = self.variable_widgets[var].text()
                status_msg.append(f"  {var} = {value:.4g} (from {source})")
        
        if missing_vars:
            status_msg.append("\nMissing parameters:")
            status_msg.extend(f"  {var}" for var in missing_vars)
        
        self.extraction_status.setText("\n".join(status_msg))
        self.extraction_status.setStyleSheet("color: #aa0000;" if missing_vars else "color: #00aa00;")
    
    def generate_x_values(self):
        """Generate x-axis values based on user input."""
        eq_name = self.equation_combo.currentText()
        
        if eq_name in ["Gaussian Pulse", "Sinusoidal Wave", "Exponential Decay", "Plane Wave"]:
            x_min = self.parse_scientific_input(self.x_min.text())
            x_max = self.parse_scientific_input(self.x_max.text())
            num_points = 1000
            return np.linspace(x_min, x_max, num_points)
        elif eq_name == "n-B Diagram":
            # For n-B diagram, we might want to plot against frequency
            B0_min = 0                 # [Tesla]
            B0_max = 1  # 1 THz
            return np.linspace(B0_min, B0_max, 10000)
        else:
            return np.linspace(0, 100, 1000)
    
    def evaluate_equation(self, x):
        """Safely evaluate the selected equation at given x values."""
        eq_name = self.equation_combo.currentText()
        eq_info = self.equation_info[eq_name]

        if eq_name == "Plasma Parameters":
            params = self.calculate_plasma_parameters()
            if params is not None:
                self.show_plasma_parameters_dialog(params)
            return np.zeros_like(x)
        
        try:
            # Prepare the evaluation context
            context = {
                'np':   np,
                'x':    x,
                'B0':   x,
                'pi':   np.pi,
                'sqrt': np.sqrt,  # Add sqrt function
                'exp':  np.exp,    # Add exp function
                'sin':  np.sin,    # Add sin function
                **PHYSICAL_CONSTANTS
            }
            
            # Add equation-specific parameters
            if eq_name == "n-B Diagram":
                context['w'] = self.parse_scientific_input(self.f0_input.text())
                context['k'] = self.parse_scientific_input(self.k_input.text())
            
            # Add extracted variables
            context.update(self.extracted_vars)
            
            # Get the formula and ensure it's in Python syntax
            formula = eq_info["formula"]
            
            # Replace any remaining special characters
            formula = (formula
                    .replace('σ', 'sigma')
                    .replace('γ', 'gamma')
                    .replace('τ', 'tau')
                    .replace('ω', 'w')
                    .replace('λ', 'lambda'))
            
            # Safely evaluate the formula
            return eval(formula, {"__builtins__": None}, context)
            
        except Exception as e:
            QMessageBox.warning(self, "Error", 
                f"Could not evaluate {eq_name} equation: {str(e)}\n"
                f"Formula: {formula}\n"
                f"Context keys: {list(context.keys())}"
            )
            return np.zeros_like(x)
    
    def add_theory_plot(self):
        """Add the current theoretical plot to the list after getting a name from the user."""
        # First extract parameters if needed
        if not hasattr(self, 'extracted_vars') or not self.extracted_vars:
            self.extract_variables_from_hdf5()
            if not hasattr(self, 'extracted_vars') or not self.extracted_vars:
                QMessageBox.warning(self, "Error", "No parameters extracted or entered")
                return

        # Generate the plot data
        x = self.generate_x_values()
        y = self.evaluate_equation(x)

        # Get plot name from user
        dialog = QDialog(self)
        dialog.setWindowTitle("Name Your Plot")
        layout = QVBoxLayout()
        
        label = QLabel("Enter a name for this plot:")
        layout.addWidget(label)
        
        name_input = QLineEdit()
        default_name = f"{self.equation_combo.currentText()} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        name_input.setText(default_name)
        layout.addWidget(name_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec_() != QDialog.Accepted:
            return  # User cancelled
        
        plot_name = name_input.text().strip()
        if not plot_name:
            plot_name = default_name

        if any(p["name"] == plot_name for p in self.theory_plots):
            QMessageBox.warning(self, "Warning", "A plot with this name already exists!")
            return

        # Create plot info
        eq_name = self.equation_combo.currentText()
        formula = self.equation_info[eq_name]["formula"]
        
        plot_info = {
            "name": plot_name,
            "equation": eq_name,
            "formula": formula,
            "x": x,
            "y": y,
            "params": dict(self.extracted_vars)
        }
        
        # Add equation-specific parameters to plot info
        if eq_name == "n-B Diagram":
            plot_info["frequency"] = self.parse_scientific_input(self.f0_input.text())
            plot_info["wavenumber"] = self.parse_scientific_input(self.k_input.text())
        elif eq_name in ["Gaussian Pulse", "Sinusoidal Wave", "Exponential Decay", "Plane Wave"]:
            plot_info["x_min"] = self.parse_scientific_input(self.x_min.text())
            plot_info["x_max"] = self.parse_scientific_input(self.x_max.text())

        # Add to our list
        self.theory_plots.append(plot_info)
        
        # Update plot list
        self.update_plot_list()
        
        QMessageBox.information(self, "Success", f"Plot '{plot_name}' added to collection")
    
    def update_plot_list(self):
        """Update the list of saved theory plots."""
        self.plot_list_widget.clear()
        for plot in self.theory_plots:
            item = QListWidgetItem(plot["name"])
            item.setData(Qt.UserRole, plot)
            self.plot_list_widget.addItem(item)
    
    def on_plot_selected(self):
        """Show information about the selected plot."""
        selected = self.plot_list_widget.selectedItems()
        if not selected:
            self.plot_info_label.setText("No plot selected")
            return
        
        plot = selected[0].data(Qt.UserRole)
        info_text = (
            f"<b>Name:</b> {plot['name']}<br>"
            f"<b>Equation:</b> {plot['equation']}<br>"
            f"<b>Formula:</b> {plot['formula']}<br>"
            f"<b>Parameters:</b><br>"
        )
        
        for param, value in plot['params'].items():
            info_text += f"  {param} = {value:.4g}<br>"
        
        # Add equation-specific parameters to info display
        if plot['equation'] == "n-B Diagram":
            info_text += f"<b>Frequency:</b> {plot.get('frequency', 'N/A')} Hz<br>"
            info_text += f"<b>Wavenumber:</b> {plot.get('wavenumber', 'N/A')} m⁻¹<br>"
        elif plot['equation'] in ["Gaussian Pulse", "Sinusoidal Wave", "Exponential Decay", "Plane Wave"]:
            info_text += f"<b>X range:</b> {plot.get('x_min', 'N/A')} to {plot.get('x_max', 'N/A')}<br>"
        
        self.plot_info_label.setText(info_text)

    def plot_selected(self):
        """Plot the selected theory plots."""
        selected = self.plot_list_widget.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Warning", "No plots selected")
            return
        
        # Create or reuse plot window
        if not hasattr(self, 'plot_window') or self.plot_window is None:
            from plot_window import PlotWindow
            self.plot_window = PlotWindow(self.parent_window)
        
        # Clear previous datasets
        self.plot_window.datasets = {}
        self.plot_window.dataset_list.clear()
        self.plot_window.data = None
        self.plot_window.dataset_type = '1D'
        
        # Add each selected plot
        for item in selected:
            plot = item.data(Qt.UserRole)
            self.plot_window.datasets[plot["name"]] = {
                'data': plot["y"],
                'color': 'blue',
                'style': '-',
                'label': plot["name"],
                'width': 2
            }
        
        # Use the first plot's x values
        if selected:
            first_plot = selected[0].data(Qt.UserRole)
            self.plot_window.data = first_plot["y"]
        
        # Configure and show plot window
        self.plot_window.update_plot()
        self.plot_window.show()
    
    def plot_all(self):
        """Plot all theory plots."""
        if not self.theory_plots:
            QMessageBox.warning(self, "Warning", "No plots to display")
            return
        
        # Create or reuse plot window
        if not hasattr(self, 'plot_window') or self.plot_window is None:
            from plot_window import PlotWindow
            self.plot_window = PlotWindow(self.parent_window)
        
        # Clear previous datasets
        self.plot_window.datasets = {}
        self.plot_window.dataset_list.clear()
        self.plot_window.data = None
        self.plot_window.dataset_type = '1D'
        
        # Add all plots
        for plot in self.theory_plots:
            self.plot_window.datasets[plot["name"]] = {
                'data': plot["y"],
                'color': 'blue',
                'style': '-',
                'label': plot["name"],
                'width': 2
            }
        
        # Use the first plot's x values
        if self.theory_plots:
            self.plot_window.data = self.theory_plots[0]["y"]
        
        # Configure and show plot window
        self.plot_window.update_plot()
        self.plot_window.show()
    
    def remove_selected(self):
        """Remove selected theory plots."""
        selected = self.plot_list_widget.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Warning", "No plots selected")
            return
        
        for item in selected:
            plot = item.data(Qt.UserRole)
            self.theory_plots.remove(plot)
        
        self.update_plot_list()
    
    def clear_parameters(self):
        """Clear all parameter inputs."""
        for widget in self.variable_widgets.values():
            widget.clear()
            widget.setStyleSheet("")
        
        for input in self.manual_params.values():
            input.setValue(0.0)
        
        self.extraction_status.setText("No parameters extracted yet")
        self.extraction_status.setStyleSheet("")
        
        if hasattr(self, 'extracted_vars'):
            del self.extracted_vars
    
    def save_all_to_hdf5(self):
        """Save all theory plots to the HDF5 file."""
        if not self.theory_plots:
            QMessageBox.warning(self, "Error", "No theory plots to save")
            return
            
        if not self.parent_window or not self.parent_window.file_path:
            QMessageBox.warning(self, "Error", "No HDF5 file loaded")
            return
        
        try:
            with h5py.File(self.parent_window.file_path, 'a') as file:
                # Create or clear theory group
                if 'theory' in file:
                    del file['theory']
                theory_group = file.create_group('theory')
                
                # Save each plot
                for plot in self.theory_plots:
                    # Create a sanitized name for the dataset
                    safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', plot["name"])
                    dataset = theory_group.create_dataset(safe_name, data=plot["y"])
                    
                    # Save x values
                    theory_group.create_dataset(f"{safe_name}_x", data=plot["x"])
                    
                    # Save metadata as attributes
                    dataset.attrs['name'] = plot["name"]
                    dataset.attrs['equation'] = plot["equation"]
                    dataset.attrs['formula'] = plot["formula"]
                    
                    # Save parameters
                    for param, value in plot["params"].items():
                        dataset.attrs[f'param_{param}'] = value
                    
                    # Save equation-specific parameters
                    if plot['equation'] == "n-B Diagram":
                        dataset.attrs['frequency'] = plot.get('frequency', 0)
                        dataset.attrs['wavenumber'] = plot.get('wavenumber', 0)
                    elif plot['equation'] in ["Gaussian Pulse", "Sinusoidal Wave", "Exponential Decay", "Plane Wave"]:
                        dataset.attrs['x_min'] = plot.get('x_min', 0)
                        dataset.attrs['x_max'] = plot.get('x_max', 0)
                
                QMessageBox.information(self, "Success", 
                    f"Saved {len(self.theory_plots)} theory plots to HDF5 file\n"
                    f"Path: /theory"
                )
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not save to HDF5: {str(e)}")
