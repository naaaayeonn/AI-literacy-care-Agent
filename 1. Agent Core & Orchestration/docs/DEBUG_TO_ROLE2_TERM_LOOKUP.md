# 2번(RAG) 용어 lookup 오류 원인 총정리 — from 1번(오케스트레이션)

> 대상: `rag_engine.py`(`lookup_term`, `_query_llm_definition`, `_query_woorimalsem_api`, `_clean_korean_josa`) + `main.py`(`POST /api/terms/lookup`)
> 배경: Step 1(동적 LLM)·Step 2(우리말샘 API)·Step 3(조사 전처리) **코드 반영은 GitHub에서 확인 완료**.
> 그런데 실제로 돌리면 "여전히 뜻을 못 찾음/오류"가 난다고 하여, **에러 메시지별 경우의 수와 짐작되는 원인을 전부** 정리했습니다.

---

## 0. 먼저 알아둘 것 — 왜 "고쳤는데 그대로"로 보이는가

`lookup_term`의 2단계(우리말샘)·3단계(임베딩)·4단계(LLM)는 **전부 `try/except`로 예외를 삼키고 `print` 후 다음 단계로 넘어갑니다.**

```python
except Exception as e:
    print(f"[rag_engine] LLM 단어 실시간 유추 실패: {e}")   # 콘솔에만 찍고
    return None                                              # 조용히 다음으로
```

➡️ **SDK 미설치·키 없음·버전 불일치·네트워크 오류 등 무엇이 터져도 서버는 안 죽고, 결과만 `source="not_found"`로 나옵니다.**
➡️ 그래서 **진짜 원인은 이미 서버 콘솔 로그의 `[rag_engine] ... 실패: ...` 줄에 찍혀 있습니다. 이걸 먼저 보세요.**

**부탁**: 서버를 띄운 터미널에서 `[rag_engine]`로 시작하는 줄을 그대로 캡처해 보내주시면 아래 표에서 바로 매칭됩니다.

---

## 1. 증상별 → 원인 → 수정 (경우의 수 총정리)

### 케이스 A. 서버가 아예 안 뜸 / import 단계에서 죽음

| 에러 메시지(예상) | 원인 | 수정 |
|---|---|---|
| `ModuleNotFoundError: No module named 'backend'` | 실행 위치가 틀림. 코드가 절대 임포트(`from backend.app...`)라 **`2. Content & RAG Agent/` 폴더 안**에서 실행해야 함 | `cd "2. Content & RAG Agent"` 후 `uvicorn backend.app.main:app --reload --port 8000` |
| `ModuleNotFoundError: No module named 'backend.app...'` (경로 꼬임) | 폴더명에 **공백·`&`·숫자**(`2. Content & RAG Agent`)가 있어 쉘/경로가 깨짐 | 폴더 경로 전체를 따옴표로 감싸기. VS Code면 워크스페이스 루트를 이 폴더로 고정 |
| `ImportError: cannot import name 'ReadingSessionState' from ...contracts` | `main.py`가 `contracts`에서 임포트하는 심볼이 실제 파일에 없음(계약 파일 불일치) | `contracts.py`에 `ReadingSessionState/ContentReducerRequest/ContentReducerResponse/QuizGenerationRequest/QuizDict` 정의 존재 확인 |
| `ModuleNotFoundError: No module named 'fastapi'`(또는 dotenv/pydantic) | 의존성 미설치 | 폴더 안에서 `pip install -r requirements.txt` |

---

### 케이스 B. Step 1 (동적 LLM / Gemini) 관련 — **가장 유력**

코드가 쓰는 API: `from google import genai` → `genai.Client()` → `client.models.generate_content(model="gemini-2.0-flash", config=genai.types.GenerateContentConfig(...))`
이건 **신규 SDK `google-genai`(≥ 1.0)** 문법입니다.

