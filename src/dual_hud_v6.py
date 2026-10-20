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
from datetime import datetime, timedelta
from pathlib import Path

# MT5 szerver idő EEST (UTC+3), rendszer local CEST (UTC+2) → 1 óra eltolódás
# A history_init.csv timestamp-jei szerver EEST szerintiek, a chart-on local CEST-et mutatunk
MT5_TZ_OFFSET = 1  # szerver EEST → local CEST: -1 óra

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
        # ZMQ Context: inaktivitás után reconnect
        context.setsockopt(zmq.RECONNECT_IVL, 1000)        # első újrapróbálkozás 1s
        context.setsockopt(zmq.RECONNECT_IVL_MAX, 5000)    # max 5s retry interval
        socket = context.socket(zmq.SUB)
        # SUB socket reconnect beállítások — ha a PUB (bridge) megszűnik és újra megjelenik,
        # a libzmq automatikusan újrapróbálkozik a connect-el.
        socket.setsockopt(zmq.RECONNECT_IVL, 1000)
        socket.setsockopt(zmq.RECONNECT_IVL_MAX, 5000)
        socket.setsockopt(zmq.LINGER, 0)
        socket.connect(f"tcp://{self.host}:{self.port}")
        socket.setsockopt_string(zmq.SUBSCRIBE, "HUD")
        # RCVTIMEO 1000ms — hogy a recv ne blokkoljon örökké ha nem jön adat,
        # hanem rendszeresen ellenőrizhessük a running flag-et.
        socket.setsockopt(zmq.RCVTIMEO, 1000)
        last_msg_ts = time.time()
        print(f"[HUD ZMQ] SUB csatlakozva → tcp://{self.host}:{self.port} (auto-reconnect be)", flush=True)
        self.msleep(500)  # rövid warm-up (PUB már él)
        while self.running:
            latest = None
            # Minden elérhető üzenetet kiolvasunk, csak az utolsót tartjuk meg
            while True:
                try:
                    msg = socket.recv_string(flags=zmq.NOBLOCK)
                    if msg.startswith("HUD "):
                        latest = json.loads(msg[4:])
                        last_msg_ts = time.time()
                except zmq.Again:
                    break
                except Exception as e:
                    print(f"[HUD ZMQ] Vételi Hiba: {e}", flush=True)
                    break
            if latest is not None:
                self.data_received.emit(latest)
            else:
                # Ha 10s óta nem jött üzenet, jelezzük hogy várakozunk.
                # A ZMQ auto-reconnect a háttérben próbálkozik — nem kell nekünk
                # újracsatlakozni, elég a státuszt logolni.
                idle = time.time() - last_msg_ts
                if idle > 10.0 and int(idle) % 10 == 0:
                    print(f"[HUD ZMQ] ⚠️ {idle:.0f}s óta nincs adat — várakozás bridge-re (auto-reconnect aktív)", flush=True)
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
        # FOLYAMOS MONITOR LOG — mit kap a bridge, mit rajzol a HUD
        # /tmp/hud_line_monitor.log: minden tick-nél nyers adat + line update értékek
        self.monitor_log = open('/tmp/hud_line_monitor.log', 'a', buffering=1)
        self.monitor_log.write(
            f"\n{'='*70}\n"
            f"[MONITOR] HUD indult: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"[MONITOR] Formátum: ts | RAW bridge | LINE update értékek (mit kapnak a line-ok)\n"
            f"{'='*70}\n"
        )
        self.monitor_log.flush()
        self._tick_count = 0
        # PREDICTION CACHE — utolsó valódi predikció tartása a következőig
        # A bridge prediction=None tick-nél 0.0-t küld → HUD meg tartja az utolsót
        self._last_pred = None

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

        # Account info label (balance + equity + P/L) — MT5 EA küldi
        # P/L szín dinamikus: zöld ha pozitív, piros ha negatív
        self.account_label = QLabel("BAL: --- | P/L: ---")
        self.account_label.setStyleSheet(
            "color: #ffcc00; font-size: 14px; font-weight: bold; padding: 6px 10px; "
            "background-color: #1a1a1a; border: 1px solid #ffcc00; border-radius: 4px;")
        info.addWidget(self.account_label, stretch=1)

        layout.addLayout(info)

        # === MAIN CHART (Candlestick, 60% magasság) ===
        self.chart = QtChart(inner_width=1, inner_height=0.6)
        self.chart.layout(background_color='#0d0d0d', text_color='#ffffff')
        self.chart.grid(vert_enabled=False, horz_enabled=False)
        self.chart.candle_style(up_color='#26a69a', down_color='#ef5350',
                                border_up_color='#26a69a', border_down_color='#ef5350',
                                wick_up_color='#26a69a', wick_down_color='#ef5350')
        self.chart.time_scale(visible=True, right_offset=2)
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
        self.subchart_normal.time_scale(visible=True, seconds_visible=False, right_offset=2)
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
        self.n_dummy_min = self.subchart_normal.create_line('DummyMin', color='rgba(25,25,25,1)', width=1, price_line=False)
        self.n_dummy_max = self.subchart_normal.create_line('DummyMax', color='rgba(25,25,25,1)', width=1, price_line=False)
        # Fix [0, 1] price range az overlay scale-en — autoscaleInfoProvider callback
        # Ez kényszeríti, hogy a threshold line-ok (0.35, 0.36, 0.47) mindig látszanak.
        self.subchart_normal.run_script(
            f"{self.n_dummy_max.id}.series.applyOptions("
            "{autoscaleInfoProvider: () => ({priceRange: {minValue: 0, maxValue: 1}})})")

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
        self.subchart_flip.time_scale(visible=True, seconds_visible=False, right_offset=2)
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
        self.f_dummy_min = self.subchart_flip.create_line('DummyMin_F', color='rgba(25,25,25,1)', width=1, price_line=False)
        self.f_dummy_max = self.subchart_flip.create_line('DummyMax_F', color='rgba(25,25,25,1)', width=1, price_line=False)
        # Fix [0, 1] price range az overlay scale-en — autoscaleInfoProvider callback
        self.subchart_flip.run_script(
            f"{self.f_dummy_max.id}.series.applyOptions("
            "{autoscaleInfoProvider: () => ({priceRange: {minValue: 0, maxValue: 1}})})")

        # === PIVOT/ZIGZAG + BID + ENTRY + POSITION LINES a fő chart-on ===
        # Fontos: 0.0 és 0.0001 értékek "Value is null" JS hibát okoznak a BTCUSD skálán!
        # Ezért BTCUSD tartományba eső induló értéket használunk (az első tick frissíti).
        #
        # Pivot/Zigzag szintek — 6 vízszintes vonal (MT5 EA küldi res_micro..sup_ter)
        # Átlépéskor MT5 küld új értéket → horizontal_line.update() mozgatja a vonalat.
        # Micro (vékony, dotted) — sűrűn változik, zigzag szerű
        self.res_micro_line = self.chart.horizontal_line(80000.0, color='#FF6B6B', width=1, style='dotted', text='R1')
        self.sup_micro_line = self.chart.horizontal_line(80000.0, color='#6BFF6B', width=1, style='dotted', text='S1')
        # Secondary (közepes, dashed) — ritkábban változik
        self.res_sec_line = self.chart.horizontal_line(80000.0, color='#FF4444', width=1, style='dashed', text='R2')
        self.sup_sec_line = self.chart.horizontal_line(80000.0, color='#44FF44', width=1, style='dashed', text='S2')
        # Tertiary (vastag, solid) — ritkán változik, fő pivot szintek
        self.res_ter_line = self.chart.horizontal_line(80000.0, color='maroon', width=2, style='solid', text='R3')
        self.sup_ter_line = self.chart.horizontal_line(80000.0, color='darkolivegreen', width=2, style='solid', text='S3')

        # === Bid/Ask line (royalblue dotted) ===
        self.bid_line = self.chart.horizontal_line(80000.0, color='royalblue', width=1, style='dotted')

        # === POZÍCIÓ VONALAK (MT5 tényleges belépési árak) ===
        # Ezek a TE nyitott MT5 pozícióid belépési árai (pos_types/pos_prices).
        # Multi-pozíció támogatás: előre lefoglalt 5 long + 5 short vonal-pool,
        # dinamikusan show/hide a nyitott pozíciók száma alapján.
        # pos_type=1  (Long)  → zöld solid vonal a nyitási árnál
        # pos_type=-1 (Short) → piros solid vonal a nyitási árnál
        # pos_type=0  (nincs) → vonal rejtve (0.0 = nem látszik BTCUSD skálán)
        self.pos_long_lines = [
            self.chart.horizontal_line(0.0, color='#00FF00', width=2, style='solid', text=f'L{i+1}')
            for i in range(5)
        ]
        self.pos_short_lines = [
            self.chart.horizontal_line(0.0, color='#FF0000', width=2, style='solid', text=f'S{i+1}')
            for i in range(5)
        ]

        # === ZMQ THREAD INDÍTÁS (késleltetve!) ===
        # QTimer.singleShot: várunk 3s hogy a WebEngine feldolgozza a JS-t
        # (create_line, horizontal_line) mielőtt az első update() jön
        # Ez megoldja a "Value is null" JS hibát!
        self.zmq_thread = ZMQReceiverThread(port=5557)
        self.zmq_thread.data_received.connect(self.on_data)
        # loadFinished: (1) ResizeObserver injektálás a container-re,
        # (2) ZMQ thread indítása 1000ms késleltetéssel.
        # A ResizeObserver automatikusan hívja reSize()-t ha a container
        # div mérete változik (Qt widget resize → webview → container).
        def _on_load_finished():
            try:
                self.chart.run_script('''
                    // Container CSS: width/height 100% → követi a webview widget méretét.
                    // Ez megoldja a "túl széles" és "maximalizálásnál jobb szél eltűnik" problémát.
                    var _lcContainer = document.getElementById('container');
                    if (_lcContainer && !window._lcContainerStyled) {
                        _lcContainer.style.width = '100%';
                        _lcContainer.style.height = '100%';
                        _lcContainer.style.overflow = 'hidden';
                        window._lcContainerStyled = true;
                    }
                    // ResizeObserver: container méretváltozás → chart reSize() minden charton.
                    if (!window._lcResizeObserver) {
                        if (_lcContainer && typeof ResizeObserver !== 'undefined') {
                            window._lcResizeObserver = new ResizeObserver(function() {
                                if (typeof Lib !== 'undefined' && Lib.Handler) {
                                    for (var key in window) {
                                        if (key.startsWith('chart_') && window[key] && typeof window[key].reSize === 'function') {
                                            try { window[key].reSize(); } catch(e) {}
                                        }
                                    }
                                }
                            });
                            window._lcResizeObserver.observe(_lcContainer);
                        }
                    }
                ''')
            except Exception as e:
                print(f"[HUD ResizeObserver] injektálás sikertelen: {e}", flush=True)
            QTimer.singleShot(1000, self.zmq_thread.start)
        self.chart.get_webview().loadFinished.connect(_on_load_finished)


    def _load_history_mt5(self):
        """History lekérése mt5linux segítségével (python hívja le, nem EA küldi).

        A HUD első tick-nél csatlakozik az mt5linux server-hez (port 18812,
        wine-on fut), és leéri az elmúlt 1500 M1 gyertyát a jelen időponttól
        visszafelé. Ez megszünteti a 15 perces részt a history vége és a live
        tick-ek között — a history mindig friss, a HUD indulásakor lett lekérve.

        Visszatér: DataFrame ['time','open','high','low','close'] (time='YYYY-MM-DD HH:MM:SS')
        vagy None ha a server nem fut / hiba van (→ visszaesés CSV-re).
        """
        try:
            from mt5linux import MetaTrader5 as MT5
            mt5 = MT5(host='127.0.0.1', port=18812)
            from datetime import datetime as _dt
            # 1500 M1 gyertya a jelen időponttól visszafelé (broker idő, UTC)
            rates = mt5.copy_rates_from("BTCUSD", mt5.TIMEFRAME_M1, _dt.now(), 1500)
            mt5.shutdown()
            if rates is None or len(rates) == 0:
                print(f"[HUD MT5] ⚠️ copy_rates_from üres válasz", flush=True)
                return None
            # numpy structured array → DataFrame
            df = pd.DataFrame(rates)
            df['time'] = (pd.to_datetime(df['time'], unit='s') - pd.Timedelta(hours=MT5_TZ_OFFSET)).dt.strftime('%Y-%m-%d %H:%M:%S')
            df = df[['time', 'open', 'high', 'low', 'close']]
            print(f"[HUD MT5] ✅ History leérve mt5linux-ból: {len(df)} M1 gyertya "
                  f"({df['time'].iloc[0]} → {df['time'].iloc[-1]})", flush=True)
            return df
        except Exception as e:
            print(f"[HUD MT5] ⚠️ mt5linux nem elérhető (server fut port 18812?): {e}", flush=True)
            return None


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
                # History betöltés: először mt5linux (python hívja le, nem EA küldi),
                # utána visszaesés a history_init.csv-re (backward compatibility).
                # Az mt5linux server (port 18812) wine-on fut, az MT5 terminalhoz kapcsolódik.
                df_hist = self._load_history_mt5()
                if df_hist is None:
                    # Visszaesés: history_init.csv olvasása (EA OnInit-ben írja)
                    import os as _os
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
                    # History time oszlop konvertálása 'YYYY-MM-DD HH:MM:SS'-re (CSV-ben unix sec van)
                    if df_hist is not None and not df_hist.empty:
                        df_hist['time'] = (pd.to_datetime(df_hist['time'].astype(int), unit='s') - pd.Timedelta(hours=MT5_TZ_OFFSET)).dt.strftime('%Y-%m-%d %H:%M:%S')
                    # Konkatenálás az első tick-kel + deduplikálás (JS crash elkerülése)
                    final_df = pd.concat([df_hist[['time', 'open', 'high', 'low', 'close']], candle_df], ignore_index=True)
                    final_df = final_df.drop_duplicates(subset=['time'], keep='last')
                    # Fő chart: 100 history + 1 tick gyertya
                    self.chart.set(final_df)
                    # Time oszlop a subchart és line inicializáláshoz
                    times = final_df['time']
                    n = len(times)
                    # subchart.set() KELL (v1.59 recipe) — OHLC dummy a time axis-hoz
                    # 0.0-1.0 tartomány: a predikció line-ok (P_Long, P_Short, P_Noise) 0-1
                    # közöttiek, a subchart-on EGY price scale van (sync csak time axis-t
                    # szinkronizál, NEM price scale-t) → a dummy OHLC-t is 0-1-be kell tenni,
                    # különben a line-ok láthatatlanok a 80000-es skálán.
                    # A library timestamp fix (datetime64[ns]) megoldotta a "Value is null"
                    # hibákat — a 0-1 dummy OHLC most már biztonságos.
                    dummy_df_ohlc = pd.DataFrame({
                        'time': times,
                        'open': [0.0]*n, 'high': [1.0]*n,
                        'low': [0.0]*n, 'close': [0.5]*n
                    })
                    self.subchart_normal.set(dummy_df_ohlc)
                    self.subchart_flip.set(dummy_df_ohlc)
                    # Line.set() a valószínűség vonalakon — time scale-t a vonalak vezetik
                    self.n_p_long.set(pd.DataFrame({'time': times, 'P_Long': [0.5]*n}))
                    self.n_p_short.set(pd.DataFrame({'time': times, 'P_Short': [0.5]*n}))
                    self.n_p_noise.set(pd.DataFrame({'time': times, 'P_Noise': [0.0]*n}))
                    self.f_p_long.set(pd.DataFrame({'time': times, 'P_Long_F': [0.5]*n}))
                    self.f_p_short.set(pd.DataFrame({'time': times, 'P_Short_F': [0.5]*n}))
                    self.f_p_noise.set(pd.DataFrame({'time': times, 'P_Noise_F': [0.0]*n}))
                    self.n_dummy_min.set(pd.DataFrame({'time': times, 'DummyMin': [0.0]*n}))
                    self.n_dummy_max.set(pd.DataFrame({'time': times, 'DummyMax': [1.0]*n}))
                    self.f_dummy_min.set(pd.DataFrame({'time': times, 'DummyMin_F': [0.0]*n}))
                    self.f_dummy_max.set(pd.DataFrame({'time': times, 'DummyMax_F': [1.0]*n}))
                    print(f"[HUD] ✅ History betöltve: {len(final_df)} gyertya "
                          f"({final_df.iloc[0]['time']} → {final_df.iloc[-1]['time']})", flush=True)
                else:
                    # Nincs history fájl: csak az első tick-kel inicializálunk
                    self.chart.set(candle_df)
                    # subchart.set() — OHLC 0-1 tartományban (predikció line-ok skálájához)
                    dummy_df_ohlc = pd.DataFrame([{'time': ts_str, 'open': 0.0, 'high': 1.0, 'low': 0.0, 'close': 0.5}])
                    self.subchart_normal.set(dummy_df_ohlc)
                    self.subchart_flip.set(dummy_df_ohlc)
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
                # ELSE AG MONITOR — minden tick-nel logoljuk, hogy az else ag lefut-e
                self.monitor_log.write(f"[ELSE] tick is_initialized={self.is_initialized} ts={ts_str} price={price:.2f}\n"); self.monitor_log.flush()
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
                # CANDLE MONITOR — minden tick-nel logoljuk (nem csak minden 20.)
                if not hasattr(self, '_candle_log_cnt'):
                    self._candle_log_cnt = 0
                self._candle_log_cnt += 1
                self.monitor_log.write(
                    f"[CANDLE] tick_count={self._candle_log_cnt} ts={ts_str} "
                    f"O={candle_s['open']:.2f} H={candle_s['high']:.2f} "
                    f"L={candle_s['low']:.2f} C={candle_s['close']:.2f} price={price:.2f}\n"
                )
                self.monitor_log.flush()
                # Subchart X-tengely előrehaladás — DummyMin/DummyMax line update
                d_min = pd.Series({'time': ts_str, 'DummyMin': 0.0}); d_min.name = 'DummyMin'
                d_max = pd.Series({'time': ts_str, 'DummyMax': 1.0}); d_max.name = 'DummyMax'
                self.n_dummy_min.update(d_min); self.n_dummy_max.update(d_max)
                d_minf = pd.Series({'time': ts_str, 'DummyMin_F': 0.0}); d_minf.name = 'DummyMin_F'
                d_maxf = pd.Series({'time': ts_str, 'DummyMax_F': 1.0}); d_maxf.name = 'DummyMax_F'
                self.f_dummy_min.update(d_minf); self.f_dummy_max.update(d_maxf)

            # Bid/ask + pivot + entry + pozíció frissítés (védve: 0.0 → nem frissítünk)
            bid_val = data.get('bid', price)
            if bid_val > 0:
                self.bid_line.update(bid_val)

            # === PIVOT/ZIGZAG SZINTEK frissítése (6 vonal) ===
            # MT5 EA küldi: res_micro, sup_micro, res_sec, sup_sec, res_ter, sup_ter
            # Átlépéskor MT5 új értéket küld → horizontal_line.update() mozgatja a vonalat.
            for key, line in [('res_micro', self.res_micro_line),
                              ('sup_micro', self.sup_micro_line),
                              ('res_sec', self.res_sec_line),
                              ('sup_sec', self.sup_sec_line),
                              ('res_ter', self.res_ter_line),
                              ('sup_ter', self.sup_ter_line)]:
                pv = data.get(key, 0.0)
                if pv > 0:
                    line.update(pv)

            # === POZÍCIÓ VONALAK (MT5 tényleges belépési árak) ===
            # pos_types/pos_prices listák a bridge-ből (MT5 EA nyitott pozíciók).
            # Több pozíció is lehet egyszerre → szétválogatás long/short,
            # majd a vonal-poolból mutatjuk az első N-t, a többi rejtve (0.0).
            pos_types = data.get('pos_types', [0])    # pl. [1, 1, -1]
            pos_prices = data.get('pos_prices', [0.0]) # pl. [81000.0, 80800.0, 81200.0]
            longs = [pp for pt, pp in zip(pos_types, pos_prices) if pt == 1 and pp > 0]
            shorts = [pp for pt, pp in zip(pos_types, pos_prices) if pt == -1 and pp > 0]
            # Long vonalak: mutatott pozíciók → ár, többi → 0.0 (rejtve)
            for i, line in enumerate(self.pos_long_lines):
                line.update(longs[i] if i < len(longs) else 0.0)
            # Short vonalak: mutatott pozíciók → ár, többi → 0.0 (rejtve)
            for i, line in enumerate(self.pos_short_lines):
                line.update(shorts[i] if i < len(shorts) else 0.0)

            # === PREDICTION CACHE: hold last real value until next prediction ===
            # A bridge prediction=None tick-eknél 0.0-t küld (build_msg else ág).
            # A HUD MEG TARTJA az utolsó valódi predikciót és vízszintesen (flat)
            # húzza a line-t a következő predikcióig — így a vonalak nem esnek 0-ra.
            # Detektálás: p_long==0.0 AND p_short==0.0 → "no prediction" tick
            # (valódi LGBM predikció sosem 0.0 mindkettő — probability mindig >0)
            raw_pL = data.get('p_long', 0.0)
            raw_pS = data.get('p_short', 0.0)
            raw_pN = data.get('p_noise', 0.0)
            raw_pLf = data.get('p_long_flip', 0.0)
            raw_pSf = data.get('p_short_flip', 0.0)
            raw_pNf = data.get('p_noise_flip', 0.0)
            raw_sig = data.get('signal', 0)
            raw_sig_f = data.get('signal_flip', 0)
            raw_regime = data.get('regime', 'neutral')
            is_no_pred = (raw_pL == 0.0 and raw_pS == 0.0)
            if is_no_pred and self._last_pred is not None:
                # HOLD: cache-elt értékek → data dict felülírása
                # Így a line update-k ÉS a label-ek is a tartott értékeket használják
                data.update(self._last_pred)
                pred_mode = "HOLD"
            elif not is_no_pred:
                # VALÓDI predikció: cache frissítése
                self._last_pred = {
                    'p_long': raw_pL, 'p_short': raw_pS, 'p_noise': raw_pN,
                    'signal': raw_sig, 'regime': raw_regime,
                    'hurst': data.get('hurst', 0.5),
                    'trend_str': data.get('trend_str', 0.0),
                    'trend_dir': data.get('trend_dir', 0),
                    'long_thr': data.get('long_thr', 0.48),
                    'short_thr': data.get('short_thr', 0.35),
                    'p_long_flip': raw_pLf, 'p_short_flip': raw_pSf,
                    'p_noise_flip': raw_pNf, 'signal_flip': raw_sig_f,
                    'long_thr_flip': data.get('long_thr_flip', 0.35),
                    'short_thr_flip': data.get('short_thr_flip', 0.48),
                }
                pred_mode = "REAL"
            else:
                # No prediction AND no cache (early ticks before first prediction):
                # SKIP line updates — lines stay at init values (0.5)
                pred_mode = "SKIP"

            if pred_mode != "SKIP":
                # === NORMAL v6 2min lines update (held or real values) ===
                pL = data.get('p_long', 0.0)
                pS = data.get('p_short', 0.0)
                pN = data.get('p_noise', 0.0)
                s_nl = pd.Series({'time': ts_str, 'P_Long': pL}); s_nl.name = 'P_Long'
                self.n_p_long.update(s_nl)
                s_ns = pd.Series({'time': ts_str, 'P_Short': pS}); s_ns.name = 'P_Short'
                self.n_p_short.update(s_ns)
                s_nn = pd.Series({'time': ts_str, 'P_Noise': pN}); s_nn.name = 'P_Noise'
                self.n_p_noise.update(s_nn)
                # Threshold dynamic update
                tL = data.get('long_thr', 0.48); tS = data.get('short_thr', 0.35)
                self.n_thr_long.update(tL)
                self.n_thr_short.update(tS)
                self.n_thr_noise.update(pN)

                # === FLIP v6 2min lines update (held or real values) ===
                pLf = data.get('p_long_flip', 0.0)
                pSf = data.get('p_short_flip', 0.0)
                pNf = data.get('p_noise_flip', 0.0)
                s_fl = pd.Series({'time': ts_str, 'P_Long_F': pLf}); s_fl.name = 'P_Long_F'
                self.f_p_long.update(s_fl)
                s_fs = pd.Series({'time': ts_str, 'P_Short_F': pSf}); s_fs.name = 'P_Short_F'
                self.f_p_short.update(s_fs)
                s_fn = pd.Series({'time': ts_str, 'P_Noise_F': pNf}); s_fn.name = 'P_Noise_F'
                self.f_p_noise.update(s_fn)
                self.f_thr_long.update(data.get('long_thr_flip', tS))
                self.f_thr_short.update(data.get('short_thr_flip', tL))
                self.f_thr_noise.update(pNf)

            # === FOLYAMOS MONITOR: raw bridge vs held line values ===
            self._tick_count += 1
            eff_pL = data.get('p_long', 0.0)
            eff_pS = data.get('p_short', 0.0)
            eff_pN = data.get('p_noise', 0.0)
            eff_pLf = data.get('p_long_flip', 0.0)
            eff_pSf = data.get('p_short_flip', 0.0)
            eff_pNf = data.get('p_noise_flip', 0.0)
            eff_sig = data.get('signal', 0)
            eff_sig_f = data.get('signal_flip', 0)
            eff_regime = data.get('regime', '?')
            init_tag = "INIT" if not self.is_initialized else "UPD"
            self.monitor_log.write(
                f"[{ts_str}] tick={self._tick_count} {init_tag} {pred_mode} | "
                f"RAW pL={raw_pL:.3f} pS={raw_pS:.3f} pN={raw_pN:.3f} sig={raw_sig} regime={raw_regime}\n"
                f"           → HELD pL={eff_pL:.3f} pS={eff_pS:.3f} pN={eff_pN:.3f} sig={eff_sig} regime={eff_regime}\n"
                f"             n_p_long.update({eff_pL:.3f})  n_p_short.update({eff_pS:.3f})  n_p_noise.update({eff_pN:.3f})\n"
                f"           FLIP RAW pLf={raw_pLf:.3f} pSf={raw_pSf:.3f} pNf={raw_pNf:.3f} sig_f={raw_sig_f}\n"
                f"             → HELD pLf={eff_pLf:.3f} pSf={eff_pSf:.3f} pNf={eff_pNf:.3f} sig_f={eff_sig_f}\n"
                f"             f_p_long.update({eff_pLf:.3f})  f_p_short.update({eff_pSf:.3f})  f_p_noise.update({eff_pNf:.3f})\n"
            )
            self.monitor_log.flush()

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

        # Account info: balance, equity, P/L (MT5 EA küldi a TICK payload végén)
        balance = data.get('balance', 0.0)
        equity = data.get('equity', 0.0)
        pos_profit = data.get('pos_profit', 0.0)
        pl_sign = '+' if pos_profit >= 0 else ''
        pl_col = '#00ff00' if pos_profit >= 0 else '#ff4444'
        self.account_label.setText(
            f"BAL: ${balance:,.2f} | EQ: ${equity:,.2f} | P/L: {pl_sign}{pos_profit:.2f}")
        self.account_label.setStyleSheet(
            f"color: {pl_col}; font-size: 14px; font-weight: bold; padding: 6px 10px; "
            f"background-color: #1a1a1a; border: 1px solid {pl_col}; border-radius: 4px;")

    def resizeEvent(self, event):
        """Ablakméretezés (maximize/fullscreen) kezelése.
        
        Probléma: a lightweight-charts JS Handler.reSize() függvénye a
        container div mérete alapján számolja a chart pixelméretét.
        A QWebEngineView widgetmérete nő (Qt layout), de a JS nem kapja meg
        az új container méretet, hacsak meg nem hívjuk a reSize()-t.
        A fő chart (60% magasság) és a 2 subchart (20%+20%) külön-külön
        méreteződik — ha csak a fő chart-ot resize-oljuk, a jobb oldali
        árfolyam-skála és a predikciós vonalak eltűnnek.
        
        Megoldás: resizeEvent-ben a chart.resize(w,h) API-t hívjuk mind a 3
        chart-on (a resize() meghívja a JS {id}.reSize()-t, ami frissíti a
        scale.width/height alapján a pixelméretet). Emellett QTimer 200ms
        késleltetéssel is meghívjuk, hogy a Qt layout biztosan lezáruljon.
        """
        super().resizeEvent(event)
        try:
            wv = self.chart.get_webview()
            w = wv.width()
            h = wv.height()
            if w > 0 and h > 0:
                # Mind a 3 chart JS reSize() hívása (arányok 0-1):
                # fő chart 1.0×0.6, subchart_normal 1.0×0.2, subchart_flip 1.0×0.2
                self.chart.resize(1.0, 0.6)
                if hasattr(self, 'subchart_normal'):
                    self.subchart_normal.resize(1.0, 0.2)
                if hasattr(self, 'subchart_flip'):
                    self.subchart_flip.resize(1.0, 0.2)
                # Fit a time scale, hogy a chart újra kitöltse a viewport-ot
                self.chart.fit()
        except Exception as e:
            print(f"[HUD resizeEvent] Hiba: {e}", flush=True)
        # 200ms múlva újra resize (biztosra megyünk, hogy a Qt layout lezárult)
        try:
            QTimer.singleShot(200, self._deferred_resize)
        except Exception:
            pass

    def _deferred_resize(self):
        """Késleltetett resize a Qt layout véglegesítése után."""
        try:
            if not self.is_initialized:
                return
            wv = self.chart.get_webview()
            w = wv.width()
            h = wv.height()
            if w > 0 and h > 0:
                self.chart.resize(1.0, 0.6)
                if hasattr(self, 'subchart_normal'):
                    self.subchart_normal.resize(1.0, 0.2)
                if hasattr(self, 'subchart_flip'):
                    self.subchart_flip.resize(1.0, 0.2)
        except Exception as e:
            print(f"[HUD _deferred_resize] Hiba: {e}", flush=True)

    def closeEvent(self, event):
        self.zmq_thread.stop()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DualPaneHUD()
    window.show()
    sys.exit(app.exec_())

