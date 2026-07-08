# 5번(QA & Evaluation Agent) 문서·계획 리뷰 피드백 — from 1번(오케스트레이션)

> 검토일: 2026-07-06 · 대상: `naaaayeonn/AI-literacy-care-Agent` main → `5. QA &Evaluation Agent/`
> 검토 범위: `ARCHITECTURE.md · DELIVERY_PLAN.md · README.md` (+ 저장소 전체에서 QA 코드 탐색)
>
> **5번은 현재 코드가 없고 문서 3개뿐입니다.** 다른 역할처럼 버그를 짚는 코드 리뷰가 불가능해,
> **문서·계획의 현실성 점검 + 실행 피드백**으로 정리했습니다. QA는 남의 산출물을 검증하는 역할이라,
> "무엇을 검증할지"보다 **"미완·분산·비용0 제약 아래 무엇을 어떻게 검증 가능하게 만들지"**가 핵심입니다.

---

## 0. 먼저: 실제 상태 (정직 점검)

저장소 전체를 스캔한 결과:

| 문서상 산출물 | 저장소 실제 | 판정 |
|---|---|---|
| pytest 구조 / tests 폴더 | `5.` 폴더엔 코드 0. `backend/evaluation/`·`golden_dataset/`·`reports/` **없음** | ❌ 미착수 |
| Golden Dataset | json **없음** | ❌ 미착수 |
| Ragas / Promptfoo / LangSmith | 구현 **없음**(문서 언급만) | ❌ 미착수 |
| Quality Report | 생성기 **없음** | ❌ 미착수 |
| README.md | **1바이트(빈 파일)** | ❌ |

- Daily Task Plan(§Daily)은 6/20~7/5에 pytest·골든셋·Ragas·Promptfoo가 **완료된 듯 적혀** 있으나, 저장소엔 **관련 코드가 하나도 없습니다.** 계획이 실제 진척과 어긋납니다.
- 다행히 **Final Checklist는 전부 `[ ]`(미완)** 으로 정직하게 남아 있습니다. 이 상태를 기준으로 재계획하는 게 맞습니다.

> 즉 5번은 "이미 만든 걸 고치는" 단계가 아니라 **"7/6부터 실제로 짓는"** 단계입니다. 남은 4일(7/6~7/10)에
> 맞춘 **현실적 최소 QA**가 필요합니다(아래 §6).

---

## 🔴 High — 계획을 그대로 실행하면 막히는 지점

### Q1. 비용 0 원칙과 평가 스택이 정면충돌
- **위치**: `ARCHITECTURE.md §2` (Ragas / LangSmith)
- **문제**: 프로젝트 대전제는 **비용 0**(외부 유료 API·호스팅 금지, `EXTENSION_DESIGN §11`). 그런데
  - **Ragas** Faithfulness/Answer Relevance는 기본적으로 **LLM judge(OpenAI 등 유료)**를 호출.
  - **LangSmith**는 클라우드 SaaS(무료 티어 제한, 외부 전송).
  → 문서대로면 **과금·외부 의존**이 생김.
- **수정 방향**:
  - Ragas는 **무료/로컬 judge**로 한정하거나, judge가 없으면 **오프라인 휴리스틱**(골든 정답 대비 키워드 포함율·토큰 겹침)으로 자동 폴백.
  - LangSmith 대신 **로컬 JSON Trace**를 기본값으로(문서 §2에 "Logging: JSON Trace"가 이미 있음 → 이걸 1순위로).
  - "유료 경로는 키 있을 때만 선택(optional)"을 명시.

### Q2. 검증 대상 코드베이스가 하나로 합쳐져 있지 않음 (분산)
- **문제**: 각 역할이 **자기 폴더에 자기 backend**를 가짐:
  - 1번 `1. Agent Core & Orchestration/backend/`
  - 2번 `2. Content & RAG Agent/backend/`
  - 3번 **루트 `backend/`**
  - 5번 arch가 상정한 `backend/evaluation/`·`backend/tests/unit|integration|smoke`는 **어느 backend인지 불명확**.
