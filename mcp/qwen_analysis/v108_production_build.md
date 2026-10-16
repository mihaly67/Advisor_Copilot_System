# v1.08 Production Build — 2026-10-02

## Áttörés: Alternatív irány-indikátor a labeling-ben

### Probléma (v1.06)
- Circ(Side, P(Long)-P(Short)) = 0.946 — modell követi az indikátort
- Side = Slope_Close_14 > 0 → label = Side × Meta → KÖRKÖRÖS

### Megoldás (v1.08)
- **Mom10_Direction** irány-indikátor a labeling-ben (Slope_Close_14 helyett)
- **PT=0.6$, SL=0.6$, maxb=5** szűk barrier (~5 perc)
- **p7 feature-k** (period=7)
- **Two-phase S1×S2** szűrés

### Eredmények

| Metrika | v1.06 | v1.08 | Változás |
|---------|-------|-------|----------|
| **WR** | 61.0% | **65.9%** | **+4.9%** |
| **Profit** | 10,555 | **12,581** | **+19%** |
| **Circ** | 0.946 | **0.713** | **-25%** |
| **Lag** | -8 | -9 | -1 |
| **WF Mean** | — | **69.0%±0.6%** | STABIL |
| **Leakage** | NO | **NO** | ✅ |

### Leakage Audit
- shift=0: 69.1% | shift=1: 69.1% | shift=2: 59.4% | shift=3: 56.0%
- **NO LEAKAGE**: shift=0 nem jobb mint shift=1

### Walk-Forward (5 fold)
- 69.2%, 69.5%, 68.6%, 69.8%, 68.0%
- Mean: 69.0%, StDev: 0.6% — rendkívül stabil

### Fájlok
- `/data/dev/projects/z-ai-copilot/models/production_v108/` — teljes production build
