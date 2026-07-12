"""
readability.py — 한국어 이독성(Readability) 및 난이도(Difficulty) 계산 모듈 (M1/M2)

이독성(표면적 가독성)과 난이도(개념적 복합성)를 두 개의 완전히 독립된 변수로 연산한다.
- 이독성 (Readability): 어휘 등급, 어절 길이, 문장 길이의 표면적 요인으로 계산 (0~100)
- 난이도 (Difficulty): 표준 전문 용어 밀도 기반의 지수 스케일링 모델(Exponential Scaling)을 활용해 
                     단 하나의 용어 등장 시에도 실질 인지 장벽(난이도)을 동적으로 반영 (0~100)
"""
from __future__ import annotations

import os
import json
import re
import math
from pathlib import Path

# ---------------------------------------------------------------------------
# 내부 캐시 데이터 로딩 (Lazy Loading)
# ---------------------------------------------------------------------------

_VOCAB_DICT: dict[str, int] | None = None
_STANDARD_TERMS: set[str] | None = None

def _get_project_root() -> Path:
    """프로젝트 루트 디렉토리를 반환한다."""
    return Path(__file__).resolve().parents[4]

def _load_vocab_dict() -> dict[str, int]:
    global _VOCAB_DICT
    if _VOCAB_DICT is not None:
        return _VOCAB_DICT
    
    try:
        path = _get_project_root() / "data" / "processed_vocab.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                _VOCAB_DICT = json.load(f)
                return _VOCAB_DICT
    except Exception:
        pass
    _VOCAB_DICT = {}
    return _VOCAB_DICT

def _load_standard_terms() -> set[str]:
    global _STANDARD_TERMS
    if _STANDARD_TERMS is not None:
        return _STANDARD_TERMS
    
    try:
        path = _get_project_root() / "data" / "processed_standard_terms.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                terms_list = json.load(f)
                _STANDARD_TERMS = set(terms_list)
                return _STANDARD_TERMS
    except Exception:
        pass
    _STANDARD_TERMS = set()
    return _STANDARD_TERMS


# ---------------------------------------------------------------------------
# 한국어 조사 및 어미 제거 정규식
# ---------------------------------------------------------------------------
_POSTPOSITION_RE = re.compile(
    r"(은|는|이|가|을|를|의|에|에서|에게|으로|로|와|과|도|만|부터|까지|처럼|보다|라고|이라고|"
    r"에서는|에게는|으로서|으로서의|으로써|이란|란|하고|습니다|니다|다|요|고|며|아|어|아서|어서|여서|니까|으니까|기|게|지|듯|듯하다|ㄴ다|는다)$"
)

def _strip_josa_and_ending(word: str) -> str:
    """단어 끝의 조사 및 어미를 제거하여 어근/어간에 가깝게 복원한다."""
    hangul = "".join(re.findall(r"[가-힣]", word))
    if not hangul:
        return word
    
    stripped = _POSTPOSITION_RE.sub("", hangul)
    if len(stripped) >= 1:
        return stripped
    return hangul


# ---------------------------------------------------------------------------
# 내부 헬퍼 정규식 및 텍스트 파서
# ---------------------------------------------------------------------------
_SENTENCE_END_RE = re.compile(
    r"(?<=[다요했됩니습])[.]\s+|(?<=[.!?。])\s+|(?<=[다요])\s+(?=[가-힣A-Z])"
)
_WORD_RE = re.compile(r"\S+")
_SYLLABLE_RE = re.compile(r"[가-힣A-Za-z0-9]")


def _split_sentences(text: str) -> list[str]:
    """문장 단위로 분리한다."""
    parts = _SENTENCE_END_RE.split(text.strip())
    return [p.strip() for p in parts if p.strip()]


def _calculate_avg_word_length(text: str) -> float:
    """평균 어절 길이를 계산한다 (전체 글자 수 / 전체 어절 수)."""
    words = _WORD_RE.findall(text)
    if not words:
        return 0.0
    total_chars = sum(len(_SYLLABLE_RE.findall(w)) for w in words)
    return total_chars / len(words)


def _avg_words_per_sentence(text: str) -> float:
    """문장당 평균 어절 수를 계산한다."""
    sentences = _split_sentences(text)
    if not sentences:
        words = _WORD_RE.findall(text)
        return float(len(words))
    total = sum(len(_WORD_RE.findall(s)) for s in sentences)
    return total / len(sentences)


# ---------------------------------------------------------------------------
# 공개 API
# ---------------------------------------------------------------------------

