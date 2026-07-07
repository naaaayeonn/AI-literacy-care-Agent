# 2번(Content & RAG Agent) 코드 리뷰 피드백 — from 1번(오케스트레이션)

> 검토일: 2026-07-06 · 대상 커밋: `naaaayeonn/AI-literacy-care-Agent` main `2. Content & RAG Agent/`
> 검토 범위: `agent.py · chunker.py · readability.py · rag_engine.py · quiz_generator.py ·
> restructurer.py · router.py · fallbacks.py · contracts.py · main.py · content_reducer_stub.py ·
> term_dictionary.json`
>
> 전반적으로 **폴백 설계(예외 비전파)·모드 토글(real/stub/demo)·계약 타입 정의가 탄탄**합니다.
> 아래는 실제 버그 / 정합성 / 확장 설계 미착수 항목이며, 심각도 순으로 정리했습니다.
> 각 항목에 `파일:라인 · 증상 · 원인 · 영향 · 수정안`을 담았습니다.

---

## 🔴 High — 실제 동작/성능/신뢰도에 영향

### H1. RAG 임베딩 성능 폭탄 — 요청마다 전체 용어집을 재인코딩
- **위치**: `rag_engine.py` `_find_terms()` memory 모드 (약 289~300행) + `inject_rag_terms()` (352~356행)
- **증상**: sentence-transformers 모델이 로드되면, 검색 텍스트 1건마다 `_TERM_DICT`의 **모든 용어를 `model.encode()`** 한다. 그리고 `inject_rag_terms`는 **청크마다** `_find_terms`를 호출한다.
- **원인**: 후보(용어집) 임베딩을 매 호출 새로 계산. 캐시가 없음.
  ```python
  # 지금: 청크 × 용어수 만큼 encode → 요청당 수백~수천 회
  for entry in _TERM_DICT:
      cand_vec = model.encode(candidate).tolist()   # ← 매번 재계산
  ```
- **영향**: `term_dictionary.json`이 크다(1016줄). 임베딩 모드가 켜지면 **요청당 수십 초** 지연 가능. (모델 미설치 시엔 keyword 폴백이라 안 느림 → 문제는 "임베딩 켜는 순간" 발현.)
- **수정안**: 용어집 임베딩을 **최초 1회만 계산해 캐시**하고, 쿼리만 매번 encode.
  ```python
  _TERM_VECS = None  # 지연 캐시
  def _term_vectors(model):
      global _TERM_VECS
      if _TERM_VECS is None:
          cands = [f"{e['term']} " + " ".join(e.get('aliases', [])) + f" {e['definition']}"
                   for e in _TERM_DICT]
          _TERM_VECS = model.encode(cands)  # batch, 1회
      return _TERM_VECS
  ```
  (pgvector 모드는 이미 DB에 임베딩을 저장하므로 OK. memory 모드만 해당.)

### H2. Faithfulness 점수가 항상 1.0 — 지표가 사실상 무의미
- **위치**: `rag_engine.py:368` `faith = _faithfulness_score(definition, definition)`
- **증상**: 같은 값을 두 번 넘겨 **항상 1.0** 반환. `_faithfulness_score`의 토큰 유사도 로직(325~332행)과 threshold 경고(371~375행)는 **절대 실행되지 않는 죽은 코드**.
- **원인**: 용어집 definition을 그대로 term.definition으로 쓰기 때문에 "직접 인용=1.0"으로 하드코딩된 상태.
- **영향**: 5번 QA가 **Ragas Faithfulness 실측값으로 기대**하는 지표인데, 실제로는 상수라 품질 신호가 되지 못함. `get_faithfulness_summary`의 `below_threshold`도 항상 0.
- **수정안**: 둘 중 하나로 정리.
  - (a) **유사도 매칭으로 가져온** definition은 실제 원문 문맥과 비교해 계산하도록 인자를 실제로 다르게 전달, 또는
  - (b) 현재가 "직접 인용 전제 상수"임을 **계약/트레이스에 명시**하고 5번에 "faithfulness=1.0은 검색(비생성) 보장 의미"라고 전달. 최소한 `_faithfulness_score(definition, definition)` 같은 오해 소지 호출은 상수로 교체(`faith = 1.0  # 직접 인용`).

