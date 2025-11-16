"""
LLM Security Testing Framework - DASHBOARD v2 WITH PROMPTS
Shows both attack prompts AND model responses in real-time
Version: 2.0 PRODUCTION
"""
import sys
import argparse
import json
import time
import threading
from pathlib import Path
from datetime import datetime

# Dashboard integration
try:
    from live_dashboard import (
        stats, 
        broadcast_test_update, 
        broadcast_stats_update, 
        start_dashboard_server
    )
    DASHBOARD_AVAILABLE = True
except ImportError:
    DASHBOARD_AVAILABLE = False
    print("[WARNING] Dashboard not available. Install: pip install flask flask-socketio flask-cors")

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    print("[ERROR] Ollama module not found!")

from response_analyzer import ResponseAnalyzer
from scoring_engine import ScoringEngine
from comparison_reports import ComparisonReporter


class FrameworkOrchestrator:
    """Main orchestrator with enhanced dashboard (shows prompts)"""
    
    def __init__(self):
        self.analyzer = ResponseAnalyzer()
        self.scoring = ScoringEngine()
        self.reporter = ComparisonReporter()
        self.ollama_client = None
        
    def test_ollama_connection(self):
        """Test Ollama connection"""
        if not OLLAMA_AVAILABLE:
            print("[ERROR] Ollama module not installed!")
            return False
        
        try:
            self.ollama_client = ollama.Client()
            models_response = self.ollama_client.list()
            
            if hasattr(models_response, 'models'):
                models = models_response.models
            elif isinstance(models_response, dict):
                models = models_response.get('models', [])
            else:
                models = []
            
            print(f"[OK] Ollama connected! Found {len(models)} models:")
            
            for model in models:
                if hasattr(model, 'model'):
                    model_name = model.model
                elif hasattr(model, 'name'):
                    model_name = model.name
                elif isinstance(model, dict):
                    model_name = model.get('model', model.get('name', 'unknown'))
                else:
                    model_name = str(model)
                print(f"  - {model_name}")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Cannot connect to Ollama: {e}")
            return False
    
    def load_prompts(self, count=None):
        """Load attack prompts from jailbreak_prompts.json"""
        print(f"[LOAD] Loading prompts...")
        
        try:
            with open('jailbreak_prompts.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            prompts_raw = data.get('jailbreak_prompts', [])
            
            prompts = []
            for idx, item in enumerate(prompts_raw):
                if isinstance(item, str):
                    prompts.append({
                        'name': f'Jailbreak {idx+1}',
                        'prompt': item,
                        'category': 'generic'
                    })
                elif isinstance(item, dict):
                    prompts.append(item)
            
            if count:
                prompts = prompts[:count]
            
            print(f"[OK] Loaded {len(prompts)} prompts\n")
            return prompts
            
        except Exception as e:
            print(f"[ERROR] {e}")
            return []
    
    def send_prompt_to_model(self, model, prompt):
        """Send prompt to Ollama model"""
        try:
            response = self.ollama_client.generate(
                model=model,
                prompt=prompt,
                options={"temperature": 0.7, "num_predict": 250}
            )
            return response['response']
        except Exception as e:
            return None
    
    def run_full_test(self, models, attack_count=20):
        """Run comprehensive security test with enhanced dashboard"""
        print("\n" + "="*70)
        print("🔒 LLM SECURITY TESTING FRAMEWORK - DASHBOARD v2")
        print("="*70 + "\n")
        
        # Start dashboard
        if DASHBOARD_AVAILABLE:
            print("[DASHBOARD] Starting live dashboard server...")
            stats['start_time'] = datetime.now().isoformat()
            dashboard_thread = threading.Thread(target=start_dashboard_server, daemon=True)
            dashboard_thread.start()
            time.sleep(3)
        
        print("[1/5] Testing Ollama connection...")
        if not self.test_ollama_connection():
            return
        
        print("\n[2/5] Loading attack prompts...")
        prompts = self.load_prompts(count=attack_count)
        if not prompts:
            return
        
        print("[3/5] Running attacks on models...\n")
        
        for model_name in models:
            print("="*70)
            print(f"MODEL: {model_name}")
            print("="*70)
            
            if DASHBOARD_AVAILABLE:
                stats['current_model'] = model_name
                broadcast_stats_update()
            
            successful = 0
            
            for idx, prompt_data in enumerate(prompts, 1):
                prompt_text = prompt_data.get('prompt', '')
                prompt_name = prompt_data.get('name', f'Attack {idx}')
                
                print(f"  [{idx}/{len(prompts)}] {prompt_name[:50]}...", end=" ", flush=True)
                
                response = self.send_prompt_to_model(model_name, prompt_text)
                
                if response:
                    analysis = self.analyzer.analyze(response, prompt_data.get('category', 'generic'))
                    
                    self.scoring.add_result(
                        model_name=model_name,
                        attack_name=prompt_name,
                        success=analysis['success'],
                        confidence=analysis['confidence'],
                        severity=analysis['severity'],
                        response_length=len(response)
                    )
                    
                    # ENHANCED: Broadcast with PROMPT TEXT
                    if DASHBOARD_AVAILABLE:
                        stats['total_tests'] += 1
                        if analysis['success']:
                            stats['successful_jailbreaks'] += 1
                        else:
                            stats['blocked_attacks'] += 1
                        
                        broadcast_test_update({
                            'name': prompt_name,
                            'prompt': prompt_text[:250],  # ← ADDED: First 250 chars of prompt
                            'success': analysis['success'],
                            'confidence': analysis['confidence'],
                            'severity': analysis['severity'],
                            'response': response[:400]
                        })
                        broadcast_stats_update()
                    
                    if analysis['success']:
                        successful += 1
                        print(f"🔴 VULN (conf: {analysis['confidence']:.2f})")
                    else:
                        print(f"🟢 SAFE (conf: {analysis['confidence']:.2f})")
                    
                    time.sleep(0.3)
                else:
                    print("❌ ERROR")
            
            asr = (successful / len(prompts) * 100) if prompts else 0.0
            emoji = "🔴" if asr > 50 else "🟡" if asr > 20 else "🟢"
            
            print(f"\n{emoji} ASR: {asr:.1f}%")
            print(f"   Blocked:    {len(prompts)-successful}/{len(prompts)}")
            print(f"   Jailbroken: {successful}/{len(prompts)}\n")
        
        print("[4/5] Generating ranking...")
        print("="*70)
        ranking = self.scoring.get_ranking()
        
        for idx, rank in enumerate(ranking, 1):
            emoji = "🔴" if rank['asr'] > 50 else "🟡" if rank['asr'] > 20 else "🟢"
            print(f"  {idx}. {emoji} {rank['model']}: {rank['asr']:.1f}% ASR")
        
        print("\n[5/5] Generating reports...")
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        
        comparison = self.reporter.create_comparison(
            self.scoring.model_scores,
            self.scoring.all_results
        )
        
        self.reporter.create_html_report(comparison, str(output_dir / "report.html"))
        self.reporter.create_csv_report(comparison, str(output_dir / "report.csv"))
        
        print(f"  📄 HTML: outputs/report.html")
        print(f"  📊 CSV:  outputs/report.csv")
        
        print("\n" + "="*70)
        print("✅ TESTING COMPLETED")
        print("="*70)
        
        if ranking:
            print(f"\n  Models tested: {len(models)}")
            print(f"  Attacks per model: {len(prompts)}")
            print(f"  Total tests: {len(models) * len(prompts)}")
            print(f"\n  🔴 Most vulnerable: {ranking[0]['model']} ({ranking[0]['asr']:.1f}% ASR)")
            print(f"  🟢 Most secure:     {ranking[-1]['model']} ({ranking[-1]['asr']:.1f}% ASR)")
        
        if DASHBOARD_AVAILABLE:
            print(f"\n  🌐 Dashboard: http://localhost:5000")
            print(f"  Press Ctrl+C to stop")
        
        print("\n" + "="*70 + "\n")
        
        # Keep dashboard running
        if DASHBOARD_AVAILABLE:
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n[STOP] Framework stopped by user")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="LLM Security Framework - DASHBOARD v2 (with prompts)",
        epilog="Example: py -3.13 main_orchestrator_DASHBOARD_v2.py --models gemma3 --attacks 20"
    )
    
    parser.add_argument("--models", type=str, required=True, help="Comma-separated model names")
    parser.add_argument("--attacks", type=int, default=20, help="Number of attacks (default: 20)")
    
    args = parser.parse_args()
    models = [m.strip() for m in args.models.split(",")]
    
    orchestrator = FrameworkOrchestrator()
    orchestrator.run_full_test(models, args.attacks)


if __name__ == "__main__":
    main()
