"""
Watchlist list screen with favorite watchlist display.
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, DataTable
from textual.binding import Binding
from textual import log, events
from textual.events import Click
from rich.text import Text

from ..services.storage import storage
from ..services.symbol_search import symbol_search_service
from ..services.data_fetcher import data_fetcher


class WatchlistListScreen(Screen):
    """Screen for viewing watchlist list and favorite watchlist."""
    
    BINDINGS = [
        Binding("escape", "pop_screen", "Back"),
        Binding("q", "pop_screen", "Back"),
        Binding("d", "delete_watchlist", "Delete", show=False),
    ]
    
    def __init__(self):
        super().__init__()
        self.watchlists = []
        self.etf_data_cache = {}  # Cache ETF data to avoid redundant API calls
    
    def compose(self) -> ComposeResult:
        """Compose the watchlist list screen."""
        yield Header()
        
        with VerticalScroll(id="main-watchlist-scroll", can_focus=False):
            with Container(id="watchlist-container"):
                # Watchlist List View
                with Vertical(id="watchlist-list-section"):
                    yield Static("Your Watchlists", id="watchlist-title")
                    with VerticalScroll(id="watchlist-scroll", can_focus=True):
                        yield DataTable(id="watchlist-table")
                    yield Static("", id="watchlist-status")
                
                # Favorite Watchlist View
                with Vertical(id="favorite-watchlist-section"):
                    yield Static("⭐ Favorite Watchlist", id="favorite-title")
                    yield Static("", id="favorite-watchlist-name")
                    with VerticalScroll(id="favorite-scroll", can_focus=True):
                        yield DataTable(id="favorite-table")
                    yield Static("", id="favorite-status")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the screen."""
        # Setup watchlist table columns
        watchlist_table = self.query_one("#watchlist-table", DataTable)
        watchlist_table.add_columns("Watchlist Name", "Symbols", "Favorite", "Delete")
        watchlist_table.cursor_type = "cell"  # Enable cell navigation
        
        # Setup favorite table columns
        favorite_table = self.query_one("#favorite-table", DataTable)
        favorite_table.add_columns(
            "Symbol",
            "Type",
            "Name",
            "Open",
            "High",
            "Low",
            "Close",
            "Prev Close",
            "NAV",
            "ETF Premium"
        )
        favorite_table.cursor_type = "row"
        
        # Load watchlists immediately (fast, no API calls)
        self._load_watchlists()
        
        # Focus the watchlist table after loading
        self.call_after_refresh(self._focus_watchlist_table)
        
        # Load favorite watchlist asynchronously (may involve API calls)
        self.set_timer(0.1, self._load_favorite_watchlist_async)
    
    def _focus_watchlist_table(self) -> None:
        """Focus the watchlist table."""
        try:
            table = self.query_one("#watchlist-table", DataTable)
            if table and table.row_count > 0:
                table.focus()
        except Exception as e:
            log(f"Error focusing watchlist table: {e}")
    
    def _load_watchlists(self) -> None:
        """Load and display all watchlists."""
        watchlist_names = storage.list_watchlist_names()
        
        if not watchlist_names:
            self._update_status("No watchlists found. Create one first!", "watchlist")
            return
        
        # Load full watchlist data
        self.watchlists = []
        for name in watchlist_names:
            watchlist = storage.load_watchlist(name)
            if watchlist:
                self.watchlists.append(watchlist)
        
        # Display in table
        self._display_watchlist_list()
    
    def _load_favorite_watchlist_async(self) -> None:
        """Load and display favorite watchlist asynchronously (may involve API calls)."""
        try:
            favorite_watchlist = storage.get_favorite_watchlist()
            
            if favorite_watchlist:
                # Show favorite section
                self.query_one("#favorite-watchlist-section").display = True
                
                # Update watchlist name
                name_widget = self.query_one("#favorite-watchlist-name")
                name_widget.update(f"📋 {favorite_watchlist.name}")
                
                # Show loading status
                status_widget = self.query_one("#favorite-status")
                status_widget.update("Loading price data...")
                
                # Populate favorite table (this may take time due to API calls)
                self._populate_favorite_table(favorite_watchlist.symbols)
                
                # Update status with final count
                total = len(favorite_watchlist.symbols)
                status_widget.update(f"{total} symbol(s)")
            else:
                # Hide favorite section if no favorite
                self.query_one("#favorite-watchlist-section").display = False
                
        except Exception as e:
            log(f"Error loading favorite watchlist: {e}")
            # Hide favorite section on error
            try:
                self.query_one("#favorite-watchlist-section").display = False
            except:
                pass
    
    def _populate_favorite_table(self, symbols) -> None:
        """Populate the favorite table with symbol data."""
        table = self.query_one("#favorite-table", DataTable)
        table.clear()
        
        # Separate equity and ETF symbols
        equity_symbols = [s.name for s in symbols if s.symbol_type.value == 'equity']
        etf_symbols = [s for s in symbols if s.symbol_type.value == 'etf']
        
        # Fetch OHLC data for equity symbols using yfinance
        equity_ohlc_data = data_fetcher.fetch_ohlc_data(equity_symbols) if equity_symbols else {}
        
        # Fetch ETF data using jugaad-data (includes NAV and premium)
        for etf_symbol in etf_symbols:
            try:
                etf_data = data_fetcher.fetch_etf_data(etf_symbol.name)
                if etf_data:
                    self.etf_data_cache[etf_symbol.name] = etf_data
            except Exception as e:
                log(f"Error fetching ETF data for {etf_symbol.name}: {e}")
        
        for symbol in symbols:
            # Get display name - use full_name if available, otherwise try search
            display_name = symbol.full_name if hasattr(symbol, 'full_name') and symbol.full_name else symbol.name
            if display_name == symbol.name:  # If no full_name, try search
                try:
                    results = symbol_search_service.search_symbols(symbol.name, max_results=1)
                    if results and len(results) > 0:
                        display_name = results[0]['name']
                except:
                    pass
            
            # Handle ETFs separately
            if symbol.symbol_type.value == 'etf' and symbol.name in self.etf_data_cache:
                etf_data = self.etf_data_cache[symbol.name]
                
                # Extract OHLC data from ETF data
                open_price = etf_data.open_price
                high_price = etf_data.high_price
                low_price = etf_data.low_price
                close_price = etf_data.close_price or etf_data.current_price
                prev_close = etf_data.previous_close
                nav = etf_data.nav
                premium = etf_data.premium_discount
                
                # Prepare Close value with color highlighting
                if close_price and prev_close:
                    close_str = f"₹{close_price:.2f}"
                    if close_price > prev_close:
                        close_text = Text(close_str, style="bold green")
                    elif close_price < prev_close:
                        close_text = Text(close_str, style="bold red")
                    else:
                        close_text = close_str
                else:
                    close_text = "-"
                
                # Prepare Premium with color highlighting
                if premium is not None:
                    premium_str = f"{premium:.2f}%"
                    abs_premium = abs(premium)
                    if abs_premium > 10:
                        premium_text = Text(premium_str, style="bold red")
                    elif abs_premium >= 5:
                        premium_text = Text(premium_str, style="bold yellow")
                    else:
                        premium_text = Text(premium_str, style="bold green")
                else:
                    premium_text = "N/A"
                
                table.add_row(
                    symbol.name,
                    symbol.symbol_type.value.upper(),
                    display_name,
                    f"₹{open_price:.2f}" if open_price else "-",
                    f"₹{high_price:.2f}" if high_price else "-",
                    f"₹{low_price:.2f}" if low_price else "-",
                    close_text,
                    f"₹{prev_close:.2f}" if prev_close else "-",
                    f"₹{nav:.2f}" if nav else "N/A",
                    premium_text
                )
            
            # Handle equities with yfinance data
            elif symbol.symbol_type.value == 'equity' and symbol.name in equity_ohlc_data and equity_ohlc_data[symbol.name]:
                data = equity_ohlc_data[symbol.name]
                
                # Prepare Close value with color highlighting
                close_price = data['Close']
                prev_close = data['Previous Close']
                close_str = f"₹{close_price}"
                
                if close_price > prev_close:
                    close_text = Text(close_str, style="bold green")
                elif close_price < prev_close:
                    close_text = Text(close_str, style="bold red")
                else:
                    close_text = close_str
                
                table.add_row(
                    symbol.name,
                    symbol.symbol_type.value.upper(),
                    display_name,
                    f"₹{data['Open']}",
                    f"₹{data['High']}",
                    f"₹{data['Low']}",
                    close_text,
                    f"₹{prev_close}",
                    "N/A",  # NAV - not applicable for equity
                    "N/A"   # Premium - not applicable for equity
                )
            else:
                # No data available (index, mutual fund, or failed fetch)
                table.add_row(
                    symbol.name,
                    symbol.symbol_type.value.upper(),
                    display_name,
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "N/A",
                    "N/A"
                )
    
    def _display_watchlist_list(self) -> None:
        """Display watchlists in DataTable."""
        table = self.query_one("#watchlist-table", DataTable)
        table.clear()
        
        for watchlist in self.watchlists:
            count = len(watchlist.symbols)
            
            # Show red heart if favorite, gray heart otherwise
            heart_icon = "❤️" if watchlist.is_favorite else "🩶"
            
            table.add_row(
                watchlist.name,
                str(count),
                heart_icon,
                "🗑"
            )
        
        status_text = f"Found {len(self.watchlists)} watchlist(s). Navigate with arrows, Enter to select."
        self._update_status(status_text, "watchlist")
    
    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        """Handle cell selection in watchlist table."""
        if event.data_table.id == "watchlist-table":
            row_index = event.coordinate.row
            col_index = event.coordinate.column
            
            if 0 <= row_index < len(self.watchlists):
                # Column 0 or 1: View watchlist (name or symbol count)
                if col_index in [0, 1]:
                    self._navigate_to_watchlist_detail(self.watchlists[row_index])
                # Column 2: Toggle favorite (heart button)
                elif col_index == 2:
                    self._toggle_favorite(self.watchlists[row_index])
                # Column 3: Delete watchlist (delete button)
                elif col_index == 3:
                    self._delete_watchlist(self.watchlists[row_index])
    
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in favorite table."""
        if event.data_table.id == "favorite-table":
            # Favorite table - navigate to symbol detail
            favorite_watchlist = storage.get_favorite_watchlist()
            if favorite_watchlist:
                row_index = event.cursor_row
                if 0 <= row_index < len(favorite_watchlist.symbols):
                    symbol = favorite_watchlist.symbols[row_index]
                    self._navigate_to_symbol(symbol.name)
    
    def action_delete_watchlist(self) -> None:
        """Delete the currently selected watchlist."""
        try:
            table = self.query_one("#watchlist-table", DataTable)
            row_index = table.cursor_row
            
            if 0 <= row_index < len(self.watchlists):
                self._delete_watchlist(self.watchlists[row_index])
        except Exception as e:
            log(f"Error in delete action: {e}")
    
    def _toggle_favorite(self, watchlist) -> None:
        """Toggle favorite status of a watchlist."""
        try:
            watchlist_name = watchlist.name
            
            # If already favorite, unfavorite it
            if watchlist.is_favorite:
                storage.unset_favorite_watchlist(watchlist_name)
                log(f"Unfavorited watchlist: {watchlist_name}")
                self._update_status(f"Removed '{watchlist_name}' from favorites.", "watchlist")
            else:
                # Set as favorite (automatically unfavorites others)
                storage.set_favorite_watchlist(watchlist_name)
                log(f"Favorited watchlist: {watchlist_name}")
                self._update_status(f"Set '{watchlist_name}' as favorite!", "watchlist")
            
            # Reload watchlists immediately
            self._load_watchlists()
            
            # Reload favorite watchlist asynchronously
            self.set_timer(0.1, self._load_favorite_watchlist_async)
            
            # Focus the watchlist table after refresh
            self.call_after_refresh(self._focus_watchlist_table)
            
        except Exception as e:
            log(f"Error toggling favorite: {e}")
            self._update_status(f"Failed to toggle favorite: {str(e)}", "watchlist")
    
    def _delete_watchlist(self, watchlist) -> None:
        """Delete the specified watchlist."""
        try:
            watchlist_name = watchlist.name
            
            # Delete from storage
            storage.delete_watchlist(watchlist_name)
            
            # Remove from local list
            self.watchlists = [w for w in self.watchlists if w.name != watchlist_name]
            
            # Refresh the display
            if len(self.watchlists) > 0:
                self._display_watchlist_list()
                self._update_status(f"Deleted watchlist '{watchlist_name}'. {len(self.watchlists)} remaining.", "watchlist")
                # Focus the watchlist table after deletion
                self.call_after_refresh(self._focus_watchlist_table)
            else:
                # No watchlists left
                table = self.query_one("#watchlist-table", DataTable)
                table.clear()
                self._update_status("No watchlists found. Create one first!", "watchlist")
            
            log(f"Deleted watchlist: {watchlist_name}")
        except Exception as e:
            log(f"Error deleting watchlist: {e}")
            self._update_status(f"Failed to delete watchlist: {str(e)}", "watchlist")
    
    def _navigate_to_watchlist_detail(self, watchlist) -> None:
        """Navigate to watchlist detail screen."""
        from .watchlist_detail_screen import WatchlistDetailScreen
        log(f"Navigating to watchlist detail: {watchlist.name}")
        self.app.push_screen(WatchlistDetailScreen(watchlist_name=watchlist.name))
    
    def _navigate_to_symbol(self, symbol_name: str) -> None:
        """Navigate to symbol detail screen, passing cached ETF data if available."""
        from .symbol_detail import SymbolDetailScreen
        log(f"Navigating to symbol: {symbol_name}")
        
        # Pass cached ETF data if available
        cached_data = self.etf_data_cache.get(symbol_name)
        self.app.push_screen(SymbolDetailScreen(symbol=symbol_name, cached_etf_data=cached_data))
    
    def on_key(self, event: events.Key) -> None:
        """Handle key presses for navigation."""
        focused = self.focused
        
        # Handle back navigation
        if event.key in ["q", "escape"]:
            self.action_pop_screen()
            return
        
        # Handle navigation between watchlist table and favorite table
        try:
            watchlist_table = self.query_one("#watchlist-table", DataTable)
            favorite_table = self.query_one("#favorite-table", DataTable)
            favorite_section = self.query_one("#favorite-watchlist-section")
            
            # Only allow navigation if favorite section is visible
            if not favorite_section.display:
                return
            
            # Down arrow: Move from watchlist table to favorite table
            if event.key == "down" and focused == watchlist_table:
                # Check if we're at the last row
                if watchlist_table.cursor_row == watchlist_table.row_count - 1:
                    event.prevent_default()
                    favorite_table.focus()
                    favorite_table.scroll_visible()
            
            # Up arrow: Move from favorite table to watchlist table
            elif event.key == "up" and focused == favorite_table:
                # Check if we're at the first row
                if favorite_table.cursor_row == 0:
                    event.prevent_default()
                    watchlist_table.focus()
                    watchlist_table.scroll_visible()
        except Exception as e:
            log(f"Error in navigation: {e}")
    
    def on_click(self, event: Click) -> None:
        """Handle mouse clicks to focus widgets."""
        widget = self.get_widget_at(event.x, event.y)[0]
        
        # Focus clickable widgets
        if isinstance(widget, DataTable):
            widget.focus()
    
    def _update_status(self, message: str, section: str = "watchlist") -> None:
        """Update status message."""
        if section == "watchlist":
            status = self.query_one("#watchlist-status")
        else:
            status = self.query_one("#favorite-status")
        
        status.update(message)
    
    def action_pop_screen(self) -> None:
        """Go back to main menu."""
        self.app.pop_screen()

