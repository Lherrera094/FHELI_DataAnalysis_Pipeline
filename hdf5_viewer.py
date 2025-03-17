# hdf5_viewer.py
import sys
import h5py
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QTreeWidget, QTreeWidgetItem, QFileDialog, QTextEdit
)
from plot_window import PlotWindow


class HDF5Viewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HDF5 File Viewer")
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

        # Exit button
        self.exit_button = QPushButton("Exit", self)
        self.exit_button.clicked.connect(self.close)  # Connect to the close method
        self.top_layout.addWidget(self.exit_button)

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

        # Variables
        self.file_path = None
        self.data = None
        self.single_value_datasets = {}  # Stores single-value datasets for axis selection
        self.plot_window = None  # Sub-window for plotting

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = HDF5Viewer()
    viewer.show()
    sys.exit(app.exec_())
