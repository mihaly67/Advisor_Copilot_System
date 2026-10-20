#!/usr/bin/env python3
"""
Scalper Copilot v6 — SHAP Elemzés
  - Betanítja a v6.2 modelleket (2min/3min/5min × Long/Short = 6 modell)
  - Elmenti a modelleket .txt formátumban (LightGBM natív)
  - SHAP TreeExplainer: feature importance + beeswarm + waterfall
  - Contra-trend SHAP dekompozíció: mely feature-ok visznek ellenirányba?
  - Plotly HTML chartok: summary, contra-dekompozíció, regime-stratifikált SHAP

Logikus sorrend: SHAP → Optuna → OOS exam
"""
import os, sys, time, warnings
import numpy as np, pandas as pd
from pathlib import Path
from datetime import datetime
warnings.filterwarnings('ignore')

import shap
import lightgbm as lgb
import plotly.graph_objects as go
import plotly.subplots as sp
from plotly.colors import qualitative

# ─── IMPORT v6 PIPELINE ───
sys.path.insert(0, str(Path(__file__).parent))
from scalper_copilot_v6 import (
    load_ticks, make_dollar_bars, build_features, label_tbm,
    cusum_filter, train_lgb, regime_filter,
    DATA_DIR, MODEL_DIR, CHART_DIR, DOLLAR_THR, HORIZON_SEC, HORIZON_NAMES,
    PROFIT_MULT, STOP_MULT, CUSUM_THR, N_FOLD, SEED
)

# ─── KONFIG ───
SHAP_SAMPLE = 5000   # SHAP magyarázó sample méret
CONTRA_TOP_N = 30    # Top-N contra példa waterfall
CHART_DIR.mkdir(parents=True, exist_ok=True)

# Színek
BG='rgb(17,17,17)'; GC='#283442'; TC='#f2f5fa'
C_LONG='#26a69a'; C_SHORT='#ef5350'; C_CONTRA='#FF6B35'; C_NOISE='#888888'

print("=" * 72)
print("SCALPER COPILOT v6 — SHAP ELEMZÉS")
print("=" * 72)

# ═══════════════════════════════════════════════════════════════
# 1. ADATBETÖLTÉS + FEATURE-ÖK + REGIME
# ═══════════════════════════════════════════════════════════════
def prepare_data(train_path):
    """Betölti az adatot, építi a feature-öket és a regime detekciót."""
    ticks = load_ticks(train_path, 'TRAIN')
    bars = make_dollar_bars(ticks, DOLLAR_THR)
    feat_df, feat_cols = build_features(bars)
    regime = regime_filter(bars, feat_df)
    return bars, feat_df, feat_cols, regime

