from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Header, Footer, Static, Select
from textual.binding import Binding

from ..services.storage import storage
from ..models.watchlist import Symbol, SymbolType
from ..utils.symbol_detector import symbol_detector

class SelectWatchlistScreen(Screen):
    BINDINGS = [
        Binding("escape", "pop_screen", "Back"),
    ]
    def __init__(self, symbol: str):
        super().__init__()
        self.symbol = symbol
        self.symbol_type, self.scheme_code = symbol_detector.detect_symbol_type(symbol)
        self.select_widget = None
    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="select-watchlist-container"):
            with Vertical():
                yield Static(f"Add '{self.symbol}' to Watchlist", id="select-heading")
                self.select_widget = Select([], id="watchlist-select")
                yield self.select_widget
                yield Button("Add to Selected Watchlist", id="add-to-list-btn", variant="primary")
                yield Static("", id="select-status")
        yield Footer()
    def on_mount(self) -> None:
        names = storage.list_watchlist_names()
        self.select_widget.set_options([(n, n) for n in names] if names else [("No Watchlists", "")])
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add-to-list-btn":
            selected = self.select_widget.value
            if not selected:
                self.query_one("#select-status").update("Select a watchlist.")
                return
            wlist = storage.load_watchlist(selected)
            if wlist:
                # Add symbol and save
                symobj = Symbol(self.symbol, self.symbol_type, scheme_code=self.scheme_code)
                wlist.add_symbol(symobj)
                storage.save_watchlist(wlist)
                self.query_one("#select-status").update(f"Added '{self.symbol}' to '{selected}'! Press Escape to go back.")
                return
            self.query_one("#select-status").update("Error: Could not load watchlist.")
    def action_pop_screen(self) -> None:
        self.app.pop_screen()
