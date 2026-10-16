# V. FOCAL LOSS MATEMATIKA + Per-bar Label Design + Implementációs Terv

## 1. FOCAL LOSS — mély matematikai elemzés

### Standard Binary Cross-Entropy:

```
BCE(p, y) = -[y × log(p) + (1-y) × log(1-p)]

Ha y=1 (TP): L = -log(p)     → p=0.9: L=0.105  p=0.5: L=0.693
Ha y=0 (SL): L = -log(1-p)   → p=0.1: L=0.105  p=0.5: L=0.693

Gradiens:
  ∂L/∂p = -(y-p) / (p(1-p))
  
  Ha y=1, p=0.9: ∂L/∂p = -(1-0.9)/(0.9×0.1) = -1.11  (kicsi — már jól osztályozza)
  Ha y=1, p=0.1: ∂L/∂p = -(1-0.1)/(0.1×0.9) = -10.0   (NAGY — rosszul osztályozza)
```

### Class imbalance hatása BCE-re:

```
72 non-TP és 1 TP egy batch-ben:
  gradiens_TP  = -1.11  (1 db)
  gradiens_non = +0.11  (72 db)
  Σ gradiens   = -1.11 + 72×0.11 = -1.11 + 7.92 = +6.81
  
  → az ÖSSZES gradiens POZITÍV → a súly a non-TP felé mozdul!
  → a TP gradiens ELNYELODIK a 72 non-TP gradiensben!
  → a modell "megtanulja" hogy default = non-TP → p ≈ 0.014 mindig!
```

### Focal Loss:

```
FL(p, y) = -[α × (1-p_t)^γ × y × log(p) + (1-α) × p_t^γ × (1-y) × log(1-p)]

ahol p_t = p ha y=1, és (1-p) ha y=0

γ (gamma) = fókuszáló paraméter:
  γ=0: FL = BCE (visszaáll)
  γ=1: FL = -p_t × log(p_t)  (moderált fókusz)
  γ=2: FL = -p_t² × log(p_t)  (erős fókusz — AJÁNLOTT!)

α (alpha) = class súly:
  α = 0.25-0.75 (tipikusan 0.25 a minoritásos class-ra)
```

### γ=2 hatása a gradiensre:

```
Ha y=1 (TP):
  BCE gradiens:  -(1-p)
  FL gradiens:   -(1-p) × (1-p)² × [γ/(1-p) + 1]  = -(1-p)³ × [2/(1-p) + 1]
  
  p=0.9 (könnyű): BCE grad = -0.1     FL grad = -0.1³ × 21 = -0.021   (5× kisebb!)
  p=0.5 (közepes): BCE grad = -0.5    FL grad = -0.5³ × 5 = -0.625   (1.25× kisebb)
  p=0.1 (nehéz): BCE grad = -0.9     FL grad = -0.9³ × 3.22 = -2.34  (2.6× NAGYOBB!)

OK-okozat:
  → Focal Loss CSÖKKENTI a "könnyű" sample-ök gradiensét (72 non-TP!)
  → Focal Loss NÖVELI a "nehéz" sample-ök gradiensét (TP amiket rosszul osztályoz!)
  → a TP gradiens NEM elnyelődik!
  → a modell a NEHEZ TP-kre fókuszál → jobb TP predikció!
```

### α és γ együttes hatása:

```
α = class súly: mennyire "fontos" a minoritásos class
γ = fókusz: mennyire "ignoráljuk" a könnyű sample-öket

α=0.25, γ=2 (Lin et al. eredeti papír):
  → a minoritás 0.25 súllyal → de a fókusz kompenzálja
  → JO ha a minoritás NAGYON kicsi (<5%)

α=0.5, γ=2 (kiegyensúlyozott):
  → mindkét class egyenlő súly → a fókusz csak a nehézséget nézi
  → JO ha a class imbalance mérsékelt (10-30:1)

α=0.75, γ=2 (minoritás preferált):
  → a minoritás 3× nagyobb súllyal → agresszív
  → VESZÉLYES: overfitting a minoritásra!

KONKRÉTAN 72:1 imbalance:
  → α=0.25, γ=2: AJÁNLOTT (Lin et al.)
  → VAGY: α=0.5, γ=3: erősebb fókusz, kiegyensúlyozott súly
  → TESZTELJÜK MINDKETTŐT!
```

---

## 2. PER-BAR LABEL DESIGN — az alapvető kérdés

### Opció A: CUSUM event label (jelenlegi)

```
Minden dollár bar → van-e CUSUM event?
  Ha van ÉS TP → label = 1
  Ha van ÉS SL → label = 0 (vagy -1?)
  Ha NINCS event → label = ??? (nincs label!)

PROBLÉMA: a bar-ok 90%-án NINCS CUSUM event → NINCS label!
  → supervised learning NEM MŰKÖDIK label nélkül!
  → kell egy label a "nem-event" bar-okra is!
```

