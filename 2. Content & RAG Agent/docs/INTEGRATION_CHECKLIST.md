# 통합 체크리스트 (INTEGRATION_CHECKLIST.md)

이 문서는 콘텐츠 및 RAG 에이전트(2번 역할)와 시스템의 타 구성 요소(1번, 3번, 4번, 5번 역할) 간의 통합 연동 상태와 점검 항목을 기술합니다.

---

## 1. 역할별 통합 항목

### 1) 1번 Orchestrator 연동 (어댑터 및 REST API)
- [x] **Stub / Real 토글 제어**:
  - `.env` 파일의 `CONTENT_REDUCER_MODE` 값을 통해 stub(더미 반환)과 real(실제 LLM/RAG) 모드가 정상 전환되는지 점검.
- [x] **REST API 호출 연동**:
  - `POST /api/content-reducer/reduce` 에 원문과 리터러시 레벨을 전송하여 분할된 청크(`chunks`)와 난이도(`difficulty_score`)를 수집하는지 점검.
  - `POST /api/content-reducer/quiz` 에 특정 청크 ID와 문맥을 전송하여 개입 퀴즈를 가져오는지 점검.

### 2) 3번 백엔드 행동 수집 에이전트 연동
- [x] **chunk_id 일관성**:
  - 3번 에이전트가 스크롤 및 지연 시간을 수집할 때 사용되는 `chunk_id`와 2번이 청킹 결과로 제공한 `chunk_id`가 일치하는지 점검.
  - 규칙 준수 여부: `chunk_{document_id}_{index:02d}` (예: `chunk_doc001_03`)

### 3) 4번 프론트엔드 연동 (UI 렌더링)
- [x] **텍스트 렌더링**:
  - `chunks[].restructured_text`를 사용자용 화면에 출력하고, 툴팁 호버 시 `terms`의 `definition`과 `source`를 노출하는지 점검.
- [x] **용어 하이라이트**:
  - `char_start`와 `char_end`를 기준으로 원문과 재구성 텍스트의 좌표가 매핑되는지 점검.
- [x] **퀴즈 카드 UI**:
  - 퀴즈 응답(`QuizDict`)의 `options` 4개와 `correct_option`을 활용해 사용자가 퀴즈를 풀고 정답/해설을 정상 노출받는지 점검.

### 4) 5번 QA 평가 에이전트 연동
- [x] **로그 및 메타데이터 수집**:
  - 2번 에이전트가 실행 후 반환하는 `trace` 필드에서 RAG의 `faithfulness_summary` 통계 및 각 단계별 지연시간(`latency_ms`)을 온전히 수집할 수 있는지 점검.
  - `trace`에 RAG 충실도 지표 경고나 에러 데이터가 누락 없이 기록되는지 검증.

---

## 2. 통합 검증 시나리오

| 검증 단계 | 테스트 명령 / 행동 | 기대 결과 | 상태 |
|---|---|---|---|
| **서버 구동** | `uvicorn backend.app.main:app --port 8000` | 8000 포트에서 FastAPI 정상 시작 | ✅ 준비 완료 |
| **헬스체크** | `GET http://localhost:8000/health` | 200 OK 및 RAG 모드 메타데이터 수집 | ✅ 준비 완료 |
| **파이프라인 실행** | `POST /api/content-reducer/reduce` | 3개 이상의 청크, difficulty_score, simplified_text 반환 | ✅ 준비 완료 |
| **퀴즈 생성** | `POST /api/content-reducer/quiz` | 질문, 4개 선택지, 정답(1~4), 인용 해설 반환 | ✅ 준비 완료 |
| **Fallback 검증** | 데이터베이스 차단 후 실행 | memory RAG 모드로 자동 전환 및 무중단 용어풀이 | ✅ 준비 완료 |
| **코드 포맷 점검** | `ruff check backend/app/agents/` | 오류 없이 린팅 통과 | ✅ 준비 완료 |

---

## 3. 트러블슈팅 가이드

- **현상: LLM 호출 지연이 너무 긴 경우**
  - 조치: `.env` 파일의 `DIFFICULTY_THRESHOLD_FOR_HEAVY_LLM` 값을 높여 가벼운 모델인 `Haiku`의 라우팅 비율을 높이거나 모드를 `stub`으로 임시 변경하여 병목을 우회합니다.
- **현상: RAG 용어풀이 데이터베이스 연결 오류**
  - 조치: DB 서버 연결 불통 시 시스템이 자동으로 local `term_dictionary.json` 파일을 찾아 인메모리 임베딩 및 키워드 방식으로 동작하므로 에러 상태 로그를 확인하되 데모는 계속 진행하면 됩니다.
