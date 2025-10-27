"""
Main menu screen for Equiterm application.
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Header, Footer, Static
from textual.binding import Binding


class MainMenuScreen(Screen):
    """Main menu screen with three primary options."""
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("escape", "quit", "Quit"),
        Binding("f", "fetch_symbol", "Fetch Symbol"),
        Binding("w", "check_watchlists", "Watchlists"),
        Binding("c", "create_watchlist", "Create Watchlist"),
        Binding("h", "show_help", "Help"),
        Binding("up", "focus_previous", "Previous"),
        Binding("down", "focus_next", "Next"),
        Binding("enter", "activate_focused", "Activate"),
    ]
    
    def compose(self) -> ComposeResult:
        """Compose the main menu layout."""
        yield Header()
        
        with VerticalScroll(id="main-scroll", can_focus=True):
            with Container(id="main-container"):
                with Vertical(id="menu-container"):
                    yield Static("EquiTerm", id="app-title")
                    yield Static("Terminal Stock Market App", id="subtitle")
                    
                    with Vertical(id="menu-buttons"):
                        yield Button("Fetch Symbol Information", id="fetch-symbol", variant="primary")
                        yield Button("Check Watchlists", id="check-watchlists", variant="primary")
                        yield Button("Create a Watchlist", id="create-watchlist", variant="primary")
                        yield Button("Help (Keyboard Shortcuts)", id="help-button", variant="default")
                    
                    yield Static("", id="spacer")
                    yield Static("Use arrow keys to navigate, Enter to select, or press 'q' to quit", id="help-text")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Focus first button on mount."""
        self.call_after_refresh(self._focus_first_button)
    
    def _focus_first_button(self) -> None:
        """Focus the first button."""
        try:
            buttons = list(self.query("Button"))
            if buttons:
                buttons[0].focus()
        except Exception:
            pass
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id
        
        if button_id == "fetch-symbol":
            self.action_fetch_symbol()
        elif button_id == "check-watchlists":
            self.action_check_watchlists()
        elif button_id == "create-watchlist":
            self.action_create_watchlist()
        elif button_id == "help-button":
            self.action_show_help()
    
    def action_fetch_symbol(self) -> None:
        """Navigate to fetch symbol screen."""
        from .fetch_symbol import FetchSymbolScreen
        self.app.push_screen(FetchSymbolScreen())
    
    def action_check_watchlists(self) -> None:
        """Navigate to watchlist view screen."""
        from .watchlist_view import WatchlistViewScreen
        self.app.push_screen(WatchlistViewScreen())
    
    def action_create_watchlist(self) -> None:
        """Navigate to create watchlist screen."""
        from .create_watchlist import CreateWatchlistScreen
        self.app.push_screen(CreateWatchlistScreen())
    
    def action_show_help(self) -> None:
        """Navigate to help screen."""
        from .help_screen import HelpScreen
        self.app.push_screen(HelpScreen())
    
    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
    
    def action_focus_previous(self) -> None:
        """Focus the previous button and scroll into view."""
        buttons = list(self.query("Button"))
        if buttons:
            current = self.focused
            if current in buttons:
                current_index = buttons.index(current)
                prev_index = (current_index - 1) % len(buttons)
                buttons[prev_index].focus()
                buttons[prev_index].scroll_visible()
            else:
                buttons[0].focus()
                buttons[0].scroll_visible()
    
    def action_focus_next(self) -> None:
        """Focus the next button and scroll into view."""
        buttons = list(self.query("Button"))
        if buttons:
            current = self.focused
            if current in buttons:
                current_index = buttons.index(current)
                next_index = (current_index + 1) % len(buttons)
                buttons[next_index].focus()
                buttons[next_index].scroll_visible()
            else:
                buttons[0].focus()
                buttons[0].scroll_visible()
    
    def action_activate_focused(self) -> None:
        """Activate the currently focused button."""
        focused = self.focused
        if hasattr(focused, 'id'):
            if focused.id == "fetch-symbol":
                self.action_fetch_symbol()
            elif focused.id == "check-watchlists":
                self.action_check_watchlists()
            elif focused.id == "create-watchlist":
                self.action_create_watchlist()
            elif focused.id == "help-button":
                self.action_show_help()
