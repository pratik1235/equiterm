from textual.app import ComposeResult
from textual.containers import Container, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Header, Footer, Static, ListView, ListItem
from textual.binding import Binding
from textual import log

from ..services.storage import storage
from ..models.watchlist import Symbol, SymbolType
from ..utils.symbol_detector import symbol_detector

class AddToWatchlistScreen(Screen):
    """Screen for selecting a watchlist to add a symbol to."""
    
    BINDINGS = [
        Binding("escape", "pop_screen", "Back"),
        Binding("q", "pop_screen", "Back"),
    ]
    
    def __init__(self, symbol: str, symbol_type: SymbolType = None, full_name: str = None):
        super().__init__()
        self.symbol = symbol
        
        # Use provided symbol_type or detect it
        if symbol_type:
            self.symbol_type = symbol_type
            _, self.scheme_code = symbol_detector.detect_symbol_type(symbol)
        else:
            self.symbol_type, self.scheme_code = symbol_detector.detect_symbol_type(symbol)
        
        self.full_name = full_name
        self.watchlist_names = []
    
    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="select-main-scroll", can_focus=True):
            with Container(id="select-watchlist-container"):
                with Vertical():
                    yield Static(f"Add '{self.symbol}' to Watchlist", id="select-heading")
                    yield Static("Select a watchlist:", id="select-label")
                    yield ListView(id="watchlist-listview")
                    yield Static("", id="select-status")
        yield Footer()
    
    def on_mount(self) -> None:
        """Load watchlists and focus the list."""
        self.watchlist_names = storage.list_watchlist_names()
        
        if not self.watchlist_names:
            self.query_one("#select-status").update("No watchlists found. Create one first!")
            return
        
        # Populate the list
        listview = self.query_one("#watchlist-listview", ListView)
        for name in self.watchlist_names:
            watchlist = storage.load_watchlist(name)
            if watchlist:
                count = len(watchlist.symbols)
                item_text = f"{name:30} | {count} symbols"
                listview.append(ListItem(Static(item_text)))
        
        # Auto-focus the list
        self.call_after_refresh(self._focus_list)
    
    def _focus_list(self) -> None:
        """Focus the watchlist list."""
        try:
            listview = self.query_one("#watchlist-listview", ListView)
            if listview.children and len(listview.children) > 0:
                listview.focus()
                self.query_one("#select-status").update("Use ↑↓ to navigate, Enter to add to watchlist")
        except Exception as e:
            log(f"Error focusing list: {e}")
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle watchlist selection."""
        if event.list_view.id == "watchlist-listview":
            index = event.list_view.index
            if 0 <= index < len(self.watchlist_names):
                selected_name = self.watchlist_names[index]
                self._add_to_watchlist(selected_name)
    
    def _add_to_watchlist(self, watchlist_name: str) -> None:
        """Add the symbol to the selected watchlist."""
        try:
            watchlist = storage.load_watchlist(watchlist_name)
            if watchlist:
                # Create symbol object with full_name
                symobj = Symbol(
                    name=self.symbol,
                    symbol_type=self.symbol_type,
                    full_name=self.full_name,
                    scheme_code=self.scheme_code
                )
                
                # Check if symbol already exists
                if any(s.name == self.symbol for s in watchlist.symbols):
                    self.query_one("#select-status").update(
                        f"'{self.symbol}' is already in '{watchlist_name}'. Press Q/Escape to go back."
                    )
                    return
                
                # Add symbol and save
                watchlist.add_symbol(symobj)
                storage.save_watchlist(watchlist)
                
                self.query_one("#select-status").update(
                    f"✅ Added '{self.symbol}' to '{watchlist_name}'! Press Q/Escape to go back."
                )
            else:
                self.query_one("#select-status").update("Error: Could not load watchlist.")
        except Exception as e:
            log(f"Error adding to watchlist: {e}")
            self.query_one("#select-status").update(f"Error: {str(e)}")
    
    def action_pop_screen(self) -> None:
        self.app.pop_screen()
