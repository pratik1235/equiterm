"""
Watchlist detail screen showing symbols in a selected watchlist.
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


class WatchlistDetailScreen(Screen):
    """Screen for viewing watchlist contents."""
    
    BINDINGS = [
        Binding("escape", "pop_screen", "Back"),
        Binding("q", "pop_screen", "Back"),
    ]
    
    def __init__(self, watchlist_name: str):
        super().__init__()
        self.watchlist_name = watchlist_name
        self.current_symbols = []
        self.etf_data_cache = {}  # Cache ETF data to avoid redundant API calls
    
    def compose(self) -> ComposeResult:
        """Compose the watchlist detail screen."""
        yield Header()
        
        with Container(id="watchlist-detail-container"):
            with Vertical(id="symbol-detail-section"):
                yield Static("", id="detail-title")
                with VerticalScroll(id="symbol-scroll", can_focus=True):
                    yield DataTable(id="symbol-table")
                yield Static("", id="symbol-status")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the screen."""
        # Setup symbol table columns with OHLC data, NAV, and ETF Premium
        symbol_table = self.query_one("#symbol-table", DataTable)
        symbol_table.add_columns(
            "Symbol",
            "Type",
            "Name",  # Full name column - will not be truncated
            "Open",
            "High",
            "Low",
            "Close",
            "Prev Close",
            "NAV",
            "ETF Premium"
        )
        symbol_table.cursor_type = "row"
        
        # Load watchlist data
        self._load_watchlist_data()
        
        # Focus the table after loading
        self.call_after_refresh(self._focus_table)
    
    def _focus_table(self) -> None:
        """Focus the symbol table."""
        try:
            table = self.query_one("#symbol-table", DataTable)
            if table and table.row_count > 0:
                table.focus()
        except Exception as e:
            log(f"Error focusing table: {e}")
    
    def _load_watchlist_data(self) -> None:
        """Load and display watchlist symbols."""
        try:
            watchlist = storage.load_watchlist(self.watchlist_name)
            
            if not watchlist:
                self._update_status(f"Watchlist '{self.watchlist_name}' not found!", "symbol")
                return
            
            # Update title
            title = self.query_one("#detail-title")
            title.update(f"Watchlist: {watchlist.name} ({len(watchlist.symbols)} symbols)")
            
            # Populate symbol table
            self._populate_symbol_table(watchlist.symbols)
            
        except Exception as e:
            log(f"Error loading watchlist data: {e}")
            self._update_status(f"Error loading watchlist: {str(e)}", "symbol")
    
    def _populate_symbol_table(self, symbols) -> None:
        """Populate the symbol table with watchlist symbols and OHLC data."""
        table = self.query_one("#symbol-table", DataTable)
        table.clear()
        
        self.current_symbols = symbols
        self.etf_data_cache = {}  # Clear cache for new watchlist
        
        # Show loading message
        self._update_status("Fetching price data...", "symbol")
        
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
        
        status = f"Loaded {len(symbols)} symbol(s). Press Enter to view details. Press Q/Escape to go back."
        self._update_status(status, "symbol")
    
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in symbol table."""
        if event.data_table.id == "symbol-table":
            row_index = event.cursor_row
            if 0 <= row_index < len(self.current_symbols):
                symbol = self.current_symbols[row_index]
                self._navigate_to_symbol(symbol.name)
    
    def _navigate_to_symbol(self, symbol_name: str) -> None:
        """Navigate to symbol detail screen, passing cached ETF data if available."""
        from .symbol_detail import SymbolDetailScreen
        log(f"Navigating to symbol: {symbol_name}")
        
        # Pass cached ETF data if available
        cached_data = self.etf_data_cache.get(symbol_name)
        self.app.push_screen(SymbolDetailScreen(symbol=symbol_name, cached_etf_data=cached_data))
    
    def on_key(self, event: events.Key) -> None:
        """Handle key presses for navigation."""
        # Handle back navigation
        if event.key in ["q", "escape"]:
            self.action_pop_screen()
    
    def on_click(self, event: Click) -> None:
        """Handle mouse clicks to focus widgets."""
        widget = self.get_widget_at(event.x, event.y)[0]
        
        # Focus clickable widgets
        if isinstance(widget, DataTable):
            widget.focus()
    
    def _update_status(self, message: str, section: str = "symbol") -> None:
        """Update status message."""
        status = self.query_one("#symbol-status")
        status.update(message)
    
    def action_pop_screen(self) -> None:
        """Go back to watchlist list screen."""
        self.app.pop_screen()

