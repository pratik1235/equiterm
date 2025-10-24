"""
Abstract storage interface and implementations for watchlist persistence.
"""

import json
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime

from ..models.watchlist import Watchlist, Symbol, SymbolType


class StorageInterface(ABC):
    """Abstract interface for watchlist storage."""
    
    @abstractmethod
    def save_watchlist(self, watchlist: Watchlist) -> bool:
        """Save a watchlist."""
        pass
    
    @abstractmethod
    def load_watchlist(self, name: str) -> Optional[Watchlist]:
        """Load a watchlist by name."""
        pass
    
    @abstractmethod
    def load_all_watchlists(self) -> Dict[str, Watchlist]:
        """Load all watchlists."""
        pass
    
    @abstractmethod
    def delete_watchlist(self, name: str) -> bool:
        """Delete a watchlist."""
        pass
    
    @abstractmethod
    def list_watchlist_names(self) -> List[str]:
        """List all watchlist names."""
        pass


class JSONStorage(StorageInterface):
    """JSON file-based storage implementation."""
    
    def __init__(self, file_path: str = "data/watchlists.json"):
        self.file_path = file_path
        self._ensure_data_directory()
    
    def _ensure_data_directory(self):
        """Ensure data directory exists."""
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
    
    def _load_raw_data(self) -> Dict:
        """Load raw JSON data from file."""
        if not os.path.exists(self.file_path):
            return {}
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    
    def _save_raw_data(self, data: Dict) -> bool:
        """Save raw JSON data to file."""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except IOError:
            return False
    
    def _dict_to_watchlist(self, data: Dict) -> Watchlist:
        """Convert dictionary to Watchlist object."""
        symbols = []
        for symbol_data in data.get('symbols', []):
            symbol = Symbol(
                name=symbol_data['name'],
                symbol_type=SymbolType(symbol_data['symbol_type']),
                scheme_code=symbol_data.get('scheme_code'),
                mfapi_url=symbol_data.get('mfapi_url')
            )
            symbols.append(symbol)
        
        return Watchlist(
            name=data['name'],
            symbols=symbols,
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def _watchlist_to_dict(self, watchlist: Watchlist) -> Dict:
        """Convert Watchlist object to dictionary."""
        symbols_data = []
        for symbol in watchlist.symbols:
            symbol_data = {
                'name': symbol.name,
                'symbol_type': symbol.symbol_type.value,
                'scheme_code': symbol.scheme_code,
                'mfapi_url': symbol.mfapi_url
            }
            symbols_data.append(symbol_data)
        
        return {
            'name': watchlist.name,
            'symbols': symbols_data,
            'created_at': watchlist.created_at,
            'updated_at': watchlist.updated_at
        }
    
    def save_watchlist(self, watchlist: Watchlist) -> bool:
        """Save a watchlist."""
        # Update timestamp
        if not watchlist.created_at:
            watchlist.created_at = datetime.now().isoformat()
        watchlist.updated_at = datetime.now().isoformat()
        
        # Load existing data
        data = self._load_raw_data()
        
        # Add/update watchlist
        data[watchlist.name] = self._watchlist_to_dict(watchlist)
        
        return self._save_raw_data(data)
    
    def load_watchlist(self, name: str) -> Optional[Watchlist]:
        """Load a watchlist by name."""
        data = self._load_raw_data()
        if name not in data:
            return None
        
        return self._dict_to_watchlist(data[name])
    
    def load_all_watchlists(self) -> Dict[str, Watchlist]:
        """Load all watchlists."""
        data = self._load_raw_data()
        watchlists = {}
        
        for name, watchlist_data in data.items():
            watchlists[name] = self._dict_to_watchlist(watchlist_data)
        
        return watchlists
    
    def delete_watchlist(self, name: str) -> bool:
        """Delete a watchlist."""
        data = self._load_raw_data()
        if name not in data:
            return False
        
        del data[name]
        return self._save_raw_data(data)
    
    def list_watchlist_names(self) -> List[str]:
        """List all watchlist names."""
        data = self._load_raw_data()
        return list(data.keys())


# Global storage instance
storage = JSONStorage()
