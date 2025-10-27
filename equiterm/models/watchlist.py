"""
Data models for watchlists and symbols.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class SymbolType(Enum):
    """Symbol type enumeration."""
    EQUITY = "equity"
    INDEX = "index"
    ETF = "etf"
    MUTUAL_FUND = "mutual_fund"


@dataclass
class Symbol:
    """Represents a financial symbol (stock, ETF, mutual fund, etc.)."""
    name: str
    symbol_type: SymbolType
    full_name: Optional[str] = None  # Company name for equity, ETF name for ETF, etc.
    scheme_code: Optional[str] = None  # For ETFs and mutual funds
    mfapi_url: Optional[str] = None   # Constructed URL for MFAPI
    
    def __post_init__(self):
        """Construct MFAPI URL if scheme code is provided."""
        if self.scheme_code and not self.mfapi_url:
            self.mfapi_url = f"https://api.mfapi.in/mf/{self.scheme_code}"


@dataclass
class Watchlist:
    """Represents a watchlist containing multiple symbols."""
    name: str
    symbols: List[Symbol] = field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    is_favorite: bool = False  # Only one watchlist can be favorite at a time
    
    def add_symbol(self, symbol: Symbol) -> None:
        """Add a symbol to the watchlist."""
        if symbol not in self.symbols:
            self.symbols.append(symbol)
    
    def remove_symbol(self, symbol_name: str) -> bool:
        """Remove a symbol from the watchlist by name."""
        for i, symbol in enumerate(self.symbols):
            if symbol.name == symbol_name:
                del self.symbols[i]
                return True
        return False
    
    def get_symbol(self, symbol_name: str) -> Optional[Symbol]:
        """Get a symbol by name."""
        for symbol in self.symbols:
            if symbol.name == symbol_name:
                return symbol
        return None


@dataclass
class MarketData:
    """Base class for market data - represents common fields across all asset types."""
    symbol: str
    symbol_type: SymbolType
    
    # Price information (common to all)
    current_price: Optional[float] = None
    open_price: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    previous_close: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    
    # Volume information (common to most)
    volume: Optional[int] = None
    value: Optional[float] = None
    
    # Metadata
    last_updated: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None


@dataclass
class StockData(MarketData):
    """Represents equity/stock market data with company-specific information."""
    
    # Price details
    close_price: Optional[float] = None
    vwap: Optional[float] = None  # Volume Weighted Average Price
    
    # Price bands and limits
    lower_circuit: Optional[float] = None
    upper_circuit: Optional[float] = None
    week_high: Optional[float] = None
    week_low: Optional[float] = None
    week_high_date: Optional[str] = None
    week_low_date: Optional[str] = None
    
    # Volume details
    total_buy_quantity: Optional[int] = None
    total_sell_quantity: Optional[int] = None
    
    # Company information
    company_name: Optional[str] = None
    industry: Optional[str] = None
    sector: Optional[str] = None
    isin: Optional[str] = None
    
    # Fundamental data
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    face_value: Optional[float] = None
    issued_size: Optional[int] = None
    
    # Trading information
    is_fno: Optional[bool] = None  # Futures & Options available
    is_slb: Optional[bool] = None  # Securities Lending & Borrowing


@dataclass
class IndexData(MarketData):
    """Represents index market data with index-specific metrics."""
    
    # Index-specific price information
    year_high: Optional[float] = None
    year_low: Optional[float] = None
    
    # Index composition
    advances: Optional[int] = None  # Number of advancing stocks
    declines: Optional[int] = None  # Number of declining stocks
    unchanged: Optional[int] = None  # Number of unchanged stocks
    
    # Performance metrics
    percent_change_365d: Optional[float] = None  # 1-year performance
    percent_change_30d: Optional[float] = None   # 1-month performance
    near_week_high: Optional[float] = None  # Distance from 52-week high (%)
    near_week_low: Optional[float] = None   # Distance from 52-week low (%)
    
    # Market status
    market_status: Optional[str] = None
    market_status_message: Optional[str] = None
    
    # Index metadata
    index_name: Optional[str] = None
    total_market_cap: Optional[float] = None  # FFMC - Free Float Market Cap


@dataclass
class ETFData(MarketData):
    """Represents ETF market data combining stock and fund characteristics."""
    
    # Stock-like characteristics
    close_price: Optional[float] = None
    vwap: Optional[float] = None
    lower_circuit: Optional[float] = None
    upper_circuit: Optional[float] = None
    week_high: Optional[float] = None
    week_low: Optional[float] = None
    week_high_date: Optional[str] = None
    week_low_date: Optional[str] = None
    
    # Fund characteristics
    nav: Optional[float] = None  # Net Asset Value (iNavValue)
    premium_discount: Optional[float] = None  # Premium/Discount to NAV
    
    # ETF information
    company_name: Optional[str] = None
    isin: Optional[str] = None
    underlying_index: Optional[str] = None  # Index being tracked
    industry: Optional[str] = None
    sector: Optional[str] = None
    
    # Trading information
    is_fno: Optional[bool] = None  # Futures & Options available
    is_slb: Optional[bool] = None  # Securities Lending & Borrowing
    total_buy_quantity: Optional[int] = None
    total_sell_quantity: Optional[int] = None
    
    # ETF-specific details
    face_value: Optional[float] = None
    issued_size: Optional[int] = None  # Total units issued
    listing_date: Optional[str] = None
    is_etf_sec: Optional[bool] = None  # Confirms it's an ETF
    
    # Price band information
    price_band_percent: Optional[str] = None  # e.g., "20" for 20% band
    tick_size: Optional[float] = None  # Minimum price movement


@dataclass
class MutualFundData(MarketData):
    """Represents mutual fund data from MFAPI."""
    
    # Fund-specific information
    nav: Optional[float] = None  # Net Asset Value
    scheme_name: Optional[str] = None
    fund_house: Optional[str] = None
    scheme_type: Optional[str] = None  # Equity, Debt, Hybrid, etc.
    scheme_category: Optional[str] = None
    
    # Performance (if available from extended API)
    returns_1y: Optional[float] = None
    returns_3y: Optional[float] = None
    returns_5y: Optional[float] = None
    
    # Fund details
    aum: Optional[float] = None  # Assets Under Management
    expense_ratio: Optional[float] = None