- **영향**: "통합 테스트/E2E"의 **대상이 물리적으로 하나로 통합돼 있지 않음** → 5번이 무엇을 import해서 무엇을 돌릴지 정할 수 없음. 이게 5번의 **최대 리스크**.
- **수정 방향**: 5번 착수 전에 **"검증 기준 코드베이스"를 1개로 확정**(누구의 backend를 통합본으로 볼지). 1번과 협의 필요. 통합본이 없으면 **역할별 backend를 각각 스모크**하는 것으로 범위를 좁혀야 함.

### Q3. 검증할 "실제 로직"이 대부분 스텁/상수 (의존성 미완)
- 내가 2·3번 코드를 리뷰한 결과, 5번이 검증하려는 대상들이 **아직 실값이 아님**:
  - **1번 score/routing**: `score.py`·`routing.py`의 실계산 함수가 `NotImplementedError` 스텁.
  - **3번 literacy_score**: `graph.py`가 **하드코딩 85.0** 반환(퀴즈·난이도 무시).
  - **2번 faithfulness**: `rag_engine`이 **항상 1.0 상수**(실측 아님) → "Faithfulness > 0.8" 검증이 무의미(항상 통과).
  - **qa_eval_client**: **no-op 스텁**(5번 퀴즈 채점 인계물 미구현).
- **영향**: 지금 Ragas/점수 정합성 테스트를 돌려도 **상수만 검증**됨 → 품질 신호가 안 됨.
- **수정 방향**: 5번은 (a) **골든 기대값·회귀 스냅샷·리포트 포맷**처럼 **남의 완성과 무관한 자산(Layer A)**을 먼저 짓고, (b) 실제 로직이 stub→real로 바뀌는 시점을 추적해 **그때 재검증**. 미검증 항목은 리포트에 **`unverified`로 정직 표기**.

---

## 🟡 Medium — 정합성 / 범위

### Q4. 확장(EXTENSION_DESIGN) QA 표면이 문서에 전혀 없음
- 계획 외 추가 기능 **크롬 확장(웹/PDF)** 이 붙으며 QA 대상이 늘었는데 5번 문서엔 미반영:
  - 웹/PDF **`content[]` 인입 계약**(`/api/session/start`), **REST 이벤트 구동**(ADR-001, WS 아님) 스모크
  - **pdf.js 텍스트 추출 품질**(줄 병합·하이픈·머리말 제거) 골든
  - 오버레이(넛지/퀴즈/툴팁) E2E, CORS
- **수정 방향**: Golden Dataset에 **PDF 추출 케이스**를 포함하고, 스모크를 **REST 왕복** 기준으로(기존 WS 가정 폐기).

### Q5. 테스트 파일명이 실제 코드 함수와 매핑 안 됨 + 중복 위험
- **위치**: `ARCHITECTURE.md §4` (`test_score.py, test_router.py, test_profile.py`)
- **문제**: 실제 검증 대상 함수는 `calculate_focus_score`·`determine_intervention`·`to_session_result`·`to_intervention_command` 등인데 문서 파일명과 연결이 없음. 또 **3번에 이미 `test_cognitive_care.py`가 존재** → 5번이 또 만들면 중복.
- **수정 방향**: 실제 함수 → 테스트 파일 매핑표를 만들고, 기존 테스트는 **재작성 말고 채택·확장**.

### Q6. Golden Dataset 스키마 미정의
- "20~30개 구축"만 있고 **입력/기대출력/판정 기준 스키마**가 없음. 무엇을 골든으로 삼는지(원문→쉬운문장? 원문→용어풀이? 원문→퀴즈?) 불명확.
- **수정 방향**: 최소 스키마 확정 — 예: `{ id, raw_text, expected_terms[], expected_difficulty_range, faithfulness_min }`. 평가 항목별로 골든을 분리.

