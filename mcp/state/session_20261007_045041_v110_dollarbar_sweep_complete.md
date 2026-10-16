# Session: v110_dollarbar_sweep_complete
*Időbélyeg: 2026-10-07T04:50:41.352500*

Dollar bar sweep COMPLETE. 8 configs tested on CFD data (correct CSVs).

RESULTS TABLE (sorted by OOS WR):
1. $444K-adapt-18f-MB8:  OOS=49.4% P=$113 T=482  | Viz=46.7% P=$38 T=227  | Gap=+2.7% ✅ STABLE
2. $444K-adapt-18f-MB5:  OOS=49.0% P=$120 T=537  | Viz=44.4% P=$25 T=225  | Gap=+4.6%
3. $654K-adapt-18f-MB8:  OOS=44.3% P=$66  T=619  | Viz=39.9% P=-$0 T=283  | Gap=+4.4%
4. $654K-adapt-18f-MB5:  OOS=44.1% P=$32  T=311  | Viz=37.1% P=-$10 T=143 | Gap=+7.0%
5. $888K-adapt-18f-MB8:  OOS=40.9% P=$12  T=540  | Viz=40.4% P=$3  T=267  | Gap=+0.5% ✅ STABLE
6. $888K-adapt-18f-MB5:  OOS=40.3% P=$2   T=310  | Viz=32.7% P=-$29 T=159 | Gap=+7.6%
7. $1.7M-adapt-18f-MB5:  OOS=34.8% P=-$40 T=310  | Viz=27.2% P=-$50 T=158 | Gap=+7.6%
8. $1.7M-adapt-18f-MB8:  OOS=34.2% P=-$55 T=380  | Viz=30.2% P=-$49 T=199 | Gap=+4.0%

VOLBAR REFERENCE: volbar_3_PT1.5_SL1.0_MB8 OOS=50.8% Viz=51.7% Gap=-0.9%

KEY FINDINGS:
- $444K is clearly best dollar bar threshold for CFD (OOS=49.4%, Viz=46.7%)
- Larger thresholds = worse performance (monotonic decline from $444K to $1.7M)
- $1.7M threshold (from futures calibration) is TERRIBLE on CFD: OOS=34.2%, Viz=30.2%
- $888K-MB8 interesting: low WR but Gap=+0.5% (most stable gap)
- Dollar bar still underperforms volbar (49.4% vs 50.8% OOS, 46.7% vs 51.7% Viz)
- MB8 consistently better than MB5 for dollar bars

8 HTML visualizations generated in /docs/v110_dollarbar/
Results JSON saved to /docs/v110_dollarbar/dollarbar_sweep_results.json