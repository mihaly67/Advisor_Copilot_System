# V5 CFD — Kódrészletek mentés (folytatáshoz)

## hud_v5_cfd.py — Subchart init blokk (aktuális állapot)

A /home/Jules/LGBM_mlops/HUD_Development/hud_v5_cfd.py ~155-195 sor:

```python
if not self.is_init:
    self.chart.set(pd.DataFrame([cd_data]))
    # Subchart line series init — MINDIG, nem csak has_pred!
    base_ts=raw_dt.floor('min')
    a0=(base_ts - pd.Timedelta(minutes=3)).strftime('%Y-%m-%d %H:%M:%S')
    a1=(base_ts - pd.Timedelta(minutes=2)).strftime('%Y-%m-%d %H:%M:%S')
    a2=(base_ts - pd.Timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M:%S')
    if has_pred:
        self.plong_line.set(pd.DataFrame([
            {'time':a0,'value':0.0},{'time':a1,'value':1.0},{'time':ts_str,'value':pl}
        ]))
        self.pshort_line.set(pd.DataFrame([{'time':ts_str,'value':ps}]))
    else:
        self.plong_line.set(pd.DataFrame([
            {'time':a0,'value':0.0},{'time':a1,'value':1.0},{'time':ts_str,'value':0.5}
        ]))
        self.pshort_line.set(pd.DataFrame([{'time':ts_str,'value':0.5}]))
    # Zajzóna alsó (0.425), felső (0.575), küszöb (0.50)
    self.noise_lo_line.set(pd.DataFrame([
        {'time':a0,'value':0.425},{'time':ts_str,'value':0.425}
    ]))
    self.noise_hi_line.set(pd.DataFrame([
        {'time':a0,'value':0.575},{'time':ts_str,'value':0.575}
    ]))
    self.thresh_line.set(pd.DataFrame([
        {'time':a0,'value':0.50},{'time':ts_str,'value':0.50}
    ]))
    self.is_init=True
```

Error handler (aktuális):
```python
except Exception as e:
    print(f"[HUD Error] {e}",flush=True)
```

---

## jules_cfd_v5.py — compute_features() (aktuális állapot)

```python
def compute_features(df, cusum_dir=None):
    """v5 features — CUSUM_Direction hozzáadva"""
    df=df.copy()
    hl=df['High']-df['Low']
    hc=np.abs(df['High']-df['Close'].shift(1))
    lc=np.abs(df['Low']-df['Close'].shift(1))
    tr=np.max(pd.concat([hl,hc,lc],axis=1),axis=1)
    atr14=tr.rolling(14).mean()+1e-8; cl=df['Close']
    if 'Micro_R' in df.columns:
        m1_atr=df['ATR_M15'].shift(1)+1e-8 if 'ATR_M15' in df.columns else atr14.shift(1)+1e-8
        df['Dist_Micro_R']=((df['Micro_R']-cl)/m1_atr).shift(1)
        df['Dist_Micro_S']=((cl-df['Micro_S'])/m1_atr).shift(1)
        df['Dist_Ter_R']=((df['Ter_R']-cl)/m1_atr).shift(1)
        df['Dist_Ter_S']=((cl-df['Ter_S'])/m1_atr).shift(1)
    hl2=df['High']-df['Low']
    df['Bar_Direction']=((df['Close']-df['Open'])/hl2.where(hl2>0,1e-8)).shift(1)
    df['Pulse_DF_Curve']=(df['Close'].diff(3)/atr14).shift(1)
    df['Price_Velocity']=(df['Close'].diff(1)/atr14).shift(1)
    dc=df['Close'].diff(1); gn=dc.where(dc>0,0).rolling(14).mean()
    dn=(-dc).where(dc<0,0).rolling(14).mean(); rs=gn/(dn+1e-8)
    df['Micro_RSI_14']=(100-100/(1+rs)).shift(1)
    for p,n in [(8,'Fast'),(21,'Medium')]:
        ema=df['Close'].ewm(span=p,adjust=False).mean()
        df[f'Trend_EMA_{n}_Dist']=((cl-ema)/atr14).shift(1)
    if cusum_dir is not None:
        raw_cd=pd.Series(cusum_dir,index=df.index)
        ff_cd=raw_cd.replace(0,np.nan).ffill().fillna(0)
        df['CUSUM_Direction']=ff_cd.shift(1)
    else:
        df['CUSUM_Direction']=0.0
    df['CUSUM_x_Bar']=df['CUSUM_Direction']*df['Bar_Direction']
    df['DF_Direction']=0.0; df['MACD_Direction']=0.0; df['Nav_Consensus']=0.0
    for f in FEAT_REGIME: df[f]=df[f].shift(1) if f in df.columns else 0.0
    df.replace([np.inf,-np.inf],np.nan,inplace=True)
    df[FEAT_NAMES]=df[FEAT_NAMES].fillna(0)
    return df
```

---

## KÖVETKEZŐ: compute_features() kiegészítése boolean/categorical feature-kkel

```python
# ÚJ Boolean feature-k (Phase 2-ben implementáljuk)
df['Above_Support'] = (df['Dist_Micro_S'] > 0).astype(int)
df['Near_Support'] = ((df['Dist_Micro_S'] > 0) & (df['Dist_Micro_S'] < 0.5)).astype(int)
df['Below_Resistance'] = (df['Dist_Micro_R'] > 0).astype(int)
df['Near_Resistance'] = ((df['Dist_Micro_R'] > 0) & (df['Dist_Micro_R'] < 0.5)).astype(int)
df['RSI_Oversold'] = (df['Micro_RSI_14'] < 30).astype(int)
df['RSI_Overbought'] = (df['Micro_RSI_14'] > 70).astype(int)
df['Bullish_Bar'] = (df['Bar_Direction'] > 0).astype(int)
df['Bearish_Bar'] = (df['Bar_Direction'] < 0).astype(int)
df['CUSUM_Up'] = (df['CUSUM_Direction'] > 0).astype(int)
df['CUSUM_Down'] = (df['CUSUM_Direction'] < 0).astype(int)
df['Trend_Up'] = (df['Trend_EMA_Fast_Dist'] > 0).astype(int)
df['Trend_Down'] = (df['Trend_EMA_Fast_Dist'] < 0).astype(int)

# Kontextus-kombinációk
df['Fade_Short_Setup'] = (df['CUSUM_Up'] & df['RSI_Overbought']).astype(int)
df['Bounce_Long_Setup'] = (df['CUSUM_Down'] & df['RSI_Oversold']).astype(int)
df['Trend_Resume_Long'] = (df['Trend_Up'] & df['Bullish_Bar'] & df['Above_Support']).astype(int)
df['Trend_Resume_Short'] = (df['Trend_Down'] & df['Bearish_Bar'] & df['Below_Resistance']).astype(int)
df['Breakdown'] = ((1 - df['Above_Support']) & df['CUSUM_Down']).astype(int)
df['Breakout'] = ((1 - df['Below_Resistance']) & df['CUSUM_Up']).astype(int)
```
