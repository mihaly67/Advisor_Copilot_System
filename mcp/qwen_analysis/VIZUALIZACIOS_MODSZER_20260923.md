# Vizualizációs Módszer (Jules stílus adaptálva)
*Időbélyeg: 2026-09-23*

## Eszköz: Plotly (HTML interaktív kimenet)

## Konvenciók (Jules + Z.ai)

### 1. Subplot szerkezet
- `make_subplots(rows=3, cols=1, shared_xaxes=True)`
- Felső panel (60%): Ár + jelzések
- Középső panel (20%): Indikátorok (ATR, RSI)
- Alsó panel (20%): Label eloszlás

### 2. CRITikus: Entry pozíció (anti-lookahead)
**Jelzéseket NEM a feature bar-nál rajzoljuk, hanem az ENTRY bar-nál!**
```python
plot_df['Entry_Timestamp'] = plot_df['Start_Timestamp'].shift(-1)
plot_df['Entry_Open'] = plot_df['Open'].shift(-1)
# Jelzések az Entry_Timestamp / Entry_Open pozícióra kerülnek
```
**Logika:** Label[i] a bar[i] feature-jeiből jön, de az ENTRY bar[i+1] Open-jén történik.

### 3. Színkódolás
- Zöld (`#00FF00`): Long (+1), bullish bar (Close >= Open)
- Piros (`#B22222`): Short (-1), bearish bar (Close < Open)
- Magenta (`#FF00FF`): Short (-1) entry marker
- Szürke (`gray`): Noise (0), RSI P_Noise
- Narancs (`#FFA500`): ATR
- Kék (`#00BFFF`): RSI

### 4. Marker típusok
- `triangle-up`: Long entry
- `triangle-down`: Short entry
- `circle`: Noise
- Vonalak: High-Low barok (Scatter mode='lines')

### 5. Dark téma
```python
plot_bgcolor='#111111'
paper_bgcolor='#000000'
font=dict(color='white')
```

### 6. Ablakozás
- Nem az összes adat, csak utolsó N bar (2000 alapértelmezett)
- Jules: 500 bar

### 7. Vízszintes vonalak (threshold-ok)
- `fig.add_hline()` RSI 30/70, vagy küszöb vonalakhoz

## Fájl: `src/visualize_labels.py`
- Bemenet: `labeled_dollar_bars.csv`
- Kimenet: `docs/labeled_bars_visualization.html`

## Kiterjesztés (modell után)
- `offline_lgbm_visualizer.py`: P_Long/P_Short/P_Noise valószínűségek
- `live_forward_test_analyzer.py`: Live EA predikciók vizualizációja
- Threshold vonalak (TH_LONG, TH_SHORT) a valószínűség panelen