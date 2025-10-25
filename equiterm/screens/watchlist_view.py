"""
Watchlist view screen with list selection and symbol navigation.
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, ListItem, ListView, DataTable
from textual.binding import Binding
from textual import log, events
from textual.events import Click

from ..services.storage import storage
from ..services.symbol_search import symbol_search_service


class WatchlistViewScreen(Screen):
    """Screen for viewing watchlists and navigating to symbols."""
    
    BINDINGS = [
        Binding("escape", "pop_screen", "Back"),
        Binding("q", "pop_screen", "Back"),
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
                    yield ListView(id="watchlist-listview")
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
        # Setup symbol table columns
        symbol_table = self.query_one("#symbol-table", DataTable)
        symbol_table.add_columns("Symbol", "Type", "Name")
        symbol_table.cursor_type = "row"
        
        # Hide detail section initially
        self.query_one("#symbol-detail-section").display = False
        
        # Load watchlists
        self._load_watchlists()
        
        # Focus the listview after loading
        self.call_after_refresh(self._focus_listview)
    
    def _focus_listview(self) -> None:
        """Focus the listview after mount."""
        try:
            listview = self.query_one("#watchlist-listview", ListView)
            if listview and listview.children and len(listview.children) > 0:
                listview.focus()
        except Exception as e:
            log(f"Error focusing listview: {e}")
    
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
        
        # Display in list
        self._display_watchlist_list()
    
    def _display_watchlist_list(self) -> None:
        """Display watchlists in ListView."""
        listview = self.query_one("#watchlist-listview", ListView)
        listview.clear()
        
        for watchlist in self.watchlists:
            count = len(watchlist.symbols)
            item_text = f"{watchlist.name:30} | {count} symbols"
            listview.append(ListItem(Static(item_text)))
        
        status_text = f"Found {len(self.watchlists)} watchlist(s). Select one to view symbols."
        self._update_status(status_text, "watchlist")
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle watchlist selection."""
        if event.list_view.id == "watchlist-listview":
            index = event.list_view.index
            if 0 <= index < len(self.watchlists):
                self._show_watchlist_detail(self.watchlists[index])
    
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
    
    def _populate_symbol_table(self, symbols) -> None:
        """Populate the symbol table with watchlist symbols."""
        table = self.query_one("#symbol-table", DataTable)
        table.clear()
        
        self.current_symbols = symbols
        
        for symbol in symbols:
            # Try to get company name from search
            company_name = symbol.name
            try:
                results = symbol_search_service.search_symbols(symbol.name, max_results=1)
                if results and len(results) > 0:
                    company_name = results[0]['name']
            except:
                pass
            
            table.add_row(
                symbol.name,
                symbol.symbol_type.value.upper(),
                company_name[:50] + "..." if len(company_name) > 50 else company_name
            )
        
        status = f"Press Enter on a symbol to view details. Press Q/Escape to go back."
        self._update_status(status, "symbol")
    
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle symbol row selection."""
        if event.data_table.id == "symbol-table":
            row_index = event.cursor_row
            if 0 <= row_index < len(self.current_symbols):
                symbol = self.current_symbols[row_index]
                self._navigate_to_symbol(symbol.name)
    
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
        if isinstance(widget, (ListView, DataTable)):
            widget.focus()
    
    def _back_to_list(self) -> None:
        """Go back to watchlist list view."""
        self.view_mode = "list"
        self.current_watchlist = None
        self.current_symbols = []
        
        # Show list, hide detail
        self.query_one("#watchlist-list-section").display = True
        self.query_one("#symbol-detail-section").display = False
        
        # Focus the list
        self.query_one("#watchlist-listview", ListView).focus()
        
        # Update status
        self._update_status(f"Found {len(self.watchlists)} watchlist(s). Select one to view symbols.", "watchlist")
    
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
