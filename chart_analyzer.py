#!/usr/bin/env python3
"""
Chart Analyzer — Plotly HTML chart DOM-based adatkinyerés + vizuális elemzés.

Két megközelítés:
  A) Playwright DOM query: HTML megnyitása → Plotly.newPlot adatok kinyerése JS-ből
  B) Regex fallback: Ha Plotly nem elérhető, regex-sel kinyerjük a trace-eket
"""
import os, sys, json, re, time, tempfile, traceback
from pathlib import Path
from typing import Optional

# ─── Regex fallback: Plotly adatok kinyerése HTML-ből JS futtatás nélkül ───

def _extract_newplot_section(html: str) -> str:
    """Kinyeri csak a Plotly.newPlot(...) hívás szekciót, kihagyva a library-t."""
    # Keresünk Plotly.newPlot vagy newPlot hívást
    # A viz_v9.html-ben inline van a teljes Plotly library, utána jön a newPlot hívás
    # Stratégia: keressük a legutolsó </script> előtti script blockot (ott van az adat)
    
    # Próbáljuk: utolsó script block ami newPlot-ot tartalmaz
    # vagy egyszerűen: utolsó 500KB (a layout + traces általában a végén)
    max_scan = 500_000
    
    # Ha a HTML kisebb mint 1MB, teljesen scaneljük
    if len(html) < 1_000_000:
        return html
    
    # Különben: eleje (cím/stílus) + vége (adat/layout)
    head = html[:50_000]  # címkék, meta
    tail = html[-max_scan:]  # Plotly.newPlot adatok
    return head + tail


