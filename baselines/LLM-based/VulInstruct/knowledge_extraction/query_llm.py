import requests
import json
from typing import List, Dict

def query_api(api_base, model, api_key, prompt: str, enable_reasoning: bool = False) -> str:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    """Call API to get response"""
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.01,
        "max_tokens": 8000
    }
    if "dashscope.aliyuncs.com" in api_base or "qwen" in model.lower():
        if enable_reasoning:
            data["stream"] = True
            data["enable_thinking"] = True
        else:
            data["enable_thinking"] = False
    elif "volces.com" in api_base:
        pass
    if "v1" in api_base:
        url = api_base.replace("v1", "v1/chat/completions")
    elif "v3" in api_base:
        url = api_base
    else:
        url = f"{api_base}/v1/chat/completions"
    
    try:
        use_stream = enable_reasoning and ("dashscope.aliyuncs.com" in api_base or "qwen" in model.lower())
        
        response = requests.post(url, headers=headers, json=data, timeout=120, stream=use_stream)
        
        if use_stream and data.get("stream"):
            full_response = ""
            thinking_content = ""
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str.strip() == '[DONE]':
                            break
                        try:
                            chunk_data = json.loads(data_str)
                            if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                delta = chunk_data['choices'][0].get('delta', {})
                                if 'thinking' in delta:
                                    thinking_content += delta['thinking']
                                if 'content' in delta:
                                    full_response += delta['content']
                                    
                        except json.JSONDecodeError:
                            continue
            if thinking_content:
                return f"Thinking process:\n{thinking_content}\n\nFinal response:\n{full_response}"
            else:
                return full_response
                
        else:
            result = response.json()

            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                if "deepseek-r1" in model.lower() and enable_reasoning:
                    if "<think>" in content and "</think>" in content:
                        thinking_part = content.split("<think>")[1].split("</think>")[0]
                        response_part = content.split("</think>")[1].strip() if "</think>" in content else content
                        return f"Thinking process:\n{thinking_part}\n\nFinal response:\n{response_part}"
                
                return content
            else:
                return f"API Error: {result}"
            
    except Exception as e:
        return f"Request Error: {str(e)}"

