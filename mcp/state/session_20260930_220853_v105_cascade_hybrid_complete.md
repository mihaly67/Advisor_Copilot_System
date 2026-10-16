# Session: v105_cascade_hybrid_complete
*Időbélyeg: 2026-09-30T22:08:53.856611*

# v1.05 Cascade + Hybrid + P(Noise) Sweep Teljes Eredmenyek — 2026.09.30

## CASCADE MODELL (mentve: /models/v105_cascade/)
- Stage 1 (Noise-vs-Dir binary): AUC=0.7666, Acc=70.6%
- Stage 2 (Long-vs-Short binary): AUC=1.0000, Acc=100.0%

## HYBRID FELFEDEZES: 3-class + Stage2 = IDENTICUS a baseline-lal!
A hibrid (3-class P(Noise) szures + Stage2 Long/Short dontes) AZONOS eredmenyt ad
mint a sima 3-class modell, mert Opp=0 mindig — a 3-class modell mar sosem
csereli Long/Short-ot, igy a Stage2 nem ad hozza semmit.

## P(Noise) THRESHOLD SWEEP — A TENYLEGES THN OPTIMALIZALAS
| ThN | Dir | WR% | Profit | P/tr | PL | DN% | L→N | S→N |
|-----|-----|-----|--------|------|-----|-----|-----|-----|
| 0.20| 3329| 73.1%|  3,967| 1.192| 2.71| 26.9%| 2982| 2427 |
| 0.25| 4329| 69.4%|  4,686| 1.082| 2.27| 30.6%| 2715| 2121 |
| 0.30| 5353| 67.5%|  5,492| 1.026| 2.08| 32.5%| 2406| 1820 |
| 0.35| 6455| 66.1%|  6,337| 0.982| 1.95| 33.9%| 2082| 1495 |
| 0.40| 7449| 64.7%|  7,014| 0.942| 1.83| 35.3%| 1784| 1236 |
| 0.50| 9309| 63.2%|  8,349| 0.897| 1.72| 36.8%| 1213|  742 |
| 0.55|10083| 62.7%|  8,874| 0.880| 1.68| 37.3%|  959|  563 |
| 0.60|10755| 62.5%|  9,411| 0.875| 1.67| 37.5%|  731|  388 |
| 0.70|11787| 61.8%| 10,053| 0.853| 1.62| 38.2%|  374|  187 |
| 0.79|12387| 61.4%| 10,428| 0.842| 1.59| 38.6%|  159|   77 |

**PROFIT MAX: ThN=0.79 → P=10,428 (Dir=12,387, WR=61.4%)**
**WR MAX (min 4000): ThN=0.24 → WR=70.4% (Dir=4,093, P=4,547)**

## P(Noise) DISTRIBUTION
- Overall: mean=0.364, std=0.226, median=0.349
- Short(0): mean=0.304 — modell kevesebb noise-t lat
- Noise(1): mean=0.410 — modell tobb noise-t lat
- Long(2):  mean=0.365 — koztes

## NOISE_WEIGHT TUNING (Stage1)
| nw  | AUC   | ThN=0.75 | Dir  | WR%  | Profit |
|-----|-------|----------|------|------|--------|
| 0.70| 0.7652| 0.75     | 3721 | 71.1%|  4,217 |
| 0.75| 0.7652| 0.75     | 3721 | 71.1%|  4,217 |
| 0.80| 0.7725| 0.75     | 3477 | 71.6%|  3,987 |
| 0.85| 0.7666| 0.75     | 3270 | 73.1%|  3,903 |
| 0.90| 0.7684| 0.75     | 3084 | 73.7%|  3,735 |
| 1.00| 0.7679| 0.75     | 2855 | 75.6%|  3,622 |

A kisebb nw tobb trade-t enged at, de a cascade mindig kevesebbet
mint a 3-class modell azonos ThN-nal.

## KULCS KONKLUZIOK
1. **A cascade NEM javit a 3-class-on** — a Stage2 AUC=1.0 miatt a hibrid=baseline
2. **A tenyleges optimalizalo parameterek: THN** (P(Noise) threshold)
3. **Profit vs WR tradeoff**: ThN=0.79→P=10,428 (WR=61.4%) vs ThN=0.30→P=5,492 (WR=67.5%)
4. **Max teoretikus profit**: 15,682 → ThN=0.79 eleri a 66.5%-at
5. **A kovetkezo lepes**: v1.06 features + uj Noise-specific feature-ok
