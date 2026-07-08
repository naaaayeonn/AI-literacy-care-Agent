# AI Literacy Care Agent - Agent Role Architecture

> **하나의 글을 여러 지능이 나누어 읽고, 사용자의 읽는 힘을 다시 사용자에게 돌려주는 구조**

---

## 1. Agent Role Map

```mermaid
flowchart LR
    Input["원문 / PDF / 웹문서<br/>raw_text"]:::input
    Behavior["읽기 행동 로그<br/>scroll, pause, blur, focus"]:::input
    Quiz["퀴즈 결과<br/>correct / total"]:::input
    Profile0["기존 사용자 프로필<br/>past trend"]:::input

    subgraph A1["Model 1. Content Reducer"]
        A1Role["문서를 읽기 가능한 단위로 쪼개고<br/>핵심 개념과 난이도를 정리"]
        A1Out["chunks<br/>terms<br/>difficulty_score<br/>simplified_text"]
    end

    subgraph A2["Model 2. Cognitive Care"]
        A2Role["사용자가 실제로 읽고 있는지<br/>집중이 무너지는지 판단"]
        A2Out["focus_score<br/>engagement_score<br/>intervention_needed"]
    end

    subgraph A3["Model 3. Intervention Router"]
        A3Role["지금 개입할지, 얼마나 강하게 개입할지 결정"]
        A3Out["none<br/>soft: highlight<br/>medium: nudge<br/>hard: quiz"]
    end

    subgraph A4["Model 4. Literacy Score Engine"]
        A4Role["이해도, 집중도, 난이도, 비정상 읽기 패턴을<br/>하나의 설명 가능한 점수로 합성"]
        A4Out["literacy_score<br/>score_breakdown<br/>penalty_breakdown"]
    end

    subgraph A5["Model 5. Reward Agent"]
        A5Role["읽기 성취를 사용자에게 피드백"]
        A5Out["XP<br/>badge<br/>reward message"]
    end

    subgraph A6["Model 6. Profile Agent"]
        A6Role["이번 세션을 장기 성장 데이터로 누적"]
        A6Out["updated_profile<br/>growth trend<br/>personalization signal"]
    end

    subgraph A7["Model 7. Self-Correction Guard"]
        A7Role["결과가 비어 있거나 이상한지 검증하고<br/>fallback과 경고를 남김"]
        A7Out["warnings<br/>trace<br/>errors"]
    end

    Output["최종 사용자 경험<br/>개입 카드 + 점수 + 성장 피드백"]:::output

    Input --> A1Role --> A1Out
    Behavior --> A2Role --> A2Out
    A1Out --> A3Role
    A2Out --> A3Role --> A3Out
    Quiz --> A4Role
    A1Out --> A4Role
    A2Out --> A4Role --> A4Out
    A4Out --> A5Role --> A5Out
    Profile0 --> A6Role
    A4Out --> A6Role --> A6Out
    A1Out --> A7Role
    A2Out --> A7Role
    A4Out --> A7Role
    A5Out --> A7Role
    A6Out --> A7Role --> A7Out
    A3Out --> Output
    A4Out --> Output
    A5Out --> Output
    A6Out --> Output
    A7Out --> Output

    classDef input fill:#ecfeff,color:#083344,stroke:#0891b2;
    classDef output fill:#dcfce7,color:#052e16,stroke:#16a34a;
```

---

## 2. The Core Idea

```mermaid
flowchart TB
    Reader["Reader"]:::reader
    TextMind["Text Intelligence<br/>무엇을 읽는가"]:::model
    BehaviorMind["Behavior Intelligence<br/>어떻게 읽고 있는가"]:::model
    DecisionMind["Decision Intelligence<br/>지금 도와야 하는가"]:::model
    ScoreMind["Evaluation Intelligence<br/>읽는 힘이 어느 정도인가"]:::model
    GrowthMind["Growth Intelligence<br/>다음에는 어떻게 맞출 것인가"]:::model

    Reader --> TextMind
    Reader --> BehaviorMind
    TextMind --> DecisionMind
    BehaviorMind --> DecisionMind
    TextMind --> ScoreMind
    BehaviorMind --> ScoreMind
    ScoreMind --> GrowthMind
    GrowthMind -. personalization .-> TextMind
    DecisionMind -. real-time intervention .-> Reader
    ScoreMind -. feedback .-> Reader

    classDef reader fill:#111827,color:#ffffff,stroke:#111827;
    classDef model fill:#f8fafc,color:#0f172a,stroke:#64748b;
```

**이 프로젝트는 단일 챗봇이 아니라, 문서 이해 모델·행동 분석 모델·개입 판단 모델·점수화 모델·성장 관리 모델이 하나의 읽기 세션 상태를 공유하는 멀티 에이전트 구조다.**

---

## 3. Agent Responsibility Table

