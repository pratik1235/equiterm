"""
Data fetching service using jugaad-data and MFAPI.
"""

import requests
from typing import Optional, Dict, Any
from datetime import datetime

from jugaad_data.nse import NSELive

from textual import log
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
            log(f"PRATIK: Equity Data: {quote}")
            if not quote or 'priceInfo' not in quote:
                log(f"PRATIK: Equity Data: {quote} is None")
                return None
            log(f"PRATIK: Equity Data: {quote} is not None")
            
            # Extract nested data structures
            info = quote.get('info', {})
            metadata = quote.get('metadata', {})
            price_info = quote.get('priceInfo', {})
            security_info = quote.get('securityInfo', {})
            industry_info = quote.get('industryInfo', {})
            intraday = price_info.get('intraDayHighLow', {})
            week_hl = price_info.get('weekHighLow', {})
            preopen = quote.get('preOpenMarket', {})
            
            # Calculate total traded volume from preopen data if available
            total_volume = preopen.get('totalTradedVolume')
            
            return MarketData(
                symbol=symbol,
                symbol_type=SymbolType.EQUITY,
                
                # Price information
                current_price=price_info.get('lastPrice'),
                open_price=price_info.get('open'),
                high_price=intraday.get('max'),
                low_price=intraday.get('min'),
                previous_close=price_info.get('previousClose'),
                close_price=price_info.get('close'),
                change=price_info.get('change'),
                change_percent=price_info.get('pChange'),
                vwap=price_info.get('vwap'),
                
                # Price bands and limits
                lower_circuit=float(price_info.get('lowerCP', 0)) if price_info.get('lowerCP') else None,
                upper_circuit=float(price_info.get('upperCP', 0)) if price_info.get('upperCP') else None,
                week_high=week_hl.get('max'),
                week_low=week_hl.get('min'),
                week_high_date=week_hl.get('maxDate'),
                week_low_date=week_hl.get('minDate'),
                
                # Volume information
                volume=total_volume,
                value=None,  # Not directly available in this response
                total_buy_quantity=preopen.get('totalBuyQuantity'),
                total_sell_quantity=preopen.get('totalSellQuantity'),
                
                # Company information
                company_name=info.get('companyName'),
                industry=industry_info.get('basicIndustry') or metadata.get('industry'),
                sector=industry_info.get('sector'),
                isin=info.get('isin') or metadata.get('isin'),
                
                # Fundamental data
                market_cap=None,  # Not in this response format
                pe_ratio=metadata.get('pdSymbolPe'),
                dividend_yield=None,  # Not in this response format
                face_value=security_info.get('faceValue'),
                issued_size=security_info.get('issuedSize'),
                
                # Trading information
                is_fno=info.get('isFNOSec'),
                is_slb=security_info.get('slb') == 'Yes',
                
                # Metadata
                last_updated=metadata.get('lastUpdateTime') or datetime.now().isoformat(),
                raw_data=quote
            )
        except Exception as e:
            log(f"PRATIK: Error fetching equity data: {e}")
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
