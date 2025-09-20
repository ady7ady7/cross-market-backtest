# Symbol configuration for cross-market backtest analysis

# Symbols to use in analysis
USED_SYMBOLS = [
    # Add symbols here that you want to include in your analysis
    # Example: "BTCUSDT", "eurusd", "xauusd"
]

# Symbols to ignore in analysis (all available symbols by default)
IGNORED_SYMBOLS = [
    "deuidxeur",
    "nzdcad",
    "eurjpy",
    "usdcad",
    "usa30idxusd",
    "eurusd",
    "lightcmdusd",
    "xagusd",
    "usa500idxusd",
    "usatechidxusd",
    "xauusd",
    "ETH/USDT"
]

def get_active_symbols():
    """Return list of symbols to use in analysis"""
    return USED_SYMBOLS

def get_ignored_symbols():
    """Return list of symbols to ignore in analysis"""
    return IGNORED_SYMBOLS

def is_symbol_active(symbol):
    """Check if a symbol should be used in analysis"""
    return symbol in USED_SYMBOLS

def move_to_used(symbol):
    """Move symbol from ignored to used list"""
    if symbol in IGNORED_SYMBOLS:
        IGNORED_SYMBOLS.remove(symbol)
        USED_SYMBOLS.append(symbol)
        print(f"Moved {symbol} to used symbols")
    else:
        print(f"{symbol} not found in ignored symbols")

def move_to_ignored(symbol):
    """Move symbol from used to ignored list"""
    if symbol in USED_SYMBOLS:
        USED_SYMBOLS.remove(symbol)
        IGNORED_SYMBOLS.append(symbol)
        print(f"Moved {symbol} to ignored symbols")
    else:
        print(f"{symbol} not found in used symbols")

def print_symbol_status():
    """Print current symbol configuration"""
    print(f"Used symbols ({len(USED_SYMBOLS)}): {USED_SYMBOLS}")
    print(f"Ignored symbols ({len(IGNORED_SYMBOLS)}): {IGNORED_SYMBOLS}")