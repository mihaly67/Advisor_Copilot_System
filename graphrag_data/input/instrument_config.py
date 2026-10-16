"""
Instrument Configuration — NEVER hardcode parameters!
All values from concept_map.json → instruments[SYMBOL]
"""
from dataclasses import dataclass, field
from typing import Dict, Optional
import json
from pathlib import Path

CMAP_PATH = Path("/data/Brain/_qwen_analysis/concept_map.json")


@dataclass
class InstrumentConfig:
    """Configuration for a trading instrument."""
    symbol: str
    tick_size: float = 0.01
    point_value: float = 1.0
    pip_decimal_position: int = 2
    dollar_bar_threshold: float = 500_000
    bar_type: str = "dollar_bar"
    vol_method: str = "EWMA on returns, span=20"
    vol_span: int = 20
    tp_mult: float = 2.0
    sl_mult: float = 2.0
    profit_mult: float = 1.5
    stop_mult: float = 1.0
    vertical_barrier_bars: int = 50
    max_holding_bars: int = 20
    long_threshold: float = 0.45
    short_threshold: float = 0.50
    long_tc_bps: float = 10.0
    short_tc_bps: float = 20.0
    notes: str = ""
    
    @classmethod
    def from_concept_map(cls, symbol: str) -> 'InstrumentConfig':
        """Load config from concept_map.json → instruments[symbol]."""
        if CMAP_PATH.exists():
            with open(CMAP_PATH) as f:
                cm = json.load(f)
            inst = cm.get("instruments", {}).get(symbol, {})
            if inst:
                return cls(
                    symbol=inst.get("instrument", symbol),
                    tick_size=inst.get("tick_size", 0.01),
                    dollar_bar_threshold=inst.get("dollar_bar_threshold", 500_000),
                    tp_mult=inst.get("tp_mult", 2.0),
                    sl_mult=inst.get("sl_mult", 2.0),
                    vertical_barrier_bars=inst.get("vertical_barrier_bars", 50),
                    notes=inst.get("notes", ""),
                )
        return cls(symbol=symbol)
    
    def get_barrier_params(self) -> Dict:
        """Get TBM barrier parameters."""
        return {
            "profit_mult": self.profit_mult,
            "stop_mult": self.stop_mult,
            "max_bars": self.max_holding_bars,
            "vol_span": self.vol_span,
        }
    
    def get_sizing_params(self) -> Dict:
        """Get position sizing parameters."""
        return {
            "long_threshold": self.long_threshold,
            "short_threshold": self.short_threshold,
            "long_tc_bps": self.long_tc_bps,
            "short_tc_bps": self.short_tc_bps,
        }


# Convenience
def get_instrument(symbol: str) -> InstrumentConfig:
    return InstrumentConfig.from_concept_map(symbol)


if __name__ == "__main__":
    btc = get_instrument("BTCUSD")
    xau = get_instrument("XAUUSD")
    print(f"BTCUSD: dollar_bar={btc.dollar_bar_threshold}, TP={btc.tp_mult}σ, SL={btc.sl_mult}σ")
    print(f"XAUUSD: dollar_bar={xau.dollar_bar_threshold}, TP={xau.tp_mult}σ, SL={xau.sl_mult}σ")
    print(f"\nBTCUSD barrier params: {btc.get_barrier_params()}")
    print(f"XAUUSD barrier params: {xau.get_barrier_params()}")