| 로그/에러 메시지(예상) | 원인 | 수정 |
|---|---|---|
| `[rag_engine] LLM 단어 실시간 유추 실패: No module named 'google.genai'` 또는 `cannot import name 'genai' from 'google'` | 신규 SDK 미설치 | `pip install -U google-genai` |
| `[rag_engine] ... 실패: module 'google.genai' has no attribute 'Client'` / `'types'` | **버전이 너무 낮음.** `requirements.txt`가 `google-genai>=0.1.1`로 핀되어 0.x가 깔림 | `requirements.txt`를 `google-genai>=1.0.0`으로 수정 후 `pip install -U -r requirements.txt` |
| `from google import genai`가 엉뚱하게 잡힘 / `AttributeError` | **구 SDK `google-generativeai`와 혼재.** 같은 `google` 네임스페이스 충돌 (참고: 1번 브릿지는 구 SDK 사용) | 이 프로젝트에선 하나로 통일. `pip uninstall google-generativeai` 후 `google-genai`만 사용 |
| `[rag_engine] ... 실패: ... API key not valid` / `PermissionDenied` / `401` | `GEMINI_API_KEY`가 틀리거나 `your_...here` 그대로 | `.env`에 실제 키 기입. (참고: 코드에 `api_key.startswith("your_")`면 스킵하는 가드 있음 → 이 경우 에러 없이 조용히 not_found) |
| `[rag_engine] ... 실패: 429 RESOURCE_EXHAUSTED` / quota | 무료 티어 쿼터 소진 | 잠시 후 재시도 or 모델 폴백 추가(아래 3번 권장안 참고) |
| `[rag_engine] ... 실패: 'NoneType' object has no attribute 'strip'` | 응답이 안전차단/빈값이라 `response.text`가 None인데 `.strip()` 호출 | `result = (response.text or "").strip()`로 방어 |
| `[rag_engine] ... 실패: 404 ... model gemini-2.0-flash not found` | 모델명이 해당 키/리전에서 resolve 안 됨 | `gemini-2.0-flash` → `gemini-2.5-flash` 등으로 교체 시도 |

---

### 케이스 C. Step 2 (우리말샘 오픈 API) 관련

| 로그/에러 메시지(예상) | 원인 | 수정 |
|---|---|---|
| 에러 없이 우리말샘만 항상 스킵 | `WOORIMAL_API_KEY`(또는 `DICTIONARY_API_KEY`) 미설정 → 함수가 `None` 조기 반환 | 공공데이터포털에서 우리말샘 오픈API 키 발급 후 `.env`에 기입 |
| `[rag_engine] 우리말샘 API 호출 실패: HTTP Error 400/401` | 키가 `your_..._here` 그대로거나 무효. (LLM과 달리 **우리말샘엔 `your_` 가드가 없어** 그대로 호출됨) | 실제 키 기입. 미사용이면 `.env`에서 키를 아예 비워 스킵 유도 |
| `[rag_engine] 우리말샘 API 호출 실패: timeout` | 네트워크/공공API 지연(5초 타임아웃) | 재시도, 타임아웃 상향, 실패 시 다음 단계로 폴백(현재 동작) |
| `[rag_engine] ... 실패: string indices must be integers` 또는 `list indices ...` | 응답 파싱 취약. `data["channel"]["item"]`이 **결과 1건일 때 list가 아닌 dict**로 오는 경우 `items[0]`가 깨짐 | `items`가 dict면 `[items]`로 감싸 처리하는 방어 코드 추가 |
| `[rag_engine] ... 실패: Expecting value: line 1` (JSON 파싱) | API가 JSON이 아닌 에러 HTML/XML 반환(`req_type=json`인데 키 오류 등) | 응답 상태/본문 로깅 후 키·파라미터 점검 |

---

### 케이스 D. Step 3 (조사/전처리) 관련

| 증상 | 원인 | 수정 |
|---|---|---|
| "메타인지는" → "메타인지" 매칭 성공하는데, "은/는"이 명사 일부인 단어("우편함은" 정상, 하지만 "라면은"→"라며ㄴ" 류)에서 오깎임 | `_clean_korean_josa`가 **맨 끝 글자 기준 단순 접미 매칭**이라 명사 끝이 조사와 겹치면 과도 제거 | 데모 단어셋에선 큰 문제 아님. 정밀화 필요 시 형태소 분석기(Kiwi) 도입 |
| "주가 누르기 방지법을"처럼 **여러 단어(공백 포함)** 는 여전히 매칭 실패 | `_clean_korean_josa`는 조사만 제거할 뿐 **복합구를 핵심 명사로 쪼개지 않음** (특수문자 정규식 `[^\w\s\-]`가 공백을 유지) | 공백 분할 후 마지막/최장 명사만 재조회하는 로직 추가(선택 고도화) |
| 영어/숫자 섞인 단어가 깨짐 | `re.sub(r"[^\w\s\-]", ...)` 후 조사 리스트 매칭 | 대부분 무해. 케이스 발견 시 예외 목록 관리 |

---

### 케이스 E. 임베딩(sentence-transformers) 관련 — 조용한 실패지만 지연 유발

| 로그/증상 | 원인 | 수정 |
|---|---|---|
| 첫 요청이 수십 초 걸림 | 최초 호출 시 `jhgan/ko-sroberta-multitask` **모델 다운로드**(수백 MB) | 최초 1회 지연은 정상. 서버 기동 시 워밍업 호출 권장 |
| `_get_embedding_model`이 항상 None(임베딩 스킵) | `sentence-transformers`/`torch` 미설치 or import 실패(조용히 None 폴백) | 임베딩 매칭이 필요하면 `pip install sentence-transformers`. 데모에선 없어도 1·2·4 단계로 동작 |
| 임베딩은 되는데 엉뚱한 용어 매칭 | 유사도 threshold `0.3`이 낮음(무관 용어 딸려옴) | 데모 데이터로 0.4~0.5 튜닝 |

