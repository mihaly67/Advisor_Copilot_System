#!/usr/bin/env python3
"""Visual Analysis: Plotly chart adatokbol vizualis elemzo HTML generalas."""
import json, math

def generate_visual_analysis(plot_data: dict, output_path: str = None) -> dict:
    plots = plot_data.get("plots", {})
    price_trace = long_probs = short_probs = long_signals = short_signals = None
    for pid, pdata in plots.items():
        if pid == "_meta": continue
        for t in pdata.get("traces", []):
            nm, tp = t.get("name","").lower(), t.get("type","")
            if tp == "candlestick" and not price_trace: price_trace = t
            elif tp == "scatter":
                if "p(dir=long)" in nm or "p(dir" in nm: long_probs = t
                elif "p_norm" in nm or "pnorm" in nm:
                    if not long_probs: long_probs = t
                if "long sig" in nm or "long_sig" in nm: long_signals = t
                if "short sig" in nm or "short_sig" in nm: short_signals = t
    prob_trace = long_probs or short_probs
    dom = _dominance(prob_trace)
    csig = _counter_signals(long_signals, short_signals, dom)
    aanom = _amplitude_anomalies(prob_trace)
    rovlp = _range_overlap(long_signals, short_signals)
    html = _build_html(prob_trace, long_signals, short_signals, dom, csig, aanom, rovlp)
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f: f.write(html)
    return {"html_length": len(html), "output_path": output_path,
            "dominance": dom, "counter_signals": csig,
            "amplitude_anomalies": aanom, "range_overlap": rovlp}

def _dominance(pt):
    d = {"long_pct":0,"short_pct":0,"neutral_pct":0,"sections":[],"transitions":0}
    if not pt or not pt.get("y"): return d
    y=[v for v in pt["y"] if v is not None]; n=len(y)
    if n==0: return d
    lc=sum(1 for v in y if v>0.5); sc=sum(1 for v in y if v<0.5)
    d["long_pct"]=round(100*lc/n,1); d["short_pct"]=round(100*sc/n,1)
    d["neutral_pct"]=round(100*(n-lc-sc)/n,1)
    cur="long" if y[0]>0.5 else "short"; ss=0
    for i in range(1,n):
        nm="long" if y[i]>0.5 else "short"
        if nm!=cur:
            d["sections"].append({"type":cur,"start_idx":ss,"end_idx":i-1,"length":i-ss})
            cur=nm; ss=i
    d["sections"].append({"type":cur,"start_idx":ss,"end_idx":n-1,"length":n-ss})
    d["transitions"]=len(d["sections"])-1; return d

def _counter_signals(ls,ss,dom):
    cs={"count":0,"long_in_short_domain":0,"short_in_long_domain":0}
    if ls:
        ly=[v for v in (ls.get("y")or[])if v is not None]
        cs["long_in_short_domain"]=int(len(ly)*dom.get("short_pct",50)/100)
        cs["count"]+=cs["long_in_short_domain"]
    if ss:
        sy=[v for v in (ss.get("y")or[])if v is not None]
        cs["short_in_long_domain"]=int(len(sy)*dom.get("long_pct",50)/100)
        cs["count"]+=cs["short_in_long_domain"]
    return cs