| Agent | 한 줄 역할 | 입력 | 판단 | 출력 |
|---|---|---|---|---|
| Content Reducer | 글을 읽기 가능한 학습 단위로 바꾸는 문서 분석가 | `raw_text` | 핵심 문단, 어려운 용어, 문서 난이도 | `chunks`, `terms`, `difficulty_score`, `simplified_text` |
| Cognitive Care | 사용자의 읽기 상태를 감지하는 집중도 관찰자 | `reading_events` | 빠른 스크롤, 이탈, 멈춤, 체류 패턴 | `focus_score`, `engagement_score`, `intervention_needed` |
| Intervention Router | 개입 타이밍과 강도를 정하는 지휘자 | `focus_score`, `chunks` | 그냥 둘지, 하이라이트할지, 넛지할지, 퀴즈를 낼지 | `intervention` |
| Literacy Score Engine | 읽기 능력을 설명 가능한 점수로 계산하는 평가자 | `quiz_result`, `focus_score`, `difficulty_score`, `reading_events` | 이해도 50%, 집중도 35%, 난이도 15%, 이상 행동 패널티 | `literacy_score`, `score_breakdown` |
| Reward Agent | 읽기 성취를 동기부여로 바꾸는 피드백 담당 | `literacy_score`, session result | 보상 수준, 배지, XP | `reward` |
| Profile Agent | 세션 결과를 장기 성장으로 누적하는 개인화 담당 | `profile`, `literacy_score`, `score_breakdown` | 성장 추세, 취약 지점, 다음 세션 힌트 | `updated_profile` |
| Self-Correction Guard | 시스템 결과를 검증하는 안전장치 | final state, `trace`, `errors` | 빈 출력, 점수 범위 오류, fallback 발생, 퀴즈 누락 | `warnings`, `trace`, `errors` |

---

## 4. Shared State as the Agent Bus

```mermaid
flowchart TB
    State[("ReadingSessionState<br/>Single Source of Truth")]:::state

    CR["Content Reducer<br/>writes: chunks, terms, difficulty"]:::agent
    CC["Cognitive Care<br/>writes: focus, engagement"]:::agent
    RT["Router<br/>writes: intervention"]:::agent
    SE["Score Engine<br/>writes: literacy_score"]:::agent
    RW["Reward<br/>writes: reward"]:::agent
    PF["Profile<br/>writes: updated_profile"]:::agent
    QA["Self-Correction<br/>writes: warnings"]:::agent

    State --> CR --> State
    State --> CC --> State
    State --> RT --> State
    State --> SE --> State
    State --> RW --> State
    State --> PF --> State
    State --> QA --> State

    classDef state fill:#fce7f3,color:#500724,stroke:#db2777;
    classDef agent fill:#f1f5f9,color:#0f172a,stroke:#475569;
```

모든 에이전트는 독립된 결과물을 따로 흩뿌리지 않고, 하나의 `ReadingSessionState`를 읽고 갱신한다. 그래서 최종 결과는 단순 응답이 아니라 **왜 그런 개입이 나왔는지, 어떤 점수 근거가 있는지, 어디서 fallback이 났는지까지 설명 가능한 세션 기록**이 된다.

---

## 5. Role-Centric Pipeline

```mermaid
flowchart LR
    T["Text<br/>무엇을 읽는가"]:::source
    B["Behavior<br/>어떻게 읽는가"]:::source
    Q["Quiz<br/>얼마나 이해했는가"]:::source

    M1["Content Reducer<br/>문서 구조화"]:::model
    M2["Cognitive Care<br/>집중도 추론"]:::model
    M3["Router<br/>개입 판단"]:::model
    M4["Score Engine<br/>리터러시 산출"]:::model
    M5["Reward<br/>성취 피드백"]:::model
    M6["Profile<br/>성장 누적"]:::model
    M7["Self-Correction<br/>품질 검증"]:::guard

    UX["Reader UI<br/>하이라이트 / 넛지 / 퀴즈 / 점수"]:::ux

    T --> M1
    B --> M2
    M1 --> M3
    M2 --> M3 --> UX
    Q --> M4
    M1 --> M4
    M2 --> M4
    M4 --> M5 --> UX
    M4 --> M6 --> UX
    M1 --> M7
    M2 --> M7
    M4 --> M7
    M7 --> UX
    M6 -. next session personalization .-> M1

    classDef source fill:#ecfeff,color:#083344,stroke:#0891b2;
    classDef model fill:#ede9fe,color:#2e1065,stroke:#7c3aed;
    classDef guard fill:#fee2e2,color:#450a0a,stroke:#dc2626;
    classDef ux fill:#dcfce7,color:#052e16,stroke:#16a34a;
```

---

## 6. Current Implementation Status

| Role | Current Status | Main File |
|---|---|---|
| Content Reducer | stub/real toggle, Gemini bridge path prepared | `backend/app/agents/content_reducer_client.py` |
| Cognitive Care | real scoring service connected through adapter | `backend/app/agents/cognitive_care_client.py` |
| Intervention Router | deterministic orchestrator logic implemented | `backend/app/orchestrator/routing.py` |
| Literacy Score Engine | deterministic scoring formula implemented | `backend/app/orchestrator/score.py` |
| Reward Agent | stub adapter prepared | `backend/app/agents/reward_client.py` |
| Profile Agent | stub adapter prepared | `backend/app/agents/literacy_profile_client.py` |
| QA / Evaluation | no-op adapter exists; self-correction guard implemented in orchestrator | `backend/app/agents/qa_eval_client.py`, `backend/app/orchestrator/self_correction.py` |

---

## 7. Presentation Sentence

**이 아키텍처의 핵심은 “글을 요약하는 AI”가 아니라, 문서 분석·읽기 행동 감지·실시간 개입·이해도 평가·성장 추적을 각 전문 에이전트가 나누어 수행하는 읽기 능력 관리 시스템이라는 점이다.**