def extract_plotly_traces_regex(html: str) -> dict:
    """Plotly.newPlot hívásból regex-sel kinyeri a trace-eket és layout-ot.
    Optimalizált: csak egyszerű (nem-nested) regex-eket használ."""
    result = {"method": "regex", "traces": [], "layout": {}, "stats": {}}
    
    chart_types = {'candlestick','scatter','scattergl','bar','heatmap',
                   'contour','surface','pie','box','violin','histogram','ohlc'}
    
    # Csak egyszerű findall — nem nested regex
    all_types = re.findall(r'"type":\s*"(\w+)"', html)
    trace_types = [t for t in all_types if t in chart_types]
    all_names = re.findall(r'"name":\s*"([^"]+)"', html)
    # Szűrjük: a Plotly data trace nevek (nem layout/template nevek)
    # A data trace nevek tipikusan: "P(Long)", "Actual Short (305)", stb.
    data_trace_names = [n for n in all_names if any(
        kw in n for kw in ['Long','Short','Noise','Predict','Actual','P(','Price',
                           'OHLC','candle','signal','pred','label','Ár','BTC','ETH']
    )]
    if not data_trace_names and all_names:
        data_trace_names = all_names[:15]
    
    # Title
    title_match = re.search(r'"title":\s*\{[^}]*?"text":\s*"([^"]+)"', html)
    if not title_match:
        title_match = re.search(r'"title":\s*"([^"]+)"', html)
    title = title_match.group(1) if title_match else ""
    result["layout"]["title"] = title
    
    # Annotations — csak a text mezők
    annotations = re.findall(r'"text":\s*"([^"]{3,80})"', html)
    # Szűrjük: csak a panel címek (tartalmaznak érthető szöveget)
    panel_keywords = ['Ár','Pred','Label','Price','Probability','Signal','Valószín']
    panel_annotations = [a for a in annotations if any(kw in a for kw in panel_keywords)]
    result["layout"]["annotations"] = panel_annotations
    
    # Shapes — küszöb vonalak (y0 értékek)
    shape_ys = re.findall(r'"y0":\s*([\d.]+)', html)
    shape_colors = re.findall(r'"color":\s*"([^"]+)"', html)
    shapes = []
    for i, y0 in enumerate(shape_ys[:10]):
        s = {"y0": float(y0)}
        if i < len(shape_colors): s["color"] = shape_colors[i]
        shapes.append(s)
    result["layout"]["shapes"] = shapes
    
    # Height/width
    hm = re.search(r'"height":\s*(\d+)', html)
    if hm: result["layout"]["height"] = int(hm.group(1))
    wm = re.search(r'"width":\s*(\d+)', html)
    if wm: result["layout"]["width"] = int(wm.group(1))
    
    # Plotly verzió
    vm = re.search(r'plotly\.js\s+v([\d.]+)', html)
    if vm: result["plotly_version"] = vm.group(1)
    
    # Candlestick: időbélyegek (csak a tail-ben keressünk, gyorsabb)
    candle_data = {}
    tail_for_ts = html[-200000:]  # utolsó 200KB elég a timestamp-ekhez
    # Csak első 100 timestamp kell (start + end + count)
    ts = []
    for m in re.finditer(r'"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})"', tail_for_ts):
        ts.append(m.group(1))
        if len(ts) >= 100:
            break
    if ts:
        # Count összes timestamp a teljes html-ben (gyors: count only)
        # Ehelyett: megbecsüljük a count-ot a tail arányából
        total_ts_estimate = len(ts)  # minimum
        candle_data["time_range"] = {
            "start": ts[0], "end": ts[-1], "num_bars": total_ts_estimate
        }
    
    # OHLC ranges — egyszerű findall
    for key in ['open','high','low','close']:
        vals = re.findall(rf'"{key}":\s*\[([\d.,\s]+)\]', html)
        if vals:
            numbers = re.findall(r'([\d.]+)', vals[0])
            if numbers and len(numbers) > 5:
                float_nums = [float(v) for v in numbers[:1000]]
                candle_data[f"{key}_range"] = {
                    "min": round(min(float_nums), 2),
                    "max": round(max(float_nums), 2),
                    "count": len(numbers)
                }
    result["candlestick"] = candle_data
    
    # Scatter trace nevek és y stats
    scatter_traces = []
    for name in data_trace_names:
        if 'scatter' in trace_types or not trace_types:
            trace = {"name": name}
            scatter_traces.append(trace)
    
    # Y értékek statisztikák (csak tail-ben keressük a y tömböket)
    tail_for_y = html[-200000:]
    # Csak a valószínűség tömböket keressük (y:[0.xxx, 0.yyy, ...])
    y_prob_arrays = []
    for m in re.finditer(r'"y":\s*\[([\d.]+(?:[eE][+-]?\d+)?(?:,\s*[\d.]+(?:[eE][+-]?\d+)?){5,})\]', tail_for_y):
        y_prob_arrays.append(m.group(1))
        if len(y_prob_arrays) >= 5:
            break
    
    for i, trace in enumerate(scatter_traces):
        if i < len(y_prob_arrays):
            ya = y_prob_arrays[i]
            y_vals = re.findall(r'([\d.eE+-]+)', ya)
            if len(y_vals) > 10:
                float_vals = [float(v) for v in y_vals[:500]]
                if 0 <= min(float_vals) and max(float_vals) <= 1.5:
                    trace["y_stats"] = {
                        "count": len(y_vals),
                        "min": round(min(float_vals), 4),
                        "max": round(max(float_vals), 4),
                        "mean": round(sum(float_vals)/len(float_vals), 4),
                    }
                    trace["y_sample"] = [round(v, 4) for v in float_vals[:5]]
    
    result["scatter_traces"] = scatter_traces[:10]  # max 10
    result["traces"] = [{"type": t} for t in trace_types[:20]]
    result["trace_names"] = data_trace_names
    
    # Statisztikák a címből
    if title:
        for key, val in re.findall(r'(\w+):(\d+)', title):
            result["stats"][key] = int(val)
    
    return result


# ─── Playwright DOM query: Plotly adatok kinyerése JS futtatásával ───

# ─── Full data extraction JS: complete y/x arrays (downsampled) for visual analysis ───

