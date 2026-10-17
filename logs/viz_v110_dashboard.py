#!/usr/bin/env python3
"""viz_v110_dashboard.py — 4-config comparison dashboard"""
import pandas as pd, numpy as np, joblib, os, warnings
import plotly.graph_objects as go
from plotly.subplots import make_subplots
warnings.filterwarnings('ignore')

PROD='/data/dev/projects/z-ai-copilot/models/production_v110_jules'
PROC='/data/dev/projects/z-ai-copilot/Master_csv/processed'
OUT='/data/dev/projects/z-ai-copilot/docs/v110/viz_v110_dashboard.html'

PAL=dict(long='#228B22',short='#B22222',noise='#888888',bg='#111111',paper='#000000',grid='#333333',zero='#444444',font='white')

# Load once
m=joblib.load(os.path.join(PROD,'lgbm_v110_jules.pkl'))
feat=[l.strip() for l in open(os.path.join(PROD,'features.txt')) if l.strip()]
df=pd.read_csv(os.path.join(PROC,'jules_v110_labeled.csv'))
df['End_Timestamp']=pd.to_datetime(df['End_Timestamp'])
df.sort_values('End_Timestamp',inplace=True); df.reset_index(drop=True,inplace=True)
si=int(len(df)*0.8); oos=df.iloc[si:].copy().reset_index(drop=True)
X=oos[feat].fillna(0).replace([np.inf,-np.inf],0)
y=oos['Target_Label'].values; stoch=oos['Stoch_State_M1'].values; y3=(y+1).astype(int)
pr=m.predict_proba(X); cl=m.classes_
i_s=list(cl).index(0); i_n=list(cl).index(1); i_l=list(cl).index(2)
pL=pr[:,i_l]; pS=pr[:,i_s]; pN=pr[:,i_n]

CONFIGS=[
    dict(name='Original',thl=0.35,ths=0.36,thn=0.47,slk=0.0,ssk=0.0,sdz=0.0,sw=3),
    dict(name='Profit-opt',thl=0.3547,ths=0.3415,thn=0.5243,slk=-0.0448,ssk=0.1933,sdz=0.2937,sw=0),
    dict(name='WR-opt',thl=0.5019,ths=0.4712,thn=0.3098,slk=-0.2591,ssk=0.2858,sdz=0.3699,sw=4),
    dict(name='Balanced',thl=0.5051,ths=0.4648,thn=0.3290,slk=-0.2514,ssk=0.2732,sdz=0.3845,sw=4),
]

def apply_filters(pL,pS,pN,stoch,thl,ths,thn,slk,ssk,sdz,sw):
    sig=np.full(len(pL),1,dtype=int)
    sig[(pL>thl)&(pL>pS)&(pN<thn)]=2; sig[(pS>ths)&(pS>pL)&(pN<thn)]=0
    if sdz>0:
        outside=np.abs(stoch)>=sdz; sig_f=sig.copy()
        sig_f[(sig==2)&(stoch<slk)&outside]=1; sig_f[(sig==0)&(stoch>ssk)&outside]=1
    else:
        sig_f=sig.copy(); sig_f[(sig==2)&(stoch<slk)]=1; sig_f[(sig==0)&(stoch>ssk)]=1
    if sw>=2:
        sig_s=np.full(len(sig_f),1,dtype=int)
        for i in range(sw-1,len(sig_f)):
            w=sig_f[i-sw+1:i+1]
            if len(set(w))==1 and w[0]!=1: sig_s[i]=w[0]
    else: sig_s=sig_f
    return sig_s

def eval_sig(sig,y3):
    has=sig!=1; t=has.sum()
    if t==0: return dict(wr=0,trades=0,nl=0,ns=0,wr_l=0,wr_s=0,profit=0)
    wins=(sig[has]==y3[has]).sum(); losses=t-wins
    nl=(sig==2).sum(); ns=(sig==0).sum()
    lm=sig==2; sm=sig==0
    wr_l=(y3[lm]==2).mean()*100 if lm.sum()>0 else 0
    wr_s=(y3[sm]==0).mean()*100 if sm.sum()>0 else 0
    return dict(wr=wins/t*100,trades=t,nl=nl,ns=ns,wr_l=wr_l,wr_s=wr_s,profit=wins*1.5-losses)

# Evaluate all configs
results=[]
for c in CONFIGS:
    sig=apply_filters(pL,pS,pN,stoch,c['thl'],c['ths'],c['thn'],c['slk'],c['ssk'],c['sdz'],c['sw'])
    r=eval_sig(sig,y3)
    r['name']=c['name']; r['sig']=sig
    results.append(r)

# Build dashboard: 4 rows x 3 cols (bar chart, confusion, param table)
fig=make_subplots(rows=2,cols=2,shared_xaxes=False,
    subplot_titles=['WR összehasonlítás','Trade szám & L/S arány',
                    'Profit összehasonlítás','L_WR vs S_WR aszimmetria'],
    vertical_spacing=0.15, horizontal_spacing=0.12)

names=[r['name'] for r in results]
colors=['#888888','#228B22','#B22222','#FFD700']

