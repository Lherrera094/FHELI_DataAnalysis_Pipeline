#Plot theoretical equations 
import scipy.constants as sp
import scipy.special as sc

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
        self.setGeometry(850, 50, 700, 950)
        
        # Reference to main window for accessing HDF5 data
        self.plasma_params = None                           # High level dictionary to save computed plasma parameters
        self.parent_window = parent                         #Calls for parent window: main_hdf5
        self.plot_window = None
        self.theory_plots = []                              # Store multiple theory plot datasets
        
        # Main layout with tabs
        self.tab_widget = QTabWidget()
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.setup_equation_tab()
        self.setup_plots_tab()
        
        # Initialize
        self.update_equation_ui()
    
#--------------------------------------------- Set Tabs Functions --------------------------------------------------------
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
            ("Plasma Parameters", "Calculates key plasma characteristics",                  # Plasma parameters
            {"T":"Period [g.p.]", "n_e": "Electron density [Norm.]", "B0": "Magnetic field [Norm.]", 
             "N_i": "System size [g.p.]","r_a":"Antenna radius [g.p.]", "L_a":"Antenna Lenght [g.p.]"},
             ["f0","T_e","m"],  False ),

            #Series of functions for helicon waves
            ("Wave_components(Helicon)", "W_", 
            {"T":"Period [g.p.]", "n_e": "Electron density [Norm.]", "B0": "Magnetic field [Norm.]"},
            [ ],            True ),
            
            ("k-beta Curve", "(delta/beta)*(beta**2 + K_s**2)",                             # k-beta curves
            {"T":"Period [g.p.]", "n_e": "Electron density [Norm.]", "B0": "Magnetic field [Norm.]"},
            [ ],            False ), 

            ("k_boundaries", "Computes boundary values for k eigenvalue",                   # Maximum value of K
            {"T":"Period [g.p.]", "n_e": "Electron density [Norm.]", "B0": "Magnetic field [Norm.]"},
            [ ],            True ),

            ("k_eigenvalues(cond.)", "Finds the k eigenvalues for helicon waves in conduncting boundaries", 
            {"T":"Period [g.p.]", "n_e": "Electron density [Norm.]", "B0": "Magnetic field [Norm.]"},
            [ ],            True ),

            ("k_eigenvalues(Insu.)", "Finds the k eigenvalues for helicon waves in conduncting boundaries", 
            {"T":"Period [g.p.]", "n_e": "Electron density [Norm.]", "B0": "Magnetic field [Norm.]"},
            [ ],            True ),

            ("Dispersion_Relation", "R/L_O/X_mode", 
            {"T":"Period [g.p.]", "n_e": "Electron density [Norm.]", "B0": "Magnetic field [Norm.]"},
            [ ],            True ),

            ("Sinusoidal_Wave", "A*sin(2π*f*x)", 
             {"T":"Period [g.p.]"}, ["Amplitud","t_end"],        False)
        ]
        
        self.equation_info = {}
        for name, formula, var_map, req_params, multi_ds in equations:
            self.equation_combo.addItem(name)
            self.equation_info[name] = {
                "formula": formula, 
                "var_map": var_map,
                "required_params": req_params,
                "multi_dataset": multi_ds
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
        self.manual_params = {}                             # Will be populated in update_equation_ui
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
    
#----------------------------------------- Physical Constants Window ---------------------------------------------------------    
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

#----------------------------------- Plasma Parameters Computation functions --------------------------------------------------
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
        r_a =   self.extracted_vars.get('r_a', 0.1)                 # grid points
        L_a =   self.extracted_vars.get('L_a', 0.1)                 # grid points
        m =     self.extracted_vars.get('m', 0)                     # Antenna mode
        
        #Convert normalized simulation values to real system
        f0 =                self.parse_scientific_input(self.f0_input.text())
        wavelenght =        sp.c/f0
        ang_f =             2*np.pi*f0
        grid_point_value =  wavelenght/T
        space_resolution =  (T/2)/wavelenght

        r_a =               r_a*grid_point_value
        L_a =               L_a*grid_point_value
        m =                 self.parse_scientific_input(self.m_input.text())
        k =                 2*np.pi/L_a
        Eq_n_e =            sp.epsilon_0 * sp.m_e * ((ang_f)**2) / (sp.e**2)
        Eq_B0 =             sp.m_e * ang_f / sp.e

        n_e =               n_e * Eq_n_e                            # m^-3
        n_i =               n_e                                     # m^-3
        B   =               B * Eq_B0                               # T

        # Convert T_e from eV to Kelvin
        T_e =               self.parse_scientific_input(self.Te_input.text())
        T_e_K =             T_e * 11604.525                                     # 1 eV = 11604.525 K
        
        # Calculate all plasma parameters
        params = {
            #Simulation parameters
            'Grid_point_size':                  grid_point_value,
            'Spatial_resolution':               space_resolution,
            'Equivalent_ne':                    Eq_n_e,
            'Equivalent_B0':                    Eq_B0,
            'Antenna_radius':                   r_a,
            'Antenna_lenght':                   L_a,
            'm':                                m,

            #Input parameters
            'Antenna_frequency':                f0,
            'Angular_frequency':                ang_f,
            'Electron_density':                 n_e,
            'Magnetic_field':                   B,
            'Electron_temperature_eV':          T_e,
            'Electron_temperature_K':           T_e_K,
            'Ion_density':                      n_i,

            #Plasma parameters calculation
            'plasma_frequency':                 np.sqrt((sp.e**2 * n_e) / (sp.epsilon_0 * sp.m_e)),
            'electron_cyclotron_frequency':     (sp.e * B) / sp.m_e,
            'ion_cyclotron_frequency':          (sp.e * B) / sp.m_p,
            'debye_length':                     np.sqrt((sp.epsilon_0 * sp.k * T_e_K) / (n_e * sp.e**2)),
            'electron_plasma_beta':             (2 * sp.mu_0 * n_e * sp.k * T_e_K) / (B**2),
            'alfven_speed':                     B / np.sqrt(sp.mu_0 * n_i * sp.m_p),
            'electron_thermal_velocity':        np.sqrt(2 * sp.k * T_e_K / sp.m_e),
            'ion_thermal_velocity':             np.sqrt(2 * sp.k * T_e_K / sp.m_p),
            'plasma_parameter':                 (4/3) * np.pi * n_e * (np.sqrt((sp.epsilon_0 * sp.k * T_e_K) / 
                                                    (n_e * sp.e**2)))**3,

            #Helicon parameters computations
            'k':                                k,
            'k_w':                              ang_f * sp.mu_0 * sp.e * n_e / B,               #whistler wavenumber
            'delta':                            ang_f / ((sp.e * B) / sp.m_e),                  #TG wavenumber
            'k_max':                            sp.e * np.sqrt(sp.mu_0 * n_e *ang_f / (sp.e*B - sp.m_e*ang_f) ),
            'k_min':                            (2*ang_f)*np.sqrt(sp.mu_0 * sp.m_e*n_e) / B,
            'beta_H':                           ang_f * sp.mu_0 * sp.e * n_e / (B*k),
            'beta_TG':                          k/(ang_f / ((sp.e * B) / sp.m_e)),
            'T_H':                              (ang_f * sp.mu_0 * sp.e * n_e / (B*k))**2 - k**2,
            'T_TG':                             np.sqrt( (k/(ang_f / ((sp.e * B) / sp.m_e)))**2 - k**2)
        }        
        
        return params
    
    def show_plasma_parameters_dialog(self, params):
        """Show the plasma parameters in a dialog with save option."""
        # Store parameters in the class variable
        self.plasma_params = params
        
        # Rest of the existing method remains the same...
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
            'Equivalent_ne':                'm^-3',
            'Equivalent_B0':                'T',
            'k_w':                          'm^2',
            'delta':                        '',
            'k_max':                        '1/m',
            'k_min':                        '1/m',
            'beta_H':                       'm',
            'beta_TG':                      'm',
            'T_H':                          'm',
            'T_TG':                         'm',
            'Antenna_radius':               'm',
            'Antenna_lenght':               'm'
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
        result_text += f"<li>Electron density:\t    {params['Electron_density']:.4e} m⁻³</li>"
        result_text += f"<li>Magnetic field:\t      {params['Magnetic_field']:.4g} T</li>"
        result_text += f"<li>Electron temperature:\t{params['Electron_temperature_eV']:.4g} eV ({params['Electron_temperature_K']:.4g} K)</li>"
        result_text += f"<li>Ion density:\t         {params['Ion_density']:.4e} m⁻³</li>"
        result_text += f"<li>Antenna frequency:\t   {params['Antenna_frequency']:.4e} Hz</li>"
        result_text += f"<li>Angular frequency:\t   {params['Angular_frequency']:.4e} 1/s</li>"
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
                if 'Theory_plasma_parameters' in file:
                    del file['Theory_plasma_parameters']
                
                # Create new group and subgroups
                plasma_group =          file.create_group('Theory_plasma_parameters')
                inputs_group =          plasma_group.create_group('Input_values')
                results_group =         plasma_group.create_group('Main_plasma')
                helicon_group =         plasma_group.create_group('Helicon')
                simulation_group =      plasma_group.create_group('Simulation_values')
                
                # Save main plasma values
                results_group.attrs['Plasma_frequency [s^-1]'] =                params['plasma_frequency']
                results_group.attrs['Electron_cyclotron_frequency [s^-1]'] =    params['electron_cyclotron_frequency']
                results_group.attrs['ion_cyclotron_frequency [s^-1]'] =         params['ion_cyclotron_frequency']
                results_group.attrs['debye_length [m]'] =                       params['debye_length']
                results_group.attrs['electron_plasma_beta'] =                   params['electron_plasma_beta']
                results_group.attrs['alfven_speed [m/s]'] =                     params['alfven_speed']
                results_group.attrs['electron_thermal_velocity [m/s]'] =        params['electron_thermal_velocity']
                results_group.attrs['ion_thermal_velocity [m/s]'] =             params['ion_thermal_velocity']
                results_group.attrs['plasma_parameter'] =                       params['plasma_parameter']

                # Save Input parameters
                inputs_group.attrs['Electron_density [m^-3]'] =                 params['Electron_density']
                inputs_group.attrs['Magnetic_field [T]'] =                      params['Magnetic_field']
                inputs_group.attrs['Electron_temperature [eV]'] =               params['Electron_temperature_eV']
                inputs_group.attrs['Electron_temperature [K]'] =                params['Electron_temperature_K']
                inputs_group.attrs['Ion_density [m^-3]'] =                      params['Ion_density']
                inputs_group.attrs['Antenna_frequency [Hz]'] =                  params['Antenna_frequency']
                inputs_group.attrs['Angular_frequency [s^-1]'] =                params['Angular_frequency']

                # Save Helicon values
                helicon_group.attrs['k [m^-1]'] =                               params['k']
                helicon_group.attrs['k_w [m^2]'] =                              params['k_w']
                helicon_group.attrs['delta'] =                                  params['delta']
                helicon_group.attrs['k_max [m^-3]'] =                           params['k_max']
                helicon_group.attrs['k_min [m^-3]'] =                           params['k_min']
                helicon_group.attrs['beta_H [m]'] =                             params['beta_H']
                helicon_group.attrs['beta_TG [m]'] =                            params['beta_TG']
                helicon_group.attrs['T_H [m]'] =                                params['T_H']
                helicon_group.attrs['T_TG [m]'] =                               params['T_TG']
                helicon_group.attrs['m [mode]'] =                               params['m']

                #Save simulation values
                simulation_group.attrs['Grid_point_size [m]'] =                 params['Grid_point_size']
                simulation_group.attrs['Spatial_resolution [g.p]'] =            params['Spatial_resolution']
                simulation_group.attrs['Equivalent_ne [m^-3]'] =                params['Equivalent_ne']
                simulation_group.attrs['Equivalent_B0 [T]'] =                   params['Equivalent_B0']
                simulation_group.attrs['Antenna_radius [cm]'] =                 params['Antenna_radius']*100
                simulation_group.attrs['Antenna_lenght [cm]'] =                 params['Antenna_lenght']*100
                
                return True
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save parameters: {str(e)}")
            return False

#--------------------------------------------- Evaluate Equations ------------------------------------------------------------
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
            "Plasma Parameters":        r"$\omega_p, \omega_c, \lambda_D, \beta, v_A$.",
            "k-beta Curve":             r"$\frac{\delta/\beta}\cdot{(\beta^2+k_s^2)}$",
            "k_boundaries" :            r"$2 * delta * k_s$ , $sqrt(delta/(1-delta)) * k_s$",
            "k_eigenvalues(cond.)":     r"$Eigenvalue_solver(Conduct.)$",
            "Wave_components(Helicon)": r"$Helicon_wave_components$",
            "k_eigenvalues(Insu.)":     r"$Eigenvalue_solver(Insulat.)$",
            "Dispersion_Relation":      r"R/L_O/X_modes",
            "n-B Diagram":              r"$n = \frac{3.83 \cdot k \cdot B_0}{r_0 \cdot \omega}$",
            "Sinusoidal_Wave":          r"$A \sin(2\pi f x)$"
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
            "T"  :  "config/period",
            "r_a":  "config/ant_radius",
            "L_a":  "config/ant_lenght",
            "n_e":  "n_e",
            "B0" :  "B0z"
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
                self.Te_input.setText("5")  # Default 1e3 m^-1 in scientific notation
                self.param_layout.addRow("Electron Temperature (T_e) [eV]:", self.Te_input)
            elif param == "m":
                self.m_input = QLineEdit()
                self.m_input.setValidator(QDoubleValidator())
                self.m_input.setText("0")  # Default 1e3 m^-1 in scientific notation
                self.param_layout.addRow("Antenna mode (m):", self.m_input)
            elif param == "t_end":
                self.t_input = QLineEdit()
                self.t_input.setValidator(QDoubleValidator())
                self.t_input.setText("0")  # Default 1e3 m^-1 in scientific notation
                self.param_layout.addRow("Studied number of periods (t_end):", self.t_input)
            elif param == "Amplitud":
                self.A_input = QLineEdit()
                self.A_input.setValidator(QDoubleValidator())
                self.A_input.setText("1")  # Default 1e3 m^-1 in scientific notation
                self.param_layout.addRow("Wave Amplitude:", self.A_input)
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
        
        if eq_name in ["Gaussian Pulse", "Exponential Decay", "Plane Wave"]:
            x_min = self.parse_scientific_input(self.x_min.text())
            x_max = self.parse_scientific_input(self.x_max.text())
            num_points = 1000
            return np.linspace(x_min, x_max, num_points)
        elif eq_name == "k-beta Curve":
            # For k-beta curve, plot is made agains beta value.
            beta_0 = 1                      # wavenumber
            beta_1 = 500                    # wavenumber
            return np.linspace(beta_0, beta_1, 3001)
        
        elif eq_name == "k_boundaries":
            # For k_max, plot is made against the frequency value.
            w0 = 0                           # frequency (Hz)
            w1 = 60000000                    # frequency (Hz)
            return np.linspace(w0, w1, 50000)
        
        elif eq_name == "k_eigenvalues(cond.)":
            # For k_max, plot is made against the frequency value.
            ki = self.plasma_params["k_min"]                # frequency (Hz)
            kf = self.plasma_params["k_max"]                # frequency (Hz)
            return np.linspace(ki, kf, 1000)

        elif eq_name == "k_eigenvalues(Insu.)":
            # For k_max, plot is made against the frequency value.
            ki = self.plasma_params["k_min"]                # frequency (Hz)
            kf = self.plasma_params["k_max"]                # frequency (Hz)
            return np.linspace(ki, kf, 1000)

        elif eq_name == "Wave_components(Helicon)":
            # For k_max, plot is made against the frequency value.
            ri = 0.0                                                    
            rf = self.plasma_params["Antenna_radius"] - self.plasma_params["Grid_point_size"]   # antenna radius
            return np.linspace(ri, rf, 1000)

        elif eq_name == "Dispersion_Relation":
            # For k_max, plot is made against the frequency value.
            w0 = 0.0                                                    
            w1 = 2*np.pi*1e9   # antenna radius
            return np.linspace(w0, w1, 500000)
        
        elif eq_name == "Sinusoidal_Wave":
            # For n-B diagram, we might want to plot against frequency
            T =     self.extracted_vars.get('T', 100)
            t =     self.parse_scientific_input(self.t_input.text())
            t_0 =   0                 # [Tesla]
            t_1 =   T * t
            return np.linspace(t_0, t_1, 50000)

        elif eq_name == "n-B Diagram":
            # For n-B diagram, we might want to plot against frequency
            B0_min = 0                  # [Tesla]
            B0_max = 1                  # 1 THz
            return np.linspace(B0_min, B0_max, 10000)
        
        else:
            return np.linspace(0, 100, 1000)
    
    def evaluate_equation(self, x):
        """Safely evaluate the selected equation at given x values."""
        eq_name = self.equation_combo.currentText()
        eq_info = self.equation_info[eq_name]

        try:
            if   eq_name == "Plasma Parameters":
                params = self.calculate_plasma_parameters()
                if params is not None:
                    self.show_plasma_parameters_dialog(params)
                return np.zeros_like(x)
            
            elif eq_name == "k-beta Curve":
                # For n-B diagram, we might want to plot against frequency
                delta = self.plasma_params["Angular_frequency"] / self.plasma_params["electron_cyclotron_frequency"]
                k =     (delta / x) * ( x**2 + (self.plasma_params["plasma_frequency"]/sp.c)**2 )
                return k
            
            elif eq_name == "k_boundaries":
                # For n-B diagram, we might want to plot against frequency
                delta =     x / self.plasma_params["electron_cyclotron_frequency"]
                k_min =     2 * delta * (self.plasma_params["plasma_frequency"]/sp.c) 
                k_max =     np.sqrt( delta / (1 - delta) ) * (self.plasma_params["plasma_frequency"]/sp.c)
                return {"k_min": k_min, "k_max": k_max}
            
            elif eq_name == "k_eigenvalues(cond.)":
                # For n-B diagram, we might want to plot against frequency
                m = self.plasma_params["m"]
                a = self.plasma_params["Antenna_radius"]

                beta_1 =    self.plasma_params["k_w"] / x
                beta_2 =    x / self.plasma_params["delta"]
                T_1    =    np.sqrt( beta_1**2 - x**2 )
                T_2    =    np.sqrt( beta_2**2 - x**2 )

                LHS =       (beta_1 + x)*sc.jv(m-1, T_1*a) + (beta_1 - x)*sc.jv(m+1, T_1*a) 
                RHS =       ( (beta_2 + x)*sc.jv(m-1, T_2*a) + (beta_2 - x)*sc.jv(m+1, T_2*a) )*( 
                              (beta_1*T_1*sc.jv(m, T_1*a)) / (beta_2*T_2*sc.jv(m, T_2*a)) )
                return {"LHS": LHS, "RHS": RHS}

            elif eq_name == "Wave_components(Helicon)":
                # For n-B diagram, we might want to plot against frequency
                k = 2*np.pi/self.plasma_params["Antenna_lenght"]
                m = self.plasma_params["m"]
                w = self.plasma_params["Angular_frequency"]
                n = self.plasma_params["Electron_density"]
                a = self.plasma_params["Antenna_radius"]

                beta_1 =    self.plasma_params["k_w"] / k
                beta_2 =    k / self.plasma_params["delta"]
                T_1    =    np.sqrt( beta_1**2 - k**2 )
                T_2    =    np.sqrt( beta_2**2 - k**2 )

                #Magnetic field wave components
                B_rH   =    (beta_1 + k)*sc.jv(m-1, T_1*x) + (beta_1 - k)*sc.jv(m+1, T_1*x) 
                B_thH  =    (beta_1 + k)*sc.jv(m-1, T_1*x) - (beta_1 - k)*sc.jv(m+1, T_1*x)
                B_zH   =    2*T_1*sc.jv(m, T_1*x)

                B_rTG  =    (beta_2 + k)*sc.jv(m-1, T_2*x) + (beta_2 - k)*sc.jv(m+1, T_2*x) 
                B_thTG =    (beta_2 + k)*sc.jv(m-1, T_2*x) - (beta_2 - k)*sc.jv(m+1, T_2*x)
                B_zTG  =    2*T_2*sc.jv(m, T_2*x)

                B_rT, B_thT, B_zT =    B_rH + B_rTG, B_thH + B_thTG, B_zH + B_zTG
                Ar, Ath, Az = B_rT.max(), B_thT.max(), B_zT.max()

                #Electric field wave components
                E_zH   = (w*sp.m_e*beta_1/(sp.e**2 * sp.mu_0 * n))*B_zH
                dE_zH  = (w*sp.m_e*beta_1**2/(sp.e**2 * sp.mu_0 * n))*( sc.jv(m-1, T_1*x) - sc.jv(m+1, T_1*x) )
                E_thH  = (m/(k))*E_zH - (w/k)*B_rH 
                E_rH   = (w/k)*B_thH + (beta_1/k)*dE_zH

                E_zTG   = (w*sp.m_e*beta_2/(sp.e**2 * sp.mu_0 * n))*B_zTG
                dE_zTG  = (w*sp.m_e*beta_2**2/(sp.e**2 * sp.mu_0 * n))*( sc.jv(m-1, T_2*x) - sc.jv(m+1, T_2*x) )
                E_thTG  = (m/(k))*E_zTG - (w/k)*B_rTG 
                E_rTG   = (w/k)*B_thTG + (beta_2/k)*dE_zTG

                E_rT, E_thT, E_zT =    E_rH + E_rTG, E_thH + E_thTG, E_zH + E_zTG
                Cr, Cth, Cz = E_rT.max(), E_thT.max(), E_zT.max()

                #Plasma current density components
                J_rH   =    (beta_1/sp.mu_0)*B_rH 
                J_thH  =    (beta_1/sp.mu_0)*B_thH
                J_zH   =    (beta_1/sp.mu_0)*B_zH

                J_rTG  =    (beta_2/sp.mu_0)*B_rTG 
                J_thTG =    (beta_2/sp.mu_0)*B_thTG
                J_zTG  =    (beta_2/sp.mu_0)*B_zTG

                J_rT, J_thT, J_zT =    J_rH + J_rTG, J_thH + J_thTG, J_zH + J_zTG
                Hr, Hth, Hz = J_rT.max(), J_thT.max(), J_zT.max()

                return { "B_rH":  B_rH/Ar,  "B_thH":  B_thH/Ath,  "B_zH":  B_zH/Az,             #Magnetic Components(Norm.)
                         "B_rTG": B_rTG/Ar, "B_thTG": B_thTG/Ath, "B_zTG": B_zTG/Az,
                         "B_rT":  B_rT/Ar,  "B_thT":  B_thT/Ath,  "B_zT":  B_zT/Az,
                         "E_rH":  E_rH/Cr,  "E_thH":  E_thH/Cth,  "E_zH":  E_zH/Cz,             #Electric Components(Norm.)
                         "E_rTG": E_zTG/Cr, "E_thTG": E_thTG/Cth, "E_zTG": E_rTG/Cz,
                         "E_rT":  E_rT/Cr,  "E_thT":  E_thT/Cth,  "E_zT":  E_zT/Cz,
                         "J_rH":  J_rH/Hr,  "J_thH":  J_thH/Hth,  "J_zH":  J_zH/Hz,             #Current Components(Norm.)
                         "J_rTG": J_rTG/Hr, "J_thTG": J_thTG/Hth, "J_zTG": J_zTG/Hz,
                         "J_rT":  J_rT/Hr,  "J_thT":  J_thT/Hth,  "J_zT":  J_zT/Hz  }

            elif eq_name == "k_eigenvalues(Insu.)":
                # For n-B diagram, we might want to plot against frequency
                k =     2*np.pi/self.plasma_params["Antenna_lenght"]
                a =     self.plasma_params["Antenna_radius"]
                m =     self.plasma_params["m"]
                w =     self.plasma_params["Angular_frequency"]
                w_p =   self.plasma_params["plasma_frequency"]

                beta_1 =    self.plasma_params["k_w"] / x
                beta_2 =    x / self.plasma_params["delta"]
                T_1    =    np.sqrt( beta_1**2 - x**2 )
                T_2    =    np.sqrt( beta_2**2 - x**2 )
                T_3    =    k**2 - (w/sp.c)**2 
                l      =    (w/sp.c)**2/( k * (w_p/sp.c)**2 )

                f_1    =    (beta_1 + k)*sc.jv(m-1, T_1*a)/sc.jv(m-1, T_3*a)
                g_1    =    (beta_1 - k)*sc.jv(m+1, T_1*a)/sc.jv(m+1, T_3*a)
                h_1    =    (2*k*T_1/T_3)*sc.jv(m, T_1*a)/sc.jv(m, T_3*a)

                f_2    =    (beta_2 + k)*sc.jv(m-1, T_2*a)/sc.jv(m-1, T_3*a)
                g_2    =    (beta_2 - k)*sc.jv(m+1, T_2*a)/sc.jv(m+1, T_3*a)
                h_2    =    (2*k*T_2/T_3)*sc.jv(m, T_2*a)/sc.jv(m, T_3*a)

                LHS =       (f_1 + g_1 - h_1)/(f_2 + g_2 - h_2)
                RHS =       (f_1 - g_1 + l*beta_1*h_1)/(f_2 - g_2 + l*beta_2*h_2)

                return {"LHS": LHS, "RHS": RHS}

            elif eq_name == "Dispersion_Relation":
                # For n-B diagram, we might want to plot against frequency
                w_c =   self.plasma_params["electron_cyclotron_frequency"]
                w_p =   self.plasma_params["plasma_frequency"]
                w_h =   np.sqrt(w_p**2 + w_c**2)
            
                k_R2 =      (x**2/sp.c**2) - (w_p**2/sp.c**2)/(1 - (w_c/x) )
                k_R =       np.where( np.isreal(np.sqrt(k_R2)), np.sqrt(k_R2), np.nan )
                k_L2 =      (x**2/sp.c**2) - (w_p**2/sp.c**2)/(1 + (w_c/x) )
                k_L =       np.where( np.isreal(np.sqrt(k_L2)), np.sqrt(k_L2), np.nan )
                k_O2 =      (x**2 - w_p**2)/sp.c**2
                k_O =       np.where( np.isreal(np.sqrt(k_O2)), np.sqrt(k_O2), np.nan )
                k_X2 =      (x**2/sp.c**2) - (w_p**2/sp.c**2)*(x**2 - w_p**2)/(x**2 - w_h**2)
                k_X =       np.where( np.isreal(np.sqrt(k_X2)), np.sqrt(k_X2), np.nan )
                
                return {"R_mode": k_R, "L_mode": k_L, "O_mode":k_O, "X_mode":k_X}

            elif eq_name == "Sinusoidal_Wave":
                # For n-B diagram, we might want to plot against frequency
                T =     self.extracted_vars.get('T', 100)
                A =     self.parse_scientific_input(self.A_input.text())
                f_sim =   A*np.sin( 2*np.pi * x / T )
    
                return f_sim

        except Exception as e:
            QMessageBox.warning(self, "Error", 
                f"Could not evaluate {eq_name} equation: {str(e)}\n"
                f"Formula: {eq_info}\n"
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

        eq_name = self.equation_combo.currentText()
        eq_info = self.equation_info[eq_name]
        
        # Special handling for plasma parameters
        if eq_name == "Plasma Parameters":
            # Plasma parameters are already calculated and stored in self.plasma_params
            return
        
        # Check if this equation produces multiple datasets
        if eq_info.get("multi_dataset", False) and isinstance(y, dict):
            # For multiple datasets, get a base name from user
            dialog = QDialog(self)
            dialog.setWindowTitle("Name Your Plots")
            layout = QVBoxLayout()
            
            label = QLabel("Enter a base name for these plots (will append curve type):")
            layout.addWidget(label)
            
            name_input = QLineEdit()
            default_name = f"{eq_name}_"
            name_input.setText(default_name)
            layout.addWidget(name_input)
            
            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            
            dialog.setLayout(layout)
            
            if dialog.exec_() != QDialog.Accepted:
                return  # User cancelled
            
            base_name = name_input.text().strip()
            if not base_name:
                base_name = default_name

            # Create plot info for each dataset
            for curve_name, y_i in y.items():
                full_name = f"{base_name}_{curve_name}"
                
                if any(p["name"] == full_name for p in self.theory_plots):
                    QMessageBox.warning(self, "Warning", f"A plot named {full_name} already exists!")
                    continue

                plot_info = {
                    "name": full_name,
                    "equation": eq_name,
                    "formula": f"{eq_info['formula']} ({curve_name})",
                    "x": x,
                    "y": y_i,
                    "params": dict(self.extracted_vars),
                    "curve_type": curve_name
                }
                
                self.theory_plots.append(plot_info)
                
            QMessageBox.information(self, "Success", f"Added {len(y)} plots to collection")

        else:    
            # For all other equations, get plot name from user
            dialog = QDialog(self)
            dialog.setWindowTitle("Name Your Plot")
            layout = QVBoxLayout()
            
            label = QLabel("Enter a name for this plot:")
            layout.addWidget(label)
            
            name_input = QLineEdit()
            default_name = f"{self.equation_combo.currentText()}_"
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
            elif eq_name in ["Gaussian Pulse", "Exponential Decay", "Plane Wave"]:
                plot_info["x_min"] = self.parse_scientific_input(self.x_min.text())
                plot_info["x_max"] = self.parse_scientific_input(self.x_max.text())

            # Add to our list
            self.theory_plots.append(plot_info)
            QMessageBox.information(self, "Success", f"Plot '{plot_name}' added to collection")
        
        # Update plot list
        self.update_plot_list()
    
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
        self.plot_window.oneD_plot()
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
        self.plot_window.oneD_plot()
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
                if 'Theory_plots' in file:
                    del file['Theory_plots']
                
                theory_group = file.create_group('Theory_plots')
                
                # Save each plot
                for plot in self.theory_plots:
                    # Create a sanitized name for the dataset
                    safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', plot["name"])
                    
                    # Create a single dataset with both x and y values
                    # Option 1: As a 2D array (Nx2)
                    xy_data = np.column_stack((plot["x"], plot["y"]))
                    dataset = theory_group.create_dataset(safe_name, data=xy_data)
                    
                    # Add dimension labels as attributes
                    dataset.attrs['columns'] = ['x', 'y']
                    
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
                    f"Path: Theory_plots"
                )
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not save to HDF5: {str(e)}")