JS_EXTRACT_FULL = """
() => {
    const MAX_PTS = 2000;  // max points per array (downsample if larger)
    function downsample(arr, maxPts) {
        if (!arr || arr.length <= maxPts) return arr ? Array.from(arr) : [];
        const step = arr.length / maxPts;
        const out = [];
        for (let i = 0; i < maxPts; i++) {
            out.push(arr[Math.floor(i * step)]);
        }
        return out;
    }
    function roundArr(arr, dec=4) {
        const m = Math.pow(10, dec);
        return arr.map(v => v == null ? null : Math.round(v * m) / m);
    }
    const plots = {};
    const divs = document.querySelectorAll('[id]');
    for (const div of divs) {
        if (window.Plotly && div.data) {
            const traces = [];
            for (const trace of div.data) {
                const t = { type: trace.type || 'scatter', name: trace.name || '' };
                // Full x array
                if (trace.x && trace.x.length > 0) {
                    t.x = downsample(trace.x, MAX_PTS);
                    t.x_count = trace.x.length;
                }
                // Full y array
                if (trace.y && trace.y.length > 0) {
                    const vals = trace.y.filter(v => v != null && !isNaN(v));
                    t.y = roundArr(downsample(trace.y, MAX_PTS));
                    t.y_count = trace.y.length;
                    t.y_min = Math.min(...vals);
                    t.y_max = Math.max(...vals);
                    t.y_mean = vals.reduce((a,b) => a+b, 0) / vals.length;
                    // Std dev
                    const mean = t.y_mean;
                    const variance = vals.reduce((a,b) => a + (b-mean)*(b-mean), 0) / vals.length;
                    t.y_std = Math.sqrt(variance);
                }
                // Candlestick OHLCV
                if (trace.type === 'candlestick') {
                    t.num_bars = trace.x ? trace.x.length : 0;
                    if (trace.open) t.open = roundArr(downsample(trace.open, MAX_PTS), 2);
                    if (trace.high) t.high = roundArr(downsample(trace.high, MAX_PTS), 2);
                    if (trace.low) t.low = roundArr(downsample(trace.low, MAX_PTS), 2);
                    if (trace.close) t.close = roundArr(downsample(trace.close, MAX_PTS), 2);
                    if (trace.x && trace.x.length > 0) {
                        t.time_start = String(trace.x[0]);
                        t.time_end = String(trace.x[trace.x.length - 1]);
                    }
                    if (trace.close && trace.close.length > 0) {
                        const closes = trace.close.filter(v => v != null);
                        t.price_min = Math.min(...closes);
                        t.price_max = Math.max(...closes);
                    }
                }
                traces.push(t);
            }
            const layout = {};
            if (div.layout) {
                layout.title = typeof div.layout.title === 'string'
                    ? div.layout.title
                    : (div.layout.title && div.layout.title.text) || '';
                if (div.layout.shapes) {
                    layout.shapes = div.layout.shapes.map(s => ({
                        type: s.type||'line', y0: s.y0, y1: s.y1,
                        color: s.line ? s.line.color : '', dash: s.line ? s.line.dash : ''
                    }));
                }
                if (div.layout.annotations) {
                    layout.annotations = div.layout.annotations.filter(a => a.text).map(a => a.text);
                }
            }
            plots[div.id] = { traces, layout, num_traces: traces.length };
        }
    }
    plots['_meta'] = {
        title: document.title,
        num_scripts: document.querySelectorAll('script').length
    };
    return plots;
}
"""

JS_EXTRACT_PLOTLY = """
() => {
    const plots = {};
    const divs = document.querySelectorAll('[id]');
    for (const div of divs) {
        if (window.Plotly && div.data) {
            const traces = [];
            for (const trace of div.data) {
                const t = { type: trace.type || 'scatter', name: trace.name || '' };
                if (trace.type === 'candlestick') {
                    t.num_bars = trace.x ? trace.x.length : 0;
                    if (trace.x && trace.x.length > 0) {
                        t.time_start = String(trace.x[0]);
                        t.time_end = String(trace.x[trace.x.length - 1]);
                    }
                    if (trace.close && trace.close.length > 0) {
                        const closes = trace.close.filter(v => v != null);
                        t.price_min = Math.min(...closes);
                        t.price_max = Math.max(...closes);
                    }
                }
                if (trace.y && trace.y.length > 0) {
                    const vals = trace.y.filter(v => v != null && !isNaN(v));
                    if (vals.length > 0) {
                        t.y_count = vals.length;
                        t.y_min = Math.min(...vals);
                        t.y_max = Math.max(...vals);
                        t.y_mean = vals.reduce((a,b) => a+b, 0) / vals.length;
                        t.y_sample = vals.slice(0, 5).map(v => Math.round(v*10000)/10000);
                    }
                }
                traces.push(t);
            }
            const layout = {};
            if (div.layout) {
                layout.title = typeof div.layout.title === 'string'
                    ? div.layout.title
                    : (div.layout.title && div.layout.title.text) || '';
                layout.height = div.layout.height || 0;
                layout.width = div.layout.width || 0;
                if (div.layout.annotations) {
                    layout.annotations = div.layout.annotations.filter(a => a.text).map(a => a.text);
                }
                if (div.layout.shapes) {
                    layout.shapes = div.layout.shapes.map(s => ({
                        type: s.type||'line', y0: s.y0, y1: s.y1,
                        color: s.line ? s.line.color : '', dash: s.line ? s.line.dash : ''
                    }));
                }
            }
            plots[div.id] = { traces, layout, num_traces: traces.length };
        }
    }
    plots['_meta'] = {
        title: document.title, num_scripts: document.querySelectorAll('script').length,
        num_divs: document.querySelectorAll('div').length,
        body_height: document.body.scrollHeight, body_width: document.body.scrollWidth
    };
    return plots;
}
"""

