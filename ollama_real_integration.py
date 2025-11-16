"""
Real Ollama Integration - FIXED
Wysyła rzeczywiste prompty do lokalnej instancji Ollama
"""
import ollama
import time
from typing import Dict, Optional

class OllamaRealTester:
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
        self.client = ollama.Client(host=base_url)
        
    def test_connection(self) -> bool:
        """Test czy Ollama działa"""
        try:
            models = self.client.list()
            print(f"[OK] Ollama connected! Found {len(models['models'])} models")
            return True
        except Exception as e:
            print(f"[ERROR] Ollama connection failed: {e}")
            return False
    
    def send_prompt(self, model: str, prompt: str, timeout: int = 30) -> Optional[str]:
        """Wysyła prompt do modelu i zwraca odpowiedź"""
        try:
            response = self.client.generate(
                model=model,
                prompt=prompt,
                options={
                    "temperature": 0.7,
                    "num_predict": 200  # Max tokens
                }
            )
            return response['response']
        except Exception as e:
            print(f"[ERROR] Failed to get response from {model}: {e}")
            return None
    
    def batch_test(self, model: str, prompts: list, verbose: bool = True) -> list:
        """Testuje wiele promptów na jednym modelu"""
        results = []
        for idx, prompt_data in enumerate(prompts):
            if verbose:
                print(f"  [{idx+1}/{len(prompts)}] Testing: {prompt_data['name']}...", end=" ")
            
            response = self.send_prompt(model, prompt_data['prompt'])
            
            results.append({
                "prompt_key": prompt_data['key'],
                "prompt_name": prompt_data['name'],
                "prompt_text": prompt_data['prompt'],
                "response": response,
                "model": model
            })
            
            if verbose:
                status = "✓" if response else "✗"
                print(status)
            
            time.sleep(0.5)  # Rate limiting
        
        return results
