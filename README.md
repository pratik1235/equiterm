# Equiterm - Terminal Stock Market Application

A modern, minimalistic terminal-based application for tracking stocks, ETFs, and mutual funds using Textual framework.

---

## 🎉 **100% Free & No Authentication Required**

**EquiTerm uses only free, public APIs** - no tokens, API keys, or registrations needed! Just install and start tracking your investments immediately. All market data is sourced from public APIs without any authentication barriers.

## Features

- 📈 **Real-time Stock Data**: Fetch live stock prices, indices, and market data
- 📊 **ETF & Mutual Fund Tracking**: Monitor NAV values and calculate premiums
- 📋 **Watchlist Management**: Create and manage personalized watchlists
- 🎨 **Modern Terminal UI**: Clean, responsive interface with color-coded data
- 🔄 **Auto-refresh**: Manual refresh for watchlist data
- 🎯 **Smart Symbol Detection**: Auto-detect symbol types (equity, ETF, index, mutual fund)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd equiterm
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python -m equiterm
```

## Usage

### Main Menu Options

1. **Fetch Symbol Information**
   - Enter any stock symbol, index name, or mutual fund scheme code
   - View categorized data: Price Info, Volume, Fundamentals, ETF/MF specific data
   - Add symbols to existing watchlists

2. **Check Watchlists**
   - View all your saved watchlists
   - See live data for all symbols in a watchlist
   - Manual refresh to update data

3. **Create a Watchlist**
   - Create new watchlists with custom names
   - Add multiple symbols with auto-detection
   - Support for stocks, ETFs, and mutual funds

### Symbol Types Supported

- **Equity**: Standard NSE symbols (RELIANCE, TCS, etc.)
- **Index**: NIFTY, SENSEX, and other indices
- **ETF**: Exchange Traded Funds with premium/discount calculation
- **Mutual Fund**: Using MFAPI scheme codes - <WIP>

<!-- ### MFAPI Integration

For mutual funds and ETFs, the app uses MFAPI (https://api.mfapi.in/). Simply enter the scheme code when adding to watchlists. -->

## Configuration

Watchlists are stored in `data/watchlists.json`. The storage layer is designed to be easily extensible to databases.

## Development

The project follows a modular structure:

```
equiterm/
├── app.py              # Main application
├── screens/            # UI screens
├── services/          # Data fetching and storage
├── models/            # Data models
└── utils/             # Utility functions
```

## License

MIT License
