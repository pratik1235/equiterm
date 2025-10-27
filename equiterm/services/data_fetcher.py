"""
Data fetching service using jugaad-data and MFAPI.
"""

import requests
from typing import Optional, Dict, Any, List
from datetime import datetime

from jugaad_data.nse import NSELive
import yfinance as yf

from textual import log
from ..models.watchlist import (
    MarketData, StockData, IndexData, ETFData, MutualFundData, SymbolType
)
from ..utils.calculations import calculate_etf_premium, calculate_change_percent

class DataFetcher:
    """Service for fetching market data from various sources."""
    
    def __init__(self):
        self.nse = NSELive()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Equiterm/0.1.0'
        })
    
    def fetch_equity_data(self, symbol: str) -> Optional[StockData]:
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
            if info.get('isETFSec'):
                return self.fetch_etf_data(symbol, quote)
            metadata = quote.get('metadata', {})
            price_info = quote.get('priceInfo', {})
            security_info = quote.get('securityInfo', {})
            industry_info = quote.get('industryInfo', {})
            intraday = price_info.get('intraDayHighLow', {})
            week_hl = price_info.get('weekHighLow', {})
            preopen = quote.get('preOpenMarket', {})
            
            # Calculate total traded volume from preopen data if available
            total_volume = preopen.get('totalTradedVolume')
            
            return StockData(
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
    
    def fetch_index_data(self, symbol: str) -> Optional[IndexData]:
        """Fetch index data using jugaad-data live_index API."""
        try:
            # Use live_index API for comprehensive index data
            response = self.nse.live_index(symbol)
            log(f"PRATIK: Index Data for symbol {symbol}: {response}")
            
            if not response or 'data' not in response or not response['data']:
                log(f"PRATIK: Index Data: Invalid response")
                return None
            
            # Extract data from response
            index_data = response['data'][0]  # Main index data
            advance_info = response.get('advance', {})
            market_status = response.get('marketStatus', {})
            
            return IndexData(
                symbol=symbol,
                symbol_type=SymbolType.INDEX,
                
                # Price information
                current_price=index_data.get('lastPrice'),
                open_price=index_data.get('open'),
                high_price=index_data.get('dayHigh'),
                low_price=index_data.get('dayLow'),
                previous_close=index_data.get('previousClose'),
                change=index_data.get('change'),
                change_percent=index_data.get('pChange'),
                
                # Volume information
                volume=index_data.get('totalTradedVolume'),
                value=index_data.get('totalTradedValue'),
                
                # Index-specific price information
                year_high=index_data.get('yearHigh'),
                year_low=index_data.get('yearLow'),
                
                # Index composition
                advances=int(advance_info.get('advances', 0)) if advance_info.get('advances') else None,
                declines=int(advance_info.get('declines', 0)) if advance_info.get('declines') else None,
                unchanged=int(advance_info.get('unchanged', 0)) if advance_info.get('unchanged') else None,
                
                # Performance metrics
                percent_change_365d=index_data.get('perChange365d'),
                percent_change_30d=index_data.get('perChange30d'),
                near_week_high=index_data.get('nearWKH'),
                near_week_low=index_data.get('nearWKL'),
                
                # Market status
                market_status=market_status.get('marketStatus'),
                market_status_message=market_status.get('marketStatusMessage'),
                
                # Index metadata
                index_name=response.get('name') or index_data.get('symbol'),
                total_market_cap=index_data.get('ffmc'),
                
                # Metadata
                last_updated=index_data.get('lastUpdateTime') or response.get('timestamp') or datetime.now().isoformat(),
                raw_data=response
            )
        except Exception as e:
            log(f"Error fetching index data: {e}")
            return None
    
    def fetch_etf_data(self, symbol: str, stock_quote: Optional[dict] = None) -> Optional[ETFData]:
        """Fetch ETF data using jugaad-data stock_quote API."""
        try:
            # Fetch ETF data (ETFs trade like stocks but have additional NAV info)
            quote = stock_quote if stock_quote else self.nse.stock_quote(symbol)
            log(f"PRATIK: ETF Data for symbol {symbol}: {quote}")
            
            if not quote or 'priceInfo' not in quote:
                log(f"PRATIK: ETF Data: {quote} is None or missing priceInfo")
                return None
            
            # Extract nested data structures
            info = quote.get('info', {})
            metadata = quote.get('metadata', {})
            price_info = quote.get('priceInfo', {})
            security_info = quote.get('securityInfo', {})
            industry_info = quote.get('industryInfo', {})
            intraday = price_info.get('intraDayHighLow', {})
            week_hl = price_info.get('weekHighLow', {})
            preopen = quote.get('preOpenMarket', {})
            
            # Extract NAV (iNavValue) from priceInfo - specific to ETFs
            nav = None
            if price_info.get('iNavValue'):
                try:
                    nav = float(price_info.get('iNavValue'))
                except (ValueError, TypeError):
                    nav = None
            
            # Calculate total traded volume
            total_volume = preopen.get('totalTradedVolume')
            
            # Get current price for premium/discount calculation
            current_price = price_info.get('lastPrice')
            
            # Calculate premium/discount if we have both NAV and current price
            premium_discount = None
            if nav and current_price:
                premium_discount = calculate_etf_premium(nav, current_price)
            
            return ETFData(
                symbol=symbol,
                symbol_type=SymbolType.ETF,
                
                # Common price information
                current_price=current_price,
                open_price=price_info.get('open'),
                high_price=intraday.get('max'),
                low_price=intraday.get('min'),
                previous_close=price_info.get('previousClose'),
                change=price_info.get('change'),
                change_percent=price_info.get('pChange'),
                
                # Volume information
                volume=total_volume,
                value=None,  # Not directly available in this response
                
                # Stock-like characteristics
                close_price=price_info.get('close'),
                vwap=price_info.get('vwap'),
                lower_circuit=float(price_info.get('lowerCP', 0)) if price_info.get('lowerCP') else None,
                upper_circuit=float(price_info.get('upperCP', 0)) if price_info.get('upperCP') else None,
                week_high=week_hl.get('max'),
                week_low=week_hl.get('min'),
                week_high_date=week_hl.get('maxDate'),
                week_low_date=week_hl.get('minDate'),
                
                # Fund characteristics (ETF-specific)
                nav=nav,
                premium_discount=premium_discount,
                
                # ETF information
                company_name=info.get('companyName'),
                isin=info.get('isin') or metadata.get('isin'),
                underlying_index=None,  # Not available in this response
                industry=industry_info.get('basicIndustry') or metadata.get('industry'),
                sector=industry_info.get('sector'),
                
                # Trading information
                is_fno=info.get('isFNOSec'),
                is_slb=security_info.get('slb') == 'Yes' if security_info.get('slb') else None,
                total_buy_quantity=preopen.get('totalBuyQuantity'),
                total_sell_quantity=preopen.get('totalSellQuantity'),
                
                # ETF-specific details
                face_value=security_info.get('faceValue'),
                issued_size=security_info.get('issuedSize'),
                listing_date=info.get('listingDate'),
                is_etf_sec=info.get('isETFSec'),
                
                # Price band information
                price_band_percent=price_info.get('pPriceBand'),
                tick_size=price_info.get('tickSize'),
                
                # Metadata
                last_updated=metadata.get('lastUpdateTime') or datetime.now().isoformat(),
                raw_data=quote
            )
            
        except Exception as e:
            log(f"Error fetching ETF data: {e}")
            return None
    
    def fetch_mutual_fund_data(self, scheme_code: str) -> Optional[MutualFundData]:
        """Fetch mutual fund data from MFAPI."""
        try:
            url = f"https://api.mfapi.in/mf/{scheme_code}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if 'data' not in data or not data['data']:
                return None
            
            # Get the latest NAV
            latest_data = data['data'][0]
            nav = float(latest_data.get('nav', 0))
            
            # Extract fund metadata
            meta = data.get('meta', {})
            
            return MutualFundData(
                symbol=scheme_code,
                symbol_type=SymbolType.MUTUAL_FUND,
                
                # Price information (NAV for mutual funds)
                current_price=nav,
                nav=nav,
                
                # Fund-specific information
                scheme_name=meta.get('scheme_name'),
                fund_house=meta.get('fund_house'),
                scheme_type=meta.get('scheme_type'),
                scheme_category=meta.get('scheme_category'),
                
                # Metadata
                last_updated=latest_data.get('date') or datetime.now().isoformat(),
                raw_data=data
            )
            
        except Exception as e:
            log(f"PRATIK: Error fetching mutual fund data: {e}")
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
    
    def fetch_ohlc_data(self, symbols: List[str]) -> Dict[str, Dict[str, float]]:
        """
        Get OHLC and Previous Close data for multiple Indian stocks using yfinance.
        
        Parameters:
        symbols (list): List of stock symbols (e.g., ['RELIANCE', 'TCS'])
        
        Returns:
        dict: Dictionary with symbols as keys and stock data as values
        """
        if not symbols:
            return {}
        
        try:
            # Append .NS to each symbol for NSE
            nse_symbols = [symbol + '.NS' for symbol in symbols]
            
            # Download data for the last 2 days to get current and previous close
            data = yf.download(nse_symbols, period='2d', progress=False)
            
            result = {}
            
            # Handle single stock vs multiple stocks
            if len(symbols) == 1:
                symbol = symbols[0]
                try:
                    latest_data = data.iloc[-1]  # Latest day
                    previous_close = data['Close'].iloc[-2] if len(data) >= 2 else data['Close'].iloc[-1]
                    
                    result[symbol] = {
                        'Open': round(latest_data['Open'], 2),
                        'High': round(latest_data['High'], 2),
                        'Low': round(latest_data['Low'], 2),
                        'Close': round(latest_data['Close'], 2),
                        'Previous Close': round(previous_close, 2)
                    }
                except Exception as e:
                    log(f"Error processing {symbol}: {e}")
                    result[symbol] = None
            else:
                # For multiple stocks
                for symbol in symbols:
                    try:
                        nse_symbol = symbol + '.NS'
                        
                        # Get latest day data
                        latest_open = data['Open'][nse_symbol].iloc[-1]
                        latest_high = data['High'][nse_symbol].iloc[-1]
                        latest_low = data['Low'][nse_symbol].iloc[-1]
                        latest_close = data['Close'][nse_symbol].iloc[-1]
                        
                        # Get previous close
                        if len(data) >= 2:
                            previous_close = data['Close'][nse_symbol].iloc[-2]
                        else:
                            previous_close = latest_close
                        
                        result[symbol] = {
                            'Open': round(latest_open, 2),
                            'High': round(latest_high, 2),
                            'Low': round(latest_low, 2),
                            'Close': round(latest_close, 2),
                            'Previous Close': round(previous_close, 2)
                        }
                    except Exception as e:
                        log(f"Error processing {symbol}: {e}")
                        result[symbol] = None
            
            return result
        except Exception as e:
            log(f"Error fetching stock data: {e}")
            return {}



# Global data fetcher instance
data_fetcher = DataFetcher()
