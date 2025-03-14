import sys
import h5py
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QTreeWidget, QTreeWidgetItem, QFileDialog, QLabel
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class HDF5Viewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HDF5 File Viewer")
        self.setGeometry(100, 100, 800, 600)

        # Main widget and layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)

        # Top layout for the button
        self.top_layout = QHBoxLayout()
        self.main_layout.addLayout(self.top_layout)

        # Load file button
        self.load_button = QPushButton("Load HDF5 File", self)
        self.load_button.clicked.connect(self.load_file)
        self.top_layout.addWidget(self.load_button)

        # Add a stretch to push the button to the left
        self.top_layout.addStretch()

        # Tree widget to display groups and datasets
        self.tree_widget = QTreeWidget(self)
        self.tree_widget.setHeaderLabel("HDF5 File Structure")
        self.tree_widget.itemClicked.connect(self.on_item_clicked)
        self.main_layout.addWidget(self.tree_widget)

        # Label to display single values
        self.value_label = QLabel("Selected Value: None", self)
        self.main_layout.addWidget(self.value_label)

        # Matplotlib canvas for plotting
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.main_layout.addWidget(self.canvas)

        # Variables
        self.file_path = None
        self.data = None

    def load_file(self):
        """Open a file dialog to load an HDF5 file."""
        self.file_path, _ = QFileDialog.getOpenFileName(
            self, "Open HDF5 File", "", "HDF5 Files (*.h5 *.hdf5)"
        )
        if not self.file_path:
            return

        # Clear the tree widget
        self.tree_widget.clear()

        # Populate the tree widget with the file's structure
        with h5py.File(self.file_path, 'r') as file:
            self.populate_tree(file, self.tree_widget)

    def populate_tree(self, node, parent_item):
        """Recursively populate the tree widget with groups and datasets."""
        for name, item in node.items():
            if isinstance(item, h5py.Group):
                # Add a group item
                group_item = QTreeWidgetItem(parent_item, [name])
                self.populate_tree(item, group_item)  # Recursively add subgroups
            elif isinstance(item, h5py.Dataset):
                # Add a dataset item
                dataset_item = QTreeWidgetItem(parent_item, [name])
                dataset_item.setData(0, 1, item)  # Store the dataset object in the item

    def on_item_clicked(self, item):
        """Handle clicking on a dataset in the tree widget."""
        # Check if the item is a dataset
        dataset = item.data(0, 1)
        if isinstance(dataset, h5py.Dataset):
            self.data = dataset[()]

            # Clear the previous plot and label
            self.figure.clear()
            self.value_label.setText("Selected Value: None")

            # Check the shape and size of the dataset
            if self.data.size == 1:  # Single value
                value = self.data.item()  # Extract the scalar value
                self.value_label.setText(f"Selected Value: {value}")
            elif self.data.ndim == 1:  # 1D data
                ax = self.figure.add_subplot(111)
                ax.plot(self.data)
                ax.set_title(item.text(0))
            elif self.data.ndim == 2:  # 2D data
                ax = self.figure.add_subplot(111)
                ax.imshow(self.data, cmap='viridis')
                ax.set_title(item.text(0))
            elif self.data.ndim == 3:  # 3D data (plot first slice)
                ax = self.figure.add_subplot(111)
                ax.imshow(self.data[0], cmap='viridis')  # Example: plot the first slice
                ax.set_title(item.text(0))

            self.canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = HDF5Viewer()
    viewer.show()
    sys.exit(app.exec_())
