#!/usr/bin/env python3
"""
MCP Backend API — Always-on HTTP service for visualization + cognitive memory.
Port 8420. Endpoints: /health, /stats, /visualize, /visualize/analyze-image,
/visualize/html-file, /cognitive-memory, /shared-brain
"""
import os, sys, json, time, tempfile, subprocess, collections, array
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

BACKEND_PORT = int(os.environ.get("MCP_BACKEND_PORT", "8420"))

def _classify(avg_b, edge_d, quads):
    if avg_b > 240: return "mostly_blank/white"
    if avg_b < 30: return "mostly_dark/black"
    vals = list(quads.values()) if quads else []
    var = max(vals) - min(vals) if vals else 0
    if edge_d > 15: return "complex_chart/diagram"
    if edge_d > 5: return "chart_with_contrast" if var > 50 else "text/moderate_content"
    if var > 80: return "split_layout/dashboard"
    return "simple_content/text"

def html_to_screenshot(html_content, width=1280, height=900, wait_ms=1000, output_path=None):
    """Render HTML -> PNG via Chromium headless, then analyze with PIL."""
    from PIL import Image
    tmp = tempfile.NamedTemporaryFile(suffix='.html', mode='w', delete=False, dir='/tmp')
    tmp.write(html_content); tmp.close()
    if output_path is None: output_path = tempfile.mktemp(suffix='.png', dir='/tmp')
    cmd = ['/usr/bin/chromium','--headless=new','--disable-gpu','--no-sandbox',
           '--disable-dev-shm-usage','--disable-extensions','--disable-software-rasterizer',
           f'--window-size={width},{height}',f'--screenshot={output_path}',f'file://{tmp.name}']
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if not os.path.exists(output_path): return {"error": f"Screenshot failed: {r.stderr[:300]}"}
        img = Image.open(output_path)
        if img.mode != 'RGB': img = img.convert('RGB')
        w, h = img.size; sz = os.path.getsize(output_path)
        pixels = list(img.getdata()); sample = pixels[::10]
        cc = collections.Counter(sample); top_c = cc.most_common(10)
        brights = [0.299*r+0.587*g+0.114*b for r,g,b in sample]
        avg_b = sum(brights)/len(brights) if brights else 0
        mn_b = min(brights) if brights else 0; mx_b = max(brights) if brights else 0
        mx, my = w//2, h//2
        qd = {"tl":img.crop((0,0,mx,my)),"tr":img.crop((mx,0,w,my)),
              "bl":img.crop((0,my,mx,h)),"br":img.crop((mx,my,w,h))}
        qb = {}
        for n,q in qd.items():
            qp = list(q.getdata())[::20]
            if qp: qb[n] = round(sum(0.299*r+0.587*g+0.114*b for r,g,b in qp)/len(qp),1)
        gray = array.array('f',[0.299*r+0.587*g+0.114*b for r,g,b in pixels])
        es,ec = 0.0,0
        for y in range(1,h-1,4):
            for x in range(1,w-1,4):
                i=y*w+x; es+=abs(gray[i+1]-gray[i-1])+abs(gray[i+w]-gray[i-w]); ec+=1
        ae = es/ec if ec else 0
        return {"screenshot_path":output_path,"analysis":{
            "dimensions":f"{w}x{h}","size_kb":round(sz/1024,1),"avg_brightness":round(avg_b,1),
            "brightness_range":f"{round(mn_b)}-{round(mx_b)}","quadrant_brightness":qb,
            "top_colors":[{"rgb":list(c),"count":n} for c,n in top_c],
            "edge_density":round(ae,2),"content_type":_classify(avg_b,ae,qb)}}
    except subprocess.TimeoutExpired: return {"error":"Chromium timeout (30s)"}
    except Exception as e: return {"error":str(e)}
    finally:
        try: os.unlink(tmp.name)
        except: pass

def analyze_image_file(image_path):
    """Analyze an existing image file with PIL."""
    from PIL import Image
    if not os.path.exists(image_path): return {"error":f"Not found: {image_path}"}
    img = Image.open(image_path)
    if img.mode != 'RGB': img = img.convert('RGB')
    w,h = img.size; pixels = list(img.getdata()); sample = pixels[::10]
    brights = [0.299*r+0.587*g+0.114*b for r,g,b in sample]
    avg_b = sum(brights)/len(brights) if brights else 0
    cc = collections.Counter(sample); top_c = cc.most_common(10)
    gray = array.array('f',[0.299*r+0.587*g+0.114*b for r,g,b in pixels])
    es,ec = 0.0,0
    for y in range(1,h-1,4):
        for x in range(1,w-1,4):
            i=y*w+x; es+=abs(gray[i+1]-gray[i-1])+abs(gray[i+w]-gray[i-w]); ec+=1
    ae = es/ec if ec else 0
    return {"path":image_path,"dimensions":f"{w}x{h}","size_kb":round(os.path.getsize(image_path)/1024,1),
            "avg_brightness":round(avg_b,1),"top_colors":[{"rgb":list(c),"count":n} for c,n in top_c],
            "edge_density":round(ae,2),"content_type":_classify(avg_b,ae,{})}

