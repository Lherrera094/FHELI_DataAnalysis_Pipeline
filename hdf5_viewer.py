# hdf5_viewer.py
import sys
import h5py
import numpy as np
import subprocess
import json
import tempfile
import os
import imageio.v2 as imageio

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
    QPushButton, QTreeWidget, QTreeWidgetItem, QFileDialog, QTextEdit, QLabel, 
    QDialog, QFormLayout, QSpinBox, QDialogButtonBox, QComboBox, QLineEdit, QCheckBox, QDoubleSpinBox
)
from plot_window import PlotWindow
import plotly.graph_objects as go


# Main window
class HDF5Viewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FHELI HDF5 Visualization.")
        self.setGeometry(100, 100, 800, 600)

        # Main widget and layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)

        # Top layout for the buttons
        self.top_layout = QHBoxLayout()
        self.main_layout.addLayout(self.top_layout)

        # Load file button
        self.load_button = QPushButton("Load HDF5 File", self)
        self.load_button.clicked.connect(self.load_file)
        self.top_layout.addWidget(self.load_button)

        # Create GIF button (NEW)
        self.gif_button = QPushButton("Create GIF", self)
        self.gif_button.clicked.connect(self.create_gif)  # Connect to the create_gif method
        self.top_layout.addWidget(self.gif_button)  # Add the button to the layout

        # Operation button
        self.operation_button = QPushButton("Dataset Operations", self)
        self.operation_button.clicked.connect(self.open_operation_window)
        self.top_layout.addWidget(self.operation_button)

        # Add a stretch to push the buttons to the left
        self.top_layout.addStretch()

        # Tree widget to display groups and datasets
        self.tree_widget = QTreeWidget(self)
        self.tree_widget.setHeaderLabel("HDF5 File Structure")
        self.tree_widget.itemClicked.connect(self.on_item_clicked)
        self.main_layout.addWidget(self.tree_widget)

        # Text edit to display values
        self.value_display = QTextEdit(self)
        self.value_display.setReadOnly(True)  # Make it read-only
        self.main_layout.addWidget(self.value_display)

        # Label to display real-time progress
        self.progress_label = QLabel("Progress: Idle", self)
        self.main_layout.addWidget(self.progress_label)

        # NEW: Bottom layout for the Exit button
        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.addStretch()  # Add a stretch to push the Exit button to the right
        self.exit_button = QPushButton("Exit", self)
        self.exit_button.clicked.connect(self.close)  # Connect to the close method
        self.bottom_layout.addWidget(self.exit_button)
        self.main_layout.addLayout(self.bottom_layout)  # Add the bottom layout to the main layout


        # Variables
        self.file_path = None
        self.data = None
        self.single_value_datasets = {}  # Stores single-value datasets for axis selection
        self.plot_window = None  # Sub-window for plotting
        self.time_series_datasets = []  # Stores time-series datasets for GIF creation
        self.operation_window = None  # NEW: Sub-window for dataset operations

    def load_file(self):
        """Open a file dialog to load an HDF5 file."""
        self.file_path, _ = QFileDialog.getOpenFileName(
            self, "Open HDF5 File", "", "HDF5 Files (*.h5 *.hdf5)"
        )
        if not self.file_path:
            return

        # Clear the tree widget and value display
        self.tree_widget.clear()
        self.value_display.clear()
        self.single_value_datasets.clear()
        self.time_series_datasets.clear()  # Clear time-series datasets

        # Populate the tree widget with the file's structure
        with h5py.File(self.file_path, 'r') as file:
            self.populate_tree(file, self.tree_widget)
        

    def populate_tree(self, node, parent_item):
        """Recursively populate the tree widget with groups and datasets."""
        for name, item in node.items():
            if isinstance(item, h5py.Group):
                # Add a group item
                group_item = QTreeWidgetItem(parent_item, [name])
                group_item.setData(0, 1, item.name)  # Store the full path of the group
                self.populate_tree(item, group_item)  # Recursively add subgroups
            elif isinstance(item, h5py.Dataset):
                # Add a dataset item
                dataset_item = QTreeWidgetItem(parent_item, [name])
                dataset_item.setData(0, 1, item.name)  # Store the full path of the dataset

                # Store single-value datasets for axis selection
                if item.size == 1:
                    self.single_value_datasets[item.name] = item[()]

                # Check if the dataset is part of a time series
                if name.startswith("E_abs__tint"):  # Example: "E_t_01", "E_t_02", etc.
                    self.time_series_datasets.append(item.name)  # Store the dataset name

    def on_item_clicked(self, item):
        """Handle clicking on a dataset or group in the tree widget."""
        # Get the full path of the selected item
        full_path = item.data(0, 1)

        # Clear the previous value display
        self.value_display.clear()

        # Open the file and access the item using the full path
        with h5py.File(self.file_path, 'r') as file:
            try:
                hdf5_object = file[full_path]  # Access the object using its full path

                if isinstance(hdf5_object, h5py.Dataset):  # Dataset
                    self.data = hdf5_object[()]

                    # Display the values
                    if self.data.size == 1:  # Single value
                        value = self.data.item()  # Extract the scalar value
                        self.value_display.setText(f"Selected Value: {value}")
                    else:  # Array
                        self.value_display.setText(f"Selected Dataset:\n{self.data}")

                        # Open the plot window for 1D or 2D datasets
                        if self.data.ndim == 1:  # 1D dataset
                            self.open_plot_window(self.data, '1D')
                        elif self.data.ndim == 2:  # 2D dataset
                            self.open_plot_window(self.data, '2D')
                        elif self.data.ndim == 3:  # 3D dataset
                            self.show_3d_choice_dialog()  # NEW: Open slice dialog for 3D datasets

                elif isinstance(hdf5_object, h5py.Group):  # Group
                    self.value_display.setText("Selected Item is a Group (not a dataset).")
            except KeyError:
                self.value_display.setText("Error: Unable to access the selected item.")

    def show_3d_choice_dialog(self):
        """Let user choose between 2D slice or 3D visualization."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Visualization Choice")
        layout = QVBoxLayout()
        
        label = QLabel("This is a 3D dataset. How would you like to visualize it?")
        layout.addWidget(label)
        
        # 2D slice button - using lambda to pass arguments
        btn_2d = QPushButton("2D Slice", dialog)
        btn_2d.clicked.connect(lambda: self.handle_3d_choice('2D', dialog))
        layout.addWidget(btn_2d)
        
        # 3D visualization button - using lambda to pass arguments
        btn_3d = QPushButton("3D Visualization", dialog)
        btn_3d.clicked.connect(lambda: self.handle_3d_choice('3D', dialog))
        layout.addWidget(btn_3d)
        
        dialog.setLayout(layout)
        dialog.exec_()

    def handle_3d_choice(self, choice, dialog):
        """Handle user's choice of visualization."""
        dialog.close()
        if choice == '2D':
            self.open_slice_dialog(self.data)
        elif choice == '3D':
            self.show_3d_parameter_dialog()

    def show_3d_parameter_dialog(self):
        """Dialog to collect parameters for 3D visualization."""
        dialog = QDialog(self)
        dialog.setWindowTitle("3D Visualization Parameters")
        layout = QFormLayout()
        
        # Add your parameter inputs here
        self.iso_surface_level = QDoubleSpinBox()
        self.iso_surface_level.setRange(0, 1)
        self.iso_surface_level.setValue(0.5)
        layout.addRow("Isosurface Level:", self.iso_surface_level)
        
        self.color_map = QComboBox()
        self.color_map.addItems(["jet", "viridis", "hot", "cool"])
        layout.addRow("Color Map:", self.color_map)
        
        # Add more parameters as needed...
        
        btn_confirm = QPushButton("Visualize", dialog)
        btn_confirm.clicked.connect(lambda: self.launch_mayavi_script(dialog))
        layout.addRow(btn_confirm)
        
        dialog.setLayout(layout)
        dialog.exec_()

    def launch_mayavi_script(self, dialog):
        """Prepare data and launch external Mayavi script."""
        dialog.close()
        
        # Create temporary file for the 3D data
        temp_dir = tempfile.mkdtemp()
        data_path = os.path.join(temp_dir, "3d_data.npy")
        np.save(data_path, self.data)
        
        # Prepare parameters
        params = {
            "data_path": data_path,
            "iso_level": self.iso_surface_level.value(),
            "colormap": self.color_map.currentText()
            # Add more parameters as needed
        }
        
        # Save parameters to JSON
        params_path = os.path.join(temp_dir, "params.json")
        with open(params_path, 'w') as f:
            json.dump(params, f)
        
        # Launch your Mayavi script
        script_path = os.path.join(os.path.dirname(__file__), "your_mayavi_script.py")
        subprocess.Popen([sys.executable, script_path, params_path])

    def open_plot_window(self, data, dataset_type):
        """Open the plot window for 1D or 2D datasets."""
        if not self.plot_window:
            self.plot_window = PlotWindow(self)
        self.plot_window.set_data(data, dataset_type)
        self.plot_window.set_single_value_datasets(self.single_value_datasets)
        self.plot_window.show()

    # Method to open the slice dialog for 3D datasets
    def open_slice_dialog(self, data):
        """Open a dialog to select the axis and slice for 3D datasets."""
        slice_dialog = SliceDialog(self)
        slice_dialog.slice_spinbox.setMaximum(data.shape[2] - 1)  # Set max slice index
        if slice_dialog.exec_() == QDialog.Accepted:
            axis, slice_index, top, bottom, left, right = slice_dialog.get_parameters()

            # Slice the 3D dataset
            if axis == 0:
                sliced_data = data[slice_index, :, :]
            elif axis == 1:
                sliced_data = data[:, slice_index, :]
            elif axis == 2:
                sliced_data = data[:, :, slice_index]

            # Open the plot window with the sliced 2D data
            self.open_plot_window(sliced_data, '2D')

    # Method to open the operation window
    def open_operation_window(self):
        """Open the operation window for dataset manipulation."""
        if not self.operation_window:
            self.operation_window = OperationWindow(self)
        self.operation_window.set_datasets(self.single_value_datasets)
        self.operation_window.show()

    # Method to create a GIF from time-series datasets
    def create_gif(self):
        """Create a GIF from time-series datasets."""
        if not self.time_series_datasets:
            self.value_display.setText("No time-series datasets found.")
            return

        # Sort the time-series datasets by their timestep
        self.time_series_datasets.sort()

        # Open the HDF5 file
        with h5py.File(self.file_path, 'r') as file:

            # Check the shape of the first dataset to determine the axis limits
            first_dataset = file[self.time_series_datasets[0]]
            if first_dataset.ndim != 3:
                self.value_display.setText("Time-series datasets must be 3D.")
                return

            # Open the slice selection dialog
            slice_dialog = SliceDialog(self)
            slice_dialog.slice_spinbox.setMaximum(first_dataset.shape[2] - 1)  # Set max slice index
            if slice_dialog.exec_() != QDialog.Accepted:
                return  # User canceled the dialog

            # Get the selected axis, slice index, and boundary removal values
            axis, slice_index, top, bottom, left, right = slice_dialog.get_parameters()  # NEW: Added boundary values

            # Find the global maximum value across all datasets
            global_max = -np.inf  # Initialize with the smallest possible value
            for dataset_name in self.time_series_datasets:
                dataset = file[dataset_name]
                data = dataset[()]

                # Slice the 3D dataset along the selected axis
                if axis == 0:
                    sliced_data = data[slice_index, :, :]
                elif axis == 1:
                    sliced_data = data[:, slice_index, :]
                elif axis == 2:
                    sliced_data = data[:, :, slice_index]

                # Remove boundary layers from the sliced 2D dataset
                rows, cols = sliced_data.shape
                if top + bottom < rows and left + right < cols:  # Ensure valid boundaries
                    sliced_data = sliced_data[top:rows - bottom, left:cols - right]
                else:
                    print("Invalid boundary removal parameters. Skipping boundary removal.")
                    self.value_display.setText("Invalid boundary removal parameters. Skipping boundary removal.")

                # Update the global maximum value
                current_max = np.max(sliced_data)
                if current_max > global_max:
                    global_max = current_max

            # Apply a small offset to avoid log(0)
            offset = 1e-10
            global_max += offset  # Ensure the maximum value is positive

            # Create a list to store the frames of the GIF
            frames = []

            for dataset_name in self.time_series_datasets:
                # Update progress label
                self.progress_label.setText(f"Processing: {dataset_name}")
                QApplication.processEvents()  # Force UI update

                dataset = file[dataset_name]
                data = dataset[()]

                # Slice the 3D dataset along the selected axis
                if axis == 0:
                    sliced_data = data[slice_index, :, :]
                elif axis == 1:
                    sliced_data = data[:, slice_index, :]
                elif axis == 2:
                    sliced_data = data[:, :, slice_index]

                # Remove boundary layers from the sliced 2D dataset
                rows, cols = sliced_data.shape
                if top + bottom < rows and left + right < cols:  # Ensure valid boundaries
                    sliced_data = sliced_data[top:rows - bottom, left:cols - right]
                else:
                    print("Invalid boundary removal parameters. Skipping boundary removal.")
                    self.value_display.setText("Invalid boundary removal parameters. Skipping boundary removal.")

                # Apply logarithmic transformation using the global maximum value
                log_data = np.log10(np.abs(sliced_data) + offset)  # Ensure all values are positive

                # Create the heatmap
                fig = go.Figure(
                        data=go.Heatmap(
                            z=log_data,
                            colorscale='jet',
                            zmin=np.log10(offset),      # Minimum value (log10(offset))
                            zmax=np.log10(global_max),  # Maximum value (log10(global_max))
                            colorbar=dict(
                                title="log10(Abs(E))",  # Updated colorbar title
                                tickvals=np.linspace(np.log10(offset), np.log10(global_max), 5),  # Linear ticks in log space
                                ticktext=[f"{10**x:.1e}" for x in np.linspace(np.log10(offset), np.log10(global_max), 5)]  # Convert back to linear scale for labels
                            )
                        )
                    )
    
                # Update layout
                fig.update_layout(
                    title=f"Abs(E) = {dataset_name}",
                    xaxis_title="Z",
                    yaxis_title="Y",
                )
    
                # Show the plot
                img_bytes = fig.to_image(format="png",width=1600,height=1200)
                img = imageio.imread(img_bytes)
                frames.append(img)

        # Save the frames as a GIF
        gif_path, _ = QFileDialog.getSaveFileName(
            self, "Save GIF", "", "GIF Files (*.gif);;All Files (*)"
            )
        
        if gif_path:
            if not gif_path.endswith('.gif'):
                gif_path += '.gif'
            imageio.mimsave(gif_path, frames, duration= 200)  # Adjust duration as needed
            self.value_display.setText(f"GIF saved to {gif_path}")
        
        # Reset progress label after completion
        self.progress_label.setText("Progress: Idle")

