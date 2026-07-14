import hashlib
import json
import logging
from ..agents.content_reducer.snowchat_client import is_snowchat_available, _call_llm_via_snowchat

logger = logging.getLogger(__name__)


def normalize_quizzes(raw) -> dict:
    """Redis에서 읽은 quizzes(JSON 문자열/dict/list)를 항상 {chunk_id: quiz} dict로 정규화한다.

    일부 처리 흐름에서 quizzes가 list 형태로 저장되어, 소비 측에서 .values()/.get()을
    호출할 때 AttributeError(500)가 나던 문제를 한 곳에서 방어한다. 소비 지점마다
    개별 가드를 두는 대신, Redis에서 읽은 직후 이 함수로 정규화해서 쓴다.
    """
    data = json.loads(raw) if isinstance(raw, str) else raw
    if isinstance(data, dict):
        return data
    if isinstance(data, list):
        return {
            (q.get("sourceChunkId") or q.get("chunkId") or q.get("source_chunk_id")): q
            for q in data
            if isinstance(q, dict)
        }
    return {}


def generate_ox_quiz(summary: str, paragraph: str, chunk_id: str, session_id: str) -> dict:
    """
    문단 요약(summary)과 원문(paragraph)을 기반으로 O/X 퀴즈를 생성합니다 (결정론적 캐싱용).
    LLM 생성은 퀴즈 출제 시점에 JIT로 수행합니다.
    """
    quiz_id = f"quiz_{session_id}_{chunk_id}"
    
    h_val = int(hashlib.md5(chunk_id.encode('utf-8')).hexdigest(), 16)
    is_even = (h_val % 2 == 0)
    
    import re
    
    # [요약] 프리픽스가 있다면 제거
    summary_clean = summary.replace("[요약]", "").strip()
    
    # 3.4% 같은 소수점 숫자가 잘리는 현상을 방지하기 위해 공백이 뒤따르는 마침표/느낌표/물음표만 기준으로 문장 분리
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', summary_clean) if s.strip()]
    statement = sentences[0] if sentences else summary_clean
    
    if is_even:
        if not statement: statement = "본문의 핵심 요약 내용과 일치합니다."
        answer = True
        explanation = "원문의 내용 및 요약과 일치하는 올바른 진술입니다."
    else:
        # M5: 의미 없는 고정 진술문 대신 summary를 반전하는 문장 생성
        if not statement: 
            statement = "이 문단의 설명과 일치하지 않습니다."
        else:
            # 문장 끝 마침표 제거
            if statement.endswith("."):
                statement_no_dot = statement[:-1]
            else:
                statement_no_dot = statement
                
            # 부드럽고 자연스러운 사실 무효화 문장 결합
            statement = statement_no_dot + "라는 내용은 사실과 다릅니다."
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


def _generate_jit_quiz_if_needed(quiz: dict, paragraph: str, summary: str):
    """JIT LLM 프롬프트 중복 제거 헬퍼"""
    if not is_snowchat_available():
        return
        
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


def select_quiz_for_state(state: dict, ignore_asked: bool = False) -> list[dict]:
    """
    현재 사용자 상태(방금 읽던 position)를 바탕으로 미출제 퀴즈 최대 3개를 선택합니다.
    ignore_asked가 True이면 이미 출제된 퀴즈라도 다시 선택합니다 (100% 달성 시 사용).
    """
    quizzes = normalize_quizzes(state.get("quizzes", {}))
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
            paragraph = chunks[i].get("original_text") or chunks[i].get("restructured_text", "")
            summary = chunks[i].get("summary") or chunks[i].get("restructured_text") or chunks[i].get("original_text", "")
            _generate_jit_quiz_if_needed(quiz, paragraph, summary)

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
                paragraph = chunks[i].get("original_text") or chunks[i].get("restructured_text", "")
                summary = chunks[i].get("summary") or chunks[i].get("restructured_text") or chunks[i].get("original_text", "")
                _generate_jit_quiz_if_needed(quiz, paragraph, summary)

                selected.append(quiz)
                
            if len(selected) >= 3:
                break
            
    return selected
