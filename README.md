# Adaptive Trend Momentum v6 (Pine Script)

Pine Script v6 strategy for TradingView with:
- **Buy/Sell signal labels** on chart
- **Long + Short** entries
- **ATR-based stop loss / take profit**
- **Trend + momentum filters** (EMA, RSI, ADX)
- **Session filter** (optional)

> ⚠️ No strategy is guaranteed to be "winning" in all markets. Use this as a robust baseline, then optimize per symbol/timeframe and paper-trade first.

---

## Files
- `Adaptive_Trend_Momentum_v6.pine` (original)
- `Adaptive_Trend_Momentum_v2.pine` (recommended current version)
- `screener.py` (Python stock screener + 30/60D strategy ranking)

## How to use in TradingView
1. Open TradingView → **Pine Editor**
2. Create a new script
3. Paste `Adaptive_Trend_Momentum_v2.pine` (recommended)
4. Click **Add to chart**
5. Open **Strategy Tester**
6. Start with Preset = `SPY 15m` and switch to `Custom` for optimization

## 30-day and 60-day backtest
In TradingView:
1. Open **Strategy Tester**
2. Click the gear icon (**Settings**) for the strategy
3. Under **Properties / Date Range** set:
   - **From**: now - 30 days (for 30D run), then rerun
   - **From**: now - 60 days (for 60D run), then rerun
4. Compare metrics:
   - Net Profit
   - Profit Factor
   - Max Drawdown
   - Win Rate
   - Sharpe/Sortino (if available)

## Recommended optimization workflow
1. Pick one market and timeframe first (example: SPY 15m, QQQ 5m, etc.)
2. Tune only 1-2 parameters at a time:
   - `fastEMA`, `slowEMA`
   - `rsiBullMin`, `rsiBearMax`
   - `adxMin`
   - `atrStopMult`, `atrTPMult`
3. Validate on out-of-sample period (different dates)
4. Keep a conservative risk model (small size, low leverage)
5. Re-check after commissions/slippage assumptions

## Suggested parameter ranges
- fastEMA: 8–34
- slowEMA: 34–100
- trendEMA: 100–300
- rsiBullMin: 50–60
- rsiBearMax: 40–50
- adxMin: 15–30
- atrStopMult: 1.0–3.0
- atrTPMult: 1.5–5.0

## Risk disclaimer
This is for educational/research purposes, not financial advice.