class H(BaseHTTPRequestHandler):
    def _j(self,d,s=200):
        self.send_response(s);self.send_header('Content-Type','application/json');self.end_headers()
        self.wfile.write(json.dumps(d,ensure_ascii=False,indent=2).encode())
    def _body(self):
        l=int(self.headers.get('Content-Length',0));return json.loads(self.rfile.read(l)) if l else {}
    def do_GET(self):
        if self.path=='/health': self._j({"status":"ok","uptime_s":round(time.time()-_t0,1)})
        elif self.path=='/stats': self._j(self._stats())
        else: self._j({"error":f"Unknown: {self.path}"},404)
    def do_POST(self):
        try: b=self._body()
        except Exception as e: self._j({"error":f"Bad JSON: {e}"},400);return
        if self.path=='/visualize':
            self._j(html_to_screenshot(b.get('html',''),b.get('width',1280),b.get('height',900),b.get('wait_ms',1000),b.get('output_path')))
        elif self.path=='/visualize/analyze-image': self._j(analyze_image_file(b.get('path','')))
        elif self.path=='/visualize/html-file':
            hp=b.get('path','')
            if not os.path.exists(hp): self._j({"error":f"Not found: {hp}"},404);return
            with open(hp,'r') as f: html=f.read()
            self._j(html_to_screenshot(html,b.get('width',1280),b.get('height',900),output_path=b.get('output_path')))
        elif self.path=='/cognitive-memory': self._j(self._cm(b))
        elif self.path=='/shared-brain': self._j(self._sb(b))
        else: self._j({"error":f"Unknown: {self.path}"},404)
    def _stats(self):
        s={"services":{}}
        try:
            from yantrikdb import YantrikDB
            db=YantrikDB("/data/mcp_server/data/yantrikdb_memories",256);db.set_embedder_named("potion-base-8M")
            s["services"]["yantrikdb"]={"status":"ok","memories":db.info().get("total_memories",0)}
        except Exception as e: s["services"]["yantrikdb"]={"status":"error","error":str(e)[:200]}
        s["services"]["chromium"]={"status":"ok" if os.path.exists("/usr/bin/chromium") else "missing"}
        try: from PIL import Image; s["services"]["pillow"]={"status":"ok"}
        except: s["services"]["pillow"]={"status":"missing"}
        return s
    def _cm(self,b):
        try:
            from yantrikdb import YantrikDB
            db=YantrikDB("/data/mcp_server/data/yantrikdb_memories",256);db.set_embedder_named("potion-base-8M")
            a=b.get("action","stats")
            if a=="stats": return db.info()
            elif a=="recall": return db.search(b.get("query",""),top_k=b.get("top_k",5))
            elif a=="record": return {"id":db.store(b.get("content",""),metadata=b.get("metadata",{})),"status":"stored"}
            else: return {"error":f"Unknown action: {a}"}
        except Exception as e: return {"error":str(e)[:500]}
    def _sb(self,b):
        try:
            import grpc;from cortexdb_client.cortex_client import CortexClient
            ch=grpc.insecure_channel("localhost:47821");CortexClient(ch)
            return {"status":"ok","port":47821,"action":b.get("action","status")}
        except Exception as e: return {"error":str(e)[:500]}
    def log_message(self,*a): pass

_t0=time.time()
def main():
    print(f"🧠 MCP Backend API on :{BACKEND_PORT}",file=sys.stderr)
    print(f"   Viz: Chromium headless + Pillow",file=sys.stderr)
    print(f"   Memory: yantrikdb (Rust) + cortexdb gRPC :47821",file=sys.stderr)
    srv=HTTPServer(('127.0.0.1',BACKEND_PORT),H)
    try: srv.serve_forever()
    except KeyboardInterrupt: print("\n🛑 Stopped",file=sys.stderr);srv.server_close()
if __name__=="__main__": main()