async def _playwright_extract(html_path=None, html_content=None,
                               wait_ms=3000, width=1600, height=1200):
    """Playwright: HTML megnyitása → JS futtatás → Plotly adatok kinyerése."""
    from playwright.async_api import async_playwright
    result = {"method": "playwright_dom", "plots": {}, "screenshot_path": None}
    tmp_html = None
    try:
        if html_path and os.path.exists(html_path):
            file_url = f"file://{os.path.abspath(html_path)}"
        elif html_content:
            tmp_html = tempfile.NamedTemporaryFile(suffix='.html', mode='w', delete=False, dir='/tmp')
            tmp_html.write(html_content); tmp_html.close()
            file_url = f"file://{tmp_html.name}"
        else:
            return {"error": "Need html_path or html_content"}
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu']
            )
            page = await browser.new_page(viewport={"width": width, "height": height})
            await page.goto(file_url, wait_until="load", timeout=30000)
            await page.wait_for_timeout(wait_ms)
            
            try:
                plotly_data = await page.evaluate(JS_EXTRACT_PLOTLY)
                result["plots"] = plotly_data
            except Exception as e:
                result["js_error"] = str(e)[:500]
            
            # Screenshot
            ss_path = tempfile.mktemp(suffix='.png', dir='/tmp')
            try:
                await page.screenshot(path=ss_path, full_page=False)
                result["screenshot_path"] = ss_path
                try:
                    from PIL import Image
                    img = Image.open(ss_path)
                    w, h = img.size
                    pixels = list(img.getdata())[::10]
                    brights = [0.299*r+0.587*g+0.114*b for r,g,b in pixels]
                    avg_b = sum(brights)/len(brights) if brights else 0
                    result["visual"] = {
                        "dimensions": f"{w}x{h}",
                        "size_kb": round(os.path.getsize(ss_path)/1024, 1),
                        "avg_brightness": round(avg_b, 1),
                    }
                except: pass
            except: pass
            
            await browser.close()
    except Exception as e:
        result["error"] = str(e)[:500]
        result["traceback"] = traceback.format_exc()[:1000]
    finally:
        if tmp_html:
            try: os.unlink(tmp_html.name)
            except: pass
    return result


