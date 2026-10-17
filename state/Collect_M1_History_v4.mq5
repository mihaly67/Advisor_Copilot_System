//+------------------------------------------------------------------+
//|                               Collect_M1_History.mq5             |
//|                        Z.ai Copilot — M1 gyertya CSV export      |
//|                                                                   |
//|  INSTRUMENT-FÜGGETLEN: _Symbol automatikus, fájlnév auto         |
//|  Ha InpSymbol="" → chart szimbólum (_Symbol)                     |
//|  Ha InpFileName="" → "M1_History_{SYMBOL}.csv" auto              |
//|  Decimal: SymbolInfoInteger(SYMBOL_DIGITS) alapján               |
//+------------------------------------------------------------------+
#property copyright "Z.ai Copilot"
#property version   "4.00"
#property strict
#property script_show_inputs

//--- Naptaros datum input (MT5 lenyilo naptart ad)
input datetime InpStartTime  = D'2024.01.01 00:00:00'; // Kezdo datum/idopont
input datetime InpEndTime    = D'2026.10.10 23:59:59'; // Zaro datum/idopont
input string   InpSymbol     = "";                     // Szimbolum (ures=_Symbol=chart)
input string   InpFileName   = "";                     // Kimenet (ures=auto: M1_History_{SYMBOL}.csv)

//+------------------------------------------------------------------+
//| History kényszerített letöltés                                   |
//+------------------------------------------------------------------+
bool ForceHistoryLoad(string sym, ENUM_TIMEFRAMES tf, datetime needed_from)
  {
   datetime first_date = 0;
   SeriesInfoInteger(sym, tf, SERIES_FIRSTDATE, first_date);
   Print("  Terminal cache elso datum: ",TimeToString(first_date,TIME_DATE|TIME_SECONDS));
   Print("  Kert kezdo datum: ",TimeToString(needed_from,TIME_DATE|TIME_SECONDS));

   if(first_date != 0 && first_date <= needed_from)
     {
      Print("  OK — cache eleg.");
      return true;
     }

   Print("  History letoltes indukalasa...");
   MqlRates rates[];
   int cnt = CopyRates(sym, tf, needed_from, 1000, rates);
   if(cnt > 0)
     {
      Print("  CopyRates sikerult: ",cnt," bar (",TimeToString(rates[0].time)," -> ",TimeToString(rates[cnt-1].time),")");
      SeriesInfoInteger(sym, tf, SERIES_FIRSTDATE, first_date);
      Print("  Uj cache elso datum: ",TimeToString(first_date,TIME_DATE|TIME_SECONDS));
      return true;
     }

   Print("  CopyRates datetime-al nem mukodik. Bars() letoltes...");
   int total = Bars(sym, tf);
   Print("  Bars() = ",total);
   if(total > 0)
     {
      cnt = CopyRates(sym, tf, 0, total, rates);
      Print("  CopyRates(0,",total,") = ",cnt);
      if(cnt > 0)
        {
         SeriesInfoInteger(sym, tf, SERIES_FIRSTDATE, first_date);
         Print("  Cache elso datum: ",TimeToString(first_date,TIME_DATE|TIME_SECONDS));
         return true;
        }
     }

   Print("  HIBA: History letoltes sikertelen!");
   return false;
  }

//+------------------------------------------------------------------+
//| Script program start function                                    |
//+------------------------------------------------------------------+
int OnStart()
  {
   //--- Instrument meghatarozasa
   string symbol = (InpSymbol == "") ? _Symbol : InpSymbol;
   SymbolSelect(symbol, true);

   //--- Fájlnév auto
   string filename = InpFileName;
   if(filename == "")
      filename = "M1_History_" + symbol + ".csv";

   //--- Decimal meghatarozasa (XAUUSD=5, BTCUSD=2, stb.)
   int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);

   if(InpStartTime >= InpEndTime)
     { Print("HIBA: Kezdo >= Zaro datum!"); return 1; }

   Print("============================================================");
   Print("  M1 GYERTYA GYUJTO v4.0 (instrument-fuggetlen)");
   Print("  Szimbolum: ",symbol," (digits=",digits,")");
   Print("  Kimenet: ",filename);
   Print("  Kezdes: ",TimeToString(InpStartTime,TIME_DATE|TIME_SECONDS));
   Print("  Zaras: ",TimeToString(InpEndTime,TIME_DATE|TIME_SECONDS));
   Print("============================================================");

   //--- History kényszerített letöltés
   if(!ForceHistoryLoad(symbol, PERIOD_M1, InpStartTime))
     { Print("  Folytatom megis, lehet van adat..."); }

   //--- Total bars elkerese
   int total_bars = Bars(symbol, PERIOD_M1);
   Print("  Total M1 bar a terminalban: ",total_bars);

   //--- Fajl megnyitas
   int handle = FileOpen(filename, FILE_WRITE|FILE_CSV|FILE_ANSI, ',');
   if(handle == INVALID_HANDLE)
     { Print("HIBA: FileOpen: ",GetLastError()); return 1; }
   FileWrite(handle, "Timestamp","Open","High","Low","Close","TickVolume");

   //--- Pozicio-alapu olvasas
   MqlRates rates[];
   int cnt = CopyRates(symbol, PERIOD_M1, 0, total_bars, rates);

   if(cnt <= 0)
     {
      Print("HIBA: CopyRates(0,",total_bars,") = ",cnt," error=",GetLastError());
      FileClose(handle);
      return 1;
     }

   Print("  CopyRates: ",cnt," bar olvasva");
   if(cnt > 0)
      Print("  Elso bar: ",TimeToString(rates[0].time,TIME_DATE|TIME_SECONDS));
   if(cnt > 1)
      Print("  Utolso bar: ",TimeToString(rates[cnt-1].time,TIME_DATE|TIME_SECONDS));

   //--- Szűrés + kiiras
   ulong written = 0;
   for(int i = 0; i < cnt; i++)
     {
      if(rates[i].time < InpStartTime) continue;
      if(rates[i].time > InpEndTime)   break;

      FileWrite(handle,
         TimeToString(rates[i].time, TIME_DATE|TIME_SECONDS),
         DoubleToString(rates[i].open,  digits),
         DoubleToString(rates[i].high,  digits),
         DoubleToString(rates[i].low,   digits),
         DoubleToString(rates[i].close, digits),
         IntegerToString(rates[i].tick_volume));
      written++;

      if(written % 100000 == 0)
         Print("  ",written," bar... (",TimeToString(rates[i].time,TIME_DATE|TIME_MINUTES),")");
     }

   FileClose(handle);

   //--- Osszefoglalo
   Print("============================================================");
   Print("  KESZ: ",filename);
   Print("  Szimbolum: ",symbol,"  Digits: ",digits);
   Print("  Kiirt M1 bar: ",written);
   Print("  Kezdes: ",TimeToString(InpStartTime,TIME_DATE|TIME_SECONDS));
   Print("  Zaras: ",TimeToString(InpEndTime,TIME_DATE|TIME_SECONDS));
   Print("============================================================");

   return 0;
  }
//+------------------------------------------------------------------+
