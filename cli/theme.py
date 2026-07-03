"""
cli/theme.py

Defines the global styling, colors, and layout configurations for the dashboard.
This ensures a consistent professional appearance across all components without hardcoding colors everywhere.
"""
from rich.console import Console
from rich.theme import Theme

# Define consistent colors based on the reference image
CUSTOM_THEME = Theme({
    "info": "cyan",
    "warning": "yellow",
    "danger": "bold red",
    "success": "bold green",
    "panel.border": "grey50",
    "header": "bold cyan",
    "label": "white",
    "value.positive": "green",
    "value.negative": "red",
    "value.neutral": "white",
    "menu.prompt": "bold cyan",
})

# A single, globally shared Console instance that uses our custom theme.
console = Console(theme=CUSTOM_THEME)

# Standard panel configuration to ensure all panels look identical
PANEL_KWARGS = {
    "border_style": "panel.border",
    "padding": (0, 1),
}

# Standard table configuration for data tables (statements, prices, etc.)
TABLE_KWARGS = {
    "border_style": "panel.border",
    "padding": (0, 1),
}
