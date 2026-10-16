# quant-ohlcv-features Digest — 540+ OHLCV Indikátor Katalógus

> Source: `/data/ml/Labelling, mormalisation , featuring, learning/quant-ohlcv-feature-master/`
> Generated: 2026-10-14

## Áttekintés
540+ önálló Python indikátor, OHLCV DataFrame-ből dolgozik. Minden fájl egyetlen
`signal(df, n, factor_name)` függvényt exportál → egyforma interface → pipeline-barát.

## 7 Kategória

| Kategória | Darab | Scalper relevancia | Top indikátorok |
|-----------|-------|--------------------|-----------------|
| **momentum** | 240 | HIGH | RSI, MACD, Stochastic, CCI, ROC, Bias, MTM, DBCD |
| **volatility** | 107 | HIGH | BB, Keltner, Donchian, ATR, CV, UVL |
| **volume** | 82 | HIGH | OBV, MFI, A/D, WVAD, CMF, VPVR |
| **trend** | 73 | MEDIUM | EMA, SMA, DEMA, TEMA, ADX, Aroon, Ichimoku |
| **price** | 19 | MEDIUM | VWAP, typical price, weighted close |
| **liquidity** | 8 | HIGH (micro) | Amihud illiquidity, market placement |
| **composite** | 11 | MEDIUM | momentum×vol, ADX+MTM, sentiment |

## Scalper-re kritikus indikátorok (TOP 20)

### Momentum (scalper must-have)
- **RSI** (Rsi.py) — overbought/oversold, 14 period default
- **RSI mean** (Rsimean.py) — smoothed RSI, kevesebb whipsaw
- **MACD** (Macd.py, Macd_v2.py, Zlmacd.py) — zero-lag MACD scalperhez
- **Stochastic** (Skdj.py, KdjK.py, KdjD.py) — range oscillator
- **CCI** (Cci.py, CciMagic.py) — overbought/oversold alternative
- **ROC** (Roc.py, RocVol.py) — rate of change, volume-weighted
- **DBCD** (Dbcd.py, Dbcd_taker.py) — divergence-based momentum (taker volume!)

### Volatility (stop sizing + regime)
- **BB width** (Bbw.py) — squeeze detection → breakout
- **ATR** (Atr.py) — stop sizing, position sizing
- **Keltner** (Keltner.py) — squeeze detection BB-vel
- **Donchian** (Donchian.py) — channel breakout

### Volume (confirmation)
- **OBV** (Obv.py) — on-balance volume trend
- **MFI** (Mfi.py) — money flow index (volume-weighted RSI)
- **CMF** (Cmf.py) — Chaikin money flow
- **WVAD** (Wvad.py) — Williams volume accumulation

### Liquidity (microstructure)
- **Amihud** (Amihud.py) — illiquidity ratio → slippage proxy
- **Illiquidity** (Illiquidity.py) — alternate formulation

## Design Principles (másolandó!)
1. **Self-contained**: minden fájl önálló, nincs cross-import
2. **Uniform interface**: `signal(df, n, factor_name)` mindenhol
3. **Side-effect-free cleanup**: intermediate columns törölve
4. **Division-by-zero safety**: `eps = 1e-8` mindenhol
5. **Relative outputs**: normalizált/ratio kimenet → scale mismatch elkerülés

## Hogyan integráljuk a scalper copilotba

### Feature pipeline integráció
```python
from momentum_feature.Rsi import signal as rsi
from volatility_feature.Bbw import signal as bbw
from volume_feature.Obv import signal as obv

df = rsi(df, n=14, factor_name="rsi_14")
df = bbw(df, n=20, factor_name="bbw_20")
df = obv(df, n=14, factor_name="obv_14")
```

### Multi-timeframe (lgbm-feature-selection pattern)
```python
from time_series_utils import df_apply_indicator
df = df_apply_indicator(df, rsi_signal, {"n": 14}, resample_period="5T")
# → rsi_14_5T column, automatically resampled and upsampled
```

### Feature selection (SHAP → correlation pruning)
```python
from feature_selection_lgbm import select_features
selected, importance = select_features(model, X_val, top_k=25, max_corr=0.85)
```

## API összehasonlítás: quant-ohlcv-features vs ta-lib
| Szempont | quant-ohlcv-features | ta-lib |
|----------|---------------------|--------|
| Darab | 540+7 | 150+ |
| Sebesség | Python (lassabb) | C (10-100x gyorsabb) |
| Interface | `signal(df, n, name)` | `func(open, high, low, close, volume)` |
| Bővíthetőség | Könnyű (1 fájl = 1 indikátor) | Nehéz (C compile) |
| Liquidity/Composite | VAN (8+11) | NINCS |
| Python native | Igen | C wrapper |

**Ajánlás**: ta-lib sebesség miatt production-ben, quant-ohlcv-features katalógusként
és liquidity/composite indikátorokhoz (amik ta-lib-ben nincsenek).
