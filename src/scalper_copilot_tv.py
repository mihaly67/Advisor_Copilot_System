#!/usr/bin/env python3
"""
Scalper Copilot v4.0 — 2min Horizon Chart (1 nap)
PyQt5 + lightweight_charts — TradingView stílusú

4 vizualizáció egy ablakban:
1. FELSŐ (70%): Candlestick OHLC + Long/Short jelzések + zaj szint sáv
2. ALSÓ (30%): P(Long) zöld + P(Short) piros (2min horizont)
3. Küszöb vonalak: Long thr + Short thr (adaptív)
4. Zajzóna: noise_lo → noise_hi szürke sáv

Template: /data/vizualizácio/hud_v5_cfd.py
"""
import sys, json, numpy as np, pandas as pd
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import Qt
from lightweight_charts.widgets import QtChart

MODEL_DIR = Path('/data/LGBM_copilot/models/scalper')
DATA_DIR = Path('/data/dev/LGB_copilot_system/RAW_CSV')
HORIZON = '2min'  # csak 2 perces!


def find_v4_models(instrument='BTCUSD'):
    metas = sorted(MODEL_DIR.glob(f'{instrument}_v4_meta_*.json'))
    if not metas: return None
    with open(metas[-1]) as f: meta = json.load(f)
    preds = sorted(MODEL_DIR.glob(f'{instrument}_v4_preds_*.csv'))
    r = {'meta': meta}
    if preds: r['preds'] = preds[-1]
    return r


def load_day_data(instrument, day_str):
    """OOS tick → 1min OHLC + preds load."""
    # OHLC
    path = DATA_DIR / 'BTCUSD' / 'BTCUSD_külön_vizsga.csv'
    print(f"Loading ticks: {path.name}...")
    df = pd.read_csv(path, parse_dates=['Timestamp'], index_col='Timestamp',
                     usecols=['Timestamp', 'Bid', 'Ask'])
    df.columns = [c.lower() for c in df.columns]
    day = pd.Timestamp(day_str)
    next_day = day + pd.Timedelta(days=1)
    df = df.loc[(df.index >= day) & (df.index < next_day)]
    mid = ((df['bid'] + df['ask']) / 2).to_frame('mid')
    ohlc = mid['mid'].resample('1min').ohlc().dropna()
    ohlc = ohlc.reset_index()
    ohlc.columns = ['date', 'open', 'high', 'low', 'close']
    ohlc['date'] = ohlc['date'].dt.strftime('%Y-%m-%d %H:%M:%S')
    print(f"  OHLC: {len(ohlc)} candles")
    return ohlc


def load_preds_2min(instrument, day_str, max_pts=6000):
    """V4 predikciók — csak 2min horizont."""
    v4 = find_v4_models(instrument)
    if not v4: return None, None, None
    preds = pd.read_csv(v4['preds'], index_col=0, parse_dates=True)
    day = pd.Timestamp(day_str)
    next_day = day + pd.Timedelta(days=1)
    preds = preds.loc[(preds.index >= day) & (preds.index < next_day)]
    if len(preds) > max_pts:
        step = len(preds) // max_pts
        preds = preds.iloc[::step]
    # 2min oszlopok
    pl_col = f'p_long_{HORIZON}'
    ps_col = f'p_short_{HORIZON}'
    lt_col = f'long_thr_{HORIZON}'
    st_col = f'short_thr_{HORIZON}'
    sig_col = f'signal_{HORIZON}'
    noise_col = 'noise_level'
    if pl_col not in preds.columns:
        print(f"  Nincs {pl_col} oszlop!"); return None, None, None

    # Predikció DataFrame — time, p_long, p_short
    pred_df = pd.DataFrame({
        'date': preds.index.strftime('%Y-%m-%d %H:%M:%S'),
        'p_long': preds[pl_col].round(4).values,
        'p_short': preds[ps_col].round(4).values,
        'long_thr': preds[lt_col].round(4).values if lt_col in preds.columns else 0.5,
        'short_thr': preds[st_col].round(4).values if st_col in preds.columns else 0.5,
        'noise': preds[noise_col].round(5).values if noise_col in preds.columns else 0.003,
        'signal': preds[sig_col].values if sig_col in preds.columns else 0,
        'price': preds['price'].round(2).values,
    })
    meta = v4['meta']
    print(f"  Preds: {len(pred_df)} bars, 2min horizon")
    return pred_df, meta, v4


