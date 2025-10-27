"""
Theme system for EquiTerm with multiple vibrant color schemes.
Inspired by Bagels financial app design.
"""

from pydantic import BaseModel, Field
from textual.design import ColorSystem


class Theme(BaseModel):
    """Theme definition with color system support."""
    
    primary: str
    secondary: str | None = None
    warning: str | None = None
    error: str | None = None
    success: str | None = None
    accent: str | None = None
    foreground: str | None = None
    background: str | None = None
    surface: str | None = None
    panel: str | None = None
    dark: bool = True
    variables: dict[str, str] = Field(default_factory=dict)

    def to_color_system(self) -> ColorSystem:
        """Convert this theme to a Textual ColorSystem."""
        return ColorSystem(**self.model_dump())


# Theme collection optimized for financial applications
THEMES: dict[str, Theme] = {
    "nord": Theme(
        primary="#88C0D0",  # Ice Blue
        secondary="#81A1C1",  # Misty Blue
        accent="#B48EAD",  # Muted Purple
        success="#A3BE8C",  # Alpine Meadow Green
        warning="#EBCB8B",  # Soft Sunlight
        error="#BF616A",  # Muted Red
        foreground="#D8DEE9",  # Light Gray
        background="#2E3440",  # Dark Slate
        surface="#3B4252",  # Darker Blue-Grey
        panel="#434C5E",  # Lighter Blue-Grey
        variables={
            "block-cursor-background": "#88C0D0",
            "block-cursor-foreground": "#2E3440",
            "block-cursor-text-style": "none",
            "footer-key-foreground": "#88C0D0",
            "input-selection-background": "#81a1c1 35%",
            "button-color-foreground": "#2E3440",
        },
    ),
    "tokyo-night": Theme(
        primary="#BB9AF7",  # Purple
        secondary="#7AA2F7",  # Blue
        accent="#FF9E64",  # Orange
        success="#9ECE6A",  # Green
        warning="#E0AF68",  # Yellow
        error="#F7768E",  # Red
        foreground="#a9b1d6",  # Light Blue-Gray
        background="#1A1B26",  # Very Dark Blue
        surface="#24283B",  # Dark Blue
        panel="#414868",  # Medium Blue-Gray
        variables={
            "button-color-foreground": "#24283B",
        },
    ),
    "gruvbox": Theme(
        primary="#85A598",  # Aqua
        secondary="#A89A85",  # Beige
        accent="#fabd2f",  # Yellow
        success="#b8bb26",  # Green
        warning="#fe8019",  # Orange
        error="#fb4934",  # Red
        foreground="#fbf1c7",  # Light Cream
        background="#282828",  # Dark Brown
        surface="#3c3836",  # Dark Gray-Brown
        panel="#504945",  # Medium Gray-Brown
        variables={
            "block-cursor-foreground": "#fbf1c7",
            "input-selection-background": "#689d6a40",
            "button-color-foreground": "#282828",
        },
    ),
    "cobalt": Theme(
        primary="#334D5C",  # Deep Cobalt Blue
        secondary="#4878A6",  # Slate Blue
        accent="#D94E64",  # Candy Apple Red
        success="#4CAF50",  # Green
        warning="#FFAA22",  # Amber
        error="#E63946",  # Red
        background="#1F262A",  # Charcoal
        surface="#27343B",  # Dark Lead
        panel="#2D3E46",  # Storm Gray
    ),
    "catppuccin-mocha": Theme(
        primary="#F5C2E7",  # Pink
        secondary="#cba6f7",  # Lavender
        accent="#fab387",  # Peach
        success="#ABE9B3",  # Green
        warning="#FAE3B0",  # Yellow
        error="#F28FAD",  # Red
        foreground="#cdd6f4",  # Text
        background="#181825",  # Base
        surface="#313244",  # Surface 0
        panel="#45475a",  # Surface 1
        variables={
            "input-cursor-foreground": "#11111b",
            "input-cursor-background": "#f5e0dc",
            "input-selection-background": "#9399b2 30%",
            "border": "#b4befe",
            "border-blurred": "#585b70",
            "footer-background": "#45475a",
            "block-cursor-foreground": "#1e1e2e",
            "block-cursor-text-style": "none",
            "button-color-foreground": "#181825",
        },
    ),
    "dracula": Theme(
        primary="#BD93F9",  # Purple
        secondary="#6272A4",  # Comment Gray
        accent="#FF79C6",  # Pink
        success="#50FA7B",  # Green
        warning="#FFB86C",  # Orange
        error="#FF5555",  # Red
        foreground="#F8F8F2",  # Foreground
        background="#282A36",  # Background
        surface="#2B2E3B",  # Slightly lighter
        panel="#313442",  # Panel
        variables={
            "button-color-foreground": "#282A36",
        },
    ),
    "galaxy": Theme(
        primary="#8A2BE2",  # Blueviolet
        secondary="#a684e8",  # Light Purple
        accent="#FF69B4",  # Hot Pink
        success="#00FA9A",  # Medium Spring Green
        warning="#FFD700",  # Gold
        error="#FF4500",  # OrangeRed
        background="#0F0F1F",  # Very Dark Blue
        surface="#1E1E3F",  # Dark Blue-Purple
        panel="#2D2B55",  # Lighter Blue-Purple
    ),
}

# Default theme for EquiTerm
DEFAULT_THEME = "nord"

