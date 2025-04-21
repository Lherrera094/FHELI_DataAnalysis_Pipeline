# plot_window.py
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QPushButton, QComboBox, 
    QLabel, QLineEdit, QFileDialog, QSpinBox, QListWidget, QAbstractItemView,
    QListWidgetItem, QMessageBox, QWidget, QDialogButtonBox, QDoubleSpinBox
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtGui import QIcon
from matplotlib.lines import Line2D
from matplotlib.collections import PathCollection
from matplotlib.figure import Figure
from matplotlib.colors import PowerNorm
from matplotlib.colors import TwoSlopeNorm
from matplotlib.colors import FuncNorm
from matplotlib.backend_bases import MouseButton
from matplotlib.widgets import RectangleSelector
import matplotlib.pyplot as plt
import numpy as np
import h5py

class PlotWindow(QDialog):
#--------------------------------------------- Main Plot Window ------------------------------------------------------
    """A sub-window for plotting 1D and 2D datasets."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Plot Window")
        self.setGeometry(850, 50, 700, 900)                    # Adjusted window size (centerX, centerY, height, width)

        # Layout
        self.layout = QVBoxLayout(self)

        # Matplotlib canvas to show figure
        self.figure = Figure()
        self.canvas = FigureCanvas( self.figure )
        self.layout.addWidget( self.canvas, stretch=4 )

        # Add a status bar for mouse position display
        self.status_bar = QLabel(self)
        self.status_bar.setAlignment(Qt.AlignRight)
        self.status_bar.setStyleSheet("QLabel { background-color : white; }")
        self.layout.addWidget(self.status_bar)

        # Dataset list widget (for multi-dataset plotting)
        self.dataset_list = QListWidget(self)
        self.dataset_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.dataset_list.itemSelectionChanged.connect(self.on_dataset_selected)

        # Set a fixed height for the list widget (e.g., 150 pixels)
        self.dataset_list.setFixedHeight(70)  # Adjust this value as needed
        self.dataset_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        self.layout.addWidget(self.dataset_list)                    # Store as instance variable

        # Form layout for plot title and axis labels
        self.form_layout = QFormLayout()
        self.layout.addLayout(self.form_layout)

#---------------------- Plot features customized by user. General for 1D and 2D --------------------------------------
        # Plot title input
        self.title_input = QLineEdit(self)
        self.title_input.setPlaceholderText("Enter plot title")
        self.form_layout.addRow("Plot Title:", self.title_input)

        # Create a horizontal layout for axis labels
        axis_labels_layout = QHBoxLayout()

        # X-axis label
        axis_labels_layout.addWidget(QLabel("X Label:"))
        self.x_label_input = QLineEdit(self)
        self.x_label_input.setPlaceholderText("Enter x-axis label")
        axis_labels_layout.addWidget(self.x_label_input)

        # Y-axis label
        axis_labels_layout.addWidget(QLabel("Y Label:"))
        self.y_label_input = QLineEdit(self)
        self.y_label_input.setPlaceholderText("Enter y-axis label")
        axis_labels_layout.addWidget(self.y_label_input)

        # Add the entire row to the form layout
        self.form_layout.addRow("Axis Labels:", axis_labels_layout)

        # Axis label size controls
        self.axis_label_size_layout = QHBoxLayout()
        self.layout.addLayout(self.axis_label_size_layout)

        self.x_label_size_label = QLabel("X Label Size:", self)
        self.x_label_size_spin = QSpinBox(self)
        self.x_label_size_spin.setRange(8, 30)  # Reasonable font size range
        self.x_label_size_spin.setValue(12)      # Default size
        self.axis_label_size_layout.addWidget(self.x_label_size_label)
        self.axis_label_size_layout.addWidget(self.x_label_size_spin)

        self.y_label_size_label = QLabel("Y Label Size:", self)
        self.y_label_size_spin = QSpinBox(self)
        self.y_label_size_spin.setRange(8, 30)
        self.y_label_size_spin.setValue(12)
        self.axis_label_size_layout.addWidget(self.y_label_size_label)
        self.axis_label_size_layout.addWidget(self.y_label_size_spin)

        self.title_label_size_label = QLabel("Plot Title Size:", self)
        self.title_label_size_spin = QSpinBox(self)
        self.title_label_size_spin.setRange(8,30)
        self.title_label_size_spin.setValue(18)
        self.axis_label_size_layout.addWidget(self.title_label_size_label)
        self.axis_label_size_layout.addWidget(self.title_label_size_spin)

#---------------------------------------- Controls for 1D plots ----------------------------------------------------
        # Add this in the 1D controls section (after the boundary removal controls)
        self.scale_layout = QHBoxLayout()
        self.layout.addLayout(self.scale_layout)

        # X-axis scale
        self.x_scale_label = QLabel("X Scale:", self)
        self.scale_layout.addWidget(self.x_scale_label)
        self.x_scale_combobox = QComboBox(self)
        self.x_scale_combobox.addItems(["Linear", "Log"])
        self.scale_layout.addWidget(self.x_scale_combobox)

        # Y-axis scale
        self.y_scale_label = QLabel("Y Scale:", self)
        self.scale_layout.addWidget(self.y_scale_label)
        self.y_scale_combobox = QComboBox(self)
        self.y_scale_combobox.addItems(["Linear", "Log"])
        self.scale_layout.addWidget(self.y_scale_combobox)

        # Create a container widget that includes both the label and controls
        self.line_props_container = QWidget()
        line_props_container_layout = QHBoxLayout(self.line_props_container)

        # Add the "Line Properties" label
        line_props_label = QLabel("Line Properties:")
        line_props_container_layout.addWidget(line_props_label)

        # Add the controls
        line_props_layout = QHBoxLayout()
        line_props_container_layout.addLayout(line_props_layout)

        # Line color
        line_props_layout.addWidget(QLabel("Color:"))
        self.line_color_combobox = QComboBox(self)
        self.line_color_combobox.addItems([ "red", "darkred", "salmon", "blue", "navy", "dodgerblue",
                                            "green", "orange", "darkcyan", "blueviolet",  
                                            "indigo", "purple", "magenta", "black",
                                            "dimgray", "chocolate", "crimson" ])
        line_props_layout.addWidget(self.line_color_combobox)

        # Line style
        line_props_layout.addWidget(QLabel("Style:"))
        self.line_style_combobox = QComboBox(self)
        self.line_style_combobox.addItems(["-", "--", "-.", ":", "None"])
        line_props_layout.addWidget(self.line_style_combobox)

        # Line width
        line_props_layout.addWidget(QLabel("Width:"))
        self.line_width = QSpinBox(self)
        self.line_width.setRange(1, 7)
        self.line_width.setValue(1)
        line_props_layout.addWidget(self.line_width)

        # Add the entire container to the form layout (without an additional label)
        self.form_layout.addRow(self.line_props_container)

        # Legend input for 1D plots
        self.legend_input = QLineEdit(self)
        self.legend_input.setPlaceholderText("Enter legend label")
        self.form_layout.addRow("Legend Label:", self.legend_input)

        # Boundary layer removal controls
        self.boundary_layout = QHBoxLayout()
        self.layout.addLayout(self.boundary_layout)

        #1D Delet points
        self.left_points = QLabel("Left points:", self)
        self.boundary_layout.addWidget(self.left_points)

        self.leftp_spinbox = QSpinBox(self)
        self.leftp_spinbox.setMinimum(0)
        self.leftp_spinbox.setMaximum(200)
        self.boundary_layout.addWidget(self.leftp_spinbox)

        self.right_points = QLabel("Right points:", self)
        self.boundary_layout.addWidget(self.right_points)

        self.rightp_spinbox = QSpinBox(self)
        self.rightp_spinbox.setMinimum(0)
        self.rightp_spinbox.setMaximum(200)
        self.boundary_layout.addWidget(self.rightp_spinbox)

#-------------------------------------------------- Controls for 2D plots -----------------------------------------------
        # Colorbar title input (for 2D plots)
        self.colorbar_title_input = QLineEdit(self)
        self.colorbar_title_input.setPlaceholderText("Enter colorbar title")
        self.form_layout.addRow("Colorbar Title:", self.colorbar_title_input)

        # Create a container widget for 2D plot colormap controls
        self.threeD_props_container = QWidget()
        threeD_props_layout = QHBoxLayout(self.threeD_props_container)

        # Scale selection
        threeD_props_layout.addWidget( QLabel("Axis Slice:") )
        self.axis_slice_combobox = QComboBox(self)
        self.axis_slice_combobox.addItems( ["X", "Y", "Z"] )
        threeD_props_layout.addWidget(self.axis_slice_combobox)

        self.slice_label = QLabel("Slice:", self)
        threeD_props_layout.addWidget(self.slice_label)

        self.slice_spinbox = QSpinBox(self)
        self.slice_spinbox.setMinimum(0)
        self.slice_spinbox.setMaximum(500)  # Arbitrary max value
        threeD_props_layout.addWidget(self.slice_spinbox)

        # Add to form layout
        self.form_layout.addRow("Slice 3D dataset:", self.threeD_props_container)

        # Create a container widget for 2D plot colormap controls
        self.twoD_props_container = QWidget()
        twoD_props_layout = QHBoxLayout(self.twoD_props_container)

        # Colormap selection
        twoD_props_layout.addWidget(QLabel("Colormap:"))
        self.colormap_combobox = QComboBox(self)
        self.colormap_combobox.addItems(plt.colormaps())
        twoD_props_layout.addWidget(self.colormap_combobox)

        # Scale selection
        twoD_props_layout.addWidget(QLabel("Scale:"))
        self.scale_combobox = QComboBox(self)
        self.scale_combobox.addItems( ["Linear", "Log", "PowerLaw", "Diverging", "Arcsinh"] )
        twoD_props_layout.addWidget(self.scale_combobox)

        # Add to form layout
        self.form_layout.addRow("Color Features:", self.twoD_props_container)

        self.top_label = QLabel("Top Layers:", self)
        self.boundary_layout.addWidget(self.top_label)

        self.top_spinbox = QSpinBox(self)
        self.top_spinbox.setMinimum(0)
        self.top_spinbox.setMaximum(200)  # Arbitrary max value
        self.boundary_layout.addWidget(self.top_spinbox)

        self.bottom_label = QLabel("Bottom Layers:", self)
        self.boundary_layout.addWidget(self.bottom_label)

        self.bottom_spinbox = QSpinBox(self)
        self.bottom_spinbox.setMinimum(0)
        self.bottom_spinbox.setMaximum(200)
        self.boundary_layout.addWidget(self.bottom_spinbox)

        self.left_label = QLabel("Left Layers:", self)
        self.boundary_layout.addWidget(self.left_label)

        self.left_spinbox = QSpinBox(self)
        self.left_spinbox.setMinimum(0)
        self.left_spinbox.setMaximum(200)
        self.boundary_layout.addWidget(self.left_spinbox)

        self.right_label = QLabel("Right Layers:", self)
        self.boundary_layout.addWidget(self.right_label)

        self.right_spinbox = QSpinBox(self)
        self.right_spinbox.setMinimum(0)
        self.right_spinbox.setMaximum(200)
        self.boundary_layout.addWidget(self.right_spinbox)

#-------------------------------------------- Shared controls for 1D and 2D --------------------------------------------------
        # Plot button (includes boundary removal functionality). It's used for 2D datasets
        self.plot_button = QPushButton("2D Plot", self)
        self.plot_button.clicked.connect(self.twoD_plot)
        self.layout.addWidget(self.plot_button)

        # Modify the button layout section to include new buttons
        self.button_layout = QHBoxLayout()
        self.layout.addLayout(self.button_layout)
        
        # First row of buttons (add operations)
        self.add_buttons_layout = QHBoxLayout()
        self.layout.addLayout(self.add_buttons_layout)
        
        self.add_button = QPushButton("Add Dataset", self)
        self.add_button.clicked.connect(self.add_dataset)
        self.add_buttons_layout.addWidget(self.add_button)
        
        self.add_points_button = QPushButton("Add Points", self)
        self.add_points_button.clicked.connect(self.add_points_dialog)
        self.add_buttons_layout.addWidget(self.add_points_button)
        
        self.add_line_button = QPushButton("Add Line", self)
        self.add_line_button.clicked.connect(self.add_line_dialog)
        self.add_buttons_layout.addWidget(self.add_line_button)
        
        # Second row of buttons (action operations)
        self.action_buttons_layout = QHBoxLayout()
        self.layout.addLayout(self.action_buttons_layout)
        
        self.update_button = QPushButton("Update Plot", self)
        self.update_button.clicked.connect(self.oneD_plot)
        self.action_buttons_layout.addWidget(self.update_button)

        self.remove_button = QPushButton("Remove Selected", self)
        self.remove_button.clicked.connect(self.remove_datasets)
        self.action_buttons_layout.addWidget(self.remove_button)

        # Save plot button
        self.save_button = QPushButton("Save Plot", self)
        self.save_button.clicked.connect(self.save_plot)
        self.action_buttons_layout.addWidget(self.save_button)

        # Variables
        self.data =             None                                #Dataset selected from main window
        self.dataset_type =     None                                # '1D' or '2D'

        self.datasets =         {}                                  # {name: (data, color, style, label, width)}
        self.current_plots =    {}                                  # Track currently plotted datasets
        self.parent_window =    parent                              # Reference to main window

        # Connect mouse events
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)

    def set_data(self, data, dataset_type):
        """Set the dataset to be plotted and its type (1D, 2D or 3D slice)."""
        self.data =             data
        self.adjusted_data =    data                                # Initialize adjusted_data with the original data
        self.dataset_type =     dataset_type

        # Show/hide controls based on dataset type
        if self.dataset_type == '1D':
            # Show 1D controls
            self.show_1d_controls()
        else:  # '2D' or '3D'
            # Show 2D controls
            self.show_2d_controls()

    def show_1d_controls(self):
        """Show controls for 1D plotting."""
        # Show line properties and legend controls
        self.line_props_container.show()
        self.form_layout.labelForField(self.legend_input).show()
        self.legend_input.show()
        self.dataset_list.show()
        
        # Show scale controls
        self.x_scale_label.show()
        self.x_scale_combobox.show()
        self.y_scale_label.show()
        self.y_scale_combobox.show()
        
        # Show action buttons
        self.add_button.show()
        self.update_button.show()
        self.remove_button.show()
        self.add_points_button.show()
        self.add_line_button.show()

        self.left_points.show()
        self.leftp_spinbox.show()
        self.right_points.show()
        self.rightp_spinbox.show()
        
        # Hide 2D-specific controls
        self.hide_2d_controls()

    def show_2d_controls(self):
        """Show controls for 2D plotting."""
        # Show 2D-specific controls
        self.top_label.show()
        self.top_spinbox.show()
        self.bottom_label.show()
        self.bottom_spinbox.show()
        self.left_label.show()
        self.left_spinbox.show()
        self.right_label.show()
        self.right_spinbox.show()
        self.twoD_props_container.show()
        self.form_layout.labelForField(self.twoD_props_container).show()
        self.colorbar_title_input.show()
        self.form_layout.labelForField(self.colorbar_title_input).show()
        self.plot_button.show()

        if self.dataset_type == '3D':
            self.threeD_props_container.show()
            self.form_layout.labelForField(self.threeD_props_container).show()
        else:
            self.threeD_props_container.hide()
            self.form_layout.labelForField(self.threeD_props_container).hide()
        
        # Hide 1D-specific controls
        self.hide_1d_controls()

    def hide_1d_controls(self):
        """Hide controls for 1D plotting."""
        self.line_props_container.hide()
        self.form_layout.labelForField(self.legend_input).hide()
        self.legend_input.hide()
        self.dataset_list.hide()
        self.x_scale_label.hide()
        self.x_scale_combobox.hide()
        self.y_scale_label.hide()
        self.y_scale_combobox.hide()
        self.add_button.hide()
        self.update_button.hide()
        self.remove_button.hide()
        self.add_points_button.hide()
        self.add_line_button.hide()
        self.left_points.hide()
        self.leftp_spinbox.hide()
        self.right_points.hide()
        self.rightp_spinbox.hide()

    def hide_2d_controls(self):
        """Hide controls for 2D plotting."""
        self.top_label.hide()
        self.top_spinbox.hide()
        self.bottom_label.hide()
        self.bottom_spinbox.hide()
        self.left_label.hide()
        self.left_spinbox.hide()
        self.right_label.hide()
        self.right_spinbox.hide()
        self.twoD_props_container.hide()
        self.form_layout.labelForField(self.twoD_props_container).hide()
        self.colorbar_title_input.hide()
        self.form_layout.labelForField(self.colorbar_title_input).hide()
        self.plot_button.hide()
        self.threeD_props_container.hide()
        self.form_layout.labelForField(self.threeD_props_container).hide()

    def remove_boundary_layers(self, data):
        """Remove the specified number of layers/points from the boundaries of the dataset."""
        if self.data is None:
            return self.data

        if self.dataset_type == '1D':  # 1D dataset
            left = self.leftp_spinbox.value()
            right = self.rightp_spinbox.value()
            length = len(data)

            if left + right < length:                           # Ensure valid boundaries
                data = data[left:length - right]
            else:
                print("Invalid boundary removal parameters. Skipping boundary removal.")

        elif self.dataset_type in ['2D', '3D']:  # 2D dataset
            top = self.top_spinbox.value()
            bottom = self.bottom_spinbox.value()
            left = self.left_spinbox.value()
            right = self.right_spinbox.value()
            rows, cols = data.shape

            if top + bottom < rows and left + right < cols:  # Ensure valid boundaries
                data = data[top:rows - bottom, left:cols - right]
            else:
                print("Invalid boundary removal parameters. Skipping boundary removal.")

        return data
    
# --------------------------------------------------- 1D datasets controls ---------------------------------------------------
    def add_dataset(self):
        """Add a new dataset from the main window."""
        if not self.parent_window or not self.parent_window.file_path:
            QMessageBox.warning(self, "Warning", "No HDF5 file loaded in main window")
            return
            
        # Get selected items from main window tree
        selected_items = self.parent_window.tree_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "No dataset selected in main window")
            return
            
        with h5py.File(self.parent_window.file_path, 'r') as file:
            for item in selected_items:
                # Get the full path from the item's data (using UserRole)
                full_path = item.data(0, Qt.UserRole)  
                
                if not full_path or not isinstance(full_path, str):
                    QMessageBox.warning(self, "Warning", f"Invalid dataset path for item: {item.text(0)}")
                    continue
                    
                try:
                    dataset = file[full_path]
                    if not isinstance(dataset, h5py.Dataset):
                        QMessageBox.warning(self, "Warning", f"{full_path} is not a dataset")
                        continue
                        
                    data = dataset[()]

                    # Check if this is a combined (x,y) dataset from theory plots
                    is_theory_plot = False
                    if data.ndim == 2 and data.shape[1] == 2 and 'columns' in dataset.attrs:
                        if list(dataset.attrs['columns']) == ['x', 'y']:
                            is_theory_plot = True
                            x_data = data[:, 0]
                            y_data = data[:, 1]
                    
                    if is_theory_plot:
                        # Handle as 1D theory plot data
                        name = dataset.attrs.get('name', full_path.split('/')[-1])
                        
                        # Add to our datasets with default styling
                        self.datasets[name] = {
                            'type': 'theory',
                            'x': x_data,
                            'y': y_data,
                            'color': self.line_color_combobox.currentText(),
                            'style': self.line_style_combobox.currentText(),
                            'label': dataset.attrs.get('formula', name),
                            'width': self.line_width.value()
                        }
                        
                    elif data.ndim == 1:
                        # Regular 1D dataset
                        name = full_path.split('/')[-1]
                        if name in self.datasets:
                            name = f"{name}_{len(self.datasets)}"  # Append number if name exists
                        
                        self.datasets[name] = {
                            'data': data,
                            'color': self.line_color_combobox.currentText(),
                            'style': self.line_style_combobox.currentText(),
                            'label': self.legend_input.text() or name,
                            'width': self.line_width.value()
                        }
                    else:
                        QMessageBox.warning(self, "Warning", 
                                        f"Dataset {full_path} is not 1D (shape: {data.shape})")
                        continue

                    '''if data.ndim != 1:
                        QMessageBox.warning(self, "Warning", f"Dataset {full_path} is not 1D (shape: {data.shape})")
                        continue
                        
                    # Generate a unique name
                    name = full_path.split('/')[-1]
                    if name in self.datasets:
                        name = f"{name}_{len(self.datasets)}"  # Append number if name exists
                    
                    # Add to our datasets with default styling
                    self.datasets[name] = {
                        'data': data,
                        'color': self.line_color_combobox.currentText(),
                        'style': self.line_style_combobox.currentText(),
                        'label': self.legend_input.text() or name,
                        'width': self.line_width.value()
                    }'''
                    
                    # Add to list widget
                    list_item = QListWidgetItem(name)
                    list_item.setData(Qt.UserRole, name)  # Store the dataset name
                    self.dataset_list.addItem(list_item)
                    
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Couldn't load dataset {full_path}: {str(e)}")
        
        if self.datasets:
            self.oneD_plot()

    def remove_datasets(self):
        """Remove selected datasets from the plot."""
        selected_items = self.dataset_list.selectedItems()
        if not selected_items:
            return
            
        # Remove from both datasets dictionary and list widget
        for item in selected_items:
            name = item.data(Qt.UserRole)
            if name in self.datasets:
                # Remove any associated plot elements
                if name in self.current_plots:
                    if isinstance(self.current_plots[name], list):
                        # Handle points (which are collections)
                        for element in self.current_plots[name]:
                            if element in self.figure.gca().collections:
                                self.figure.gca().collections.remove(element)
                    elif isinstance(self.current_plots[name], Line2D):
                        # Handle lines
                        self.current_plots[name].remove()
                    del self.current_plots[name]
                
                # Remove from datasets dictionary
                del self.datasets[name]
            
            # Remove from list widget
            self.dataset_list.takeItem(self.dataset_list.row(item))
        
        # Redraw the canvas to reflect changes
        self.canvas.draw()
    
    def on_dataset_selected(self):
        """Safely handle dataset selection without crashing."""
        try:
            # Check if widgets still exist
            if not all(hasattr(self, attr) for attr in [
                'line_color_combobox', 'line_style_combobox',
                'legend_input', 'line_width', 'dataset_list'
            ]):
                return

            selected_items = self.dataset_list.selectedItems()
            if not selected_items:
                return

            name = selected_items[0].data(Qt.UserRole)
            if name not in self.datasets:
                return

            dataset = self.datasets[name]

            # Safely disable/enable controls
            def safe_set_enabled(widget, enabled):
                if widget and hasattr(widget, 'setEnabled'):
                    widget.setEnabled(enabled)

            # Disable all controls first
            safe_set_enabled(self.line_color_combobox, False)
            safe_set_enabled(self.line_style_combobox, False)
            safe_set_enabled(self.legend_input, False)
            safe_set_enabled(self.line_width, False)

            # Only enable for regular datasets
            if dataset.get('type') == 'theory' or 'type' not in dataset:
                safe_set_enabled(self.line_color_combobox, True)
                safe_set_enabled(self.line_style_combobox, True)
                safe_set_enabled(self.legend_input, True)
                safe_set_enabled(self.line_width, True)

                # Safely update values
                if self.line_color_combobox:
                    self.line_color_combobox.setCurrentText(dataset.get('color', 'blue'))
                if self.line_style_combobox:
                    self.line_style_combobox.setCurrentText(dataset.get('style', '-'))
                if self.legend_input:
                    self.legend_input.setText(dataset.get('label', name))
                if self.line_width:
                    self.line_width.setValue(dataset.get('width', 1))

        except Exception as e:
            print(f"Error in on_dataset_selected: {e}")
        
    def apply_customization(self):
        """Apply current customization to selected dataset."""        
        selected_items = self.dataset_list.selectedItems()
        if not selected_items or len(selected_items) != 1:
            return

        for item in selected_items:
            name = item.data(Qt.UserRole)
            if name in self.datasets:
                # Only update properties that exist and widgets are available
                updates = {}
                if hasattr(self, 'line_color_combobox') and self.line_color_combobox:
                    updates['color'] = self.line_color_combobox.currentText()
                if hasattr(self, 'line_style_combobox') and self.line_style_combobox:
                    updates['style'] = self.line_style_combobox.currentText()
                if hasattr(self, 'legend_input') and self.legend_input:
                    updates['label'] = self.legend_input.text()
                if hasattr(self, 'line_width') and self.line_width:
                    updates['width'] = self.line_width.value()
                
                self.datasets[name].update(updates)

    def add_points_dialog(self):
        """Open a dialog to add points to the plot."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Point")
        layout = QFormLayout(dialog)
        
        # X coordinates (local variable, not instance)
        x_points_input = QLineEdit(dialog)
        x_points_input.setPlaceholderText("e.g., 1,2,3,4,5")
        layout.addRow("X Coordinates (comma separated):", x_points_input)
        
        # Y coordinates (local variable, not instance)
        y_points_input = QLineEdit(dialog)
        y_points_input.setPlaceholderText("e.g., 10,20,30,40,50")
        layout.addRow("Y Coordinates (comma separated):", y_points_input)
        
        # Point style (local variable, not instance)
        point_style = QComboBox(dialog)
        point_style.addItems([".", "o", "s", "^", "v", "<", ">", "p", "*", "h", "+", "x", "D"])
        layout.addRow("Point Style:", point_style)
        
        # Point color (local variable, not instance)
        point_color = QComboBox(dialog)
        point_color.addItems(["blue", "red", "green", "black", "purple", "orange", "cyan", "magenta"])
        layout.addRow("Point Color:", point_color)
        
        # Point size (local variable, not instance)
        point_size = QSpinBox(dialog)
        point_size.setRange(1, 20)
        point_size.setValue(6)
        layout.addRow("Point Size:", point_size)
        
        # Label (local variable, not instance)
        points_label = QLineEdit(dialog)
        points_label.setPlaceholderText("Points Label")
        layout.addRow("Label:", points_label)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            try:
                x_points = [float(x.strip()) for x in x_points_input.text().split(",")]
                y_points = [float(y.strip()) for y in y_points_input.text().split(",")]
                
                if len(x_points) != len(y_points):
                    QMessageBox.warning(self, "Error", "X and Y points must have the same length")
                    return
                
                # Generate a unique name
                name = f"Points_{len(self.datasets)}"
                
                # Add to our datasets
                self.datasets[name] = {
                    'type': 'points',
                    'x': x_points,
                    'y': y_points,
                    'style': point_style.currentText(),
                    'color': point_color.currentText(),
                    'size': point_size.value(),
                    'label': points_label.text() or name
                }
                
                # Add to list widget
                list_item = QListWidgetItem(name)
                list_item.setData(Qt.UserRole, name)
                list_item.setIcon(QIcon.fromTheme("draw-dot"))  # Points icon
                self.dataset_list.addItem(list_item)
                
                self.oneD_plot()
                
            except ValueError:
                QMessageBox.warning(self, "Error", "Invalid input format. Please enter numbers separated by commas.")

    def add_line_dialog(self):
        """Open a dialog to add a line to the plot."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Line")
        layout = QFormLayout(dialog)
        
        # Create local widgets (not instance variables)
        line_x1 = QDoubleSpinBox(dialog)
        line_x1.setRange(-1e6, 1e6)
        line_x2 = QDoubleSpinBox(dialog)
        line_x2.setRange(-1e6, 1e6)
        line_y1 = QDoubleSpinBox(dialog)
        line_y1.setRange(-1e6, 1e6)
        line_y2 = QDoubleSpinBox(dialog)
        line_y2.setRange(-1e6, 1e6)
        
        points_layout = QHBoxLayout()
        points_layout.addWidget(QLabel("From (x,y):"))
        points_layout.addWidget(line_x1)
        points_layout.addWidget(line_y1)
        points_layout.addWidget(QLabel("To (x,y):"))
        points_layout.addWidget(line_x2)
        points_layout.addWidget(line_y2)
        layout.addRow(points_layout)
        
        line_style = QComboBox(dialog)
        line_style.addItems(["-", "--", "-.", ":"])
        layout.addRow("Line Style:", line_style)
        
        line_color = QComboBox(dialog)
        line_color.addItems(["blue", "red", "green", "black", "purple", "orange", "cyan", "magenta"])
        layout.addRow("Line Color:", line_color)
        
        line_width = QSpinBox(dialog)
        line_width.setRange(1, 10)
        line_width.setValue(1)
        layout.addRow("Line Width:", line_width)
        
        line_label = QLineEdit(dialog)
        line_label.setPlaceholderText("Line Label")
        layout.addRow("Label:", line_label)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            # Generate a unique name
            name = f"Line_{len(self.datasets)}"
            
            # Add to our datasets
            self.datasets[name] = {
                'type': 'line',
                'x1': line_x1.value(),
                'y1': line_y1.value(),
                'x2': line_x2.value(),
                'y2': line_y2.value(),
                'style': line_style.currentText(),
                'color': line_color.currentText(),
                'width': line_width.value(),
                'label': line_label.text() or name
            }
            
            # Add to list widget
            list_item = QListWidgetItem(name)
            list_item.setData(Qt.UserRole, name)
            list_item.setIcon(QIcon.fromTheme("draw-line"))  # Line icon
            self.dataset_list.addItem(list_item)
            
            self.oneD_plot()

# --------------------------------------------------- plot functions controls ---------------------------------------------------
    def oneD_plot(self):
        """Update the plot with all datasets added to the list."""
        self.apply_customization()

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        if not self.datasets:
            self.canvas.draw()
            return

        # Plot each dataset with its customization
        for name, dataset in self.datasets.items():
            if dataset.get('type') == 'theory':
                # Theory plot data with separate x and y
                ax.plot(
                    dataset['x'],
                    dataset['y'],
                    color=dataset['color'],
                    linestyle=dataset['style'],
                    label=dataset['label'],
                    linewidth=dataset['width']
                )
            
            elif 'type' not in dataset:                         # Regular 1D dataset
                data = dataset['data']
                
                # Apply boundary removal using the spin boxes
                left = self.leftp_spinbox.value()
                right = self.rightp_spinbox.value()
                
                if left + right < len(data):
                    data = data[left:len(data)-right]
                
                ax.plot(
                    data,
                    color=dataset['color'],
                    linestyle=dataset['style'],
                    label=dataset['label'],
                    linewidth=dataset['width']
                )
            elif dataset['type'] == 'points':  # Points dataset
                ax.plot(
                    dataset['x'], dataset['y'],
                    linestyle='None',
                    marker=dataset['style'],
                    color=dataset['color'],
                    markersize=dataset['size'],
                    label=dataset['label']
                )
            elif dataset['type'] == 'line':  # Line dataset
                ax.plot(
                    [dataset['x1'], dataset['x2']],
                    [dataset['y1'], dataset['y2']],
                    linestyle=dataset['style'],
                    color=dataset['color'],
                    linewidth=dataset['width'],
                    label=dataset['label']
                )
        
        # Set labels and title
        ax.set_xlabel( self.x_label_input.text() or "X Axis",  fontsize=self.x_label_size_spin.value() )
        ax.set_ylabel( self.y_label_input.text() or "Y Axis",  fontsize=self.y_label_size_spin.value() )
        ax.set_title(  self.title_input.text()   or "1D Plot", fontsize=self.title_label_size_spin.value())

        # Apply logarithmic scales if selected
        if self.x_scale_combobox.currentText() == "Log":
            ax.set_xscale('log')
        if self.y_scale_combobox.currentText() == "Log":
            ax.set_yscale('log')
        
        # Add legend if we have any custom labels
        if any(d['label'] for d in self.datasets.values()):
            ax.legend()
        
        ax.grid(True)
        self.canvas.draw()

    def twoD_plot(self):
        """Plot 2D datasets only."""
        if self.data is None:
            return

        # Clear the previous plot
        self.figure.clear()

        # Create a new plot
        ax = self.figure.add_subplot(111)

        if self.dataset_type == "3D":
            axis = self.axis_slice_combobox.currentText()                                 # Get the axis label (x, y, z)
            slice_index = self.slice_spinbox.value()

            # Map x, y, z to axis indices
            axis_map = {"X": 0, "Y": 1, "Z": 2}

            # Slice the 3D dataset
            if axis_map[axis] == 0:
                data = self.data[slice_index, :, :]
            elif axis_map[axis] == 1:
                data = self.data[:, slice_index, :]
            elif axis_map[axis] == 2:
                data = self.data[:, :, slice_index]
        
        else:
            data = self.data

        # Check if data is 2D
        if data.ndim != 2:
            QMessageBox.warning(self, "Warning", 
                            f"Cannot plot data with shape {data.shape}. Expected 2D array.")
            return

        # Remove boundary layers/points
        data = self.remove_boundary_layers( data )                                                               # 2D dataset
            
        # Get selected colormap
        colormap = self.colormap_combobox.currentText()
        scale = self.scale_combobox.currentText()
        colorbar_title = self.colorbar_title_input.text() or "Value"

        # Plot the data with the selected colormap and scale
        if   scale == "Linear":
            im = ax.imshow(data, cmap=colormap, origin='lower')                   
        elif scale == "Log":  
            im = ax.imshow(data, cmap=colormap, norm="log", origin='lower')    
        elif scale == "PowerLaw":
            im = ax.imshow(data, cmap=colormap, norm=PowerNorm(gamma=0.7), origin='lower')
        elif scale == "Diverging":
            try:
                norm = TwoSlopeNorm(vmin=data.min(), vcenter=0, vmax=data.max())
                im = ax.imshow(data, cmap=colormap, norm=norm, origin='lower')
            except:
                print("The minimum value, zero and maximum must be in ascending order.")
                im = ax.imshow(data, cmap=colormap, origin='lower' )
        else:
            # Define the forward and inverse functions for the normalization
            def forward(x):
                return np.arcsinh(x * 1.0) / np.arcsinh(1.0)
            
            def inverse(x):
                return np.sinh(x) / 1.0
            
            norm = FuncNorm( (forward, inverse), vmin=0, vmax=data.max() )
            im = ax.imshow(data, cmap=colormap, norm=norm, origin='lower')

        # Add colorbar with title
        cbar = self.figure.colorbar(im, ax=ax)
        cbar.set_label(colorbar_title, fontsize=self.y_label_size_spin.value())

        # Set labels with custom sizes
        ax.set_xlabel(self.x_label_input.text() or "X-Axis", 
                     fontsize=self.x_label_size_spin.value())
        ax.set_ylabel(self.y_label_input.text() or "Y-Axis", 
                     fontsize=self.y_label_size_spin.value())
            
        ax.set_title(self.title_input.text() or "2D Heatmap",
                     fontsize=self.title_label_size_spin.value())

            
        # Refresh the canvas
        self.canvas.draw()

    def save_plot(self):
        """Save the current plot to a file."""
        if not self.figure.axes:
            return  # No plot to save

        # Open a file dialog to choose the save location
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Plot", "", "PNG Files (*.png);;All Files (*)"
        )
        if not file_path:
            return

        # Save the plot
        self.figure.savefig(file_path, dpi = 1200)

# ----------------------------------------------- Mouse Motion track and activity------------------------------------------------

    def on_mouse_move(self, event):
        """Display mouse position in status bar."""
        if event.inaxes and self.figure.axes:
            ax = self.figure.axes[0]
            x, y = event.xdata, event.ydata
                
            # Format coordinates based on axis scale
            x_fmt = "{:.3g}".format(x)
            y_fmt = "{:.3g}".format(y)
                
            if ax.get_xscale() == 'log':
                x_fmt = "10^{:.3g}".format(np.log10(x))
            if ax.get_yscale() == 'log':
                y_fmt = "10^{:.3g}".format(np.log10(y))
                    
            self.status_bar.setText(f"x: {x_fmt}, y: {y_fmt}")