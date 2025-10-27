from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal, VerticalScroll, ScrollableContainer
from textual.screen import Screen
from textual.widgets import Button, Header, Footer, Static, DataTable, LoadingIndicator
from textual.binding import Binding
from textual import log, events
from rich.text import Text
from datetime import date, timedelta
import plotext as plt

from ..services.data_fetcher import data_fetcher
from ..services.storage import storage
from ..utils.symbol_detector import symbol_detector
from ..utils.calculations import format_currency, format_percentage
from ..models.watchlist import (
    SymbolType, MarketData, StockData, IndexData, ETFData, MutualFundData
)

try:
    from jugaad_data.nse import stock_df, index_df
except ImportError:
    stock_df = None
    index_df = None

class SymbolDetailScreen(Screen):
    BINDINGS = [
        Binding("escape", "pop_screen", "Back"),
        Binding("q", "pop_screen", "Back"),
        Binding("a", "add_to_watchlist", "Add to Watchlist"),
        Binding("down", "focus_next", "Next", show=False),
        Binding("up", "focus_previous", "Previous", show=False),
    ]

    def __init__(self, symbol: str):
        super().__init__()
        self.symbol = symbol
        self.symbol_type, self.scheme_code = symbol_detector.detect_symbol_type(symbol)
        self.data_table = None
        self.graph_widget = None
        self.historical_data = None
        self.current_data = None  # Store current MarketData for full_name extraction

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="detail-main-scroll", can_focus=False):
            yield Static(f"Symbol: {self.symbol}", id="symbol-heading")
            with Horizontal(id="detail-content-row"):
                # Left side: Data table
                with Vertical(id="detail-left-panel"):
                    self.data_table = DataTable(id="detail-table")
                    yield self.data_table
                    yield LoadingIndicator(id="detail-loading")
                # Right side: Graph
                with Vertical(id="detail-right-panel"):
                    self.graph_widget = Static("", id="price-graph")
                    yield self.graph_widget
                    yield Static("Loading historical data...", id="graph-status")
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
        self.data_table.cursor_type = "row"
        self.query_one("#detail-loading").display = True
        self.query_one("#error-message-container").display = False  # Hide error by default
        self._update_watchlist_button()
        self.set_timer(0.1, self.load_symbol_data)  # Defer to ensure render
        self.set_timer(0.2, self.load_historical_data)  # Load historical data
        
        # Auto-focus the data table
        self.call_after_refresh(self._focus_table)
    
    def _focus_table(self) -> None:
        """Focus the data table."""
        try:
            self.data_table.focus()
        except Exception:
            pass
    
    def on_key(self, event: events.Key) -> None:
        """Handle key events for seamless navigation."""
        focused = self.focused
        
        if event.key == "down":
            if focused == self.data_table:
                # Check if we're at the last row of the table
                if self.data_table.row_count > 0:
                    cursor_row = self.data_table.cursor_row
                    if cursor_row == self.data_table.row_count - 1:
                        # At last row, move to button
                        event.prevent_default()
                        event.stop()
                        try:
                            button = self.query_one("#add-watchlist-button", Button)
                            if not button.disabled:
                                button.focus()
                                button.scroll_visible()
                        except Exception:
                            pass
        
        elif event.key == "up":
            if focused == self.query_one("#add-watchlist-button", Button):
                # Move from button back to table
                event.prevent_default()
                event.stop()
                self.data_table.focus()
                self.data_table.scroll_visible()
    
    def action_focus_next(self) -> None:
        """Move focus to next element."""
        self.screen.focus_next()
    
    def action_focus_previous(self) -> None:
        """Move focus to previous element."""
        self.screen.focus_previous()

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
    
    def load_historical_data(self) -> None:
        """Load and display historical data for the last 30 days."""
        try:
            if stock_df is None or index_df is None:
                self.query_one("#graph-status").update("jugaad_data not available")
                return
            
            # Calculate date range (last 30 days)
            to_date = date.today()
            from_date = to_date - timedelta(days=30)
            
            # Fetch historical data based on symbol type
            df = None
            if self.symbol_type in [SymbolType.EQUITY, SymbolType.ETF]:
                try:
                    df = stock_df(
                        symbol=self.symbol,
                        from_date=from_date,
                        to_date=to_date,
                        series="EQ"
                    )
                except Exception as e:
                    log(f"Error fetching stock data for {self.symbol}: {e}")
                    self.query_one("#graph-status").update(f"Error: {str(e)[:50]}")
                    return
            elif self.symbol_type == SymbolType.INDEX:
                try:
                    df = index_df(
                        symbol=self.symbol,
                        from_date=from_date,
                        to_date=to_date
                    )
                except Exception as e:
                    log(f"Error fetching index data for {self.symbol}: {e}")
                    self.query_one("#graph-status").update(f"Error: {str(e)[:50]}")
                    return
            else:
                self.query_one("#graph-status").update("Historical data not available for this type")
                return
            
            if df is None or df.empty:
                self.query_one("#graph-status").update("No historical data available")
                return
            
            self.historical_data = df
            self._plot_historical_data()
            
        except Exception as e:
            log(f"Error loading historical data: {e}")
            self.query_one("#graph-status").update(f"Error: {str(e)[:50]}")
    
    def _plot_historical_data(self) -> None:
        """Plot historical price data using plotext."""
        try:
            if self.historical_data is None or self.historical_data.empty:
                return
            
            df = self.historical_data
            
            # Clear previous plot
            plt.clear_figure()
            plt.clear_data()
            plt.clear_color()
            
            # Extract dates and close prices
            dates = []
            if 'DATE' in df.columns:
                dates = df['DATE'].tolist()
            elif 'HistoricalDate' in df.columns:
                dates = df['HistoricalDate'].tolist()
            else:
                dates = list(range(len(df)))
            
            if 'CLOSE' in df.columns:
                close_prices = df['CLOSE'].tolist()
            elif 'close' in df.columns:
                close_prices = df['close'].tolist()
            else:
                self.query_one("#graph-status").update("Close price column not found")
                return
            
            # Convert dates to "DD Mon" format
            date_labels = []
            for d in dates:
                if isinstance(d, str):
                    # Parse string date and format as "DD Mon"
                    try:
                        from datetime import datetime
                        parsed_date = datetime.strptime(d[:10], "%Y-%m-%d")
                        date_labels.append(parsed_date.strftime("%d %b"))
                    except:
                        date_labels.append(d[:5])  # Fallback to first 5 chars
                else:
                    date_labels.append(str(d))
            
            # Create the plot with date labels on x-axis
            x_indices = list(range(len(close_prices)))
            plt.plot(x_indices, close_prices, marker="braille")
            plt.title(f"{self.symbol} - 30 Day Price Chart")
            plt.xlabel("Date")
            plt.ylabel("Close Price (Rs)")
            
            # Set custom x-axis labels (show every 5th date to avoid clutter)
            if len(date_labels) > 10:
                step = len(date_labels) // 10
                xticks = list(range(0, len(date_labels), step))
                xlabels = [date_labels[i] for i in xticks]
                plt.xticks(xticks, xlabels)
            else:
                plt.xticks(x_indices, date_labels)
            
            # Set plot size to fit the right panel (approximately)
            plt.plot_size(width=70, height=25)
            
            # Generate the plot as text
            plot_text = plt.build()
            
            # Update the graph widget
            self.graph_widget.update(plot_text)
            self.query_one("#graph-status").update(f"Data points: {len(close_prices)}")
            
        except Exception as e:
            log(f"Error plotting data: {e}")
            self.query_one("#graph-status").update(f"Plot error: {str(e)[:50]}")

    def _display_data(self, data: MarketData) -> None:
        """Route to appropriate display method based on data type."""
        if data is None:
            self._display_no_data_message()
            return
        
        # Store current data for later use (e.g., adding to watchlist)
        self.current_data = data
        
        if isinstance(data, StockData):
            self._display_stock_data(data)
        elif isinstance(data, IndexData):
            self._display_index_data(data)
        elif isinstance(data, ETFData):
            self.symbol_type = SymbolType.ETF
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
        
        # Close Price with color highlighting
        if data.close_price is not None:
            close_value = format_currency(data.close_price)
            # Color highlight based on comparison with previous close
            if data.previous_close is not None:
                if data.close_price > data.previous_close:
                    close_text = Text(close_value, style="bold green")
                elif data.close_price < data.previous_close:
                    close_text = Text(close_value, style="bold red")
                else:
                    close_text = close_value  # No highlight when equal
            else:
                close_text = close_value  # No highlight if no previous close
            table.add_row("Close Price", close_text)
        
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
            # Current Level with color highlighting for Index
            current_value = format_currency(data.current_price)
            if data.previous_close is not None:
                if data.current_price > data.previous_close:
                    current_text = Text(current_value, style="bold green")
                elif data.current_price < data.previous_close:
                    current_text = Text(current_value, style="bold red")
                else:
                    current_text = current_value
            else:
                current_text = current_value
            table.add_row("Current Level", current_text)
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
        
        # Close Price with color highlighting for ETF
        if data.close_price is not None:
            close_value = format_currency(data.close_price)
            # Color highlight based on comparison with previous close
            if data.previous_close is not None:
                if data.close_price > data.previous_close:
                    close_text = Text(close_value, style="bold green")
                elif data.close_price < data.previous_close:
                    close_text = Text(close_value, style="bold red")
                else:
                    close_text = close_value  # No highlight when equal
            else:
                close_text = close_value  # No highlight if no previous close
            table.add_row("Close Price", close_text)
        
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
            from .add_to_watchlist import AddToWatchlistScreen
            
            # Extract full_name from current data
            full_name = None
            if self.current_data:
                if isinstance(self.current_data, StockData):
                    full_name = self.current_data.company_name
                elif isinstance(self.current_data, ETFData):
                    full_name = self.current_data.company_name
                elif isinstance(self.current_data, IndexData):
                    full_name = self.current_data.index_name
                elif isinstance(self.current_data, MutualFundData):
                    full_name = self.current_data.scheme_name
            
            self.app.push_screen(
                AddToWatchlistScreen(
                    symbol=self.symbol,
                    symbol_type=self.symbol_type,
                    full_name=full_name
                )
            )

    def action_add_to_watchlist(self) -> None:
        """Action to trigger adding a symbol to a watchlist."""
        self.query_one("#add-watchlist-button").press()

    def action_pop_screen(self) -> None:
        self.app.pop_screen()