def extract_plotly_playwright(html_path=None, html_content=None,
                               wait_ms=3000, width=1600, height=1200):
    """Sync wrapper a Playwright async extract körül."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(
                    asyncio.run,
                    _playwright_extract(html_path, html_content, wait_ms, width, height)
                )
                return future.result(timeout=60)
        else:
            return loop.run_until_complete(
                _playwright_extract(html_path, html_content, wait_ms, width, height)
            )
    except RuntimeError:
        return asyncio.run(
            _playwright_extract(html_path, html_content, wait_ms, width, height)
        )


async def _playwright_extract_full(html_path=None, html_content=None,
                                     wait_ms=3000, width=1600, height=1200):
    """Playwright: FULL data extraction (downsampled arrays) for visual analysis."""
    from playwright.async_api import async_playwright
    result = {"method": "playwright_full", "plots": {}}
    tmp_html = None
    try:
        if html_path and os.path.exists(html_path):
            file_url = f"file://{os.path.abspath(html_path)}"
        elif html_content:
            tmp_html = tempfile.NamedTemporaryFile(suffix='.html', mode='w', delete=False, dir='/tmp')
            tmp_html.write(html_content); tmp_html.close()
            file_url = f"file://{tmp_html.name}"
        else:
            return {"error": "Need html_path or html_content"}
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu']
            )
            page = await browser.new_page(viewport={"width": width, "height": height})
            await page.goto(file_url, wait_until="load", timeout=30000)
            await page.wait_for_timeout(wait_ms)
            try:
                plotly_data = await page.evaluate(JS_EXTRACT_FULL)
                result["plots"] = plotly_data
            except Exception as e:
                result["js_error"] = str(e)[:500]
            await browser.close()
    except Exception as e:
        result["error"] = str(e)[:500]
        result["traceback"] = traceback.format_exc()[:1000]
    finally:
        if tmp_html:
            try: os.unlink(tmp_html.name)
            except: pass
    return result

def extract_full_data(html_path=None, html_content=None, wait_ms=3000):
    """Sync wrapper for full data extraction."""
    import asyncio
    try:
        return asyncio.run(_playwright_extract_full(html_path, html_content, wait_ms))
    except RuntimeError:
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run,
                _playwright_extract_full(html_path, html_content, wait_ms))
            return future.result(timeout=90)


    """HTML chart elemzés. method: auto/playwright/regex"""
    if html_path and os.path.exists(html_path):
        with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()
        source = html_path
    elif html_content:
        source = "<html_content>"
    else:
        return {"error": "Need html_path or html_content"}
    
    result = {"source": source, "file_size_kb": round(len(html_content)/1024, 1)}
    # Optimalizálás: nagy HTML-eknél csak a releváns részt scaneljük regex-sel
    html_for_regex = _extract_newplot_section(html_content)
    regex_result = extract_plotly_traces_regex(html_for_regex)
    result["regex_analysis"] = regex_result
    
    if method in ("auto", "playwright"):
        try:
            pw_result = extract_plotly_playwright(
                html_path=html_path,
                html_content=html_content if not html_path else None,
                wait_ms=wait_ms
            )
            result["playwright_analysis"] = pw_result
        except Exception as e:
            result["playwright_error"] = str(e)[:500]
    
    summary = {}
    rr = regex_result
    if rr.get("layout", {}).get("title"):
        summary["title"] = rr["layout"]["title"]
    if rr.get("layout", {}).get("annotations"):
        summary["panels"] = rr["layout"]["annotations"]
    if rr.get("candlestick", {}).get("time_range"):
        summary["time_range"] = rr["candlestick"]["time_range"]
    if rr.get("scatter_traces"):
        summary["prediction_curves"] = [t["name"] for t in rr["scatter_traces"] if "name" in t]
    if rr.get("stats"):
        summary["class_counts"] = rr["stats"]
    if rr.get("layout", {}).get("shapes"):
        thresholds = [f"y={s['y0']}" for s in rr["layout"]["shapes"] if 'y0' in s]
        if thresholds: summary["thresholds"] = thresholds
    result["summary"] = summary
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Chart Analyzer")
    parser.add_argument("path", help="HTML fájl útvonal")
    parser.add_argument("--method", default="auto", choices=["auto","playwright","regex"])
    parser.add_argument("--wait", type=int, default=3000)
    args = parser.parse_args()
    
    t0 = time.time()
    result = analyze(html_path=args.path, method=args.method, wait_ms=args.wait)
    elapsed = time.time() - t0
    
    print(f"⏱  Elemzés: {elapsed:.1f}s")
    print(f"📄 Forrás: {result.get('source','?')}")
    if "summary" in result:
        s = result["summary"]
        print(f"📋 Cím: {s.get('title','')}")
        print(f"📋 Panelek: {s.get('panels',[])}")
        if "time_range" in s:
            tr = s["time_range"]
            print(f"📋 Idő: {tr['start']} → {tr['end']} ({tr['num_bars']} bar)")
        print(f"📋 Görbék: {s.get('prediction_curves',[])}")
        print(f"📋 Osztályok: {s.get('class_counts',{})}")
        print(f"📋 Küszöbök: {s.get('thresholds',[])}")
    
    out_path = args.path.replace('.html', '_analysis.json')
    with open(out_path, 'w') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print(f"💾 Mentve: {out_path}")
