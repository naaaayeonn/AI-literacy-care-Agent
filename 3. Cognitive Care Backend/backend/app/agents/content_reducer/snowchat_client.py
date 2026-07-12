import os
import json
import urllib.request

def is_snowchat_available() -> bool:
    """
    SnowChat API 키가 환경 변수에 설정되어 있는지 확인한다.
    """
    snowchat_key = os.getenv("SNOWCHAT_API_KEY", "")
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    
    if (not snowchat_key or snowchat_key.startswith("your_")) and (not gemini_key or gemini_key.startswith("your_")):
        return False
    return True

def _call_llm_via_snowchat(model: str, prompt: str, system_instruction: str | None = None) -> str:
    """
    Mindlogic SnowChat API Gateway를 호출하여 응답을 받는다.
    """
    snowchat_key = os.getenv("SNOWCHAT_API_KEY", "")
    
    # If SnowChat key is valid, try it first
    if snowchat_key and not snowchat_key.startswith("your_"):
        url = "https://factchat-cloud.mindlogic.ai/v1/gateway/chat/completions"
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        
        headers = {
            "Authorization": f"Bearer {snowchat_key}",
            "Content-Type": "application/json",
            "User-Agent": user_agent
        }
        
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 1024,
            "temperature": 0.7
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                choices = res_data.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "")
                    return content.strip()
                    
            raise ValueError("Empty response from SnowChat API.")
        except Exception as e:
            print(f"SnowChat API failed: {e}")
            pass # Fallthrough to Gemini if available

    # Fallback to Google Gemini
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key and not gemini_key.startswith("your_"):
        try:
            gemini_model_name = "gemini-1.5-flash" if "flash" in model.lower() else "gemini-1.5-pro"
            gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model_name}:generateContent?key={gemini_key}"
            
            parts = []
            if system_instruction:
                parts.append({"text": f"System Instruction: {system_instruction}\n\n"})
            parts.append({"text": prompt})
            
            payload = {
                "contents": [{"parts": parts}]
            }
            
            gemini_req = urllib.request.Request(
                gemini_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(gemini_req, timeout=15) as gemini_res:
                res_data = json.loads(gemini_res.read().decode("utf-8"))
                candidates = res_data.get("candidates", [])
                if candidates:
                    content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    return content.strip()
        except Exception as gemini_e:
            print(f"Gemini fallback failed: {gemini_e}")
            raise gemini_e

    raise ValueError("All API fallbacks failed or no valid API key was found.")
