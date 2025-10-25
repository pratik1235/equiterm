"""
Fetch symbol information screen with autocomplete search.
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Header, Footer, Input, Static, ListItem, ListView
from textual.binding import Binding
from textual import log, events
from textual.events import Click

from ..services.symbol_search import symbol_search_service


class FetchSymbolScreen(Screen):
    """Screen for searching and fetching symbol information with autocomplete."""

    BINDINGS = [
        Binding("escape", "pop_screen", "Back"),
        Binding("q", "pop_screen", "Back"),
        Binding("up", "focus_input", "Focus Input", show=False),
        Binding("down", "focus_results", "Focus Results", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.search_results = []

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="fetch-main-scroll", can_focus=True):
            with Container(id="fetch-container"):
                with Vertical(id="input-section"):
                    yield Static("Search Symbol or Company Name:", id="input-label")
                    yield Input(
                        placeholder="Type to search (e.g., RELIANCE, NIFTY, Motilal...)",
                        id="symbol-input"
                    )
                with Vertical(id="results-section"):
                    yield ListView(id="results-list")
                    yield Static("", id="search-status")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the screen."""
        input_widget = self.query_one("#symbol-input", Input)
        input_widget.can_focus = True
        input_widget.focus()
        # Hide results initially
        self.query_one("#results-section").display = False

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes for autocomplete search."""
        if event.input.id == "symbol-input":
            query = event.value.strip()
            
            if len(query) >= 2:  # Start searching after 2 characters
                self._perform_search(query)
            else:
                # Hide results if query is too short
                self._clear_results()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle enter key on input."""
        if event.input.id == "symbol-input":
            # If there are results, select the first one
            list_view = self.query_one("#results-list", ListView)
            if list_view.children and len(list_view.children) > 0:
                list_view.focus()
                list_view.index = 0
                self._navigate_to_symbol(self.search_results[0]['symbol'])
    
    def on_key(self, event: events.Key) -> None:
        """Handle key presses for navigation."""
        focused = self.focused
        
        # Prevent 'q' from going back when input is focused
        if isinstance(focused, Input) and event.key == "q":
            return  # Let the input handle it
        
        # Handle down arrow from input field
        if isinstance(focused, Input) and focused.id == "symbol-input":
            if event.key == "down":
                # Move focus to results list if it has items
                list_view = self.query_one("#results-list", ListView)
                if list_view.children and len(list_view.children) > 0:
                    event.prevent_default()
                    list_view.focus()
                    list_view.index = 0
        
        # Handle up arrow from results list
        elif isinstance(focused, ListView) and focused.id == "results-list":
            if event.key == "up":
                # If at the top of the list, move focus back to input
                if focused.index == 0:
                    event.prevent_default()
                    self.query_one(Input).focus()

    def _perform_search(self, query: str) -> None:
        """Perform symbol search and update results."""
        # Search for symbols
        results = symbol_search_service.search_symbols(query, max_results=10)
        self.search_results = results
        
        # Update UI
        self._display_results(results)

    def _display_results(self, results: list) -> None:
        """Display search results in the list view."""
        list_view = self.query_one("#results-list", ListView)
        status = self.query_one("#search-status")
        results_section = self.query_one("#results-section")
        
        # Clear existing items
        list_view.clear()
        
        if results:
            # Show results section
            results_section.display = True
            
            # Add results to list
            for result in results:
                symbol = result['symbol']
                name = result['name']
                
                # Create list item with formatted text
                item_text = f"{symbol:15} | {name}"
                list_item = ListItem(Static(item_text))
                list_view.append(list_item)
            
            status.update(f"Found {len(results)} results. Use ↑↓ to navigate, Enter to select.")
        else:
            # Show "no results" message
            results_section.display = True
            status.update("No results found. Try a different search term.")

    def _clear_results(self) -> None:
        """Clear search results."""
        list_view = self.query_one("#results-list", ListView)
        list_view.clear()
        self.search_results = []
        self.query_one("#results-section").display = False

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle selection from the results list."""
        if event.list_view.id == "results-list":
            # Get the selected index
            index = event.list_view.index
            if 0 <= index < len(self.search_results):
                symbol = self.search_results[index]['symbol']
                self._navigate_to_symbol(symbol)

    def _navigate_to_symbol(self, symbol: str) -> None:
        """Navigate to symbol detail screen."""
        from .symbol_detail import SymbolDetailScreen
        log(f"Navigating to symbol: {symbol}")
        self.app.push_screen(SymbolDetailScreen(symbol=symbol))

    def action_focus_input(self) -> None:
        """Focus back on the input field."""
        self.query_one(Input).focus()
    
    def action_focus_results(self) -> None:
        """Focus on the results list."""
        list_view = self.query_one("#results-list", ListView)
        if list_view.children and len(list_view.children) > 0:
            list_view.focus()
            if list_view.index is None or list_view.index < 0:
                list_view.index = 0

    def on_click(self, event: Click) -> None:
        """Handle mouse clicks to focus widgets."""
        # Get the widget that was clicked
        widget = self.get_widget_at(event.x, event.y)[0]
        
        # If it's an Input widget, focus it
        if isinstance(widget, Input):
            widget.focus()
    
    def action_pop_screen(self) -> None:
        """Go back to the main menu."""
        self.app.pop_screen()
