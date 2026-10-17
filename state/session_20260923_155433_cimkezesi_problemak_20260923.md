# Session: cimkezesi_problemak_20260923
*Időbélyeg: 2026-09-23T15:54:33.885315*

Címkézési probléma: profitos pozíció menedzselése a kihívás. Vesztő egyértelmű (SL→zár). Profitos: PT elérése NEM=zárás, lehet tovább nő. 3× PT→új predikció+trailing. Visszaesések drawdown védelem. Megoldás: 4 rétegű exit (statikus TB→trailing→profit extenzio 3×PT→drawdown védelem). RAG: freqtrade trailing, kalshi dynamic exit (confidence-decay), mlfinlab aszimmetrikus PT/SL. Most: statikus TB labeler implementálása, később bővítés. Kutatás mentve: /data/Brain/_qwen_analysis/CIMKEZESI_PROBLEMA_KUTATAS_20260923.md