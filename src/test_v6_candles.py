#!/usr/bin/env python3
"""
Test: v6 HUD gyertya rajzolás standalone (bridge nélkül)
Betölti a history_init.csv-t és mock ZMQ tick-eket küld.
Ha a chart ablakban megjelennek a gyertyák és frissülnek tick-enként → ✅ OK
"""
import sys, os, json, time
import zmq
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from pathlib import Path

# RDP/VNC fekete képernyő javítás
os.environ["QTWEBENGINE_DISABLE_GPU"] = "1"
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-software-rasterizer"
sys.argv.append("--disable-gpu")
sys.argv.append("--no-sandbox")

from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget,
                               QHBoxLayout, QLabel)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
from lightweight_charts.widgets import QtChart


HISTORY_PATH = "/home/Jules/.wine/drive_c/Program Files/MetaTrader 5 IC Markets EU/MQL5/Files/history_init.csv"
ZMQ_PORT = 5557


class MockZMQPublisher(QThread):
    """Mock ZMQ publisher — history_init.csv alapján szimulál tick-eket."""
    tick_sent = pyqtSignal(dict)

    def __init__(self, zmq_port=ZMQ_PORT):
        super().__init__()
        self.zmq_port = zmq_port
        self.running = True

    def run(self):
        ctx = zmq.Context()
        pub = ctx.socket(zmq.PUB)
        pub.bind(f'tcp://*:{self.zmq_port}')
        print(f"[MockBridge] ZMQ PUB figyel: tcp://*:{self.zmq_port}", flush=True)

        # Betöltjük a history-t
        df = pd.read_csv(HISTORY_PATH)
        print(f"[MockBridge] History: {len(df)} gyertya", flush=True)

        # Küldjük a history utolsó 5 gyertyáját tick-ként (hogy a HUD chart.set()-et hívjon)
        self.msleep(2000)  # várjuk a HUD csatlakozását

        # Első tick — ez indítja el a HUD-ot (history_init.csv olvasás + chart.set)
        last_bar = df.iloc[-1]
        dt = datetime.fromtimestamp(int(last_bar['time']), tz=timezone.utc)
        ts_str = dt.strftime('%Y-%m-%d %H:%M:%S')
        price = float(last_bar['close'])

        msg = {
            'timestamp': ts_str, 'ts': ts_str, 'price': price,
            'open': float(last_bar['open']), 'high': float(last_bar['high']),
            'low': float(last_bar['low']), 'close': float(last_bar['close']),
            'bid': price, 'ask': price + 5.0,
            'pos_types': [0], 'pos_prices': [0.0], 'pos_profit': 0.0,
            'res_micro': 0.0, 'sup_micro': 0.0,
            'res_sec': 0.0, 'sup_sec': 0.0, 'res_ter': 0.0, 'sup_ter': 0.0,
            'p_long': 0.6, 'p_short': 0.3, 'p_noise': 0.3,
            'signal': 1, 'long_thr': 0.48, 'short_thr': 0.35,
            'regime': 'neutral', 'hurst': 0.5, 'trend_str': 0.0, 'trend_dir': 0,
            'p_long_flip': 0.3, 'p_short_flip': 0.6, 'p_noise_flip': 0.3,
            'signal_flip': -1, 'long_thr_flip': 0.35, 'short_thr_flip': 0.48,
            'is_stable': False, 'is_stable_flip': False,
        }
        pub.send_string(f'HUD {json.dumps(msg)}')
        print(f"[MockBridge] Első tick elküldve: {ts_str} price={price:.1f}", flush=True)

        # Utána szimulálunk új M1 gyertyákat (1 tick / 2 sec)
        current_price = price
        tick_count = 0
        while self.running:
            self.msleep(2000)
            # Új perc
            now = datetime.now(tz=timezone.utc)
            ts_str = now.strftime('%Y-%m-%d %H:%M:%S')
            # Random áringadozás
            delta = np.random.normal(0, 15)  # BTCUSD ~15$ std
            current_price += delta
            ohlc_open = current_price - delta/2
            ohlc_high = current_price + abs(delta)
            ohlc_low = current_price - abs(delta)
            ohlc_close = current_price

            msg = {
                'timestamp': ts_str, 'ts': ts_str, 'price': current_price,
                'open': ohlc_open, 'high': ohlc_high,
                'low': ohlc_low, 'close': ohlc_close,
                'bid': current_price - 2.5, 'ask': current_price + 2.5,
                'pos_types': [0], 'pos_prices': [0.0], 'pos_profit': 0.0,
                'res_micro': 0.0, 'sup_micro': 0.0,
                'res_sec': 0.0, 'sup_sec': 0.0, 'res_ter': 0.0, 'sup_ter': 0.0,
                'p_long': 0.5 + np.random.normal(0, 0.1),
                'p_short': 0.3 + np.random.normal(0, 0.1),
                'p_noise': 0.3 + np.random.normal(0, 0.05),
                'signal': np.random.choice([-1, 0, 1]),
                'long_thr': 0.48, 'short_thr': 0.35,
                'regime': np.random.choice(['trending', 'mean_reverting', 'neutral']),
                'hurst': 0.5, 'trend_str': 0.5, 'trend_dir': 0,
                'p_long_flip': 0.3, 'p_short_flip': 0.5, 'p_noise_flip': 0.3,
                'signal_flip': 0, 'long_thr_flip': 0.35, 'short_thr_flip': 0.48,
                'is_stable': False, 'is_stable_flip': False,
            }
            pub.send_string(f'HUD {json.dumps(msg)}')
            tick_count += 1
            if tick_count % 5 == 0:
                print(f"[MockBridge] tick={tick_count} price={current_price:.1f} ts={ts_str}", flush=True)

        pub.close()
        ctx.term()

    def stop(self):
        self.running = False
        self.wait()


def main():
    """Futtatja a dual_hud_v6.py-t mock bridge-szel."""
    # Indítjuk a mock publishert háttérben
    mock = MockZMQPublisher()
    mock.start()
    # Indítjuk a HUD-ot
    print("[Test] Indítom a dual_hud_v6.py HUD-ot...", flush=True)
    # Importáljuk és futtatjuk a HUD-ot
    sys.path.insert(0, '/data/LGBM_copilot/src')
    from dual_hud_v6 import DualPaneHUD

    app = QApplication(sys.argv)
    window = DualPaneHUD()
    window.show()

    # 60 sec után leállítjuk
    def auto_stop():
        print("[Test] 60 sec letelt — leállítom", flush=True)
        mock.stop()
        app.quit()
    QTimer.singleShot(60000, auto_stop)

    ret = app.exec_()
    mock.stop()
    sys.exit(ret)


if __name__ == '__main__':
    main()
