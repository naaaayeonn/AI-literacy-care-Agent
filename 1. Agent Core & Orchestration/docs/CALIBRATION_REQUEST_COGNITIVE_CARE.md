# 캘리브레이션 요청 — Cognitive Care (3번 ↔ 1번)

## 배경

3번 `cognitive_care.py`(`calculate_focus_score`, `determine_intervention`)를 오케스트레이터 real impl로 연결 완료했습니다. (`LITERACY_COGNITIVE_CARE_IMPL=real`)

연결은 정상 동작하는데, **점수 캘리브레이션 이슈**가 있어 조율 요청합니다.

## 문제

동일한 데모 읽기 이벤트(blur 2회 등)로 비교:

| 구현 | focus_score | 최종 intervention |
|---|---|---|
| 기존 stub | 39.0 | **medium / nudge** |
| 3번 real | **95.4** | **none** ❌ |

현재 3번 식은 **blur 1초당 2점 감점**이라, 산만하게 읽어도 95점이 나옵니다.
그 결과 이 프로젝트의 핵심 장면인 **"집중 저하 → 개입"이 데모에서 사라집니다.**

## 참고: 개입 레벨은 1번 routing이 단독 결정

최종 intervention level은 오케스트레이터 `routing.py`가 focus_score로 결정합니다.
즉 3번은 **focus_score만 현실적인 분포로** 내주면 됩니다.

```
focus_score >= 75  → none
50 <= focus < 75   → soft   (하이라이트)
30 <= focus < 50   → medium (넛지/재읽기)
focus < 30         → hard   (퀴즈)
```

## 요청 사항

1. **blur(이탈) 감점 강화** — 이탈은 집중 저하의 강한 신호. 1초당 2점은 너무 약합니다.
   이탈 1회당 고정 감점 + 시간 비례 감점 조합 권장.
2. **빠른 스크롤(찍어보기) 감점** — 현재 누적 5회 초과부터만 감점. `duration_ms < 300` 같은
   빠른 스크롤은 개별로 감점해 주세요.
3. **(선택) engagement_score 산출** — 현재 미산출이라 1번이 focus_score로 대체 중입니다.
   별도 신호(체류시간/재방문 등)로 내주면 점수 설명력이 좋아집니다.

## 캘리브레이션 목표 (이 3개 시나리오로 검증)

| 시나리오 | 이벤트 구성 | 기대 focus | 기대 개입 |
|---|---|---|---|
| 집중 읽기 | pause 위주, blur 0 | **≥ 80** | none |
| 산만(데모) | blur 2회(≈2.3s) + 빠른 scroll 2회 | **35~50** | medium |
| 매우 산만 | blur 4회 이상 | **≤ 30** | hard |

특히 **데모 시나리오에서 focus ≤ 50**이 나와야 발표에서 개입 장면을 보여줄 수 있습니다.

## 연결 위치 (참고)

- 1번 repo: `1. Agent Core & Orchestration/backend/app/agents/real/cognitive_care_service.py`
  (3번 원본 그대로 이식 — 3번이 갱신하면 이 파일만 교체하면 됩니다)
- 어댑터: `.../agents/cognitive_care_client.py`
