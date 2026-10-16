# Session: leak_audit_complete
*Időbélyeg: 2026-09-26T17:04:53.807499*

ADATSZIVARGAS AUDIT - VEGSO EREDMENYEK

## v1.04 WR=60.9% = ADATSZIVARGAS (bizonyitva)
- Override WR=100% (korkoros: Slope=label es Slope=feature)
- Forward return H=1: Long 49.7%, Short 49.0% = VELETLENSZINT
- Random kontroll WR=42.7% (nem 60.9%)

## v1.03 WR=40% = SZINTEN FIKCIO!
- Forward WR=49.6% minden threshold-nel
- P(Long) vs fwd5: Pearson=-0.013 (NEGATIV korrelacio!)
- Inverz konfidencia: P(L)>0.7 → 45.8% pos (rosszabb mint veletlen)
- P(L)=[0.4,0.5) a legjobb: 54.5% (alacsony konfidencia = jobb)

## Triple barrier label JO, de modell nem latja
- TB label PT=1.5 MB=15: 88% H5 pozitivitás
- Slope/MomScore label: 50% = veletlenszint
- Feature-ek NEM tartalmaznak prediktiv informaciot az iranyrol

## Gyokerok
1. Label-feature leak (v1.04)
2. Feature-ek nem prediktaljak a forward return-t (v1.03)
3. Modell overfit: inverz konfidencia
4. Label WR != Forward WR — label eloitezo, de forward random