"""
Create watchlist screen with autocomplete search for adding symbols.
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, VerticalScroll, Horizontal
from textual.screen import Screen
from textual.widgets import Button, Header, Footer, Input, Static, DataTable, ListItem, ListView
from textual.binding import Binding
from textual import log, events

from ..services.storage import storage
from ..services.symbol_search import symbol_search_service
from ..utils.symbol_detector import symbol_detector
from ..models.watchlist import Watchlist, Symbol, SymbolType


class CreateWatchlistScreen(Screen):
    """Screen for creating new watchlists with autocomplete symbol search."""
    
    BINDINGS = [
        Binding("escape", "pop_screen", "Back"),
        Binding("q", "pop_screen", "Back"),
        Binding("ctrl+s", "save_watchlist", "Save Watchlist"),
    ]
    
    def __init__(self):
        super().__init__()
        self.watchlist_name = ""
        self.symbols = []
        self.search_results = []
    
    def compose(self) -> ComposeResult:
        """Compose the create watchlist screen."""
        yield Header()
        
        with VerticalScroll(id="create-main-scroll", can_focus=True):
            with Container(id="create-container"):
                # Watchlist Name Section
                with Vertical(id="name-section"):
                    yield Static("Create New Watchlist", id="form-title")
                    yield Static("Watchlist Name:", id="name-label")
                    yield Input(placeholder="e.g., My Tech Stocks", id="name-input")
                
                # Symbol Search Section
                with Vertical(id="search-section"):
                    yield Static("Add Symbols:", id="search-title")
                    yield Input(
                        placeholder="Search by symbol or company name...",
                        id="symbol-search-input"
                    )
                    with Vertical(id="search-results-section"):
                        yield ListView(id="search-results-list")
                        yield Static("", id="search-status")
                
                # Added Symbols Section
                with Vertical(id="symbols-section"):
                    yield Static("Symbols in Watchlist:", id="symbols-title")
                    yield DataTable(id="symbols-table")
                
                # Action Buttons
                with Horizontal(id="action-buttons"):
                    yield Button("💾 Save Watchlist", id="save-button", variant="primary")
                    yield Button("🗑️  Clear All", id="clear-button", variant="default")
                
                yield Static("", id="status-text")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the screen."""
        # Setup symbols table
        symbols_table = self.query_one("#symbols-table", DataTable)
        symbols_table.add_columns("Symbol", "Name", "Type")
        
        # Hide search results initially
        self.query_one("#search-results-section").display = False
        
        # Focus name input
        self.query_one("#name-input", Input).focus()
        
        self._update_status("Enter a name for your watchlist and search for symbols to add.")
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes."""
        if event.input.id == "name-input":
            self.watchlist_name = event.value.strip()
        
        elif event.input.id == "symbol-search-input":
            query = event.value.strip()
            
            if len(query) >= 2:
                # Perform search
                self._perform_search(query)
            else:
                # Clear results
                self._clear_search_results()
    
    def on_key(self, event: events.Key) -> None:
        """Handle key presses for navigation."""
        focused = self.focused
        
        # Prevent 'q' from going back when input is focused
        if isinstance(focused, Input) and event.key == "q":
            return  # Let the input handle it
        
        # Enhanced navigation between all sections
        if event.key == "down":
            # From name input -> search input
            if isinstance(focused, Input) and focused.id == "name-input":
                event.prevent_default()
                self.query_one("#symbol-search-input", Input).focus()
                return
            
            # From search input -> results (if available) or symbols table
            elif isinstance(focused, Input) and focused.id == "symbol-search-input":
                list_view = self.query_one("#search-results-list", ListView)
                if list_view.children and len(list_view.children) > 0 and list_view.display:
                    event.prevent_default()
                    list_view.focus()
                    list_view.index = 0
                else:
                    # Jump to symbols table if no search results
                    event.prevent_default()
                    symbols_table = self.query_one("#symbols-table", DataTable)
                    if symbols_table.row_count > 0:
                        symbols_table.focus()
                return
            
            # From search results -> symbols table
            elif isinstance(focused, ListView) and focused.id == "search-results-list":
                # Let ListView handle navigation within itself, unless at the end
                if focused.index == len(focused.children) - 1:
                    event.prevent_default()
                    symbols_table = self.query_one("#symbols-table", DataTable)
                    if symbols_table.row_count > 0:
                        symbols_table.focus()
                return
            
            # From symbols table -> buttons
            elif isinstance(focused, DataTable) and focused.id == "symbols-table":
                # Let DataTable handle navigation within itself, unless at the end
                if focused.cursor_row == focused.row_count - 1:
                    event.prevent_default()
                    self.query_one("#save-button", Button).focus()
                return
        
        elif event.key == "up":
            # From search input -> name input
            if isinstance(focused, Input) and focused.id == "symbol-search-input":
                event.prevent_default()
                self.query_one("#name-input", Input).focus()
                return
            
            # From search results -> search input (if at top)
            elif isinstance(focused, ListView) and focused.id == "search-results-list":
                if focused.index == 0:
                    event.prevent_default()
                    self.query_one("#symbol-search-input", Input).focus()
                return
            
            # From symbols table -> search results or search input
            elif isinstance(focused, DataTable) and focused.id == "symbols-table":
                if focused.cursor_row == 0:
                    event.prevent_default()
                    list_view = self.query_one("#search-results-list", ListView)
                    if list_view.children and len(list_view.children) > 0 and list_view.display:
                        list_view.focus()
                        list_view.index = len(list_view.children) - 1
                    else:
                        self.query_one("#symbol-search-input", Input).focus()
                return
            
            # From buttons -> symbols table
            elif isinstance(focused, Button):
                event.prevent_default()
                symbols_table = self.query_one("#symbols-table", DataTable)
                if symbols_table.row_count > 0:
                    symbols_table.focus()
                else:
                    self.query_one("#symbol-search-input", Input).focus()
                return
    
    def _perform_search(self, query: str) -> None:
        """Perform symbol search."""
        results = symbol_search_service.search_symbols(query, max_results=10)
        self.search_results = results
        self._display_search_results(results)
    
    def _display_search_results(self, results: list) -> None:
        """Display search results."""
        list_view = self.query_one("#search-results-list", ListView)
        status = self.query_one("#search-status")
        results_section = self.query_one("#search-results-section")
        
        list_view.clear()
        
        if results:
            results_section.display = True
            
            for result in results:
                symbol = result['symbol']
                name = result['name']
                
                # Check if already added
                already_added = any(s.name == symbol for s in self.symbols)
                prefix = "✓ " if already_added else "  "
                
                item_text = f"{prefix}{symbol:15} | {name}"
                list_item = ListItem(Static(item_text))
                list_view.append(list_item)
            
            status.update(f"Found {len(results)} results. Press Enter to add, ↑↓ to navigate.")
        else:
            results_section.display = True
            status.update("No results found.")
    
    def _clear_search_results(self) -> None:
        """Clear search results."""
        list_view = self.query_one("#search-results-list", ListView)
        list_view.clear()
        self.search_results = []
        self.query_one("#search-results-section").display = False
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle symbol selection from search results."""
        if event.list_view.id == "search-results-list":
            index = event.list_view.index
            if 0 <= index < len(self.search_results):
                result = self.search_results[index]
                self._add_symbol_from_search(result['symbol'], result['name'])
    
    def _add_symbol_from_search(self, symbol_name: str, company_name: str) -> None:
        """Add a symbol from search results to the watchlist."""
        # Check for duplicates
        if any(s.name == symbol_name for s in self.symbols):
            self._update_status(f"✓ {symbol_name} is already in the watchlist.", "info")
            # Refresh display to show checkmark
            self._display_search_results(self.search_results)
            return
        
        # Detect symbol type
        symbol_type, scheme_code = symbol_detector.detect_symbol_type(symbol_name)
        
        # Create symbol object
        symbol = Symbol(
            name=symbol_name,
            symbol_type=symbol_type,
            scheme_code=scheme_code
        )
        
        # Add to symbols list
        self.symbols.append(symbol)
        self._update_symbols_table()
        
        # Update status
        self._update_status(f"✓ Added {symbol_name} to watchlist ({len(self.symbols)} symbols)", "success")
        
        # Refresh search results to show checkmark
        self._display_search_results(self.search_results)
        
        # Keep focus on search input for quick additions
        self.query_one("#symbol-search-input", Input).focus()
    
    def _update_symbols_table(self) -> None:
        """Update the symbols table display."""
        table = self.query_one("#symbols-table", DataTable)
        table.clear()
        
        for symbol in self.symbols:
            # Get company name from search results if available
            company_name = ""
            for result in self.search_results:
                if result['symbol'] == symbol.name:
                    company_name = result['name']
                    break
            
            if not company_name:
                company_name = symbol.name
            
            table.add_row(
                symbol.name,
                company_name[:40] + "..." if len(company_name) > 40 else company_name,
                symbol.symbol_type.value.upper()
            )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "save-button":
            self.action_save_watchlist()
        elif event.button.id == "clear-button":
            self.action_clear_all()
    
    def action_save_watchlist(self) -> None:
        """Save the watchlist."""
        if not self.watchlist_name:
            self._update_status("❌ Please enter a watchlist name.", "error")
            self.query_one("#name-input", Input).focus()
            return
        
        if not self.symbols:
            self._update_status("❌ Please add at least one symbol to the watchlist.", "error")
            self.query_one("#symbol-search-input", Input).focus()
            return
        
        # Check if watchlist name already exists
        existing_watchlists = storage.list_watchlist_names()
        if self.watchlist_name in existing_watchlists:
            self._update_status(f"❌ Watchlist '{self.watchlist_name}' already exists.", "error")
            return
        
        # Create watchlist
        watchlist = Watchlist(
            name=self.watchlist_name,
            symbols=self.symbols
        )
        
        # Save to storage
        if storage.save_watchlist(watchlist):
            self._update_status(
                f"✓ Watchlist '{self.watchlist_name}' saved with {len(self.symbols)} symbols!",
                "success"
            )
            # Clear form after short delay
            self.set_timer(2.0, self.action_clear_all)
        else:
            self._update_status("❌ Failed to save watchlist.", "error")
    
    def action_clear_all(self) -> None:
        """Clear all form inputs."""
        self.watchlist_name = ""
        self.symbols = []
        self.search_results = []
        
        self.query_one("#name-input", Input).value = ""
        self.query_one("#symbol-search-input", Input).value = ""
        
        self._update_symbols_table()
        self._clear_search_results()
        
        self.query_one("#name-input", Input).focus()
        self._update_status("Form cleared. Ready to create a new watchlist.")
    
    def _update_status(self, message: str, status_type: str = "info") -> None:
        """Update status message."""
        status = self.query_one("#status-text")
        
        # Add color based on status type
        if status_type == "success":
            styled_message = f"[green]{message}[/green]"
        elif status_type == "error":
            styled_message = f"[red]{message}[/red]"
        else:
            styled_message = message
        
        status.update(styled_message)
    
    def action_pop_screen(self) -> None:
        """Go back to main menu."""
        self.app.pop_screen()
