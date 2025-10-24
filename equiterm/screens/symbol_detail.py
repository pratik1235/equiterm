from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.screen import Screen
from textual.widgets import Button, Header, Footer, Static, DataTable, LoadingIndicator
from textual.binding import Binding
from textual import log

from ..services.data_fetcher import data_fetcher
from ..services.storage import storage
from ..utils.symbol_detector import symbol_detector
from ..utils.calculations import format_currency, format_percentage
from ..models.watchlist import SymbolType

class SymbolDetailScreen(Screen):
    BINDINGS = [
        Binding("escape", "pop_screen", "Back"),
        Binding("a", "add_to_watchlist", "Add to Watchlist"),
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
                with Horizontal(id="detail-button-row"):
                    yield Button("Add to Watchlist", id="add-watchlist-button", variant="primary")
        yield Footer()

    def on_mount(self) -> None:
        self.data_table.add_columns("Field", "Value")
        self.query_one("#detail-loading").display = True
        self._update_watchlist_button()
        self.set_timer(0.1, self.load_symbol_data)  # Defer to ensure render

    def _update_watchlist_button(self) -> None:
        """Disable 'Add to Watchlist' button if no watchlists exist."""
        watchlist_button = self.query_one("#add-watchlist-button")
        has_watchlists = bool(storage.list_watchlist_names())
        watchlist_button.disabled = not has_watchlists

    def load_symbol_data(self) -> None:
        self.data_table.clear()
        self.query_one("#detail-loading").display = True
        # Try live fetch, fallback to demo data
        data = data_fetcher.fetch_symbol_data(self.symbol, self.symbol_type, self.scheme_code)
        log(
            f"PRATIK: Symbol: {self.symbol}, "
            f"Symbol Type: {self.symbol_type}, "
            f"Scheme Code: {self.scheme_code}, "
            f"Data: {data}"
        )
        self.query_one("#detail-loading").display = False
        self._display_data(data)

    def _display_data(self, data) -> None:
        table = self.data_table
        table.clear()
        
        # Company Information
        if data.company_name:
            table.add_row("Company", data.company_name)
        table.add_row("Symbol", data.symbol)
        table.add_row("Type", data.symbol_type.value.upper())
        if data.industry:
            table.add_row("Industry", data.industry)
        if data.sector:
            table.add_row("Sector", data.sector)
        if data.isin:
            table.add_row("ISIN", data.isin)
        
        # Price Information
        table.add_row("", "")
        table.add_row("📊 PRICE INFORMATION", "")
        table.add_row("", "")
        log(f"PRATIK: Data: {data}")
        if data.current_price is not None:
            table.add_row("Current Price", format_currency(data.current_price))
        if data.open_price is not None:
            table.add_row("Open Price", format_currency(data.open_price))
        if data.close_price is not None:
            table.add_row("Close Price", format_currency(data.close_price))
        if data.high_price is not None:
            table.add_row("Day High", format_currency(data.high_price))
        if data.low_price is not None:
            table.add_row("Day Low", format_currency(data.low_price))
        if data.previous_close is not None:
            table.add_row("Previous Close", format_currency(data.previous_close))
        if data.vwap is not None:
            table.add_row("VWAP", format_currency(data.vwap))
        if data.change is not None:
            table.add_row("Change", format_currency(data.change))
        if data.change_percent is not None:
            table.add_row("Change %", format_percentage(data.change_percent))
        
        # Circuit Limits & 52-Week Range
        if data.lower_circuit or data.upper_circuit or data.week_high or data.week_low:
            table.add_row("", "")
            table.add_row("📉 LIMITS & RANGE", "")
            table.add_row("", "")
            if data.lower_circuit is not None:
                table.add_row("Lower Circuit", format_currency(data.lower_circuit))
            if data.upper_circuit is not None:
                table.add_row("Upper Circuit", format_currency(data.upper_circuit))
            if data.week_high is not None:
                week_high_str = format_currency(data.week_high)
                if data.week_high_date:
                    week_high_str += f" ({data.week_high_date})"
                table.add_row("52-Week High", week_high_str)
            if data.week_low is not None:
                week_low_str = format_currency(data.week_low)
                if data.week_low_date:
                    week_low_str += f" ({data.week_low_date})"
                table.add_row("52-Week Low", week_low_str)
        
        # Volume & Liquidity
        if data.volume is not None or data.value is not None or data.total_buy_quantity or data.total_sell_quantity:
            table.add_row("", "")
            table.add_row("📈 VOLUME & LIQUIDITY", "")
            table.add_row("", "")
            if data.volume is not None:
                table.add_row("Volume", f"{data.volume:,}")
            if data.value is not None:
                table.add_row("Value", format_currency(data.value))
            if data.total_buy_quantity is not None:
                table.add_row("Total Buy Qty", f"{data.total_buy_quantity:,}")
            if data.total_sell_quantity is not None:
                table.add_row("Total Sell Qty", f"{data.total_sell_quantity:,}")
        
        # ETF/MF Information
        if data.symbol_type in [SymbolType.ETF, SymbolType.MUTUAL_FUND]:
            table.add_row("", "")
            table.add_row("💰 ETF/MF INFORMATION", "")
            table.add_row("", "")
            if data.nav is not None:
                table.add_row("NAV", format_currency(data.nav))
            if data.premium_discount is not None:
                table.add_row("Premium/Discount", format_percentage(data.premium_discount))
        
        # Fundamentals
        if data.market_cap or data.pe_ratio or data.dividend_yield or data.face_value or data.issued_size:
            table.add_row("", "")
            table.add_row("📊 FUNDAMENTALS", "")
            table.add_row("", "")
            if data.market_cap is not None:
                table.add_row("Market Cap", format_currency(data.market_cap))
            if data.pe_ratio is not None:
                table.add_row("P/E Ratio", f"{data.pe_ratio:.2f}")
            if data.dividend_yield is not None:
                table.add_row("Dividend Yield", format_percentage(data.dividend_yield))
            if data.face_value is not None:
                table.add_row("Face Value", format_currency(data.face_value))
            if data.issued_size is not None:
                table.add_row("Issued Size", f"{data.issued_size:,}")
        
        # Trading Information
        if data.is_fno is not None or data.is_slb is not None:
            table.add_row("", "")
            table.add_row("🔄 TRADING INFO", "")
            table.add_row("", "")
            if data.is_fno is not None:
                table.add_row("F&O Available", "Yes" if data.is_fno else "No")
            if data.is_slb is not None:
                table.add_row("SLB Available", "Yes" if data.is_slb else "No")
        
        # Last Updated
        if data.last_updated:
            table.add_row("", "")
            table.add_row("Last Updated", data.last_updated)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "add-watchlist-button":
            from .select_watchlist import SelectWatchlistScreen
            self.app.push_screen(SelectWatchlistScreen(symbol=self.symbol))

    def action_add_to_watchlist(self) -> None:
        """Action to trigger adding a symbol to a watchlist."""
        self.query_one("#add-watchlist-button").press()

    def action_pop_screen(self) -> None:
        self.app.pop_screen()
