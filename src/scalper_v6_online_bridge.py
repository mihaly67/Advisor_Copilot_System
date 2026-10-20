#!/usr/bin/env python3
"""
Scalper V6 Online Bridge — TCP szerver a Merkava EA-nak + LGBM élő predikció

Architektúra:
  [Merkava EA (MT5)] --TCP socket 5556--> [Bridge: DollarBarAggregator + LGBM predict]
  [Bridge] --ZMQ PUB 5557--> [dual_hud_v6.py]

Protokoll (MQL5 Socket, port 5556 — InpDomBridgePort):
  - EA SocketConnect('127.0.0.1', 5556) — kliensként csatlakozik
  - TICK|time_msc|bid|ask|pos_type|pos_price|pos_profit|av1|av2|bv1|bv2|ap1|ap2|bp1|bp2|pivot_res_micro|pivot_sup_micro|pivot_res_sec|pivot_sup_sec|pivot_res_ter|pivot_sup_ter\n
  - HISTORY_START|N\n ... time_msc|bid|ask\n ... HISTORY_END\n
Pipeline:
  1. TCP szerver fogadja a tick-eket (MQL5 Socket protokoll)
  2. DollarBarAggregator: tick-ek → $0.5M dollar bars (ring buffer, 250 bar)
  3. Amikor új bar zár: build_features + regime_filter (scalper_copilot_v6.py)
  4. LGBM predict a v6 2min modellekkel (long + short)
  5. p_noise = min(p_long, p_short), signal = argmax + threshold
  6. Regime-aware filter (contra-trend suppress)
  7. FLIP: p_long<->p_short, signal csere
  8. ZMQ PUB 5557 a HUD-nak
"""
import sys, os, json, time, signal as sig_mod, threading, socket, io, contextlib
import numpy as np, pandas as pd
from datetime import datetime, timezone, timedelta

import zmq
import lightgbm as lgb

# scalper_copilot_v6 import (feature engineering + regime filter) — elnémítjuk a print-jét
sys.path.insert(0, '/data/LGBM_copilot/src')
_old_stdout = sys.stdout; sys.stdout = io.StringIO()
try:
    import scalper_copilot_v6 as v6
finally:
    sys.stdout = _old_stdout

# ─── KONFIG ───
MODEL_DIR = '/data/LGBM_copilot/models/scalper'
LONG_MODEL = f'{MODEL_DIR}/BTCUSD_v6_long_2min_shap.txt'
SHORT_MODEL = f'{MODEL_DIR}/BTCUSD_v6_short_2min_shap.txt'
TCP_HOST = '0.0.0.0'
TCP_PORT = 5556          # Merkava EA InpDomBridgePort
ZMQ_PORT = 5557          # HUD SUB port
DOLLAR_THR = 500_000     # $0.5M dollar bars (v6 konstans)
RING_BUFFER_SIZE = 250   # bar ring buffer (100+ rolling window a regime-hez)
LONG_THR = 0.48          # fix threshold (preds CSV tipikus érték)
SHORT_THR = 0.35         # fix threshold (preds CSV tipikus érték)
MIN_BARS_FOR_PREDICT = 110  # minimum bar (rolling 100 + regime)
FORMING_BAR_PREDICT_EVERY = 50  # hány tickenként predikáljunk a formálódó bar-on
# EA által generált history_init.csv — 100 M1 bár (OnInit-ben írja)
HISTORY_INIT_PATH = '/home/Jules/.wine/drive_c/Program Files/MetaTrader 5 IC Markets EU/MQL5/Files/history_init.csv'
# MT5 szerver idő EEST (UTC+3), rendszer local CEST (UTC+2) → 1 óra eltolódás
# A timestamp-ek szerver EEST szerintiek, a chart-on local CEST-et mutatunk
MT5_TZ_OFFSET = 1  # szerver EEST → local CEST: -1 óra


