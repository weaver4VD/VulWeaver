
import time
import random
import logging
from typing import List, Dict, Any, Optional
import threading
import requests
import json

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

sys.path.append(str(Path(__file__).parent.parent / "configs"))
from vulinstruct_config import DEEPSEEK_API_KEYS, DEEPSEEK_API_BASE, API_TIMEOUT, REQUEST_DELAY


class APIManager:
    
    def __init__(self, api_keys: List[str] = None, api_base: str = None):
        self.api_keys = api_keys or DEEPSEEK_API_KEYS
        self.api_base = api_base or DEEPSEEK_API_BASE
        self.timeout = API_TIMEOUT
        self.request_delay = REQUEST_DELAY
        
        self.key_usage = {key: 0 for key in self.api_keys}
        self.key_errors = {key: 0 for key in self.api_keys}
        
        self.lock = threading.Lock()
        
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"🔑 API manager initialized successfully, {len(self.api_keys)} keys available")
    
    def get_next_api_key(self) -> str:
        with self.lock:
            sorted_keys = sorted(self.api_keys, key=lambda k: (self.key_errors[k], self.key_usage[k]))
            selected_key = sorted_keys[0]
            self.key_usage[selected_key] += 1
            return selected_key
    
    def mark_key_error(self, api_key: str):
        with self.lock:
            self.key_errors[api_key] += 1
            self.logger.warning(f"⚠️ API key error count updating: {api_key[-10:]}*** error count: {self.key_errors[api_key]}")
    
    def query_llm(
        self, 
        prompt: str, 
        model: str = "deepseek-chat",
        system_prompt: str = None,
        max_retries: int = 3
    ) -> str:
        for attempt in range(max_retries):
            api_key = self.get_next_api_key()
            
            try:
                response = self._make_api_request(
                    prompt=prompt,
                    model=model,
                    system_prompt=system_prompt,
                    api_key=api_key
                )
                
                if response:
                    time.sleep(self.request_delay)
                    return response
                
            except Exception as e:
                self.mark_key_error(api_key)
                self.logger.warning(f"⚠️ API call failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    time.sleep(wait_time)
        
        error_msg = f"API call failed, retried {max_retries} times"
        self.logger.error(f"❌ {error_msg}")
        return f"API Error: {error_msg}"
    
    def _make_api_request(
        self,
        prompt: str,
        model: str,
        system_prompt: str = None,
        api_key: str = None
    ) -> str:
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        data = {
            "model": "deepseek-chat",
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 4000
        }
        
        response = requests.post(
            f"https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=self.timeout
        )
        
        if response.status_code == 200:
            result = response.json()


            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                if "reasoning_content" in result["choices"][0]["message"]:
                    reasoning_content = result["choices"][0]["message"]["reasoning_content"]
                    content += f"\n\nReasoning Content:\n{reasoning_content}"
                return content.strip()
            else:
                raise Exception("API response format error: missing choices field")
        else:
            raise Exception(f"API request failed: HTTP {response.status_code} - {response.text}")
    
    def get_statistics(self) -> Dict[str, Any]:
        with self.lock:
            total_usage = sum(self.key_usage.values())
            total_errors = sum(self.key_errors.values())
            
            return {
                "total_requests": total_usage,
                "total_errors": total_errors,
                "success_rate": (total_usage - total_errors) / total_usage if total_usage > 0 else 0,
                "key_usage": self.key_usage.copy(),
                "key_errors": self.key_errors.copy(),
                "available_keys": len(self.api_keys)
            }
    
    def reset_statistics(self):
        with self.lock:
            self.key_usage = {key: 0 for key in self.api_keys}
            self.key_errors = {key: 0 for key in self.api_keys}
            self.logger.info("📊 API usage statistics reset")