# Session: v12_opt6_complete
*Időbélyeg: 2026-10-10T17:35:54.296137*

V12 opt6: MLP scaled to hidden=64, layers=4, dropout=0.1. valAUC=0.825 (+4.7% vs opt5 0.788). perm_z=39.2. 14,721 params. CosineAnnealingWarmRestarts scheduler. torch.compile NOT available on P4000 Pascal (sm_61 < 7.0, Triton needs >=7.0). Learning curve still shows underfitting - more data would help. Time=939s same as opt5.