def analyze_readability(text: str) -> float:
    """
    한국어 텍스트의 이독성(표면적 가독성) 지수를 계산한다 (0~100).
    순수하게 표면적인 가소성 변수(어휘 난도, 어절 길이, 문장 길이)로만 독립적으로 계산한다.
    """
    if not text or not text.strip():
        return 50.0

    words = _WORD_RE.findall(text)
    if not words:
        return 50.0

    vocab_dict = _load_vocab_dict()

    # 1. 평균 어절 길이
    avg_word_len = _calculate_avg_word_length(text)

    # 2. 평균 어절 수
    avg_words_per_sent = _avg_words_per_sentence(text)

    # 3. 어휘 난도 계산 (3등급 이상 + 미등록 어휘 비율)
    korean_words_count = 0
    difficult_words_count = 0

    for word in words:
        stem = _strip_josa_and_ending(word)
        if not stem:
            continue
        korean_words_count += 1
        
        # 어휘 사전 대조 (접두사 혹은 완전 일치 탐색)
        matched = False
        if stem in vocab_dict:
            if vocab_dict[stem] >= 3:
                difficult_words_count += 1
            matched = True
        else:
            for v_word, v_grade in vocab_dict.items():
                if v_word.startswith(stem) or stem.startswith(v_word):
                    if v_grade >= 3:
                        difficult_words_count += 1
                    matched = True
                    break
        
        if not matched:
            if len(stem) > 1:
                difficult_words_count += 1

    difficult_ratio = (difficult_words_count / korean_words_count * 100.0) if korean_words_count > 0 else 0.0

    # 표면적 이독성 원점수 계산 (전문용어 패널티 배제)
    raw_score = (
        95.0
        - (difficult_ratio * 0.4)      # 고급 어휘 비율 패널티
        - (avg_words_per_sent * 1.2)     # 문장 길이 패널티
        - (avg_word_len * 2.5)           # 어절 복잡도 패널티
    )

    # 15.0 ~ 85.0의 실질적 원점수 범위를 0.0 ~ 100.0 범위로 선형 스케일링
    min_val = 15.0
    max_val = 85.0
    scaled_score = ((raw_score - min_val) / (max_val - min_val)) * 100.0

    return float(max(0.0, min(100.0, scaled_score)))


def calculate_difficulty_score(readability_score_or_text: float | str) -> float:
    """
    (개편) 텍스트 또는 가독성 점수를 기준으로 난이도 점수(0~100)를 반환한다.
    
    독립변수 처리 규칙:
      - 입력이 str(텍스트)인 경우: 전문 용어 밀도 기반으로 개념적 난이도를 직접 0~100 범위로 독립 산출한다.
        (지수 스케일링 모델 적용: 단 한 개의 전문 용어만 등장해도 난이도가 60~70점 이상으로 강력 상승)
      - 입력이 float(점수)인 경우: 기존 1번 Orchestrator와의 하위 호환성을 유지하기 위해 100 - readability_score 를 반환한다.
    """
    if isinstance(readability_score_or_text, str):
        # 100% 독립적인 개념적 난이도 계산 (전문 용어 밀도 기반 지수 스케일링)
        tech_density = get_technical_term_density(readability_score_or_text)
        # 지수 스케일링 모델: 100 * (1 - e^(-0.25 * tech_density))
        scaled_diff = 100.0 * (1.0 - math.exp(-0.25 * tech_density))
        return float(max(0.0, min(100.0, scaled_diff)))
    
    # 하위 호환성 폴백
    return float(max(0.0, min(100.0, 100.0 - readability_score_or_text)))


def get_technical_term_density(text: str) -> float:
    """
    텍스트 내의 표준 전문 용어 밀도(%)를 계산한다.
    공식: (표준 전문 용어 매칭 수 / 전체 어절 수) * 100
    """
    words = _WORD_RE.findall(text)
    if not words:
        return 0.0

    standard_terms = _load_standard_terms()
    match_count = 0

    for word in words:
        stem = _strip_josa_and_ending(word)
        if not stem:
            continue
        
        norm_stem = stem.replace(" ", "")
        if norm_stem in standard_terms:
            match_count += 1

    return (match_count / len(words)) * 100.0


def get_readability_label(score: float) -> str:
    """가독성 점수에 대한 한국어 레이블을 반환한다."""
    if score >= 55.0:
        return "쉬움"
    elif score >= 40.0:
        return "보통"
    elif score >= 25.0:
        return "어려움"
    return "매우 어려움"