### H3. 재구성 라우팅의 `term_count` 분기가 죽어 있음 (실행 순서 버그)
- **위치**: `agent.py` Step3(재구성 144행) → Step4(용어주입 155행) 순서 + `restructurer.py:162` `term_count = len(chunk.get("terms", []))`
- **증상**: 재구성 시점엔 **아직 terms가 주입되기 전**이라 `term_count`가 **항상 0**. `router.select_model`의 `term_count >= 3 → 고성능 모델` 분기(router.py:49)가 재구성 경로에서 **절대 발동 안 함**.
- **원인**: 파이프라인 순서가 "재구성 → 용어주입"인데, 라우팅은 용어 수에 의존.
- **영향**: 전문 용어 많은(=heavy 모델이 필요한) 청크가 경량 모델로 처리될 수 있음 → 재구성 품질 저하 가능.
- **수정안**: (a) Step4(용어주입)를 Step3(재구성) **앞으로** 옮기거나, (b) 재구성 라우팅에서 용어 수 대신 청크 난이도만 쓰도록 명시. 순서를 바꾸면 재구성 프롬프트에 용어 정보를 실어 품질도 개선 가능.

---

## 🟡 Medium — 계약 정합성 / 통합 시 문제

### M1. CORS `allow_credentials=True` + `allow_origins=["*"]` — 보안·일관성 문제
- **위치**: `main.py:37~43`
- **증상**: Starlette는 이 조합에서 raw `*` 대신 요청 Origin을 echo해 **동작은 하지만**, 결과적으로 **모든 사이트가 자격증명 포함 요청**을 보낼 수 있게 열림.
- **원인**: 쿠키/세션 인증을 안 쓰는데 `allow_credentials=True`를 켬. (우리 3번 백엔드 `main.py`는 `allow_credentials=False`로 맞춰져 있어 **정책 불일치**.)
- **영향**: 통합 시 오리진 정책 불일치 + 불필요한 노출. 확장(chrome-extension://)·임의 사이트 fetch 시 혼선.
- **수정안**: 인증쿠키를 안 쓰므로 `allow_credentials=False`로 변경(3번과 동일). 자격증명이 필요해지면 그때 오리진 화이트리스트로 좁힌다.

### M2. `_meta` 필드가 ChunkDict 계약 밖으로 누출
- **위치**: `restructurer.py:176~177, 182`
- **증상**: `chunk.setdefault("_meta", {})["routing"|"model"] = ...` — `contracts.py`의 `ChunkDict`엔 `_meta` 없음. 이 키가 chunks에 실려 **API 응답으로 그대로 나감**.
- **영향**: 4번 프론트/1번 오케스트레이터가 예상 못한 필드 수신. 계약 위반.
- **수정안**: 라우팅 메타는 `step_trace`(trace)로 옮기고 chunk에서 제거. 정말 chunk에 남겨야 하면 `contracts.ChunkDict`에 `_meta: NotRequired[dict]`로 명시.

### M3. `char_start`/`char_end` 부정확 — 프론트 하이라이트 어긋남
- **위치**: `chunker.py:135~139` (+ LangChain `chunk_overlap=40` 41행)
- **증상**: 위치 탐색이 `text.find(chunk_text, cursor)`이고 `cursor=이전 청크 end`. LangChain overlap으로 **다음 청크가 cursor 이전에서 시작**하면 `find`가 -1 → `start=cursor`(잘못된 값). 또 splitter가 공백/개행을 정규화하면 원문에서 정확히 못 찾음.
- **영향**: `char_start/char_end` 기반 4번 하이라이트가 틀어짐(계약 49~50행이 "프론트 하이라이트용"이라 명시).
- **수정안**: (a) overlap을 0으로, (b) 위치 탐색을 `cursor` 없이 `text.find(chunk_text)`로 하되 중복 텍스트 대비 마지막 매칭 cursor 유지, (c) 못 찾으면 `char_start=-1`로 표기해 프론트가 하이라이트 스킵하도록. 최소한 "청크는 원문의 연속 부분집합"을 보장.

### M4. `main.py` reduce — user_id/document_id를 profile에서만 추출
- **위치**: `main.py:89~90`
- **증상**: `req.profile.get("user_id"/"document_id")` — 요청 스키마(`ContentReducerRequestModel`)에 최상위 `user_id`/`document_id`가 없어, profile에 안 넣으면 **항상 default_user/default_doc**.
- **영향**: 2번 API를 직접 호출하는 소비자가 문서 식별자를 못 넘김 → chunk_id가 `chunk_default_doc_..`로 고정될 수 있음.
- **수정안**: 요청 모델에 `document_id`(옵션) 필드 추가하거나, 호출 계약 문서에 "profile.document_id 필수" 명시. (우리 3번 확장 경로는 별도 alias라 당장 깨지진 않으나, 실제 2번 연동 시 정합 필요.)

---

## 🟢 확장 설계(EXTENSION_DESIGN.md) — 2번 추가 작업 미착수

> 정본: `docs/EXTENSION_DESIGN.md` §10(2번), §9-5(PDF 텍스트 추출), §11(비용 0).
> 아래는 확장 기능을 위해 **새로 필요한** 2번 작업으로, 현재 코드엔 없음.

### E1. PDF 문단 재구성 로직 (§10 2번 ①)
- pdf.js `getTextContent()` 결과 → **문단 재구성**: 줄 병합, 하이픈 줄바꿈(`-\n`) 병합, 머리말/꼬리말(반복 라인) 제거.
- 현재 2번은 이미 합쳐진 `raw_text`만 받음 → PDF 특유의 깨진 줄바꿈 정제 로직이 없음.
- **필요**: pdf 텍스트 아이템 → 깨끗한 `content[]` 정규화 함수. (클라이언트 viewer.js가 1차 추출하더라도, 문단 재구성 품질 계약은 2번 몫으로 위임됨.)

### E2. 웹=Readability / PDF=pdf.js 두 소스의 `content[]` 정규화 통일 (§10 2번 ②)
- 두 입력원이 **동일한 `content[]` 형태**로 들어오도록 정규화 규격 확정. 현재 chunker/agent는 소스 구분 없이 raw_text만 처리 → 규격만 맞으면 재사용 가능하나, "동일 정규화" 보장 로직/문서가 필요.

### E3. 단어 hover 단건 lookup — 무료 경로 (§10 2번 ③, §11)
- 확장 오버레이의 **단어 hover 툴팁**용 "단어 1개 → 뜻" 경량 조회가 필요. 현재 `inject_rag_terms`는 **청크 배치**용이라 단건 hover엔 과함.
- **필요**: `lookup_term(word) -> TermDict | None` 형태의 단건 함수(용어집 직접 매칭 우선). **무료 경로만**(기존 term_dictionary/로컬 사전) — 유료 사전 API 금지.
- 3번이 확장용 `/api/terms/lookup` 엔드포인트를 붙이려면 이 함수가 전제.

### E4. (선택) 문단별 난이도 태그 (§10 2번 ④)
- 청크 `difficulty`는 이미 계산됨(chunker). 이를 "어려운 문단 우선 개입" 데이터로 노출하는 계약만 정리하면 재사용 가능.

---

## ⚪ Low — 개선/확인

- **L1. 순차 LLM 호출 + `time.sleep(0.05)`** (`restructurer.py:185`): 청크별 동기 호출. 긴 문서면 지연. 후속 async/배치 고려(데모엔 무방).
- **L2. 모델 ID 확인** (`router.py:21~22`, `quiz_generator.py:143`): `claude-haiku-4-5`(날짜 없는 별칭)·`claude-sonnet-4-5`가 실제 API에서 resolve되는지 확인 권장.
- **L3. 임베딩 유사도 threshold 0.3** (`rag_engine.py:311`): ko-sroberta 기준 0.3이면 무관 용어가 딸려올 수 있음. 데모 데이터로 튜닝 권장.
- **L4. `_load_term_dictionary` 예외 시 `print`**: 운영에선 로깅으로. (기능 문제는 아님.)

---

## 통합(1번 관점) 체크리스트

- [ ] **H1/H2/H3** 먼저 처리 — 성능·품질 신뢰도 직접 영향
- [ ] **M1 CORS** 3번과 정책 통일(`allow_credentials=False`)
- [ ] **M2 `_meta`** 제거 → 계약(ChunkDict) 클린 유지 (1번/4번이 그대로 소비)
- [ ] **E3 단건 lookup 함수** 제공 시점 공유 → 3번 확장 단어뜻 엔드포인트 일정 맞춤
- [ ] `run_content_reducer(state)` 시그니처는 유지 부탁(1번이 이 계약으로 호출). 변경 시 사전 공지.

> 문의: 1번(오케스트레이션). 계약 변경은 `contracts.py`와 함께 1번에 공지 바랍니다.
