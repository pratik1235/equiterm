from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Header, Footer, Static, DataTable, LoadingIndicator
from textual.binding import Binding

from ..services.data_fetcher import data_fetcher
from ..utils.symbol_detector import symbol_detector
from ..utils.calculations import format_currency, format_percentage, get_color_for_change
from ..models.watchlist import SymbolType

class SymbolDetailScreen(Screen):
    BINDINGS = [
        Binding("escape", "pop_screen", "Back"),
    ]

    def __init__(self, symbol: str):
        super().__init__()
        self.symbol = symbol
        self.symbol_type, self.scheme_code = symbol_detector.detect_symbol_type(symbol)
        self.data_table = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="sym-detail-container"):
            with Vertical():
                yield Static(f"Symbol: {self.symbol}", id="symbol-heading")
                self.data_table = DataTable(id="detail-table")
                yield self.data_table
                yield LoadingIndicator(id="detail-loading")
        yield Footer()

    def on_mount(self) -> None:
        self.data_table.add_columns("Field", "Value")
        self.query_one("#detail-loading").display = True
        self.set_timer(0.1, self.load_symbol_data)  # Defer to ensure render

    def load_symbol_data(self) -> None:
        self.data_table.clear()
        self.query_one("#detail-loading").display = True
        # Try live fetch, fallback to demo data
        data = data_fetcher.fetch_symbol_data(self.symbol, self.symbol_type, self.scheme_code)
        if not data:
            from .fetch_symbol import FetchSymbolScreen
            data = FetchSymbolScreen._create_demo_data(self, self.symbol, self.symbol_type)
        self.query_one("#detail-loading").display = False
        self._display_data(data)

    def _display_data(self, data) -> None:
        table = self.data_table
        table.clear()
        table.add_row("Type", data.symbol_type.value.upper(), style="bold")
        table.add_row("", "", style="bold")
        table.add_row("📊 PRICE INFORMATION", "", style="bold")
        table.add_row("", "", style="bold")
        if data.current_price is not None:
            table.add_row("Current Price", format_currency(data.current_price))
        if data.open_price is not None:
            table.add_row("Open Price", format_currency(data.open_price))
        if data.high_price is not None:
            table.add_row("Day High", format_currency(data.high_price))
        if data.low_price is not None:
            table.add_row("Day Low", format_currency(data.low_price))
        if data.previous_close is not None:
            table.add_row("Previous Close", format_currency(data.previous_close))
        if data.change_percent is not None:
            change_color = get_color_for_change(data.change_percent)
            table.add_row("Change %", format_percentage(data.change_percent), style=change_color)
        if data.volume is not None or data.value is not None:
            table.add_row("", "", style="bold")
            table.add_row("📈 VOLUME & LIQUIDITY", "", style="bold")
            table.add_row("", "", style="bold")
            if data.volume is not None:
                table.add_row("Volume", f"{data.volume:,}")
            if data.value is not None:
                table.add_row("Value", format_currency(data.value))
        if data.symbol_type in [SymbolType.ETF, SymbolType.MUTUAL_FUND]:
            table.add_row("", "", style="bold")
            table.add_row("💰 ETF/MF INFORMATION", "", style="bold")
            table.add_row("", "", style="bold")
            if data.nav is not None:
                table.add_row("NAV", format_currency(data.nav))
            if data.premium_discount is not None:
                pcol = get_color_for_change(data.premium_discount)
                table.add_row("Premium/Discount", format_percentage(data.premium_discount), style=pcol)
        if data.market_cap is not None or data.pe_ratio is not None or data.dividend_yield is not None:
            table.add_row("", "", style="bold")
            table.add_row("📈 FUNDAMENTALS", "", style="bold")
            table.add_row("", "", style="bold")
            if data.market_cap is not None:
                table.add_row("Market Cap", format_currency(data.market_cap))
            if data.pe_ratio is not None:
                table.add_row("P/E Ratio", f"{data.pe_ratio:.2f}")
            if data.dividend_yield is not None:
                table.add_row("Dividend Yield", format_percentage(data.dividend_yield))

    def action_pop_screen(self) -> None:
        self.app.pop_screen()