# ═══════════════════════════════════════════════════════════════
# 2. MODELL TANÍTÁS + MENTÉS + SHAP
# ═══════════════════════════════════════════════════════════════
def train_and_shap(bars, feat_df, feat_cols, regime, horizon_sec, horizon_name):
    """Betanít Long+Short modelleket, menti .txt-be, futtat SHAP-ot."""
    print(f"\n{'─'*50}\nSHAP: {horizon_name} ({horizon_sec}s)\n{'─'*50}")
    
    y_long, y_short = label_tbm(bars, horizon_sec, PROFIT_MULT, STOP_MULT)
    idx = feat_df.index.intersection(bars.index[:len(y_long)])
    fa = feat_df.loc[idx]
    yl = pd.Series(y_long[:len(bars)], index=bars.index[:len(y_long)]).loc[idx]
    ys = pd.Series(y_short[:len(bars)], index=bars.index[:len(y_short)]).loc[idx]
    
    ev, cthr = cusum_filter(bars['ret'].loc[idx].fillna(0), CUSUM_THR)
    fc = fa.iloc[ev]
    ylc = (yl.iloc[ev] == 1).astype(int)
    ysc = (ys.iloc[ev] == 1).astype(int)
    print(f"    CUSUM: {len(ev):,}/{len(idx):,} thr={cthr:.6f}")
    
    result = {'horizon': horizon_name, 'horizon_sec': horizon_sec, 'feat_cols': feat_cols}
    
    for side, y_c in [('Long', ylc), ('Short', ysc)]:
        print(f"\n  ── {side} modell ──")
        models, auc_mean, aucs = train_lgb(fc, y_c, N_FOLD)
        model = models[-1]
        
        model_path = MODEL_DIR / f'BTCUSD_v6_{side.lower()}_{horizon_name}_shap.txt'
        model.save_model(str(model_path))
        print(f"    Modell elmentve: {model_path.name} (AUC={auc_mean:.4f})")
        
        preds = model.predict(fa)
        
        print(f"    SHAP TreeExplainer (sample={SHAP_SAMPLE})...")
        t0 = time.time()
        explainer = shap.TreeExplainer(model)
        
        np.random.seed(SEED)
        n_total = len(fa)
        if n_total > SHAP_SAMPLE:
            sample_idx = np.sort(np.random.choice(n_total, SHAP_SAMPLE, replace=False))
            X_sample = fa.iloc[sample_idx]
        else:
            sample_idx = np.arange(n_total)
            X_sample = fa
        
        shap_vals = explainer.shap_values(X_sample)
        if isinstance(shap_vals, list):
            shap_vals = shap_vals[1]
        
        base_val = explainer.expected_value
        if isinstance(base_val, list):
            base_val = base_val[1]
        
        elapsed = time.time() - t0
        print(f"    SHAP kész: {elapsed:.1f}s | base_value={base_val:.4f}")
        
        result[f'models_{side.lower()}'] = models
        result[f'model_{side.lower()}'] = model
        result[f'auc_{side.lower()}'] = auc_mean
        result[f'preds_{side.lower()}'] = preds
        result[f'shap_{side.lower()}'] = shap_vals
        result[f'shap_sample_idx_{side.lower()}'] = sample_idx
        result[f'base_val_{side.lower()}'] = base_val
        result[f'explainer_{side.lower()}'] = explainer
    
    # ── Contra-trend azonosítás ──
    regime_vals = regime['regime'].loc[fa.index].values
    trend_dir_vals = regime['trend_dir'].loc[fa.index].values
    trend_str_vals = regime['trend_str'].loc[fa.index].values
    hurst_vals = regime['hurst'].loc[fa.index].values
    
    pL = result['preds_long']
    pS = result['preds_short']
    tL = np.mean(pL[ev]) + 0.5 * np.std(pL[ev])
    tS = np.mean(pS[ev]) + 0.5 * np.std(pS[ev])
    
    sig = np.zeros(len(fa))
    sig[pL > tL] = 1; sig[pS > tS] = -1
    both = (pL > tL) & (pS > tS)
    sig[both & (pL >= pS)] = 1; sig[both & (pS > pL)] = -1
    
    contra_mask = np.zeros(len(fa), dtype=bool)
    contra_mask[(sig == 1) & (trend_dir_vals < 0)] = True
    contra_mask[(sig == -1) & (trend_dir_vals > 0)] = True
    
    n_contra = contra_mask.sum()
    n_signal = (sig != 0).sum()
    contra_pct = n_contra / max(1, n_signal)
    
    print(f"\n  📊 Contra-trend: {n_contra:,} / {n_signal:,} ({contra_pct:.1%})")
    print(f"     Trending: {(contra_mask & (regime_vals=='trending')).sum():,} | "
          f"Mean-Rev: {(contra_mask & (regime_vals=='mean_rev')).sum():,} | "
          f"Neutral: {(contra_mask & (regime_vals=='neutral')).sum():,}")
    
    result.update({
        'signal': sig, 'threshold_long': tL, 'threshold_short': tS,
        'p_long': pL, 'p_short': pS,
        'contra_mask': contra_mask, 'contra_pct': contra_pct,
        'regime_vals': regime_vals, 'trend_dir_vals': trend_dir_vals,
        'trend_str_vals': trend_str_vals, 'hurst_vals': hurst_vals,
        'fa_index': fa.index, 'fa': fa
    })
    return result

