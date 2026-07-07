"""
run_m1_demo.py — M1 Smoke Test 및 데모 러너

M1 파이프라인 전체 흐름을 검증하는 스크립트.
한 명령으로 실행 가능: python scripts/run_m1_demo.py

검증 항목:
  1. 데모 기사 로드
  2. 가독성 분석
  3. 의미 단위 청킹 (3개 이상)
  4. 텍스트 재구성 (restructured_text 존재)
  5. RAG 용어풀이 (terms 존재, faithfulness_score 포함)
  6. 반복 실행 안정성 (3회)
  7. Fallback 동작 확인 (빈 텍스트)
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.agents.content_reducer.agent import run_content_reducer


# ---------------------------------------------------------------------------
# 색상 출력 (터미널)
# ---------------------------------------------------------------------------

def _ok(msg: str) -> str:
    return f"  [OK]  {msg}"


def _fail(msg: str) -> str:
    return f"  [NG]  {msg}"


def _info(msg: str) -> str:
    return f"  [--]  {msg}"


# ---------------------------------------------------------------------------
# 데모 기사 로드
# ---------------------------------------------------------------------------

def load_demo_article() -> str:
    article_path = PROJECT_ROOT / "data" / "demo_articles" / "article_01.txt"
    if not article_path.exists():
        raise FileNotFoundError(f"데모 기사 없음: {article_path}")
    return article_path.read_text(encoding="utf-8").strip()


# ---------------------------------------------------------------------------
# 단일 파이프라인 실행 및 검증
# ---------------------------------------------------------------------------

def run_and_verify(raw_text: str, run_index: int = 1) -> dict:
    """파이프라인을 실행하고 검증 결과를 반환한다."""
    state = {
        "session_id": f"smoke_test_{run_index:03d}",
        "user_id": "tester",
        "document_id": f"doc_demo_{run_index:03d}",
        "raw_text": raw_text,
        "profile": {
            "reading_level": "intermediate",
            "user_literacy_level": 3,
            "target_domain": "IT/AI",
        },
        "trace": [],
        "errors": [],
    }

    t0 = time.monotonic()
    result = run_content_reducer(state)
    elapsed = round((time.monotonic() - t0) * 1000)

    checks = {}

    # 1. difficulty_score 범위
    ds = result.get("difficulty_score", -1)
    checks["difficulty_in_range"] = 0.0 <= ds <= 100.0

    # 2. chunk 수 >= 3 (M1 QA 기준)
    chunks = result.get("chunks", [])
    checks["chunks_gte_3"] = len(chunks) >= 3

    # 3. 각 chunk에 chunk_id, char_start, char_end 존재
    required_fields = {"chunk_id", "original_text", "char_start", "char_end"}
    checks["chunk_required_fields"] = all(
        required_fields.issubset(set(ch.keys())) for ch in chunks
    )

    # 4. restructured_text 존재
    checks["restructured_text_exists"] = all(
        "restructured_text" in ch for ch in chunks
    )

    # 5. terms 배열에 term, definition, source 존재
    all_terms = result.get("terms", [])
    checks["terms_have_fields"] = all(
        {"term", "definition", "source"}.issubset(set(t.keys()))
        for t in all_terms
    ) if all_terms else True  # terms=[]도 허용

    # 6. faithfulness_score 포함
    checks["faithfulness_score_present"] = all(
        "faithfulness_score" in t for t in all_terms
    ) if all_terms else True

    # 7. trace에 content_reducer 기록
    steps = [tr["step"] for tr in result.get("trace", [])]
    checks["trace_recorded"] = "content_reducer" in steps

    # 8. errors 비어있음 (fallback 없이 성공)
    checks["no_errors"] = len(result.get("errors", [])) == 0

    return {
        "run": run_index,
        "elapsed_ms": elapsed,
        "difficulty_score": ds,
        "chunk_count": len(chunks),
        "term_count": len(all_terms),
        "checks": checks,
        "all_passed": all(checks.values()),
    }


# ---------------------------------------------------------------------------
# Fallback 테스트
# ---------------------------------------------------------------------------

def test_fallback_on_empty() -> bool:
    """빈 텍스트에서도 fallback이 동작하는지 확인한다."""
    state = {
        "session_id": "fallback_test",
        "user_id": "tester",
        "document_id": "doc_empty",
        "raw_text": "",
        "profile": {},
        "trace": [],
        "errors": [],
    }
    try:
        result = run_content_reducer(state)
        return "chunks" in result and "terms" in result
    except Exception:
        return False


# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------

def main() -> int:
    print()
    print("=" * 60)
    print("  Content Reducer M1 Smoke Test")
    print("=" * 60)
    print()

    # 데모 기사 로드
    try:
        article = load_demo_article()
        print(_ok(f"데모 기사 로드: {len(article)}자"))
    except FileNotFoundError as e:
        print(_fail(str(e)))
        return 1

    print()
    print("── 파이프라인 3회 반복 실행 ──")

    all_passed = True
    results = []

    for i in range(1, 4):
        r = run_and_verify(article, run_index=i)
        results.append(r)

        status = "[PASS]" if r["all_passed"] else "[FAIL]"
        print(
            f"  Run {i}: {status}  "
            f"[{r['elapsed_ms']}ms | "
            f"difficulty={r['difficulty_score']:.1f} | "
            f"chunks={r['chunk_count']} | "
            f"terms={r['term_count']}]"
        )

        if not r["all_passed"]:
            all_passed = False
            for check_name, passed in r["checks"].items():
                if not passed:
                    print(f"       └─ {_fail(check_name)}")

    print()
    print("── Fallback 테스트 ──")
    fb_ok = test_fallback_on_empty()
    print(_ok("fallback: empty text") if fb_ok else _fail("fallback: empty text"))
    if not fb_ok:
        all_passed = False

    print()
    print("── 상세 결과 (첫 번째 실행) ──")
    r0 = results[0]
    for check_name, passed in r0["checks"].items():
        icon = "[OK]" if passed else "[NG]"
        print(f"  {icon} {check_name}")

    print()
    if all_passed:
        print("[SUCCESS] M1 Smoke Test ALL PASSED")
        return 0
    else:
        print("[FAILURE] M1 Smoke Test SOME FAILED - check above items")
        return 1


if __name__ == "__main__":
    sys.exit(main())
