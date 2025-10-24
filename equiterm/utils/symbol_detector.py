"""
Symbol type detection utilities.
"""

import re
from typing import Optional, Tuple
from jugaad_data.nse import NSELive

from ..models.watchlist import SymbolType


class SymbolDetector:
    """Detects symbol type based on pattern matching and API validation."""
    
    # Common index patterns
    INDEX_PATTERNS = [
        r'^NIFTY',
        r'^SENSEX',
        r'^BANKNIFTY',
        r'^NIFTY.*',
        r'^SENSEX.*',
        r'^BSE.*',
        r'^NSE.*'
    ]
    
    # ETF patterns (common ETF symbols)
    ETF_PATTERNS = [
        r'.*ETF.*',
        r'.*BEES.*',
        r'.*GOLD.*',
        r'.*SILVER.*'
    ]
    
    def __init__(self):
        self.nse = NSELive()
    
    def detect_symbol_type(self, symbol: str) -> Tuple[SymbolType, Optional[str]]:
        """
        Detect symbol type and return scheme code if applicable.
        
        Args:
            symbol: Symbol name to detect
            
        Returns:
            Tuple of (SymbolType, scheme_code)
        """
        symbol_upper = symbol.upper().strip()
        
        # Check for index patterns
        if self._is_index(symbol_upper):
            return SymbolType.INDEX, None
        
        # Check for ETF patterns
        if self._is_etf_pattern(symbol_upper):
            return SymbolType.ETF, None
        
        # Try to validate as equity
        if self._is_valid_equity(symbol_upper):
            return SymbolType.EQUITY, None
        
        # Check if it's a mutual fund scheme code (numeric)
        if self._is_mutual_fund_scheme(symbol_upper):
            return SymbolType.MUTUAL_FUND, symbol_upper
        
        # Default to equity for unknown symbols
        return SymbolType.EQUITY, None
    
    def _is_index(self, symbol: str) -> bool:
        """Check if symbol matches index patterns."""
        for pattern in self.INDEX_PATTERNS:
            if re.match(pattern, symbol, re.IGNORECASE):
                return True
        return False
    
    def _is_etf_pattern(self, symbol: str) -> bool:
        """Check if symbol matches ETF patterns."""
        for pattern in self.ETF_PATTERNS:
            if re.match(pattern, symbol, re.IGNORECASE):
                return True
        return False
    
    def _is_valid_equity(self, symbol: str) -> bool:
        """Validate if symbol is a valid equity symbol."""
        try:
            # Try to fetch quote to validate
            quote = self.nse.stock_quote(symbol)
            return quote is not None and 'lastPrice' in quote
        except Exception:
            return False
    
    def _is_mutual_fund_scheme(self, symbol: str) -> bool:
        """Check if symbol is a mutual fund scheme code (numeric)."""
        return symbol.isdigit() and len(symbol) >= 4
    
    def validate_symbol(self, symbol: str, symbol_type: SymbolType) -> bool:
        """
        Validate if symbol exists for the given type.
        
        Args:
            symbol: Symbol to validate
            symbol_type: Expected symbol type
            
        Returns:
            True if valid, False otherwise
        """
        try:
            if symbol_type == SymbolType.EQUITY:
                quote = self.nse.stock_quote(symbol)
                return quote is not None and 'lastPrice' in quote
            elif symbol_type == SymbolType.INDEX:
                quote = self.nse.index_quote(symbol)
                return quote is not None and 'lastPrice' in quote
            elif symbol_type in [SymbolType.ETF, SymbolType.MUTUAL_FUND]:
                # For ETF/MF, we'll validate when fetching data
                return True
            return False
        except Exception:
            return False


# Global instance
symbol_detector = SymbolDetector()
