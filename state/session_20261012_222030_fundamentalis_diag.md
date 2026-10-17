# Session: fundamentalis_diag
*Időbélyeg: 2026-10-12T22:20:30.196942*

FUNDAMENTÁLIS DIAGNÓZIS + JAVÍTÁSOK

1. CÍMKÉZÉS HIBA (15.3% szennyezett):
   - Long/Short modellek NEM first-arrival: both esetén mindkettő label=1
   - 24K bar: Long=1 de Short hamarabb, 26K: Short=1 de Long hamarabb
   - Javítás: numba-ban first-arrival logika → AUC romlott (0.62→0.56)
   - Visszaállítva: eredeti címkézés (both=1,1) + combo first-arrival

2. TICK_SPEED DOMINANCIA (gain=111K, 4× második):
   - Tick_Speed corr(Long)=+0.133, corr(Short)=+0.125 — POZITÍV MINDKETTŐHÖZ
   - NEM irány-informált! Csak aktivitás/intenzitás
   - Long=1 de bar DOWN: 51.8% — label NEM korrelál bar irányával
   - Tick_Imbalance: FORDÍTOTTAN működik! Positive TI → 78.7% Short pred!

3. DIR MODELL (combo first-arrival: Long vs Short):
   - AUC=0.53, WR=52.8% — szinte random
   - BIZONYÍTJA: feature-ök NEM hordoznak elég irány-információt

4. NORMALIZÁLT P_norm = P(L)/(P(L)+P(S)):
   - Mean=0.496, std=0.044, range=[0.30, 0.68]
   - 44% Long, 56% Short — kiegyenlítettebb mint P(Long) vs P(Short)
   - Viz: egyetlen kék görbe + 0.5/0.45/0.55 küszöbök

5. ÚJ FEATURE-ÖK:
   - Tick_Imbalance = Tick_Speed * Bar_Sign (irányt hordozó sebesség)
   - Tick_Speed_Mean20 (simított aktivitás szint)

KÖVETKEZTETÉS: A feature-ök túlnyomórészt aktivitás/intenzitás, nem irány.
A P_norm normalizálás segít a Short dominancián, de az irány-felismerés
fundamentálisan limitált az jelenlegi feature-ökkel.