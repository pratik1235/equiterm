"""
Help screen showing keyboard shortcuts in tabular format.
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, DataTable
from textual.binding import Binding


class HelpScreen(Screen):
    """Help screen showing keyboard shortcuts in a table."""
    
    BINDINGS = [
        Binding("escape", "pop_screen", "Back"),
        Binding("q", "pop_screen", "Back"),
        Binding("h", "pop_screen", "Back"),
    ]
    
    def compose(self) -> ComposeResult:
        """Compose the help screen."""
        yield Header()
        
        with Container(id="help-container"):
            with VerticalScroll(id="help-scroll", can_focus=True):
                yield Static("EquiTerm - Keyboard Shortcuts", id="help-title")
                
                # Global Shortcuts Table
                yield Static("Global Shortcuts (All Screens)", classes="section-title")
                yield DataTable(id="global-shortcuts-table", classes="shortcuts-table")
                
                yield Static("", classes="spacer")
                
                # Main Menu Shortcuts Table
                yield Static("Main Menu", classes="section-title")
                yield DataTable(id="main-menu-table", classes="shortcuts-table")
                
                yield Static("", classes="spacer")
                
                # Fetch Symbol Shortcuts Table
                yield Static("Fetch Symbol Screen", classes="section-title")
                yield DataTable(id="fetch-symbol-table", classes="shortcuts-table")
                
                yield Static("", classes="spacer")
                
                # Create Watchlist Shortcuts Table
                yield Static("Create Watchlist Screen", classes="section-title")
                yield DataTable(id="create-watchlist-table", classes="shortcuts-table")
                
                yield Static("", classes="spacer")
                
                # Watchlist View Shortcuts Table
                yield Static("Watchlist View Screen", classes="section-title")
                yield DataTable(id="watchlist-view-table", classes="shortcuts-table")
                
                yield Static("", classes="spacer")
                
                # Symbol Detail Shortcuts Table
                yield Static("Symbol Detail Screen", classes="section-title")
                yield DataTable(id="symbol-detail-table", classes="shortcuts-table")
                
                yield Static("", classes="spacer")
                
                yield Static("Press Q, Escape, or H to go back", id="help-footer")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the help screen with shortcut data."""
        self._populate_global_shortcuts()
        self._populate_main_menu_shortcuts()
        self._populate_fetch_symbol_shortcuts()
        self._populate_create_watchlist_shortcuts()
        self._populate_watchlist_view_shortcuts()
        self._populate_symbol_detail_shortcuts()
        
        # Auto-focus the scroll container
        self.call_after_refresh(self._focus_scroll)
    
    def _focus_scroll(self) -> None:
        """Focus the scroll container."""
        try:
            scroll = self.query_one("#help-scroll")
            scroll.focus()
        except Exception:
            pass
    
    def _populate_global_shortcuts(self) -> None:
        """Populate global shortcuts table."""
        table = self.query_one("#global-shortcuts-table", DataTable)
        table.add_columns("Key", "Action", "Notes")
        
        shortcuts = [
            ("↑ / ↓", "Navigate", "Move up/down through items"),
            ("Enter", "Select/Activate", "Select current item or activate button"),
            ("Tab", "Next Field", "Move to next input field"),
            ("Shift+Tab", "Previous Field", "Move to previous input field"),
            ("Escape", "Go Back", "Return to previous screen"),
            ("Q", "Go Back", "Return to previous screen (disabled in inputs)"),
            ("Mouse Click", "Focus/Select", "Click to focus or select any element"),
        ]
        
        for key, action, notes in shortcuts:
            table.add_row(key, action, notes)
    
    def _populate_main_menu_shortcuts(self) -> None:
        """Populate main menu shortcuts table."""
        table = self.query_one("#main-menu-table", DataTable)
        table.add_columns("Key", "Action", "Description")
        
        shortcuts = [
            ("F", "Fetch Symbol", "Open symbol search screen"),
            ("W", "Watchlists", "View your watchlists"),
            ("C", "Create Watchlist", "Create a new watchlist"),
            ("H", "Help", "Show this help screen"),
            ("↑ / ↓", "Navigate", "Move between menu options"),
            ("Enter", "Select", "Open selected menu option"),
            ("Q / Escape", "Quit", "Exit the application"),
        ]
        
        for key, action, desc in shortcuts:
            table.add_row(key, action, desc)
    
    def _populate_fetch_symbol_shortcuts(self) -> None:
        """Populate fetch symbol shortcuts table."""
        table = self.query_one("#fetch-symbol-table", DataTable)
        table.add_columns("Key", "Action", "Description")
        
        shortcuts = [
            ("Type", "Search", "Start typing to search (2+ characters)"),
            ("↓", "Move Down", "Move from input to search results"),
            ("↑", "Move Up", "Move from results back to input"),
            ("Enter", "Select Symbol", "Select symbol from results and view details"),
            ("Mouse Click", "Focus/Select", "Click input to type or click result to select"),
            ("Q / Escape", "Go Back", "Return to main menu"),
        ]
        
        for key, action, desc in shortcuts:
            table.add_row(key, action, desc)
    
    def _populate_create_watchlist_shortcuts(self) -> None:
        """Populate create watchlist shortcuts table."""
        table = self.query_one("#create-watchlist-table", DataTable)
        table.add_columns("Key", "Action", "Description")
        
        shortcuts = [
            ("Type", "Search", "Search for symbols to add"),
            ("↑ / ↓", "Navigate", "Move between name, search, results, table, buttons"),
            ("Enter", "Add Symbol", "Add selected symbol to watchlist"),
            ("Ctrl+S", "Save", "Save the watchlist"),
            ("Tab", "Next Field", "Move to next input field"),
            ("Mouse Click", "Focus/Select", "Click to focus inputs or select items"),
            ("Q / Escape", "Go Back", "Return to main menu (Q disabled in inputs)"),
        ]
        
        for key, action, desc in shortcuts:
            table.add_row(key, action, desc)
    
    def _populate_watchlist_view_shortcuts(self) -> None:
        """Populate watchlist view shortcuts table."""
        table = self.query_one("#watchlist-view-table", DataTable)
        table.add_columns("Key", "Action", "Description")
        
        shortcuts = [
            ("↑ / ↓", "Navigate", "Move through watchlists or symbols"),
            ("Enter", "View/Select", "View watchlist symbols or symbol details"),
            ("Q / Escape", "Go Back", "Return to list view or main menu"),
            ("Mouse Click", "Select", "Click to select watchlist or symbol"),
        ]
        
        for key, action, desc in shortcuts:
            table.add_row(key, action, desc)
    
    def _populate_symbol_detail_shortcuts(self) -> None:
        """Populate symbol detail shortcuts table."""
        table = self.query_one("#symbol-detail-table", DataTable)
        table.add_columns("Key", "Action", "Description")
        
        shortcuts = [
            ("↑ / ↓", "Scroll", "Scroll through symbol data"),
            ("A", "Add to Watchlist", "Add this symbol to a watchlist"),
            ("Q / Escape", "Go Back", "Return to previous screen"),
        ]
        
        for key, action, desc in shortcuts:
            table.add_row(key, action, desc)
    
    def action_pop_screen(self) -> None:
        """Go back to previous screen."""
        self.app.pop_screen()
