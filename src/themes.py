"""Color themes for EchoPy music visualizer."""

from typing import List, Dict
from PySide6.QtGui import QColor, QLinearGradient
from PySide6.QtCore import QPointF


class ColorTheme:
    """Represents a color theme for visualization."""

    def __init__(
        self,
        name: str,
        colors: List[str],
        bg_color: str = "#000000",
        text_color: str = "#FFFFFF",
    ):
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
        a = int(c1.alpha() + (c2.alpha() - c1.alpha()) * t)

        return QColor(r, g, b, a)

    def create_gradient(self, start: QPointF, end: QPointF) -> QLinearGradient:
        """Create a QLinearGradient from this theme."""
        gradient = QLinearGradient(start, end)

        num_colors = len(self.colors)
        for i, color in enumerate(self.colors):
            position = i / (num_colors - 1) if num_colors > 1 else 0
            gradient.setColorAt(position, color)

        return gradient


# Define 10 predefined themes (Modernized & Vibrantly adjusted)
THEMES: Dict[str, ColorTheme] = {
    "modern": ColorTheme(
        name="Modern",
        colors=[
            "#7A5FFF",
            "#00E5FF",
            "#00FFC2",
        ],  # Deep Purple to Bright Neon Cyan/Mint
        bg_color="#05050A",
        text_color="#F0F8FF",
    ),
    "cyberpunk": ColorTheme(
        name="Cyberpunk",
        colors=[
            "#FF007F",
            "#B900FF",
            "#00F0FF",
            "#00FF66",
        ],  # Vibrant Pink, Violet, Bright Cyan, Neon Green
        bg_color="#0A0214",
        text_color="#00F0FF",
    ),
    "aurora": ColorTheme(
        name="Aurora",
        colors=[
            "#00FF87",
            "#00FFFF",
            "#0055FF",
            "#7B2CBF",
        ],  # Sharp Green to Deep Royal Blue-Purple
        bg_color="#020815",
        text_color="#00FFFF",
    ),
    "aesthetic": ColorTheme(
        name="Aesthetic",
        colors=["#FF99C8", "#D9A8FF", "#A9C1FF", "#9EEBCB"],  # Richer pastels
        bg_color="#FAF5F8",
        text_color="#333333",
    ),
    "classic": ColorTheme(
        name="Classic",
        colors=["#1EFF00", "#18CC00", "#109900"],
        bg_color="#000000",
        text_color="#1EFF00",
    ),
    "fire": ColorTheme(
        name="Fire",
        colors=[
            "#FF1100",
            "#FF4500",
            "#FF8C00",
            "#FFD700",
            "#FFFF33",
        ],  # More dynamic fire curve
        bg_color="#0F0000",
        text_color="#FF8C00",
    ),
    "ocean": ColorTheme(
        name="Ocean",
        colors=[
            "#001F54",
            "#034078",
            "#0A1128",
            "#1282A2",
            "#00E5FF",
        ],  # Deeper abyss to bright surface
        bg_color="#010A15",
        text_color="#00E5FF",
    ),
    "sunset": ColorTheme(
        name="Sunset",
        colors=[
            "#FF3366",
            "#FF6B35",
            "#F4A261",
            "#E9C46A",
            "#9B5DE5",
        ],  # Warmer midtones mixing with purple night
        bg_color="#12050C",
        text_color="#F4A261",
    ),
    "neon": ColorTheme(
        name="Neon",
        colors=["#FF00FF", "#FF0055", "#FF3300", "#FFFF00", "#33FF00", "#00FFFF"],
        bg_color="#000000",
        text_color="#FAFAFA",
    ),
    "monochrome": ColorTheme(
        name="Monochrome",
        colors=["#FFFFFF", "#D4D4D4", "#A3A3A3", "#737373"],
        bg_color="#050505",
        text_color="#FFFFFF",
    ),
    "rainbow": ColorTheme(
        name="Rainbow",
        colors=["#FF0040", "#FF8000", "#FFEE00", "#00FF00", "#0040FF", "#8A2BE2"],
        bg_color="#000000",
        text_color="#FFFFFF",
    ),
    "deep_space": ColorTheme(
        name="Deep Space",
        colors=[
            "#05001A",
            "#1A004D",
            "#4B0099",
            "#8C1AFF",
            "#D966FF",
        ],  # Vibrant nebula purples
        bg_color="#02000A",
        text_color="#D966FF",
    ),
    "lava": ColorTheme(
        name="Lava",
        colors=["#2A0000", "#5E0000", "#A30000", "#E63900", "#FF7F00"],
        bg_color="#0A0000",
        text_color="#FFB366",
    ),
    "spectre": ColorTheme(
        name="Spectre",
        colors=[
            "#4A00E0",
            "#8E2DE2",
            "#FF00FF",
            "#00FFFF",
        ],  # Purple to Neon Pink and Cyan
        bg_color="#0D001A",
        text_color="#00FFFF",
    ),
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
