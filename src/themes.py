"""Color themes for EchoPy music visualizer."""

from typing import List, Dict
from PySide6.QtGui import QColor, QLinearGradient
from PySide6.QtCore import QPointF


class ColorTheme:
    """Represents a color theme for visualization."""
    
    def __init__(self, name: str, colors: List[str], bg_color: str = "#000000", text_color: str = "#FFFFFF"):
        """
        Initialize a color theme.
        
        Args:
            name: Theme name
            colors: List of hex color strings for gradients
            bg_color: Background color hex string
            text_color: UI text color hex string
        """
        self.name = name
        self.colors = [QColor(c) for c in colors]
        self.bg_color = QColor(bg_color)
        self.text_color = QColor(text_color)
    
    def get_color(self, index: int) -> QColor:
        """Get a color from the theme by index (wraps around)."""
        return self.colors[index % len(self.colors)]
    
    def get_gradient_color(self, value: float) -> QColor:
        """
        Get a color from the gradient based on value (0.0 to 1.0).
        
        Args:
            value: Position in gradient (0.0 to 1.0)
            
        Returns:
            Interpolated QColor
        """
        value = max(0.0, min(1.0, value))
        
        if len(self.colors) == 1:
            return self.colors[0]
        
        # Calculate which two colors to interpolate between
        segment = value * (len(self.colors) - 1)
        index = int(segment)
        
        if index >= len(self.colors) - 1:
            return self.colors[-1]
        
        # Interpolate between the two colors
        t = segment - index
        c1 = self.colors[index]
        c2 = self.colors[index + 1]
        
        r = int(c1.red() + (c2.red() - c1.red()) * t)
        g = int(c1.green() + (c2.green() - c1.green()) * t)
        b = int(c1.blue() + (c2.blue() - c1.blue()) * t)
        
        return QColor(r, g, b)
    
    def create_gradient(self, start: QPointF, end: QPointF) -> QLinearGradient:
        """Create a QLinearGradient from this theme."""
        gradient = QLinearGradient(start, end)
        
        num_colors = len(self.colors)
        for i, color in enumerate(self.colors):
            position = i / (num_colors - 1) if num_colors > 1 else 0
            gradient.setColorAt(position, color)
        
        return gradient


# Define 10 predefined themes
THEMES: Dict[str, ColorTheme] = {
    "modern": ColorTheme(
        name="Modern",
        colors=["#00D9FF", "#7B2FFF", "#BD00FF"],
        bg_color="#0A0A0A",
        text_color="#FFFFFF"
    ),
    
    "cyberpunk": ColorTheme(
        name="Cyberpunk",
        colors=["#FF006E", "#FF1B8D", "#00F0FF", "#00D4FF"],
        bg_color="#0D0221",
        text_color="#00F0FF"
    ),
    
    "aesthetic": ColorTheme(
        name="Aesthetic",
        colors=["#FFB3D9", "#C9A0DC", "#B19CD9", "#A8E6CF"],
        bg_color="#FFF5F7",
        text_color="#5A5A5A"
    ),
    
    "classic": ColorTheme(
        name="Classic",
        colors=["#00FF00", "#00DD00", "#00BB00", "#009900"],
        bg_color="#000000",
        text_color="#00FF00"
    ),
    
    "fire": ColorTheme(
        name="Fire",
        colors=["#FF0000", "#FF4400", "#FF8800", "#FFAA00", "#FFFF00"],
        bg_color="#1A0000",
        text_color="#FFAA00"
    ),
    
    "ocean": ColorTheme(
        name="Ocean",
        colors=["#003366", "#005588", "#0099CC", "#00BBEE", "#00FFCC"],
        bg_color="#001122",
        text_color="#00FFCC"
    ),
    
    "sunset": ColorTheme(
        name="Sunset",
        colors=["#FF6B35", "#FF8C42", "#F4A261", "#FF006E", "#8338EC"],
        bg_color="#1A0A14",
        text_color="#FFB4A2"
    ),
    
    "neon": ColorTheme(
        name="Neon",
        colors=["#FF00FF", "#FF0080", "#FF0000", "#FF8000", "#FFFF00", "#00FF00", "#00FFFF"],
        bg_color="#000000",
        text_color="#FFFFFF"
    ),
    
    "monochrome": ColorTheme(
        name="Monochrome",
        colors=["#FFFFFF", "#CCCCCC", "#999999", "#666666"],
        bg_color="#000000",
        text_color="#FFFFFF"
    ),
    
    "rainbow": ColorTheme(
        name="Rainbow",
        colors=["#FF0000", "#FF7F00", "#FFFF00", "#00FF00", "#0000FF", "#4B0082", "#9400D3"],
        bg_color="#000000",
        text_color="#FFFFFF"
    ),
    
    "deep_space": ColorTheme(
        name="Deep Space",
        colors=["#000033", "#000066", "#330099", "#6600CC", "#9900FF"],
        bg_color="#000011",
        text_color="#99CCFF"
    ),
    
    "lava": ColorTheme(
        name="Lava",
        colors=["#330000", "#660000", "#990000", "#CC3300", "#FF6600"],
        bg_color="#110000",
        text_color="#FFCC33"
    )
}


def get_theme(name: str) -> ColorTheme:
    """
    Get a theme by name.
    
    Args:
        name: Theme name (lowercase)
        
    Returns:
        ColorTheme instance
    """
    key = name.lower().replace(" ", "_")
    return THEMES.get(key, THEMES["modern"])


def get_theme_names() -> List[str]:
    """Get list of all available theme names."""
    return [theme.name for theme in THEMES.values()]
