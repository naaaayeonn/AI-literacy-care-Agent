import hashlib
import json
import logging
from ..agents.content_reducer.snowchat_client import is_snowchat_available, _call_llm_via_snowchat

logger = logging.getLogger(__name__)

def generate_ox_quiz(summary: str, paragraph: str, chunk_id: str, session_id: str) -> dict:
    """
    문단 요약(summary)과 원문(paragraph)을 기반으로 O/X 퀴즈를 생성합니다 (결정론적 캐싱용).
    LLM 생성은 퀴즈 출제 시점에 JIT로 수행합니다.
    """
    quiz_id = f"quiz_{session_id}_{chunk_id}"
    
    h_val = int(hashlib.md5(chunk_id.encode('utf-8')).hexdigest(), 16)
    is_even = (h_val % 2 == 0)
    
    import re
    if is_even:
        sentences = re.split(r'(?<=[.!?])\s+', summary)
        statement = sentences[0] if sentences else summary
        if not statement: statement = "본문의 내용을 올바르게 요약했습니다."
        answer = True
        explanation = "요약과 일치합니다."
    else:
        statement = "이 문단은 앞의 내용과 완전히 반대됩니다."
        answer = False
        explanation = "원문의 내용과 다른 진술입니다."

    return {
        "quizId": quiz_id,
        "type": "ox",
        "question": statement,
        "statement": statement,
        "options": ["O", "X"],
        "answer": answer,
        "explanation": explanation,
        "sourceChunkId": chunk_id
    }


