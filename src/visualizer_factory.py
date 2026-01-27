"""Factory for creating and managing visualization styles."""

from typing import Dict, List, Type, Optional
from visualizer import BaseVisualizer
from styles.spectrum_bars import SpectrumBars
from styles.waveform import Waveform
from styles.circular import CircularSpectrum
from styles.particles import Particles
from styles.radial_bars import RadialBars
from styles.fire_effect import FireEffect
from styles.matrix_rain import MatrixRain
from styles.oscilloscope import Oscilloscope
from styles.frequency_rings import FrequencyRings
from styles.audio_lines import AudioLines
from utils import logger


class VisualizerFactory:
    """Manages registration and creation of visualizer styles."""
    
    _styles: Dict[str, Type[BaseVisualizer]] = {
        "spectrum_bars": SpectrumBars,
        "waveform": Waveform,
        "circular": CircularSpectrum,
        "particles": Particles,
        "radial_bars": RadialBars,
        "fire_effect": FireEffect,
        "matrix_rain": MatrixRain,
        "oscilloscope": Oscilloscope,
        "frequency_rings": FrequencyRings,
        "audio_lines": AudioLines
    }
    
    _instances: Dict[str, BaseVisualizer] = {}

    @classmethod
    def get_visualizer(cls, name: str) -> Optional[BaseVisualizer]:
        """
        Get or create a visualizer instance by name.
        
        Args:
            name: Style name
            
        Returns:
            Visualizer instance or None if not found
        """
        if name in cls._instances:
            return cls._instances[name]
        
        if name in cls._styles:
            try:
                instance = cls._styles[name]()
                cls._instances[name] = instance
                return instance
            except Exception as e:
                logger.error(f"Error creating visualizer '{name}': {e}")
                return None
        
        logger.warning(f"Visualizer style '{name}' not found")
        return None

    @classmethod
    def get_available_styles(cls) -> List[str]:
        """Get list of registered style names."""
        return list(cls._styles.keys())

    @classmethod
    def register_style(cls, name: str, visualizer_class: Type[BaseVisualizer]):
        """Register a new visualizer style."""
        cls._styles[name] = visualizer_class
        logger.info(f"Registered new visualizer style: {name}")
