from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Header, Footer, Static, DataTable, LoadingIndicator
from textual.binding import Binding
from textual import log

from ..services.data_fetcher import data_fetcher
from ..services.storage import storage
from ..utils.symbol_detector import symbol_detector
from ..utils.calculations import format_currency, format_percentage
from ..models.watchlist import (
    SymbolType, MarketData, StockData, IndexData, ETFData, MutualFundData
)

class SymbolDetailScreen(Screen):
    BINDINGS = [
        Binding("escape", "pop_screen", "Back"),
        Binding("q", "pop_screen", "Back"),
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
            with VerticalScroll(id="detail-main-scroll", can_focus=True):
                with Vertical():
                    yield Static(f"Symbol: {self.symbol}", id="symbol-heading")
                    self.data_table = DataTable(id="detail-table")
                    yield self.data_table
                    yield LoadingIndicator(id="detail-loading")
                    # Error message container (hidden by default)
                    with Container(id="error-message-container"):
                        with Vertical(id="error-content"):
                            yield Static("⚠️", id="error-icon")
                            yield Static("No data found for this symbol", id="error-text")
                            yield Static(f"Symbol: {self.symbol}", id="error-symbol")
                            yield Static("Please check the symbol name and try again.", id="error-hint")
                    with Horizontal(id="detail-button-row"):
                        yield Button("Add to Watchlist", id="add-watchlist-button", variant="primary")
        yield Footer()

    def on_mount(self) -> None:
        self.data_table.add_columns("Field", "Value")
        self.query_one("#detail-loading").display = True
        self.query_one("#error-message-container").display = False  # Hide error by default
        self._update_watchlist_button()
        self.set_timer(0.1, self.load_symbol_data)  # Defer to ensure render
        
        # Auto-focus the scroll container
        self.call_after_refresh(self._focus_scroll)
    
    def _focus_scroll(self) -> None:
        """Focus the scroll container."""
        try:
            scroll = self.query_one("#detail-main-scroll")
            scroll.focus()
        except Exception:
            pass

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

    def _display_data(self, data: MarketData) -> None:
        """Route to appropriate display method based on data type."""
        if data is None:
            self._display_no_data_message()
            return
        
        if isinstance(data, StockData):
            self._display_stock_data(data)
        elif isinstance(data, IndexData):
            self._display_index_data(data)
        elif isinstance(data, ETFData):
            self._display_etf_data(data)
        elif isinstance(data, MutualFundData):
            self._display_mutual_fund_data(data)
        else:
            # Fallback for base MarketData
            self._display_generic_data(data)
    
    def _display_no_data_message(self) -> None:
        """Display a centered modal-like message when no data is found."""
        # Hide the data table and button row
        self.data_table.display = False
        self.query_one("#detail-button-row").display = False
        
        # Show error message container
        error_container = self.query_one("#error-message-container")
        error_container.display = True
    
    def _display_stock_data(self, data: StockData) -> None:
        """Display stock-specific data."""
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
    
    def _display_index_data(self, data: IndexData) -> None:
        """Display index-specific data."""
        table = self.data_table
        table.clear()
        
        # Index Information
        if data.index_name:
            table.add_row("Index Name", data.index_name)
        table.add_row("Symbol", data.symbol)
        table.add_row("Type", data.symbol_type.value.upper())
        
        # Market Status
        if data.market_status:
            table.add_row("Market Status", data.market_status)
        if data.market_status_message:
            table.add_row("Status Message", data.market_status_message)
        
        # Price Information
        table.add_row("", "")
        table.add_row("📊 PRICE INFORMATION", "")
        table.add_row("", "")
        if data.current_price is not None:
            table.add_row("Current Level", format_currency(data.current_price))
        if data.open_price is not None:
            table.add_row("Open", format_currency(data.open_price))
        if data.high_price is not None:
            table.add_row("Day High", format_currency(data.high_price))
        if data.low_price is not None:
            table.add_row("Day Low", format_currency(data.low_price))
        if data.previous_close is not None:
            table.add_row("Previous Close", format_currency(data.previous_close))
        if data.change is not None:
            table.add_row("Change", format_currency(data.change))
        if data.change_percent is not None:
            table.add_row("Change %", format_percentage(data.change_percent))
        
        # Year Range
        if data.year_high or data.year_low:
            table.add_row("", "")
            table.add_row("📉 YEAR RANGE", "")
            table.add_row("", "")
            if data.year_high is not None:
                table.add_row("Year High", format_currency(data.year_high))
            if data.year_low is not None:
                table.add_row("Year Low", format_currency(data.year_low))
            if data.near_week_high is not None:
                table.add_row("Near Week High", f"{data.near_week_high:.2f}%")
            if data.near_week_low is not None:
                table.add_row("Near Week Low", f"{data.near_week_low:.2f}%")
        
        # Index Composition
        if data.advances is not None or data.declines is not None:
            table.add_row("", "")
            table.add_row("📈 INDEX COMPOSITION", "")
            table.add_row("", "")
            if data.advances is not None:
                table.add_row("Advances", str(data.advances))
            if data.declines is not None:
                table.add_row("Declines", str(data.declines))
            if data.unchanged is not None:
                table.add_row("Unchanged", str(data.unchanged))
        
        # Performance Metrics
        if data.percent_change_365d or data.percent_change_30d:
            table.add_row("", "")
            table.add_row("📊 PERFORMANCE", "")
            table.add_row("", "")
            if data.percent_change_365d is not None:
                table.add_row("1-Year Return", format_percentage(data.percent_change_365d))
            if data.percent_change_30d is not None:
                table.add_row("1-Month Return", format_percentage(data.percent_change_30d))
        
        # Volume & Market Cap
        if data.volume or data.value or data.total_market_cap:
            table.add_row("", "")
            table.add_row("📈 VOLUME & MARKET CAP", "")
            table.add_row("", "")
            if data.volume is not None:
                table.add_row("Total Volume", f"{data.volume:,}")
            if data.value is not None:
                table.add_row("Total Value", format_currency(data.value))
            if data.total_market_cap is not None:
                table.add_row("Free Float Mkt Cap", format_currency(data.total_market_cap))
        
        # Last Updated
        if data.last_updated:
            table.add_row("", "")
            table.add_row("Last Updated", data.last_updated)
    
    def _display_etf_data(self, data: ETFData) -> None:
        """Display ETF-specific data."""
        table = self.data_table
        table.clear()
        
        # ETF Information
        if data.company_name:
            table.add_row("ETF Name", data.company_name)
        table.add_row("Symbol", data.symbol)
        table.add_row("Type", data.symbol_type.value.upper())
        if data.isin:
            table.add_row("ISIN", data.isin)
        if data.industry:
            table.add_row("Industry", data.industry)
        if data.sector:
            table.add_row("Sector", data.sector)
        if data.underlying_index:
            table.add_row("Underlying Index", data.underlying_index)
        if data.listing_date:
            table.add_row("Listing Date", data.listing_date)
        
        # Price Information
        table.add_row("", "")
        table.add_row("📊 PRICE INFORMATION", "")
        table.add_row("", "")
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
        
        # NAV & Premium/Discount
        if data.nav or data.premium_discount:
            table.add_row("", "")
            table.add_row("💰 NAV & PREMIUM/DISCOUNT", "")
            table.add_row("", "")
            if data.nav is not None:
                table.add_row("NAV", format_currency(data.nav))
            if data.premium_discount is not None:
                table.add_row("Premium/Discount", format_percentage(data.premium_discount))
        
        # Circuit Limits & Range
        if data.lower_circuit or data.upper_circuit or data.week_high or data.week_low:
            table.add_row("", "")
            table.add_row("📉 LIMITS & RANGE", "")
            table.add_row("", "")
            if data.lower_circuit is not None:
                table.add_row("Lower Circuit", format_currency(data.lower_circuit))
            if data.upper_circuit is not None:
                table.add_row("Upper Circuit", format_currency(data.upper_circuit))
            if data.price_band_percent:
                table.add_row("Price Band", f"{data.price_band_percent}%")
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
        if data.volume or data.value or data.total_buy_quantity or data.total_sell_quantity:
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
        
        # ETF Details
        if data.face_value or data.issued_size or data.tick_size:
            table.add_row("", "")
            table.add_row("📊 ETF DETAILS", "")
            table.add_row("", "")
            if data.face_value is not None:
                table.add_row("Face Value", format_currency(data.face_value))
            if data.issued_size is not None:
                table.add_row("Issued Size", f"{data.issued_size:,} units")
            if data.tick_size is not None:
                table.add_row("Tick Size", format_currency(data.tick_size))
        
        # Trading Information
        if data.is_fno is not None or data.is_slb is not None:
            table.add_row("", "")
            table.add_row("🔄 TRADING INFO", "")
            table.add_row("", "")
            if data.is_fno is not None:
                table.add_row("F&O Available", "Yes" if data.is_fno else "No")
            if data.is_slb is not None:
                table.add_row("SLB Available", "Yes" if data.is_slb else "No")
            if data.is_etf_sec is not None:
                table.add_row("ETF Security", "Yes" if data.is_etf_sec else "No")
        
        # Last Updated
        if data.last_updated:
            table.add_row("", "")
            table.add_row("Last Updated", data.last_updated)
    
    def _display_mutual_fund_data(self, data: MutualFundData) -> None:
        """Display mutual fund-specific data."""
        table = self.data_table
        table.clear()
        
        # Fund Information
        if data.scheme_name:
            table.add_row("Scheme Name", data.scheme_name)
        table.add_row("Scheme Code", data.symbol)
        table.add_row("Type", data.symbol_type.value.upper())
        if data.fund_house:
            table.add_row("Fund House", data.fund_house)
        if data.scheme_type:
            table.add_row("Scheme Type", data.scheme_type)
        if data.scheme_category:
            table.add_row("Category", data.scheme_category)
        
        # NAV Information
        table.add_row("", "")
        table.add_row("💰 NAV INFORMATION", "")
        table.add_row("", "")
        if data.nav is not None:
            table.add_row("Current NAV", format_currency(data.nav))
        
        # Performance
        if data.returns_1y or data.returns_3y or data.returns_5y:
            table.add_row("", "")
            table.add_row("📊 RETURNS", "")
            table.add_row("", "")
            if data.returns_1y is not None:
                table.add_row("1-Year Return", format_percentage(data.returns_1y))
            if data.returns_3y is not None:
                table.add_row("3-Year Return", format_percentage(data.returns_3y))
            if data.returns_5y is not None:
                table.add_row("5-Year Return", format_percentage(data.returns_5y))
        
        # Fund Details
        if data.aum or data.expense_ratio:
            table.add_row("", "")
            table.add_row("📈 FUND DETAILS", "")
            table.add_row("", "")
            if data.aum is not None:
                table.add_row("AUM", format_currency(data.aum))
            if data.expense_ratio is not None:
                table.add_row("Expense Ratio", f"{data.expense_ratio:.2f}%")
        
        # Last Updated
        if data.last_updated:
            table.add_row("", "")
            table.add_row("Last Updated", data.last_updated)
    
    def _display_generic_data(self, data: MarketData) -> None:
        """Display generic market data (fallback)."""
        table = self.data_table
        table.clear()
        
        # Basic Information
        table.add_row("Symbol", data.symbol)
        table.add_row("Type", data.symbol_type.value.upper())
        
        # Price Information
        if data.current_price or data.open_price or data.high_price or data.low_price:
            table.add_row("", "")
            table.add_row("📊 PRICE INFORMATION", "")
            table.add_row("", "")
            if data.current_price is not None:
                table.add_row("Current Price", format_currency(data.current_price))
            if data.open_price is not None:
                table.add_row("Open Price", format_currency(data.open_price))
            if data.high_price is not None:
                table.add_row("High", format_currency(data.high_price))
            if data.low_price is not None:
                table.add_row("Low", format_currency(data.low_price))
            if data.previous_close is not None:
                table.add_row("Previous Close", format_currency(data.previous_close))
            if data.change is not None:
                table.add_row("Change", format_currency(data.change))
            if data.change_percent is not None:
                table.add_row("Change %", format_percentage(data.change_percent))
        
        # Volume
        if data.volume or data.value:
            table.add_row("", "")
            table.add_row("📈 VOLUME", "")
            table.add_row("", "")
            if data.volume is not None:
                table.add_row("Volume", f"{data.volume:,}")
            if data.value is not None:
                table.add_row("Value", format_currency(data.value))
        
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
