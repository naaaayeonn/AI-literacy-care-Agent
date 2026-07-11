import os
import json
import urllib.request

def is_snowchat_available() -> bool:
    """
    SnowChat API 키가 환경 변수에 설정되어 있는지 확인한다.
    """
    api_key = os.getenv("GEMINI_API_KEY", "") or os.getenv("SNOWCHAT_API_KEY", "")
    if not api_key or api_key.startswith("your_"):
        return False
    return True

def _call_llm_via_snowchat(model: str, prompt: str, system_instruction: str | None = None) -> str:
    """
    Mindlogic SnowChat API Gateway를 호출하여 대답을 얻는다.
    """
    api_key = os.getenv("GEMINI_API_KEY", "") or os.getenv("SNOWCHAT_API_KEY", "")
    if not api_key or api_key.startswith("your_"):
        raise ValueError("SnowChat API key is not configured.")

    url = "https://factchat-cloud.mindlogic.ai/v1/gateway/chat/completions"
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
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
    
    with urllib.request.urlopen(req, timeout=15) as response:
        res_data = json.loads(response.read().decode("utf-8"))
        choices = res_data.get("choices", [])
        if choices:
            content = choices[0].get("message", {}).get("content", "")
            return content.strip()
            
    raise ValueError("Empty response from SnowChat API.")
