# [Delivery Plan] ③ 백엔드 & 실시간 데이터 처리 (Backend & Real-time Data)

본 문서는 **2026 AI·SW 디지털 경진대회 SW부문**에 참가하는 **AllDayHappyDay** 팀의 프로젝트 **'AI 리터러시 케어 에이전트'** 중 **③ 백엔드 & 실시간 데이터 처리** 역할의 개발 및 인도 계획서(DELIVERY_PLAN.md)이다.

본 계획은 상용화 기능(인증/JWT 등)을 배제하고, 대회 MVP(최소 기능 제품) 구현을 타겟으로 **FastAPI 서버 구축, PostgreSQL/Redis 로컬 구동, 실시간 WebSocket 로그 수집, 집중도 Scoring Logic v1 구현 및 대시보드 API 완성**을 목표로 한다.

---

## 📅 일자별 개발 계획 (6/20 ~ 7/6)

### 1단계: M0 - 인프라 및 더미 E2E 통신 단계 (6/20 ~ 6/22)

#### 6/20 (토)
| 항목 | 내용 |
| :--- | :--- |
| **목표** | 로컬 개발 인프라 구축 및 FastAPI 웹 서버 스캐폴딩 |
| **구현할 파일** | [docker-compose.yml](file:///C:/Users/Administrator/.gemini/antigravity/scratch/literacy-backend/docker-compose.yml)<br>[requirements.txt](file:///C:/Users/Administrator/.gemini/antigravity/scratch/literacy-backend/requirements.txt)<br>[app/main.py](file:///C:/Users/Administrator/.gemini/antigravity/scratch/literacy-backend/app/main.py)<br>[app/core/config.py](file:///C:/Users/Administrator/.gemini/antigravity/scratch/literacy-backend/app/core/config.py) |
| **완료 기준** | `docker-compose up` 명령어로 PostgreSQL 및 Redis가 구동되고, FastAPI 서버 헬스체크 API (`GET /health`) 호출 시 `200 OK`를 응답함. |
| **팀원 확인사항** | 전체 파트 공통 사용 Python 버전(예: 3.11) 및 빌드 환경 합의. |
| **실패 시 대체안** | Docker 구동 에러 발생 시, 로컬 PC에 PostgreSQL 및 Redis를 개별 서비스로 수동 설치하여 테스트 진행. |

#### 6/21 (일)
| 항목 | 내용 |
| :--- | :--- |
| **목표** | 데이터베이스 관계형 스키마 설계 및 ORM 모델 정의 |
| **구현할 파일** | [app/db/session.py](file:///C:/Users/Administrator/.gemini/antigravity/scratch/literacy-backend/app/db/session.py)<br>[app/models/user.py](file:///C:/Users/Administrator/.gemini/antigravity/scratch/literacy-backend/app/models/user.py)<br>[app/models/document.py](file:///C:/Users/Administrator/.gemini/antigravity/scratch/literacy-backend/app/models/document.py)<br>[app/models/session.py](file:///C:/Users/Administrator/.gemini/antigravity/scratch/literacy-backend/app/models/session.py)<br>[app/models/log.py](file:///C:/Users/Administrator/.gemini/antigravity/scratch/literacy-backend/app/models/log.py)<br>[app/models/quiz.py](file:///C:/Users/Administrator/.gemini/antigravity/scratch/literacy-backend/app/models/quiz.py)<br>[app/models/profile.py](file:///C:/Users/Administrator/.gemini/antigravity/scratch/literacy-backend/app/models/profile.py) |
| **완료 기준** | SQLAlchemy ORM 구동 시 PostgreSQL 내에 정의한 7개 테이블이 에러 없이 자동 생성(DDL 수행)되고 더미 Insert가 성공함. |
| **팀원 확인사항** | ① 코어 파트(이소희)와 DB 기본 키 구조 및 에이전트 공유 상태 스키마 구조 정합성 검증. |
| **실패 시 대체안** | ORM 자동 생성 설정 오류 발생 시, raw SQL DDL 스크립트를 작성하여 DB 툴(DBeaver 등)로 직접 테이블 생성 후 진행. |

#### 6/22 (월) [M0]
| 항목 | 내용 |
| :--- | :--- |
| **목표** | WebSocket 통신 인터페이스 프로토타입 구현 (M0 달성) |
| **구현할 파일** | [app/websocket/manager.py](file:///C:/Users/Administrator/.gemini/antigravity/scratch/literacy-backend/app/websocket/manager.py)<br>[app/websocket/endpoint.py](file:///C:/Users/Administrator/.gemini/antigravity/scratch/literacy-backend/app/websocket/endpoint.py) |
| **완료 기준** | WebSocket 테스트 클라이언트를 통해 특정 `session_id`로 연결이 이루어지고, 더미 JSON 행동 데이터 송수신 메시지가 터미널 콘솔 로그에 확인됨. |
| **팀원 확인사항** | ④ 프론트엔드 파트와 WebSocket 이벤트 페이로드 포맷(JSON Key) 및 데이터 전송 주기(2초) 최종 합의. |
| **실패 시 대체안** | 로컬 WebSocket 포트 충돌 또는 웹소켓 드라이버 장애 시, 일반 HTTP POST API를 2초 간격으로 호출하는 폴링(Polling) 방식으로 임시 우회 구현. |

---

### 2단계: M1 - 핵심 폐루프 시연 단계 (6/23 ~ 6/29)

#### 6/23 (화)
| 항목 | 내용 |
| :--- | :--- |
| **목표** | 실시간 행동 데이터의 Redis 임시 적재 로직 완성 |
| **구현할 파일** | [app/services/session_service.py](file:///C:/Users/Administrator/.gemini/antigravity/scratch/literacy-backend/app/services/session_service.py) |
| **완료 기준** | WebSocket을 통해 유입되는 미세 데이터(스크롤, 체류시간 등)가 Redis List (`raw_behavior:{session_id}`)에 순차적으로 push되어 메모리에 캐싱됨. |
| **팀원 확인사항** | 실시간 세션이 이탈될 경우 Redis 데이터의 TTL(Time-To-Live, 2시간 설정안) 타당성 조율. |
| **실패 시 대체안** | Redis 메모리 오류 또는 커넥션 지연 시, PostgreSQL 임시 세션 행동 테이블(`temp_behavior_logs`)을 구성하여 직접 insert 처리. |

#### 6/24 (수)
| 항목 | 내용 |
| :--- | :--- |
| **목표** | 실시간 집중도 Scoring Logic v1 수학 모듈 구현 |
| **구현할 파일** | [app/services/scoring.py](file:///C:/Users/Administrator/.gemini/antigravity/scratch/literacy-backend/app/services/scoring.py) |
| **완료 기준** | 평균 스크롤 속도, 문단별 체류시간 리스트, 이탈 횟수를 인풋으로 넣어 가우시안 및 감점 수식을 거친 최종 0~100 사이의 집중도 점수가 리턴됨. |
| **팀원 확인사항** | ② 콘텐츠/RAG 파트에서 계산해 주는 지문 정보 내 문단별 기대 독해 소요시간 ($T_{expected}$) 데이터 규격 확인. |
| **실패 시 대체안** | 실시간 복잡도 계산 오버헤드 우려 시, 가우시안 확률 밀도 계산을 제거하고 [실제 체류시간 / 예상 체류시간] 비율의 단순 평균 산식으로 v1을 단순화. |

#### 6/25 (목)
| 항목 | 내용 |
| :--- | :--- |
| **목표** | 퀴즈 결과 저장 및 실시간 독해 진행률 업데이트 API 구현 |
| **구현할 파일** | [app/api/v1/sessions.py](file:///C:/Users/Administrator/.gemini/antigravity/scratch/literacy-backend/app/api/v1/sessions.py)<br>[app/schemas/session.py](file:///C:/Users/Administrator/.gemini/antigravity/scratch/literacy-backend/app/schemas/session.py) |
| **완료 기준** | `POST /api/v1/sessions/{session_id}/quiz` API 호출을 통해 사용자가 작성한 답안 및 정답 여부 정보가 `quiz_results` 테이블에 성공적으로 저장됨. |
| **팀원 확인사항** | 퀴즈 정답 검증 로직의 담당 주체 결정 (프론트에서 즉시 채점 후 결과값만 백엔드로 보낼 것인지, 백엔드에서 정답 테이블과 비교 검증할지). |
| **실패 시 대체안** | 개별 퀴즈 API 연동 지연 시, 세션 종료 API (`complete`) 호출 시 퀴즈 결과 배열을 포함해 단일 트랜잭션으로 저장하도록 스펙 통합. |

#### 6/26 (금)
| 항목 | 내용 |
| :--- | :--- |
| **목표** | 최종 Literacy Score 산출 및 세션 완료 처리 API 구축 |
| **구현할 파일** | [app/api/v1/sessions.py](file:///C:/Users/Administrator/.gemini/antigravity/scratch/literacy-backend/app/api/v1/sessions.py) (complete endpoint)<br>[app/services/scoring.py](file:///C:/Users/Administrator/.gemini/antigravity/scratch/literacy-backend/app/services/scoring.py) (score synthesis) |
| **완료 기준** | 세션 종료 API 호출 시 Redis의 행동 데이터를 전부 조회하여 PostgreSQL에 Bulk Insert하고, 최종 문해력 점수(이해도 x 집중도 x 가독성 보정)를 계산하여 응답함. |
| **팀원 확인사항** | ① 코어 파트(이소희)와 Literacy Score 산출 공식의 세부 가중치(Comprehension vs Engagement 비율) 확정. |
| **실패 시 대체안** | 난이도 보정 및 가중 합산 복잡 연산 시 오류가 발생할 경우, 가독성 지표 보정을 제외한 [퀴즈 정답률 x 집중도] 단순 곱 산출법 적용. |

#### 6/27 ~ 6/28 (토~일)
| 항목 | 내용 |
| :--- | :--- |
| **목표** | API 안전 장치 마련 및 비정상 이탈 예외 처리 튜닝 |
| **구현할 파일** | [app/main.py](file:///C:/Users/Administrator/.gemini/antigravity/scratch/literacy-backend/app/main.py) (Exception Handler)<br>[app/websocket/endpoint.py](file:///C:/Users/Administrator/.gemini/antigravity/scratch/literacy-backend/app/websocket/endpoint.py) (Disconnect handler) |
| **완료 기준** | 유저가 퀴즈를 다 안 풀고 세션을 강제 종료하거나 브라우저를 닫을 때, 백엔드가 500 에러를 뱉지 않고 기본 예외 로그 및 세션 타임아웃 처리를 완결함. |
| **팀원 확인사항** | 프론트엔드 연동용 로컬 및 개발 도메인 CORS 허용 정책 설정 정보 수집. |
| **실패 시 대체안** | 세밀한 예외 분기가 지연될 경우, 최상위 `try-except Exception`으로 에러 감싸기(wrapping)만 처리 후 통과. |

#### 6/29 (월) [M1]
| 항목 | 내용 |
| :--- | :--- |
| **목표** | 테스트 지문 및 유저 데이터 시딩, M1 흐름 동작 검증 (M1 달성) |
| **구현할 파일** | [app/db/seeds.py](file:///C:/Users/Administrator/.gemini/antigravity/scratch/literacy-backend/app/db/seeds.py) |
| **완료 기준** | DB 시드 스크립트 실행 후 1편의 테스트 글 독해 시작 -> 실시간 웹소켓 행동로그 전송 -> 퀴즈 풀이 -> 세션 종료 -> Literacy Score 확인 전과정이 단일 세션에서 완벽히 수동 시뮬레이션됨. |
| **팀원 확인사항** | ⑤ QA 파트와 M1 데모 완주 여부 검증 및 시연 브라우저 연동 점검. |
| **실패 시 대체안** | 프론트-백 연동 에러 발생 시, 로컬에서 Postman API Runner 기능을 활용하여 시나리오 API들을 순차 호출하는 백엔드 시퀀스 동작만 검증. |

---

### 3단계: M2 - 누적 데이터 시계열 분석 및 대시보드 연동 단계 (6/30 ~ 7/6)

#### 6/30 (화)
| 항목 | 내용 |
| :--- | :--- |
| **목표** | 장기 리터러시 프로필(Literacy Profile) 적재 로직 구현 |
| **구현할 파일** | [app/services/profile.py](file:///C:/Users/Administrator/.gemini/antigravity/scratch/literacy-backend/app/services/profile.py)<br>[app/api/v1/profile.py](file:///C:/Users/Administrator/.gemini/antigravity/scratch/literacy-backend/app/api/v1/profile.py) |
| **완료 기준** | 개별 세션의 점수가 산출될 때마다 사용자의 `literacy_profiles` 레코드 내 누적 세션 횟수가 증가하고, 취약점 분석 정보가 JSONB 데이터로 자동 업데이트됨. |
| **팀원 확인사항** | ① 코어 파트 및 ⑤ QA 파트와 취약점 판단 조건(예: 퀴즈 난이도 '하' 오답 시 어휘 취약 판단 등) 조건 검토. |
| **실패 시 대체안** | JSONB 취약 영역 분석 적재 구현 지연 시, 단순 누적 세션 횟수와 세션별 최종 점수의 평균값만 갱신 저장하도록 간소화. |

#### 7/1 (수)
| 항목 | 내용 |
| :--- | :--- |
| **목표** | 게이미피케이션 리워드(XP/레벨) 처리 및 집계 API 완성 |
| **구현할 파일** | [app/services/reward_service.py](file:///C:/Users/Administrator/.gemini/antigravity/scratch/literacy-backend/app/services/reward_service.py)<br>[app/api/v1/analytics.py](file:///C:/Users/Administrator/.gemini/antigravity/scratch/literacy-backend/app/api/v1/analytics.py) |
| **완료 기준** | 세션 종료 시 계산된 점수에 맞춰 유저 경험치(XP)가 갱신되어 반영되고, 대시보드 호출용 집계 API(`GET /api/v1/analytics/summary`) 호출 시 정상 리스트가 반환됨. |
| **팀원 확인사항** | ④ 프론트 파트가 요구하는 주간/월간 시계열 데이터 가공 형식 및 경험치 테이블 설계 검토. |
| **실패 시 대체안** | 레벨업 로직에 따른 실시간 처리가 늦어질 경우, 경험치 누적은 제외하고 단순 Literacy Score의 날짜별 추이 데이터만 시계열 API로 전송. |

#### 7/2 ~ 7/4 (목~토) [개인 일정 반영 최소 작업 기간]
| 항목 | 내용 |
| :--- | :--- |
| **목표** | 로그 시스템 점검, 데이터 스키마 명세화 및 버그 검수 |
| **구현할 파일** | [app/models/README.md](file:///C:/Users/Administrator/.gemini/antigravity/scratch/literacy-backend/app/models/README.md) (스키마 명세서) |
| **완료 기준** | 신규 기능 개발 없이 기존 작성 모듈들의 로깅 포맷 확인 및 스키마 변경 불필요성 확정. |
| **팀원 확인사항** | 타 파트(프론트, RAG)와의 데이터 불일치 이슈 수집 및 문서 업데이트. |
| **실패 시 대체안** | 스키마 명세화 지연 시 테이블 주석(Comment)만 DB 내에 직접 명시하고 문서화 작업은 생략함. |

#### 7/5 (일)
| 항목 | 내용 |
| :--- | :--- |
| **목표** | 프론트엔드 및 AI 에이전트 코어와의 전체 데이터 흐름 최종 통합 연동 |
| **구현할 파일** | [app/main.py](file:///C:/Users/Administrator/.gemini/antigravity/scratch/literacy-backend/app/main.py) (인터페이스 조율 및 추가 라우터 점검) |
| **완료 기준** | 실제 프론트엔드 UI 화면에서 사용자가 지문을 읽고 퀴즈를 푸는 동안 백엔드 DB와 Redis가 실시간 연동되어 UI 상에 성장 추이가 그려짐. |
| **팀원 확인사항** | 최종 시연에 활용할 시나리오용 테스트 지문 ID 고정 및 최종 API 명세 확인. |
| **실패 시 대체안** | 특정 에이전트 연동 부분에서 예외가 날 경우, 백엔드에서 해당 에이전트 호출을 bypass하고 미리 생성해둔 목업(Mock) 데이터셋을 리턴하도록 긴급 변경. |

#### 7/6 (월) [M2]
| 항목 | 내용 |
| :--- | :--- |
| **목표** | 데이터 통합 시나리오 테스트 진행 및 백엔드 파트 최종 완료 선언 (M2 달성) |
| **구현할 파일** | [tests/integration_test.py](file:///C:/Users/Administrator/.gemini/antigravity/scratch/literacy-backend/tests/integration_test.py) |
| **완료 기준** | 100회 이상의 WebSocket 미세 스트리밍 전송 및 퀴즈 제출, 대시보드 시계열 분석 호출로 이루어지는 종합 테스트 코드가 통과함. |
| **팀원 확인사항** | ⑤ QA 파트와의 백엔드 데이터 정합성 검증 확인서 승인. |
| **실패 시 대체안** | 시나리오 테스트 상 실패 항목 발생 시, 지장을 주는 일부 마이너 기능(경험치 배지 획득 등)의 연동 부분을 비활성화하고 코어 읽기 흐름만 통과 처리함. |

---

### [M3] 2번/5번 최종 통합 현황 (2026-07-09 기준)

> 1번 팀 코드리뷰 반영 · 기능 프리즈 전 최종 상태

| 항목 | 상태 | 근거 |
| :--- | :--- | :--- |
| **2번(Content Reducer) 통합** | ✅ **완료** | `/start` → `run_content_reducer(state)` 실제 호출, chunks/terms/difficulty 정상 생성 확인 |
| **5번(Quiz/QA) 퀴즈 채점 저장 (Q1)** | ✅ **완료** | `/quiz/submit` 채점 결과 `session:{id}:quiz_result` Redis에 누적 저장 |
| **5번(Quiz/QA) correct_count 계약 (Q2)** | ✅ **완료** | `/result` quiz_result를 `{correct_count, total_count}` 구조로 교체, stub(`qa_evaluation_stub`) 삭제 |
| **5번(Quiz/QA) 정답키 채점 (Q3)** | ✅ **완료** | `submit_quiz` 하드코딩 제거 → `correctOption`/`selectedOption` 비교 채점, 폴백 포함 |
| **5번 QA 품질 게이트 (Q4)** | ✅ **완료** | `run_evaluation_from_state` 지연 로딩 try/except로 `/result`에 부착, 실패 시 `state["errors"]`에만 기록 |

**결론**: M3의 2번은 이미 완료, 5번 퀴즈/QA 배선(Q1~Q4) 모두 2026-07-09에 배선 완료.  
`score.py`가 `correct_count/total_count`를 읽어 실제 정답률 → Literacy Score 이해도 항목이 실 연결됨.  
기능 프리즈(7/10) 전 완료 선언.