@contextlib.contextmanager
def suppress_stdout():
    old = sys.stdout
    sys.stdout = io.StringIO()
    try:
        yield
    finally:
        sys.stdout = old


class DollarBarAggregator:
    """Tick-ek → $0.5M dollar bars (ring buffer)."""

    def __init__(self, dthr=DOLLAR_THR, max_bars=RING_BUFFER_SIZE):
        self.dthr = dthr
        self.max_bars = max_bars
        self.cum = 0.0
        self.vol = 0.0
        self.n = 0
        self.o = None; self.h = None; self.l = None
        self.t0 = None
        self.bars = []  # list of dicts (ring buffer)

    def add_tick(self, ts_ms, price):
        """Add a tick. Returns closed bar dict if a bar was closed, else None."""
        if self.o is None:
            self.o = price; self.h = price; self.l = price
            self.t0 = ts_ms
        self.cum += price  # dollar volume proxy (price per tick)
        self.vol += 0.5
        self.n += 1
        if price > self.h: self.h = price
        if price < self.l: self.l = price
        if self.cum >= self.dthr:
            bar = {'ts': self.t0, 'open': self.o, 'high': self.h, 'low': self.l,
                   'close': price, 'dollar': self.cum, 'vol': self.vol, 'n': self.n}
            self.bars.append(bar)
            if len(self.bars) > self.max_bars:
                self.bars.pop(0)
            closed_bar = bar
            # Reset for next bar
            self.cum = 0.0; self.vol = 0.0; self.n = 0
            self.o = price; self.h = price; self.l = price
            self.t0 = ts_ms
            return closed_bar
        return None

    def get_bars_df(self):
        """Return bars as DataFrame with ATR, ret (for build_features)."""
        if len(self.bars) < 2:
            return None
        df = pd.DataFrame(self.bars)
        df['ts'] = pd.to_datetime(df['ts'], unit='ms', utc=True)
        df = df.set_index('ts')
        df['atr'] = df['high'] - df['low']
        df['atr_pct'] = df['atr'] / df['close']
        df['ret'] = df['close'].pct_change()
        return df

    def current_forming_bar(self, current_price):
        """Return the forming (unclosed) bar as a dict."""
        if self.o is None:
            return {'open': current_price, 'high': current_price, 'low': current_price}
        return {'open': self.o, 'high': self.h, 'low': self.l}

    def init_from_history(self, history_bars):
        """Rekonstruálja a dollár barokat az M1 history-ból (history_init.csv).

        Az M1 gyertyák close árával szimulálunk tick-eket. DOLLAR_THR=$0.5M és
        BTCUSD ár ~$83000 mellett ~6 M1 gyertya zár 1 dollár bart. 1500 M1
        gyertyából ~250 dollár bar adódik — bőven elég a MIN_BARS_FOR_PREDICT=110
        küszöbhöz, így a bridge újraindítás után azonnal prediktálhat (nem kell
        ~15 percet várni 110 élő dollar bar felépülésére).

        Megjegyzés: a rekonstruált barok szélesebbek az élő baroknál (M1 vs
        ~1min), így az első percekben a predikciók kissé out-of-distribution
        lehetnek. Ahogy az élő tick-ek érkeznek, a ring buffer (250) fokozatosan
        frissül élő barokkal, ~15 perc múlva teljesen friss a rolling ablak.
        """
        if not history_bars:
            return
        for bar in history_bars:
            # M1 time (CEST string) → EEST unix ms (szerver idő, mint az élő tick-ek)
            dt = datetime.strptime(bar['time'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc) + timedelta(hours=MT5_TZ_OFFSET)
            ts_ms = int(dt.timestamp()) * 1000
            price = bar['close']
            self.add_tick(ts_ms, price)
        print(f"[Bridge] ✅ DollarBarAggregator inicializálva: {len(self.bars)} bar "
              f"(formálódó: {self.cum:.0f}/${self.dthr:.0f})", flush=True)


class M1BarAggregator:
    """Tick-ek → M1 (1 perces) gyertyák — MT5 chart pontos másolata.

    Minden tick frissíti az aktuális perc gyertyáját (high/low/close).
    Amikor új perc kezdődik, új gyertya nyílik.
    A lightweight_charts update() ugyanazt a time-t frissíti, új time-t ad hozzá.
    """

    def __init__(self):
        self.current_minute = None  # unix másodperc (perc kezdete)
        self.o = None; self.h = None; self.l = None; self.c = None

    def add_tick(self, ts_ms, price):
        """Add a tick. Returns (m1_ts_str, OHLC dict).

        m1_ts_str: 'YYYY-MM-DD HH:MM' formátum (perc pontosság)
        OHLC: {'open', 'high', 'low', 'close'} az aktuális M1 gyertya
        """
        sec = ts_ms // 1000
        minute_ts = sec - (sec % 60)  # perc kezdete (unix másodperc)
        if self.current_minute is None or minute_ts != self.current_minute:
            # Új perc → új gyertya
            self.current_minute = minute_ts
            self.o = price; self.h = price; self.l = price; self.c = price
        else:
            # Ugyanaz a perc → frissítjük a gyertyát
            if price > self.h: self.h = price
            if price < self.l: self.l = price
            self.c = price
        dt = datetime.fromtimestamp(minute_ts, tz=timezone.utc) - timedelta(hours=MT5_TZ_OFFSET)
        ts_str = dt.strftime('%Y-%m-%d %H:%M:%S')
        return ts_str, {'open': self.o, 'high': self.h, 'low': self.l, 'close': self.c}

    def init_from_last_bar(self, m1_ts_str, candle):
        """Initialize the aggregator state from the last M1 bar (from history_init.csv).

        Úgy állítjuk be, hogy a következő tick ugyanabban a percben frissítse ezt a gyertyát,
        új percben pedig új gyertyát nyisson.
        """
        # m1_ts_str local CEST formátumú (a load_history_init konvertálta)
        # Visszaalakítás szerver EEST unix timestamp-re: +MT5_TZ_OFFSET óra
        dt = datetime.strptime(m1_ts_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc) + timedelta(hours=MT5_TZ_OFFSET)
        self.current_minute = int(dt.timestamp())
        self.o = candle['open']; self.h = candle['high']
        self.l = candle['low']; self.c = candle['close']


class V6LivePredictor:
    """LGBM v6 2min live predictor."""

    def __init__(self):
        print(f"[Bridge] Loading v6 2min models...", flush=True)
        self.model_long = lgb.Booster(model_file=LONG_MODEL)
        self.model_short = lgb.Booster(model_file=SHORT_MODEL)
        print(f"[Bridge] ✅ Models loaded: long={os.path.basename(LONG_MODEL)}, short={os.path.basename(SHORT_MODEL)}", flush=True)

    def predict(self, bars_df):
        """Predict on the last bar. Returns dict or None."""
        if len(bars_df) < MIN_BARS_FOR_PREDICT:
            return None
        try:
            with suppress_stdout():
                feat_df, feat_cols = v6.build_features(bars_df)
                regime = v6.regime_filter(bars_df, feat_df)
            if len(feat_df) == 0:
                return None
            last_feat = feat_df.iloc[[-1]]
            last_regime = regime.iloc[-1]
            pL = float(self.model_long.predict(last_feat)[0])
            pS = float(self.model_short.predict(last_feat)[0])
            pN = min(pL, pS)
            # Signal
            sig = 0
            if pL > LONG_THR and pS > SHORT_THR:
                sig = 1 if pL >= pS else -1
            elif pL > LONG_THR:
                sig = 1
            elif pS > SHORT_THR:
                sig = -1
            # Regime-aware filter
            regime_val = str(last_regime['regime'])
            trend_dir = float(last_regime['trend_dir'])
            trend_str = float(last_regime['trend_str'])
            hurst = float(last_regime['hurst'])
            if sig != 0:
                is_trending = regime_val == 'trending'
                is_contra = (sig == -1 and trend_dir > 0) or (sig == 1 and trend_dir < 0)
                if is_contra and is_trending:
                    sig = 0
                elif is_contra and trend_str > 1.5:
                    if sig == 1 and pL < LONG_THR + 0.08: sig = 0
                    elif sig == -1 and pS < SHORT_THR + 0.08: sig = 0
            return {'p_long': pL, 'p_short': pS, 'p_noise': pN, 'signal': sig,
                    'long_thr': LONG_THR, 'short_thr': SHORT_THR, 'regime': regime_val,
                    'hurst': hurst, 'trend_str': trend_str, 'trend_dir': trend_dir}
        except Exception as e:
            print(f"[Bridge] ⚠️ predict error: {e}", flush=True)
            return None


class TCPServerThread(threading.Thread):
    """TCP szerver a Merkava EA-nak (MQL5 Socket protokoll)."""

    def __init__(self, host=TCP_HOST, port=TCP_PORT, on_tick_callback=None, on_connect_callback=None):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self.on_tick_callback = on_tick_callback
        self.on_connect_callback = on_connect_callback
        self.server_socket = None
        self.client_socket = None
        self.running = False
        self.buffer = ''
        self.tick_count = 0
        self.history_mode = False

    def run(self):
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        self.server_socket.settimeout(1.0)
        print(f"[Bridge] TCP szerver figyel: {self.host}:{self.port}", flush=True)
        print(f"[Bridge] Várakozás Merkava EA kapcsolódására...", flush=True)
        while self.running:
            if self.client_socket is None:
                try:
                    self.client_socket, addr = self.server_socket.accept()
                    self.client_socket.settimeout(0.5)
                    print(f"[Bridge] ✅ EA csatlakozott: {addr}", flush=True)
                    # EA csatlakozott → history újraolvasása (lehet, hogy frissült)
                    if self.on_connect_callback:
                        self.on_connect_callback()
                except socket.timeout:
                    continue
                except OSError:
                    break
            try:
                data = self.client_socket.recv(8192)
                if not data:
                    print(f"[Bridge] ❌ EA lekapcsolódott", flush=True)
                    self.client_socket.close()
                    self.client_socket = None
                    continue
                self.buffer += data.decode('utf-8', errors='replace')
                while '\n' in self.buffer:
                    line, self.buffer = self.buffer.split('\n', 1)
                    self.process_line(line.strip())
            except socket.timeout:
                continue
            except OSError:
                self.client_socket = None
                continue
        if self.client_socket:
            self.client_socket.close()
        if self.server_socket:
            self.server_socket.close()

    def process_line(self, line):
        if not line:
            return
        if line.startswith('HISTORY_START'):
            self.history_mode = True
            n = int(line.split('|')[1]) if '|' in line else 0
            print(f"[Bridge] History start ({n} ticks)", flush=True)
            return
        if line.startswith('HISTORY_END'):
            self.history_mode = False
            print(f"[Bridge] History end", flush=True)
            return
        if line.startswith('TICK|'):
            # Full EA payload: TICK|time_msc|bid|ask|pos_type|pos_price|pos_profit|av1|av2|bv1|bv2|ap1|ap2|bp1|bp2|res_mic|sup_mic|res_sec|sup_sec|res_ter|sup_ter
            parts = line.split('|')
            if len(parts) < 4: return
            try:
                time_msc = int(parts[1])
                bid = float(parts[2]); ask = float(parts[3])
                price = (bid + ask) / 2
                # Pozicio (comma-separated multi-pos)
                pos_types = [int(x) for x in parts[4].split(',')] if len(parts) > 4 and parts[4] != '0' else [0]
                pos_prices = [float(x) for x in parts[5].split(',')] if len(parts) > 5 and parts[5] != '0.0' else [0.0]
                pos_profit = float(parts[6]) if len(parts) > 6 else 0.0
                # DOM
                av1 = int(parts[7]) if len(parts) > 7 else 0
                av2 = int(parts[8]) if len(parts) > 8 else 0
                bv1 = int(parts[9]) if len(parts) > 9 else 0
                bv2 = int(parts[10]) if len(parts) > 10 else 0
                ap1 = float(parts[11]) if len(parts) > 11 else 0.0
                ap2 = float(parts[12]) if len(parts) > 12 else 0.0
                bp1 = float(parts[13]) if len(parts) > 13 else 0.0
                bp2 = float(parts[14]) if len(parts) > 14 else 0.0
                # Pivot/ZigZag
                res_mic = float(parts[15]) if len(parts) > 15 else 0.0
                sup_mic = float(parts[16]) if len(parts) > 16 else 0.0
                res_sec = float(parts[17]) if len(parts) > 17 else 0.0
                sup_sec = float(parts[18]) if len(parts) > 18 else 0.0
                res_ter = float(parts[19]) if len(parts) > 19 else 0.0
                sup_ter = float(parts[20]) if len(parts) > 20 else 0.0
                # Account info (balance, equity) — v3.0 EA küldi a payload végén
                balance = float(parts[21]) if len(parts) > 21 else 0.0
                equity = float(parts[22]) if len(parts) > 22 else 0.0
                self.tick_count += 1
                if self.on_tick_callback:
                    self.on_tick_callback(time_msc, price, bid, ask,
                        pos_types, pos_prices, pos_profit,
                        res_mic, sup_mic, res_sec, sup_sec, res_ter, sup_ter,
                        balance, equity)
            except (ValueError, IndexError):
                pass
            return
        if '|' in line and not line.startswith('TICK'):
            # History tick: time_msc|bid|ask
            parts = line.split('|')
            if len(parts) >= 3:
                try:
                    time_msc = int(parts[0])
                    bid = float(parts[1]); ask = float(parts[2])
                    price = (bid + ask) / 2
                    if self.on_tick_callback:
                        self.on_tick_callback(time_msc, price, bid, ask,
                            [0], [0.0], 0.0, 0,0,0,0,0,0)
                except (ValueError, IndexError):
                    pass
            return
    def stop(self):
        self.running = False
        if self.client_socket:
            try: self.client_socket.close()
            except: pass
        if self.server_socket:
            try: self.server_socket.close()
            except: pass


def load_history_init():
    """Load the 100 M1 bars from the EA's history_init.csv file.

    Az EA OnInit()-jében CopyRates(PERIOD_M1, 0, 100) → FileWrite.
    Formátum: time(unix sec),open,high,low,close
    Visszatér: list of dicts [{'time': 'YYYY-MM-DD HH:MM', 'open', 'high', 'low', 'close'}, ...]
    vagy None ha a fájl nem létezik/hibás.
    """
    if not os.path.exists(HISTORY_INIT_PATH):
        print(f"[Bridge] ⚠️ history_init.csv nem található: {HISTORY_INIT_PATH}", flush=True)
        return None
    try:
        df = pd.read_csv(HISTORY_INIT_PATH)
        bars = []
        for _, row in df.iterrows():
            dt = datetime.fromtimestamp(int(row['time']), tz=timezone.utc) - timedelta(hours=MT5_TZ_OFFSET)
            ts_str = dt.strftime('%Y-%m-%d %H:%M:%S')
            bars.append({
                'time': ts_str,
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
            })
        print(f"[Bridge] ✅ history_init.csv betöltve: {len(bars)} M1 gyertya "
              f"({bars[0]['time']} → {bars[-1]['time']})", flush=True)
        return bars
    except Exception as e:
        print(f"[Bridge] ⚠️ history_init.csv betöltési hiba: {e}", flush=True)
        return None


def build_msg(m1_ts_str, m1_candle, price, prediction, bid=None, ask=None, pos_types=None, pos_prices=None, pos_profit=0.0, res_mic=0.0, sup_mic=0.0, res_sec=0.0, sup_sec=0.0, res_ter=0.0, sup_ter=0.0, balance=0.0, equity=0.0):
    """Build the ZMQ JSON message for the HUD (normal + flip).

    m1_ts_str: M1 perc time ('YYYY-MM-DD HH:MM:SS') — a HUD chart time-ja
    m1_candle: {'open', 'high', 'low', 'close'} az aktuális M1 gyertya
    bid/ask: a tick bid/ask árak (a HUD bid_line-hoz)
    """
    msg = {'timestamp': m1_ts_str, 'ts': m1_ts_str, 'price': price,
           'open': m1_candle['open'],
           'high': m1_candle['high'],
           'low': m1_candle['low'],
           'close': m1_candle['close'],
           'bid': bid if bid is not None else price,
           'ask': ask if ask is not None else price,
           'pos_types': pos_types or [0], 'pos_prices': pos_prices or [0.0],
           'pos_profit': pos_profit,
           'balance': balance, 'equity': equity,
           'res_micro': res_mic, 'sup_micro': sup_mic,
           'res_sec': res_sec, 'sup_sec': sup_sec,
           'res_ter': res_ter, 'sup_ter': sup_ter}
    if prediction:
        msg['p_long'] = prediction['p_long']
        msg['p_short'] = prediction['p_short']
        msg['p_noise'] = prediction['p_noise']
        msg['signal'] = prediction['signal']
        msg['long_thr'] = prediction['long_thr']
        msg['short_thr'] = prediction['short_thr']
        msg['regime'] = prediction['regime']
        msg['hurst'] = prediction['hurst']
        msg['trend_str'] = prediction['trend_str']
        msg['trend_dir'] = prediction['trend_dir']
        # FLIP: p_long<->p_short, signal csere, threshold csere
        msg['p_long_flip'] = prediction['p_short']
        msg['p_short_flip'] = prediction['p_long']
        msg['p_noise_flip'] = prediction['p_noise']
        msg['signal_flip'] = -prediction['signal']
        msg['long_thr_flip'] = prediction['short_thr']
        msg['short_thr_flip'] = prediction['long_thr']
    else:
        msg.update({'p_long': 0.0, 'p_short': 0.0, 'p_noise': 0.0, 'signal': 0,
                   'long_thr': LONG_THR, 'short_thr': SHORT_THR,
                   'regime': 'neutral', 'hurst': 0.5, 'trend_str': 0.0, 'trend_dir': 0,
                   'p_long_flip': 0.0, 'p_short_flip': 0.0, 'p_noise_flip': 0.0,
                   'signal_flip': 0, 'long_thr_flip': SHORT_THR, 'short_thr_flip': LONG_THR})
    return msg


def main():
    print("=" * 60, flush=True)
    print("SCALPER V6 ONLINE BRIDGE — TCP szerver + LGBM élő predikció", flush=True)
    print("=" * 60, flush=True)
    predictor = V6LivePredictor()
    aggregator = DollarBarAggregator()      # $0.5M dollar bars (v6 predikcióhoz)
    m1_aggregator = M1BarAggregator()       # M1 gyertyák (MT5 chart másolat a HUD-nak)
    ctx = zmq.Context()
    pub = ctx.socket(zmq.PUB)
    pub.bind(f'tcp://*:{ZMQ_PORT}')
    print(f"[Bridge] ZMQ PUB figyel: tcp://*:{ZMQ_PORT}", flush=True)
    tick_count = [0]; bar_count = [0]

    def on_tick(ts_ms, price, bid, ask, pos_types, pos_prices, pos_profit, res_mic, sup_mic, res_sec, sup_sec, res_ter, sup_ter, balance=0.0, equity=0.0):
        tick_count[0] += 1
        # M1 gyertya aggregáció (MT5 chart másolat) — MINDEN tick-re
        m1_ts_str, m1_candle = m1_aggregator.add_tick(ts_ms, price)
        # Dollar bar aggregáció (v6 predikcióhoz)
        closed_bar = aggregator.add_tick(ts_ms, price)
        prediction = None
        if closed_bar is not None:
            bar_count[0] += 1
            bars_df = aggregator.get_bars_df()
            if bars_df is not None and len(bars_df) >= MIN_BARS_FOR_PREDICT:
                prediction = predictor.predict(bars_df)
        elif tick_count[0] % FORMING_BAR_PREDICT_EVERY == 0:
            bars_df = aggregator.get_bars_df()
            if bars_df is not None and len(bars_df) >= MIN_BARS_FOR_PREDICT:
                prediction = predictor.predict(bars_df)
        # MINDEN tick-re küldjük a chart update-et (M1 gyertya frissítése, mint az MT5)
        msg = build_msg(m1_ts_str, m1_candle, price, prediction, bid=bid, ask=ask, pos_types=pos_types, pos_prices=pos_prices, pos_profit=pos_profit, res_mic=res_mic, sup_mic=sup_mic, res_sec=res_sec, sup_sec=sup_sec, res_ter=res_ter, sup_ter=sup_ter, balance=balance, equity=equity)
        pub.send_string(f'HUD {json.dumps(msg)}')
        if tick_count[0] % 200 == 0 or closed_bar is not None:
            regime_str = prediction['regime'] if prediction else '---'
            print(f"[Bridge] tick={tick_count[0]} bar={bar_count[0]} "
                  f"price={price:.1f} m1={m1_ts_str} regime={regime_str} "
                  f"pL={msg.get('p_long',0):.3f} pS={msg.get('p_short',0):.3f} "
                  f"sig={msg.get('signal',0)}", flush=True)

    def init_aggregators_from_history():
        """Beolvassa a history_init.csv-t és inicializálja az aggregátorok állapotát.

        - M1BarAggregator: az utolsó M1 gyertyával (HUD chart másolat)
        - DollarBarAggregator: az összes M1 gyertyával rekonstruálva (azonnali predikció)

        A HUD maga olvassa a history_init.csv-t az első tick-nél (mint a v1.59 minta),
        így nincs ZMQ slow joiner probléma.
        """
        history_bars = load_history_init()
        if history_bars and len(history_bars) > 0:
            last_bar = history_bars[-1]
            m1_aggregator.init_from_last_bar(last_bar['time'], last_bar)
            print(f"[Bridge] ✅ M1Aggregator inicializálva: {len(history_bars)} gyertya "
                  f"(utolsó: {last_bar['time']} close={last_bar['close']:.1f})", flush=True)
            # Dollar bar rekonstrukció M1 history-ből (cold start → azonnali predikció)
            aggregator.init_from_history(history_bars)

    tcp_server = TCPServerThread(on_tick_callback=on_tick, on_connect_callback=init_aggregators_from_history)
    tcp_server.start()
    # Induláskor is inicializáljuk az aggregátorokat (ha a fájl már létezik)
    init_aggregators_from_history()

    def shutdown(sig, frame):
        print(f"\n[Bridge] Leállítás ({sig})...", flush=True)
        tcp_server.stop()
        pub.close()
        ctx.term()
        sys.exit(0)
    sig_mod.signal(sig_mod.SIGINT, shutdown)
    sig_mod.signal(sig_mod.SIGTERM, shutdown)
    print(f"\n[Bridge] 🚀 Készenlétben — várakozás EA tick-ekre...", flush=True)
    print(f"[Bridge] DOLLAR_THR=${DOLLAR_THR/1e6:.1f}M, RING={RING_BUFFER_SIZE}, "
          f"LONG_THR={LONG_THR}, SHORT_THR={SHORT_THR}", flush=True)
    print(f"[Bridge] TCP port={TCP_PORT} (EA), ZMQ port={ZMQ_PORT} (HUD)\n", flush=True)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown(sig_mod.SIGINT, None)


if __name__ == '__main__':
    main()
