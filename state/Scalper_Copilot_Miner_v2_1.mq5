//+------------------------------------------------------------------+
//|                      Scalper_Copilot_Miner_v2.mq5                |
//|                                              Jules (Agent)       |
//| MT5 tick CSV gyujto — INSTRUMENT-FÜGGETLEN                       |
//| V2.1: _Symbol auto, filename auto, digits auto                   |
//| Masodpercenkenti aggregacio + MTF Close + ATR + RSI + S/R        |
//| Kimeneti oszlopok (18):                                          |
//|   Timestamp, Bid, Ask, Bid_Volume, Ask_Volume, Spread,          |
//|   1m_Close, 5m_Close, 15m_Close, 30m_Close,                     |
//|   ATR_M15, RSI_M15,                                             |
//|   Micro_R, Sec_R, Ter_R, Micro_S, Sec_S, Ter_S                  |
//| FONTOS: Bid_Volume/Ask_Volume TENYLEGES!                        |
//| Ha volume_real=0 (CFD tipikus), tick-count proxy-t hasznal      |
//+------------------------------------------------------------------+
#property copyright "Jules"
#property version   "2.10"
#property strict
#property script_show_inputs

input datetime InpStartDate   = D'2026.06.16 00:00:00';
input datetime InpEndDate     = D'2026.10.10 23:59:59';
input string   InpFileName    = "";            // Kimenet (ures=auto: Scalper_Copilot_MTF_Data_v2_{SYMBOL}.csv)
input string   InpSymbol      = "";            // Szimbolum (ures=_Symbol=chart)
input bool     InpUseTickProxy = true;

//+------------------------------------------------------------------+
string FormatTime(ulong time_msc)
{
   datetime time_sec = (datetime)(time_msc / 1000);
   int msc = (int)(time_msc % 1000);
   return StringFormat("%s.%03d", TimeToString(time_sec, TIME_DATE|TIME_SECONDS), msc);
}

//+------------------------------------------------------------------+
bool ForceLoadHistory(string symbol, ENUM_TIMEFRAMES period, datetime start_date, datetime end_date)
{
   int max_wait = 100;
   while(!SeriesInfoInteger(symbol, period, SERIES_SYNCHRONIZED) && max_wait > 0 && !IsStopped())
   { Sleep(100); max_wait--; }
   MqlRates temp[];
   int copied = CopyRates(symbol, period, start_date, end_date, temp);
   max_wait = 50;
   while(copied <= 0 && max_wait > 0 && !IsStopped())
   { Sleep(200); copied = CopyRates(symbol, period, start_date, end_date, temp); max_wait--; }
   return (copied > 0);
}

//+------------------------------------------------------------------+
void AdvanceCursor(MqlRates &rates[], int count, datetime tick_time, int period_sec, int &idx)
{
   while(idx < count - 1 && (rates[idx + 1].time + period_sec) <= tick_time)
      idx++;
}

//+------------------------------------------------------------------+
void CalcSR(MqlRates &rates[], int count, int idx, int lookback, double &resistance, double &support)
{
   resistance = rates[idx].high;
   support    = rates[idx].low;
   int start  = MathMax(0, idx - lookback + 1);
   for(int i = start; i <= idx; i++)
   {
      if(rates[i].high > resistance) resistance = rates[i].high;
      if(rates[i].low  < support)    support    = rates[i].low;
   }
}

