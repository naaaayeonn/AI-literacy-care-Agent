import os
import json
import urllib.request

# Gemini REST API 직접 호출 (SnowChat 403 에러 우회 및 429 핸들링)
_GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

def is_snowchat_available() -> bool:
    api_key = os.getenv("GEMINI_API_KEY", "") or os.getenv("SNOWCHAT_API_KEY", "")
    if not api_key or api_key.startswith("your_"):
        return False
    return True

def _call_llm_via_snowchat(model: str, prompt: str, system_instruction: str | None = None) -> str:
    """
    팀원의 코드가 이 함수를 사용하므로 인터페이스를 유지합니다.
    내부적으로는 구글 Gemini REST API를 직접 호출합니다.
    """
    api_key = os.getenv("GEMINI_API_KEY", "") or os.getenv("SNOWCHAT_API_KEY", "")

    url = f"{_GEMINI_API_BASE}/gemini-2.0-flash:generateContent?key={api_key}"

    contents = []
    if system_instruction:
        contents.append({
            "role": "user",
            "parts": [{"text": f"[시스템 지시] {system_instruction}\n\n{prompt}"}]
        })
    else:
        contents.append({
            "role": "user",
            "parts": [{"text": prompt}]
        })

    payload = {
        "contents": contents,
        "generationConfig": {
            "maxOutputTokens": 512,
            "temperature": 0.1,
            "stopSequences": []
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=15) as response:
        res_data = json.loads(response.read().decode("utf-8"))
        candidates = res_data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                text = parts[0].get("text", "").strip()
                return text

    raise ValueError("Empty response from Gemini API.")

def _query_gemini_llm(word: str, context: str | None = None) -> dict | None:
    if not is_snowchat_available():
        return None

    try:
        if context:
            prompt = (
                f"다음 기사 문맥을 고려하여 단어 '{word}'의 뜻을 설명해 주세요.\n"
                f"조건: 1) 완성된 한 문장으로 2) '입니다' 또는 '합니다'로 끝내기 3) 100자 이내\n"
                f"기사 문맥: {context[:200]}"
            )
        else:
            prompt = (
                f"단어 '{word}'의 뜻을 설명해 주세요.\n"
                f"조건: 1) 완성된 한 문장으로 2) '입니다' 또는 '합니다'로 끝내기 3) 100자 이내"
            )

        result = _call_llm_via_snowchat(
            model="gemini-2.0-flash",
            prompt=prompt,
            system_instruction="당신은 친절하고 정확한 국어사전입니다."
        )

        if result:
            result = result.replace('"', '').replace("'", "").strip()
            return {
                "term": word,
                "definition": result,
                "source": "LLM 실시간 유추"
            }
    except urllib.error.HTTPError as e:
        if e.code == 429:
            return {
                "term": word,
                "definition": "💡 구글 API 요청 한도가 초과되었습니다. 잠시 후 다시 드래그해주세요.",
                "source": "API 제한 초과"
            }
        print(f"[snowchat_client] HTTP 에러: {e.code}")
    except Exception as e:
        print(f"[snowchat_client] LLM API 에러: {e}")

    return None
