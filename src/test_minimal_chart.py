#!/usr/bin/env python3
"""
TESZT 3: fő chart + 2 subchart (mint v6). Ha "Value is null" jön → a 2 subchart a probléma.
"""
import sys, os
os.environ["QTWEBENGINE_DISABLE_GPU"] = "1"
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-software-rasterizer"
sys.argv += ["--disable-gpu", "--no-sandbox"]

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer
from lightweight_charts.widgets import QtChart
import pandas as pd


class TestHUD(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TEST 3 — chart + 2 subchart (v6 layout)")
        self.resize(1400, 950)
        self.setStyleSheet("background-color: #0d0d0d; color: #ffffff;")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Fő chart (60% magasság)
        self.chart = QtChart(inner_width=1, inner_height=0.6)
        self.chart.layout(background_color='#0d0d0d', text_color='#ffffff')
        self.chart.candle_style(up_color='#26a69a', down_color='#ef5350',
                                border_up_color='#26a69a', border_down_color='#ef5350',
                                wick_up_color='#26a69a', wick_down_color='#ef5350')
        self.chart.time_scale(visible=True, right_offset=12)
        layout.addWidget(self.chart.get_webview(), stretch=6)

        # 1. subchart (NORMAL) — v6 layout
        self.subchart_normal = self.chart.create_subchart(
            position='left', width=1.0, height=0.2, sync=True)
        self.subchart_normal.layout(background_color='#0d0d0d', text_color='#ffffff')
        self.subchart_normal.candle_style(
            up_color='rgba(0,0,0,0)', down_color='rgba(0,0,0,0)',
            border_up_color='rgba(0,0,0,0)', border_down_color='rgba(0,0,0,0)',
            wick_up_color='rgba(0,0,0,0)', wick_down_color='rgba(0,0,0,0)')

        # 2. subchart (FLIP) — v6 layout
        self.subchart_flip = self.chart.create_subchart(
            position='left', width=1.0, height=0.2, sync=True)
        self.subchart_flip.layout(background_color='#0d0d0d', text_color='#ffff00')
        self.subchart_flip.candle_style(
            up_color='rgba(0,0,0,0)', down_color='rgba(0,0,0,0)',
            border_up_color='rgba(0,0,0,0)', border_down_color='rgba(0,0,0,0)',
            wick_up_color='rgba(0,0,0,0)', wick_down_color='rgba(0,0,0,0)')

        # Gyertyák (BTCUSD tartomány)
        self.df = pd.DataFrame({
            'time': ['2026-10-20 12:20:00', '2026-10-20 12:21:00', '2026-10-20 12:22:00'],
            'open':  [81320.0, 81330.0, 81325.0],
            'high':  [81350.0, 81355.0, 81340.0],
            'low':   [81310.0, 81320.0, 81315.0],
            'close': [81340.0, 81335.0, 81330.0],
        })

        # Subchart dummy OHLC — v1.59 recept: 0.0-1.0
        times = self.df['time']
        n = len(times)
        self.dummy_df = pd.DataFrame({
            'time': times,
            'open': [0.0]*n, 'high': [1.0]*n,
            'low': [0.0]*n, 'close': [0.5]*n,
        })

        self.chart.get_webview().loadFinished.connect(
            lambda: QTimer.singleShot(1000, self.set_data))

    def set_data(self):
        print("[Test3] chart.set() hívása...", flush=True)
        self.chart.set(self.df)
        print("[Test3] subchart_normal.set() hívása...", flush=True)
        self.subchart_normal.set(self.dummy_df)
        print("[Test3] subchart_flip.set() hívása...", flush=True)
        self.subchart_flip.set(self.dummy_df)
        print("[Test3] ✅ Mind a 3 set() lefutott", flush=True)
        # JS callback: számoljuk meg a gyertyákat a fő chart-on
        QTimer.singleShot(2000, self.check_candle_count)

    def check_candle_count(self):
        def callback(result):
            print(f"[JS] Fő chart gyertyák száma: {result}", flush=True)
        # A lightweight-charts series data() a chart HTML element-en belül van
        # Próbáljuk a chart id-jával
        chart_id = self.chart.id if hasattr(self.chart, 'id') else 'chart_0'
        js = f'''
        try {{
            var data = {chart_id}.series.data();
            document.title = "CANDLES:" + data.length;
        }} catch(e) {{
            document.title = "ERROR:" + e.message;
        }}
        '''
        self.chart.get_webview().page().runJavaScript(js)
        QTimer.singleShot(500, self.print_title)

    def print_title(self):
        def callback(title):
            print(f"[JS] Document title: {title}", flush=True)
        self.chart.get_webview().page().runJavaScript('document.title', callback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = TestHUD()
    win.show()
    QTimer.singleShot(15000, app.quit)
    sys.exit(app.exec_())