class Copilot2minChart(QMainWindow):
    """1 nap Scalper Copilot — 2min horizont, 4 vizualizáció."""

    def __init__(self, instrument='BTCUSD', day_str='2026-10-05'):
        super().__init__()
        self.instrument = instrument
        self.day_str = day_str
        self.setWindowTitle(
            f"BTCUSD Scalper Copilot v4.0 — {HORIZON} Horizon — {day_str}")
        self.resize(1400, 900)
        self.setStyleSheet("background-color:#000000;")

        cw = QWidget(); self.setCentralWidget(cw)
        ml = QVBoxLayout(cw); ml.setContentsMargins(5, 5, 5, 5)

        # Info sáv
        ic = QWidget()
        ic.setStyleSheet("background-color:#000;border-bottom:1px solid #333;")
        il = QVBoxLayout(ic); il.setContentsMargins(5, 2, 5, 2); il.setSpacing(1)
        self.title_lbl = QLabel(f"⏱️ {instrument} Copilot v4.0 — {HORIZON} — {day_str}")
        self.title_lbl.setStyleSheet("color:#00d2ff;font-size:15px;font-weight:bold;")
        self.title_lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        il.addWidget(self.title_lbl)
        self.info_lbl = QLabel("Loading...")
        self.info_lbl.setStyleSheet("color:#AAA;font-size:12px;")
        self.info_lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        il.addWidget(self.info_lbl)
        ml.addWidget(ic)

        # FŐ CHART (70%)
        self.chart = QtChart(inner_width=1, inner_height=0.7)
        self.chart.layout(background_color='#121212', text_color='#fff')
        self.chart.grid(vert_enabled=False, horz_enabled=False)
        self.chart.time_scale(visible=True, right_offset=0)
        self.chart.legend(visible=True)
        self.chart.get_webview().setStyleSheet("background-color:#121212;")

        # SUBCHART (30%)
        self.sub = self.chart.create_subchart(width=1, height=0.3, sync=True)
        self.sub.layout(background_color='#0a0a0a', text_color='#fff')
        self.sub.grid(vert_enabled=False, horz_enabled=False)
        self.sub.time_scale(visible=True, right_offset=0)

        # Subchart line series-ek
        self.plong_line = self.sub.create_line('P(Long)', color='#22AA22', width=2)
        self.pshort_line = self.sub.create_line('P(Short)', color='#CC3333', width=2)
        self.lthr_line = self.sub.create_line('Long thr', color='#22AA22', width=1, style='dotted')
        self.sthr_line = self.sub.create_line('Short thr', color='#CC3333', width=1, style='dotted')
        self.noise_lo = self.sub.create_line('Noise-Lo', color='#666666', width=1, style='dashed')
        self.noise_hi = self.sub.create_line('Noise-Hi', color='#666666', width=1, style='dashed')
        self.anchor = self.sub.create_line('_anchor', color='transparent', width=0)

        ml.addWidget(self.chart.get_webview())
        self._load_data()

    def _load_data(self):
        """Adat betöltés és chart rajzolás."""
        ohlc = load_day_data(self.instrument, self.day_str)
        if ohlc is None or len(ohlc) == 0:
            self.info_lbl.setText("Nincs OHLC adat!"); return

        pred_df, meta, v4 = load_preds_2min(self.instrument, self.day_str)
        if pred_df is None:
            self.info_lbl.setText("Nincs v4 predikció!"); return

        h = meta['horizons'].get(HORIZON, {})
        l_auc = h.get('long_auc', 0)
        s_auc = h.get('short_auc', 0)
        l_thr = h.get('long_thr_ad', 0.5)
        s_thr = h.get('short_thr_ad', 0.5)

        # Fő chart: candlestick
        self.chart.set(ohlc)
        print(f"  Candlestick set: {len(ohlc)} bars")

        # Jelzés markerek
        long_marks = pred_df[pred_df['signal'] == 1]
        short_marks = pred_df[pred_df['signal'] == -1]
        n_long, n_short = len(long_marks), len(short_marks)

        if n_long > 0:
            ll = self.chart.create_line('Long ▲', color='#22AA22', width=1)
            ll.set(pd.DataFrame({'date': long_marks['date'].values,
                                 'value': (long_marks['price'].values * 0.9997).round(2)}))
        if n_short > 0:
            sl = self.chart.create_line('Short ▼', color='#CC3333', width=1)
            sl.set(pd.DataFrame({'date': short_marks['date'].values,
                                 'value': (short_marks['price'].values * 1.0003).round(2)}))

        # SUBCHART: valószínűségek
        self.plong_line.set(pd.DataFrame({
            'date': pred_df['date'].values, 'value': pred_df['p_long'].values}))
        self.pshort_line.set(pd.DataFrame({
            'date': pred_df['date'].values, 'value': pred_df['p_short'].values}))

        # Küszöb vonalak
        lt_mean = float(pred_df['long_thr'].mean())
        st_mean = float(pred_df['short_thr'].mean())
        self.lthr_line.set(pd.DataFrame({
            'date': pred_df['date'].values, 'value': [lt_mean] * len(pred_df)}))
        self.sthr_line.set(pd.DataFrame({
            'date': pred_df['date'].values, 'value': [st_mean] * len(pred_df)}))

        # Zajzóna: küszöb ± noise * sqrt(120)
        noise_mean = float(pred_df['noise'].mean())
        nf = noise_mean * np.sqrt(120)
        nz_lo = max(0, lt_mean - nf)
        nz_hi = min(1, lt_mean + nf)
        self.noise_lo.set(pd.DataFrame({
            'date': pred_df['date'].values, 'value': [nz_lo] * len(pred_df)}))
        self.noise_hi.set(pd.DataFrame({
            'date': pred_df['date'].values, 'value': [nz_hi] * len(pred_df)}))

        # Anchor [0,1]
        self.anchor.set(pd.DataFrame({
            'date': [pred_df['date'].values[0], pred_df['date'].values[-1]],
            'value': [0.0, 1.0]}))

        self.info_lbl.setText(
            f"📊 2min: L AUC={l_auc:.3f} (thr={lt_mean:.3f}) │ "
            f"S AUC={s_auc:.3f} (thr={st_mean:.3f}) │ "
            f"Noise={noise_mean*100:.3f}% │ "
            f"Long ▲={n_long} │ Short ▼={n_short} │ Bars={len(pred_df)}")
        print(f"  Chart ready: {n_long} Long, {n_short} Short signals")


def run_copilot_chart(instrument='BTCUSD', day_str='2026-10-05'):
    """Fő belépési pont — chart megjelenítés."""
    app = QApplication(sys.argv)
    window = Copilot2minChart(instrument, day_str)
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(
        description='Scalper Copilot v4.0 — 2min Chart (1 nap, TradingView stílus)')
    p.add_argument('--instrument', default='BTCUSD')
    p.add_argument('--date', default='2026-10-05', help='Date YYYY-MM-DD')
    a = p.parse_args()
    run_copilot_chart(a.instrument, a.date)