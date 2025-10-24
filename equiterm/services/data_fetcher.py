"""
Data fetching service using jugaad-data and MFAPI.
"""

import requests
from typing import Optional, Dict, Any
from datetime import datetime

from jugaad_data.nse import NSELive

from ..models.watchlist import MarketData, SymbolType
from ..utils.calculations import calculate_etf_premium, calculate_change_percent


class DataFetcher:
    """Service for fetching market data from various sources."""
    
    def __init__(self):
        self.nse = NSELive()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Equiterm/0.1.0'
        })
    
    def fetch_equity_data(self, symbol: str) -> Optional[MarketData]:
        """Fetch equity data using jugaad-data."""
        try:
            quote = self.nse.stock_quote(symbol)
            if not quote or 'lastPrice' not in quote:
                return None
            
            return MarketData(
                symbol=symbol,
                symbol_type=SymbolType.EQUITY,
                current_price=quote.get('lastPrice'),
                open_price=quote.get('open'),
                high_price=quote.get('dayHigh'),
                low_price=quote.get('dayLow'),
                previous_close=quote.get('previousClose'),
                change_percent=quote.get('pChange'),
                volume=quote.get('totalTradedVolume'),
                value=quote.get('totalTradedValue'),
                market_cap=quote.get('marketCap'),
                pe_ratio=quote.get('pe'),
                dividend_yield=quote.get('dividendYield'),
                last_updated=datetime.now().isoformat(),
                raw_data=quote
            )
        except Exception as e:
            # Log error but don't print to avoid cluttering terminal
            return None
    
    def fetch_index_data(self, symbol: str) -> Optional[MarketData]:
        """Fetch index data using jugaad-data."""
        try:
            quote = self.nse.index_quote(symbol)
            if not quote or 'lastPrice' not in quote:
                return None
            
            return MarketData(
                symbol=symbol,
                symbol_type=SymbolType.INDEX,
                current_price=quote.get('lastPrice'),
                open_price=quote.get('open'),
                high_price=quote.get('dayHigh'),
                low_price=quote.get('dayLow'),
                previous_close=quote.get('previousClose'),
                change_percent=quote.get('pChange'),
                volume=quote.get('totalTradedVolume'),
                value=quote.get('totalTradedValue'),
                last_updated=datetime.now().isoformat(),
                raw_data=quote
            )
        except Exception as e:
            return None
    
    def fetch_etf_data(self, symbol: str, scheme_code: Optional[str] = None) -> Optional[MarketData]:
        """Fetch ETF data combining jugaad-data and MFAPI."""
        try:
            # First try to get market data from jugaad-data
            market_data = self.fetch_equity_data(symbol)
            if not market_data:
                return None
            
            # If we have a scheme code, fetch NAV from MFAPI
            nav = None
            if scheme_code:
                nav = self._fetch_nav_from_mfapi(scheme_code)
                if nav:
                    market_data.nav = nav
                    # Calculate premium/discount
                    if market_data.current_price and nav:
                        market_data.premium_discount = calculate_etf_premium(nav, market_data.current_price)
            
            market_data.symbol_type = SymbolType.ETF
            return market_data
            
        except Exception as e:
            return None
    
    def fetch_mutual_fund_data(self, scheme_code: str) -> Optional[MarketData]:
        """Fetch mutual fund data from MFAPI."""
        try:
            nav_data = self._fetch_nav_from_mfapi(scheme_code)
            if not nav_data:
                return None
            
            return MarketData(
                symbol=scheme_code,
                symbol_type=SymbolType.MUTUAL_FUND,
                nav=nav_data,
                last_updated=datetime.now().isoformat()
            )
            
        except Exception as e:
            return None
    
    def _fetch_nav_from_mfapi(self, scheme_code: str) -> Optional[float]:
        """Fetch NAV from MFAPI."""
        try:
            url = f"https://api.mfapi.in/mf/{scheme_code}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if 'data' in data and data['data']:
                # Get the latest NAV
                latest_data = data['data'][0]
                return float(latest_data.get('nav', 0))
            
            return None
            
        except Exception as e:
            return None
    
    def fetch_symbol_data(self, symbol: str, symbol_type: SymbolType, scheme_code: Optional[str] = None) -> Optional[MarketData]:
        """Fetch data based on symbol type."""
        if symbol_type == SymbolType.EQUITY:
            return self.fetch_equity_data(symbol)
        elif symbol_type == SymbolType.INDEX:
            return self.fetch_index_data(symbol)
        elif symbol_type == SymbolType.ETF:
            return self.fetch_etf_data(symbol, scheme_code)
        elif symbol_type == SymbolType.MUTUAL_FUND:
            return self.fetch_mutual_fund_data(scheme_code or symbol)
        else:
            return None
    
    def fetch_multiple_symbols(self, symbols_data: list) -> Dict[str, MarketData]:
        """Fetch data for multiple symbols."""
        results = {}
        
        for symbol_info in symbols_data:
            symbol = symbol_info.get('symbol')
            symbol_type = symbol_info.get('type')
            scheme_code = symbol_info.get('scheme_code')
            
            if symbol:
                data = self.fetch_symbol_data(symbol, symbol_type, scheme_code)
                if data:
                    results[symbol] = data
        
        return results


# Global data fetcher instance
data_fetcher = DataFetcher()