def select_quiz_for_state(state: dict, ignore_asked: bool = False) -> list[dict]:
    """
    현재 사용자 상태(방금 읽던 position)를 바탕으로 미출제 퀴즈 최대 3개를 선택합니다.
    ignore_asked가 True이면 이미 출제된 퀴즈라도 다시 선택합니다 (100% 달성 시 사용).
    """
    quizzes = state.get("quizzes", {})
    if not quizzes:
        return []
        
    asked_quiz_ids = state.get("asked_quiz_ids", [])
    events = state.get("reading_events", [])
    chunks = state.get("chunks", [])
    
    if not events or not chunks:
        return []
        
    # 가장 최근 이벤트의 position 추출
    latest_position = events[-1].get("position", 0.0)
    if latest_position is None:
        latest_position = 0.0
        
    # 방금 읽은 문단 인덱스 추정
    chunk_index = round(latest_position * (len(chunks) - 1))
    chunk_index = max(0, min(chunk_index, len(chunks) - 1))
    
    selected = []
    # 현재 문단부터 최대 3개 문단을 역순으로 탐색
    for i in range(chunk_index, -1, -1):
        target_chunk_id = chunks[i].get("chunk_id")
        if not target_chunk_id:
            continue
            
        quiz = quizzes.get(target_chunk_id)
        if not quiz:
            continue
            
        # 이미 출제된 퀴즈인지 확인
        if ignore_asked or (quiz["quizId"] not in asked_quiz_ids):
            # 여기서 JIT로 LLM 기반 단문 퀴즈 생성
            if is_snowchat_available():
                paragraph = chunks[i].get("original_text") or chunks[i].get("restructured_text", "")
                summary = chunks[i].get("summary") or chunks[i].get("restructured_text") or chunks[i].get("original_text", "")
                try:
                    prompt = f"""다음 문단을 읽고 내용을 확인하는 O/X 퀴즈를 딱 1문제 만들어주세요.
문단: {paragraph}
요약: {summary}

[조건]
1. 진술문(statement)은 반드시 **20자 내외의 짧고 명확한 한 문장**이어야 합니다. ("~이다.", "~다." 형식)
2. 정답(answer)은 무작위로 True(O) 또는 False(X)가 되도록 하세요.
3. 해설(explanation)은 1~2문장으로 간결하게 적어주세요.
4. JSON 내부에 큰따옴표(")를 포함해야 할 경우 반드시 백슬래시로 이스케이프(\\")하세요. 줄바꿈(\n)은 절대 포함하지 마세요. (JSON 파싱 에러 방지)
5. 반드시 아래 JSON 형식으로만 응답하세요. 다른 말은 절대 하지 마세요.

{{
  "statement": "짧은 진술문",
  "answer": true,
  "explanation": "해설 내용"
}}"""
                    res_text = _call_llm_via_snowchat("gemini-2.5-flash", prompt)
                    
                    # JSON 블록 추출 로직 강화
                    import re
                    match = re.search(r'\{.*\}', res_text.replace('\n', ' '), re.DOTALL)
                    if match:
                        res_text = match.group(0)
                        
                    res_json = json.loads(res_text)
                    if res_json.get("statement"):
                        quiz["question"] = res_json["statement"]
                        quiz["statement"] = res_json["statement"]
                        quiz["answer"] = bool(res_json.get("answer", True))
                        quiz["explanation"] = res_json.get("explanation", "")
                except Exception as e:
                    logger.error(f"Failed to generate LLM quiz JIT: {e}")
                    # 실패 시 예외를 던지지 않고 기존 fallback 퀴즈를 사용하도록 그대로 유지함

            selected.append(quiz)
            
        if len(selected) >= 3:
            break
            
    # 2. 3개가 안 채워졌다면 (예: 첫 문단 부근) 밑으로 내려가면서 마저 찾기
    if len(selected) < 3:
        for i in range(chunk_index + 1, len(chunks)):
            target_chunk_id = chunks[i].get("chunk_id")
            if not target_chunk_id:
                continue
                
            quiz = quizzes.get(target_chunk_id)
            if not quiz:
                continue
                
            if (ignore_asked or quiz["quizId"] not in asked_quiz_ids) and quiz not in selected:
                if is_snowchat_available():
                    paragraph = chunks[i].get("original_text") or chunks[i].get("restructured_text", "")
                    summary = chunks[i].get("summary") or chunks[i].get("restructured_text") or chunks[i].get("original_text", "")
                    try:
                        prompt = f"""다음 문단을 읽고 내용을 확인하는 O/X 퀴즈를 단 1문제 만들어주세요.
문단: {paragraph}
요약: {summary}

[조건]
1. 진술은 반드시 **20자 내외의 짧고 명확한 한 문장**이어야 합니다. ("~이다.", "~다" 형식)
2. 정답(answer)은 무작위로 True(O) 또는 False(X)가 되도록 하세요.
3. 해설(explanation)은 1~2문장으로 간결하게 적어주세요.
4. JSON 내부에 큰따옴표(")를 포함해야 할 경우 반드시 백슬래시로 이스케이프(\\")하세요. 줄바꿈(\n)은 절대 포함하지 마세요. (JSON 파싱 에러 방지)
5. 반드시 아래 JSON 형식으로만 응답하세요. 다른 말은 절대 쓰지 마세요.

{{
  "statement": "짧은 진술문",
  "answer": true,
  "explanation": "해설 내용"
}}"""
                        res_text = _call_llm_via_snowchat("gemini-2.5-flash", prompt)
                        
                        import re
                        match = re.search(r'\{.*\}', res_text.replace('\n', ' '), re.DOTALL)
                        if match:
                            res_text = match.group(0)
                        
                        res_json = json.loads(res_text)
                        if res_json.get("statement"):
                            quiz["question"] = res_json["statement"]
                            quiz["statement"] = res_json["statement"]
                            quiz["answer"] = bool(res_json.get("answer", True))
                            quiz["explanation"] = res_json.get("explanation", "")
                    except Exception as e:
                        logger.error(f"Failed to generate LLM quiz JIT: {e}")
                        # 실패 시 예외를 던지지 않고 기존 fallback 퀴즈를 사용하도록 그대로 유지함

                selected.append(quiz)
                
            if len(selected) >= 3:
                break
            
    return selected
