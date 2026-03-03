#!/usr/bin/env python3
"""
Lightweight strategy screener for ATM v2 logic.

- Pulls symbols from a built-in list (large caps + liquid ETFs)
- Runs 30D and 60D backtests on each symbol
- Ranks by weighted score with drawdown penalty

Usage:
  python3 screener.py --interval 15m --top 20
"""

import argparse
import itertools
from dataclasses import dataclass
import numpy as np
import pandas as pd
import yfinance as yf

UNIVERSE = [
    "SPY", "QQQ", "IWM", "DIA", "XLF", "XLK", "XLE", "XLV", "XLI", "XLP", "XLY", "XLB", "XLU", "XLC",
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AMD", "AVGO", "NFLX", "CRM", "INTC", "MU",
    "JPM", "BAC", "GS", "WFC", "UNH", "LLY", "JNJ", "PFE", "XOM", "CVX", "COP", "CAT", "DE", "BA", "NKE"
]

@dataclass
class Params:
    fast: int = 13
    slow: int = 55
    trend: int = 200
    rsi_len: int = 14
    rsi_bull: int = 58
    rsi_bear: int = 42
    adx_len: int = 14
    adx_min: float = 18.0
    atr_len: int = 14
    stop_mult: float = 1.2
    tp_mult: float = 3.5


def rma(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(alpha=1 / n, adjust=False).mean()


def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    d = close.diff()
    up = d.clip(lower=0)
    dn = -d.clip(upper=0)
    rs = rma(up, n) / rma(dn, n)
    return 100 - (100 / (1 + rs))


def dmi_adx(df: pd.DataFrame, n: int = 14):
    h, l, c = df["High"], df["Low"], df["Close"]
    up = h.diff()
    down = -l.diff()
    plus_dm = np.where((up > down) & (up > 0), up, 0.0)
    minus_dm = np.where((down > up) & (down > 0), down, 0.0)

    tr = pd.concat([
        h - l,
        (h - c.shift()).abs(),
        (l - c.shift()).abs(),
    ], axis=1).max(axis=1)

    atr = rma(tr, n)
    plus_di = 100 * (rma(pd.Series(plus_dm, index=df.index), n) / atr)
    minus_di = 100 * (rma(pd.Series(minus_dm, index=df.index), n) / atr)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    adx = rma(dx, n)
    return adx, atr


def backtest(df: pd.DataFrame, p: Params):
    c = df["Close"]
    ema_f = c.ewm(span=p.fast, adjust=False).mean()
    ema_s = c.ewm(span=p.slow, adjust=False).mean()
    ema_t = c.ewm(span=p.trend, adjust=False).mean()
    rr = rsi(c, p.rsi_len)
    adx, atr = dmi_adx(df, p.adx_len)

    trend_up = (c > ema_t) & (ema_f > ema_s)
    trend_dn = (c < ema_t) & (ema_f < ema_s)

    long_cross = (ema_f > ema_s) & (ema_f.shift(1) <= ema_s.shift(1))
    short_cross = (ema_f < ema_s) & (ema_f.shift(1) >= ema_s.shift(1))

    long_signal = trend_up & long_cross & (rr > p.rsi_bull) & (adx > p.adx_min)
    short_signal = trend_dn & short_cross & (rr < p.rsi_bear) & (adx > p.adx_min)

    eq = 10000.0
    peak = eq
    max_dd = 0.0
    pos = 0
    entry = 0.0
    trades = wins = losses = 0
    gp = gl = 0.0

    for i in range(1, len(df)):
        price = float(c.iloc[i])
        low = float(df["Low"].iloc[i])
        high = float(df["High"].iloc[i])
        atrv = float(atr.iloc[i]) if pd.notna(atr.iloc[i]) else 0.0

        if pos == 0:
            if bool(long_signal.iloc[i]):
                pos = 1
                entry = price
                trades += 1
            elif bool(short_signal.iloc[i]):
                pos = -1
                entry = price
                trades += 1
        elif pos == 1:
            stop = entry - atrv * p.stop_mult
            tp = entry + atrv * p.tp_mult
            ex = None
            if low <= stop:
                ex = stop
            elif high >= tp:
                ex = tp
            elif price < float(ema_s.iloc[i]):
                ex = price
            if ex is not None:
                pnl = eq * ((ex - entry) / entry)
                eq += pnl
                pos = 0
                if pnl >= 0:
                    wins += 1
                    gp += pnl
                else:
                    losses += 1
                    gl += -pnl
        else:
            stop = entry + atrv * p.stop_mult
            tp = entry - atrv * p.tp_mult
            ex = None
            if high >= stop:
                ex = stop
            elif low <= tp:
                ex = tp
            elif price > float(ema_s.iloc[i]):
                ex = price
            if ex is not None:
                pnl = eq * ((entry - ex) / entry)
                eq += pnl
                pos = 0
                if pnl >= 0:
                    wins += 1
                    gp += pnl
                else:
                    losses += 1
                    gl += -pnl

        peak = max(peak, eq)
        max_dd = max(max_dd, (peak - eq) / peak)

    net = eq - 10000
    win_rate = wins / max(1, (wins + losses)) * 100
    pf = gp / gl if gl > 0 else np.inf
    return {
        "ret_pct": net / 10000 * 100,
        "net": net,
        "trades": trades,
        "win_pct": win_rate,
        "pf": pf,
        "max_dd_pct": max_dd * 100,
    }


def run(args):
    params = Params()
    rows = []

    for sym in UNIVERSE:
        try:
            df = yf.download(sym, period="60d", interval=args.interval, auto_adjust=False, progress=False)
            if df is None or df.empty:
                continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df.dropna()
            if len(df) < 200:
                continue

            sub30 = df[df.index >= df.index.max() - pd.Timedelta(days=30)]
            sub60 = df[df.index >= df.index.max() - pd.Timedelta(days=60)]
            if len(sub30) < 100 or len(sub60) < 200:
                continue

            r30 = backtest(sub30, params)
            r60 = backtest(sub60, params)

            score = (0.4 * r30["ret_pct"] + 0.6 * r60["ret_pct"]) - (0.3 * r60["max_dd_pct"])
            rows.append({
                "symbol": sym,
                "score": score,
                "ret30%": r30["ret_pct"],
                "ret60%": r60["ret_pct"],
                "dd60%": r60["max_dd_pct"],
                "pf60": r60["pf"],
                "tr60": r60["trades"],
                "win60%": r60["win_pct"],
            })
        except Exception:
            continue

    out = pd.DataFrame(rows)
    if out.empty:
        print("No results. Try another interval.")
        return

    out = out.sort_values("score", ascending=False)
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", None)

    print("\n=== TOP CANDIDATES ===")
    print(out.head(args.top).to_string(index=False, float_format=lambda x: f"{x:0.2f}"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", default="15m", help="e.g. 5m, 15m, 30m, 1h")
    parser.add_argument("--top", type=int, default=20)
    run(parser.parse_args())