---

### 케이스 F. 엔드포인트/요청 레벨 (3번·4번 연동 시)

| 에러 | 원인 | 수정 |
|---|---|---|
| HTTP `422 Unprocessable Entity` | 요청 바디 필드명 불일치. 스키마는 `word`(필수), `sessionId`, `context` | 호출부가 `{"word": "...", "context": "..."}` 형태로 보내는지 확인 |
| HTTP `500 Lookup failed: ...` | `lookup_term` **바깥**에서 예외(내부는 다 캐치됨). 대개 import 시점 문제 | `detail` 메시지의 실제 예외 확인 → 케이스 A/B와 대조 |
| CORS 차단 | 확장/타 오리진에서 호출 | `main.py`는 이미 `allow_origins=["*"], allow_credentials=False` → 정상. 안 되면 프리플라이트 확인 |
| 결과는 오는데 `definition`이 빈 문자열 + `source="not_found"` | 위 B/C/E가 전부 조용히 실패한 최종 폴백 | 콘솔의 `[rag_engine] ... 실패` 로그로 실제 실패 단계 특정 |

---

## 2. 5분 자가진단 (폴더 안에서 순서대로 실행)

```bash
cd "2. Content & RAG Agent"

# ① 신규 Gemini SDK 설치/버전 확인 (케이스 B)
python -c "import google.genai as g; print('google-genai', getattr(g,'__version__','?'))"

# ② 패키지 import 경로 확인 (케이스 A)
python -c "from backend.app.agents.content_reducer.rag_engine import lookup_term; print('import OK')"

# ③ 실제 lookup 동작 + 삼켜진 에러 콘솔 노출 (케이스 B/C/E)
python -c "from backend.app.agents.content_reducer.rag_engine import lookup_term; print(lookup_term('메타인지를', '기사 문맥 예시입니다'))"

# ④ 키 로딩 확인 (케이스 B/C)
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('GEMINI:', bool(os.getenv('GEMINI_API_KEY')) and not os.getenv('GEMINI_API_KEY','').startswith('your_')); print('WOORIMAL:', bool(os.getenv('WOORIMAL_API_KEY')) and not os.getenv('WOORIMAL_API_KEY','').startswith('your_'))"
```

**판독법**
- ①에서 `ImportError`/버전 `0.x` → **케이스 B (SDK)** 확정 → `google-genai>=1.0.0` 설치
- ②에서 `ModuleNotFoundError` → **케이스 A (실행 위치)** 확정
- ③에서 콘솔에 `[rag_engine] ... 실패: ...`가 찍히면 그 메시지를 위 표에서 매칭
- ④에서 `False`면 해당 키 미설정 → 그 경로는 원래 스킵되는 게 정상(에러 아님)

---

## 3. 권장 개선(선택) — 실패를 "조용히" 두지 말 것

지금은 모든 실패가 `print`로만 남아 원인 파악이 어렵습니다. 최소 두 가지만 반영하면 디버깅이 훨씬 쉬워집니다.

1. **응답에 실패 흔적 남기기**: `lookup_term`이 not_found를 반환할 때, 어느 단계까지 시도했는지(`tried: ["local","woorimal","embed","llm"]`)를 응답 메타에 실어 프론트/로그에서 원인 추적 가능하게.
2. **LLM 응답 None 방어**: `result = (response.text or "").strip()` — 안전차단·빈응답 시 `AttributeError` 방지.
3. **(여유되면) `requirements.txt` 핀 상향**: `google-genai>=1.0.0` — 0.x가 깔리는 사고 원천 차단.

---

## 4. 1번이 필요한 것 (회신 요청)

아래 중 하나만 보내주시면 원인 1개로 특정해 드립니다.

- [ ] 서버 콘솔의 `[rag_engine]`로 시작하는 실패 로그 줄, 또는
- [ ] `500` 응답의 `detail` 전문, 또는
- [ ] 위 **2. 자가진단 ①~④의 출력 결과**

> 요약: **Step 1~3 코드 반영은 끝났고, 남은 건 순수 실행환경(SDK 버전·실행 위치·API 키·응답 파싱) 문제**입니다. 전부 조용히 실패하는 구조라 증상이 안 바뀐 것뿐이며, 콘솔 로그 한 줄이면 정확한 지점을 잡을 수 있습니다.
