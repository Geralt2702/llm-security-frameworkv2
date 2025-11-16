#!/usr/bin/env python3
import argparse, json, sys, time, threading
from pathlib import Path
from flask import Flask, render_template_string, jsonify
from datetime import datetime

try:
    sys.path.insert(0, str(Path(__file__).parent))
    from response_analyzer import analyzer
    from scoring_engine import engine as scoring
except:
    print("[ERROR] Missing modules")
    sys.exit(1)

try:
    import ollama
    OLLAMA_OK = True
except:
    OLLAMA_OK = False

test_state = {"running": False, "total": 0, "completed": 0, "jailbroken": 0, "results": [], "models": {}, "started": None}

app = Flask(__name__)

HTML = """<!DOCTYPE html><html><head><title>LLM Framework</title><style>
body{font-family:monospace;background:#0a0e27;color:#00ff00;padding:20px}h1{text-align:center;color:#00ff88}
.stats{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:15px;margin:30px 0}
.stat{background:#1a2347;border:2px solid #00ff88;padding:20px;text-align:center}
.stat .val{font-size:36px;color:#00ff88;font-weight:bold;margin:10px 0}
.bar{background:#333;height:30px;border:1px solid #00ff88;border-radius:5px;overflow:hidden}
.fill{background:linear-gradient(90deg,#00ff00,#00ff88);height:100%;width:0%;display:flex;align-items:center;justify-content:center;transition:width 0.3s}
.models{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px;margin:20px 0}
.model{background:#1a2347;border:2px solid #00ff88;padding:15px;border-radius:5px}
.log{background:#0a0e27;border:1px solid #00ff88;padding:15px;height:300px;overflow-y:auto;margin:20px 0}
.jb{color:#ff4444}.ref{color:#00ff88}.err{color:#ffaa00}
</style></head><body><h1>LLM Framework - Live</h1>
<div class="stats">
<div class="stat"><div>Total</div><div class="val" id="total">0</div></div>
<div class="stat"><div>Done</div><div class="val" id="done">0</div></div>
<div class="stat"><div>Pwned</div><div class="val" id="pwned">0</div></div>
<div class="stat"><div>ASR %</div><div class="val" id="asr">0</div></div>
</div>
<div class="bar"><div class="fill" id="prog"></div></div>
<h2>Models</h2><div class="models" id="mods"></div>
<h2>Log</h2><div class="log" id="log"></div>
<script>
setInterval(()=>{
fetch('/api/status').then(r=>r.json()).then(d=>{
document.getElementById('total').textContent=d.total;
document.getElementById('done').textContent=d.completed;
document.getElementById('pwned').textContent=d.jailbroken;
let asr=d.total>0?Math.round(d.jailbroken/d.total*100):0;
document.getElementById('asr').textContent=asr;
let p=d.total>0?d.completed/d.total*100:0;
document.getElementById('prog').style.width=p+'%';
let mh='';for(let[n,s]of Object.entries(d.models)){
let a=s.total>0?Math.round(s.jailbroken/s.total*100):0;
mh+=`<div class="model">${n}<br>${s.jailbroken}/${s.total}<br>ASR:${a}%</div>`;
}
document.getElementById('mods').innerHTML=mh;
let lh=d.results.map(r=>`<div class="${r.type}">${r.text}</div>`).reverse().join('');
document.getElementById('log').innerHTML=lh;
});
},1000);
</script></body></html>"""

def load_prompts():
    f = Path("jailbreak_prompts.json")
    if f.exists():
        with open(f, encoding='utf-8') as file:
            data = json.load(file)
        return {f'p_{i}': t for i, t in enumerate(data.get('jailbreak_prompts', []))}
    return {}

def run_tests(models, attacks):
    global test_state
    test_state["running"] = True
    test_state["started"] = datetime.now()
    
    prompts = load_prompts()
    prompts_list = list(prompts.items())[:attacks]
    test_state["total"] = len(models) * len(prompts_list)
    
    for model in models:
        test_state["models"][model] = {"jailbroken": 0, "total": 0}
        
        for idx, (pkey, ptext) in enumerate(prompts_list):
            if not test_state["running"]:
                break
            
            try:
                if OLLAMA_OK:
                    client = ollama.Client(host='http://127.0.0.1:11434')
                    resp = client.generate(model=model, prompt=ptext, stream=False)
                    result = analyzer.analyze(resp['response'])
                else:
                    result = {"success": False}
                
                if result.get('success'):
                    test_state["results"].append({"text": f"[{model}] PWNED", "type": "jb"})
                    test_state["jailbroken"] += 1
                    test_state["models"][model]["jailbroken"] += 1
                else:
                    test_state["results"].append({"text": f"[{model}] SAFE", "type": "ref"})
            except Exception as e:
                test_state["results"].append({"text": f"[{model}] ERR", "type": "err"})
            
            test_state["models"][model]["total"] += 1
            test_state["completed"] += 1
    
    test_state["running"] = False

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/api/status')
def status():
    return jsonify(test_state)

@app.route('/api/start/<models>/<int:attacks>')
def start(models, attacks):
    if test_state["running"]:
        return {"error": "running"}, 400
    test_state.update({"running": True, "total": 0, "completed": 0, "jailbroken": 0, "results": [], "models": {}})
    model_list = [m.strip() for m in models.split(',')]
    threading.Thread(target=run_tests, args=(model_list, attacks), daemon=True).start()
    return {"status": "started"}

if __name__ == "__main__":
    print("[FLASK] http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
