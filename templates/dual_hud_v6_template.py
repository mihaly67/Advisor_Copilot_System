#!/usr/bin/env python3
"""
Dual HUD v6 — Scalper 2min (Normal + FLIP) ÉLES Dashboard
  FELSŐ (60%): Candlestick + regime színezés
  BAL alsó: Normal v6 2min — P_Long zöld, P_Short piros, P_Noise szürke, threshold dashed
  JOBB alsó: FLIP v6 2min — P_Long<->P_Short csere, sárga rámegy a címre

ZMQ SUB port 5557-re hallgat. Bridge (scalper_v6_online_bridge.py) küldi az adatot.
Template-ként mentve — módosítható ha kell.
"""
import sys, os, json, time
import zmq
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

# RDP/VNC fekete képernyő javítás
os.environ["QTWEBENGINE_DISABLE_GPU"] = "1"
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-software-rasterizer"
sys.argv.append("--disable-gpu")
sys.argv.append("--no-sandbox")

from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget,
                              QHBoxLayout, QLabel, QFrame)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt5.QtWebEngineWidgets import QWebEngineView
from lightweight_charts.widgets import QtChart



class ZMQReceiverThread(QThread):
    data_received = pyqtSignal(dict)

    def __init__(self, port=5557, host='127.0.0.1'):
        super().__init__()
        self.port = port
        self.host = host
        self.running = True

    def run(self):
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.connect(f"tcp://{self.host}:{self.port}")
        socket.setsockopt_string(zmq.SUBSCRIBE, "HUD")
        self.msleep(2000)
        while self.running:
            latest = None
            while True:
                try:
                    msg = socket.recv_string(flags=zmq.NOBLOCK)
                    if msg.startswith("HUD "):
                        latest = json.loads(msg[4:])
                except zmq.Again:
                    break
                except Exception as e:
                    print(f"ZMQ Vételi Hiba: {e}", flush=True)
                    break
            if latest is not None:
                self.data_received.emit(latest)
            self.msleep(10)

    def stop(self):
        self.running = False
        self.wait()


