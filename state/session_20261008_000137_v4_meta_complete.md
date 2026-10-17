# Session: v4_meta_complete
*Időbélyeg: 2026-10-08T00:01:37.172287*

## Jules CFD v4 Meta-Labeling>— BUILT &724

### Teljes pipeline a 4.15M tick adaton (12s futD

### Eredmények
| | OOS | VIZSGA |
|-|-----|--------|
| WR | 54.4% | 49.8% |
| Profit | $160 | $56 |
| Long WR | 41.9% | 48.4% |
| Short WR | 59.5% | 50.3% |
| CUSUM baseline | 49.2% | 48.1% |
| **2 javulás | +5.1% | +1.7% |

### Bar_Direction importance: 12.24% (TOP 3!)

### Architecture
A

### Adatok
- 4.15M tick tanító (2.5 hónap)
- 386K tick vizsga (5 nap)
- Tick: 18 oszlop (Bid/Ask/Volume/MTF/ZigZag/IndikátorokC
- Dollar bar: ~42K bar ($444K adaptive thresholdC
- Features: 15 (S/R + Bar_Dir + Momentum + Trend + RegimeC

### F. Új gyűjtőscript kell (v3C ha NavSystem értékeket is gyűjteni akarunk
