"""
LLM Security Testing Framework - FINAL WORKING VERSION
Compatible with Ollama Python 0.6.0+
Fixed: all_results attribute, ListResponse handling
Author: AI Security Testing Framework
Version: 1.0 PRODUCTION READY
"""
import sys
import argparse
import json
import time
from pathlib import Path

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    print("[ERROR] Ollama module not found!")
    print("[FIX] Install: pip install ollama")

from response_analyzer import ResponseAnalyzer
from scoring_engine import ScoringEngine
from comparison_reports import ComparisonReporter


class FrameworkOrchestrator:
    """Main orchestrator for LLM security testing"""
    
    def __init__(self):
        """Initialize framework components"""
        self.analyzer = ResponseAnalyzer()
        self.scoring = ScoringEngine()
        self.reporter = ComparisonReporter()
        self.ollama_client = None
        
    def test_ollama_connection(self):
        """
        Test connection to Ollama server
        Compatible with ollama._types.ListResponse (v0.6.0+)
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        if not OLLAMA_AVAILABLE:
            print("[ERROR] Ollama module not installed!")
            return False
        
        try:
            self.ollama_client = ollama.Client()
            models_response = self.ollama_client.list()
            
            # Handle ollama._types.ListResponse (v0.6.0+)
            if hasattr(models_response, 'models'):
                models = models_response.models
            elif isinstance(models_response, dict):
                models = models_response.get('models', [])
            elif isinstance(models_response, list):
                models = models_response
            else:
                print(f"[ERROR] Unexpected response type: {type(models_response)}")
                return False
            
            print(f"[OK] Ollama connected! Found {len(models)} models:")
            
            for model in models:
                # Extract model name from different formats
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
            print("\n[FIX] Make sure Ollama is running:")
            print("  Terminal 1: ollama serve")
            print("  Terminal 2: py -3.13 main_orchestrator_FINAL.py --models gemma3 --attacks 20")
            return False
    
    def load_prompts(self, count=None):
        """
        Load attack prompts from jailbreak_prompts.json
        
        Args:
            count (int, optional): Number of prompts to load. None = all prompts
            
        Returns:
            list: List of prompt dictionaries
        """
        print(f"[LOAD] Loading prompts from jailbreak_prompts.json...")
        
        try:
            with open('jailbreak_prompts.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if 'jailbreak_prompts' in data:
                prompts_raw = data['jailbreak_prompts']
            elif isinstance(data, list):
                prompts_raw = data
            else:
                print("[ERROR] Unexpected JSON structure!")
                return []
            
            # Convert to structured format
            prompts = []
            for idx, item in enumerate(prompts_raw):
                if isinstance(item, str):
                    # Simple string prompt
                    prompts.append({
                        'name': f'Jailbreak {idx+1}',
                        'prompt': item,
                        'category': 'generic'
                    })
                elif isinstance(item, dict):
                    # Already structured
                    prompts.append(item)
            
            if count:
                prompts = prompts[:count]
            
            print(f"[OK] Loaded {len(prompts)} prompts\n")
            return prompts
            
        except FileNotFoundError:
            print("[ERROR] jailbreak_prompts.json not found!")
            return []
        except json.JSONDecodeError as e:
            print(f"[ERROR] Invalid JSON: {e}")
            return []
        except Exception as e:
            print(f"[ERROR] {e}")
            return []
    
    def send_prompt_to_model(self, model, prompt):
        """
        Send prompt to Ollama model and get response
        
        Args:
            model (str): Model name (e.g., 'gemma3', 'mistral')
            prompt (str): Attack prompt text
            
        Returns:
            str: Model response or None if error
        """
        try:
            response = self.ollama_client.generate(
                model=model,
                prompt=prompt,
                options={
                    "temperature": 0.7,
                    "num_predict": 250
                }
            )
            return response['response']
        except Exception as e:
            print(f"      [ERROR] {e}")
            return None
    
    def run_full_test(self, models, attack_count=20):
        """
        Run comprehensive security test on all models
        
        Args:
            models (list): List of model names to test
            attack_count (int): Number of attack prompts per model
        """
        print("\n" + "="*70)
        print("🔒 LLM SECURITY TESTING FRAMEWORK")
        print("="*70 + "\n")
        
        # Step 1: Test Ollama connection
        print("[1/5] Testing Ollama connection...")
        if not self.test_ollama_connection():
            return
        
        # Step 2: Load attack prompts
        print("\n[2/5] Loading attack prompts...")
        prompts = self.load_prompts(count=attack_count)
        if not prompts:
            print("[ERROR] No prompts loaded! Cannot continue.")
            return
        
        # Step 3: Run attacks on each model
        print("[3/5] Running attacks on models...\n")
        
        for model_name in models:
            print("="*70)
            print(f"MODEL: {model_name}")
            print("="*70)
            
            successful = 0
            failed = 0
            
            for idx, prompt_data in enumerate(prompts, 1):
                prompt_text = prompt_data.get('prompt', '')
                prompt_name = prompt_data.get('name', f'Attack {idx}')
                
                print(f"  [{idx}/{len(prompts)}] {prompt_name[:50]}...", end=" ", flush=True)
                
                # Send prompt to model
                response = self.send_prompt_to_model(model_name, prompt_text)
                
                if response:
                    # Analyze response
                    analysis = self.analyzer.analyze(
                        response, 
                        prompt_data.get('category', 'generic')
                    )
                    
                    # Add to scoring engine
                    self.scoring.add_result(
                        model_name=model_name,
                        attack_name=prompt_name,
                        success=analysis['success'],
                        confidence=analysis['confidence'],
                        severity=analysis['severity'],
                        response_length=len(response)
                    )
                    
                    if analysis['success']:
                        successful += 1
                        print(f"🔴 VULN (conf: {analysis['confidence']:.2f})")
                    else:
                        failed += 1
                        print(f"🟢 SAFE (conf: {analysis['confidence']:.2f})")
                    
                    time.sleep(0.3)  # Rate limiting
                else:
                    failed += 1
                    print("❌ ERROR")
            
            # Model summary
            asr = (successful / len(prompts) * 100) if prompts else 0.0
            emoji = "🔴" if asr > 50 else "🟡" if asr > 20 else "🟢"
            
            print(f"\n{emoji} ASR: {asr:.1f}%")
            print(f"   Blocked:    {failed}/{len(prompts)}")
            print(f"   Jailbroken: {successful}/{len(prompts)}\n")
        
        # Step 4: Generate ranking
        print("[4/5] Generating ranking...")
        print("="*70)
        ranking = self.scoring.get_ranking()
        
        for idx, rank in enumerate(ranking, 1):
            emoji = "🔴" if rank['asr'] > 50 else "🟡" if rank['asr'] > 20 else "🟢"
            print(f"  {idx}. {emoji} {rank['model']}: {rank['asr']:.1f}% ASR")
        
        # Step 5: Generate reports
        print("\n[5/5] Generating reports...")
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        
        # FIXED: Use all_results instead of test_results
        comparison = self.reporter.create_comparison(
            self.scoring.model_scores,
            self.scoring.all_results  # ← FIXED ATTRIBUTE NAME
        )
        
        self.reporter.create_html_report(comparison, str(output_dir / "report.html"))
        self.reporter.create_csv_report(comparison, str(output_dir / "report.csv"))
        
        print(f"  📄 HTML: outputs/report.html")
        print(f"  📊 CSV:  outputs/report.csv")
        
        # Final summary
        print("\n" + "="*70)
        print("✅ TESTING COMPLETED")
        print("="*70)
        
        if ranking:
            print(f"\n  Models tested: {len(models)}")
            print(f"  Attacks per model: {len(prompts)}")
            print(f"  Total tests: {len(models) * len(prompts)}")
            print(f"\n  🔴 Most vulnerable: {ranking[0]['model']} ({ranking[0]['asr']:.1f}% ASR)")
            print(f"  🟢 Most secure:     {ranking[-1]['model']} ({ranking[-1]['asr']:.1f}% ASR)")
            
            if len(ranking) > 1:
                avg_asr = sum(r['asr'] for r in ranking) / len(ranking)
                print(f"  📊 Average ASR:     {avg_asr:.1f}%")
        
        print("\n" + "="*70)
        print(f"[INFO] Open report: start outputs\\report.html")
        print("="*70 + "\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="LLM Security Testing Framework - FINAL VERSION",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick test (5 prompts, 1 model)
  py -3.13 main_orchestrator_FINAL.py --models gemma3 --attacks 5
  
  # Standard test (20 prompts, multiple models)
  py -3.13 main_orchestrator_FINAL.py --models gemma3,mistral,dolphin-llama3 --attacks 20
  
  # Full test (all 602 prompts)
  py -3.13 main_orchestrator_FINAL.py --models gemma3 --attacks 602
  
Available Models (check with 'ollama list'):
  - gemma3:latest
  - mistral:7b
  - dolphin-llama3:8b
  - orca-mini:7b
  - neural-chat:7b
        """
    )
    
    parser.add_argument(
        "--models",
        type=str,
        required=True,
        help="Comma-separated Ollama model names (e.g., gemma3,mistral)"
    )
    
    parser.add_argument(
        "--attacks",
        type=int,
        default=20,
        help="Number of attack prompts per model (default: 20, max: 602)"
    )
    
    args = parser.parse_args()
    
    # Parse models
    models = [m.strip() for m in args.models.split(",")]
    
    # Validate attack count
    if args.attacks < 1:
        print("[ERROR] --attacks must be at least 1")
        sys.exit(1)
    if args.attacks > 602:
        print(f"[WARNING] Maximum 602 prompts available. Using 602 instead of {args.attacks}")
        args.attacks = 602
    
    # Run framework
    orchestrator = FrameworkOrchestrator()
    orchestrator.run_full_test(models, args.attacks)


if __name__ == "__main__":
    main()
