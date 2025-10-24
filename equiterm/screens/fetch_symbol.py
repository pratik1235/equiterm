"""
Fetch symbol information screen.
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.screen import Screen
from textual.widgets import Button, Header, Footer, Input, Static, DataTable, LoadingIndicator
from textual.binding import Binding
from textual.message import Message

from ..services.data_fetcher import data_fetcher
from ..services.storage import storage
from ..utils.symbol_detector import symbol_detector
from ..utils.calculations import format_currency, format_percentage, get_color_for_change
from ..models.watchlist import SymbolType


class FetchSymbolScreen(Screen):
    """Screen for fetching and displaying symbol information."""
    
    BINDINGS = [
        Binding("escape", "pop_screen", "Back"),
        Binding("enter", "fetch_data", "Fetch"),
        Binding("a", "add_to_watchlist", "Add to Watchlist"),
        Binding("tab", "focus_next", "Next"),
        Binding("shift+tab", "focus_previous", "Previous"),
        Binding("i", "focus_input", "Focus Input"),
        Binding("f", "focus_fetch_button", "Focus Fetch Button"),
        Binding("w", "focus_watchlist_button", "Focus Watchlist Button"),
    ]
    
    def __init__(self):
        super().__init__()
        self.current_data = None
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with Container(id="fetch-container"):
            with Vertical(id="input-section"):
                yield Static("Enter Symbol Name:", id="input-label")
                yield Input(placeholder="e.g., RELIANCE, NIFTY50, 120716", id="symbol-input")
                yield Static("", id="detected-type")
                
                yield Horizontal(
                    Button("🔍 Search", id="fetch-button", variant="primary"),
                    Button("Add to Watchlist", id="add-watchlist-button", variant="default", disabled=False),
                    id="button-row"
                )
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the screen."""
        # Only focus setup and button enablement required
        self.call_after_refresh(self._focus_input)
        self.call_after_refresh(self._setup_focus_order)
    
    def _focus_input(self) -> None:
        """Focus the input field."""
        try:
            input_widget = self.query_one("#symbol-input")
            if input_widget:
                input_widget.focus()
                # Try to focus again after a short delay
                self.set_timer(0.1, self._retry_focus)
        except Exception:
            pass
    
    def _retry_focus(self) -> None:
        """Retry focusing the input field."""
        try:
            input_widget = self.query_one("#symbol-input")
            if input_widget:
                input_widget.focus()
        except Exception:
            pass
    
    def _setup_focus_order(self) -> None:
        """Set up the focus order for better navigation."""
        try:
            # Get all focusable widgets
            input_widget = self.query_one("#symbol-input")
            fetch_button = self.query_one("#fetch-button")
            watchlist_button = self.query_one("#add-watchlist-button")
            
            # Set focus order if widgets exist
            if input_widget and fetch_button and watchlist_button:
                # This helps with Tab navigation
                input_widget.can_focus = True
                fetch_button.can_focus = True
                watchlist_button.can_focus = True
        except Exception:
            pass
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes for auto-detection."""
        if event.input.id == "symbol-input":
            symbol = event.value.strip()
            if symbol:
                # Auto-detect symbol type
                symbol_type, scheme_code = symbol_detector.detect_symbol_type(symbol)
                type_display = self.query_one("#detected-type")
                type_display.update(f"Detected Type: {symbol_type.value.upper()}" + 
                                  (f" (Scheme: {scheme_code})" if scheme_code else ""))
            else:
                type_display = self.query_one("#detected-type")
                type_display.update("")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        input_widget = self.query_one("#symbol-input")
        symbol = input_widget.value.strip() if input_widget else ""
        if event.button.id == "fetch-button" and symbol:
            # Navigate to Symbol Detail Screen
            from .symbol_detail import SymbolDetailScreen
            self.app.push_screen(SymbolDetailScreen(symbol=symbol))
        elif event.button.id == "add-watchlist-button" and symbol:
            # Navigate to Select Watchlist Screen
            from .select_watchlist import SelectWatchlistScreen
            self.app.push_screen(SelectWatchlistScreen(symbol=symbol))
    
    def action_fetch_data(self) -> None:
        """Fetch data for the entered symbol."""
        try:
            symbol_input = self.query_one("#symbol-input")
            symbol = symbol_input.value.strip()
        except Exception:
            self._update_status("Error accessing input field.", "error")
            return
            
        if not symbol:
            self._update_status("Please enter a symbol name.", "error")
            return
        
        # Show loading indicator
        loading = self.query_one("#loading")
        loading.display = True
        self._update_status("Fetching data...", "info")
        
        # Auto-detect symbol type
        symbol_type, scheme_code = symbol_detector.detect_symbol_type(symbol)
        
        # Fetch data
        data = data_fetcher.fetch_symbol_data(symbol, symbol_type, scheme_code)
        
        # Hide loading indicator
        loading.display = False
        loading.visible = False
        
        if data:
            self.current_data = data
            self._display_data(data)
            self._update_status("Data fetched successfully!", "success")
            
            # Enable add to watchlist button
            add_button = self.query_one("#add-watchlist-button")
            add_button.disabled = False
        else:
            # Show demo data for testing
            self._update_status(f"API data unavailable. Showing demo data for {symbol}.", "info")
            self.current_data = self._create_demo_data(symbol, symbol_type)
            self._display_data(self.current_data)
            
            # Enable add to watchlist button
            add_button = self.query_one("#add-watchlist-button")
            add_button.disabled = False
    
    def _display_data(self, data) -> None:
        """Display the fetched data in categorized sections."""
        # This method is no longer used for data display in FetchSymbolScreen
        # as the data detail display is moved to SymbolDetailScreen.
        # Keeping it for now as it might be used elsewhere or for future re-use.
        pass
    
    def _update_status(self, message: str, status_type: str = "info") -> None:
        """Update status message."""
        status = self.query_one("#status-text")
        status.update(f"[{status_type.upper()}] {message}")
    
    def action_add_to_watchlist(self) -> None:
        """Show watchlist selection for adding symbol."""
        if not self.current_data:
            self._update_status("No data to add to watchlist.", "error")
            return
        
        # Get available watchlists
        watchlist_names = storage.list_watchlist_names()
        
        if not watchlist_names:
            self._update_status("No watchlists found. Create a watchlist first.", "error")
            return
        
        # For now, show a simple message. In a full implementation,
        # this would show a selection dialog
        self._update_status(f"Available watchlists: {', '.join(watchlist_names)}", "info")
    
    def action_pop_screen(self) -> None:
        """Go back to main menu."""
        self.app.pop_screen()
    
    def action_focus_input(self) -> None:
        """Manually focus the input field."""
        self._focus_input()
    
    def action_focus_fetch_button(self) -> None:
        """Focus the fetch button."""
        try:
            fetch_button = self.query_one("#fetch-button")
            if fetch_button:
                fetch_button.focus()
        except Exception:
            pass
    
    def action_focus_watchlist_button(self) -> None:
        """Focus the watchlist button."""
        try:
            watchlist_button = self.query_one("#add-watchlist-button")
            if watchlist_button:
                watchlist_button.focus()
        except Exception:
            pass
    
    def _create_demo_data(self, symbol: str, symbol_type):
        """Create demo data for testing when API is unavailable."""
        from ..models.watchlist import MarketData, SymbolType
        
        if symbol_type == SymbolType.EQUITY:
            return MarketData(
                symbol=symbol,
                symbol_type=symbol_type,
                current_price=2500.50,
                open_price=2480.00,
                high_price=2520.00,
                low_price=2475.00,
                previous_close=2485.25,
                change_percent=0.61,
                volume=1500000,
                value=3750000000,
                market_cap=1700000000000,
                pe_ratio=15.2,
                dividend_yield=1.2
            )
        elif symbol_type == SymbolType.INDEX:
            return MarketData(
                symbol=symbol,
                symbol_type=symbol_type,
                current_price=18500.25,
                open_price=18450.00,
                high_price=18520.00,
                low_price=18420.00,
                previous_close=18480.50,
                change_percent=0.11,
                volume=50000000,
                value=925000000000
            )
        else:
            return MarketData(
                symbol=symbol,
                symbol_type=symbol_type,
                current_price=100.25,
                nav=99.80,
                premium_discount=0.45
            )
    
    def on_screen_resume(self) -> None:
        """Called when screen is resumed/shown."""
        # Ensure input is focused when screen is shown
        self.call_after_refresh(self._focus_input)
