# plot_window.py
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QPushButton, QComboBox, QLabel, QLineEdit, QFileDialog
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


class PlotWindow(QDialog):
    """A sub-window for plotting 1D and 2D datasets."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Plot Window")
        self.setGeometry(200, 200, 800, 600)

        # Layout
        self.layout = QVBoxLayout(self)

        # Matplotlib canvas
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

        # Form layout for plot title and axis labels
        self.form_layout = QFormLayout()
        self.layout.addLayout(self.form_layout)

        # Plot title input
        self.title_input = QLineEdit(self)
        self.title_input.setPlaceholderText("Enter plot title")
        self.form_layout.addRow("Plot Title:", self.title_input)

        # X-axis label input
        self.x_label_input = QLineEdit(self)
        self.x_label_input.setPlaceholderText("Enter x-axis label")
        self.form_layout.addRow("X-Axis Label:", self.x_label_input)

        # Y-axis label input
        self.y_label_input = QLineEdit(self)
        self.y_label_input.setPlaceholderText("Enter y-axis label")
        self.form_layout.addRow("Y-Axis Label:", self.y_label_input)

        # Colormap selection (for 2D heatmap)
        self.colormap_label = QLabel("Colormap:", self)
        self.colormap_combobox = QComboBox(self)
        self.colormap_combobox.addItems(plt.colormaps())  # Add all available colormaps
        self.form_layout.addRow(self.colormap_label, self.colormap_combobox)

        # Axis selection dropdowns (for 2D datasets)
        self.axis_layout = QHBoxLayout()
        self.layout.addLayout(self.axis_layout)

        self.x_axis_label = QLabel("X Axis:", self)
        self.axis_layout.addWidget(self.x_axis_label)

        self.x_axis_combobox = QComboBox(self)
        self.axis_layout.addWidget(self.x_axis_combobox)

        self.y_axis_label = QLabel("Y Axis:", self)
        self.axis_layout.addWidget(self.y_axis_label)

        self.y_axis_combobox = QComboBox(self)
        self.axis_layout.addWidget(self.y_axis_combobox)

        # Plot button
        self.plot_button = QPushButton("Plot", self)
        self.plot_button.clicked.connect(self.plot)
        self.layout.addWidget(self.plot_button)

        # Save plot button
        self.save_button = QPushButton("Save Plot", self)
        self.save_button.clicked.connect(self.save_plot)
        self.layout.addWidget(self.save_button)

        # Variables
        self.data = None
        self.single_value_datasets = {}
        self.dataset_type = None  # '1D' or '2D'

    def set_data(self, data, dataset_type):
        """Set the dataset to be plotted and its type (1D or 2D)."""
        self.data = data
        self.dataset_type = dataset_type

        # Show/hide axis selection based on dataset type
        if self.dataset_type == '1D':
            self.x_axis_label.hide()
            self.x_axis_combobox.hide()
            self.y_axis_label.hide()
            self.y_axis_combobox.hide()
            self.colormap_label.hide()
            self.colormap_combobox.hide()
        else:  # '2D'
            self.x_axis_label.show()
            self.x_axis_combobox.show()
            self.y_axis_label.show()
            self.y_axis_combobox.show()
            self.colormap_label.show()
            self.colormap_combobox.show()

    def set_single_value_datasets(self, single_value_datasets):
        """Set the single-value datasets for axis selection (for 2D datasets)."""
        self.single_value_datasets = single_value_datasets
        self.x_axis_combobox.clear()
        self.y_axis_combobox.clear()
        self.x_axis_combobox.addItems(single_value_datasets.keys())
        self.y_axis_combobox.addItems(single_value_datasets.keys())

    def plot(self):
        """Plot the dataset."""
        if self.data is None:
            return

        # Clear the previous plot
        self.figure.clear()

        # Create a new plot
        ax = self.figure.add_subplot(111)

        if self.dataset_type == '1D':  # 1D dataset
            ax.plot(self.data)
            ax.set_xlabel(self.x_label_input.text() or "Index")
            ax.set_ylabel(self.y_label_input.text() or "Value")
            ax.set_title(self.title_input.text() or "1D Plot")
        else:  # 2D dataset
            # Get selected colormap
            colormap = self.colormap_combobox.currentText()

            # Create a heatmap
            im = ax.imshow(self.data, cmap=colormap)
            self.figure.colorbar(im, ax=ax)  # Add a colorbar

            ax.set_xlabel(self.x_label_input.text() or "X Axis")
            ax.set_ylabel(self.y_label_input.text() or "Y Axis")
            ax.set_title(self.title_input.text() or "2D Heatmap")

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
        self.figure.savefig(file_path)
