# plot_window.py
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QPushButton, QComboBox, 
    QLabel, QLineEdit, QFileDialog, QSpinBox, QListWidget, QAbstractItemView,
    QListWidgetItem, QMessageBox, QWidget
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.colors import PowerNorm
from matplotlib.colors import TwoSlopeNorm
from matplotlib.colors import FuncNorm
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
        self.layout.addWidget( self.canvas, stretch=3 )

        # Dataset list widget (for multi-dataset plotting)
        self.dataset_list = QListWidget(self)
        self.dataset_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.dataset_list.itemSelectionChanged.connect(self.on_dataset_selected)

        # Set a fixed height for the list widget (e.g., 150 pixels)
        self.dataset_list.setFixedHeight(70)  # Adjust this value as needed
        self.dataset_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        
        # Alternatively, set maximum height if you want it to be able to grow slightly
        # self.dataset_list.setMaximumHeight(200)

        self.datasets_label = QLabel("Datasets:", self)  # Store as instance variable
        self.layout.addWidget(self.datasets_label)
        self.layout.addWidget(self.dataset_list)

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
        self.line_color_combobox.addItems([ "blue", "royalblue", "red", "forestgreen", "black", "purple", "orange", "navy", 
                                            "magenta", "tomato","darkcyan","steelblue"])
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

