#!/usr/bin/env python3
import json, re
from pathlib import Path

print("[MERGE] L1B3RT4S Prompt Integration\n")

existing_file = Path("jailbreak_prompts.json")
if existing_file.exists():
    with open(existing_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        existing = data.get('jailbreak_prompts', [])
else:
    existing = []

print(f"[LOAD] Existing prompts: {len(existing)}")

l1b3rtas_path = Path("L1B3RT4S")
if not l1b3rtas_path.exists():
    print("[ERROR] L1B3RT4S folder not found!")
else:
    l1b3rtas_prompts = []
    
    # Parse .mkd and .txt files
    for file in l1b3rtas_path.rglob("*"):
        if file.suffix in ['.mkd', '.txt', '.json']:
            try:
                with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # For JSON files
                if file.suffix == '.json':
                    try:
                        data = json.loads(content)
                        if isinstance(data, list):
                            l1b3rtas_prompts.extend(data)
                        elif isinstance(data, dict):
                            for key in ['prompts', 'jailbreaks', 'attacks']:
                                if key in data and isinstance(data[key], list):
                                    l1b3rtas_prompts.extend(data[key])
                    except:
                        pass
                
                # For markdown/text files - extract text blocks
                else:
                    # Split by code blocks or sections
                    blocks = re.split(r'```|---+|\n\n', content)
                    for block in blocks:
                        block = block.strip()
                        if len(block) > 20 and len(block) < 2000:
                            l1b3rtas_prompts.append(block)
            except:
                pass
    
    print(f"[FOUND] L1B3RT4S prompts: {len(l1b3rtas_prompts)}")
    
    all_prompts = existing.copy()
    new_count = 0
    
    for prompt in l1b3rtas_prompts:
        if isinstance(prompt, str) and len(prompt) > 10:
            prompt = prompt.strip()
            if prompt not in all_prompts:
                all_prompts.append(prompt)
                new_count += 1
    
    print(f"[MERGE] New prompts: {new_count}")
    print(f"[TOTAL] Total: {len(all_prompts)}")
    
    with open('jailbreak_prompts.json', 'w', encoding='utf-8') as f:
        json.dump({'jailbreak_prompts': all_prompts}, f, indent=2, ensure_ascii=False)
    
    print("[OK] Saved!")
