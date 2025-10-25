"""
Symbol search service using NSE autocomplete API.
"""

import requests
from typing import List, Dict, Optional
from textual import log


class SymbolSearchService:
    """Service for searching NSE symbols using autocomplete API."""
    
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://www.nseindia.com"
        self.search_url = f"{self.base_url}/api/search/autocomplete"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        self._initialized = False
    
    def _initialize_session(self) -> None:
        """Initialize session by visiting homepage to get cookies."""
        if not self._initialized:
            try:
                self.session.get(self.base_url, headers=self.headers, timeout=5)
                self._initialized = True
                log("Symbol search session initialized")
            except Exception as e:
                log(f"Error initializing symbol search session: {e}")
    
    def search_symbols(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """
        Search for symbols matching the query.
        
        Args:
            query: Search query (symbol or company name)
            max_results: Maximum number of results to return (default: 10)
        
        Returns:
            List of dictionaries with 'symbol' and 'name' keys
        """
        if not query or len(query.strip()) == 0:
            return []
        
        # Initialize session if needed
        self._initialize_session()
        
        params = {'q': query.strip()}
        
        try:
            response = self.session.get(
                self.search_url,
                params=params,
                headers=self.headers,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                symbols = data.get('symbols', [])
                
                # Format results
                results = []
                for item in symbols[:max_results]:
                    symbol = item.get('symbol', '')
                    name = item.get('symbol_info', '') or item.get('symbol_suggest', '')
                    
                    if symbol:
                        results.append({
                            'symbol': symbol,
                            'name': name or symbol
                        })
                
                log(f"Found {len(results)} results for query: {query}")
                return results
            else:
                log(f"Symbol search error: HTTP {response.status_code}")
                return []
        
        except Exception as e:
            log(f"Error searching symbols: {e}")
            return []


# Global instance
symbol_search_service = SymbolSearchService()