### Opció B: 3-class (Long/Short/None)

```
Minden bar → 3 class:
  label=2: CUSUM Long event ÉS TP
  label=1: CUSUM Short event ÉS TP
  label=0: NINCS event VAGY SL event

PROBLÉMA: class imbalance még rosszabb!
  label=2: ~1.4% (300 bar)
  label=1: ~0.4% (80 bar)
  label=0: ~98.2% (42,362 bar)
  → 3-class Focal Loss bonyolultabb
```

### Opció C: Binary — "profitable entry or not" (AJÁNLOTT)

```
Minden bar → 2 class:
  label=1: ha EZ a bar CUSUM event ÉS TP (Long VAGY Short)
  label=0: minden más

Class imbalance:
  label=1: 583 bar (1.4%)
  label=0: 42,159 bar (98.6%)
  → 72:1 → Focal Loss kezelheti!

DE: ez csak azt mondja "van-e profitable entry", nem a irányt!
  → a LGBM Long/Short külön modell → irány már megvan!
  → az MLP csak a META-LABEL-t erősíti: "ez az entry jó-e?"
```

### Opció D: Separate Long/Short binary (LEGJOBB!)

```
KÉT külön modell:
  MLP_Long: label=1 ha CUSUM Long TP, label=0 minden más
  MLP_Short: label=1 ha CUSUM Short TP, label=0 minden más

MLP_Long imbalance:
  label=1: ~300 bar (0.7%)
  label=0: ~42,442 bar (99.3%)
  → 141:1 → Focal Loss γ=3 kell!

MLP_Short imbalance:
  label=1: ~80 bar (0.2%)
  label=0: ~42,662 bar (99.8%)
  → 533:1 → TÚL sok! → oversampling kell!

KÖVETKEZMÉNY: Short MLP nagyon nehéz → kevés TP!
  → LEHET hogy csak Long MLP-t építünk először
  → Short MLP később, több adattal
```

### Opció E: Window-based label (sliding window)

```
Minden bar → mi történik a következő W bar-ban?
  label=1: ha a következő W bar-ban PT elért (Long entry)
  label=0: ha SL elért VAGY semmi

ELŐNY: nem kell CUSUM event! Minden bar-ra van label!
HÁTRÁNY: lookahead! A label JÖVŐbeli adatot használ!
  → de ez PONTOSAN a meta-label definíció (jogosult)!
  → a TRAINING-hez OK, de a PREDIKCIÓHOZ nem (mert nem tudjuk a jövőt)

MEGOLDÁS: predikciókor csak a feature-öket használjuk, a label-t nem!
  → a label csak training-kor létezik
  → predikciókor: MLP(features) → p = "valószínűség hogy PT lesz"
  → ez PONTOSAN a meta-model!
```

### DÖNTÉS: Opció C (binary meta-label) + később Opció D (separate)

```
Először: binary "profitable entry?" model
  → egyszerűbb, több TP sample (583 vs 300)
  → Focal Loss γ=2 kezelheti a 72:1
  → ha működik → separate Long/Short
```

---

## 3. KONKRÉT IMPLEMENTÁCIÓS TERV — lépésről lépésre

### Lépés 1: Feature redukció + RankGauss normalizáció

```python
# 1. Feature szűrés: 32 → 18
KEEP_FEATURES = [
    'body_sign_f', 'consecutive_f', 'vol_ratio_f', 'ticks_inv_f',
    'RSI_3_f', 'RSI_5_f', 'Slope_3_f', 'ema8_gap_f',
    'above_ema8_f', 'above_ema20_f', 'PastRet_1_f', 'PastRet_2_f',
    'vol_calm_f', 'body_ratio_f', 'wick_u_r_f', 'wick_l_r_f',
    'Conviction_Bar_f', 'Fast_Bar_f'
]

# 2. RankGauss transzformáció
from scipy.special import erfinv

def rankgauss(x, eps=1e-6):
    """Rank → Inverse Gaussian CDF → N(0,1)"""
    rank = x.rank() / (len(x) + 1)  # uniform (0,1)
    rank = rank.clip(eps, 1-eps)     # clamp → bounded!
    z = erfinv(2 * rank - 1) * np.sqrt(2)  # → N(0,1)
    return z

# 3. RSI centring: (RSI - 50) / 50 → [-1, +1]
```

### Lépés 2: Per-bar dataset építés

```python
class PerBarDataset(Dataset):
    def __init__(self, features, labels, window=1):
        self.X = features  # (N, 18) after RankGauss
        self.y = labels    # (N,) binary meta-label
        self.window = window
    
    def __len__(self):
        return len(self.X) - self.window + 1
    
    def __getitem__(self, idx):
        if self.window == 1:
            x = self.X[idx]  # (18,)
        else:
            x = self.X[idx:idx+self.window].flatten()  # (18*W,)
        y = self.y[idx + self.window - 1]
        return torch.tensor(x, dtype=torch.float32), torch.tensor(y, dtype=torch.float32)
```

