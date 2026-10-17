# Session: v109_jules_style
*Időbélyeg: 2026-10-03T09:57:37.947818*

v1.09 Jules-style: 10 features trained on Z.ai data → WR=52.2%, circ=0.565, acc=0.533. Jules v5 CANNOT be directly applied to Z.ai 1-min bar data (feature distribution mismatch → only Long). v1.08's 65 features are necessary for time bars. Adopt: stability filter + threshold logic + class_weight=balanced. Do NOT adopt: 10-feature set (too few for time bars). Next: v1.10 = v1.08 + Jules stability filter.