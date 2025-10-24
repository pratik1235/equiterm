"""
Create watchlist screen for adding symbols to new watchlists.
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.screen import Screen
from textual.widgets import Button, Header, Footer, Input, Static, DataTable, Select
from textual.binding import Binding
from textual.message import Message

from ..services.storage import storage
from ..utils.symbol_detector import symbol_detector
from ..models.watchlist import Watchlist, Symbol, SymbolType


class CreateWatchlistScreen(Screen):
    """Screen for creating new watchlists with symbols."""
    
    BINDINGS = [
        Binding("escape", "pop_screen", "Back"),
        Binding("s", "save_watchlist", "Save"),
        Binding("a", "add_symbol", "Add Symbol"),
        Binding("tab", "focus_next", "Next"),
        Binding("shift+tab", "focus_previous", "Previous"),
        Binding("n", "focus_name_input", "Focus Name Input"),
        Binding("y", "focus_symbol_input", "Focus Symbol Input"),
        Binding("c", "focus_scheme_input", "Focus Scheme Input"),
        Binding("r", "focus_remove_button", "Focus Remove Button"),
        Binding("save", "focus_save_button", "Focus Save Button"),
    ]
    
    def __init__(self):
        super().__init__()
        self.watchlist_name = ""
        self.symbols = []
        self.name_input = None
        self.symbol_input = None
        self.scheme_input = None
        self.symbols_table = None
        self.status_text = None
    
    def compose(self) -> ComposeResult:
        """Compose the create watchlist screen."""
        yield Header()
        
        with Container(id="create-container"):
            with Vertical(id="form-section"):
                yield Static("Create New Watchlist", id="form-title")
                
                # Watchlist name input
                yield Static("Watchlist Name:", id="name-label")
                self.name_input = Input(placeholder="e.g., My Portfolio", id="name-input")
                
                # Symbol input section
                yield Static("Add Symbol:", id="symbol-section-title")
                
                with Horizontal(id="symbol-inputs"):
                    yield Static("Symbol:", id="symbol-label")
                    self.symbol_input = Input(placeholder="RELIANCE", id="symbol-input")
                    yield Static("Scheme Code (for ETF/MF):", id="scheme-label")
                    self.scheme_input = Input(placeholder="120716", id="scheme-input")
                
                with Horizontal(id="symbol-buttons"):
                    yield Button("Add Symbol", id="add-symbol-button", variant="primary")
                    yield Button("Remove Selected", id="remove-symbol-button", variant="default")
                
                # Symbols table
                yield Static("Symbols in Watchlist:", id="symbols-title")
                self.symbols_table = DataTable(id="symbols-table")
                
                # Status and actions
                yield Static("", id="status-text")
                
                with Horizontal(id="action-buttons"):
                    yield Button("Save Watchlist", id="save-button", variant="primary")
                    yield Button("Clear All", id="clear-button", variant="default")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the screen."""
        self.symbols_table.add_columns("Symbol", "Type", "Scheme Code")
        self._update_status("Enter watchlist name and add symbols", "info")
        # Focus the name input field after the screen is mounted
        self.call_after_refresh(self._focus_name_input)
    
    def _focus_name_input(self) -> None:
        """Focus the name input field."""
        try:
            self.query_one("#name-input").focus()
        except Exception:
            pass
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes."""
        if event.input.id == "name-input":
            self.watchlist_name = event.value.strip()
        elif event.input.id == "symbol-input":
            # Auto-detect symbol type
            symbol = event.value.strip()
            if symbol:
                symbol_type, scheme_code = symbol_detector.detect_symbol_type(symbol)
                self._update_status(f"Detected: {symbol_type.value.upper()}" + 
                                  (f" (Scheme: {scheme_code})" if scheme_code else ""), "info")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "add-symbol-button":
            self.action_add_symbol()
        elif event.button.id == "remove-symbol-button":
            self.action_remove_symbol()
        elif event.button.id == "save-button":
            self.action_save_watchlist()
        elif event.button.id == "clear-button":
            self.action_clear_all()
    
    def action_add_symbol(self) -> None:
        """Add a symbol to the watchlist."""
        symbol_name = self.symbol_input.value.strip()
        scheme_code = self.scheme_input.value.strip()
        
        if not symbol_name:
            self._update_status("Please enter a symbol name.", "error")
            return
        
        # Auto-detect symbol type
        symbol_type, detected_scheme = symbol_detector.detect_symbol_type(symbol_name)
        
        # Use provided scheme code or detected one
        final_scheme = scheme_code or detected_scheme
        
        # Create symbol object
        symbol = Symbol(
            name=symbol_name,
            symbol_type=symbol_type,
            scheme_code=final_scheme
        )
        
        # Check for duplicates
        if any(s.name == symbol_name for s in self.symbols):
            self._update_status(f"Symbol {symbol_name} already exists in watchlist.", "error")
            return
        
        # Add to symbols list
        self.symbols.append(symbol)
        self._update_symbols_table()
        
        # Clear inputs
        self.symbol_input.value = ""
        self.scheme_input.value = ""
        self.symbol_input.focus()
        
        self._update_status(f"Added {symbol_name} ({symbol_type.value}) to watchlist.", "success")
    
    def action_remove_symbol(self) -> None:
        """Remove selected symbol from watchlist."""
        # For simplicity, remove the last added symbol
        # In a full implementation, this would handle table selection
        if self.symbols:
            removed_symbol = self.symbols.pop()
            self._update_symbols_table()
            self._update_status(f"Removed {removed_symbol.name} from watchlist.", "info")
        else:
            self._update_status("No symbols to remove.", "error")
    
    def action_save_watchlist(self) -> None:
        """Save the watchlist."""
        if not self.watchlist_name:
            self._update_status("Please enter a watchlist name.", "error")
            return
        
        if not self.symbols:
            self._update_status("Please add at least one symbol to the watchlist.", "error")
            return
        
        # Check if watchlist name already exists
        existing_watchlists = storage.list_watchlist_names()
        if self.watchlist_name in existing_watchlists:
            self._update_status(f"Watchlist '{self.watchlist_name}' already exists.", "error")
            return
        
        # Create watchlist
        watchlist = Watchlist(
            name=self.watchlist_name,
            symbols=self.symbols
        )
        
        # Save to storage
        if storage.save_watchlist(watchlist):
            self._update_status(f"Watchlist '{self.watchlist_name}' saved successfully!", "success")
            # Clear form
            self.action_clear_all()
        else:
            self._update_status("Failed to save watchlist.", "error")
    
    def action_clear_all(self) -> None:
        """Clear all form inputs."""
        self.watchlist_name = ""
        self.symbols = []
        self.name_input.value = ""
        self.symbol_input.value = ""
        self.scheme_input.value = ""
        self._update_symbols_table()
        self.name_input.focus()
        self._update_status("Form cleared.", "info")
    
    def _update_symbols_table(self) -> None:
        """Update the symbols table display."""
        table = self.symbols_table
        table.clear()
        
        for symbol in self.symbols:
            scheme_display = symbol.scheme_code or "N/A"
            table.add_row(
                symbol.name,
                symbol.symbol_type.value.upper(),
                scheme_display
            )
    
    def _update_status(self, message: str, status_type: str = "info") -> None:
        """Update status message."""
        status = self.query_one("#status-text")
        status.update(f"[{status_type.upper()}] {message}")
    
    def action_pop_screen(self) -> None:
        """Go back to main menu."""
        self.app.pop_screen()
    
    def on_screen_resume(self) -> None:
        """Called when screen is resumed/shown."""
        # Ensure input is focused when screen is shown
        self.call_after_refresh(self._focus_name_input)
    
    def action_focus_name_input(self) -> None:
        """Focus the name input field."""
        try:
            name_input = self.query_one("#name-input")
            if name_input:
                name_input.focus()
        except Exception:
            pass
    
    def action_focus_symbol_input(self) -> None:
        """Focus the symbol input field."""
        try:
            symbol_input = self.query_one("#symbol-input")
            if symbol_input:
                symbol_input.focus()
        except Exception:
            pass
    
    def action_focus_scheme_input(self) -> None:
        """Focus the scheme input field."""
        try:
            scheme_input = self.query_one("#scheme-input")
            if scheme_input:
                scheme_input.focus()
        except Exception:
            pass
    
    def action_focus_remove_button(self) -> None:
        """Focus the remove button."""
        try:
            remove_button = self.query_one("#remove-symbol-button")
            if remove_button:
                remove_button.focus()
        except Exception:
            pass
    
    def action_focus_save_button(self) -> None:
        """Focus the save button."""
        try:
            save_button = self.query_one("#save-button")
            if save_button:
                save_button.focus()
        except Exception:
            pass
