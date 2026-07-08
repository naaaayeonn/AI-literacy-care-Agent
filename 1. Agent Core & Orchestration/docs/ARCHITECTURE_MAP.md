# AI Literacy Care Agent Architecture

> **AI가 글을 대신 읽어주는 시대, 사람의 읽는 힘을 측정하고 회복시키는 Closed-Loop Care System**

---

## 1. System Big Picture

```mermaid
flowchart TB
    User["Reader<br/>Web Article / PDF"]:::actor

    subgraph EXT["Chrome Extension Layer"]
        Popup["Popup UI<br/>on/off control"]:::ui
        Content["Content Script<br/>article extraction"]:::ui
        PDF["PDF Viewer<br/>pdf.js based reader"]:::ui
        Tracker["Reading Tracker<br/>scroll / pause / blur / focus"]:::edge
        Overlay["Intervention Overlay<br/>nudge / highlight / quiz"]:::edge
    end

    subgraph API["FastAPI Boundary"]
        SessionAPI["/api/session<br/>extension contract"]:::api
        CoreAPI["/api/reading-sessions<br/>core contract"]:::api
        Contract["Frontend Contract Mapper<br/>camelCase <-> state"]:::api
    end

    subgraph CORE["Orchestrator Core"]
        State["ReadingSessionState<br/>single source of truth"]:::state
        Graph["Reading Session Graph<br/>step runner + fallback"]:::core
        Routing["Routing Decision<br/>none / soft / medium / hard"]:::core
        SelfCheck["Self-Correction<br/>warnings / trace / errors"]:::core
    end

    subgraph AGENTS["Agent Modules"]
        Reducer["Content Reducer<br/>chunks / terms / difficulty"]:::agent
        Cognitive["Cognitive Care<br/>focus / engagement"]:::agent
        Score["Literacy Score Engine<br/>comprehension + engagement"]:::agent
        Reward["Reward Agent<br/>XP / badge"]:::agent
        Profile["Profile Agent<br/>growth trend"]:::agent
    end

    Store[("In-Memory Session Store<br/>SESSION_STORE")]:::store

    User --> Content
    User --> PDF
    Popup --> Content
    Content --> Tracker
    PDF --> Tracker
    Tracker --> SessionAPI
    SessionAPI --> Contract
    CoreAPI --> State
    Contract --> State
    State <--> Store
    State --> Graph
    Graph --> Reducer
    Graph --> Cognitive
    Graph --> Routing
    Graph --> Score
    Graph --> Reward
    Graph --> Profile
    Graph --> SelfCheck
    Routing --> Contract
    Contract --> Overlay
    Overlay --> User

    classDef actor fill:#111827,color:#ffffff,stroke:#111827;
    classDef ui fill:#e0f2fe,color:#0f172a,stroke:#0284c7;
    classDef edge fill:#dcfce7,color:#052e16,stroke:#16a34a;
    classDef api fill:#fef3c7,color:#451a03,stroke:#d97706;
    classDef state fill:#fce7f3,color:#500724,stroke:#db2777;
    classDef core fill:#ede9fe,color:#2e1065,stroke:#7c3aed;
    classDef agent fill:#f1f5f9,color:#0f172a,stroke:#475569;
    classDef store fill:#fee2e2,color:#450a0a,stroke:#dc2626;
```

---

## 2. Runtime Flow

```mermaid
sequenceDiagram
    autonumber
    participant R as Reader
    participant E as Chrome Extension
    participant A as FastAPI
    participant S as SESSION_STORE
    participant O as Orchestrator
    participant G as Agent Modules

    R->>E: Open article or PDF
    E->>E: Extract readable content
    E->>A: POST /api/session/start<br/>content[], userId, source
    A->>G: Content Reducer
    G-->>A: chunks, terms, difficultyScore
    A->>S: Save ReadingSessionState
    A-->>E: sessionId + reader setup data

    loop While reading
        R->>E: scroll / pause / blur / focus
        E->>A: POST /api/session/{id}/events
        A->>S: Append normalized events
        A->>G: Cognitive Care
        G-->>A: focusScore, engagementScore
        A->>O: Routing Decision
        O-->>A: intervention command
        A-->>E: nudge / highlight / quiz / none
        E-->>R: Render subtle intervention
    end

    E->>A: GET /api/session/{id}/result
    A->>O: Run full session graph
    O->>G: Score -> Reward -> Profile -> Self-Correction
    G-->>A: literacyScore, reward, updatedProfile, warnings
    A->>S: Save final state
    A-->>E: Final result
```

---

## 3. Orchestrator Pipeline

