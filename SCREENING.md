# Screening Workflow (V2)

Use `screener.py` to find symbols worth deeper testing in TradingView.

## Run
```bash
python3 screener.py --interval 15m --top 20
```

## What it does
- Downloads last 60 days of data for a liquid universe (ETFs + mega/large caps)
- Runs this strategy logic on each symbol
- Calculates:
  - 30D return
  - 60D return
  - 60D max drawdown
  - 60D profit factor
  - 60D trades / win rate
- Ranks by weighted score:
  - Positive weight on 30D + 60D returns
  - Penalty for higher drawdown

## Suggested process
1. Run screener on 15m and 5m.
2. Pick top 5 symbols by score.
3. Backtest those in TradingView using `Adaptive_Trend_Momentum_v2.pine`.
4. Tune parameters per symbol (Custom preset).
5. Keep a notebook of best params by symbol/timeframe.

## Important
This is a research filter, not a guaranteed edge. Use paper trading and strict risk controls.
