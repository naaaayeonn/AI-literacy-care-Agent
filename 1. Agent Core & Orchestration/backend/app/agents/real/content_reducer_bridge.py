"""1번 임시 브릿지 — content_reducer 실연결 (2번 실구현 도착 시 교체).

배경: 2번(Content & RAG)의 real 파이프라인은 이 환경에서 실행 불가하다
(langchain·sentence-transformers 미설치, restructurer가 유료 anthropic 호출).
폐루프 데모를 위해 1번(오케스트레이션)이 임시로 붙인 얇은 어댑터다.

구성:
- chunks / difficulty : 오프라인 결정론(의존성·API·비용 0)
- terms              : 2번 term_dictionary.json **검색**(신뢰출처, 생성 아님 → 환각 0)
- simplified_text    : Gemini 무료(gemini-2.5-flash) 재구성, 실패 시 원문 폴백

출력 형태는 2번 `contracts.py`의 ChunkDict/TermDict를 따른다 → 2번 real로 교체해도
프론트 계약이 안 바뀐다. 이 파일과 `term_dictionary.json`은 2번 실구현이 오면 폐기.
자세한 교체 요청: docs/HANDOFF_TO_ROLE2_GEMINI_BRIDGE.md
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from backend.app.orchestrator.state import ReadingSessionState

_TERM_DICT_PATH = Path(__file__).with_name("term_dictionary.json")
_REPO_ROOT = Path(__file__).resolve().parents[4]

_TERM_CACHE: list[dict] | None = None
_CHUNK_TARGET_CHARS = 400


# --------------------------------------------------------------------------- #
# 용어 사전 (오프라인, 신뢰 출처)
# --------------------------------------------------------------------------- #
def _load_terms() -> list[dict]:
    """2번 term_dictionary.json을 최초 1회 로드해 캐시한다."""
    global _TERM_CACHE
    if _TERM_CACHE is None:
        try:
            data = json.loads(_TERM_DICT_PATH.read_text(encoding="utf-8"))
            _TERM_CACHE = data.get("terms", []) if isinstance(data, dict) else []
        except (OSError, ValueError):
            _TERM_CACHE = []
    return _TERM_CACHE


def _find_terms(text: str, chunk_id: str) -> list[dict]:
    """text에 등장하는 사전 용어를 검색해 TermDict 리스트로 반환(생성 아님)."""
    if not text:
        return []
    low = text.lower()
    found: list[dict] = []
    for entry in _load_terms():
        names = [entry.get("term", "")] + list(entry.get("aliases", []))
        if any(name and name.lower() in low for name in names):
            found.append(
                {
                    "term": entry["term"],
                    "definition": entry.get("definition", ""),
                    "source": entry.get("source", ""),
                    "faithfulness_score": 1.0,  # 사전 직접 인용(검색) → 1.0
                    "chunk_id": chunk_id,
                }
            )
    return found


# --------------------------------------------------------------------------- #
# 청킹 · 난이도 (오프라인, 결정론)
# --------------------------------------------------------------------------- #
def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _difficulty(text: str) -> float:
    """문장 길이·긴 단어 비율 기반 0~100 난이도(결정론 휴리스틱)."""
    body = text.strip()
    if not body:
        return 50.0
    sentences = [s for s in re.split(r"[.!?。\n]+", body) if s.strip()]
    tokens = body.split()
    n_sent = max(1, len(sentences))
    n_tok = max(1, len(tokens))
    avg_sentence_len = len(body) / n_sent
    long_word_ratio = sum(1 for w in tokens if len(w) >= 6) / n_tok
    score = 25.0 + avg_sentence_len * 0.35 + long_word_ratio * 45.0
    return round(_clamp(score, 0.0, 100.0), 1)


def _split_paragraphs(text: str) -> list[tuple[str, int, int]]:
    """(문단, char_start, char_end)를 원문 위치와 함께 추출(단조 증가 커서)."""
    paragraphs: list[tuple[str, int, int]] = []
    cursor = 0
    for raw in re.split(r"\n\s*\n", text):
        para = raw.strip()
        if not para:
            continue
        idx = text.find(para, cursor)
        if idx == -1:
            idx = cursor
        paragraphs.append((para, idx, idx + len(para)))
        cursor = idx + len(para)
    return paragraphs


def _chunk_text(text: str, document_id: str) -> list[dict]:
    """원문을 문단 기반으로 묶어 결정론적 ChunkDict 리스트를 만든다."""
    paragraphs = _split_paragraphs(text)
    if not paragraphs:
        return [
            {
                "chunk_id": f"chunk_{document_id}_01",
                "original_text": "",
                "difficulty": 50.0,
                "char_start": 0,
                "char_end": 0,
            }
        ]

    chunks: list[dict] = []
    buffer: list[tuple[str, int, int]] = []
    buffer_len = 0

    def flush() -> None:
        nonlocal buffer, buffer_len
        if not buffer:
            return
        start = buffer[0][1]
        end = buffer[-1][2]
        body = text[start:end]
        chunk_id = f"chunk_{document_id}_{len(chunks) + 1:02d}"
        chunks.append(
            {
                "chunk_id": chunk_id,
                "original_text": body,
                "difficulty": _difficulty(body),
                "char_start": start,
                "char_end": end,
            }
        )
        buffer = []
        buffer_len = 0

    for para in paragraphs:
        buffer.append(para)
        buffer_len += len(para[0])
        if buffer_len >= _CHUNK_TARGET_CHARS:
            flush()
    flush()
    return chunks


# --------------------------------------------------------------------------- #
# 쉬운문장 재구성 (Gemini 무료, 실패 시 원문 폴백)
# --------------------------------------------------------------------------- #
def _load_dotenv_key(name: str) -> str | None:
    """os.environ에 없으면 저장소 .env에서 name 값을 최선 노력으로 읽는다."""
    value = os.getenv(name)
    if value:
        return value
    env_path = _REPO_ROOT / ".env"
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            if key.strip() == name:
                return val.strip().strip("\"'") or None
    except OSError:
        return None
    return None


# 무료 tier는 모델별로 quota가 따로 소진된다(예: 2.5-flash PerDay 소진 시에도
# flash-latest는 남아있음). 앞에서부터 시도하고 429/실패 시 다음 모델로 폴백한다.
_GEMINI_FALLBACK_MODELS = (
    "gemini-flash-latest",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
)


def _restructure(text: str) -> str | None:
    """Gemini로 쉬운 문장 재구성. 키 없음/네트워크/전 모델 quota 소진 시 None(→원문 폴백)."""
    body = text.strip()
    api_key = _load_dotenv_key("GEMINI_API_KEY")
    if not api_key or not body:
        return None
    try:
        import google.generativeai as genai  # 지연 import(선택 의존성)
    except Exception:
        return None

    genai.configure(api_key=api_key)
    primary = _load_dotenv_key("GEMINI_MODEL")
    models = ([primary] if primary else []) + [
        m for m in _GEMINI_FALLBACK_MODELS if m != primary
    ]
    prompt = (
        "다음 글을 뜻은 그대로 유지하되 초등학교 고학년도 이해할 수 있게 "
        "쉬운 문장으로 다시 써 줘. 없는 정보를 지어내지 말고, 머리말·설명 없이 "
        "본문만 출력해:\n\n" + body
    )
    for model_name in models:
        try:
            response = genai.GenerativeModel(model_name).generate_content(prompt)
            out = (getattr(response, "text", "") or "").strip()
            if out:
                return out
        except Exception:
            # quota(429)·안전차단·네트워크 등 → 다음 모델로 폴백.
            continue
    return None


# --------------------------------------------------------------------------- #
# 진입점 — 1번 어댑터가 _REAL_IMPL로 연결
# --------------------------------------------------------------------------- #
def content_reducer_bridge(state: ReadingSessionState) -> ReadingSessionState:
    """raw_text → chunks/terms/difficulty_score/simplified_text(계약 필드)."""
    raw_text = (state.get("raw_text") or "").strip()
    document_id = str(state.get("document_id") or "doc")

    chunks = _chunk_text(raw_text, document_id)

    session_terms: dict[str, dict] = {}
    for chunk in chunks:
        terms = _find_terms(chunk["original_text"], chunk["chunk_id"])
        if terms:
            chunk["terms"] = terms
        for term in terms:
            session_terms.setdefault(term["term"], term)

    difficulties = [c["difficulty"] for c in chunks] or [50.0]
    difficulty_score = round(sum(difficulties) / len(difficulties), 1)

    simplified = _restructure(raw_text) or raw_text

    state["chunks"] = chunks
    state["terms"] = list(session_terms.values())
    state["difficulty_score"] = float(difficulty_score)
    state["simplified_text"] = simplified
    state["readability_score"] = round(_clamp(100.0 - difficulty_score, 0.0, 100.0), 1)
    return state
