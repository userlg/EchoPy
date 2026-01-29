"""Main window for EchoPy visualizer."""

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QMenuBar,
                                QMenu, QMessageBox, QPushButton)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QKeySequence, QPixmap
from visualizer import VisualizerWidget
from audio_processor import AudioProcessor
from visualizer_factory import VisualizerFactory
from ui.controls import ControlPanel
from ui.settings_dialog import SettingsDialog
from themes import get_theme
from utils import Config, SmoothingBuffer, load_image, logger, get_resource_path
import os
import sys


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        """Initialize main window."""
        super().__init__()
        
        # Configuration
        self.config = Config()
        
        # Initialize components
        # DIP: Inject smoothing buffer
        fft_size = self.config.get("fft_size", 2048)
        smoothing = self.config.get("smoothing", 0.8)
        smoother = SmoothingBuffer(fft_size // 2, smoothing)
        
        self.audio_processor = AudioProcessor(
            sample_rate=self.config.get("sample_rate", 44100),
            fft_size=fft_size,
            smoother=smoother
        )
        
        # Create visualizer widget
        self.visualizer_widget = VisualizerWidget()
        
        # Create control panel
        self.control_panel = ControlPanel()
        
        # Create settings dialog
        
        # Create settings dialog
        self.settings_dialog = SettingsDialog(self)
        
        # Setup UI
        self._setup_ui()
        self._setup_shortcuts() # Re-enabled shortcuts even without menu bar
        self._connect_signals()
        
        # Load saved configuration (this sets the visualizer and theme)
        self._load_config()
        
        # Restore saved gain
        saved_gain = self.config.get("gain", 100.0)
        # Convert % to multiplier
        initial_gain_mult = 60.0 * (saved_gain / 100.0)
        self.audio_processor.set_gain(initial_gain_mult)
        
        # Start audio processing with saved device
        saved_device = self.config.get("audio_device")
        # Handle "Auto" (-1) or stored None
        if saved_device == -1: saved_device = None
            
        self.audio_processor.start(device_index=saved_device)

    def contextMenuEvent(self, event):
        """Show context menu on right click."""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 1px solid #333;
            }
            QMenu::item {
                padding: 8px 20px;
            }
            QMenu::item:selected {
                background-color: #00d2ff;
                color: #000000;
            }
        """)
        
        # Add actions
        settings_action = menu.addAction("Preferences")
        settings_action.triggered.connect(self._show_settings)
        
        menu.addSeparator()
        
        toggle_controls = menu.addAction("Toggle Controls")
        toggle_controls.triggered.connect(self._toggle_controls)
        
        fullscreen_action = menu.addAction("Toggle Fullscreen")
        fullscreen_action.triggered.connect(lambda: self._toggle_fullscreen(not self.isFullScreen()))
        
        screenshot_action = menu.addAction("Take Screenshot")
        screenshot_action.triggered.connect(self._take_screenshot)
        
        menu.addSeparator()
        
        about_action = menu.addAction("About")
        about_action.triggered.connect(self._show_about)
        
        exit_action = menu.addAction("Exit")
        exit_action.triggered.connect(self.close)
        
        menu.exec(event.globalPos())
        
        # Control panel is hidden by default, toggle with Ctrl+H
        # self.control_panel.show()
        # QTimer.singleShot(100, self._position_control_panel)
    
    def _setup_ui(self):
        """Setup user interface."""
        self.setWindowTitle("EchoPy - Music Visualizer")
        self.setMinimumSize(800, 600)
        self.resize(1200, 800)
        
        # Set central widget
        self.setCentralWidget(self.visualizer_widget)
        
        # Load and apply modern stylesheet
        self._apply_stylesheet()
        
        # Set window icon explicitly
        from PySide6.QtGui import QIcon
        icon_path = get_resource_path(os.path.join("resources", "favicon.png"))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def _apply_stylesheet(self):
        """Load and apply QSS stylesheet."""
        qss_path = get_resource_path(os.path.join("resources", "modern.qss"))
        
        if os.path.exists(qss_path):
            try:
                with open(qss_path, "r") as f:
                    self.setStyleSheet(f.read())
                logger.info(f"Modern stylesheet applied from: {qss_path}")
            except Exception as e:
                logger.error(f"Failed to load stylesheet: {e}")
        else:
            logger.warning(f"Stylesheet not found at: {qss_path}")
            # Fallback
            self.setStyleSheet("QMainWindow { background-color: #121212; color: #ffffff; }")

    def _setup_shortcuts(self):
        """Initialize keyboard shortcuts without showing a menu bar."""
        # Fullscreen
        fs_act = QAction(self)
        fs_act.setShortcut(QKeySequence("F11"))
        fs_act.triggered.connect(lambda: self._toggle_fullscreen(not self.isFullScreen()))
        self.addAction(fs_act)
        
        # Toggle Controls (Ctrl+H)
        cntl_act = QAction(self)
        cntl_act.setShortcut(QKeySequence("Ctrl+H"))
        cntl_act.triggered.connect(self._toggle_controls)
        self.addAction(cntl_act)
        
        # Open Settings (Ctrl+,)
        set_act = QAction(self)
        set_act.setShortcut(QKeySequence("Ctrl+,"))
        set_act.triggered.connect(self._show_settings)
        self.addAction(set_act)
        
        # Screenshot (S)
        sc_act = QAction(self)
        sc_act.setShortcut(QKeySequence("S"))
        sc_act.triggered.connect(self._take_screenshot)
        self.addAction(sc_act)
        
        # Exit (Ctrl+Q)
        exit_act = QAction(self)
        exit_act.setShortcut(QKeySequence("Ctrl+Q"))
        exit_act.triggered.connect(self.close)
        self.addAction(exit_act)
    
    def _connect_signals(self):
        """Connect signals and slots."""
        # Audio processor signals
        self.audio_processor.audio_data_ready.connect(
            self.visualizer_widget.update_audio_data
        )
        
        # Control panel signals
        self.control_panel.style_changed.connect(self._change_style)
        self.control_panel.theme_changed.connect(self._change_theme)
        self.control_panel.background_changed.connect(self._load_background)
        self.control_panel.background_cleared.connect(self._clear_background)
        self.control_panel.settings_requested.connect(self._show_settings)
        
        # Settings dialog signals
        self.settings_dialog.device_changed.connect(self._change_device)
        self.settings_dialog.smoothing_changed.connect(self._change_smoothing)
        self.settings_dialog.gain_changed.connect(self._change_gain)
        self.settings_dialog.sample_rate_changed.connect(self._change_sample_rate)
        self.settings_dialog.opacity_changed.connect(self._change_opacity)
    
    def _load_config(self):
        """Load configuration from file."""
        # Set initial theme
        theme_name = self.config.get("theme", "modern")
        self._change_theme(theme_name)
        # Sync control panel UI
        self.control_panel.set_current_theme_name(theme_name)
        
        # Set initial style
        style_name = self.config.get("style", "spectrum_bars")
        self._change_style(style_name)
        # Sync control panel UI
        self.control_panel.set_current_style(style_name)
        
        # Load background image if saved
        bg_path = self.config.get("background_image")
        if bg_path and os.path.exists(bg_path):
            self._load_background(bg_path, save=False)
        elif bg_path:
             logger.warning(f"Saved background image not found: {bg_path}")
             
        # Restore opacity
        opacity = self.config.get("opacity", 0.3)
        self.visualizer_widget.set_background_opacity(opacity)
        
        # Load audio devices into settings
        devices = self.audio_processor.get_devices()
        self.settings_dialog.set_devices(devices)
        
        # Load sensitivity settings
        sensitivity = self.config.get("sensitivity", {})
        if sensitivity:
            self.visualizer_widget.set_sensitivity(
                sensitivity.get("rms_threshold_on", 0.0008),
                sensitivity.get("rms_threshold_off", 0.0004),
                sensitivity.get("silence_timeout", 45)
            )
    
    def _change_style(self, style_name: str):
        """Change visualization style."""
        logger.info(f"Changing style to: {style_name}")
        
        # Use Factory to get visualizer instance
        visualizer = VisualizerFactory.get_visualizer(style_name)
        
        if visualizer:
            self.visualizer_widget.set_visualizer(visualizer)
            self.config.set("style", style_name)
        else:
            logger.warning(f"Style '{style_name}' not found, using fallback")
            fallback = VisualizerFactory.get_visualizer("spectrum_bars")
            if fallback:
                self.visualizer_widget.set_visualizer(fallback)
                self.config.set("style", "spectrum_bars")
    
    
    def _change_theme(self, theme_name: str):
        """Change color theme."""
        logger.info(f"Changing theme to: {theme_name}")
        theme = get_theme(theme_name)
        self.visualizer_widget.set_theme(theme)
        self.config.set("theme", theme_name)
    
    def _load_background(self, file_path: str, save: bool = True):
        """Load background image."""
        pixmap = load_image(file_path)
        if pixmap:
            self.visualizer_widget.set_background_image(pixmap)
            if save:
                self.config.set("background_image", file_path)
        else:
            if save: # Only show error if user manually triggered it
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to load image: {file_path}"
                )
    
    def _clear_background(self):
        """Clear background image."""
        self.visualizer_widget.set_background_image(None)
        self.config.set("background_image", None)
    
    def _change_device(self, device_index: int):
        """Change audio input device."""
        self.audio_processor.set_device(device_index)
        self.config.set("audio_device", device_index)
    
    def _change_smoothing(self, smoothing: float):
        """Change smoothing factor."""
        self.audio_processor.set_smoothing(smoothing)
        self.config.set("smoothing", smoothing)

    def _change_gain(self, gain: float):
        """Change gain multiplier."""
        # Convert percentage (e.g. 100.0) to multiplier (e.g. 60.0 default base)
        # Base gain is 60.0, so 100% = 60.0
        base_gain = 60.0
        multiplier = gain / 100.0
        new_gain = base_gain * multiplier
        new_gain = base_gain * multiplier
        self.audio_processor.set_gain(new_gain)
        self.config.set("gain", gain)

    def _change_sample_rate(self, rate: int):
        """Change sample rate."""
        # This usually requires restarting the stream, which set_device might handle if we force it,
        # but for now we just save it and let the next restart or device switch pick it up if possible.
        # Ideally, AudioProcessor should have a set_sample_rate method.
        # For this task, we focus on persistence.
        self.config.set("sample_rate", rate)
        self.config.set("sample_rate", rate)
        QMessageBox.information(self, "Restart Required", "Sample rate changes will apply on next restart or device switch.")

    def _change_opacity(self, opacity: float):
        """Change background opacity."""
        self.visualizer_widget.set_background_opacity(opacity)
        self.visualizer_widget.update() # Force redraw
        self.config.set("opacity", opacity)
    
    def _toggle_fullscreen(self, checked: bool):
        """Toggle fullscreen mode."""
        if checked:
            self.showFullScreen()
        else:
            self.showNormal()
    
    def _show_controls(self):
        """Show control panel."""
        self.control_panel.show()
        self._position_control_panel()
        
    def _toggle_controls(self):
        """Toggle control panel visibility."""
        if self.control_panel.isVisible():
            self.control_panel.hide()
        else:
            self._show_controls()
    
    def _position_control_panel(self):
        """Position control panel on screen."""
        # Position in top-right corner
        screen_geom = self.screen().geometry()
        x = screen_geom.width() - self.control_panel.width() - 20
        y = 20
        
        self.control_panel.move(x, y)
        
    
    def _show_settings(self):
        """Show settings dialog."""
        # Inject current state to prevent redundant updates
        current_device = self.audio_processor.device_index
        if current_device is None: current_device = -1
        
        self.settings_dialog.load_current_settings(
            device_idx=current_device,
            sample_rate=self.audio_processor.sample_rate,
            fft_size=self.audio_processor.fft_size,
            smoothing=self.config.get("smoothing", 0.8),
            # Fix: Use stored percentage gain, not internal multiplier
            gain=self.config.get("gain", 100.0), 
            opacity=self.config.get("opacity", 0.3), # Note: Opacity isn't fully wired yet in main config but good to have
            fps=self.config.get("fps_limit", 60)
        )
        self.settings_dialog.exec()
    
    def _take_screenshot(self):
        """Capture visualization and save to file."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        
        # Ensure captures directory exists
        if not os.path.exists("captures"):
            os.makedirs("captures")
        
        filepath = os.path.join("captures", filename)
        
        # Grab the visualizer widget
        pixmap = self.visualizer_widget.grab()
        if pixmap.save(filepath, "PNG"):
            logger.info(f"Screenshot saved to: {filepath}")
        else:
            logger.error(f"Failed to save screenshot to: {filepath}")
    
    def _show_about(self):
        """Show about dialog."""
        about_text = (
            "<div style='color: #ffffff; background-color: #1a1a1a; padding: 10px; border-radius: 8px;'>"
            "<h1 style='color: #00d2ff; margin-bottom: 0;'>EchoPy</h1>"
            "<p style='color: #888; margin-top: 0;'>Modern Music Visualizer v1.0.1</p>"
            "<hr style='border: 0; border-top: 1px solid #333;'>"
            "<p>A professional real-time audio visualization tool built with PySide6 and NumPy.</p>"
            "<h3>✨ Key Features</h3>"
            "<ul>"
            "<li>Dynamic Audio Analysis with Hanning Windowing</li>"
            "<li>Plugin Architecture for Visualizers</li>"
            "<li>Modern Glassmorphism Design System</li>"
            "<li>Low Latency Real-time Processing</li>"
            "</ul>"
            "<h3>⌨️ Global Shortcuts</h3>"
            "<table style='width: 100%;'>"
            "<tr><td><b>F11</b></td><td>Toggle Fullscreen</td></tr>"
            "<tr><td><b>Ctrl+H</b></td><td>Toggle Controls</td></tr>"
            "<tr><td><b>Ctrl+,</b></td><td>Preferences</td></tr>"
            "<tr><td><b>S</b></td><td>Take Screenshot</td></tr>"
            "<tr><td><b>Ctrl+Q</b></td><td>Exit Application</td></tr>"
            "</table>"
            "<p style='font-size: 10px; color: #555; margin-top: 20px;'>Developed by EchoPy Team & DeepMind Advanced Agentic Coding Assistant</p>"
            "</div>"
        )
        
        QMessageBox.about(self, "About EchoPy", about_text)
    
    def keyPressEvent(self, event):
        """Handle key press events."""
        # ESC to exit fullscreen
        if event.key() == Qt.Key_Escape and self.isFullScreen():
            self.showNormal()
        else:
            super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Stop audio processing
        self.audio_processor.stop()
        
        # Accept close event
        event.accept()
