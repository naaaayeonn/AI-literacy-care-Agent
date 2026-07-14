from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid
import json
from datetime import datetime, timezone

from ..core.db import get_db
from ..core.redis import get_redis
from ..models.models import ReadingSession, ReadingEvent, User, QuizResult
from ..schemas.schemas import (
    SessionStartRequest, SessionStartResponse, SessionFinishRequest, SessionFinishResponse, EventsRequestModel,
    QuizSubmitRequest, QuizSubmitResponse, TermExplainRequest, TermExplainResponse
)
from ..orchestrator.state import create_initial_state
from ..orchestrator.graph import run_reading_session
from .frontend_contract import to_intervention_command, to_session_result
from ..services.cognitive_care import (
    calculate_focus_score,
    determine_intervention,
    _scroll_velocity,
    _personalized_scroll_threshold,
)


def _update_user_scroll_baseline(user, state_events: list, difficulty_score: float) -> None:
    """세션 종료 시 개인화 baseline을 EWMA로 갱신한다(rolling).

    이번 글 난이도 D에서 "정상 읽기"로 스크롤한 속도의 중앙값을 관측치 v_obs로 삼아,
    D에 더 가까운 캘리브레이션 점(easy/hard)을 v_obs 쪽으로 당긴다. n_sessions++로 신뢰도↑.
    """
    if user is None:
        return
    base = getattr(user, "scroll_baseline", None)
    if not isinstance(base, dict) or base.get("easy") is None:
        return  # 온보딩 baseline이 있어야 갱신 대상이 됨

    thr = _personalized_scroll_threshold(base, difficulty_score)
    vels = []
    for e in state_events:
        if e.get("type") != "scroll":
            continue
        v = _scroll_velocity(e)  # top-level velocity 또는 metadata.payload.scrollVelocity 자동 처리
        if 0.05 < v < thr:  # 스키밍(≥thr)·정지(≈0) 제외 = 정상 읽기 속도
            vels.append(v)
    if not vels:
        return
    vels.sort()
    v_obs = vels[len(vels) // 2]  # 중앙값

    alpha = 0.3
    d_easy = float(base.get("d_easy", 20.0))
    d_hard = float(base.get("d_hard", 75.0))
    nb = dict(base)
    if abs(difficulty_score - d_easy) <= abs(difficulty_score - d_hard):
        nb["easy"] = round((1 - alpha) * float(base.get("easy", v_obs)) + alpha * v_obs, 3)
    else:
        nb["hard"] = round((1 - alpha) * float(base.get("hard", v_obs)) + alpha * v_obs, 3)
    try:
        nb["n_sessions"] = int(base.get("n_sessions", 0)) + 1
    except (TypeError, ValueError):
        nb["n_sessions"] = 1
    user.scroll_baseline = nb
from ..services.quiz_service import select_quiz_for_state, generate_ox_quiz

router = APIRouter(prefix="/api/session", tags=["Sessions"])



@router.post("/start", response_model=SessionStartResponse)
async def start_session(req: SessionStartRequest, request: Request, db: AsyncSession = Depends(get_db)):
    from sqlalchemy.exc import IntegrityError
    user_result = await db.execute(select(User).filter(User.id == req.userId))
    user = user_result.scalars().first()
    if not user:
        user = User(id=req.userId)
        db.add(user)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            # 경합으로 이미 생성됐으면 다시 조회
            user = (await db.execute(select(User).filter(User.id == req.userId))).scalars().first()

    session_id = f"s_{uuid.uuid4().hex[:8]}"
    document_id = req.articleId or "doc"
    
    new_session = ReadingSession(
        id=session_id,
        user_id=req.userId,
        document_id=document_id
    )
    db.add(new_session)
    await db.commit()
    
    # 개인화 스크롤 baseline: 유저에 누적된 rolling baseline을 우선 사용하고, 없으면 온보딩값 사용.
    # (rolling은 세션을 거칠수록 정교해지므로 신뢰도가 높다)
    redis_client = await get_redis()
    baseline_val = None
    persisted = getattr(user, "scroll_baseline", None) if user else None
    if isinstance(persisted, dict) and persisted.get("easy") is not None:
        baseline_val = persisted
    elif req.baselineScrollSpeed:
        baseline_val = {
            "easy": req.baselineScrollSpeed.easy,
            "hard": req.baselineScrollSpeed.hard,
            "d_easy": (req.baselineScrollSpeed.dEasy if req.baselineScrollSpeed.dEasy is not None else 20.0),
            "d_hard": (req.baselineScrollSpeed.dHard if req.baselineScrollSpeed.dHard is not None else 75.0),
            "n_sessions": 0,
        }
        # 온보딩값을 유저에 초기 저장(다음 세션부터 rolling 갱신)
        try:
            user.scroll_baseline = baseline_val
            await db.commit()
        except Exception:
            await db.rollback()
    if baseline_val:
        await redis_client.set(f"session:{session_id}:baseline", json.dumps(baseline_val))

    host = request.headers.get("host", "localhost:8000")
    ws_endpoint = f"ws://{host}/ws/reading/{session_id}"
    
    # 2번 연동 (실제 Content Reducer 에이전트 적용)
    from ..agents.content_reducer.agent import run_content_reducer
    
    if req.rawText:
        mock_raw_text = req.rawText
    elif req.content:
        mock_raw_text = "\n\n".join(req.content)
    else:
        mock_raw_text = "AI 기술의 발전에 따라 우리의 삶은 크게 변화하고 있습니다. 특히 문해력이 중요한 시기가 되었습니다. 다양한 정보를 비판적으로 수용하고 활용하는 능력이 필수적입니다. 인공지능이 제공하는 정보를 무조건 믿기보다는 스스로 생각하고 판단하는 힘을 길러야 합니다."
    
    state = create_initial_state(session_id=session_id, user_id=req.userId, document_id=document_id, raw_text=mock_raw_text)
    updated_state = run_content_reducer(state)
    
    def map_term(t):
        return {"term": t["term"], "definition": t["definition"], "source": t["source"], "faithfulnessScore": t.get("faithfulness_score", 1.0), "chunkId": t["chunk_id"]}

    def map_chunk(c):
        return {
            "chunkId": c["chunk_id"], "originalText": c["original_text"],
            "restructuredText": c.get("restructured_text", ""), "difficulty": c["difficulty"],
            "charStart": c["char_start"], "charEnd": c["char_end"],
            "terms": [map_term(t) for t in c.get("terms", [])]
        }
        
        
    article_data = {
        "id": document_id,
        "title": "AI 리터러시 데모 아티클 (2번 연동)",
        "category": "Technology",
        "author": "AI Care System",
        "content": [c["original_text"] for c in updated_state.get("chunks", [])],
        "difficulty": str(updated_state.get("difficulty_score", 50.0)),
        "chunks": [map_chunk(c) for c in updated_state.get("chunks", [])]
    }
    
    # 퀴즈 미리 생성하여 Redis에 캐싱 — 순수 O/X(진술문+참·거짓). role-1 canonical과 정렬.
    # 4지선다 질문에 O/X 버튼을 붙이던 방식(의미 불일치)을 폐기하고, 2번 summary로
    # 참·거짓 판별 가능한 진술문을 만든다(generate_ox_quiz).
    quizzes = {}
    for c in updated_state.get("chunks", []):
        summary = c.get("summary") or c.get("restructured_text") or c.get("original_text", "")
        paragraph = c.get("original_text") or c.get("restructured_text", "")
        q = generate_ox_quiz(summary, paragraph, c["chunk_id"], session_id)
        q["chunkId"] = c["chunk_id"]      # 3번 캐시 키 호환
        q["sessionId"] = session_id
        quizzes[c["chunk_id"]] = q
        
    redis_client = await get_redis()
    await redis_client.set(f"session:{session_id}:quizzes", json.dumps(quizzes))
    await redis_client.set(f"session:{session_id}:chunks", json.dumps(updated_state.get("chunks", [])))
    # 글 난이도/이독성(문서 레벨) 보관 → /result 점수 계산 시 재사용(도전력 도메인 품질).
    await redis_client.set(f"session:{session_id}:textmeta", json.dumps({
        "difficulty_score": updated_state.get("difficulty_score", 50.0),
        "readability_score": updated_state.get("readability_score", 50.0),
    }))
    
    return SessionStartResponse(
        sessionId=session_id, 
        article=article_data,
        wsEndpoint=ws_endpoint
    )

@router.post("/{session_id}/events")
async def process_events(session_id: str, req: EventsRequestModel):
    redis_client = await get_redis()
    try:
        redis_key = f"session:{session_id}:events"
        for ev in req.events:
            await redis_client.rpush(redis_key, ev.model_dump_json())
            
        all_events_raw = await redis_client.lrange(redis_key, 0, -1)
        reading_events = []
        for raw in all_events_raw:
            data = json.loads(raw)
            reading_events.append({
                "type": data["type"],
                "timestamp_ms": data["timestamp_ms"],
                "position": data.get("position"),
                "duration_ms": data.get("duration_ms"),
                "velocity": data.get("velocity"),
                "metadata": data
            })

        # 개인화 캘리브레이션 baseline 로드
        baseline_raw = await redis_client.get(f"session:{session_id}:baseline")
        baseline = None
        if baseline_raw:
            try:
                baseline = json.loads(baseline_raw)
            except Exception:
                pass

        # 글 난이도(2번) 로드 → 난이도-인지 스키밍 임계값에 사용
        difficulty_score = None
        textmeta_raw = await redis_client.get(f"session:{session_id}:textmeta")
        if textmeta_raw:
            try:
                difficulty_score = json.loads(textmeta_raw).get("difficulty_score")
            except Exception:
                pass

        user_requested_quiz = any(e.get("type") == "request_quiz" for e in reading_events)
        focus_score = calculate_focus_score(reading_events, baseline, difficulty_score)
        intervention_needed, intervention_level, msg = determine_intervention(focus_score)
        
        state = create_initial_state(session_id=session_id, user_id="", document_id="", raw_text="")
        state["reading_events"] = reading_events
        
        from .frontend_contract import _completion_rate
        current_progress = _completion_rate(state)
        
        if user_requested_quiz:
            intervention_needed = True
            intervention_level = "hard"
            msg = "요청하신 이해도 퀴즈입니다."
        elif current_progress >= 100:
            intervention_needed = True
            intervention_level = "hard"
            msg = "끝까지 다 읽으셨군요! 마무리 퀴즈를 풀어보세요. 📝"
            
        level_to_type = {"none": "none", "soft": "highlight", "medium": "nudge", "hard": "quiz"}
        internal_type = level_to_type.get(intervention_level, "none")
        
        state["focus_score"] = focus_score
        state["intervention"] = {
            "level": intervention_level,
            "type": internal_type,
            "message": msg
        }
        
        # 퀴즈(hard 개입)인 경우 캐시된 퀴즈 중 하나를 선택
        if internal_type == "quiz":
            quizzes_raw = await redis_client.get(f"session:{session_id}:quizzes")
            chunks_raw = await redis_client.get(f"session:{session_id}:chunks")
            asked_raw = await redis_client.get(f"session:{session_id}:asked_quizzes")
            last_quiz_time_raw = await redis_client.get(f"session:{session_id}:last_quiz_time")
            finish_quiz_shown_raw = await redis_client.get(f"session:{session_id}:finish_quiz_shown")
            
            if quizzes_raw and chunks_raw:
                state["quizzes"] = json.loads(quizzes_raw)
                state["chunks"] = json.loads(chunks_raw)
                state["asked_quiz_ids"] = json.loads(asked_raw) if asked_raw else []
                
                import time
                current_time = time.time()
                last_quiz_time = float(last_quiz_time_raw) if last_quiz_time_raw else 0.0
                finish_quiz_shown = bool(finish_quiz_shown_raw)
                
                # M3: 쿨다운(25초) 및 상한(최대 3번) 체크
                is_finishing = current_progress >= 100
                can_show_quiz = True
                
                if user_requested_quiz:
                    can_show_quiz = True
                elif is_finishing:
                    if finish_quiz_shown:
                        can_show_quiz = False
                else:
                    if current_time - last_quiz_time < 25.0:
                        can_show_quiz = False
                    if len(state["asked_quiz_ids"]) >= 3:
                        can_show_quiz = False

                if can_show_quiz:
                    # 완독 마무리 퀴즈는 최대 1번만
                    selected_quizzes = select_quiz_for_state(state, ignore_asked=False)
                    
                    # [C1] JIT 퀴즈가 생성되었을 수 있으므로 quizzes를 Redis에 다시 저장
                    await redis_client.set(f"session:{session_id}:quizzes", json.dumps(state["quizzes"]))
                    
                    if selected_quizzes:
                        # [M3] 3문제 띄워주기 위해 최대 3개 반환
                        selected_quiz = selected_quizzes[:3]
                        state["intervention"]["quiz_data"] = selected_quiz
                        
                        # 출제 기록 업데이트
                        for q in selected_quiz:
                            state["asked_quiz_ids"].append(q["quizId"])
                        await redis_client.set(f"session:{session_id}:asked_quizzes", json.dumps(state["asked_quiz_ids"]))
                        await redis_client.set(f"session:{session_id}:last_quiz_time", str(current_time))
                        
                        if is_finishing:
                            await redis_client.set(f"session:{session_id}:finish_quiz_shown", "1")
                    else:
                        # 적절한 퀴즈가 없으면
                        if is_finishing and not user_requested_quiz:
                            state["intervention"]["level"] = "none"
                            state["intervention"]["type"] = "none"
                            state["intervention"]["message"] = ""
                        else:
                            state["intervention"]["level"] = "medium"
                            state["intervention"]["type"] = "nudge"
                else:
                    # 퀴즈를 띄울 수 없으면 강제로 none 또는 nudge 처리
                    state["intervention"]["level"] = "none"
                    state["intervention"]["type"] = "none"
                    state["intervention"]["message"] = ""
        
        return to_intervention_command(state)
    except Exception as e:
        import logging
        logging.error(f"Error in process_events: {e}")
        raise

@router.post("/{session_id}/quiz/submit", response_model=QuizSubmitResponse)
async def submit_quiz(session_id: str, req: QuizSubmitRequest, db: AsyncSession = Depends(get_db)):
    """O/X 답안 서버 채점 + 이해도 누적. role-1 canonical과 정렬.

    정답키(answer)는 서버 캐시에만 있고 프론트로 나가지 않으므로(위조 불가),
    selectedOption("O"/"X")을 캐시된 정답과 비교해 채점한다. 채점 결과는
    quiz_result(correct/total)로 누적해 result 엔드포인트의 이해도 산출에 쓴다.
    """
    redis_client = await get_redis()
    quizzes_raw = await redis_client.get(f"session:{session_id}:quizzes")
    if not quizzes_raw:
        raise HTTPException(status_code=404, detail="No quizzes found for session")

    quizzes = json.loads(quizzes_raw)
    if isinstance(quizzes, dict):
        quiz_list = list(quizzes.values())
    elif isinstance(quizzes, list):
        quiz_list = quizzes
    else:
        quiz_list = []

    target_quiz = next((q for q in quiz_list if q["quizId"] == req.quizId), None)
    if not target_quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # 서버 채점: "O"=True, "X"=False
    is_correct = (req.selectedOption == "O") == bool(target_quiz["answer"])
    focus_recovered = 15.0 if is_correct else 0.0
    xp_earned = 10 if is_correct else 0

    # 이해도 산출용 누적(result 엔드포인트가 quiz_result를 읽는다)
    quiz_key = f"session:{session_id}:quiz_result"
    existing_raw = await redis_client.get(quiz_key)
    existing = json.loads(existing_raw) if existing_raw else {"correct_count": 0, "total_count": 0, "answers": []}
    existing["total_count"] += 1
    if is_correct:
        existing["correct_count"] += 1
    existing["answers"].append({"quiz_id": req.quizId, "selected": req.selectedOption, "correct": is_correct})
    await redis_client.set(quiz_key, json.dumps(existing), ex=86400)

    # 6/25: 퀴즈 제출 결과 DB 테이블 기록 추가
    try:
        question_text = target_quiz.get("question") or target_quiz.get("statement") or ""
        correct_opt = "O" if target_quiz["answer"] else "X"
        new_result = QuizResult(
            session_id=session_id,
            quiz_id=req.quizId,
            question=question_text,
            selected_option=req.selectedOption,
            correct_option=correct_opt,
            is_correct=is_correct
        )
        db.add(new_result)
        await db.commit()
        
        # 퀴즈 제출 시 사용자 대시보드 데이터 캐시 무효화
        try:
            res = await db.execute(select(ReadingSession).filter(ReadingSession.id == session_id))
            sess = res.scalars().first()
            if sess:
                await redis_client.delete(f"user:{sess.user_id}:growth_report_cache")
        except Exception as cache_err:
            print(f"Failed to clear cache on quiz submit: {cache_err}")
    except Exception as _db_err:
        await db.rollback()
        import logging
        logging.warning(f"Failed to save QuizResult row: {_db_err}")

    return QuizSubmitResponse(
        correct=is_correct,
        explanation=target_quiz.get("explanation", ""),
        focusRecovered=focus_recovered,
        xpEarned=xp_earned,
    )


@router.post("/{session_id}/finish", response_model=SessionFinishResponse)
async def finish_session(
    session_id: str, 
    req: SessionFinishRequest, 
    db: AsyncSession = Depends(get_db),
):
    redis_client = await get_redis()
    
    try:
        # 1. DB에서 세션 조회
        result = await db.execute(select(ReadingSession).filter(ReadingSession.id == session_id))
        session = result.scalars().first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
            
        # 2. Redis에서 이벤트 가져오기
        redis_key = f"session:{session_id}:events"
        all_events_raw = await redis_client.lrange(redis_key, 0, -1)
        
        saved_count = 0
        state_events = []
        for raw_event in all_events_raw:
            event_dict = json.loads(raw_event)
            new_event = ReadingEvent(
                session_id=session_id,
                event_type=event_dict.get("type", "unknown"),
                timestamp_ms=event_dict.get("timestamp_ms", 0),
                metadata_json=event_dict
            )
            db.add(new_event)
            saved_count += 1
            
            state_events.append({
                "type": event_dict.get("type", "unknown"),
                "timestamp_ms": event_dict.get("timestamp_ms", 0),
                "position": event_dict.get("position"),
                "duration_ms": event_dict.get("duration_ms"),
                "metadata": event_dict
            })
            
        # 3. 오케스트레이터(Role 1) 파이프라인 실행
        initial_state = create_initial_state(
            session_id=session_id,
            user_id=session.user_id,
            document_id=session.document_id,
            raw_text="Sample Document Text"
        )
        initial_state["reading_events"] = state_events
        final_state = run_reading_session(initial_state)

        # 4. 세션 정보 업데이트
        session.literacy_score = final_state.get("literacy_score", req.literacy_score)
        session.comprehension_score = final_state.get("score_breakdown", {}).get("comprehension_score", req.comprehension_score)
        session.engagement_score = final_state.get("score_breakdown", {}).get("engagement_score", req.engagement_score)
        
        # 4-0. 독해 세션 시간(duration_seconds) 및 종료 시각 계산 후 저장
        try:
            duration_sec = 0
            if state_events:
                sorted_events = sorted(state_events, key=lambda e: e.get("timestamp_ms", 0))
                if len(sorted_events) >= 2:
                    start_ts = sorted_events[0].get("timestamp_ms", 0)
                    end_ts = sorted_events[-1].get("timestamp_ms", 0)
                    duration_sec = max(0, int((end_ts - start_ts) / 1000.0))
            
            # Fallback: 만약 이벤트 기록이 없거나 0초 이하인 경우 세션 생성 시각과 완료 시각의 차이로 계산
            if duration_sec <= 0 and session.created_at:
                from datetime import timezone
                now_utc = datetime.now(timezone.utc)
                sess_created = session.created_at
                if sess_created.tzinfo is None:
                    sess_created = sess_created.replace(tzinfo=timezone.utc)
                duration_sec = max(0, int((now_utc - sess_created).total_seconds()))
                
            session.duration_seconds = duration_sec
            session.finished_at = datetime.now(timezone.utc)
        except Exception as _dur_err:
            print(f"Failed to calculate session duration on finish: {_dur_err}")
            
        # 4-1. 퀴즈 정답 결과로 총 획득 XP 산출 후 저장
        try:
            quiz_results_res = await db.execute(
                select(QuizResult).filter(QuizResult.session_id == session_id)
            )
            q_results = quiz_results_res.scalars().all()
            correct_count = sum(1 for qr in q_results if qr.is_correct)
            session.xp_earned = correct_count * 10
        except Exception as _xp_err:
            session.xp_earned = 0
            print(f"Failed to calculate session XP on finish: {_xp_err}")
            
        await db.commit()
        await redis_client.delete(redis_key)
        
        # 4-2. 사용자 성장 보고서 캐시 무효화
        try:
            await redis_client.delete(f"user:{session.user_id}:growth_report_cache")
        except Exception as cache_err:
            print(f"Failed to clear cache on finish_session: {cache_err}")
        
        return SessionFinishResponse(
            session_id=session_id, 
            message="Session finished and flushed to PostgreSQL.",
            saved_events_count=saved_count
        )
    except Exception as e:
        import logging
        logging.error(f"Error in finish_session: {e}")
        raise

@router.get("/{session_id}/result")
async def get_session_result(session_id: str, db: AsyncSession = Depends(get_db)):
    redis_client = await get_redis()
    try:
        # DB 세션 조회
        result = await db.execute(select(ReadingSession).filter(ReadingSession.id == session_id))
        session = result.scalars().first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Redis에서 먼저 가져오기 (M4 fallback)
        redis_key = f"session:{session_id}:events"
        all_events_raw = await redis_client.lrange(redis_key, 0, -1)
        
        state_events = []
        if all_events_raw:
            for raw in all_events_raw:
                data = json.loads(raw)
                state_events.append({
                    "type": data["type"],
                    "timestamp_ms": data["timestamp_ms"],
                    "position": data.get("position"),
                    "duration_ms": data.get("duration_ms"),
                    "metadata": data
                })
                db.add(ReadingEvent(
                    session_id=session_id,
                    event_type=data["type"],
                    timestamp_ms=data["timestamp_ms"],
                    metadata_json=data
                ))
            # Redis에 있던 걸 DB에 넣었으니 Flush 처리
            await db.commit()
            await redis_client.delete(redis_key)
        else:
            # Redis에 없으면 DB에서 조회
            events_result = await db.execute(select(ReadingEvent).filter(ReadingEvent.session_id == session_id))
            events = events_result.scalars().all()
            for ev in events:
                state_events.append({
                    "type": ev.event_type,
                    "timestamp_ms": ev.timestamp_ms,
                    "position": ev.metadata_json.get("position"),
                    "duration_ms": ev.metadata_json.get("duration_ms"),
                    "metadata": ev.metadata_json
                })

        initial_state = create_initial_state(
            session_id=session_id,
            user_id=session.user_id,
            document_id=session.document_id,
            raw_text=""
        )
        initial_state["reading_events"] = state_events

        # 글 난이도/이독성 복원(/start에서 보관) → 도전력 도메인·글 프로필이 실제 글 기준으로 계산됨.
        textmeta_raw = await redis_client.get(f"session:{session_id}:textmeta")
        if textmeta_raw:
            try:
                tm = json.loads(textmeta_raw)
                initial_state["difficulty_score"] = tm.get("difficulty_score", 50.0)
                initial_state["readability_score"] = tm.get("readability_score", 50.0)
            except Exception:
                pass

        # Q1/Q2: Redis에서 실제 퀴즈 채점 결과 읽기 (stub 제거)
        quiz_key = f"session:{session_id}:quiz_result"
        quiz_raw = await redis_client.get(quiz_key)
        if quiz_raw:
            quiz_data = json.loads(quiz_raw)
            initial_state["quiz_result"] = {
                "correct_count": quiz_data.get("correct_count", 0),
                "total_count":   quiz_data.get("total_count", 0),
                "answers":       quiz_data.get("answers", [])
            }
        else:
            # 퀴즈를 아예 안 풀었을 때 기본값 (점수 반영 안 됨)
            initial_state["quiz_result"] = {"correct_count": 0, "total_count": 0}

        # [C2/M1] QA 입력 복원 — /start에서 Redis에 보관한 실제 chunks(원문/요약)·quizzes(진술문)를
        # state로 되살려 웹 경로에서도 faithfulness/relevance가 실측되게 한다.
        # (복원 안 하면 raw_text=""·chunks 부재로 QA가 항상 0으로 나옴)
        # ※ 반드시 run_reading_session 전에 평가 — 이후 content_reducer가 chunks를 스텁으로 덮어씀.
        chunks_raw = await redis_client.get(f"session:{session_id}:chunks")
        if chunks_raw:
            try:
                initial_state["chunks"] = json.loads(chunks_raw)
            except Exception:
                pass
        quizzes_raw = await redis_client.get(f"session:{session_id}:quizzes")
        if quizzes_raw:
            try:
                initial_state["quizzes"] = json.loads(quizzes_raw)
            except Exception:
                pass

        # Q4: 5번 QA 품질 게이트 (실패해도 세션 유지)
        try:
            from backend.evaluation.evaluation_pipeline import run_evaluation_from_state
            initial_state["qa_evaluation"] = run_evaluation_from_state(initial_state)
        except Exception as _qa_err:
            # state의 errors는 list 규약이므로 append로 기록(과거 dict 인덱싱은 TypeError 유발)
            initial_state.setdefault("errors", []).append({"step": "qa_evaluation", "error": str(_qa_err)})

        final_state = run_reading_session(initial_state)

        # [C3] DB에 세션 결과 저장
        session.literacy_score = final_state.get("literacy_score", 50.0)
        score_breakdown = final_state.get("score_breakdown", {})
        session.comprehension_score = score_breakdown.get("comprehension_score", 50.0)
        session.engagement_score = score_breakdown.get("engagement_score", 50.0)
        # 이독성 + 문해 5대 지표 저장(대시보드 레이더의 실데이터 소스)
        session.readability_score = score_breakdown.get("readability_score", 50.0)
        session.literacy_domains = final_state.get("literacy_domains") or score_breakdown.get("literacy_domains")

        # duration_seconds 계산 (첫 이벤트와 마지막 이벤트의 timestamp 차이)
        if state_events:
            start_ts = state_events[0].get("timestamp_ms", 0)
            end_ts = state_events[-1].get("timestamp_ms", start_ts)
            session.duration_seconds = max(0, int((end_ts - start_ts) / 1000.0))
        else:
            session.duration_seconds = 0
            
        session.xp_earned = sum(ans.get("correct", False) * 10 for ans in initial_state.get("quiz_result", {}).get("answers", []))

        # ── 개인화 baseline rolling 갱신(EWMA) ──
        # 이번 세션에서 "정상 읽기"로 스크롤한 속도(스키밍/0 제외)의 중앙값을 관측치로,
        # 이 글 난이도에 가까운 캘리브레이션 점(easy/hard)을 EWMA로 당긴다 → 읽을수록 정교.
        try:
            user_result = await db.execute(select(User).filter(User.id == session.user_id))
            user = user_result.scalars().first()
            _update_user_scroll_baseline(user, state_events, initial_state.get("difficulty_score", 50.0))
        except Exception as _bl_err:
            logging_import = __import__("logging"); logging_import.warning(f"baseline update skip: {_bl_err}")

        await db.commit()

        return to_session_result(final_state)
    except Exception as e:
        import logging
        logging.error(f"Error in get_session_result: {e}")
        raise

@router.post("/{session_id}/explain", response_model=TermExplainResponse)
async def explain_term(
    session_id: str,
    req: TermExplainRequest,
    db: AsyncSession = Depends(get_db),
):
    """용어 설명 API - 실시간 RAG 엔진(우리말샘 API + LLM 유추) 연동 완료."""
    # 세션 존재 확인
    result = await db.execute(select(ReadingSession).filter(ReadingSession.id == session_id))
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    term = req.term.strip()
    
    from ..agents.content_reducer.rag_engine import lookup_term
    try:
        t = lookup_term(term, req.context)
        explanation = t["definition"]
        source = t["source"]
        
        # 단어 뜻 조회 실패 시, 디버깅을 위해 에러 내역 및 시도 항목 상세 리턴
        if source == "not_found":
            meta = t.get("_meta", {})
            tried_str = ", ".join(meta.get("tried", []))
            errors_str = ", ".join([f"{k}: {v}" for k, v in meta.get("errors", {}).items()])
            explanation = f"뜻을 분석하지 못했습니다.\n[시도된 항목]: {tried_str}\n[에러 로그]: {errors_str or '없음'}"
            source = "Debug Info"
    except Exception as e:
        explanation = f"'{term}'에 대한 사전 뜻을 찾을 수 없습니다. ({str(e)})"
        source = "Local Fallback"

    # 실시간 단어장 연동을 위해 lookup 이벤트 캐시에 기록 (세션 종료 시 DB 저장)
    try:
        import time
        redis_client = await get_redis()
        lookup_ev = {
            "type": "lookup",
            "timestamp_ms": int(time.time() * 1000),
            "term": term,
            "definition": explanation,
            "source": source
        }
        await redis_client.rpush(f"session:{session_id}:events", json.dumps(lookup_ev))
    except Exception as _ev_err:
        pass

    return TermExplainResponse(
        explanation=explanation,
        definition=explanation,
        source=source
    )

@router.post("/reset")
async def reset_demo_data(db: AsyncSession = Depends(get_db)):
    """전체 데이터베이스 및 Redis 세션 데이터를 완전 초기화하여 시연 리허설 반복 실행을 보장함 (7/13, 7/14)"""
    from ..core.db import engine
    from ..models.models import Base
    
    redis_client = await get_redis()
    
    try:
        # DB 모든 테이블을 Drop 후 Recreate하여 스키마 변경 사항(readability_score 등)을 강제 적용
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        
        # 2. Redis 세션 캐시 버퍼 제거
        # Redis 내의 모든 키를 탐색하여 삭제
        # InMemoryRedisClient의 경우 store를 직접 비워줌
        if hasattr(redis_client, "store"):
            redis_client.store.clear()
        else:
            # 실제 Redis일 경우 keys 조회 및 삭제
            keys = await redis_client.keys("session:*:events")
            for k in keys:
                await redis_client.delete(k)
                
        print("[Reset] Database and Redis cache successfully cleared for demo rehearsal.")
        return {"status": "success", "message": "Demo data successfully reset."}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database reset failed: {str(e)}")
    finally:
        await redis_client.aclose()
