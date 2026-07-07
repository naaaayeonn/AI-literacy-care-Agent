"""
readability.py — 한국어 가독성 지수 계산 모듈 (M0)

Flesch-Kincaid 유사 알고리즘을 한국어에 맞게 조정한 순수 함수(Pure Function).
같은 입력에서 항상 같은 출력을 반환한다.

점수 해석:
  70 이상  → 쉬운 문장 (초중등 수준)
  50 ~ 69  → 보통 (일반 성인 수준)
  30 ~ 49  → 어려운 문장 (전문/학술 수준)
  30 미만  → 매우 어려운 문장 (고급 학술 수준)

참고 공식 문서: docs/READABILITY_FORMULA.md
"""
from __future__ import annotations

import re


# ---------------------------------------------------------------------------
# 내부 정규식 상수
# ---------------------------------------------------------------------------

_ENGLISH_WORD_RE = re.compile(r"[A-Za-z]{3,}")        # 3자 이상 영단어
_TECH_SUFFIX_RE = re.compile(                          # 한국어 전문 용어 접미사
    r"(?:화|율|성|도|적|론|법|형|식|계|기|학)(?:이|가|은|는|을|를|의|에|으로|로)?"
)
_SENTENCE_END_RE = re.compile(                         # 문장 종결 패턴
    r"(?<=[다요했됩니습])[.]\s+|(?<=[.!?。])\s+|(?<=[다요])\s+(?=[가-힣A-Z])"
)
_SYLLABLE_RE = re.compile(r"[가-힣]")                  # 한글 음절
_WORD_RE = re.compile(r"\S+")                          # 어절 (공백 기준)


# ---------------------------------------------------------------------------
# 내부 헬퍼 함수
# ---------------------------------------------------------------------------

def _split_sentences(text: str) -> list[str]:
    """문장 단위로 분리한다."""
    parts = _SENTENCE_END_RE.split(text.strip())
    return [p.strip() for p in parts if p.strip()]


def _avg_syllables_per_word(text: str) -> float:
    """어절당 평균 음절 수를 계산한다."""
    words = _WORD_RE.findall(text)
    if not words:
        return 0.0
    total = sum(len(_SYLLABLE_RE.findall(w)) for w in words)
    return total / len(words)


def _avg_words_per_sentence(text: str) -> float:
    """문장당 평균 어절 수를 계산한다."""
    sentences = _split_sentences(text)
    if not sentences:
        words = _WORD_RE.findall(text)
        return float(len(words))
    total = sum(len(_WORD_RE.findall(s)) for s in sentences)
    return total / len(sentences)


def _technical_term_ratio(text: str) -> float:
    """
    전문 용어 비율을 추정한다 (0~1).
    - 3자 이상 영단어 수
    - 한국어 전문 용어 접미사 패턴 수
    """
    words = _WORD_RE.findall(text)
    if not words:
        return 0.0
    english = len(_ENGLISH_WORD_RE.findall(text))
    tech = len(_TECH_SUFFIX_RE.findall(text))
    return min((english + tech) / len(words), 1.0)


# ---------------------------------------------------------------------------
# 공개 API
# ---------------------------------------------------------------------------

def analyze_readability(text: str) -> float:
    """
    한국어 텍스트의 가독성 지수를 계산한다.

    Args:
        text: 분석할 한국어 텍스트

    Returns:
        0~100 범위의 가독성 점수.
        높을수록 읽기 쉽고, 낮을수록 읽기 어렵다.

    Examples:
        >>> score = analyze_readability("안녕하세요. 오늘 날씨가 좋네요.")
        >>> 60 <= score <= 100
        True
        >>> hard = analyze_readability(
        ...     "LLM 기반 하이브리드 라우팅 최적화 알고리즘의 레이턴시 벤치마크 분석."
        ... )
        >>> hard < 60
        True
    """
    if not text or not text.strip():
        return 50.0  # 빈 텍스트는 중간값

    avg_syl = _avg_syllables_per_word(text)
    avg_words = _avg_words_per_sentence(text)
    tech_ratio = _technical_term_ratio(text)

    # 한국어 보정 Flesch-Kincaid 공식
    score = (
        100.0
        - (avg_words * 1.015)       # 문장 길이 패널티
        - (avg_syl * 8.0)           # 어절 복잡도 패널티
        - (tech_ratio * 35.0)       # 전문 용어 비율 패널티
    )

    return float(max(0.0, min(100.0, score)))


def calculate_difficulty_score(readability_score: float) -> float:
    """
    가독성 점수를 난이도 점수(difficulty_score)로 변환한다.
    1번 Literacy Score Engine에 전달하는 값.

    Returns:
        0~100 범위 (높을수록 어렵다)
    """
    return float(max(0.0, min(100.0, 100.0 - readability_score)))


def get_readability_label(score: float) -> str:
    """가독성 점수에 대한 한국어 레이블을 반환한다."""
    if score >= 70:
        return "쉬움"
    elif score >= 50:
        return "보통"
    elif score >= 30:
        return "어려움"
    return "매우 어려움"
