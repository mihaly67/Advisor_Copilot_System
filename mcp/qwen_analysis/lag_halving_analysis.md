# Lag Felezés Teszt — Végső Elemzés (2026-10-01)

## Teszteredmények

### 1. Derivált feature-ök EGYÉNI lag-ja: CSODÁLATOS felezés!
| Feature | Alap Lag | Derivált Lag | Csökkentés |
|---|---|---|---|
| Slope_Close_14_Vel | -8 | -1 | 88% |
| MomScore_14_Vel | -8 | -1 | 88% |
| EMA50_Slope_Up_Vel | -6 | -1 | 83% |
| Flow_MFI_5_Vel | -5 | -1 | 80% |
| Stoch_D_Vel | -4 | -1 | 75% |
| Pulse_MACD_Hist_Vel | -3 | -1 | 67% |
| Micro_RSI_14_Vel | -2 | 0 | 100% |
| WPR_14_Vel | -2 | 0 | 100% |

### 2. MODELL P(Long) lag: -8 MINDEN változatnál!
| Modell | Feat | LblWR | FwdL | Profit | P(L)Lag |
|---|---|---|---|---|---|
| Eredeti | 65 | 61.2% | 48.1% | 10446 | -8 |
| Cserélt (lassú→derivált) | 65 | 58.4% | 48.7% | 9375 | -8 |
| Hibrid (lassú+derivált) | 73 | 61.4% | 48.2% | 10523 | -8 |

### 3. SHAP: deriváltak HASZNÁLTAK, de nem dominálnak
- Cserélt modell SHAP top: WPR_14_Vel(0.15), Stoch_D_Vel(0.11), Slope_Close_14_Vel(0.09)
- Hibrid modell SHAP top: Pulse_MACD_Hist_Vel(0.11), Flow_MFI_5_Vel(0.10), MomScore_14_Vel(0.10)

## GYÖKÉR OK: A LABEL LASSÚ!

A triple barrier label "Eléri-e az ár a 1.2$ PT-t 5 percen belül?" inherensen lassú:
- A válasz 5 percet néz előre → a lassú feature-ök JOBBAN korrelálnak vele
- A gyors deriváltak a MOZGÁS SEBESSÉGÉT mérik → a SZINTET nem
- A modell racionálisan a lassú feature-öket preferálja

## Megoldási irányok
1. **Kétfázisú modell**: Stage1 = irány (lassú feature-ök) → Stage2 = timing (deriváltak)
2. **Gyorsabb label**: 2-3 perces triple barrier → jobban illik a deriváltakhoz
3. **Derivált alapú entry signal**: ha P(Dir)>0.7 ÉS derivált megerősít → belépés
