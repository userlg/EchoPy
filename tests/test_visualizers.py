import sys
import os
import unittest
import numpy as np
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPainter, QImage
from PySide6.QtCore import Qt

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from visualizer_factory import VisualizerFactory
from themes import get_theme


class TestVisualizers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create QApplication instance if it doesn't exist
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication([])

    def test_all_visualizers_render(self):
        # Setup dummy audio data
        waveform = np.sin(np.linspace(0, 10 * np.pi, 2048))
        fft_data = np.abs(np.fft.rfft(waveform))
        fft_data = fft_data / (np.max(fft_data) + 1e-5)  # normalize

        # Get all styles
        styles = VisualizerFactory.get_available_styles()
        self.assertIn("synthwave_grid", styles)

        theme = get_theme("modern")

        for style_name in styles:
            with self.subTest(style=style_name):
                # Setup rendering canvas per visualizer
                image = QImage(800, 600, QImage.Format_ARGB32_Premultiplied)
                painter = QPainter(image)
                self.assertTrue(painter.isActive(), f"QPainter should be active for {style_name}")

                # Get the visualizer instance
                visualizer = VisualizerFactory.get_visualizer(style_name)
                self.assertIsNotNone(visualizer)
                
                # Setup
                visualizer.set_theme(theme)
                visualizer.set_size(800, 600)
                
                # Try rendering. This will catch any exceptions raised inside render.
                try:
                    visualizer.render(painter, waveform, fft_data)
                except Exception as e:
                    self.fail(f"Visualizer '{style_name}' failed to render: {e}")
                finally:
                    painter.end()


if __name__ == '__main__':
    unittest.main()