class DualPaneHUD(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Jules Scalper v6 — Normal vs FLIP (2min)")
        self.resize(1400, 950)
        self.setStyleSheet("background-color: #0d0d0d; color: #ffffff;")
        self.is_initialized = False
        self.is_history_loaded = False

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # === INFO PANEL (3 részre osztva) ===
        info = QHBoxLayout()
        self.title_label = QLabel("⏳ Várakozás ZMQ adatra (port 5557)...")
        self.title_label.setStyleSheet(
            "color: #00d2ff; font-size: 16px; font-weight: bold; padding: 4px 12px;")
        info.addWidget(self.title_label, stretch=2)

        self.normal_label = QLabel("NORMAL: ---")
        self.normal_label.setStyleSheet(
            "color: gray; font-size: 14px; font-weight: bold; padding: 6px 10px; "
            "background-color: #1a1a1a; border: 1px solid #333; border-radius: 4px;")
        info.addWidget(self.normal_label, stretch=1)

        self.flip_label = QLabel("FLIP: ---")
        self.flip_label.setStyleSheet(
            "color: gray; font-size: 14px; font-weight: bold; padding: 6px 10px; "
            "background-color: #1a1a1a; border: 1px solid #666600; border-radius: 4px;")
        info.addWidget(self.flip_label, stretch=1)

        layout.addLayout(info)

        # === MAIN CHART (Candlestick, 60% magasság) ===
        self.chart = QtChart(inner_width=1, inner_height=0.6)
        self.chart.layout(background_color='#0d0d0d', text_color='#ffffff')
        self.chart.grid(vert_enabled=False, horz_enabled=False)
        self.chart.candle_style(up_color='#26a69a', down_color='#ef5350',
                                border_up_color='#26a69a', border_down_color='#ef5350',
                                wick_up_color='#26a69a', wick_down_color='#ef5350')
        self.chart.time_scale(visible=True, right_offset=12)
        self.chart.get_webview().setStyleSheet("background-color: #0d0d0d;")
        layout.addWidget(self.chart.get_webview(), stretch=6)



        # === BAL ALSÓ SUBCHART — NORMAL v6 2min ===
        # width=1.0, height=0.2 -> teljes szelesseg, 20% magassag, a fo chart alatt
        self.subchart_normal = self.chart.create_subchart(
            position='left', width=1.0, height=0.2, sync=True)
        self.subchart_normal.layout(background_color='#0d0d0d', text_color='#ffffff')
        self.subchart_normal.grid(vert_enabled=False, horz_enabled=False)
        self.subchart_normal.price_scale(auto_scale=True,
                                          scale_margin_top=0.05, scale_margin_bottom=0.05)
        self.subchart_normal.run_script(
            f"{self.subchart_normal.id}.chart.priceScale('right').applyOptions("
            "{'visible': true, 'autoScale': true, 'scaleMargins': {'top': 0.05, 'bottom': 0.05}})")
        self.subchart_normal.time_scale(visible=True, seconds_visible=False, right_offset=12)
        self.subchart_normal.candle_style(
            up_color='rgba(0,0,0,0)', down_color='rgba(0,0,0,0)',
            border_up_color='rgba(0,0,0,0)', border_down_color='rgba(0,0,0,0)',
            wick_up_color='rgba(0,0,0,0)', wick_down_color='rgba(0,0,0,0)')
        # Lines (normal)
        self.n_p_long = self.subchart_normal.create_line('P_Long', color='#228B22', width=2, price_line=False)
        self.n_p_short = self.subchart_normal.create_line('P_Short', color='#B22222', width=2, price_line=False)
        self.n_p_noise = self.subchart_normal.create_line('P_Noise', color='#888888', width=1, style='dotted', price_line=False)
        self.n_thr_long = self.subchart_normal.horizontal_line(0.35, color='#228B22', width=1, style='dashed', text='Thr_L')
        self.n_thr_short = self.subchart_normal.horizontal_line(0.36, color='#B22222', width=1, style='dashed', text='Thr_S')
        self.n_thr_noise = self.subchart_normal.horizontal_line(0.47, color='#888888', width=1, style='dotted', text='Noise')
        # Dummy line a subchart X-tengely előrehaladásához (v1.59 minta)
        self.n_dummy_min = self.subchart_normal.create_line('DummyMin', color='rgba(0,0,0,0)', width=1, price_line=False)
        self.n_dummy_max = self.subchart_normal.create_line('DummyMax', color='rgba(0,0,0,0)', width=1, price_line=False)

        # === KÖZÉPSŐ ALSÓ SUBCHART — FLIP v6 2min (egymas alatt) ===
        # width=1.0, height=0.2 -> a normal subchart alatt, sargaval hangsulyozva
        self.subchart_flip = self.chart.create_subchart(
            position='left', width=1.0, height=0.2, sync=True)
        self.subchart_flip.layout(background_color='#0d0d0d', text_color='#ffff00')
        self.subchart_flip.grid(vert_enabled=False, horz_enabled=False)
        self.subchart_flip.price_scale(auto_scale=True,
                                        scale_margin_top=0.05, scale_margin_bottom=0.05)
        self.subchart_flip.run_script(
            f"{self.subchart_flip.id}.chart.priceScale('right').applyOptions("
            "{'visible': true, 'autoScale': true, 'scaleMargins': {'top': 0.05, 'bottom': 0.05}})")
        self.subchart_flip.time_scale(visible=True, seconds_visible=False, right_offset=12)
        self.subchart_flip.candle_style(
            up_color='rgba(0,0,0,0)', down_color='rgba(0,0,0,0)',
            border_up_color='rgba(0,0,0,0)', border_down_color='rgba(0,0,0,0)',
            wick_up_color='rgba(0,0,0,0)', wick_down_color='rgba(0,0,0,0)')
        # Lines (flip — sárga hangsúly)
        self.f_p_long = self.subchart_flip.create_line('P_Long_F', color='#228B22', width=2, price_line=False)
        self.f_p_short = self.subchart_flip.create_line('P_Short_F', color='#B22222', width=2, price_line=False)
        self.f_p_noise = self.subchart_flip.create_line('P_Noise_F', color='#888888', width=1, style='dotted', price_line=False)
        self.f_thr_long = self.subchart_flip.horizontal_line(0.35, color='#228B22', width=1, style='dashed', text='Thr_L')
        self.f_thr_short = self.subchart_flip.horizontal_line(0.36, color='#B22222', width=1, style='dashed', text='Thr_S')
        self.f_thr_noise = self.subchart_flip.horizontal_line(0.47, color='#888888', width=1, style='dotted', text='Noise')
        # Dummy line a subchart X-tengely előrehaladásához (v1.59 minta)
        self.f_dummy_min = self.subchart_flip.create_line('DummyMin_F', color='rgba(0,0,0,0)', width=1, price_line=False)
        self.f_dummy_max = self.subchart_flip.create_line('DummyMax_F', color='rgba(0,0,0,0)', width=1, price_line=False)

        # === PIVOT + BID/ASK LINES a fő chart-on ===
        self.bid_line = self.chart.horizontal_line(0.0, color='royalblue', width=1, style='dotted')
        self.res_ter_line = self.chart.horizontal_line(0.0001, color='maroon', width=2, style='solid', text='R3')
        self.sup_ter_line = self.chart.horizontal_line(0.0001, color='darkolivegreen', width=2, style='solid', text='S3')

        # === ZMQ THREAD INDÍTÁS ===
        self.zmq_thread = ZMQReceiverThread(port=5557)
        self.zmq_thread.data_received.connect(self.on_data)
        self.zmq_thread.start()


    def on_data(self, data):
        try:
            price = data.get('price', 0.0)
            ts_str = data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            # Candlestick DataFrame a fő chart-hoz (mint v1.59)
            candle_df = pd.DataFrame([{
                'time': ts_str,
                'open': data.get('open', price),
                'high': data.get('high', price),
                'low': data.get('low', price),
                'close': data.get('close', price),
            }])
            # Subchart dummy DataFrame — OHLC formátum (type-stabil)
            dummy_df = pd.DataFrame([{
                'time': ts_str, 'open': 0.0, 'high': 1.0, 'low': 0.0, 'close': 0.5
            }])

            if not self.is_initialized:
                # Első tick: olvassuk be a history_init.csv-t (mint v1.59),
                # konkatenáljuk az első tick-kel, deduplikáljuk, és chart.set(final_df).
                # A HUD maga olvassa a fájlt — nincs ZMQ slow joiner probléma.
                import os as _os
                df_hist = None
                paths = [
                    "/home/Jules/.wine/drive_c/Program Files/MetaTrader 5 IC Markets EU/MQL5/Files/history_init.csv",
                    "/home/misi/.wine/drive_c/Program Files/MetaTrader 5 IC Markets EU/MQL5/Files/history_init.csv",
                    "history_init.csv",
                ]
                for p in paths:
                    if _os.path.exists(p):
                        df_hist = pd.read_csv(p)
                        print(f"[HUD] History fájl olvasva: {p}", flush=True)
                        break

                if df_hist is not None and not df_hist.empty:
                    # History time oszlop konvertálása 'YYYY-MM-DD HH:MM:SS'-re (mint v1.59)
                    df_hist['time'] = pd.to_datetime(df_hist['time'].astype(int), unit='s').dt.strftime('%Y-%m-%d %H:%M:%S')
                    # Konkatenálás az első tick-kel + deduplikálás (JS crash elkerülése)
                    final_df = pd.concat([df_hist[['time', 'open', 'high', 'low', 'close']], candle_df], ignore_index=True)
                    final_df = final_df.drop_duplicates(subset=['time'], keep='last')
                    # Fő chart: 100 history + 1 tick gyertya
                    self.chart.set(final_df)
                    # Subchart-ok: dummy OHLC a history time oszlopával (szinkron chart-tal)
                    times = final_df['time']
                    df_hist_dummy = pd.DataFrame({'time': times, 'open': [0.0]*len(times), 'high': [1.0]*len(times), 'low': [0.0]*len(times), 'close': [0.5]*len(times)})
                    self.subchart_normal.set(df_hist_dummy)
                    self.subchart_flip.set(df_hist_dummy)
                    # Line-ok inicializálása a history time oszlopával (0 értékekkel)
                    # — így a line-ok és a chart time oszlopa szinkron van (nincs "Value is null")
                    self.n_p_long.set(pd.DataFrame({'time': times, 'P_Long': [0.0]*len(times)}))
                    self.n_p_short.set(pd.DataFrame({'time': times, 'P_Short': [0.0]*len(times)}))
                    self.n_p_noise.set(pd.DataFrame({'time': times, 'P_Noise': [0.0]*len(times)}))
                    self.f_p_long.set(pd.DataFrame({'time': times, 'P_Long_F': [0.0]*len(times)}))
                    self.f_p_short.set(pd.DataFrame({'time': times, 'P_Short_F': [0.0]*len(times)}))
                    self.f_p_noise.set(pd.DataFrame({'time': times, 'P_Noise_F': [0.0]*len(times)}))
                    self.n_dummy_min.set(pd.DataFrame({'time': times, 'DummyMin': [0.0]*len(times)}))
                    self.n_dummy_max.set(pd.DataFrame({'time': times, 'DummyMax': [1.0]*len(times)}))
                    self.f_dummy_min.set(pd.DataFrame({'time': times, 'DummyMin_F': [0.0]*len(times)}))
                    self.f_dummy_max.set(pd.DataFrame({'time': times, 'DummyMax_F': [1.0]*len(times)}))
                    print(f"[HUD] ✅ History betöltve: {len(final_df)} gyertya "
                          f"({final_df.iloc[0]['time']} → {final_df.iloc[-1]['time']})", flush=True)
                else:
                    # Nincs history fájl: csak az első tick-kel inicializálunk
                    self.chart.set(candle_df)
                    self.subchart_normal.set(dummy_df)
                    self.subchart_flip.set(dummy_df)
                    pL0 = data.get('p_long', 0.0); pS0 = data.get('p_short', 0.0); pN0 = data.get('p_noise', 0.0)
                    self.n_p_long.set(pd.DataFrame([{'time': ts_str, 'P_Long': pL0}]))
                    self.n_p_short.set(pd.DataFrame([{'time': ts_str, 'P_Short': pS0}]))
                    self.n_p_noise.set(pd.DataFrame([{'time': ts_str, 'P_Noise': pN0}]))
                    pLf0 = data.get('p_long_flip', pS0); pSf0 = data.get('p_short_flip', pL0); pNf0 = data.get('p_noise_flip', pN0)
                    self.f_p_long.set(pd.DataFrame([{'time': ts_str, 'P_Long_F': pLf0}]))
                    self.f_p_short.set(pd.DataFrame([{'time': ts_str, 'P_Short_F': pSf0}]))
                    self.f_p_noise.set(pd.DataFrame([{'time': ts_str, 'P_Noise_F': pNf0}]))
                    self.n_dummy_min.set(pd.DataFrame([{'time': ts_str, 'DummyMin': 0.0}]))
                    self.n_dummy_max.set(pd.DataFrame([{'time': ts_str, 'DummyMax': 1.0}]))
                    self.f_dummy_min.set(pd.DataFrame([{'time': ts_str, 'DummyMin_F': 0.0}]))
                    self.f_dummy_max.set(pd.DataFrame([{'time': ts_str, 'DummyMax_F': 1.0}]))
                    print(f"[HUD] ⚠️ Nincs history fájl — csak tick inicializálás", flush=True)
                self.is_initialized = True
            else:
                # Fő chart frissítése — új Series (soha nem iloc[0] a belső state miatt)
                candle_s = pd.Series({
                    'time': ts_str,
                    'open': data.get('open', price),
                    'high': data.get('high', price),
                    'low': data.get('low', price),
                    'close': data.get('close', price),
                })
                candle_s.name = None
                self.chart.update(candle_s)
                # Subchart X-tengely előrehaladás — DummyMin/DummyMax line update
                d_min = pd.Series({'time': ts_str, 'DummyMin': 0.0}); d_min.name = 'DummyMin'
                d_max = pd.Series({'time': ts_str, 'DummyMax': 1.0}); d_max.name = 'DummyMax'
                self.n_dummy_min.update(d_min); self.n_dummy_max.update(d_max)
                d_minf = pd.Series({'time': ts_str, 'DummyMin_F': 0.0}); d_minf.name = 'DummyMin_F'
                d_maxf = pd.Series({'time': ts_str, 'DummyMax_F': 1.0}); d_maxf.name = 'DummyMax_F'
                self.f_dummy_min.update(d_minf); self.f_dummy_max.update(d_maxf)

            # Bid/ask + pivot frissítés
            self.bid_line.update(data.get('bid', price))

            # === NORMAL v6 2min lines update ===
            s_nl = pd.Series({'time': ts_str, 'P_Long': data.get('p_long', 0.0)}); s_nl.name = 'P_Long'
            self.n_p_long.update(s_nl)
            s_ns = pd.Series({'time': ts_str, 'P_Short': data.get('p_short', 0.0)}); s_ns.name = 'P_Short'
            self.n_p_short.update(s_ns)
            s_nn = pd.Series({'time': ts_str, 'P_Noise': data.get('p_noise', 0.0)}); s_nn.name = 'P_Noise'
            self.n_p_noise.update(s_nn)
            # Threshold dynamic update
            tL = data.get('long_thr', 0.35); tS = data.get('short_thr', 0.36); tN = data.get('p_noise', 0.47)
            self.n_thr_long.update(tL)
            self.n_thr_short.update(tS)
            self.n_thr_noise.update(tN)

            # === FLIP v6 2min lines update ===
            s_fl = pd.Series({'time': ts_str, 'P_Long_F': data.get('p_long_flip', 0.0)}); s_fl.name = 'P_Long_F'
            self.f_p_long.update(s_fl)
            s_fs = pd.Series({'time': ts_str, 'P_Short_F': data.get('p_short_flip', 0.0)}); s_fs.name = 'P_Short_F'
            self.f_p_short.update(s_fs)
            s_fn = pd.Series({'time': ts_str, 'P_Noise_F': data.get('p_noise_flip', 0.0)}); s_fn.name = 'P_Noise_F'
            self.f_p_noise.update(s_fn)
            self.f_thr_long.update(data.get('long_thr_flip', tL))
            self.f_thr_short.update(data.get('short_thr_flip', tS))
            self.f_thr_noise.update(data.get('p_noise_flip', tN))

        except Exception as e:
            print(f"Update hiba: {e}", flush=True)

        # === INFO LABELS frissítése ===
        self._update_labels(data)


    def _update_labels(self, data):
        # NORMAL
        sig = data.get('signal', 0)
        pL = data.get('p_long', 0.0); pS = data.get('p_short', 0.0); pN = data.get('p_noise', 0.0)
        stable = data.get('is_stable', False)
        regime = data.get('regime', 'neutral')
        if sig == 1:
            txt, col = "BUY (Long)", "#228B22"
        elif sig == -1:
            txt, col = "SELL (Short)", "#B22222"
        else:
            txt, col = "WAIT (Hold)", "gray"
        stb = " [STABLE]" if stable else " [UNSTABLE]"
        self.normal_label.setText(
            f"NORMAL: {txt}{stb} | L:{pL:.2f} S:{pS:.2f} N:{pN:.2f} [{regime}]")
        self.normal_label.setStyleSheet(
            f"color: {col}; font-size: 14px; font-weight: bold; padding: 6px 10px; "
            f"background-color: #1a1a1a; border: 1px solid {col}; border-radius: 4px;")

        # FLIP
        sig_f = data.get('signal_flip', 0)
        pLf = data.get('p_long_flip', 0.0); pSf = data.get('p_short_flip', 0.0)
        if sig_f == 1:
            txt_f, col_f = "BUY (Long) F", "#228B22"
        elif sig_f == -1:
            txt_f, col_f = "SELL (Short) F", "#B22222"
        else:
            txt_f, col_f = "WAIT (Hold) F", "gray"
        stb_f = " [STABLE]" if data.get('is_stable_flip', False) else " [UNSTABLE]"
        self.flip_label.setText(
            f"FLIP: {txt_f}{stb_f} | L:{pLf:.2f} S:{pSf:.2f} N:{data.get('p_noise_flip',0):.2f}")
        self.flip_label.setStyleSheet(
            f"color: {col_f}; font-size: 14px; font-weight: bold; padding: 6px 10px; "
            f"background-color: #1a1a1a; border: 2px solid #FFD700; border-radius: 4px;")

        # FŐ cím: ár + regime + hurst
        price = data.get('price', 0.0)
        hurst = data.get('hurst', 0.5)
        trend_str = data.get('trend_str', 0.0)
        self.title_label.setText(
            f"📊 BTCUSD Scalper v6 2min | ÁR: {price:.2f} | "
            f"Regime: {regime} | H={hurst:.2f} | TS={trend_str:.1f}")

    def closeEvent(self, event):
        self.zmq_thread.stop()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DualPaneHUD()
    window.show()
    sys.exit(app.exec_())

