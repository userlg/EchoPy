"""Control panel for EchoPy visualizer."""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                                QComboBox, QLabel, QFileDialog, QGridLayout, QFrame,
                                QGraphicsDropShadowEffect)
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QColor, QIcon
from themes import get_theme_names
from utils import get_resource_path
import os


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
        
        # Transparent main widget to allow custom container shape
        self.setStyleSheet("background: transparent;")
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI components."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        self.container = QFrame()
        self.container.setObjectName("MainContainer")
        
        # Get absolute path for arrow icon and normalize slashes for CSS
        arrow_icon = get_resource_path(os.path.join("resources", "icons", "arrow_down.svg")).replace("\\", "/")
        
        self.container.setStyleSheet(f"""
            QFrame#MainContainer {{
                background-color: #1a1a1a;
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 16px;
            }}
            QLabel {{
                color: #ffffff;
                font-family: 'Segoe UI', sans-serif;
                font-weight: 500;
            }}
            QPushButton {{
                background-color: #333333;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 6px;
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: #444444;
                border-color: #00d2ff;
            }}
            QPushButton:checked {{
                background-color: #00d2ff;
                color: #000000;
            }}
            QComboBox {{
                background-color: #333333;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 6px;
                padding: 5px;
                min-height: 25px;
            }}
            QComboBox:hover {{
                border-color: #00d2ff;
                background-color: #404040;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border-left-width: 0px;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
                background-color: transparent;
            }}
            QComboBox::down-arrow {{
                image: url({arrow_icon});
                width: 16px;
                height: 16px;
                margin-right: 10px;
            }}
            QComboBox QAbstractItemView {{
                background-color: #2b2b2b;
                color: #ffffff;
                selection-background-color: #00d2ff;
                selection-color: #000000;
                border: 1px solid #555555;
                border-radius: 4px;
                outline: none;
            }}
        """)
        
        # Add drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 5)
        self.container.setGraphicsEffect(shadow)
        
        # Internal layout
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("EchoPy Controls")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: white; margin-bottom: 5px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Style selector
        style_layout = QVBoxLayout()
        style_label = QLabel("Visualization Style")
        style_label.setStyleSheet("font-weight: bold; color: #aaa;")
        
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
        theme_label = QLabel("Color Theme")
        theme_label.setStyleSheet("font-weight: bold; color: #aaa;")
        
        # Theme buttons in grid
        theme_grid = QGridLayout()
        theme_grid.setSpacing(8)
        
        themes = get_theme_names()
        self.theme_buttons = []
        
        for i, theme_name in enumerate(themes):
            btn = QPushButton(theme_name)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, name=theme_name.lower(): self._on_theme_clicked(name))
            btn.setMinimumHeight(30)
            btn.setCursor(Qt.PointingHandCursor)
            
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
        bg_label = QLabel("Background")
        bg_label.setStyleSheet("font-weight: bold; color: #aaa;")
        
        bg_buttons = QHBoxLayout()
        
        self.load_bg_btn = QPushButton(" Load BG")
        self.load_bg_btn.clicked.connect(self._on_load_background)
        self.load_bg_btn.setCursor(Qt.PointingHandCursor)
        # Set icon
        icon_path = get_resource_path(os.path.join("resources", "icons", "upload.svg"))
        if os.path.exists(icon_path):
            self.load_bg_btn.setIcon(QIcon(icon_path))
            self.load_bg_btn.setIconSize(QSize(18, 18))
        
        self.clear_bg_btn = QPushButton(" Clear")
        self.clear_bg_btn.clicked.connect(self._on_clear_background)
        self.clear_bg_btn.setCursor(Qt.PointingHandCursor)
        # Set icon
        icon_path = get_resource_path(os.path.join("resources", "icons", "trash.svg"))
        if os.path.exists(icon_path):
             self.clear_bg_btn.setIcon(QIcon(icon_path))
             self.clear_bg_btn.setIconSize(QSize(18, 18))
        
        bg_buttons.addWidget(self.load_bg_btn)
        bg_buttons.addWidget(self.clear_bg_btn)
        
        bg_layout.addWidget(bg_label)
        bg_layout.addLayout(bg_buttons)
        layout.addLayout(bg_layout)
        
        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: rgba(255, 255, 255, 20); border: none; height: 1px;")
        layout.addWidget(line)
        
        # Settings button
        self.settings_btn = QPushButton(" Preferences")
        self.settings_btn.clicked.connect(self.settings_requested.emit)
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        # Set icon
        icon_path = get_resource_path(os.path.join("resources", "icons", "settings.svg"))
        if os.path.exists(icon_path):
             self.settings_btn.setIcon(QIcon(icon_path))
             self.settings_btn.setIconSize(QSize(18, 18))
        layout.addWidget(self.settings_btn)
        
        # Close button
        close_btn = QPushButton(" Hide Controls")
        close_btn.clicked.connect(self.hide)
        close_btn.setCursor(Qt.PointingHandCursor)
        # Set icon
        icon_path = get_resource_path(os.path.join("resources", "icons", "hide.svg"))
        if os.path.exists(icon_path):
             close_btn.setIcon(QIcon(icon_path))
             close_btn.setIconSize(QSize(18, 18))
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 50, 50, 50);
                border: 1px solid rgba(255, 50, 50, 100);
            }
            QPushButton:hover {
                background-color: rgba(255, 50, 50, 100);
            }
        """)
        layout.addWidget(close_btn)
        
        # Add container to main layout
        main_layout.addWidget(self.container)
        self.setLayout(main_layout)
        self.setFixedWidth(280)
    
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

    def set_current_style(self, style_name: str):
        """Set the current style programmatically (e.g. on load)."""
        # Inverse mapping
        style_map = {
            "spectrum_bars": "Spectrum Bars",
            "waveform": "Waveform",
            "circular": "Circular Spectrum",
            "particles": "Particles",
            "radial_bars": "Radial Bars",
            "fire_effect": "Fire Effect",
            "matrix_rain": "Matrix Rain",
            "oscilloscope": "Oscilloscope",
            "frequency_rings": "Frequency Rings",
            "audio_lines": "Audio Lines"
        }
        display_name = style_map.get(style_name)
        if display_name:
            self.style_combo.blockSignals(True)
            self.style_combo.setCurrentText(display_name)
            self.style_combo.blockSignals(False)

    def set_current_theme_name(self, theme_name: str):
        """Set the current theme button programmatically."""
        self.blockSignals(True)
        found = False
        for btn in self.theme_buttons:
            if btn.text().lower() == theme_name.lower():
                btn.setChecked(True)
                found = True
            else:
                btn.setChecked(False)
        self.blockSignals(False)
