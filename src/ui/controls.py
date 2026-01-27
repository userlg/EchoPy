"""Control panel for EchoPy visualizer."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                                QComboBox, QLabel, QFileDialog, QGridLayout)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor
from themes import get_theme_names


class ControlPanel(QWidget):
    """Control panel widget with style and theme selectors."""
    
    # Signals
    style_changed = Signal(str)
    theme_changed = Signal(str)
    background_changed = Signal(str)
    background_cleared = Signal()
    settings_requested = Signal()
    
    def __init__(self, parent=None):
        """Initialize control panel."""
        super().__init__(parent)
        
        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setObjectName("ControlPanel")
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI components."""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("EchoPy Controls")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        layout.addWidget(title)
        
        # Style selector
        style_layout = QVBoxLayout()
        style_label = QLabel("Visualization Style:")
        
        self.style_combo = QComboBox()
        self.style_combo.addItems([
            "Spectrum Bars",
            "Waveform",
            "Circular Spectrum",
            "Particles",
            "Radial Bars",
            "Fire Effect",
            "Matrix Rain",
            "Oscilloscope",
            "Frequency Rings",
            "Audio Lines"
        ])
        self.style_combo.currentTextChanged.connect(self._on_style_changed)
        
        style_layout.addWidget(style_label)
        style_layout.addWidget(self.style_combo)
        layout.addLayout(style_layout)
        
        # Theme selector
        theme_layout = QVBoxLayout()
        theme_label = QLabel("Color Theme:")
        
        # Theme buttons in grid
        theme_grid = QGridLayout()
        theme_grid.setSpacing(5)
        
        themes = get_theme_names()
        self.theme_buttons = []
        
        for i, theme_name in enumerate(themes):
            btn = QPushButton(theme_name)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, name=theme_name.lower(): self._on_theme_clicked(name))
            btn.setMinimumHeight(30)
            
            row = i // 2
            col = i % 2
            theme_grid.addWidget(btn, row, col)
            self.theme_buttons.append(btn)
        
        # Set first theme as checked
        if self.theme_buttons:
            self.theme_buttons[0].setChecked(True)
        
        theme_layout.addWidget(theme_label)
        theme_layout.addLayout(theme_grid)
        layout.addLayout(theme_layout)
        
        # Background controls
        bg_layout = QVBoxLayout()
        bg_label = QLabel("Background:")
        
        bg_buttons = QHBoxLayout()
        
        self.load_bg_btn = QPushButton("Load Image")
        self.load_bg_btn.clicked.connect(self._on_load_background)
        
        self.clear_bg_btn = QPushButton("Clear")
        self.clear_bg_btn.clicked.connect(self._on_clear_background)
        
        bg_buttons.addWidget(self.load_bg_btn)
        bg_buttons.addWidget(self.clear_bg_btn)
        
        bg_layout.addWidget(bg_label)
        bg_layout.addLayout(bg_buttons)
        layout.addLayout(bg_layout)
        
        # Settings button
        self.settings_btn = QPushButton("Settings")
        self.settings_btn.clicked.connect(self.settings_requested.emit)
        layout.addWidget(self.settings_btn)
        
        # Close button
        close_btn = QPushButton("Hide Controls")
        close_btn.clicked.connect(self.hide)
        layout.addWidget(close_btn)
        
        layout.addStretch()
        
        self.setLayout(layout)
        self.setFixedWidth(250)
    
    def _on_style_changed(self, style_name: str):
        """Handle style change."""
        # Convert display name to internal name
        style_map = {
            "Spectrum Bars": "spectrum_bars",
            "Waveform": "waveform",
            "Circular Spectrum": "circular",
            "Particles": "particles",
            "Radial Bars": "radial_bars",
            "Fire Effect": "fire_effect",
            "Matrix Rain": "matrix_rain",
            "Oscilloscope": "oscilloscope",
            "Frequency Rings": "frequency_rings",
            "Audio Lines": "audio_lines"
        }
        
        internal_name = style_map.get(style_name, "spectrum_bars")
        self.style_changed.emit(internal_name)
    
    def _on_theme_clicked(self, theme_name: str):
        """Handle theme button click."""
        # Uncheck other theme buttons
        for btn in self.theme_buttons:
            if btn.text().lower() != theme_name:
                btn.setChecked(False)
        
        self.theme_changed.emit(theme_name)
    
    def _on_load_background(self):
        """Handle load background button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Background Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_path:
            self.background_changed.emit(file_path)
    
    def _on_clear_background(self):
        """Handle clear background button click."""
        self.background_cleared.emit()