#Shared controls for 1D and 2D
        # Plot button (includes boundary removal functionality). It's used for 2D datasets
        self.plot_button = QPushButton("Plot", self)
        self.plot_button.clicked.connect(self.plot)
        self.layout.addWidget(self.plot_button)

        # Action buttons
        self.button_layout = QHBoxLayout()
        self.layout.addLayout(self.button_layout)
        
        self.add_button = QPushButton("Add Dataset", self)
        self.add_button.clicked.connect(self.add_dataset)
        self.button_layout.addWidget(self.add_button)
        
        self.update_button = QPushButton("Update Plot", self)
        self.update_button.clicked.connect(self.update_plot)
        self.button_layout.addWidget(self.update_button)

        self.remove_button = QPushButton("Remove Selected", self)
        self.remove_button.clicked.connect(self.remove_datasets)
        self.button_layout.addWidget(self.remove_button)

        # Save plot button
        self.save_button = QPushButton("Save Plot", self)
        self.save_button.clicked.connect(self.save_plot)
        self.layout.addWidget(self.save_button)

        # Variables
        self.data =             None                                #Dataset selected from main window
        self.dataset_type =     None                                # '1D' or '2D'

        self.datasets =         {}                                  # {name: (data, color, style, label, width)}
        self.current_plots =    {}                                  # Track currently plotted datasets
        self.parent_window =    parent                              # Reference to main window

    def set_data(self, data, dataset_type):
        """Set the dataset to be plotted and its type (1D, 2D or 3D slice)."""
        self.data =             data
        self.adjusted_data =    data                                # Initialize adjusted_data with the original data
        self.dataset_type =     dataset_type

        # Show/hide axis selection based on dataset type
        if self.dataset_type == '1D':
            # Show features in plot_window for 1D plots
            # Show only left and right removal for 1D datasets
            self.boundary_layout.addWidget(self.left_points)
            self.boundary_layout.addWidget(self.leftp_spinbox)
            self.boundary_layout.addWidget(self.right_points)
            self.boundary_layout.addWidget(self.rightp_spinbox)

            self.left_points.show()
            self.leftp_spinbox.show()
            self.right_points.show()
            self.rightp_spinbox.show()

            # In the 1D section of set_data:
            self.x_scale_label.show()
            self.x_scale_combobox.show()
            self.y_scale_label.show()
            self.y_scale_combobox.show()

            # Show line color, line style, and legend options for 1D plots
            self.line_props_container.show()
            self.form_layout.labelForField(self.legend_input).show()
            self.legend_input.show()
            self.datasets_label.show()
            self.dataset_list.show()

            self.add_button.show()
            self.update_button.show()
            self.remove_button.show()

            # Hide features of 2D plots
            # Hide top and bottom removal for 1D datasets
            self.top_label.hide()
            self.top_spinbox.hide()
            self.bottom_label.hide()
            self.bottom_spinbox.hide()
            self.left_label.hide()
            self.left_spinbox.hide()
            self.right_label.hide()
            self.right_spinbox.hide()

            #3D slice controls
            self.threeD_props_container.hide()
            self.form_layout.labelForField(self.threeD_props_container).hide()
            self.slice_label.hide()
            self.slice_spinbox.hide()

            self.twoD_props_container.hide()
            self.form_layout.labelForField(self.twoD_props_container).hide()
            self.colorbar_title_input.hide()
            self.form_layout.labelForField(self.colorbar_title_input).hide()
            self.form_layout.labelForField(self.colorbar_title_input).hide()
            self.colorbar_title_input.hide()

            self.plot_button.hide()

        else:                                             # '2D'
            # Show features in plot_window for 2D plots
            # Show top, bottom, left, and right removal for 2D datasets
            self.boundary_layout.addWidget(self.top_label)
            self.boundary_layout.addWidget(self.top_spinbox)
            self.boundary_layout.addWidget(self.bottom_label)
            self.boundary_layout.addWidget(self.bottom_spinbox)
            self.boundary_layout.addWidget(self.left_label)
            self.boundary_layout.addWidget(self.left_spinbox)
            self.boundary_layout.addWidget(self.right_label)
            self.boundary_layout.addWidget(self.right_spinbox)

            # Hide top and bottom removal for 1D datasets
            self.top_label.show()
            self.top_spinbox.show()
            self.bottom_label.show()
            self.bottom_spinbox.show()
            self.left_label.show()
            self.left_spinbox.show()
            self.right_label.show()
            self.right_spinbox.show()

            if self.dataset_type == "3D":
                #3D slice controls
                self.threeD_props_container.show()
                self.form_layout.labelForField(self.threeD_props_container).show()
                self.slice_label.show()
                self.slice_spinbox.show()
            else:
                #3D slice controls
                self.threeD_props_container.hide()
                self.form_layout.labelForField(self.threeD_props_container).hide()
                self.slice_label.hide()
                self.slice_spinbox.hide()

            # Show 2D controls
            self.twoD_props_container.show()
            self.form_layout.labelForField(self.twoD_props_container).show()
            self.colorbar_title_input.show()
            self.form_layout.labelForField(self.colorbar_title_input).show()
            self.form_layout.labelForField(self.colorbar_title_input).show()
            self.colorbar_title_input.show()

            self.plot_button.show()

            self.left_points.hide()
            self.leftp_spinbox.hide()
            self.right_points.hide()
            self.rightp_spinbox.hide()

            # In the 2D section of set_data:
            self.x_scale_label.hide()
            self.x_scale_combobox.hide()
            self.y_scale_label.hide()
            self.y_scale_combobox.hide()

            # Hide line color, line style, and legend options for 2D plots
            self.line_props_container.hide()
            self.form_layout.labelForField(self.legend_input).hide()
            self.legend_input.hide()
            self.datasets_label.hide()
            self.dataset_list.hide()

            self.add_button.hide()
            self.update_button.hide()
            self.remove_button.hide()

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

    """def add_dataset(self):
        #Add a new dataset from the main window.
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
                full_path = item.data(0, 1)
                try:
                    dataset = file[full_path]
                    if not isinstance(dataset, h5py.Dataset):
                        continue
                        
                    data = dataset[()]
                    if data.ndim != 1:
                        QMessageBox.warning(self, "Warning", f"Dataset {full_path} is not 1D")
                        continue
                        
                    # Generate a unique name
                    name = full_path.split('/')[-1]
                    if name in self.datasets:
                        name = f"{name}_{full_path.split('/')[-2]}"
                        print(name)
                        
                    # Add to our datasets with default styling
                    default_color = "blue"  # Default color if combo box isn't available
                    default_style = "-"     # Default line style
                    default_width = 1       # Default line width
                    default_label = name    #Default label name if not input
                    
                    # Try to get current values from UI elements if they exist
                    try:
                        default_color = self.line_color_combobox.currentText()
                        default_style = self.line_style_combobox.currentText()
                        default_width = self.line_width.value()
                        default_label = self.legend_input.text()
                    except AttributeError:
                        pass
                        
                    self.datasets[name] = {
                        'data': data,
                        'color': default_color,
                        'style': default_style,
                        'label': default_label,
                        'width': default_width
                    }
                    
                    # Add to list widget
                    list_item = QListWidgetItem(name)
                    list_item.setData(Qt.UserRole, name)  # Store the dataset name
                    self.dataset_list.addItem(list_item)
                    
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Couldn't load dataset {full_path}: {str(e)}")
        
        if self.datasets:
            self.update_plot()"""
    
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
                full_path = item.data(0, Qt.UserRole)  # This is the critical fix
                
                if not full_path or not isinstance(full_path, str):
                    QMessageBox.warning(self, "Warning", f"Invalid dataset path for item: {item.text(0)}")
                    continue
                    
                try:
                    dataset = file[full_path]
                    if not isinstance(dataset, h5py.Dataset):
                        QMessageBox.warning(self, "Warning", f"{full_path} is not a dataset")
                        continue
                        
                    data = dataset[()]
                    if data.ndim != 1:
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
                    }
                    
                    # Add to list widget
                    list_item = QListWidgetItem(name)
                    list_item.setData(Qt.UserRole, name)  # Store the dataset name
                    self.dataset_list.addItem(list_item)
                    
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Couldn't load dataset {full_path}: {str(e)}")
        
        if self.datasets:
            self.update_plot()

    def remove_datasets(self):
        """Remove selected datasets from the plot."""
        selected_items = self.dataset_list.selectedItems()
        if not selected_items:
            return
            
        for item in selected_items:
            name = item.data(Qt.UserRole)
            if name in self.datasets:
                del self.datasets[name]
            self.dataset_list.takeItem(self.dataset_list.row(item))
        
        self.update_plot()                                                  # Refresh the plot after removal
    
    def on_dataset_selected(self):
        """When a dataset is selected, update the customization controls."""
        selected_items = self.dataset_list.selectedItems()
            
        # Return if no items are selected
        if not selected_items:
            return
            
        name = selected_items[0].data(Qt.UserRole)
        if name not in self.datasets:
            return
            
        dataset = self.datasets[name]
        
        # Update controls to match selected dataset
        self.line_color_combobox.setCurrentText(    dataset['color'] )
        self.line_style_combobox.setCurrentText(    dataset['style'] )
        self.legend_input.setText(                  dataset['label'] )                     
        self.line_width.setValue(                   dataset['width'] )
    
    def apply_customization(self):
        """Apply current customization to selected dataset."""
        selected_items = self.dataset_list.selectedItems()
        if not selected_items or len(selected_items) != 1:
            return
            
        for item in selected_items:
            name = item.data(Qt.UserRole)
            if name in self.datasets:
                self.datasets[name].update({
                    'color': self.line_color_combobox.currentText(),
                    'style': self.line_style_combobox.currentText(),
                    'label': self.legend_input.text(),
                    'width': self.line_width.value(),
                    'x_scale': self.x_scale_combobox.currentText(),
                    'y_scale': self.y_scale_combobox.currentText()
                })

    def update_plot(self):
        """Update the plot with all datasets added to the list."""
        self.apply_customization()

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        if not self.datasets:
            self.canvas.draw()
            return
            
        # Plot each dataset with its customization
        for name, dataset in self.datasets.items():
            data = dataset['data']
            
            # Apply boundary removal using the spin boxes
            left = self.leftp_spinbox.value()  # Changed from self.left_points
            right = self.rightp_spinbox.value()  # Changed from self.right_points
            
            if left + right < len(data):
                data = data[left:len(data)-right]
            
            ax.plot(
                data,
                color=dataset['color'],
                linestyle=dataset['style'],
                label=dataset['label'],
                linewidth=dataset['width']
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

    def plot(self):
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
