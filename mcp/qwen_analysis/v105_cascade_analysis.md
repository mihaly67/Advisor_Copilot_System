# v1.05 Cascade + Hybrid + P(Noise) Sweep — Teljes Eredmenyek

**Datum**: 2026.09.30

## 1. Cascade Architektura

| Stage | Feladat | AUC | Accuracy |
|-------|---------|-----|----------|
| Stage 1 | Noise-vs-Dir (binary) | 0.7666 | 70.6% |
| Stage 2 | Long-vs-Short (binary) | **1.0000** | **100.0%** |

**Stage 2 AUC=1.0**: Long és Short osztalyok TELJESEN szetvalnak — soha nincs opposite error (Opp=0 mindig).

## 2. Cascade vs Baseline OOS

| Scenario | Modell | Dir | WR% | Profit | P/tr | PL | L→N | S→N | Opp |
|----------|--------|-----|-----|--------|------|-----|-----|-----|-----|
| Laza | Baseline | 10083 | 62.7% | **8,874** | 0.880 | 1.68 | 959 | 563 | 0 |
| Laza | Cascade 0.65 | 6073 | **66.1%** | 5,966 | **0.982** | 1.95 | 2264 | 1564 | 0 |
| Szigor | Baseline | 5353 | 67.5% | **5,492** | 1.026 | 2.08 | 2406 | 1820 | 0 |
| Szigor | Cascade 0.85 | 1644 | **88.3%** | 2,712 | **1.650** | 7.56 | 3384 | 3005 | 0 |

**Cascade WR brutálisan jobb, de profit rosszabb — túl sok trade-t öl meg.**

## 3. Hybrid: 3-class P(Noise) + Stage2

**Azonos a baseline-lal!** Mivel a 3-class modell sosem cserel Long↔Short (Opp=0),
a Stage2 nem ad hozza semmit — ΔWR=0, ΔP=0 minden scenarionál.

## 4. P(Noise) Threshold Sweep — A TENYLEGES OPTIMALIZALAS

| ThN | Dir | WR% | Profit | P/tr | PL | L→N | S→N |
|-----|-----|-----|--------|------|-----|-----|-----|
| 0.20 | 3,329 | 73.1% | 3,967 | 1.192 | 2.71 | 2,982 | 2,427 |
| 0.30 | 5,353 | 67.5% | 5,492 | 1.026 | 2.08 | 2,406 | 1,820 |
| 0.40 | 7,449 | 64.7% | 7,014 | 0.942 | 1.83 | 1,784 | 1,236 |
| 0.55 | 10,083 | 62.7% | 8,874 | 0.880 | 1.68 | 959 | 563 |
| 0.60 | 10,755 | 62.5% | **9,411** | 0.875 | 1.67 | 731 | 388 |
| 0.79 | 12,387 | 61.4% | **10,428** | 0.842 | 1.59 | 159 | 77 |

### Optimalis pontok
- **Profit MAX**: ThN=0.79 → P=10,428 (WR=61.4%, Dir=12,387)
- **Szigor (eredeti)**: ThN=0.55 → P=8,874 (WR=62.7%, Dir=10,083)
- **WR MAX (min 4000)**: ThN=0.24 → WR=70.4% (P=4,547)

## 5. P(Noise) Distribúció

| True Label | Mean P(Noise) | Std | Median |
|------------|---------------|-----|--------|
| Short(0) | 0.304 | 0.219 | 0.285 |
| Noise(1) | 0.410 | 0.210 | 0.388 |
| Long(2) | 0.365 | 0.239 | 0.360 |

A modell jól megkülönbözteti a Noise-ot (mean=0.41) a Directionaltól (mean=0.30-0.37),
de van jelentős átfedés → a Dir→Noise misclassification forrás.

## 6. Noise Weight Tuning (Stage1)

| nw | AUC | Dir(ThN=0.75) | WR% | Profit |
|----|-----|---------------|-----|--------|
| 0.70 | 0.7652 | 3,721 | 71.1% | 4,217 |
| 0.85 | 0.7666 | 3,270 | 73.1% | 3,903 |
| 1.00 | 0.7679 | 2,855 | 75.6% | 3,622 |

Kisebb nw → több trade, de cascade mindig kevesebb mint 3-class.

## 7. Kulcs Konklúziók

1. **A cascade NEM javit a 3-class-on** — Stage2 AUC=1.0 miatt hibrid=baseline
2. **Csak ThN (P(Noise) threshold) számít** — ThL, THS irrelevánsak
3. **Profit vs WR tradeoff**: ThN=0.79→P=10,428 vs ThN=0.30→P=5,492 (WR=67.5%)
4. **Max teoretikus profit**: 15,682 → ThN=0.79 eléri a 66.5%-át
5. **A következő lépés**: v1.06 features + Noise-specific feature-ök fejlesztése

## 8. Mentett Fájlok

- `/models/v105_cascade/stage1_noise_vs_dir.pkl`
- `/models/v105_cascade/stage2_long_vs_short.pkl`
- `/models/v105_cascade/features.txt`
- `/models/v105_cascade/metrics.json`
- `/src/cascade_v105.py`
