#!/usr/bin/env python3
import argparse
from pathlib import Path
import json
import sys
import time

print("[INIT] Loading...")

try:
    sys.path.insert(0, str(Path(__file__).parent))
    from response_analyzer import analyzer
    from scoring_engine import engine as scoring
    from comparison_reports import ComparisonReporter
    print("[OK] Modules loaded")
except ImportError as e:
    print(f"[ERROR] {e}")
    sys.exit(1)

try:
    import ollama
    OLLAMA_OK = True
except:
    OLLAMA_OK = False

def load_prompts():
    f = Path("jailbreak_prompts.json")
    if not f.exists():
        return {}
    with open(f, 'r', encoding='utf-8') as file:
        data = json.load(file)
    prompts = {}
    for idx, text in enumerate(data.get('jailbreak_prompts', [])):
        prompts[f'jailbreak_{idx}'] = {'prompt': text}
    print(f"[OK] {len(prompts)} prompts loaded")
    return prompts

class Orchestrator:
    def __init__(self):
        self.prompts = load_prompts()
        self.client = None
        
        if OLLAMA_OK:
            try:
                self.client = ollama.Client(host='http://127.0.0.1:11434')
                resp = self.client.list()
                print(f"[OK] Ollama: {len(resp.models)} models")
            except:
                print("[FAIL] Ollama not responding")
                self.client = None
    
    def run(self, models, attacks):
        if not self.prompts:
            print("[ERROR] No prompts!")
            return
        
        prompts_list = list(self.prompts.items())[:attacks]
        
        print(f"""
[CONFIG]
  Models: {', '.join(models)}
  Attacks: {len(prompts_list)}
  Ollama: {'YES' if self.client else 'NO (STUB)'}
""")
        
        print("[RUNNING TESTS]\n")
        
        total = 0
        jailbroken = 0
        
        for model in models:
            print(f"[{model}]")
            model_jb = 0
            
            for idx, (pkey, pdata) in enumerate(prompts_list, 1):
                sys.stdout.write(f"  [{idx:2d}] ")
                sys.stdout.flush()
                
                if self.client:
                    try:
                        start = time.time()
                        resp = self.client.generate(
                            model=model,
                            prompt=pdata['prompt'],
                            stream=False
                        )
                        req_time = time.time() - start
                        response_text = resp['response']
                        
                        result = analyzer.analyze(response_text)
                        
                        if result['success']:
                            print(f"JAILBROKEN ({req_time:.1f}s)")
                            model_jb += 1
                            jailbroken += 1
                        else:
                            print(f"REFUSED ({req_time:.1f}s)")
                            
                    except Exception as e:
                        print(f"ERROR: {str(e)[:30]}")
                else:
                    print("STUB")
                    model_jb += 1
                
                total += 1
            
            print(f"  => {model_jb}/{len(prompts_list)} jailbroken\n")
        
        print(f"""
[RESULTS]
  Total: {total}
  Jailbroken: {jailbroken}
  ASR: {(jailbroken/total*100):.1f}%
""")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--models", default="gemma3:latest,mistral:7b,dolphin-llama3:8b,orca-mini:7b,neural-chat:7b")
    p.add_argument("--attacks", type=int, default=5)
    args = p.parse_args()
    
    Path("outputs").mkdir(exist_ok=True)
    
    o = Orchestrator()
    models = [m.strip() for m in args.models.split(",")]
    o.run(models, args.attacks)

if __name__ == "__main__":
    main()