# Panel 1: WR bars
fig.add_trace(go.Bar(x=names,y=[r['wr'] for r in results],
    marker_color=colors,text=[f'{r["wr"]:.1f}%' for r in results],
    textposition='outside',name='WR%'),row=1,col=1)

# Panel 2: Trades + L/S
fig.add_trace(go.Bar(x=names,y=[r['nl'] for r in results],
    marker_color='#228B22',name='Long',offsetgroup=0),row=1,col=2)
fig.add_trace(go.Bar(x=names,y=[r['ns'] for r in results],
    marker_color='#B22222',name='Short',offsetgroup=1),row=1,col=2)

# Panel 3: Profit
fig.add_trace(go.Bar(x=names,y=[r['profit'] for r in results],
    marker_color=colors,text=[f'{r["profit"]:.0f}' for r in results],
    textposition='outside',name='Profit'),row=2,col=1)

# Panel 4: L_WR vs S_WR
fig.add_trace(go.Bar(x=names,y=[r['wr_l'] for r in results],
    marker_color='#228B22',name='L_WR%',offsetgroup=0),row=2,col=2)
fig.add_trace(go.Bar(x=names,y=[r['wr_s'] for r in results],
    marker_color='#B22222',name='S_WR%',offsetgroup=1),row=2,col=2)

gc=dict(gridcolor=PAL['grid'],linecolor=PAL['zero'],zerolinecolor=PAL['zero'])
fig.update_layout(height=900,width=1400,
    title_text='Z.ai v1.10 Jules CFD — Optuna 4-config Dashboard',
    title_font=dict(size=16,color=PAL['font']),
    plot_bgcolor=PAL['bg'],paper_bgcolor=PAL['paper'],font=dict(color=PAL['font']),
    legend=dict(bgcolor='#222222',bordercolor='#333333',borderwidth=1,font=dict(color='white',size=11)),
    barmode='group',
    template=dict(layout=dict(xaxis=gc,yaxis=gc)))
for row in [1,2]:
    for col in [1,2]:
        fig.update_xaxes(**gc,row=row,col=col)
        fig.update_yaxes(**gc,row=row,col=col)

# Add annotation table
table_text = "│ Config     │  WR  │ Trades │  L   │  S   │ L_WR │ S_WR │ Profit │\n"
table_text+= "│────────────│──────│────────│──────│──────│──────│──────│────────│\n"
for r in results:
    table_text+= f"│ {r['name']:<10s} │ {r['wr']:4.1f}% │ {r['trades']:>6,} │ {r['nl']:>4,} │ {r['ns']:>4,} │ {r['wr_l']:4.1f}% │ {r['wr_s']:4.1f}% │ {r['profit']:>6.0f} │\n"

fig.add_annotation(text=table_text, xref='paper', yref='paper',
    x=0.5, y=-0.08, showarrow=False, font=dict(family='Courier New',size=10,color='#00FF00'),
    bgcolor='#111111',bordercolor='#333333',borderwidth=1)

os.makedirs(os.path.dirname(OUT),exist_ok=True)
fig.write_html(OUT,include_plotlyjs='cdn')
with open(OUT,'r') as f: html=f.read()
for old,new in [('"gridcolor":"white"','"gridcolor":"#333333"'),
                 ('"linecolor":"white"','"linecolor":"#444444"'),
                 ('"zerolinecolor":"white"','"zerolinecolor":"#444444"')]:
    html=html.replace(old,new)
with open(OUT,'w') as f: f.write(html)
sz=os.path.getsize(OUT)/1024
print(f'✅ Dashboard: {OUT} ({sz:.0f} KB)')

# Print full results
print(f'\n{"="*80}')
print(f'V1.10 JULES CFD — 4-CONFIG COMPARISON (FULL OOS)')
print(f'{"="*80}')
print(f'│ {"Config":<10s} │ {"WR":>5s} │ {"Trades":>6s} │ {"Long":>5s} │ {"Short":>5s} │ {"L_WR":>5s} │ {"S_WR":>5s} │ {"Profit":>7s} │')
print(f'│{"─"*12}│{"─"*7}│{"─"*8}│{"─"*7}│{"─"*7}│{"─"*7}│{"─"*7}│{"─"*9}│')
for r in results:
    print(f'│ {r["name"]:<10s} │ {r["wr"]:4.1f}% │ {r["trades"]:>6,} │ {r["nl"]:>5,} │ {r["ns"]:>5,} │ {r["wr_l"]:4.1f}% │ {r["wr_s"]:4.1f}% │ {r["profit"]:>7.0f} │')

# Confusion matrices
print(f'\n--- KONFÚZIÓS MÁTRIXOK ---')
for r in results:
    sig=r['sig']
    print(f'\n{r["name"]}:')
    print('           PredShort  PredNoise  PredLong')
    for al,an in [(0,'Short'),(1,'Noise'),(2,'Long')]:
        row=[f'{((y3==al)&(sig==pl)).sum():8,}' for pl in [0,1,2]]
        print(f'  Act{an:5s} {" ".join(row)}')
