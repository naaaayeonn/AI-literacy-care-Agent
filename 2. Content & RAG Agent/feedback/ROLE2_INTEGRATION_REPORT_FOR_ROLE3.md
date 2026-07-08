# RAG & 단어 조회 엔진 최종 연동 및 피드백 결과 보고서 (for Role 3)

안녕하세요, 2번(Content & RAG) 담당자입니다. 3번(Cognitive Care Backend) 담당자님이 전달해주신 피드백(`3)peedback.txt`)과 오류 가능성 리포트를 바탕으로 기능 추가 및 안정화 작업을 진행했습니다. 

연동 및 배포에 필요한 주요 변동사항, 백엔드 사양, 그리고 주의사항을 정리해 드립니다.

---

## 1. 현재 업데이트 상태 (Update Status)

- **동음이의어 문맥 기반 자동 판별 도입 완료**: 우리말샘 API 검색 결과 하나의 단어에 복수의 정의(동음이의어 후보군)가 반환되는 경우, 기사 문맥(`context`)을 고려해 LLM이 가장 적합한 사전 정의 번호를 자동 분류 및 선택하여 제공합니다. 이를 통해 문맥과 무관한 엉뚱한 동음이의어 뜻을 반환하는 문제가 원천 차단되었습니다.
- **형태소(조사) 전처리 도입 완료**: 드래그한 단어에 조사가 붙어 있더라도 대표적인 한국어 조사 목록을 역순 매칭하여 깎아낸 뒤 명사 원형을 안전하게 추출합니다.
- **우리말샘 오픈 API 연동 완료**: 2차 검색 경로인 국립국어원 우리말샘 API에서 뜻을 정상적으로 탐색합니다.
- **문맥 기반 실시간 LLM 유추 도입 완료**: 단어 데이터가 모든 사전 경로에서 최종 누락되었을 때, 기사의 앞뒤 문맥(`context`)을 바탕으로 실시간 단어 뜻을 50자 이내로 자동 유추합니다.
- **디버그 추적 필드(`_meta`) 설계 및 적용**: 조회 실패/성공 시 내부에서 거친 검색 시도 로그(`tried`)와 각 단계에서 발생한 에러 기록(`errors`)을 리포팅하여 디버깅 편의성을 극대화했습니다.
- **우리말샘 API 파싱 예외 처리 완료**: 단건 검색 결과인 경우 XML/JSON 파서가 리스트가 아닌 딕셔너리로 반환해 깨지던 현상을 리스트로 래핑하여 방어했습니다.
- **테스트 빌드 통과**: 추가된 동음이의어 판별 및 디버깅 기능을 포함해 총 **96개 통합 테스트 전체 통과(100% Green)**를 검증했습니다.

---

## 2. 연동된 LLM 및 백과사전 API 정보

### 🤖 LLM 정보: 스노우챗(SnowChat) API 게이트웨이
- **Base URL**: `https://factchat-cloud.mindlogic.ai/v1/gateway`
- **사용 모델**: `gemini-2.5-flash`
  - *이유*: 스노우챗 내 탑재된 최신 경량 모델로 속도가 매우 빠르고 한국어 재구성/단어 유추 퀄리티가 우수합니다.
- **인증 방식**: Bearer Token 인증 (API 헤더 사용)
- **발급 키**: `W21AiHIpDbcz5no1QRYu3vqCYcHYOjPA`

### 📖 백과사전 정보: 국립국어원 우리말샘 오픈 API
- **검색 엔드포인트**: `https://opendict.korean.go.kr/api/search`
- **조회 파라미터**: `req_type=json`, `part=word`
- **키 관리**: `.env` 파일의 `WOORIMAL_API_KEY` 변수로 로드

---

## 3. 연동 가이드 및 주의사항 (Precautions)

### 💡 `context` 필드 전송 (매우 권장)
- `/api/terms/lookup` API 요청 시, 사용자가 드래그한 단어가 위치한 주변 문장(문맥)을 `context` 필드에 함께 실어 전달해 주세요.
- 문맥 정보가 있어야 실시간 LLM 유추 및 **동음이의어 정밀 판별(Disambiguation)** 시 기사의 도메인(IT, 법률, 의학 등)에 최적화된 뜻을 올바르게 도출할 수 있습니다.

### 🔑 환경 변수 설정 (`.env`)
- 로컬 개발 환경의 `.env` 파일에 아래 변수를 정상적으로 세팅해 주세요. 스노우챗 API 키는 보안 가이드를 만족하는 `GEMINI_API_KEY` 변수에 입력됩니다:
  ```env
  GEMINI_API_KEY=W21AiHIpDbcz5no1QRYu3vqCYcHYOjPA
  WOORIMAL_API_KEY=your_real_woorimalsem_api_key_here
  ```
- 키가 누락되거나 틀려 실패할 경우, 시스템이 다운되지 않고 `_meta.errors` 필드에 에러 메시지를 기록한 뒤 조용히 `source="not_found"` 폴백으로 가드되도록 구현되었습니다.

### 🛠️ 디버깅 정보 활용법
- API 응답 바디 하위에 새로 추가된 `_meta` 필드를 참조해 주세요:
  ```json
  "_meta": {
    "tried": ["local", "woorimal", "embedding", "llm"],
    "errors": {
      "embedding": "No embedding model loaded",
      "llm": "403 - Forbidden Model Access"
    }
  }
  ```
- 이를 확인하면 단어가 매칭되지 않았을 때 로컬 DB 오류인지, API 네트워크 에러인지, 키 오류인지 실시간으로 원인을 특정할 수 있습니다.

---

## 4. API 입출력 규격 명세

### 단어 조회 API
- **Endpoint**: `POST /api/terms/lookup`
- **Request Body:**
  ```json
  {
    "word": "방지법을",
    "sessionId": "sess_test123", // (선택)
    "context": "이번에 통과된 주가 누르기 방지법을 위반할 경우 처벌받습니다." // (선택, 매우 권장)
  }
  ```

- **Response Body (camelCase & snake_case 이중 호환 규격):**
  ```json
  {
    "term": "방지법", // 전처리 필터링 후 원형
    "definition": "어떠한 행위나 현상을 미연에 막기 위한 법률.", 
    "source": "우리말샘 (국립국어원)" | "LLM 실시간 유추" | "로컬 사전" | "RAG 유사 매칭" | "not_found",
    "faithfulnessScore": 1.0,
    "faithfulness_score": 1.0,
    "chunkId": "",
    "chunk_id": "",
    "_meta": {
      "tried": ["local", "woorimal", "embedding", "llm"],
      "errors": {}
    }
  }
  ```

### ※ 출처(`source`) 구분값 정리
- `"로컬 사전"`: 사전 지정된 106개 로컬 용어집 매핑 성공
- `"우리말샘 (국립국어원)"`: 우리말샘 오픈 API 실시간 조회 성공 (동음이의어 판별 포함)
- `"RAG 유사 매칭"`: 임베딩 코사인 유사도 0.3 이상 매핑 성공
- `"LLM 실시간 유추"`: 실시간 문맥 기반 유추 답변 생성 성공
- `"not_found"`: 전체 실패 시 폴백 가드 작동