# ═══════════════════════════════════════════════════════════════
# 3. SHAP CHARTOK (Plotly HTML)
# ═══════════════════════════════════════════════════════════════
def make_shap_charts(result, output_dir):
    """Generál SHAP Plotly HTML chartokat egy horizon eredményéhez."""
    hn = result['horizon']
    feat_cols = result['feat_cols']
    n_feat = len(feat_cols)
    shap_L = result['shap_long']
    shap_S = result['shap_short']
    
    # ── 1. FEATURE IMPORTANCE |SHAP| átlag — Long vs Short ──
    imp_L = np.abs(shap_L).mean(axis=0)
    imp_S = np.abs(shap_S).mean(axis=0)
    top_n = min(25, n_feat)
    
    fig = sp.make_subplots(rows=1, cols=2,
        subplot_titles=[f'{hn} Long |SHAP|', f'{hn} Short |SHAP|'],
        horizontal_spacing=0.15)
    
    order_L = np.argsort(imp_L)[::-1][:top_n]
    fig.add_trace(go.Bar(
        y=[feat_cols[i] for i in order_L][::-1], orientation='h',
        x=imp_L[order_L][::-1], marker_color=C_LONG, name='Long'
    ), row=1, col=1)
    
    order_S = np.argsort(imp_S)[::-1][:top_n]
    fig.add_trace(go.Bar(
        y=[feat_cols[i] for i in order_S][::-1], orientation='h',
        x=imp_S[order_S][::-1], marker_color=C_SHORT, name='Short'
    ), row=1, col=2)
    
    fig.update_layout(title_text=f'SHAP Feature Importance — {hn}',
        template='plotly_dark', height=700, showlegend=False,
        paper_bgcolor=BG, plot_bgcolor=BG, font=dict(color=TC))
    p1 = output_dir / f'shap_importance_{hn}.html'
    fig.write_html(str(p1))
    print(f"    📈 Chart: {p1.name}")
    
    # ── 2. SHAP BEESWARM (interaktív scatter) ──
    for side, shap_v, color in [('Long', shap_L, C_LONG), ('Short', shap_S, C_SHORT)]:
        sample_idx = result[f'shap_sample_idx_{side.lower()}']
        X_sample = result['fa'].iloc[sample_idx]
        imp = np.abs(shap_v).mean(axis=0)
        top_idx = np.argsort(imp)[::-1][:15]
        
        fig2 = go.Figure()
        for rank, fi in enumerate(top_idx):
            fname = feat_cols[fi]
            sv = shap_v[:, fi]
            fv = X_sample.iloc[:, fi].values
            fv_norm = (fv - np.nanmin(fv)) / max(1e-12, np.nanmax(fv) - np.nanmin(fv))
            fig2.add_trace(go.Scatter(
                x=sv, y=np.full(len(sv), rank), mode='markers',
                marker=dict(size=4, color=fv_norm, colorscale='RdYlGn',
                    showscale=(rank==0),
                    colorbar=dict(title='Feature value', x=1.02) if rank==0 else None,
                    opacity=0.6),
                name=fname,
                hovertemplate=f'{fname}<br>SHAP: %{{x:.4f}}<br>Value: %{{customdata:.4f}}<extra></extra>',
                customdata=fv
            ))
        
        fig2.update_layout(
            title_text=f'SHAP Beeswarm — {hn} {side}',
            template='plotly_dark', height=600, width=1000,
            yaxis=dict(tickmode='array', tickvals=list(range(15)),
                ticktext=[feat_cols[i] for i in top_idx], autorange='reversed'),
            xaxis_title='SHAP value (impact on model output)',
            showlegend=False, paper_bgcolor=BG, plot_bgcolor=BG,
            font=dict(color=TC, size=11))
        p2 = output_dir / f'shap_beeswarm_{hn}_{side.lower()}.html'
        fig2.write_html(str(p2))
        print(f"    🐝 Chart: {p2.name}")
    
    # ── 3. CONTRA-TREND SHAP DEKOMPOZÍCIÓ ──
    contra_mask = result['contra_mask']
    sig = result['signal']
    fa = result['fa']
    
    if contra_mask.sum() == 0:
        print(f"    ⚠️ Nincs contra-trend bár — contra chart kihagyva")
        return
    
    normal_mask = (sig != 0) & (~contra_mask)
    contra_indices = np.where(contra_mask)[0]
    long_contra = contra_indices[sig[contra_indices] == 1]
    short_contra = contra_indices[sig[contra_indices] == -1]
    
    # Sample mapping
    sample_set_L = set(result['shap_sample_idx_long'])
    sample_set_S = set(result['shap_sample_idx_short'])
    idx_to_pos_L = {int(v): k for k, v in enumerate(result['shap_sample_idx_long'])}
    idx_to_pos_S = {int(v): k for k, v in enumerate(result['shap_sample_idx_short'])}
    
    fig3 = sp.make_subplots(rows=1, cols=2,
        subplot_titles=['Contra vs Normal |SHAP| — Long', 'Contra vs Normal |SHAP| — Short'],
        horizontal_spacing=0.15)
    
    for col, side, shap_v, color, idx_map, sample_set in [
        (1, 'Long', shap_L, C_LONG, idx_to_pos_L, sample_set_L),
        (2, 'Short', shap_S, C_SHORT, idx_to_pos_S, sample_set_S)
    ]:
        side_sig = 1 if side == 'Long' else -1
        contra_arr = np.where(contra_mask & (sig == side_sig))[0]
        normal_arr = np.where((sig == side_sig) & normal_mask)[0]
        
        contra_pos = [idx_map[int(i)] for i in contra_arr if int(i) in idx_map]
        normal_pos = [idx_map[int(i)] for i in normal_arr if int(i) in idx_map]
        
        contra_imp = np.abs(shap_v[contra_pos]).mean(axis=0) if contra_pos else np.zeros(n_feat)
        normal_imp = np.abs(shap_v[normal_pos]).mean(axis=0) if normal_pos else np.zeros(n_feat)
        diff = contra_imp - normal_imp
        top_feat = np.argsort(diff)[::-1][:15]
        
        fig3.add_trace(go.Bar(
            y=[feat_cols[i] for i in top_feat][::-1], orientation='h',
            x=contra_imp[top_feat][::-1], marker_color=C_CONTRA,
            name=f'Contra ({side})', opacity=0.8
        ), row=1, col=col)
        fig3.add_trace(go.Bar(
            y=[feat_cols[i] for i in top_feat][::-1], orientation='h',
            x=normal_imp[top_feat][::-1], marker_color=color,
            name=f'Normal ({side})', opacity=0.5
        ), row=1, col=col)
    
    fig3.update_layout(
        title_text=f'🔴 Contra-trend SHAP Dekompozíció — {hn}',
        template='plotly_dark', height=700, barmode='group',
        paper_bgcolor=BG, plot_bgcolor=BG, font=dict(color=TC, size=11))
    p3 = output_dir / f'shap_contra_decomposition_{hn}.html'
    fig3.write_html(str(p3))
    print(f"    🔴 Chart: {p3.name}")
    
    # ── 3b. Contra waterfall: top contra példák ──
    for side, shap_v, color in [('Long', shap_L, C_LONG), ('Short', shap_S, C_SHORT)]:
        side_sig = 1 if side == 'Long' else -1
        idx_key = f'shap_sample_idx_{side.lower()}'
        idx_map = {int(v): k for k, v in enumerate(result[idx_key])}
        
        contra_arr = np.where(contra_mask & (sig == side_sig))[0]
        contra_in_sample = [int(i) for i in contra_arr if int(i) in idx_map]
        if not contra_in_sample:
            continue
        
        model_preds = result[f'preds_{side.lower()}']
        contra_preds = model_preds[contra_in_sample]
        top_local = np.argsort(contra_preds)[::-1][:min(CONTRA_TOP_N, len(contra_preds))]
        top_orig = [contra_in_sample[j] for j in top_local]
        top_pos = [idx_map[i] for i in top_orig]
        
        mean_shap = shap_v[top_pos].mean(axis=0)
        top_feat = np.argsort(np.abs(mean_shap))[::-1][:15]
        
        fig_wf = go.Figure()
        colors_wf = [C_LONG if mean_shap[i] > 0 else C_SHORT for i in top_feat]
        fig_wf.add_trace(go.Bar(
            x=[mean_shap[i] for i in top_feat],
            y=[feat_cols[i] for i in top_feat], orientation='h',
            marker_color=colors_wf,
            text=[f'{mean_shap[i]:+.4f}' for i in top_feat],
            textposition='outside', textfont=dict(size=10, color=TC)
        ))
        fig_wf.update_layout(
            title_text=f'Contra-trend Waterfall — {hn} {side} (top {len(top_orig)} contra)',
            template='plotly_dark', height=600,
            xaxis_title='Átlagos SHAP érték (contra bárokon)',
            yaxis=dict(autorange='reversed'), showlegend=False,
            paper_bgcolor=BG, plot_bgcolor=BG, font=dict(color=TC, size=11))
        p_wf = output_dir / f'shap_contra_waterfall_{hn}_{side.lower()}.html'
        fig_wf.write_html(str(p_wf))
        print(f"    🔻 Chart: {p_wf.name}")