```mermaid
flowchart LR
    Raw["raw_text<br/>profile<br/>reading_events"]:::input
    Reducer["1. Content Reducer<br/>chunking, terms, difficulty"]:::step
    Cognitive["2. Cognitive Care<br/>focus, engagement"]:::step
    Route["3. Routing Decision<br/>intervention level"]:::step
    Score["4. Score Engine<br/>literacy score"]:::step
    Reward["5. Reward<br/>XP, badge"]:::step
    Profile["6. Profile Update<br/>growth trend"]:::step
    Review["7. Self-Correction<br/>warnings, trace"]:::step
    Result["final result<br/>score, profile, trace"]:::output

    Raw --> Reducer --> Cognitive --> Route --> Score --> Reward --> Profile --> Review --> Result

    classDef input fill:#ecfeff,color:#083344,stroke:#0891b2;
    classDef step fill:#f8fafc,color:#0f172a,stroke:#64748b;
    classDef output fill:#dcfce7,color:#052e16,stroke:#16a34a;
```

The pipeline is intentionally state-first. Every module reads and writes the same `ReadingSessionState`, so the system can explain what happened through `trace`, recover with fallback values through `errors`, and surface quality issues through `warnings`.

---

## 4. Layered Architecture

```mermaid
flowchart TB
    L1["Experience Layer<br/>popup, overlay, PDF viewer, article page"]:::l1
    L2["Capture Layer<br/>content extraction, reading event tracker"]:::l2
    L3["API Layer<br/>FastAPI routers, CORS, contract mapping"]:::l3
    L4["State Layer<br/>ReadingSessionState, SESSION_STORE"]:::l4
    L5["Intelligence Layer<br/>content reducer, cognitive care, routing, scoring"]:::l5
    L6["Growth Layer<br/>reward, profile trend, self-correction"]:::l6

    L1 --> L2 --> L3 --> L4 --> L5 --> L6
    L6 -. personalized next session .-> L5
    L5 -. intervention command .-> L1

    classDef l1 fill:#dbeafe,color:#172554,stroke:#2563eb;
    classDef l2 fill:#ccfbf1,color:#042f2e,stroke:#0d9488;
    classDef l3 fill:#fef3c7,color:#451a03,stroke:#d97706;
    classDef l4 fill:#fce7f3,color:#500724,stroke:#db2777;
    classDef l5 fill:#ede9fe,color:#2e1065,stroke:#7c3aed;
    classDef l6 fill:#dcfce7,color:#052e16,stroke:#16a34a;
```

---

## 5. Key Modules

| Area | Path | Responsibility |
|---|---|---|
| App entry | `backend/app/main.py` | FastAPI app, CORS, router mounting, `.env` loading |
| Extension API | `backend/app/api/extension_session.py` | Browser extension contract, camelCase payloads, intervention/result mapping |
| Core API | `backend/app/api/reading_session.py` | Internal reading session lifecycle: start, events, quiz, finish, result |
| State model | `backend/app/orchestrator/state.py` | Shared typed state used by all agents |
| Flow runner | `backend/app/orchestrator/graph.py` | Ordered agent execution, fallback handling, trace logging |
| Routing | `backend/app/orchestrator/routing.py` | Decides whether and how strongly to intervene |
| Score | `backend/app/orchestrator/score.py` | Calculates reproducible literacy score and score breakdown |
| Extension shell | `extension/manifest.json` | Chrome MV3 extension permissions, popup, content scripts |
| Shared extension logic | `extension/shared/` | Tracker, overlay, session client reused by article/PDF flows |
| PDF reader | `extension/pdf/` | Local PDF viewer powered by bundled pdf.js |

---

## 6. Data Contract Snapshot

```mermaid
erDiagram
    ReadingSessionState {
        string session_id
        string user_id
        string document_id
        string raw_text
        object profile
        list reading_events
        list chunks
        string simplified_text
        list terms
        float difficulty_score
        float focus_score
        float engagement_score
        object intervention
        object quiz_result
        float comprehension_score
        float literacy_score
        object score_breakdown
        object reward
        object updated_profile
        list trace
        list errors
        list warnings
    }

    ReadingEvent {
        string type
        int timestamp_ms
        float position
        int duration_ms
        object metadata
    }

    InterventionCommand {
        string level
        string type
        string message
        string target_chunk_id
        string reason
    }

    ReadingSessionState ||--o{ ReadingEvent : collects
    ReadingSessionState ||--o| InterventionCommand : emits
```

---

## 7. One-Line Architecture Summary

**브라우저에서 읽기 행동을 수집하고, FastAPI 오케스트레이터가 이해도와 집중도를 계산해 실시간 개입과 성장 추적까지 되돌려주는 폐루프 AI 리터러시 케어 구조.**