### Q7. Quality Report에 "미검증" 표현이 없음
- 예시 JSON(`{passed, faithfulness, relevance, warnings}`)에 **`unverified`/`skipped` 필드가 없음**. 의존 모듈 미완으로 실측 못 한 항목을 "통과"로 오해할 위험.
- **수정 방향**: 리포트에 `verified[]` / `unverified[]`를 분리. "스텁 기준 통과 / 실 모듈 미검증"을 구분 기재.

---

## 🟢 Low — 위생/문서

- **Q8. README.md 빈 파일(1바이트)** — 최소한 실행법·범위 한 줄이라도.
- **Q9. Daily Task Plan이 과거를 완료처럼 서술** — 실제 진척(코드 0)과 어긋남. 7/6 기준으로 재작성 권장.
- **Q10. 저장소 루트 스트레이 파일** — `hi`(내용 "hi"), `test/index.html`(내용 "test") 같은 실험/임시 파일이 커밋됨. 정리 권장(5번만의 문제는 아니나 QA가 배포 전 점검 항목으로 잡기 좋음).
- **Q11. CI(GitHub Actions) "선택"** — 남은 일정상 CI는 후순위. pytest 로컬 그린 + 스모크가 먼저.

---

## 6. 7/6~7/10 현실적 최소 QA 제안 (비용0·의존성 인지)

> 거창한 스택(Ragas+Promptfoo+LangSmith+Docker+CI) 전부보다, **남은 4일에 실제로 돌아가는 것**을 우선.

**Layer A (5번 단독, 남의 완성과 무관 — 먼저)**
1. `evaluation/`·`golden_dataset/`·`reports/` 스캐폴딩 + `pytest.ini`
2. Golden Dataset v1 (웹 5~10 + **PDF 추출 3~5**) — 스키마 확정(Q6)
3. 기존 테스트(2번 `test_*` 8개, 3번 `test_cognitive_care`) **채택 + 전체 green 스냅샷**(회귀 기준선)
4. Quality Report 생성기 — **`unverified` 노출 포함**(Q7)

**Layer B (스텁 대상 — 지금 가능)**
5. REST 왕복 스모크(`/api/session/start`(content[]) → `/events` → `/result`) — 확장 경로(Q4)
6. **오프라인 휴리스틱 faithfulness/relevance**(골든 대비) — Ragas judge 없이도 점수 산출(Q1)

**Layer C (실 모듈 도착 시 — 컨틴전시)**
7. 1번 score·2번 실제 요약·3번 literacy가 stub→real로 바뀌면 **같은 골든셋으로 재검증**. 미도착분은 `unverified`.

**7/11~14**: 신규 금지, 회귀 재검증·리포트 갱신·데모 리허설만. **7/15 제출.**

---

## 통합(1번 관점) 우선순위

1. **Q2 검증 대상 코드베이스 1개로 확정** — 이게 없으면 통합 테스트가 성립 안 함. 1번과 즉시 협의.
2. **Q1 비용0 폴백** — Ragas 오프라인 휴리스틱 + JSON Trace 기본값.
3. **Q3 의존성 인지 3-레이어** — Layer A/B 먼저, Layer C는 컨틴전시.
4. **Q4 확장 QA 표면** 추가(PDF 추출·REST 스모크).
5. 나머지 위생(Q8~Q11).

> 참고: 1번 로컬 레포에 5번용 **의존성 인지 재계획(3-레이어 A/B/C)·비용0 폴백·확장 QA 표면**을
> 이미 정리한 `5_ARCHITECTURE.md`/`5_DELIVERY_PLAN.md` 초안이 있습니다. 그대로 가져다 쓰면 Q1~Q4가 해소됩니다.
> 또한 2·3·4번에도 개별 피드백을 전달했으니(`FEEDBACK_TO_ROLE{2,3,4}_...`), 5번의 검증 대상 상태를 그 문서로 파악하면 됩니다.
