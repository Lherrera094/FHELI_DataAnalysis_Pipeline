# hdf5_viewer.py
import sys
import h5py
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
    QPushButton, QTreeWidget, QTreeWidgetItem, QFileDialog, QTextEdit, QLabel, 
    QDialog, QFormLayout, QSpinBox, QDialogButtonBox, QComboBox
)
from plot_window import PlotWindow
import plotly.graph_objects as go
import imageio.v2 as imageio

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
                elif isinstance(hdf5_object, h5py.Group):  # Group
                    self.value_display.setText("Selected Item is a Group (not a dataset).")
            except KeyError:
                self.value_display.setText("Error: Unable to access the selected item.")

    def open_plot_window(self, data, dataset_type):
        """Open the plot window for 1D or 2D datasets."""
        if not self.plot_window:
            self.plot_window = PlotWindow(self)
        self.plot_window.set_data(data, dataset_type)
        self.plot_window.set_single_value_datasets(self.single_value_datasets)
        self.plot_window.show()

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

            # NEW: Open the slice selection dialog
            slice_dialog = SliceDialog(self)
            slice_dialog.slice_spinbox.setMaximum(first_dataset.shape[0] - 1)  # Set max slice index
            if slice_dialog.exec_() != QDialog.Accepted:
                return  # User canceled the dialog

            # Get the selected axis and slice index
            axis, slice_index = slice_dialog.get_parameters()

            # Create a list to store the frames of the GIF
            frames = []

            for dataset_name in self.time_series_datasets:
                # Update progress label
                self.progress_label.setText(f"Processing: {dataset_name}")
                QApplication.processEvents()  # Force UI update

                dataset = file[dataset_name]
                data = dataset[()]
                offset = 1e-16

                # Slice the 3D dataset along the selected axis
                if axis == 0:
                    sliced_data = data[slice_index, :, :]
                elif axis == 1:
                    sliced_data = data[:, slice_index, :]
                elif axis == 2:
                    sliced_data = data[:, :, slice_index]

                z_log = np.log(sliced_data + offset)

                fig = go.Figure(    data=go.Heatmap(
                                    #z = sliced_data,                # Flattened volume data
                                    z = z_log,
                                    colorscale='jet',               # Choose a colorscale
                                    zmin=np.min( np.log10(1e-10) ),
                                    zmax=np.max( np.log10(2) ),
                                    colorbar=dict(
                                                    title="logAbs(E)",
                                                    tickvals= np.logspace( 1e-10, 2, 4),
                                                    ticktext= [f"{1e-10}","0.1","1","2",f"{2}"]
                                    )  
                                ) )
    
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
            imageio.mimsave(gif_path, frames, duration=0.5)  # Adjust duration as needed
            self.value_display.setText(f"GIF saved to {gif_path}")
        
        # Reset progress label after completion
        self.progress_label.setText("Progress: Idle")


# Added SliceDialog class
class SliceDialog(QDialog):
    """Dialog to select the axis and slice for 3D datasets."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Slice Parameters")
        self.setGeometry(200, 200, 300, 150)

        # Layout
        self.layout = QFormLayout(self)

        # Axis selection
        self.axis_label = QLabel("Axis:", self)
        self.axis_combobox = QComboBox(self)
        self.axis_combobox.addItems(["x", "y", "z"])  # Options for axis 0, 1, or 2
        self.layout.addRow(self.axis_label, self.axis_combobox)

        # Slice selection
        self.slice_label = QLabel("Slice Index:", self)
        self.slice_spinbox = QSpinBox(self)
        self.slice_spinbox.setMinimum(0)
        self.slice_spinbox.setMaximum(100)  # Default max, will be updated dynamically
        self.layout.addRow(self.slice_label, self.slice_spinbox)

        # Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addRow(self.button_box)

    def get_parameters(self):
        """Return the selected axis and slice index."""
        axis = int(self.axis_combobox.currentText())
        slice_index = self.slice_spinbox.value()
        return axis, slice_index


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = HDF5Viewer()
    viewer.show()
    sys.exit(app.exec_())