# hdf5_viewer.py (updated OperationWindow class for 1D, 2D, and sliced 3D datasets)
class OperationWindow(QDialog):
    """A window to perform operations on 1D, 2D, and sliced 3D datasets."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dataset Operations")
        self.setGeometry(200, 200, 400, 350)  # CHANGED: Adjusted window size

        # Layout
        self.layout = QVBoxLayout(self)

        # Dataset selection
        self.dataset_label = QLabel("Select Dataset:", self)
        self.dataset_combobox = QComboBox(self)
        self.layout.addWidget(self.dataset_label)
        self.layout.addWidget(self.dataset_combobox)

        # Operation selection
        self.operation_label = QLabel("Select Operation:", self)
        self.operation_combobox = QComboBox(self)
        self.operation_combobox.addItems([
            "Multiply by Constant", 
            "Fourier Transform"  # NEW: Only these two options
        ])
        self.layout.addWidget(self.operation_label)
        self.layout.addWidget(self.operation_combobox)

        # Constant input (for "Multiply by Constant")
        self.constant_label = QLabel("Constant Value:", self)
        self.constant_input = QLineEdit(self)
        self.constant_input.setPlaceholderText("Enter a constant value")
        self.layout.addWidget(self.constant_label)
        self.layout.addWidget(self.constant_input)

        # NEW: Slice selection for 3D datasets
        self.slice_layout = QHBoxLayout()
        self.layout.addLayout(self.slice_layout)

        self.slice_label = QLabel("Slice Index (for 3D datasets):", self)
        self.slice_layout.addWidget(self.slice_label)

        self.slice_spinbox = QSpinBox(self)
        self.slice_spinbox.setMinimum(0)
        self.slice_spinbox.setMaximum(100)  # Default max, will be updated dynamically
        self.slice_layout.addWidget(self.slice_spinbox)

        self.slice_axis_label = QLabel("Slice Axis:", self)
        self.slice_layout.addWidget(self.slice_axis_label)

        self.slice_axis_combobox = QComboBox(self)
        self.slice_axis_combobox.addItems(["0", "1", "2"])  # Options for axis 0, 1, or 2
        self.slice_layout.addWidget(self.slice_axis_combobox)

        # NEW: Fourier Transform options
        self.ft_layout = QHBoxLayout()
        self.layout.addLayout(self.ft_layout)

        self.ft_shift_checkbox = QCheckBox("Apply FFT Shift", self)  # Option to center the FFT
        self.ft_layout.addWidget(self.ft_shift_checkbox)

        self.ft_log_checkbox = QCheckBox("Log Scale", self)  # Option to apply log scale to FFT
        self.ft_layout.addWidget(self.ft_log_checkbox)

        # Plot button
        self.plot_button = QPushButton("Plot Modified Dataset", self)
        self.plot_button.clicked.connect(self.plot_modified_dataset)
        self.layout.addWidget(self.plot_button)

        # Variables
        self.datasets = {}  # Stores datasets for selection
        self.modified_data = None  # Stores the modified dataset

    def set_datasets(self, datasets):
        """Set the available datasets for selection."""
        self.datasets = datasets
        self.dataset_combobox.clear()
        self.dataset_combobox.addItems(datasets.keys())

    def compute_fourier_transform(self, data):
        """Compute the Fourier Transform of the dataset."""
        if data.ndim == 1:  # 1D dataset
            fft_data = np.fft.fft(data)  # Compute 1D FFT
            if self.ft_shift_checkbox.isChecked():
                fft_data = np.fft.fftshift(fft_data)  # Center the FFT
        elif data.ndim == 2:  # 2D dataset
            fft_data = np.fft.fft2(data)  # Compute 2D FFT
            if self.ft_shift_checkbox.isChecked():
                fft_data = np.fft.fftshift(fft_data)  # Center the FFT
        else:
            print("Fourier Transform is only supported for 1D and 2D datasets.")
            return None

        if self.ft_log_checkbox.isChecked():
            fft_data = np.log(np.abs(fft_data))  # Apply log scale
        else:
            fft_data = np.abs(fft_data)  # Take the magnitude
        return fft_data

    def slice_3d_dataset(self, data):
        """Slice a 3D dataset along the specified axis and index."""
        axis = int(self.slice_axis_combobox.currentText())
        slice_index = self.slice_spinbox.value()

        if axis == 0:
            return data[slice_index, :, :]  # Slice along axis 0
        elif axis == 1:
            return data[:, slice_index, :]  # Slice along axis 1
        elif axis == 2:
            return data[:, :, slice_index]  # Slice along axis 2
        else:
            return None

    def plot_modified_dataset(self):
        """Perform the selected operation and plot the modified dataset."""
        selected_dataset = self.dataset_combobox.currentText()
        data = self.datasets[selected_dataset]

        # NEW: Handle 3D datasets by slicing
        if data.ndim == 3:
            data = self.slice_3d_dataset(data)
            if data is None:
                print("Invalid slice parameters for 3D dataset.")
                return

        if self.operation_combobox.currentText() == "Multiply by Constant":
            try:
                constant = float(self.constant_input.text())
                self.modified_data = data * constant
            except ValueError:
                self.modified_data = None
                print("Invalid constant value.")
        elif self.operation_combobox.currentText() == "Fourier Transform":  # NEW: Fourier Transform
            if data.ndim in [1, 2]:  # Only works for 1D and 2D datasets
                self.modified_data = self.compute_fourier_transform(data)
            else:
                print("Fourier Transform is only supported for 1D and 2D datasets.")
                self.modified_data = None

        if self.modified_data is not None:
            dataset_type = '1D' if self.modified_data.ndim == 1 else '2D'  # Determine dataset type
            self.parent().open_plot_window(self.modified_data, dataset_type)  # Plot the modified dataset


# Added SliceDialog class
class SliceDialog(QDialog):
    """Dialog to select the axis and slice for 3D datasets."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Slice Parameters")
        self.setGeometry(200, 200, 300, 250)  # Adjusted window size

        # Layout
        self.layout = QFormLayout(self)

        # Axis selection
        self.axis_label = QLabel("Axis:", self)
        self.axis_combobox = QComboBox(self)
        self.axis_combobox.addItems(["x", "y", "z"])  # CHANGED: Replaced 0,1,2 with x,y,z
        self.layout.addRow(self.axis_label, self.axis_combobox)

        # Slice selection
        self.slice_label = QLabel("Slice Index:", self)
        self.slice_spinbox = QSpinBox(self)
        self.slice_spinbox.setMinimum(0)
        self.slice_spinbox.setMaximum(100)  # Default max, will be updated dynamically
        self.layout.addRow(self.slice_label, self.slice_spinbox)

        # Boundary removal controls
        self.boundary_layout = QFormLayout()
        self.layout.addRow(self.boundary_layout)

        self.top_label = QLabel("Top Layers:", self)
        self.top_spinbox = QSpinBox(self)
        self.top_spinbox.setMinimum(0)
        self.top_spinbox.setMaximum(100)  # Arbitrary max value
        self.boundary_layout.addRow(self.top_label, self.top_spinbox)

        self.bottom_label = QLabel("Bottom Layers:", self)
        self.bottom_spinbox = QSpinBox(self)
        self.bottom_spinbox.setMinimum(0)
        self.bottom_spinbox.setMaximum(100)
        self.boundary_layout.addRow(self.bottom_label, self.bottom_spinbox)

        self.left_label = QLabel("Left Layers:", self)
        self.left_spinbox = QSpinBox(self)
        self.left_spinbox.setMinimum(0)
        self.left_spinbox.setMaximum(100)
        self.boundary_layout.addRow(self.left_label, self.left_spinbox)

        self.right_label = QLabel("Right Layers:", self)
        self.right_spinbox = QSpinBox(self)
        self.right_spinbox.setMinimum(0)
        self.right_spinbox.setMaximum(100)
        self.boundary_layout.addRow(self.right_label, self.right_spinbox)

        # Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addRow(self.button_box)

    def get_parameters(self):
        """Return the selected axis and slice index."""
        axis = self.axis_combobox.currentText()  # CHANGED: Get the axis label (x, y, z)
        slice_index = self.slice_spinbox.value()

        # NEW: Get boundary removal values
        top = self.top_spinbox.value()
        bottom = self.bottom_spinbox.value()
        left = self.left_spinbox.value()
        right = self.right_spinbox.value()

        # NEW: Map x, y, z to axis indices
        axis_map = {"x": 0, "y": 1, "z": 2}
        return axis_map[axis], slice_index, top, bottom, left, right  # NEW: Added boundary values


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = HDF5Viewer()
    viewer.show()
    sys.exit(app.exec_())