def _amplitude_anomalies(pt):
    aa={"count":0,"sections":[]}
    if not pt or not pt.get("y"): return aa
    y=[v for v in pt["y"] if v is not None]; n=len(y)
    if n<20: return aa
    mean=sum(y)/n; std=math.sqrt(sum((v-mean)**2 for v in y)/n) if n>1 else 1
    if std<=0: return aa
    w=max(20,n//50); ib=False; bs=0
    for i in range(n-w+1):
        cm=sum(y[i:i+w])/w; z=abs(cm-mean)/std
        if z>1.5:
            if not ib: bs=i; ib=True
        else:
            if ib:
                aa["sections"].append({"start_idx":bs,"end_idx":i,"length":i-bs,
                    "direction":"long_burst"if y[(bs+i)//2]>0.5 else"short_burst"})
                aa["count"]+=1; ib=False
    if ib:
        aa["sections"].append({"start_idx":bs,"end_idx":n-1,"length":n-bs,
            "direction":"long_burst"if y[-1]>0.5 else"short_burst"})
        aa["count"]+=1
    return aa

def _range_overlap(ls,ss):
    ro={"long_range":None,"short_range":None,"overlap_pct":0,"long_spread":0,"short_spread":0}
    if not ls or not ss: return ro
    ly=[v for v in(ls.get("y")or[])if v is not None]
    sy=[v for v in(ss.get("y")or[])if v is not None]
    if not ly or not sy: return ro
    lmn,lmx,mn,sx=min(ly),max(ly),min(sy),max(sy)
    ro["long_range"]=[round(lmn,2),round(lmx,2)]; ro["short_range"]=[round(mn,2),round(sx,2)]
    ro["long_spread"]=round(lmx-lmn,2); ro["short_spread"]=round(sx-mn,2)
    om,ox=max(lmn,mn),min(lmx,sx)
    if ox>om:
        t=max(lmx,sx)-min(lmn,mn)
        ro["overlap_pct"]=round(100*(ox-om)/t,1) if t>0 else 0
    return ro

def _build_html(pt, ls, ss, dom, csig, aanom, rovlp):
    P=[]
    BG="paper_bgcolor:'#1a1a2e',plot_bgcolor:'#16213e',font:{color:'#e0e0e0'}"
    P.append('<!DOCTYPE html><html lang="hu"><head><meta charset="UTF-8">'
      '<title>Predikcio Vizualis Elemzes</title>'
      '<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>'
      '<style>'
      'body{font-family:"Segoe UI",sans-serif;background:#1a1a2e;color:#e0e0e0;margin:0;padding:20px}'
      'h1{color:#00d4ff;border-bottom:2px solid #00d4ff;padding-bottom:10px}'
      'h2{color:#ff6b6b;margin-top:30px}'
      '.card{background:#16213e;border-radius:12px;padding:20px;margin:15px 0;border:1px solid #0f3460}'
      '.card h3{color:#00d4ff;margin-top:0}'
      '.stat{display:inline-block;margin:8px 15px;font-size:1.1em}'
      '.stat .val{font-weight:bold;font-size:1.4em}'
      '.long{color:#00ff88}.short{color:#ff4466}.neutral{color:#ffaa00}.anomaly{color:#ff6b6b}'
      '.chart-container{margin:20px 0}'
      '</style></head><body><h1>🔮 Predikcio Vizualis Elemzes</h1>')
    P.append(f'<div class="card"><h3>📊 Dominancia</h3>'
      f'<div class="stat"><span class="long">Long: <span class="val">{dom["long_pct"]}%</span></span></div>'
      f'<div class="stat"><span class="short">Short: <span class="val">{dom["short_pct"]}%</span></span></div>'
      f'<div class="stat"><span class="neutral">Neutral: <span class="val">{dom["neutral_pct"]}%</span></span></div>'
      f'<div class="stat">Valtasok: <span class="val">{dom["transitions"]}</span></div></div>'
      f'<div class="card"><h3>⚠️ Ellentrenjelzesek</h3>'
      f'<div class="stat">Osszes: <span class="val anomaly">{csig["count"]}</span></div>'
      f'<div class="stat"><span class="long">L→Short: <span class="val">{csig["long_in_short_domain"]}</span></span></div>'
      f'<div class="stat"><span class="short">S→Long: <span class="val">{csig["short_in_long_domain"]}</span></span></div></div>'
      f'<div class="card"><h3>📈 Amplitudo Anomaliak</h3>'
      f'<div class="stat">Burst-ek: <span class="val anomaly">{aanom["count"]}</span></div></div>'
      f'<div class="card"><h3>🔄 Tartomeny Fedes</h3>'
      f'<div class="stat"><span class="long">Long: <span class="val">{rovlp["long_range"]}</span> (spread:{rovlp["long_spread"]})</span></div>'
      f'<div class="stat"><span class="short">Short: <span class="val">{rovlp["short_range"]}</span> (spread:{rovlp["short_spread"]})</span></div>'
      f'<div class="stat">Fedes: <span class="val">{rovlp["overlap_pct"]}%</span></div></div>')
    cid=[0]
    def nid():
        cid[0]+=1; return cid[0]
    _add_charts(P,nid,pt,ls,ss,dom,aanom,rovlp,BG)
    P.append('</body></html>')
    return "\n".join(P)

def _add_charts(P,nid,pt,ls,ss,dom,aanom,rovlp,BG):
    # 1. Predikcios gorbe + dominancia
    if pt and pt.get("y"):
        c=nid(); yj=json.dumps(pt["y"])
        P.append(f'''<div class="chart-container"><h2>1. P(DIR=Long) + Dominancia</h2><div id="ch{c}"></div></div>
<script>
var y={yj},x=Array.from({{length:y.length}},(_,i)=>i);
var t1={{x,y,type:'scatter',mode:'lines',name:'P(DIR=Long)',line:{{color:'#00d4ff',width:2}}}};
var t2={{x:[x[0],x[x.length-1]],y:[0.5,0.5],type:'scatter',mode:'lines',name:'Threshold',line:{{color:'#ffaa00',width:1,dash:'dash'}}}};
var lX=[],lY=[],sX=[],sY=[];
for(var i=0;i<y.length;i++){{
  if(y[i]!=null&&y[i]>0.5){{lX.push(x[i]);lY.push(y[i])}}else{{if(lX.length>0){{lX.push(null);lY.push(null)}}}}
  if(y[i]!=null&&y[i]<0.5){{sX.push(x[i]);sY.push(y[i])}}else{{if(sX.length>0){{sX.push(null);sY.push(null)}}}}
}}
var t3={{x:lX,y:lY,type:'scatter',mode:'lines',fill:'tozeroy',name:'Long dom.',line:{{width:0}},fillcolor:'rgba(0,255,136,0.15)'}};
var t4={{x:sX,y:sY,type:'scatter',mode:'lines',fill:'tozeroy',name:'Short dom.',line:{{width:0}},fillcolor:'rgba(255,68,102,0.15)'}};
Plotly.newPlot('ch{c}',[t3,t4,t1,t2],{{{BG},title:{{text:'P(DIR=Long) — Zold=Long, Piros=Short',font:{{color:'#e0e0e0'}}}},xaxis:{{title:'Ido index',gridcolor:'#333'}},yaxis:{{title:'P(DIR=Long)',gridcolor:'#333',range:[0,1]}},height:400,margin:{{t:50,b:50}}}},{{responsive:true}});
</script>''')
    # 2. Signal scatter overlay
    if ls and ss:
        c=nid(); ly=ls.get("y",[]); sy=ss.get("y",[])
        lx,sx=list(range(len(ly))),list(range(len(sy)))
        P.append(f'''<div class="chart-container"><h2>2. Signal Elheleyzkedes (Ar-tartomany)</h2><div id="ch{c}"></div></div>
<script>
var tL={{x:{json.dumps(lx)},y:{json.dumps(ly)},type:'scatter',mode:'markers',name:'Long ({len(ly)} db)',marker:{{color:'#00ff88',size:6,opacity:0.7}}}};
var tS={{x:{json.dumps(sx)},y:{json.dumps(sy)},type:'scatter',mode:'markers',name:'Short ({len(sy)} db)',marker:{{color:'#ff4466',size:6,opacity:0.7}}}};
Plotly.newPlot('ch{c}',[tL,tS],{{{BG},title:{{text:'Long 🟢 vs Short 🔴 Signal Arak',font:{{color:'#e0e0e0'}}}},xaxis:{{title:'Ido',gridcolor:'#333'}},yaxis:{{title:'Ar ($)',gridcolor:'#333'}},height:400,margin:{{t:50,b:50}}}},{{responsive:true}});
</script>''')
    # 3. Tartomany hisztogram
    if ls and ss:
        ly=[v for v in(ls.get("y")or[])if v is not None]
        sy=[v for v in(ss.get("y")or[])if v is not None]
        if ly and sy:
            c=nid(); av=ly+sy; lo,hi=min(av),max(av)
            nb=40; bw=(hi-lo)/nb if hi>lo else 1
            lb,sb=[0]*nb,[0]*nb
            for v in ly: lb[min(int((v-lo)/bw),nb-1)]+=1
            for v in sy: sb[min(int((v-lo)/bw),nb-1)]+=1
            bc=[round(lo+(i+0.5)*bw,1) for i in range(nb)]
            P.append(f'''<div class="chart-container"><h2>3. Ar-tartomany Eloszlas + Fedes</h2><div id="ch{c}"></div></div>
<script>
Plotly.newPlot('ch{c}',[
  {{x:{json.dumps(bc)},y:{json.dumps(lb)},type:'bar',name:'Long',marker:{{color:'rgba(0,255,136,0.6)'}}}},
  {{x:{json.dumps(bc)},y:{json.dumps(sb)},type:'bar',name:'Short',marker:{{color:'rgba(255,68,102,0.6)'}}}}
],{{{BG},barmode:'overlay',title:{{text:'Eloszlas — Fedes: {rovlp["overlap_pct"]}%',font:{{color:'#e0e0e0'}}}},xaxis:{{title:'Ar ($)',gridcolor:'#333'}},yaxis:{{title:'Count',gridcolor:'#333'}},height:400,margin:{{t:50,b:50}}}},{{responsive:true}});
</script>''')
    # 4. Amplitudo z-score
    if pt and pt.get("y"):
        y=[v for v in pt["y"] if v is not None]; n=len(y)
        if n>20:
            c=nid(); mean=sum(y)/n
            std=math.sqrt(sum((v-mean)**2 for v in y)/n) if n>1 else 1
            w=max(20,n//50); zs=[]
            for i in range(n):
                s=max(0,i-w//2); e=min(n,i+w//2)
                cm=sum(y[s:e])/(e-s)
                zs.append(round((cm-mean)/std,3) if std>0 else 0)
            P.append(f'''<div class="chart-container"><h2>4. Amplitudo Anomalia (Z-score)</h2><div id="ch{c}"></div></div>
<script>
var zs={json.dumps(zs)},zX=Array.from({{length:zs.length}},(_,i)=>i);
var tZ={{x:zX,y:zs,type:'scatter',mode:'lines',name:'Z-score',line:{{color:'#00d4ff',width:1.5}}}};
var aY=zs.map(z=>Math.abs(z)>1.5?z:null);
var tA={{x:zX,y:aY,type:'scatter',mode:'markers',name:'Anomalia ({aanom["count"]} burst)',marker:{{color:'#ff4466',size:4,opacity:0.8}}}};
Plotly.newPlot('ch{c}',[tZ,tA,
  {{x:[zX[0],zX[zX.length-1]],y:[1.5,1.5],type:'scatter',mode:'lines',name:'+1.5σ',line:{{color:'#ff6b6b',width:1,dash:'dash'}}}},
  {{x:[zX[0],zX[zX.length-1]],y:[-1.5,-1.5],type:'scatter',mode:'lines',name:'-1.5σ',line:{{color:'#ff6b6b',width:1,dash:'dash'}}}}
],{{{BG},title:{{text:'|Z|>1.5 = burst',font:{{color:'#e0e0e0'}}}},xaxis:{{title:'Ido',gridcolor:'#333'}},yaxis:{{title:'Z-score',gridcolor:'#333'}},
  shapes:[{{type:'rect',xref:'paper',yref:'y',x0:0,x1:1,y0:-1.5,y1:1.5,fillcolor:'rgba(0,255,136,0.05)',line:{{width:0}}}}],
  height:350,margin:{{t:50,b:50}}}},{{responsive:true}});
</script>''')
    # 5. Dominancia valtas timeline
    if dom["sections"]:
        c=nid(); secs=dom["sections"][:100]
        P.append(f'''<div class="chart-container"><h2>5. Dominancia Valtas Timeline</h2><div id="ch{c}"></div></div>
<script>
var secs={json.dumps(secs)},trs=[];
secs.forEach(function(s,i){{
  trs.push({{x:[s.start_idx,s.end_idx],y:[i,i],type:'scatter',mode:'lines',
    line:{{color:s.type==='long'?'#00ff88':'#ff4466',width:8}},
    showlegend:i===0,name:s.type==='long'?'Long':'Short'}});
}});
Plotly.newPlot('ch{c}',trs,{{{BG},title:{{text:'{dom["transitions"]} valtas',font:{{color:'#e0e0e0'}}}},xaxis:{{title:'Ido',gridcolor:'#333'}},yaxis:{{title:'Szekcio #',gridcolor:'#333'}},height:350,margin:{{t:50,b:50}}}},{{responsive:true}});
</script>''')
