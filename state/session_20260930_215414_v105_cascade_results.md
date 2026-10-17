# Session: v105_cascade_results
*Időbélyeg: 2026-09-30T21:54:14.612204*

# v1.05 Cascade Kétlépcsős Döntés Eredmények — 2026.09.30

## CASCADE MODELL ARCHITEKTURA
- Stage 1: Binary Noise-vs-Dir (AUC=0.7666, Acc=70.6%)
- Stage 2: Binary Long-vs-Short (AUC=1.0000, Acc=100.0%!!)
- **Stage 2 AUC=1.0 → Long és Short TELJESEN szétválnak! Soha nincs opposite!**
- Mentve: /data/dev/projects/z-ai-copilot/models/v105_cascade/

## CASCADE vs BASELINE OOS EREDMENYEK

### Cascade (ThN = P(Dir) threshold)
| Scenario | ThN | Dir | WR% | Profit | P/tr | PL | DN% | L→Noise | S→Noise | Opp |
|----------|-----|-----|-----|--------|------|-----|-----|---------|---------|-----|
| Laza     |0.65| 6073| 66.1%|  5966| 0.982| 1.95| 33.9%| 2264| 1564| 0 |
| S1       |0.70| 4561| 68.6%|  4826| 1.058| 2.19| 31.4%| 2699| 2013| 0 |
| S2       |0.75| 3270| 73.1%|  3903| 1.194| 2.72| 26.9%| 3007| 2443| 0 |
| S3       |0.80| 2275| 79.8%|  3170| 1.393| 3.95| 20.2%| 3251| 2775| 0 |
| Szigor   |0.85| 1644| 88.3%|  2712| 1.650| 7.56| 11.7%| 3384| 3005| 0 |

### Baseline 3-class
| Scenario | Dir | WR% | Profit | P/tr | DN% | L→Noise | S→Noise | Opp |
|----------|-----|-----|--------|------|-----|---------|---------|-----|
| Laza     |10083| 62.7%|  8874| 0.880| 37.3%|  959|  563| 0 |
| S1       | 9309| 63.2%|  8349| 0.897| 36.8%| 1213|  742| 0 |
| S2       | 7449| 64.7%|  7014| 0.942| 35.3%| 1784| 1236| 0 |
| S3       | 6455| 66.1%|  6337| 0.982| 33.9%| 2082| 1495| 0 |
| Szigor   | 5353| 67.5%|  5492| 1.026| 32.5%| 2406| 1820| 0 |

### DELTA (Cascade - Baseline)
| Scenario | Δ WR | Δ Profit | Δ L→Noise | Δ S→Noise |
|----------|------|----------|-----------|-----------|
| Laza     | +3.4%|  -2908   | +1305     | +1001     |
| S1       | +5.4%|  -3523   | +1486     | +1271     |
| S2       | +8.4%|  -3111   | +1223     | +1207     |
| S3       |+13.7%|  -3167   | +1169     | +1280     |
| Szigor   |+20.8%|  -2780   | +978      | +1185     |

### CASCADE FINE SWEEP TOP PROFIT
| ThN | Dir | WR% | Profit | P/tr | PL | DN% | L→Noise | S→Noise |
|-----|-----|-----|--------|------|-----|-----|---------|---------|
|0.50 | 9789| 62.6%|  8583| 0.877| 1.67| 37.4%| 1102| 615 |
|0.55 | 8710| 63.5%|  7892| 0.906| 1.74| 36.5%| 1425| 882 |
|0.60 | 7446| 64.6%|  6987| 0.938| 1.83| 35.4%| 1823| 1207 |

## KULCS FELFEDEZES: ThL NEM SZAMIT!
Stage 2 AUC=1.0 → Long/Long szétválnak → ThL nem befolyásolja az eredményt!
Csak ThN (P(Dir) threshold) számít!

## ELEMZES
- Cascade WR drasztikusan jobb (+3.4% to +20.8%)
- Cascade P/tr drasztikusan jobb (0.98→1.65)
- Cascade PL ratio drasztikusan jobb (1.95→7.56)
- DE Cascade profit ALACSONYABB mert kevesebb trade
- A Stage 1 binary modell TULSZIGORU → túl sok bar-ot Noise-ként kezel
- Noise recall baseline=32.2% → cascade Stage1 csak ~43%-ot ismer fel Dir-nek
- A cascade L→Noise + S→Noise NÖVEKSZIK mert a binary modell több irányos bar-t "öl meg"
