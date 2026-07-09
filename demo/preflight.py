# -*- coding: utf-8 -*-
"""
AI 리터러시 케어 — 데모 프리플라이트 점검
서버(localhost:8000)가 떠 있는 상태에서 실행하면, 시연에 필요한 기능이
모두 정상인지 1분 안에 확인하고 ✅/❌ 체크리스트를 출력한다.

사용법:  (서버 켠 뒤)  python demo/preflight.py
"""
import json
import sys
import urllib.request

BASE = "http://127.0.0.1:8000"
OK, FAIL, WARN = "[  OK  ]", "[ FAIL ]", "[ WARN ]"
results = []


def _req(path, method="GET", body=None, timeout=20):
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode("utf-8", "replace")
        return r.status, raw


def check(name, fn):
    try:
        ok, msg = fn()
        tag = OK if ok is True else (WARN if ok == "warn" else FAIL)
        print(f"{tag} {name} — {msg}")
        results.append(ok is True or ok == "warn")
    except Exception as e:
        print(f"{FAIL} {name} — 예외: {e}")
        results.append(False)


def c_health():
    s, raw = _req("/health")
    d = json.loads(raw)
    return (s == 200), f"status={d.get('status')} db={d.get('db')} redis={d.get('redis')}"


def c_frontend():
    s, raw = _req("/")
    ok = s == 200 and ('id="root"' in raw or "<title>" in raw)
    return ok, f"HTTP {s}, index.html 서빙={'예' if ok else '아니오'}"


def c_start():
    s, raw = _req("/api/session/start", "POST", {"userId": "preflight", "articleId": "a",
                  "content": ["AI가 만든 정보를 비판적으로 검증하는 능력이 중요합니다."]})
    d = json.loads(raw)
    sid = d.get("sessionId")
    chunks = len(d.get("article", {}).get("chunks", []))
    globals()["_SID"] = sid
    return (bool(sid) and chunks > 0), f"sessionId={sid}, 본문 chunks={chunks}"


def c_focus_drop():
    sid = globals().get("_SID")
    if not sid:
        return False, "세션 없음(start 실패)"
    evs = [{"type": "scroll", "timestamp_ms": i * 150, "position": i / 12,
            "payload": {"scrollVelocity": 4000}} for i in range(12)]
    s, raw = _req(f"/api/session/{sid}/events", "POST", {"session_id": sid, "events": evs})
    d = json.loads(raw)
    p = d.get("payload", {})
    fs = p.get("focusScore")
    ok = fs is not None and fs < 75
    return ok, f"빠른 스크롤 → 집중도 {fs}, 개입={d.get('type')}/{p.get('nudgeLevel')}"


def c_focus_normal():
    s0, raw0 = _req("/api/session/start", "POST", {"userId": "preflight2", "content": ["문장"]})
    sid = json.loads(raw0).get("sessionId")
    evs = [{"type": "scroll", "timestamp_ms": i * 900, "position": i / 6,
            "payload": {"scrollVelocity": 200}} for i in range(6)]
    s, raw = _req(f"/api/session/{sid}/events", "POST", {"session_id": sid, "events": evs})
    fs = json.loads(raw).get("payload", {}).get("focusScore")
    ok = fs is not None and fs >= 75
    return ok, f"정상 속도 읽기 → 집중도 {fs} (높게 유지되어야 정상)"


def c_result():
    sid = globals().get("_SID")
    s, raw = _req(f"/api/session/{sid}/result")
    d = json.loads(raw)
    ls = d.get("literacyScore")
    return (ls is not None), f"literacyScore={ls}, comprehension={d.get('comprehensionScore')}"


def c_term_local():
    s, raw = _req("/api/terms/lookup", "POST", {"word": "환각",
                  "context": "AI가 사실이 아닌 정보를 생성하는 현상."})
    d = json.loads(raw)
    ok = bool(d.get("definition")) and d.get("source") != "not_found"
    return ok, f"'환각' → {d.get('source')}: {str(d.get('definition'))[:40]}"


def c_term_dict_key():
    s, raw = _req("/api/terms/lookup", "POST", {"word": "전고체",
                  "context": "전고체 배터리 같은 차세대 기술."})
    d = json.loads(raw)
    if d.get("source") not in (None, "not_found") and d.get("definition"):
        return True, f"사전 키 작동 — '전고체' → {d.get('source')}"
    return "warn", "임의 단어(전고체)는 not_found — 사전 키(WOORIMAL/STDICT) 미설정. 데모는 로컬 사전 단어(환각 등)/hover 툴팁으로 진행"


print("\n================ 데모 프리플라이트 점검 ================\n")
check("1. 백엔드 health", c_health)
check("2. 프론트 서빙(/)", c_frontend)
check("3. 세션 시작(/start, 2번 본문 처리)", c_start)
check("4. 집중도 하락 감지(빠른 스크롤→개입)", c_focus_drop)
check("5. 정상 읽기 오탐 없음", c_focus_normal)
check("6. 최종 점수 산출(/result)", c_result)
check("7. 용어 조회 — 로컬 사전(환각)", c_term_local)
check("8. 용어 조회 — 임의 단어(사전 키 상태)", c_term_dict_key)

print("\n" + "=" * 56)
passed = sum(1 for r in results if r)
if all(results):
    print(f"✅ 전체 통과 ({passed}/{len(results)}) — 데모 준비 완료!")
    sys.exit(0)
else:
    print(f"⚠️ {passed}/{len(results)} 통과 — 위 FAIL 항목을 확인하세요.")
    sys.exit(1)