# ═══════════════════════════════════════════════════════════════
# 4. ÖSSZESÍTŐ DASHBOARD
# ═══════════════════════════════════════════════════════════════
def make_summary_dashboard(all_results, output_dir):
    """Összesítő dashboard: feature importance + contra SHAP delta."""
    horizons = [r['horizon'] for r in all_results]
    n_h = len(horizons)
    
    fig = sp.make_subplots(rows=2, cols=n_h,
        subplot_titles=[f'{hn} — |SHAP| Top 15' for hn in horizons] +
                       [f'{hn} — Contra SHAP Δ' for hn in horizons],
        vertical_spacing=0.12)
    
    for col, result in enumerate(all_results, 1):
        hn = result['horizon']
        feat_cols = result['feat_cols']
        shap_L = result['shap_long']
        shap_S = result['shap_short']
        
        imp = (np.abs(shap_L).mean(axis=0) + np.abs(shap_S).mean(axis=0)) / 2
        top_idx = np.argsort(imp)[::-1][:15]
        colors_row1 = [C_LONG, C_SHORT, '#FFC107'][col-1]
        
        fig.add_trace(go.Bar(
            y=[feat_cols[i] for i in top_idx][::-1], orientation='h',
            x=imp[top_idx][::-1], marker_color=colors_row1, showlegend=False
        ), row=1, col=col)
        
        # Contra SHAP delta (Long modell)
        contra_mask = result['contra_mask']; sig = result['signal']
        idx_map = {int(v): k for k, v in enumerate(result['shap_sample_idx_long'])}
        contra_pos = [idx_map[int(i)] for i in np.where(contra_mask & (sig==1))[0] if int(i) in idx_map]
        normal_pos = [idx_map[int(i)] for i in np.where((sig==1) & ~contra_mask)[0] if int(i) in idx_map]
        
        if contra_pos and normal_pos:
            delta = np.abs(shap_L[contra_pos]).mean(0) - np.abs(shap_L[normal_pos]).mean(0)
            top_d = np.argsort(delta)[::-1][:15]
            c_d = [C_CONTRA if delta[i]>0 else C_NOISE for i in top_d]
            fig.add_trace(go.Bar(
                y=[feat_cols[i] for i in top_d][::-1], orientation='h',
                x=delta[top_d][::-1], marker_color=c_d[::-1], showlegend=False
            ), row=2, col=col)
    
    fig.update_layout(
        title_text='SHAP Összesítő — Scalper Copilot v6.2 (3 horizon)',
        template='plotly_dark', height=900,
        paper_bgcolor=BG, plot_bgcolor=BG, font=dict(color=TC, size=10))
    p = output_dir / 'shap_summary_dashboard.html'
    fig.write_html(str(p))
    print(f"\n📊 Dashboard: {p.name}")

