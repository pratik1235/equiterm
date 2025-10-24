"""
Help screen showing keyboard shortcuts.
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.screen import Screen
from textual.widgets import Button, Header, Footer, Static
from textual.binding import Binding


class HelpScreen(Screen):
    """Help screen showing keyboard shortcuts."""
    
    BINDINGS = [
        Binding("escape", "pop_screen", "Back"),
        Binding("h", "pop_screen", "Back"),
    ]
    
    def compose(self) -> ComposeResult:
        """Compose the help screen."""
        yield Header()
        
        with Container(id="help-container"):
            with Vertical(id="help-content"):
                yield Static("EquiTerm - Keyboard Shortcuts", id="help-title")
                
                yield Static("", id="spacer")
                
                # Main Menu Shortcuts
                yield Static("Main Menu:", id="section-title")
                yield Static("• Arrow Keys: Navigate between buttons")
                yield Static("• Enter: Activate focused button")
                yield Static("• F: Fetch Symbol Information")
                yield Static("• W: Check Watchlists")
                yield Static("• C: Create a Watchlist")
                yield Static("• Q: Quit")
                
                yield Static("", id="spacer")
                
                # Fetch Symbol Shortcuts
                yield Static("Fetch Symbol Screen:", id="section-title")
                yield Static("• I: Focus Input Field")
                yield Static("• F: Focus Fetch Button")
                yield Static("• W: Focus Watchlist Button")
                yield Static("• Tab/Shift+Tab: Navigate between elements")
                yield Static("• Enter: Fetch data (when input focused)")
                yield Static("• A: Add to Watchlist")
                
                yield Static("", id="spacer")
                
                # Create Watchlist Shortcuts
                yield Static("Create Watchlist Screen:", id="section-title")
                yield Static("• N: Focus Name Input")
                yield Static("• Y: Focus Symbol Input")
                yield Static("• C: Focus Scheme Input")
                yield Static("• R: Focus Remove Button")
                yield Static("• S: Focus Save Button")
                yield Static("• A: Add Symbol")
                yield Static("• S: Save Watchlist")
                
                yield Static("", id="spacer")
                
                # Watchlist View Shortcuts
                yield Static("Watchlist View Screen:", id="section-title")
                yield Static("• S: Focus Select Widget")
                yield Static("• V: Focus View Button")
                yield Static("• F: Focus Refresh Button")
                yield Static("• X: Focus Delete Button")
                yield Static("• R: Refresh Data")
                yield Static("• D: Delete Watchlist")
                
                yield Static("", id="spacer")
                
                yield Static("Press Escape or H to go back", id="help-footer")
        
        yield Footer()
    
    def action_pop_screen(self) -> None:
        """Go back to previous screen."""
        self.app.pop_screen()
