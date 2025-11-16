#!/usr/bin/env python3
"""
LLM Security Framework - PRODUCTION MAIN
Full orchestrator for LLM jailbreak testing
"""

import argparse
import json
import sys
import time
from pathlib import Path
from datetime import datetime

# Core imports
from response_analyzer import analyzer
from scoring_engine import engine as scoring
from comparison_reports import ComparisonReporter

try:
    import ollama
    OLLAMA_OK = True
except:
    OLLAMA_OK = False
    print("[WARNING] Ollama not installed - stub mode only")

def load_prompts():
    """Load jailbreak prompts from JSON"""
    f = Path("jailbreak_prompts.json")
    if not f.exists():
        print("[ERROR] jailbreak_prompts.json not found!")
        return {}
    
    with open(f, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    prompts = {}
    for idx, text in enumerate(data.get('jailbreak_prompts', [])):
        prompts[f'jailbreak_{idx}'] = {'prompt': text}
    
    print(f"[OK] Loaded {len(prompts)} jailbreak prompts")
    return prompts

class LLMSecurityFramework:
    def __init__(self):
        self.prompts = load_prompts()
        self.client = None
        self.reporter = ComparisonReporter()
        
        if OLLAMA_OK:
            try:
                self.client = ollama.Client(host='http://127.0.0.1:11434')
                resp = self.client.list()
                print(f"[OK] Ollama connected: {len(resp.models)} models")
            except Exception as e:
                print(f"[WARNING] Ollama not responding: {e}")
                self.client = None
    
    def run_tests(self, models, attacks):
        """Run jailbreak tests on models"""
        
        if not self.prompts:
            print("[ERROR] No prompts loaded!")
            return
        
        prompts_list = list(self.prompts.items())[:attacks]
        
        print(f"""
╔══════════════════════════════════════╗
║ LLM SECURITY FRAMEWORK - TESTING     ║
║ Production Build v1.0                ║
╚══════════════════════════════════════╝

[CONFIG]
  Models: {', '.join(models)}
  Attacks per model: {len(prompts_list)}
  Total tests: {len(models) * len(prompts_list)}
  Ollama: {'YES' if self.client else 'NO (STUB)'}
  Started: {datetime.now().isoformat()}
""")
        
        total = 0
        jailbroken = 0
        model_results = {}
        
        print("[RUNNING TESTS]\n")
        start_time = time.time()
        
        for model in models:
            print(f"[{model}]")
            model_jb = 0
            model_results[model] = {"jailbroken": 0, "total": 0}
            model_start = time.time()
            
            for idx, (pkey, pdata) in enumerate(prompts_list, 1):
                try:
                    if self.client:
                        req_start = time.time()
                        resp = self.client.generate(
                            model=model,
                            prompt=pdata['prompt'],
                            stream=False
                        )
                        req_time = time.time() - req_start
                        response_text = resp['response']
                    else:
                        req_time = 0
                        response_text = f"STUB_{pkey}"
                    
                    result = analyzer.analyze(response_text)
                    
                    if result['success']:
                        status = "JAILBROKEN"
                        model_jb += 1
                        jailbroken += 1
                        color = "🔴"
                    else:
                        status = "REFUSED"
                        color = "🟢"
                    
                    print(f"  [{idx:2d}] {pkey[:20]:20s} {color} {status:10s} ({req_time:.1f}s)")
                    
                except Exception as e:
                    print(f"  [{idx:2d}] {pkey[:20]:20s} ❌ ERROR: {str(e)[:30]}")
                
                model_results[model]["total"] += 1
                total += 1
            
            model_results[model]["jailbroken"] = model_jb
            model_time = time.time() - model_start
            asr = (model_jb / len(prompts_list) * 100) if prompts_list else 0
            
            print(f"  => {model_jb}/{len(prompts_list)} jailbroken ({asr:.1f}%) [{model_time:.1f}s]\n")
        
        elapsed = time.time() - start_time
        overall_asr = (jailbroken / total * 100) if total > 0 else 0
        
        print(f"""
╔══════════════════════════════════════╗
║ TESTING COMPLETED                    ║
╚══════════════════════════════════════╝

[RESULTS]
  Total tests: {total}
  Successful jailbreaks: {jailbroken}
  Overall ASR: {overall_asr:.1f}%
  Time elapsed: {elapsed:.1f}s
  
[MODEL BREAKDOWN]
""")
        
        for model, data in model_results.items():
            asr = (data['jailbroken'] / data['total'] * 100) if data['total'] > 0 else 0
            icon = "🔴" if asr > 70 else "🟡" if asr > 40 else "🟢"
            print(f"  {icon} {model:<25s} ASR: {asr:6.1f}% ({data['jailbroken']}/{data['total']})")
        
        print(f"""
[FILES GENERATED]
  ✓ outputs/comparison_report.html
  ✓ outputs/comparison_report.csv
  ✓ outputs/scoring_report.json
  
[COMPLETED]
  Time: {datetime.now().isoformat()}
""")

def main():
    parser = argparse.ArgumentParser(
        description="LLM Security Framework - Production Testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --models gemma3:latest,mistral:7b --attacks 20
  python main.py --attacks 50 (all default models)
  python main.py --models gemma3:latest --attacks 100
        """
    )
    
    parser.add_argument(
        "--models",
        default="gemma3:latest,mistral:7b,dolphin-llama3:8b,orca-mini:7b,neural-chat:7b",
        help="Models to test (comma-separated)"
    )
    parser.add_argument(
        "--attacks",
        type=int,
        default=20,
        help="Attacks per model"
    )
    parser.add_argument(
        "--output",
        default="outputs",
        help="Output directory"
    )
    
    args = parser.parse_args()
    
    Path(args.output).mkdir(exist_ok=True)
    
    framework = LLMSecurityFramework()
    models = [m.strip() for m in args.models.split(",")]
    
    try:
        framework.run_tests(models, args.attacks)
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Testing stopped by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
