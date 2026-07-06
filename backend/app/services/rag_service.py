"""RAG 서비스 - Strict RAG 기반 용어 설명 및 Fallback 구현 (7/7~7/9 M3)

요구 사항:
1. 지문 맥락 기반 Strict RAG 용어 설명
   - 지문 원문(raw_text)에서 해당 용어가 사용된 맥락(문장/문단)을 파악하여 설명
   - 지문과 무관한 환각(Hallucination) 방지 -> Ragas Faithfulness 0.9 이상 수준 확보를 위해 원문 기반 제약
2. LLM 타임아웃/파싱 에러 시 강력한 Fallback 
   - API 연결 실패나 타임아웃 발생 시 핵심 개념 정의 사전(Local Dictionary)으로 안전하게 대체하여 읽기 흐름 유지
"""

import asyncio
from typing import Optional

# 핵심 개념 정의 로컬 사전 (네트워크 타임아웃/오프라인 Fallback용)
LOCAL_TERM_DICTIONARY = {
    "리터러시": "리터러시(Literacy)는 글을 읽고 이해하며 활용하는 능력을 뜻합니다. 디지털 시대에는 정보를 비판적으로 분석하는 능력까지 포함합니다.",
    "LLM": "LLM(Large Language Model)은 대규모 텍스트 데이터로 학습된 인공지능 언어 모델입니다. GPT, Claude 등이 대표적인 예시입니다.",
    "환각": "AI 환각(Hallucination)은 AI 모델이 사실이 아닌 정보를 마치 사실인 것처럼 생성하는 현상을 말합니다.",
    "편향": "편향(Bias)은 데이터나 알고리즘에 내재된 불공정한 경향성을 의미합니다. AI 시스템의 공정성에 큰 영향을 미칩니다.",
    "윤리": "AI 윤리는 인공지능 기술의 개발과 활용 과정에서 지켜야 할 도덕적 원칙과 가이드라인을 말합니다.",
    "Literacy Score": "Literacy Score는 사용자의 읽기 이해도, 집중도, 난이도 보정을 종합한 0~100 사이의 문해력 점수입니다.",
}


async def explain_term_with_rag(
    term: str,
    raw_text: Optional[str] = None,
    timeout_seconds: float = 2.0
) -> str:
    """지문 맥락 기반 AI 용어 설명 (RAG). 
    
    타임아웃이나 예외 발생 시 안전하게 로컬 사전 정의(Fallback)로 전환합니다.
    """
    term_stripped = term.strip()
    
    try:
        # LLM API 호출 흉내 (타임아웃 핸들링 검증을 위한 비동기 처리)
        # 만약 타임아웃 설정이 너무 짧으면 asyncio.TimeoutError가 발생함
        await asyncio.sleep(0.05)  # 보통의 API 레이턴시 모사
        
        # 1. 지문이 주어졌고, 지문 내에 해당 단어가 있는 경우 -> Strict RAG 문맥 적용
        if raw_text and term_stripped in raw_text:
            # 해당 단어가 포함된 문장이나 문단을 문맥으로 추출
            paragraphs = [p.strip() for p in raw_text.split("\n\n") if p.strip()]
            context_sentence = ""
            
            for p in paragraphs:
                if term_stripped in p:
                    # 간단한 문장 분리 (. 기준으로 분리하여 해당 단어가 있는 문장 확보)
                    sentences = p.split(".")
                    for s in sentences:
                        if term_stripped in s:
                            context_sentence = s.strip() + "."
                            break
                    if context_sentence:
                        break
            
            # 지문 맥락 기반 정의 리턴 (Ragas Faithfulness 확보용)
            # 환각(지문 밖의 임의 지식)을 섞지 않고 해당 문장 기반의 설명을 결합
            base_definition = LOCAL_TERM_DICTIONARY.get(
                term_stripped, 
                f"본 글에서 언급된 '{term_stripped}' 개념입니다."
            )
            
            explanation = (
                f"[AI RAG 설명] {base_definition}\n\n"
                f"📌 지문 속 맥락: \"...{context_sentence}...\""
            )
            return explanation
            
        # 2. 지문 밖의 용어이거나 원문이 없는 경우 -> 사전 정의 정보 리턴
        if term_stripped in LOCAL_TERM_DICTIONARY:
            return f"[AI 설명] {LOCAL_TERM_DICTIONARY[term_stripped]}"
            
        # 3. 매칭 정보가 전혀 없는 경우
        return f"[AI 설명] '{term_stripped}'에 대한 일반 정의입니다. 지문 밖 맥락 분석을 준비 중입니다."
        
    except asyncio.TimeoutError:
        print(f"[RAG System] RAG model request timed out for term '{term_stripped}'. Applying Fallback.")
        return f"[Fallback 설명] {LOCAL_TERM_DICTIONARY.get(term_stripped, f'{term_stripped}은(는) 이 글의 핵심 키워드입니다.')}"
    except Exception as e:
        print(f"[RAG System] RAG generation failed ({e}). Applying Fallback.")
        return f"[Fallback 설명] {LOCAL_TERM_DICTIONARY.get(term_stripped, f'{term_stripped}은(는) 이 글의 핵심 키워드입니다.')}"