# ═══════════════════════════════════════════════════════════════
# 5. CONTRA-TREND RANKING REPORT
# ═══════════════════════════════════════════════════════════════
def generate_contra_report(all_results, output_dir):
    """Szöveges jelentés: mely feature-ok a legfőbb contra-trend okozók."""
    lines = [
        "# SHAP Contra-Trend Elemzés — Scalper Copilot v6.2",
        f"# Dátum: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ""
    ]
    
    feat_counter = {}  # cross-horizon contra feature-ok
    
    for result in all_results:
        hn = result['horizon']
        feat_cols = result['feat_cols']
        contra_pct = result['contra_pct']
        contra_mask = result['contra_mask']
        sig = result['signal']
        
        lines.append(f"## {hn} horizon")
        lines.append(f"- Contra-trend: {contra_pct:.1%}")
        
        for side, shap_key, sample_key in [
            ('Long', 'shap_long', 'shap_sample_idx_long'),
            ('Short', 'shap_short', 'shap_sample_idx_short')
        ]:
            side_sig = 1 if side == 'Long' else -1
            shap_v = result[shap_key]
            idx_map = {int(v): k for k, v in enumerate(result[sample_key])}
            
            contra_arr = np.where(contra_mask & (sig == side_sig))[0]
            normal_arr = np.where((sig == side_sig) & ~contra_mask)[0]
            contra_pos = [idx_map[int(i)] for i in contra_arr if int(i) in idx_map]
            normal_pos = [idx_map[int(i)] for i in normal_arr if int(i) in idx_map]
            
            if contra_pos and normal_pos:
                c_imp = np.abs(shap_v[contra_pos]).mean(axis=0)
                n_imp = np.abs(shap_v[normal_pos]).mean(axis=0)
                delta = c_imp - n_imp
                top5 = np.argsort(delta)[::-1][:5]
                lines.append(f"- {side} contra top feature-ok (SHAP Δ):")
                for fi in top5:
                    fname = feat_cols[fi]
                    lines.append(f"  - {fname}: Δ={delta[fi]:+.4f} (contra={c_imp[fi]:.4f} normal={n_imp[fi]:.4f})")
                    # Cross-horizon counter
                    key = f"{fname}"
                    if key not in feat_counter:
                        feat_counter[key] = []
                    feat_counter[key].append(f'{hn}_{side[0]} Δ={delta[fi]:+.4f}')
        
        lines.append("")
    
    # Cross-horizon összesítő
    lines.append("## Összesítő: Cross-horizon contra feature-ok")
    for fname, entries in sorted(feat_counter.items(), key=lambda x: -len(x[1])):
        if len(entries) >= 2:
            lines.append(f"- **{fname}** ({len(entries)}x): {', '.join(entries)}")
    
    lines.extend(["",
        "## Javaslat (SHAP alapján)",
        "1. Legnagyobb contra-SHAP Δ feature-ok → regime filter bővítés cél",
        "2. Ha RSI/bollinger okoz contra → meta-labeling küszöb emelése ezeknél",
        "3. Ha ema_cross okoz contra → trend_dir erősebb súlyozás",
        "4. Ha vol_imbalance okoz contra → flow direction feature hozzáadás",
        "5. Optuna: ezen feature-ok súly/küszöb paramétereinek optimalizálása"
    ])
    
    report_path = output_dir / 'shap_contra_report.md'
    with open(report_path, 'w') as f:
        f.write('\n'.join(lines))
    print(f"\n📝 Report: {report_path.name}")
    return '\n'.join(lines)

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    ts_total = datetime.now()
    
    # 1. Adat előkészítés
    train_path = DATA_DIR / 'BTCUSD_training_tick.csv'
    bars, feat_df, feat_cols, regime = prepare_data(train_path)
    
    # 2. SHAP elemzés per horizon
    all_results = []
    for hsec in HORIZON_SEC:
        hn = HORIZON_NAMES[hsec]
        result = train_and_shap(bars, feat_df, feat_cols, regime, hsec, hn)
        all_results.append(result)
    
    # 3. Chartok
    print(f"\n{'═'*50}\nCHART GENERÁLÁS\n{'═'*50}")
    for result in all_results:
        make_shap_charts(result, CHART_DIR)
    
    # 4. Összesítő dashboard
    make_summary_dashboard(all_results, CHART_DIR)
    
    # 5. Contra-trend report
    report = generate_contra_report(all_results, CHART_DIR)
    
    # Összesítő
    el = (datetime.now() - ts_total).total_seconds()
    print(f"\n{'='*72}")
    print(f"SHAP ELEMZÉS KÉSZ — {el:.0f}s")
    print(f"  Horizontok: {list(HORIZON_NAMES.values())}")
    print(f"  Modellek: {MODEL_DIR}/BTCUSD_v6_*_shap.txt")
    print(f"  Chartok: {CHART_DIR}/shap_*.html")
    print(f"  Report: {CHART_DIR}/shap_contra_report.md")
    for result in all_results:
        hn = result['horizon']
        cp = result['contra_pct']
        n_contra = result['contra_mask'].sum()
        print(f"  {hn}: contra={n_contra:,} ({cp:.1%})")
    print(f"{'='*72}")
    print(f"\n➡️ KÖVETKEZŐ: Optuna hiperopt (scalper_optuna_v6.py)")