//+------------------------------------------------------------------+
void OnStart()
{
   string symbol = (InpSymbol == "") ? _Symbol : InpSymbol;
   SymbolSelect(symbol, true);

   //--- Fájlnév auto
   string filename = InpFileName;
   if(filename == "")
      filename = "Scalper_Copilot_MTF_Data_v2_" + symbol + ".csv";

   //--- Decimal meghatarozasa
   int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
   // CFD volume decimal: price digits + 3 (pl. XAUUSD: 5+3=8, BTCUSD: 2+3=5)
   int vol_digits = digits + 3;

   PrintFormat("Scalper Copilot Miner v2.1 | %s | digits=%d | vol_digits=%d", symbol, digits, vol_digits);
   PrintFormat("Kimenet: %s", filename);

   //--- MTF bar adatok betoltese (2 nap korabbi history a lookback-hez)
   datetime mtf_start = InpStartDate - (2 * 24 * 60 * 60);
   MqlRates rates_1m[], rates_5m[], rates_15m[], rates_30m[];
   ForceLoadHistory(symbol, PERIOD_M1,  mtf_start, InpEndDate);
   ForceLoadHistory(symbol, PERIOD_M5,  mtf_start, InpEndDate);
   ForceLoadHistory(symbol, PERIOD_M15, mtf_start, InpEndDate);
   ForceLoadHistory(symbol, PERIOD_M30, mtf_start, InpEndDate);
   int copied_1m  = CopyRates(symbol, PERIOD_M1,  mtf_start, InpEndDate, rates_1m);
   int copied_5m  = CopyRates(symbol, PERIOD_M5,  mtf_start, InpEndDate, rates_5m);
   int copied_15m = CopyRates(symbol, PERIOD_M15, mtf_start, InpEndDate, rates_15m);
   int copied_30m = CopyRates(symbol, PERIOD_M30, mtf_start, InpEndDate, rates_30m);
   PrintFormat("M1=%d M5=%d M15=%d M30=%d", copied_1m, copied_5m, copied_15m, copied_30m);

   //--- ATR + RSI indikatorok (M15)
   int atr_handle = iATR(symbol, PERIOD_M15, 14);
   int rsi_handle = iRSI(symbol, PERIOD_M15, 14, PRICE_CLOSE);
   if(atr_handle == INVALID_HANDLE || rsi_handle == INVALID_HANDLE)
   { Print("HIBA: Indikator handle!"); return; }
   int wait = 200;
   while(BarsCalculated(atr_handle) <= 0 && BarsCalculated(rsi_handle) <= 0 && wait > 0 && !IsStopped())
   { Sleep(100); wait--; }
   double atr_buf[], rsi_buf[];
   ArraySetAsSeries(atr_buf, false);
   ArraySetAsSeries(rsi_buf, false);
   int atr_copied = CopyBuffer(atr_handle, 0, mtf_start, InpEndDate, atr_buf);
   int rsi_copied = CopyBuffer(rsi_handle, 0, mtf_start, InpEndDate, rsi_buf);
   int atr_off = 0, rsi_off = 0;
   if(atr_copied > 0 && atr_copied < copied_15m) atr_off = copied_15m - atr_copied;
   if(rsi_copied > 0 && rsi_copied < copied_15m) rsi_off = copied_15m - rsi_copied;

   //--- Tick adatok betoltese
   ulong start_msc = (ulong)InpStartDate * 1000;
   ulong end_msc   = (ulong)InpEndDate   * 1000;
   MqlTick tick_array[];
   int total_ticks = CopyTicksRange(symbol, tick_array, COPY_TICKS_TRADE, start_msc, end_msc);
   if(total_ticks <= 0)
   {
      Print("TRADE=0, trying ALL...");
      total_ticks = CopyTicksRange(symbol, tick_array, COPY_TICKS_ALL, start_msc, end_msc);
   }
   if(total_ticks <= 0) { Print("Nincs tick!"); return; }
   PrintFormat("Osszes tick: %d", total_ticks);

   //--- CSV fajl nyitas
   int file_handle = FileOpen(filename, FILE_WRITE|FILE_CSV|FILE_ANSI, ',');
   if(file_handle == INVALID_HANDLE) { Print("Fajl hiba!"); return; }
   FileWrite(file_handle,
      "Timestamp,Bid,Ask,Bid_Volume,Ask_Volume,Spread,"
      "1m_Close,5m_Close,15m_Close,30m_Close,"
      "ATR_M15,RSI_M15,"
      "Micro_R,Sec_R,Ter_R,Micro_S,Sec_S,Ter_S");

   //--- Cursor es aggregacios valtozok
   int idx_1m=0, idx_5m=0, idx_15m=0, idx_30m=0;
   double c1=0, c5=0, c15=0, c30=0;
   datetime cur_sec=0;
   double b_bid=0, b_ask=0, b_bid_vol=0, b_ask_vol=0;
   int b_count=0, b_bid_ticks=0, b_ask_ticks=0;
   int written=0, ticks_with_vol=0, ticks_no_vol=0;
   int b_bid_ticks_total=0, b_ask_ticks_total=0;

   //--- FO CIKLUS: tick-enkenti feldolgozas, masodpercenkenti flush
   for(int i=0; i<total_ticks && !IsStopped(); i++)
   {
      long tick_s = tick_array[i].time_msc / 1000;
      datetime tick_dt = (datetime)tick_s;

      //--- MTF cursor elorebbites
      AdvanceCursor(rates_1m,  copied_1m,  tick_dt, 60,   idx_1m);
      AdvanceCursor(rates_5m,  copied_5m,  tick_dt, 300,  idx_5m);
      AdvanceCursor(rates_15m, copied_15m, tick_dt, 900,  idx_15m);
      AdvanceCursor(rates_30m, copied_30m, tick_dt, 1800, idx_30m);
      c1  = rates_1m[idx_1m].close;
      c5  = rates_5m[idx_5m].close;
      c15 = rates_15m[idx_15m].close;
      c30 = rates_30m[idx_30m].close;

      //--- S/R levels (15m, lookback=20)
      double micro_r, micro_s, sec_r, sec_s, ter_r, ter_s;
      CalcSR(rates_15m, copied_15m, idx_15m, 5,  micro_r, micro_s);
      CalcSR(rates_15m, copied_15m, idx_15m, 20, sec_r,  sec_s);
      CalcSR(rates_15m, copied_15m, idx_15m, 60, ter_r,  ter_s);

      //--- ATR/RSI cursor
      double atr_val = 0, rsi_val = 50;
      int a_idx = idx_15m - atr_off;
      if(a_idx >= 0 && a_idx < atr_copied) atr_val = atr_buf[a_idx];
      int r_idx = idx_15m - rsi_off;
      if(r_idx >= 0 && r_idx < rsi_copied) rsi_val = rsi_buf[r_idx];

      double spread = b_ask - b_bid;

      //--- Masodpercenkenti flush
      if(tick_s != cur_sec && cur_sec > 0)
      {
         //--- Tick-count proxy: ha valodi volume=0 (CFD tipikus)
         if(InpUseTickProxy && b_bid_vol==0 && b_ask_vol==0)
         {
            b_bid_vol = (double)b_bid_ticks;
            b_ask_vol = (double)b_ask_ticks;
         }

         FileWrite(file_handle, StringFormat(
            "%s,%.*f,%.*f,%.*f,%.*f,%.*f,%.*f,%.*f,%.*f,%.*f,%.*f,%.2f,%.*f,%.*f,%.*f,%.*f,%.*f,%.*f",
            FormatTime(cur_sec*1000),
            digits, b_bid, digits, b_ask,
            vol_digits, b_bid_vol, vol_digits, b_ask_vol,
            digits, spread,
            digits, c1, digits, c5, digits, c15, digits, c30,
            digits, atr_val, rsi_val,
            digits, micro_r, digits, sec_r, digits, ter_r,
            digits, micro_s, digits, sec_s, digits, ter_s));
         written++;
      }
      //--- Uj masodperc kezdes
      if(tick_s != cur_sec)
      {
         cur_sec     = tick_s;
         b_bid       = tick_array[i].bid;
         b_ask       = tick_array[i].ask;
         b_bid_vol   = 0;
         b_ask_vol   = 0;
         b_count     = 0;
         b_bid_ticks = 0;
         b_ask_ticks = 0;
      }

      //--- Bid/ask frissites (last tick)
      if(tick_array[i].bid > 0) b_bid = tick_array[i].bid;
      if(tick_array[i].ask > 0) b_ask = tick_array[i].ask;

      //--- Volume gyujtes (valodi vagy tick-count proxy)
      double tvol = tick_array[i].volume_real;
      if(tvol <= 0) tvol = (double)tick_array[i].volume;

      if(tvol > 0 && (tick_array[i].flags & TICK_FLAG_VOLUME) != 0)
      {
         ticks_with_vol++;
         if((tick_array[i].flags & TICK_FLAG_BUY)  != 0) b_ask_vol += tvol;
         else if((tick_array[i].flags & TICK_FLAG_SELL) != 0) b_bid_vol += tvol;
      }
      else
      {
         ticks_no_vol++;
      }

      //--- Tick-count proxy: CFD tick-ek szamlalasa BID/ASK flag alapjan
      bool has_buy  = ((tick_array[i].flags & TICK_FLAG_BUY)  != 0);
      bool has_sell = ((tick_array[i].flags & TICK_FLAG_SELL) != 0);
      bool has_bid  = ((tick_array[i].flags & TICK_FLAG_BID)  != 0);
      bool has_ask  = ((tick_array[i].flags & TICK_FLAG_ASK)  != 0);

      if(has_buy)        { b_ask_ticks++; b_ask_ticks_total++; }
      if(has_sell)       { b_bid_ticks++; b_bid_ticks_total++; }
      if(!has_buy && !has_sell)
      {
         if(has_bid)     { b_bid_ticks++; b_bid_ticks_total++; }
         if(has_ask)     { b_ask_ticks++; b_ask_ticks_total++; }
         if(!has_bid && !has_ask)
         {  b_bid_ticks++; b_ask_ticks++; b_bid_ticks_total++; b_ask_ticks_total++; }
      }

      b_count++;
   }

   //--- Takaritas
   FileClose(file_handle);
   IndicatorRelease(atr_handle);
   IndicatorRelease(rsi_handle);

   PrintFormat("Kesz! %s | %s | %d sor | Vol: %d | NoVol: %d | BidTicks: %d | AskTicks: %d",
               filename, symbol, written, ticks_with_vol, ticks_no_vol,
               b_bid_ticks_total, b_ask_ticks_total);
   if(ticks_with_vol == 0 && ticks_no_vol > 0)
      Print("MEGJEGYZES: volume_real=0! Tick-count proxy hasznalva.");
}
//+------------------------------------------------------------------+
