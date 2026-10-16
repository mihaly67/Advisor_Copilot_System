# FinMLKit Digest — Financial ML Toolkit (2nd implementation)

> Source: `/data/ml/Labelling, mormalisation , featuring, learning/finmlkit-main/`
> Generated: 2026-10-14

## Áttekintés
Open-source, lightweight financial ML library. Pip-installable (`pip install finmlkit`).
Feldolgoz: raw trades → bars → features → labels → supervised learning.

## Modulok
```
finmlkit/
├── bar/       # Standard, dollar, volume, tick bars
├── feature/   # Bar-level indicators + intra-bar features (footprints)
├── label/     # Triple barrier, trend scanning, meta-labeling
├── sampling/  # CUSUM filter, volume/dollar sampling
├── utils/     # Helpers, HDF5 I/O
```

## Összehasonlítás: finmlkit vs financial-ml-toolkit

| Szempont | finmlkit | financial-ml-toolkit |
|----------|----------|---------------------|
| Install | `pip install finmlkit` | Manual (no pip) |
| Bars | Standard, dollar, volume, tick + Binance DB | Standard, dollar, volume |
| Features | Bar-level + **intra-bar footprints** | Bar-level only |
| Labels | TBM, trend, meta | TBM, trend, meta |
| I/O | HDF5 (Binance compatible) | CSV |
| Speed | Numba JIT | NumPy |
| Tests | Full pytest suite | Partial |
| Docs | ReadTheDocs | README only |

## Scalper-re releváns új funkciók
1. **Intra-bar footprints** — order flow feature-k bar-on belül (quant-ohlcv-features-ben nincs)
2. **Binance raw trades → HDF5** — `scripts/binance2h5.py` → crypto data pipeline
3. **Numba JIT** — gyorsabb label/bar computation
4. **HDF5 I/O** — hatékony tárolás nagy adathalmazokhoz

## Ajánlás
- **financial-ml-toolkit**: kutatás + referenciakód (AFML könyv alapján)
- **finmlkit**: production pipeline (pip, JIT, HDF5, footprints)
