"""Settings dialog for EchoPy."""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QSlider,
    QPushButton,
    QSpinBox,
    QGroupBox,
    QFormLayout,
)
from PySide6.QtCore import Qt, Signal, QTimer


class SettingsDialog(QDialog):
    """Settings dialog for audio and performance configuration."""

    # Signals
    device_changed = Signal(int)
    smoothing_changed = Signal(float)
    gain_changed = Signal(float)
    sample_rate_changed = Signal(int)
    opacity_changed = Signal(float)
    fps_changed = Signal(int)

    def __init__(self, parent=None):
        """Initialize settings dialog."""
        super().__init__(parent)
        self.setWindowTitle("EchoPy Settings")
        self.setModal(True)
        self.setMinimumWidth(400)

        # State tracking (to prevent redundant apply calls)
        self.current_state = {
            "device": -1,
            "sample_rate": 44100,
            "fft_size": 2048,
            "smoothing": 0.8,
            "gain": 100.0,
            "opacity": 0.3,
            "fps_limit": 60,
        }

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

        # Gain / Height slider
        gain_layout = QHBoxLayout()
        self.gain_slider = QSlider(Qt.Horizontal)
        self.gain_slider.setMinimum(10)
        self.gain_slider.setMaximum(300)
        self.gain_slider.setValue(100)
        self.gain_slider.valueChanged.connect(self._on_gain_changed)

        self.gain_label = QLabel("100%")
        gain_layout.addWidget(self.gain_slider)
        gain_layout.addWidget(self.gain_label)

        viz_layout.addRow("Gain / Height:", gain_layout)

        # Background opacity
        opacity_layout = QHBoxLayout()
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setMinimum(0)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(30)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)

        self.opacity_label = QLabel("30%")

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

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #00ff00; font-weight: bold;")

        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self._on_apply)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)

        button_layout.addWidget(self.status_label)
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

        self.device_combo.addItem("✨ Default System Audio (Auto)", -1)

        for device in devices:
            name = f"{device['name']} ({device['channels']} ch)"
            self.device_combo.addItem(name, device["index"])

    def load_current_settings(
        self,
        device_idx: int,
        sample_rate: int,
        fft_size: int,
        smoothing: float,
        gain: float,
        opacity: float,
        fps: int,
    ):
        """Load current settings into dialog state to prevent redundant updates."""
        self.current_state = {
            "device": device_idx,
            "sample_rate": sample_rate,
            "fft_size": fft_size,
            "smoothing": smoothing,
            "gain": gain,
            "opacity": opacity,
            "fps_limit": fps,
        }

        # Update UI to match
        idx = self.device_combo.findData(device_idx)
        if idx >= 0:
            self.device_combo.setCurrentIndex(idx)
        else:
            # If current device not found (e.g. PyAudioWPatch loopback), select Auto
            self.device_combo.setCurrentIndex(0)  # Index 0 is now Auto (-1)

        self.sample_rate_combo.setCurrentText(str(sample_rate))
        self.fft_combo.setCurrentText(str(fft_size))

        self.smoothing_slider.setValue(int(smoothing * 100))
        self.gain_slider.setValue(int(gain))
        self.opacity_slider.setValue(int(opacity * 100))
        self.fps_spin.setValue(fps)

    def get_smoothing(self) -> float:
        """Get smoothing value."""
        return self.smoothing_slider.value() / 100.0

    def get_gain(self) -> float:
        """Get gain value."""
        return self.gain_slider.value()  # Return as percentage multiplier (e.g. 100.0)

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

    def _on_gain_changed(self, value: int):
        """Handle gain slider change."""
        self.gain_label.setText(f"{value}%")

    def _on_opacity_changed(self, value: int):
        """Handle opacity slider change."""
        self.opacity_label.setText(f"{value}%")

    def _on_apply(self):
        """Handle apply button click."""
        # Check and Emit signals ONLY if changed

        # 1. Device (Critical - causes restart)
        new_device = self.get_selected_device()
        if new_device != self.current_state["device"] and new_device is not None:
            self.device_changed.emit(new_device)
            self.current_state["device"] = new_device

        # 2. Smoothing
        new_smoothing = self.get_smoothing()
        if abs(new_smoothing - self.current_state["smoothing"]) > 0.01:
            self.smoothing_changed.emit(new_smoothing)
            self.current_state["smoothing"] = new_smoothing

        # 3. Gain
        new_gain = self.get_gain()
        if abs(new_gain - self.current_state["gain"]) > 0.1:
            self.gain_changed.emit(new_gain)
            self.current_state["gain"] = new_gain

        # 4. Sample Rate
        new_sr = self.get_sample_rate()
        if new_sr != self.current_state["sample_rate"]:
            self.sample_rate_changed.emit(new_sr)
            self.current_state["sample_rate"] = new_sr

        # 5. Opacity
        new_opacity = self.get_opacity()
        if abs(new_opacity - self.current_state["opacity"]) > 0.01:
            self.opacity_changed.emit(new_opacity)
            self.current_state["opacity"] = new_opacity

        # 6. FPS Limit
        new_fps = self.get_fps_limit()
        if new_fps != self.current_state["fps_limit"]:
            self.fps_changed.emit(new_fps)
            self.current_state["fps_limit"] = new_fps

        self.status_label.setText("Settings Applied!")
        QTimer.singleShot(2000, lambda: self.status_label.setText(""))
