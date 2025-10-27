"""
Watchlist view screen with list selection and symbol navigation.
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, VerticalScroll, Horizontal
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, ListItem, ListView, DataTable, Button
from textual.binding import Binding
from textual import log, events
from textual.events import Click
from rich.text import Text

from ..services.storage import storage
from ..services.symbol_search import symbol_search_service

try:
    import yfinance as yf
except ImportError:
    yf = None


class WatchlistViewScreen(Screen):
    """Screen for viewing watchlists and navigating to symbols."""
    
    BINDINGS = [
        Binding("escape", "pop_screen", "Back"),
        Binding("q", "pop_screen", "Back"),
        Binding("d", "delete_watchlist", "Delete", show=False),
    ]
    
    def __init__(self):
        super().__init__()
        self.watchlists = []
        self.current_watchlist = None
        self.current_symbols = []
        self.view_mode = "list"  # "list" or "detail"
    
    def compose(self) -> ComposeResult:
        """Compose the watchlist view screen."""
        yield Header()
        
        with Container(id="watchlist-container"):
            # Watchlist List View
            with Vertical(id="watchlist-list-section"):
                yield Static("Your Watchlists", id="watchlist-title")
                with VerticalScroll(id="watchlist-scroll", can_focus=True):
                    yield DataTable(id="watchlist-table")
                yield Static("", id="watchlist-status")
            
            # Symbol Detail View (hidden initially)
            with Vertical(id="symbol-detail-section"):
                yield Static("", id="detail-title")
                with VerticalScroll(id="symbol-scroll", can_focus=True):
                    yield DataTable(id="symbol-table")
                yield Static("", id="symbol-status")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the screen."""
        # Setup watchlist table columns
        watchlist_table = self.query_one("#watchlist-table", DataTable)
        watchlist_table.add_columns("Watchlist Name", "Symbols", "Delete")
        watchlist_table.cursor_type = "cell"  # Enable cell navigation
        
        # Setup symbol table columns with OHLC data
        symbol_table = self.query_one("#symbol-table", DataTable)
        symbol_table.add_columns(
            "Symbol",
            "Type",
            "Name",  # Full name column - will not be truncated
            "Open",
            "High",
            "Low",
            "Close",
            "Prev Close"
        )
        symbol_table.cursor_type = "row"
        
        # Hide detail section initially
        self.query_one("#symbol-detail-section").display = False
        
        # Load watchlists
        self._load_watchlists()
        
        # Focus the watchlist table after loading
        self.call_after_refresh(self._focus_watchlist_table)
    
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
    
    def _display_watchlist_list(self) -> None:
        """Display watchlists in DataTable."""
        table = self.query_one("#watchlist-table", DataTable)
        table.clear()
        
        for watchlist in self.watchlists:
            count = len(watchlist.symbols)
            table.add_row(
                watchlist.name,
                str(count),
                "🗑 Delete"
            )
        
        status_text = f"Found {len(self.watchlists)} watchlist(s). Navigate with arrow keys, Enter to view."
        self._update_status(status_text, "watchlist")
    
    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        """Handle cell selection in watchlist table."""
        if event.data_table.id == "watchlist-table":
            row_index = event.coordinate.row
            col_index = event.coordinate.column
            
            if 0 <= row_index < len(self.watchlists):
                # Column 0 or 1: View watchlist (name or symbol count)
                if col_index in [0, 1]:
                    self._show_watchlist_detail(self.watchlists[row_index])
                # Column 2: Delete watchlist (delete button)
                elif col_index == 2:
                    self._delete_watchlist(self.watchlists[row_index])
    
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in symbol table."""
        if event.data_table.id == "symbol-table":
            # Symbol table - navigate to symbol detail
            row_index = event.cursor_row
            if 0 <= row_index < len(self.current_symbols):
                symbol = self.current_symbols[row_index]
                self._navigate_to_symbol(symbol.name)
    
    def action_delete_watchlist(self) -> None:
        """Delete the currently selected watchlist."""
        if self.view_mode != "list":
            return
        
        try:
            table = self.query_one("#watchlist-table", DataTable)
            row_index = table.cursor_row
            
            if 0 <= row_index < len(self.watchlists):
                self._delete_watchlist(self.watchlists[row_index])
        except Exception as e:
            log(f"Error in delete action: {e}")
    
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
    
    def _show_watchlist_detail(self, watchlist) -> None:
        """Show symbols in the selected watchlist."""
        self.current_watchlist = watchlist
        self.view_mode = "detail"
        
        # Hide list, show detail
        self.query_one("#watchlist-list-section").display = False
        self.query_one("#symbol-detail-section").display = True
        
        # Update title
        title = self.query_one("#detail-title")
        title.update(f"Watchlist: {watchlist.name} ({len(watchlist.symbols)} symbols)")
        
        # Populate symbol table
        self._populate_symbol_table(watchlist.symbols)
        
        # Focus the table after refresh
        self.call_after_refresh(self._focus_table)
    
    def _focus_table(self) -> None:
        """Focus the symbol table."""
        try:
            table = self.query_one("#symbol-table", DataTable)
            if table and table.row_count > 0:
                table.focus()
        except Exception as e:
            log(f"Error focusing table: {e}")
    
    def _get_stock_data(self, symbols):
        """
        Get OHLC and Previous Close data for multiple Indian stocks using yfinance.
        
        Parameters:
        symbols (list): List of stock symbols (e.g., ['RELIANCE', 'TCS'])
        
        Returns:
        dict: Dictionary with symbols as keys and stock data as values
        """
        if yf is None:
            log("yfinance not available")
            return {}
        
        if not symbols:
            return {}
        
        try:
            # Append .NS to each symbol for NSE
            nse_symbols = [symbol + '.NS' for symbol in symbols]
            
            # Download data for the last 2 days to get current and previous close
            data = yf.download(nse_symbols, period='2d', progress=False)
            
            result = {}
            
            # Handle single stock vs multiple stocks
            if len(symbols) == 1:
                symbol = symbols[0]
                try:
                    latest_data = data.iloc[-1]  # Latest day
                    previous_close = data['Close'].iloc[-2] if len(data) >= 2 else data['Close'].iloc[-1]
                    
                    result[symbol] = {
                        'Open': round(latest_data['Open'], 2),
                        'High': round(latest_data['High'], 2),
                        'Low': round(latest_data['Low'], 2),
                        'Close': round(latest_data['Close'], 2),
                        'Previous Close': round(previous_close, 2)
                    }
                except Exception as e:
                    log(f"Error processing {symbol}: {e}")
                    result[symbol] = None
            else:
                # For multiple stocks
                for symbol in symbols:
                    try:
                        nse_symbol = symbol + '.NS'
                        
                        # Get latest day data
                        latest_open = data['Open'][nse_symbol].iloc[-1]
                        latest_high = data['High'][nse_symbol].iloc[-1]
                        latest_low = data['Low'][nse_symbol].iloc[-1]
                        latest_close = data['Close'][nse_symbol].iloc[-1]
                        
                        # Get previous close
                        if len(data) >= 2:
                            previous_close = data['Close'][nse_symbol].iloc[-2]
                        else:
                            previous_close = latest_close
                        
                        result[symbol] = {
                            'Open': round(latest_open, 2),
                            'High': round(latest_high, 2),
                            'Low': round(latest_low, 2),
                            'Close': round(latest_close, 2),
                            'Previous Close': round(previous_close, 2)
                        }
                    except Exception as e:
                        log(f"Error processing {symbol}: {e}")
                        result[symbol] = None
            
            return result
        except Exception as e:
            log(f"Error fetching stock data: {e}")
            return {}
    
    def _populate_symbol_table(self, symbols) -> None:
        """Populate the symbol table with watchlist symbols and OHLC data."""
        table = self.query_one("#symbol-table", DataTable)
        table.clear()
        
        self.current_symbols = symbols
        
        # Show loading message
        self._update_status("Fetching price data...", "symbol")
        
        # Get all equity/ETF symbols for batch fetch
        equity_symbols = [s.name for s in symbols if s.symbol_type.value in ['equity', 'etf']]
        
        # Fetch OHLC data for all equity symbols at once
        stock_data = self._get_stock_data(equity_symbols) if equity_symbols else {}
        
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
            
            # DO NOT truncate - let the table handle scrolling
            # The table will be horizontally scrollable
            
            # Get OHLC data if available
            if symbol.name in stock_data and stock_data[symbol.name]:
                data = stock_data[symbol.name]
                
                # Prepare Close value with color highlighting
                close_price = data['Close']
                prev_close = data['Previous Close']
                close_str = f"₹{close_price}"
                
                # Color highlight based on comparison with previous close
                if close_price > prev_close:
                    close_text = Text(close_str, style="bold green")
                elif close_price < prev_close:
                    close_text = Text(close_str, style="bold red")
                else:
                    close_text = close_str  # No highlight when equal
                
                table.add_row(
                    symbol.name,
                    symbol.symbol_type.value.upper(),
                    display_name,  # Full name - not truncated
                    f"₹{data['Open']}",
                    f"₹{data['High']}",
                    f"₹{data['Low']}",
                    close_text,  # Color-highlighted Close
                    f"₹{prev_close}"
                )
            else:
                # No data available (index, mutual fund, or failed fetch)
                table.add_row(
                    symbol.name,
                    symbol.symbol_type.value.upper(),
                    display_name,  # Full name - not truncated
                    "-",
                    "-",
                    "-",
                    "-",
                    "-"
                )
        
        status = f"Loaded {len(symbols)} symbol(s). Press Enter to view details. Press Q/Escape to go back."
        self._update_status(status, "symbol")
    
    def _navigate_to_symbol(self, symbol_name: str) -> None:
        """Navigate to symbol detail screen."""
        from .symbol_detail import SymbolDetailScreen
        log(f"Navigating to symbol: {symbol_name}")
        self.app.push_screen(SymbolDetailScreen(symbol=symbol_name))
    
    def on_key(self, event: events.Key) -> None:
        """Handle key presses for navigation."""
        focused = self.focused
        
        # Handle back navigation
        if event.key in ["q", "escape"]:
            if self.view_mode == "detail":
                # Go back to list view
                event.prevent_default()
                self._back_to_list()
            else:
                # Go back to main menu
                self.action_pop_screen()
            return
        
        # Enhanced up/down navigation
        # In list view mode, ListView handles its own navigation
        # In detail view mode, DataTable handles its own navigation
        # No special handling needed as Textual handles this automatically
    
    def on_click(self, event: Click) -> None:
        """Handle mouse clicks to focus widgets."""
        widget = self.get_widget_at(event.x, event.y)[0]
        
        # Focus clickable widgets
        if isinstance(widget, (DataTable, Button)):
            widget.focus()
    
    def _back_to_list(self) -> None:
        """Go back to watchlist list view."""
        self.view_mode = "list"
        self.current_watchlist = None
        self.current_symbols = []
        
        # Show list, hide detail
        self.query_one("#watchlist-list-section").display = True
        self.query_one("#symbol-detail-section").display = False
        
        # Focus the watchlist table
        self.call_after_refresh(self._focus_watchlist_table)
        
        # Update status
        self._update_status(f"Found {len(self.watchlists)} watchlist(s). Navigate with arrow keys, Enter to view.", "watchlist")
    
    def _update_status(self, message: str, section: str = "watchlist") -> None:
        """Update status message."""
        if section == "watchlist":
            status = self.query_one("#watchlist-status")
        else:
            status = self.query_one("#symbol-status")
        
        status.update(message)
    
    def action_pop_screen(self) -> None:
        """Go back to main menu."""
        self.app.pop_screen()
