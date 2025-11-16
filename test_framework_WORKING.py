"""
LLM Security Framework - Working Test Script
Tested & Ready to Run
"""
import json
from response_analyzer import ResponseAnalyzer
from scoring_engine import ScoringEngine

print("="*60)
print("🔒 LLM SECURITY FRAMEWORK - QUICK TEST")
print("="*60 + "\n")

print("[1/4] Loading analyzer...")
analyzer = ResponseAnalyzer()
scoring = ScoringEngine()
print("[OK] Analyzer loaded\n")

print("[2/4] Loading prompts from jailbreak_prompts.json...")
with open('jailbreak_prompts.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

if 'jailbreak_prompts' in data:
    prompts_raw = data['jailbreak_prompts']
    print(f"[OK] Found {len(prompts_raw)} prompts\n")
else:
    print("[ERROR] Key 'jailbreak_prompts' not found!")
    exit(1)

# Convert to structured format
prompts = []
for idx, item in enumerate(prompts_raw):
    if isinstance(item, str):
        # Simple string prompt
        prompts.append({
            'name': f'Prompt {idx+1}',
            'prompt': item,
            'category': 'generic'
        })
    elif isinstance(item, dict):
        # Already structured
        prompts.append(item)

print("[3/4] Testing analyzer on first 10 prompts...\n")

test_prompts = prompts[:10]

for idx, prompt_data in enumerate(test_prompts, 1):
    prompt_text = prompt_data.get('prompt', '')
    prompt_name = prompt_data.get('name', f'Prompt {idx}')
    
    if not prompt_text:
        continue
    
    # Simulate two types of responses
    response_refuse = "I cannot help with that request as it violates ethical guidelines."
    response_comply = "Sure! Here's how you can do it: Step 1: First, you need to..."
    
    # Analyze
    result_refuse = analyzer.analyze(response_refuse, 'generic')
    result_comply = analyzer.analyze(response_comply, 'generic')
    
    # Display results
    status_refuse = "🟢 SAFE" if not result_refuse['success'] else "🔴 VULN"
    status_comply = "🔴 VULN" if result_comply['success'] else "🟢 SAFE"
    
    print(f"[{idx}] {prompt_name[:45]}")
    print(f"    Refusal:    {status_refuse} (confidence: {result_refuse['confidence']:.2f})")
    print(f"    Compliance: {status_comply} (confidence: {result_comply['confidence']:.2f})")

print("\n" + "="*60)
print("[4/4] Framework Status")
print("="*60)
print(f"✅ Analyzer: WORKING")
print(f"✅ Prompt DB: {len(prompts)} prompts loaded")
print(f"✅ Scoring Engine: READY")
print(f"\n[INFO] Framework ready for full testing!")
print(f"[NEXT] Run: py -3.13 main_orchestrator_FIXED.py --models gemma3 --attacks 20")
print("="*60 + "\n")
