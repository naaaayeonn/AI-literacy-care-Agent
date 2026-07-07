# 시계열 성장 추세 설계 메모 (7/3 · 설계 단계)

> 상태: **설계 메모(초안)**. 이번 단계는 구현이 아니라 "어떤 데이터로 성장
> 추세를 만들고, 어떻게 다음 세션에 되먹임할지" 기준을 정한다.
> 코드 변경 없음. 계약 변경은 **제안(proposal)** 이며 확정은 M2 통합(7/5~),
> 동결은 M3(7/10).

## 1. 목적

단일 세션 점수가 아니라 **"성장하고 있는가"** 를 보여주는 것이 이 프로젝트의
차별점이다 (ARCHITECTURE §10: "ChatGPT는 텍스트를 처리한다 / 우리는 읽기 과정과
성장을 관리한다"). 이를 위해 세션별 `literacy_score`를 누적해 추세를 계산하고,
그 추세를 다음 세션의 난이도·개입 기준에 되먹인다.

## 2. 현재 구현 (v0, baseline)

`backend/app/agents/stubs/literacy_profile_stub.py`

- 입력: `profile.previous_literacy_score` (단일 값)
- 비교: `literacy_score` vs `previous_literacy_score` (±3 임계)
- 출력: `updated_profile.trend` ∈ `improving | declining | stable | baseline`

한계: **점 2개 비교**라 노이즈에 약하고, 그래프용 시계열 데이터가 없으며,
문서 난이도가 다르면 점수 비교가 공정하지 않다.

## 3. 데이터 모델 (제안)

프로필이 **점수 히스토리**를 들고 다닌다. 저장 주체는 5번(Profile/DB), 1번은
shape만 정의한다. (state.py의 `profile`/`updated_profile`은 dict라 스키마 변경
불필요 — 아래는 dict 하위 구조 약속이다.)

```json
{
  "reading_level": "intermediate",
  "score_history": [
    { "session_id": "s_001", "document_id": "doc1", "literacy_score": 64.0, "difficulty_score": 60.0, "timestamp_ms": 1719000000000 },
    { "session_id": "s_002", "document_id": "doc2", "literacy_score": 70.0, "difficulty_score": 72.0, "timestamp_ms": 1719600000000 }
  ],
  "weaknesses": ["technical_terms"]
}
```

- `score_history`는 **최근 N개(예: 20)만 유지**(capped). 오래된 건 잘라낸다.
- 프론트 성장 그래프는 `score_history[].literacy_score`(+timestamp)만 있으면 그린다.

## 4. 추세 계산 (단계적)

| 단계 | 방법 | 비고 |
|---|---|---|
| v0 (현재) | 직전 1개 vs 현재 (±3) | 노이즈 취약 |
| v1 | 최근 K개(예: 3) **이동평균** 비교 | 단발성 변동 완화 |
| v2 | 최근 K개 **선형회귀 기울기**(slope) | 기울기 부호·크기로 분류 |

분류 규칙(v1/v2 공통, 임계는 튜닝 대상):

```text
delta = 현재(또는 최근평균) - 직전구간평균
delta >  +T  → improving
delta <  -T  → declining
그 외        → stable
히스토리 부족 → baseline   (cold start)
```

**난이도 보정**: 문서마다 `difficulty_score`가 다르므로, 추세 비교 전에
난이도를 반영해 정규화한다. 예: `adjusted = literacy_score + (difficulty_score - 50) * w`.
(높은 난이도에서 같은 점수면 더 큰 성장으로 본다.)

## 5. 되먹임 루프 (Self-Correction / 개인화)

추세가 다음 세션의 두 가지 기준을 조정한다.

1. **난이도 추천** (→ 2번 Content Reducer 입력 `profile`)
   - `improving` + 높은 focus → 다음 글 난이도 ↑
   - `declining` → 난이도 ↓ 또는 쉬운 설명 비중 ↑
2. **개입 민감도** (→ 1번 routing.py 임계)
   - `declining` → focus 임계를 올려 **더 빨리** 개입 (예: soft 시작점 50→60)
   - `improving` → 개입 임계 완화

> 주의: routing.py 임계 상수를 프로필에 따라 바꾸는 것은 **계약 변경**이므로
> M3 동결 전에 합의한다. v0~v1까지는 "추천값만 출력"하고 실제 라우팅 반영은
> M2 이후 선택적으로 켠다.

## 6. 계약 변경 (제안 → API_CONTRACT 반영)

5번 Literacy Profile 계약 확장(기존 필드는 유지, **추가만**):

- 입력: `profile.score_history` (이전 세션 누적, 없으면 `[]` = cold start)
- 출력 `updated_profile`에 추가:
  - `previous_scores`: `list[float]` (그래프용, score_history에서 추출)
  - `trend`: 기존 유지 (`improving|stable|declining|baseline`)
  - `recommended_difficulty`: float (다음 글 난이도 추천, 선택)
  - `recommended_next_action`: 기존 유지

호환성: 모두 **추가 필드**이며 기존 `trend` 동작은 그대로 → 프론트/기존 테스트
무영향. v0 stub은 `score_history`가 없으면 지금처럼 단일 비교로 동작.

## 7. 구현 순서 (이 메모 이후)

```text
1) profile 입력에 score_history 수용 (없으면 baseline) — 하위호환
2) updated_profile.previous_scores 채우기 (그래프 우선)
3) v1 이동평균 trend
4) recommended_difficulty 산출 (Content Reducer 입력으로 전달)
5) (선택) routing 임계의 프로필 기반 조정 — M2 이후, 합의 필요
```

## 8. 미해결/합의 필요

- `score_history` 영속화 위치: 데모는 요청 `profile`에 실어 왕복 vs 서버 보관(5번 DB).
- 추세 임계 `T`, 윈도우 `K`, 난이도 가중 `w`의 기본값.
- routing 임계를 프로필로 바꿀지 여부(계약 변경 영향).
