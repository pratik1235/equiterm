"""
Fetch symbol information screen.
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Header, Footer, Input, Static
from textual.binding import Binding

from ..utils.symbol_detector import symbol_detector


class FetchSymbolScreen(Screen):
    """Screen for fetching symbol information."""

    BINDINGS = [
        Binding("escape", "pop_screen", "Back"),
        Binding("enter", "fetch_data", "Search", show=False),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="fetch-container"):
            with Vertical(id="input-section"):
                yield Static("Enter Symbol Name:", id="input-label")
                yield Input(placeholder="e.g., RELIANCE, NIFTY50, 120716", id="symbol-input")
                yield Button("🔍 Search", id="fetch-button", variant="primary")
                yield Static("", id="detected-type")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the screen."""
        self.query_one(Input).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes for auto-detection and auto-capitalize."""
        if event.input.id == "symbol-input":
            # Auto-capitalize the input
            if event.value != event.value.upper():
                event.input.value = event.value.upper()
                return
            
            symbol = event.value.strip()
            type_display = self.query_one("#detected-type")
            if symbol:
                symbol_type, scheme_code = symbol_detector.detect_symbol_type(symbol)
                type_display.update(f"Detected Type: {symbol_type.value.upper()}" +
                                  (f" (Scheme: {scheme_code})" if scheme_code else ""))
            else:
                type_display.update("")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle enter key on input to trigger search."""
        if event.input.id == "symbol-input" and event.value.strip():
            self.query_one("#fetch-button").press()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        symbol = self.query_one(Input).value.strip()
        if not symbol:
            return

        if event.button.id == "fetch-button":
            from .symbol_detail import SymbolDetailScreen
            self.app.push_screen(SymbolDetailScreen(symbol=symbol))

    def action_fetch_data(self) -> None:
        """Action to trigger fetching symbol data."""
        if self.query_one(Input).value.strip():
            self.query_one("#fetch-button").press()

    def action_pop_screen(self) -> None:
        """Go back to the main menu."""
        self.app.pop_screen()
