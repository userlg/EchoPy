"""Settings dialog for EchoPy."""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                                QComboBox, QSlider, QPushButton, QSpinBox,
                                QGroupBox, QFormLayout)
from PySide6.QtCore import Qt, Signal


class SettingsDialog(QDialog):
    """Settings dialog for audio and performance configuration."""
    
    # Signals
    device_changed = Signal(int)
    smoothing_changed = Signal(float)
    sample_rate_changed = Signal(int)
    
    def __init__(self, parent=None):
        """Initialize settings dialog."""
        super().__init__(parent)
        self.setWindowTitle("EchoPy Settings")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI components."""
        layout = QVBoxLayout()
        
        # Audio settings group
        audio_group = QGroupBox("Audio Settings")
        audio_layout = QFormLayout()
        
        # Device selector
        self.device_combo = QComboBox()
        audio_layout.addRow("Input Device:", self.device_combo)
        
        # Sample rate
        self.sample_rate_combo = QComboBox()
        self.sample_rate_combo.addItems(["22050", "44100", "48000"])
        self.sample_rate_combo.setCurrentText("44100")
        audio_layout.addRow("Sample Rate:", self.sample_rate_combo)
        
        # FFT size
        self.fft_combo = QComboBox()
        self.fft_combo.addItems(["1024", "2048", "4096", "8192"])
        self.fft_combo.setCurrentText("2048")
        audio_layout.addRow("FFT Size:", self.fft_combo)
        
        audio_group.setLayout(audio_layout)
        layout.addWidget(audio_group)
        
        # Visualization settings group
        viz_group = QGroupBox("Visualization Settings")
        viz_layout = QFormLayout()
        
        # Smoothing slider
        smoothing_layout = QHBoxLayout()
        self.smoothing_slider = QSlider(Qt.Horizontal)
        self.smoothing_slider.setMinimum(0)
        self.smoothing_slider.setMaximum(100)
        self.smoothing_slider.setValue(80)
        self.smoothing_slider.valueChanged.connect(self._on_smoothing_changed)
        
        self.smoothing_label = QLabel("0.80")
        smoothing_layout.addWidget(self.smoothing_slider)
        smoothing_layout.addWidget(self.smoothing_label)
        
        viz_layout.addRow("Smoothing:", smoothing_layout)
        
        # Background opacity
        opacity_layout = QHBoxLayout()
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setMinimum(0)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(30)
        
        self.opacity_label = QLabel("30%")
        self.opacity_slider.valueChanged.connect(
            lambda v: self.opacity_label.setText(f"{v}%")
        )
        
        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addWidget(self.opacity_label)
        
        viz_layout.addRow("BG Opacity:", opacity_layout)
        
        # FPS limit
        self.fps_spin = QSpinBox()
        self.fps_spin.setMinimum(15)
        self.fps_spin.setMaximum(120)
        self.fps_spin.setValue(60)
        self.fps_spin.setSuffix(" FPS")
        
        viz_layout.addRow("FPS Limit:", self.fps_spin)
        
        viz_group.setLayout(viz_layout)
        layout.addWidget(viz_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self._on_apply)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(self.apply_btn)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def set_devices(self, devices: list):
        """
        Set available audio devices.
        
        Args:
            devices: List of device info dictionaries
        """
        self.device_combo.clear()
        
        for device in devices:
            name = f"{device['name']} ({device['channels']} ch)"
            self.device_combo.addItem(name, device['index'])
    
    def get_smoothing(self) -> float:
        """Get smoothing value."""
        return self.smoothing_slider.value() / 100.0
    
    def get_opacity(self) -> float:
        """Get background opacity value."""
        return self.opacity_slider.value() / 100.0
    
    def get_fps_limit(self) -> int:
        """Get FPS limit."""
        return self.fps_spin.value()
    
    def get_selected_device(self) -> int:
        """Get selected device index."""
        return self.device_combo.currentData()
    
    def get_sample_rate(self) -> int:
        """Get selected sample rate."""
        return int(self.sample_rate_combo.currentText())
    
    def _on_smoothing_changed(self, value: int):
        """Handle smoothing slider change."""
        self.smoothing_label.setText(f"{value / 100:.2f}")
    
    def _on_apply(self):
        """Handle apply button click."""
        # Emit signals
        device_idx = self.get_selected_device()
        if device_idx is not None:
            self.device_changed.emit(device_idx)
        
        self.smoothing_changed.emit(self.get_smoothing())
        self.sample_rate_changed.emit(self.get_sample_rate())
