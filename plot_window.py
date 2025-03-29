# plot_window.py
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QPushButton, QComboBox, QLabel, QLineEdit, QFileDialog,
    QSpinBox, QListWidget, QAbstractItemView )

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np

class PlotWindow(QDialog):
    """A sub-window for plotting 1D and 2D datasets."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Plot Window")
        self.setGeometry(850, 100, 700, 800)                    # Adjusted window size (centerX, centerY, height, width)

        # Layout
        self.layout = QVBoxLayout(self)

        # Matplotlib canvas to show figure
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

        # Form layout for plot title and axis labels
        self.form_layout = QFormLayout()
        self.layout.addLayout(self.form_layout)

#Plot features customized by user. General for 1D and 2D
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

#Controls for 1D plots
        # Line color selection for 1D plots
        self.line_color_label = QLabel("Line Color:", self)
        self.line_color_combobox = QComboBox(self)
        self.line_color_combobox.addItems(["blue", "red", "green", "black", "purple", "orange", "cyan", "magenta"]) 
        self.form_layout.addRow(self.line_color_label, self.line_color_combobox)

        # Line style selection for 1D plots
        self.line_style_label = QLabel("Line Style:", self)
        self.line_style_combobox = QComboBox(self)
        self.line_style_combobox.addItems(["-", "--", "-.", ":", "None"])  # Add common line styles
        self.form_layout.addRow(self.line_style_label, self.line_style_combobox)

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

#Controls for 2D plots
        # Colorbar title input (for 2D plots)
        self.colorbar_title_input = QLineEdit(self)
        self.colorbar_title_input.setPlaceholderText("Enter colorbar title")
        self.form_layout.addRow("Colorbar Title:", self.colorbar_title_input)

        # Colormap selection
        self.colormap_label = QLabel("Colormap:", self)
        self.colormap_combobox = QComboBox(self)
        self.colormap_combobox.addItems(plt.colormaps())  # Add all available colormaps
        self.form_layout.addRow(self.colormap_label, self.colormap_combobox)

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
        # Scale selection (linear or logarithmic)
        self.scale_label = QLabel("Scale:", self)
        self.scale_combobox = QComboBox(self)
        self.scale_combobox.addItems(["linear", "log"])                             # Options for scale
        self.form_layout.addRow(self.scale_label, self.scale_combobox)

        # Plot button (includes boundary removal functionality)
        self.plot_button = QPushButton("Plot", self)
        self.plot_button.clicked.connect(self.plot)
        self.layout.addWidget(self.plot_button)

        # Save plot button
        self.save_button = QPushButton("Save Plot", self)
        self.save_button.clicked.connect(self.save_plot)
        self.layout.addWidget(self.save_button)

        # Variables
        self.data = None
        self.adjusted_data = None                               # Stores the dataset after boundary removal
        self.dataset_type = None                                # '1D' or '2D'

    def set_data(self, data, dataset_type):
        """Set the dataset to be plotted and its type (1D or 2D)."""
        self.data = data
        self.adjusted_data = data  #s Initialize adjusted_data with the original data
        self.dataset_type = dataset_type

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

            # Show line color, line style, and legend options for 1D plots
            self.line_color_label.show()
            self.line_color_combobox.show()
            self.line_style_label.show()
            self.line_style_combobox.show()
            self.form_layout.labelForField(self.legend_input).show()
            self.legend_input.show()

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

            self.colormap_label.hide()
            self.colormap_combobox.hide()
            self.scale_label.hide()
            self.scale_combobox.hide()
            self.form_layout.labelForField(self.colorbar_title_input).hide()
            self.colorbar_title_input.hide()

        else:  # '2D'
            
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

            self.colormap_label.show()
            self.colormap_combobox.show()
            self.scale_label.show()
            self.scale_combobox.show()
            self.form_layout.labelForField(self.colorbar_title_input).show()
            self.colorbar_title_input.show()

            self.left_points.hide()
            self.leftp_spinbox.hide()
            self.right_points.hide()
            self.rightp_spinbox.hide()

            # Hide line color, line style, and legend options for 2D plots
            self.line_color_label.hide()
            self.line_color_combobox.hide()
            self.line_style_label.hide()
            self.line_style_combobox.hide()
            self.form_layout.labelForField(self.legend_input).hide()
            self.legend_input.hide()


    def remove_boundary_layers(self):
        """Remove the specified number of layers/points from the boundaries of the dataset."""
        if self.adjusted_data is None:
            return self.adjusted_data

        if self.dataset_type == '1D':  # 1D dataset
            left = self.leftp_spinbox.value()
            right = self.rightp_spinbox.value()
            length = len(self.adjusted_data)

            if left + right < length:                           # Ensure valid boundaries
                self.adjusted_data = self.adjusted_data[left:length - right]
            else:
                print("Invalid boundary removal parameters. Skipping boundary removal.")

        elif self.dataset_type == '2D':  # 2D dataset
            top = self.top_spinbox.value()
            bottom = self.bottom_spinbox.value()
            left = self.left_spinbox.value()
            right = self.right_spinbox.value()
            rows, cols = self.adjusted_data.shape

            if top + bottom < rows and left + right < cols:  # Ensure valid boundaries
                self.adjusted_data = self.adjusted_data[top:rows - bottom, left:cols - right]
            else:
                print("Invalid boundary removal parameters. Skipping boundary removal.")

        return self.adjusted_data

    def plot(self):
        """Plot the dataset."""
        if self.data is None:
            return

        # Clear the previous plot
        self.figure.clear()

        # Create a new plot
        ax = self.figure.add_subplot(111)

        # Remove boundary layers/points
        self.adjusted_data = self.remove_boundary_layers()

        if self.dataset_type == '1D':  # 1D dataset
            # Get line color, line style, and legend label
            line_color = self.line_color_combobox.currentText()
            line_style = self.line_style_combobox.currentText()
            line_legend = self.legend_input.text()

            ax.grid(True)

            # Plot the data with the selected color and line style
            ax.plot(self.adjusted_data, color=line_color, linestyle=line_style, label=line_legend )

            # Set labels with custom sizes
            ax.set_xlabel(self.x_label_input.text() or "Index", 
                         fontsize=self.x_label_size_spin.value())
            ax.set_ylabel(self.y_label_input.text() or "Value", 
                         fontsize=self.y_label_size_spin.value())
            ax.set_title(self.title_input.text() or "1D Plot",
                         fontsize=self.title_label_size_spin.value())
            if line_legend:
                ax.legend()

        else:  # 2D dataset
            # Get selected colormap
            colormap = self.colormap_combobox.currentText()
            scale = self.scale_combobox.currentText()
            colorbar_title = self.colorbar_title_input.text() or "Value"

            # Plot the data with the selected colormap and scale
            if scale == "linear":
                im = ax.imshow(self.adjusted_data, cmap=colormap, origin='lower')                   # Use adjusted_data
            else:  # "log"
                im = ax.imshow(self.adjusted_data, cmap=colormap, norm="log", origin='lower')       # Use adjusted_data

            #self.figure.colorbar(im, ax=ax)  # Add a colorbar
            # Add colorbar with title
            cbar = self.figure.colorbar(im, ax=ax)
            cbar.set_label(colorbar_title, fontsize=self.y_label_size_spin.value())

            # Set labels with custom sizes
            ax.set_xlabel(self.x_label_input.text() or "X", 
                         fontsize=self.x_label_size_spin.value())
            ax.set_ylabel(self.y_label_input.text() or "Y", 
                         fontsize=self.y_label_size_spin.value())
            
            ax.set_title(self.title_input.text() or "2D Heatmap",
                         fontsize=self.title_label_size_spin.value())

        # Refresh the canvas
        self.canvas.draw()

    def plot_selected(self):
        """Plot all selected 1D datasets with automatic legends."""
        if not self.datasets or self.dataset_type != '1D':
            return
            
        selected_items = self.dataset_list.selectedItems()
        if not selected_items:
            return
            
        # Clear previous plot but keep track of existing plots
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Get plot customization
        line_color = self.line_color_combobox.currentText()
        line_style = self.line_style_combobox.currentText()
        
        # Plot each selected dataset
        for item in selected_items:
            name = item.text()
            data = self.datasets[name]
            
            # Apply boundary removal
            left = self.left_spinbox.value()
            right = self.right_spinbox.value()
            if left + right < len(data):
                data = data[left:len(data)-right]
            
            # Plot with dataset name as legend
            ax.plot(data, color=line_color, linestyle=line_style, label=name)
            self.current_plots[name] = data  # Track plotted datasets
        
        # Add legend and labels
        if len(selected_items) >= 1:
            ax.legend()
            
        ax.set_xlabel(self.x_label_input.text() or "Index")
        ax.set_ylabel(self.y_label_input.text() or "Value")
        ax.set_title(self.title_input.text() or "1D Plot Comparison")
        
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
