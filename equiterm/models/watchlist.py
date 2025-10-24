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
    """Represents market data for a symbol."""
    symbol: str
    symbol_type: SymbolType
    
    # Price information
    current_price: Optional[float] = None
    open_price: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    previous_close: Optional[float] = None
    change_percent: Optional[float] = None
    
    # Volume information
    volume: Optional[int] = None
    value: Optional[float] = None
    
    # ETF/MF specific
    nav: Optional[float] = None
    premium_discount: Optional[float] = None
    
    # Additional data
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    
    # Metadata
    last_updated: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None
