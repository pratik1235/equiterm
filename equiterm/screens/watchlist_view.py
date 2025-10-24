"""
Watchlist view screen for displaying and managing watchlists.
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.screen import Screen
from textual.widgets import Button, Header, Footer, Static, DataTable, Select, LoadingIndicator
from textual.binding import Binding

from ..services.storage import storage
from ..services.data_fetcher import data_fetcher
from ..utils.calculations import format_currency, format_percentage, get_color_for_change
from ..models.watchlist import SymbolType


class WatchlistViewScreen(Screen):
    """Screen for viewing and managing watchlists."""
    
    BINDINGS = [
        Binding("escape", "pop_screen", "Back"),
        Binding("r", "refresh_data", "Refresh"),
        Binding("d", "delete_watchlist", "Delete"),
        Binding("tab", "focus_next", "Next"),
        Binding("shift+tab", "focus_previous", "Previous"),
        Binding("s", "focus_select", "Focus Select"),
        Binding("v", "focus_view_button", "Focus View Button"),
        Binding("f", "focus_refresh_button", "Focus Refresh Button"),
        Binding("x", "focus_delete_button", "Focus Delete Button"),
    ]
    
    def __init__(self):
        super().__init__()
        self.current_watchlist = None
        self.watchlist_select = None
        self.data_table = None
        self.status_text = None
        self.refresh_button = None
    
    def compose(self) -> ComposeResult:
        """Compose the watchlist view screen."""
        yield Header()
        
        with Container(id="watchlist-container"):
            with Vertical(id="watchlist-section"):
                yield Static("Select Watchlist:", id="select-label")
                self.watchlist_select = Select([], id="watchlist-select")
                
                with Horizontal(id="action-buttons"):
                    yield Button("View Data", id="view-button", variant="primary")
                    yield Button("Refresh Data", id="refresh-button", variant="default")
                    yield Button("Delete Watchlist", id="delete-button", variant="error")
                
                yield Static("", id="status-text")
            
            with Vertical(id="data-section"):
                yield Static("Watchlist Data:", id="data-title")
                self.data_table = DataTable(id="data-table")
                yield LoadingIndicator(id="loading", visible=False)
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the screen."""
        self._load_watchlists()
        self.data_table.add_columns("Symbol", "Type", "Price/NAV", "Change %", "Premium %")
    
    def _load_watchlists(self) -> None:
        """Load available watchlists into the select widget."""
        watchlist_names = storage.list_watchlist_names()
        
        if not watchlist_names:
            self._update_status("No watchlists found. Create a watchlist first.", "error")
            return
        
        # Create options for select widget
        options = [(name, name) for name in watchlist_names]
        self.watchlist_select.set_options(options)
        self._update_status(f"Found {len(watchlist_names)} watchlist(s). Select one to view.", "info")
    
    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle watchlist selection change."""
        if event.select.id == "watchlist-select":
            self.current_watchlist = event.value
            self._update_status(f"Selected: {event.value}", "info")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "view-button":
            self.action_view_data()
        elif event.button.id == "refresh-button":
            self.action_refresh_data()
        elif event.button.id == "delete-button":
            self.action_delete_watchlist()
    
    def action_view_data(self) -> None:
        """View data for the selected watchlist."""
        if not self.current_watchlist:
            self._update_status("Please select a watchlist first.", "error")
            return
        
        # Load watchlist
        watchlist = storage.load_watchlist(self.current_watchlist)
        if not watchlist:
            self._update_status(f"Failed to load watchlist: {self.current_watchlist}", "error")
            return
        
        if not watchlist.symbols:
            self._update_status("Watchlist is empty.", "error")
            return
        
        # Show loading indicator
        loading = self.query_one("#loading")
        loading.display = True
        loading.visible = True
        self._update_status("Fetching data...", "info")
        
        # Fetch data for all symbols
        symbols_data = []
        for symbol in watchlist.symbols:
            symbols_data.append({
                'symbol': symbol.name,
                'type': symbol.symbol_type,
                'scheme_code': symbol.scheme_code
            })
        
        # Fetch data
        market_data = data_fetcher.fetch_multiple_symbols(symbols_data)
        
        # Hide loading indicator
        loading.display = False
        loading.visible = False
        
        if market_data:
            self._display_watchlist_data(market_data)
            self._update_status(f"Data updated for {len(market_data)} symbols.", "success")
        else:
            self._update_status("Failed to fetch data for any symbols.", "error")
    
    def action_refresh_data(self) -> None:
        """Refresh data for the current watchlist."""
        if not self.current_watchlist:
            self._update_status("Please select a watchlist first.", "error")
            return
        
        self.action_view_data()  # Same as view data
    
    def action_delete_watchlist(self) -> None:
        """Delete the selected watchlist."""
        if not self.current_watchlist:
            self._update_status("Please select a watchlist first.", "error")
            return
        
        # For now, just show a message. In a full implementation,
        # this would show a confirmation dialog
        self._update_status(f"Delete functionality for '{self.current_watchlist}' not implemented yet.", "info")
    
    def _display_watchlist_data(self, market_data: dict) -> None:
        """Display watchlist data in the table."""
        table = self.data_table
        table.clear()
        
        for symbol, data in market_data.items():
            # Format price/NAV
            if data.symbol_type == SymbolType.MUTUAL_FUND:
                price_display = format_currency(data.nav) if data.nav else "N/A"
            else:
                price_display = format_currency(data.current_price) if data.current_price else "N/A"
            
            # Format change percentage
            change_display = format_percentage(data.change_percent) if data.change_percent is not None else "N/A"
            change_color = get_color_for_change(data.change_percent)
            
            # Format premium for ETFs
            premium_display = "N/A"
            if data.symbol_type == SymbolType.ETF and data.premium_discount is not None:
                premium_display = format_percentage(data.premium_discount)
            
            # Add row with appropriate styling
            table.add_row(
                symbol,
                data.symbol_type.value.upper(),
                price_display,
                change_display,
                premium_display,
                style=change_color
            )
    
    def _update_status(self, message: str, status_type: str = "info") -> None:
        """Update status message."""
        status = self.query_one("#status-text")
        status.update(f"[{status_type.upper()}] {message}")
    
    def action_pop_screen(self) -> None:
        """Go back to main menu."""
        self.app.pop_screen()
    
    def action_focus_select(self) -> None:
        """Focus the watchlist select widget."""
        try:
            select_widget = self.query_one("#watchlist-select")
            if select_widget:
                select_widget.focus()
        except Exception:
            pass
    
    def action_focus_view_button(self) -> None:
        """Focus the view button."""
        try:
            view_button = self.query_one("#view-button")
            if view_button:
                view_button.focus()
        except Exception:
            pass
    
    def action_focus_refresh_button(self) -> None:
        """Focus the refresh button."""
        try:
            refresh_button = self.query_one("#refresh-button")
            if refresh_button:
                refresh_button.focus()
        except Exception:
            pass
    
    def action_focus_delete_button(self) -> None:
        """Focus the delete button."""
        try:
            delete_button = self.query_one("#delete-button")
            if delete_button:
                delete_button.focus()
        except Exception:
            pass
