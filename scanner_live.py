import yfinance as yf
import pandas as pd
import numpy as np

# ---------- TECHNICAL INDICATORS ----------
def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def macd(series, fast=12, slow=26, signal=9):
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    return macd_line, signal_line

def atr(high, low, close, period=14):
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()

# ---------- SINGLE STOCK SCAN ----------
def scan_stock(symbol, period="6mo"):
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        df = ticker.history(period=period, interval="1d", auto_adjust=True)
        if df is None or len(df) < 60:
            return None

        df = df.dropna()
        close = df["Close"]
        high = df["High"]
        low = df["Low"]
        volume = df["Volume"]

        # Indicators
        ema20 = ema(close, 20)
        ema50 = ema(close, 50)
        ema200 = ema(close, 200) if len(close) >= 200 else None
        rsi14 = rsi(close, 14)
        macd_line, signal_line = macd(close)
        atr14 = atr(high, low, close, 14)

        # Latest values
        c = close.iloc[-1]
        e20 = ema20.iloc[-1]
        e50 = ema50.iloc[-1]
        r = rsi14.iloc[-1]
        m = macd_line.iloc[-1]
        s = signal_line.iloc[-1]
        a = atr14.iloc[-1]
        vol = volume.iloc[-1]
        avg_vol = volume.rolling(20).mean().iloc[-1]

        # Conditions
        ema_cross = e20 > e50
        rsi_strong = r > 55
        macd_bull = m > s
        breakout = c > high.rolling(20).max().shift(1).iloc[-1]
        vol_spike = vol > 1.5 * avg_vol if avg_vol > 0 else False

        score = sum([ema_cross, rsi_strong, macd_bull, breakout, vol_spike])
        if score < 3:
            return None

        # Trade levels
        entry = round(c, 2)
        stop = round(c - 1.5 * a, 2)
        target = round(c + 3 * a, 2)
        risk = entry - stop
        reward = target - entry
        rr = round(reward / risk, 2) if risk > 0 else 0
        upside_pct = round((target - entry) / entry * 100, 2)

        reasons = []
        if ema_cross: reasons.append("EMA20 > EMA50")
        if rsi_strong: reasons.append("RSI > 55")
        if macd_bull: reasons.append("MACD bullish")
        if breakout: reasons.append("20-day breakout")
        if vol_spike: reasons.append("Volume spike")

        if score >= 4:
            signal = "BUY"
        else:
            signal = "WATCH"

        return {
            "Symbol": symbol,
            "Signal": signal,
            "Score": score,
            "Entry": entry,
            "StopLoss": stop,
            "Target": target,
            "RR_Ratio": rr,
            "Upside_%": upside_pct,
            "Reasons": ", ".join(reasons),
            "ATR": round(a, 2)
        }
    except Exception as e:
        return None


# ---------- FULL NIFTY500 SCAN ----------
def run_full_scan(symbols, max_workers=10):
    from concurrent.futures import ThreadPoolExecutor, as_completed
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(scan_stock, sym): sym for sym in symbols}
        for future in as_completed(futures):
            res = future.result()
            if res:
                results.append(res)

    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values(["Score", "RR_Ratio"], ascending=[False, False])
    return df


# ---------- NIFTY500 SYMBOL LIST (yfinance) ----------
def get_nifty500_symbols():
    """
    Nifty500 list ke liye niftystocks package use karo
    ya manually CSV se load karo.
    """
    try:
        from niftystocks import ns
        return ns.get_nifty500_symbols()
    except ImportError:
        # Fallback: manual list
        return [
            "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
            "HINDUNILVR", "SBIN", "BHARTIARTL", "ITC", "KOTAKBANK",
            "LT", "AXISBANK", "BAJFINANCE", "ASIANPAINT", "MARUTI",
            "TITAN", "SUNPHARMA", "WIPRO", "NESTLEIND", "ULTRACEMCO",
            # ... apni poori Nifty500 list yahan daalo
          ]
