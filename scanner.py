import ccxt
import pandas as pd
import numpy as np
from functools import lru_cache

# ==========================================
# ⚙️ Config
# ==========================================
EXCHANGE = ccxt.binance()
TIMEFRAME = '4h'
LIMIT = 300
N_LOOKBACK = 24
UNIVERSE_LIMIT = 150

# ==========================================
# 🧹 Skiplist (unwanted tokens)
# ==========================================
SKIPLIST = {
    # Leveraged tokens
    "ETHUP","ETHDOWN","ETHBULL","ETHBEAR","BTCUP","BTCDOWN",
    "BNBUP","BNBDOWN","BNBBULL","BNBBEAR","ADAUP","ADADOWN",
    "LINKUP","LINKDOWN","XTZUP","XTZDOWN","EOSUP","EOSDOWN",
    "EOSBULL","EOSBEAR","TRXUP","TRXDOWN","XRPUP","XRPDOWN",
    "XRPBULL","XRPBEAR","DOTUP","DOTDOWN","LTCUP","LTCDOWN",
    "UNIUP","UNIDOWN","SXPUP","SXPDOWN","FILUP","FILDOWN",
    "YFIUP","YFIDOWN","BCHUP","BCHDOWN","AAVEUP","AAVEDOWN",
    "SUSHIUP","SUSHIDOWN","XLMUP","XLMDOWN","1INCHUP","1INCHDOWN",
    "BULL","BEAR",
    # Stablecoins
    "USDC","TUSD","USDS","BUSD","DAI","SUSD","USDP","FDUSD","AEUR",
    "EURI","XUSD","USD1","BFUSD","USDE","USTC","USDSB",
    # Wrapped / Bridged
    "WBTC","WBETH","BETH",
    # Fiat pairs
    "EUR","GBP","AUD","BKRW",
    # Dead or deprecated
    "FTT","LUNC","BCC","VEN","PAX","BCHABC","NANO","GTO","ERD","COCOS",
    "DOCK","HC","MCO","VITE","DREP","LTO","STPT","WTC","XZC","GXS","AKRO",
}

# ==========================================
# 📈 Helpers
# ==========================================
def zscore(series):
    if len(series) < 2 or series.std() == 0:
        return 0
    return (series.iloc[-1] - series.mean()) / series.std()

@lru_cache(maxsize=1)
def get_universe():
    print("📡 Loading Binance markets...")
    markets = EXCHANGE.load_markets()
    rows = []
    for s, m in markets.items():
        if m.get('spot') and s.endswith('/USDT'):
            base = s.split('/')[0].upper()
            if base in SKIPLIST:
                continue
            vol = float(m.get('info', {}).get('volume', 0) or 0)
            rows.append((s, vol))
    df = pd.DataFrame(rows, columns=['symbol', 'vol'])
    df = df.sort_values('vol', ascending=False).head(UNIVERSE_LIMIT)
    print(f"✅ Universe built with {len(df)} symbols (skipped {len(SKIPLIST)} tokens)")
    return df['symbol'].tolist()

def fetch_ohlcv(symbol):
    ohlcv = EXCHANGE.fetch_ohlcv(symbol, timeframe=TIMEFRAME, limit=LIMIT)
    df = pd.DataFrame(ohlcv, columns=['ts','open','high','low','close','volume'])
    df['ts'] = pd.to_datetime(df['ts'], unit='ms')
    return df

def compute_metrics(df):
    if len(df) < N_LOOKBACK + 1:
        return None

    last = df['close'].iloc[-1]
    prev = df['close'].iloc[-N_LOOKBACK]
    pct_change = (last - prev) / prev * 100

    roll_high = df['high'].rolling(N_LOOKBACK).max()
    recent_high = roll_high.iloc[-2]
    breakout = (last - recent_high) / recent_high * 100 if recent_high else 0

    returns = df['close'].pct_change()
    vol_z = zscore(returns.tail(N_LOOKBACK).abs())
    volatility = returns.rolling(N_LOOKBACK).std()
    vol_breakout = zscore(volatility.tail(N_LOOKBACK))
    relative_strength = (last / df['close'].mean()) - 1

    composite = (
        np.clip(breakout, -50, 50) * 0.5 +
        np.clip(pct_change, -50, 50) * 0.3 +
        np.clip(vol_z, -5, 5) * 0.1 +
        np.clip(relative_strength, -5, 5) * 0.1
    )

    return {
        'last_price': round(float(last), 6),
        'pct_change_%': round(pct_change, 2),
        'breakout_%': round(breakout, 2),
        'vol_z': round(vol_z, 2),
        'vol_breakout': round(vol_breakout, 2),
        'relative_strength': round(relative_strength, 2),
        'score': round(composite, 2),
    }

def scan_universe():
    rows = []
    for symbol in get_universe():
        try:
            df = fetch_ohlcv(symbol)
            m = compute_metrics(df)
            if m:
                rows.append({'Symbol': symbol, **m})
        except Exception:
            continue

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    # human-friendly column names
    pretty_labels = {
        'last_price': 'Last Price',
        'pct_change_%': 'Change (%)',
        'breakout_%': 'Breakout (%)',
        'vol_z': 'Volatility Z-Score',
        'vol_breakout': 'Volatility Breakout',
        'relative_strength': 'Relative Strength',
        'score': 'Composite Score',
    }
    df = df.rename(columns=pretty_labels)

    # sort by Composite Score
    df = df.sort_values('Composite Score', ascending=False)
    return df.reset_index(drop=True)


# ==========================================
# 🧭 Run
# ==========================================
if __name__ == "__main__":
    print("🚀 Scanning market...")
    df = scan_universe()
    print(df.head(20))
    df.to_csv("scanner_output.csv", index=False)
    print("✅ Results saved to scanner_output.csv")

