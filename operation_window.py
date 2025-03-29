import numpy as np

#import PyQt5 widgets
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
    QPushButton, QTreeWidget, QTreeWidgetItem, QFileDialog, QTextEdit, QLabel, 
    QDialog, QFormLayout, QSpinBox, QDialogButtonBox, QComboBox, QLineEdit, QCheckBox, QDoubleSpinBox
)

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

        # Handle 3D datasets by slicing
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