### Lépés 3: Focal Loss

```python
class FocalLoss(nn.Module):
    def __init__(self, alpha=0.25, gamma=2.0):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
    
    def forward(self, p, y):
        # p: predicted probability [0,1], y: label {0,1}
        p = p.clamp(1e-6, 1-1e-6)  # numerical stability
        p_t = p * y + (1-p) * (1-y)  # p if y=1, (1-p) if y=0
        
        # Focal weight
        focal_weight = (1 - p_t) ** self.gamma
        
        # Alpha weight
        alpha_weight = self.alpha * y + (1-self.alpha) * (1-y)
        
        # BCE
        bce = -torch.log(p_t)
        
        return (alpha_weight * focal_weight * bce).mean()
```

### Lépés 4: MLP architektúra

```python
class V11MLP(nn.Module):
    def __init__(self, input_dim=18, hidden=16, layers=2, dropout=0.3):
        super().__init__()
        self.net = nn.ModuleList()
        
        # Input layer + BatchNorm
        self.net.append(nn.Linear(input_dim, hidden))
        self.bn = nn.BatchNorm1d(hidden)
        
        # Hidden layers
        for _ in range(layers - 1):
            self.net.append(nn.Linear(hidden, hidden))
        
        # Output
        self.out = nn.Linear(hidden, 1)
        self.dropout = nn.Dropout(dropout)
        self.act = nn.LeakyReLU(0.01)  # nem dying!
    
    def forward(self, x):
        for i, layer in enumerate(self.net):
            residual = x if i > 0 and x.shape[-1] == layer.out_features else None
            x = layer(x)
            if i == 0: x = self.bn(x)
            x = self.act(x)
            x = self.dropout(x)
            if residual is not None: x = x + residual  # skip connection
        return torch.sigmoid(self.out(x)).squeeze(-1)
```

### Lépés 5: Overfitting detektálás — MIND a 6 módszer

```python
# 1. Train/Val gap — early stopping
# 2. Purged walk-forward CV — 5 fold, embargo=10
# 3. Learning curve — 20%, 40%, 60%, 80%, 100%
# 4. Label permutation test — 100 shuffle
# 5. Bootstrap CI — 30 model
# 6. Dropout sensitivity — p=0, 0.3, 0.5
```

### Lépés 6: Diszkrepancia rendszer

```python
def predict_bar(features_bar):
    # LGBM
    p_lgbm = lgbm_model.predict_proba(features_bar)[1]
    
    # MLP (RankGauss normalizált)
    features_rg = rankgauss_transform(features_bar)
    p_mlp = mlp_model(torch.tensor(features_rg)).item()
    
    # Diszkrepancia
    delta = p_lgbm - p_mlp
    
    # Döntés
    if abs(delta) > 0.20:  # nagy diszkrepancia
        flag = f"⚠️ LGBM={p_lgbm:.2f} MLP={p_mlp:.2f} Δ={delta:+.2f}"
    else:
        flag = None
    
    return {
        'p_lgbm': p_lgbm,
        'p_mlp': p_mlp,
        'delta': delta,
        'disagreement': flag
    }
```

---

## TESZTELÉSI SORREND — minden lépést ALAPOSAN!

```
1. RankGauss validáció:
   → transzformáljuk a 18 feature-t
   → ellenőrizzük: mean≈0, std≈1, nincs ∞, nincs NaN
   → OOS: clip [0.001, 0.999] → bounded

2. Feature korreláció validáció:
   → RankGauss UTÁN: corr mátrix → nincs |ρ|>0.9!
   → ha még van → dobjuk el a második feature-t

3. Label permutation test ELŐSZÖR:
   → tanítunk y_shuffled → AUC_random
   → tanítunk y_original → AUC_real
   → HA AUC_real >> AUC_random → VAN signal → folytathatjuk
   → HA AUC_real ≈ AUC_random → NINCS signal → DESIGN HIBA!

4. Learning curve:
   → 20%, 40%, 60%, 80%, 100% adat → val_AUC
   → hol telítődik? → optimális adat mennyiség

5. Dropout sensitivity:
   → p=0, 0.3, 0.5 → melyik a legjobb val_AUC?

6. Purged CV:
   → 5 fold, embargo=10 → OOS AUC és PnL

7. Train/Val gap:
   → tanítás közben → early stopping → optimális epoch

8. Bootstrap CI:
   → 30 modell → predikció CI → bizonytalanság kvantifikálás

9. Diszkrepancia:
   → LGBM vs MLP → milyen gyakran nem értenek egyet?
   → amikor nem → melyiknek van igaza?
```
