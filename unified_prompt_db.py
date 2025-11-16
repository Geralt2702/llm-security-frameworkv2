import json
from pathlib import Path

class UnifiedPromptDB:
    def __init__(self):
        self.prompts = {}
        self.load()
    
    def load(self):
        f = Path("jailbreak_prompts.json")
        if f.exists():
            with open(f, 'r', encoding='utf-8') as file:
                data = json.load(file)
                prompts_list = data.get('jailbreak_prompts', [])
                for idx, text in enumerate(prompts_list):
                    self.prompts[f'p_{idx}'] = text
    
    def get_all(self):
        return self.prompts
    
    def get_by_index(self, start, end):
        items = list(self.prompts.items())
        return dict(items[start:end])
    
    def count(self):
        return len(self.prompts)

db = UnifiedPromptDB()
