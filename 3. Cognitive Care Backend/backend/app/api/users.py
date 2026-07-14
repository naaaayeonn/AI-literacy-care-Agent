import json
import asyncio
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..core.db import get_db
from ..core.redis import get_redis
from ..models.models import ReadingSession, ReadingEvent, User, QuizResult
from ..agents.content_reducer.snowchat_client import is_snowchat_available, _call_llm_via_snowchat

router = APIRouter(prefix="/api/user", tags=["User Data Management"])

@router.delete("/{user_id}/data")
async def delete_user_data(user_id: str, db: AsyncSession = Depends(get_db)):
    """
    ADR-002: 익명 사용자 데이터 파기 요청 (세션 및 이벤트 일괄 삭제)
    """
    user_result = await db.execute(select(User).filter(User.id == user_id))
    user = user_result.scalars().first()
    
    if not user:
        return {"status": "success", "message": f"User {user_id} not found or already deleted."}
        
    # 세션 조회
    sessions_result = await db.execute(select(ReadingSession).filter(ReadingSession.user_id == user_id))
    sessions = sessions_result.scalars().all()
    session_ids = [s.id for s in sessions]
    
    # 해당 세션의 모든 이벤트 삭제
    if session_ids:
        for sid in session_ids:
            events_result = await db.execute(select(ReadingEvent).filter(ReadingEvent.session_id == sid))
            events = events_result.scalars().all()
            for ev in events:
                await db.delete(ev)
            
        for s in sessions:
            await db.delete(s)
            
    await db.delete(user)
    await db.commit()
    
    return {"status": "success", "message": f"Data for user {user_id} deleted successfully."}


@router.get("/{user_id}/growth")
async def get_user_growth(user_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns the user's detailed growth report data (weekly/monthly).
    Dynamically generated from ReadingSessions and LLM.
    """
    redis_client = await get_redis()
    # 7/14: 개발 및 데모의 실시간 반영을 위해 캐시 비활성화
    # cache_key = f"user:{user_id}:growth_report_cache"
    # try:
    #     cached_raw = await redis_client.get(cache_key)
    #     if cached_raw:
    #         data = json.loads(cached_raw)
    #         await redis_client.aclose()
    #         return data
    # except Exception as cache_err:
    #     print(f"Cache lookup failed: {cache_err}")

    sessions_result = await db.execute(select(ReadingSession).filter(ReadingSession.user_id == user_id))
    sessions = sessions_result.scalars().all()
    
    # Basic fallbacks if no sessions exist
    if not sessions:
        await redis_client.aclose()
        return generate_empty_growth_report()
        
    # 모든 세션의 퀴즈 정답 수 실시간 조회 (진행 중인 활성 세션의 점수 유실 방지)
    quiz_correct_counts = {}
    try:
        q_results = (await db.execute(
            select(QuizResult).filter(
                QuizResult.session_id.in_([s.id for s in sessions]),
                QuizResult.is_correct == True
            )
        )).scalars().all()
        for qr in q_results:
            quiz_correct_counts[qr.session_id] = quiz_correct_counts.get(qr.session_id, 0) + 1
    except Exception as e:
        print(f"Failed to query quiz results: {e}")
    
    # 1. 독해 시간 동적 산출 (활성 세션의 경우 Redis의 실시간 이벤트 간 시간 차이로 계산)
    total_xp = sum(quiz_correct_counts.get(s.id, 0) * 10 for s in sessions)
    total_duration = 0
    for s in sessions:
        if s.duration_seconds:
            total_duration += s.duration_seconds
        else:
            try:
                redis_key = f"session:{s.id}:events"
                all_events_raw = await redis_client.lrange(redis_key, 0, -1)
                if all_events_raw:
                    events = [json.loads(raw) for raw in all_events_raw]
                    start_ts = events[0].get("timestamp_ms", 0)
                    end_ts = events[-1].get("timestamp_ms", start_ts)
                    total_duration += max(0, int((end_ts - start_ts) / 1000.0))
            except Exception:
                pass
    total_duration_mins = total_duration // 60

    # M2: 요일별 실제 데이터 집계 (요일 순으로 정렬)
    weekday_names = ["월", "화", "수", "목", "금", "토", "일"]
    weekly_activity = {name: {"time": 0, "xp": 0} for name in weekday_names}
    
    for s in sessions:
        if s.created_at:
            day_idx = s.created_at.weekday()  # 월요일=0, 일요일=6
            day_name = weekday_names[day_idx]
            
            # 요일별 독해 시간도 활성 세션 보정치 사용
            duration_sec = s.duration_seconds
            if not duration_sec:
                try:
                    redis_key = f"session:{s.id}:events"
                    all_events_raw = await redis_client.lrange(redis_key, 0, -1)
                    if all_events_raw:
                        events = [json.loads(raw) for raw in all_events_raw]
                        start_ts = events[0].get("timestamp_ms", 0)
                        end_ts = events[-1].get("timestamp_ms", start_ts)
                        duration_sec = max(0, int((end_ts - start_ts) / 1000.0))
                except Exception:
                    pass
            
            weekly_activity[day_name]["time"] += (duration_sec or 0) // 60
            weekly_activity[day_name]["xp"] += quiz_correct_counts.get(s.id, 0) * 10
            
    activity_data_weekly = [
        {"label": name, "time": data["time"], "xp": data["xp"]}
        for name, data in weekly_activity.items()
    ]

    # M1: 5대 지표 실측 신호 기반 정직한 파생
    sorted_sessions = sorted(sessions, key=lambda s: s.created_at if s.created_at else datetime.min.replace(tzinfo=timezone.utc))
    first_session = sorted_sessions[0]
    
    # 실제 활동(퀴즈 풀이 결과가 존재하거나, DB 이벤트가 있거나, Redis 실시간 이벤트가 존재하거나, 점수가 있거나 완독됨)
    session_ids_with_quizzes = set((await db.execute(select(QuizResult.session_id).distinct())).scalars().all())
    session_ids_with_events = set((await db.execute(select(ReadingEvent.session_id).distinct())).scalars().all())
    
    latest_sess = sorted_sessions[-1]
    has_redis_events = False
    try:
        has_redis_events = await redis_client.exists(f"session:{latest_sess.id}:events") > 0
    except Exception:
        pass
        
    active_sessions = []
    for s in sorted_sessions:
        is_active = (
            (s.id == latest_sess.id and has_redis_events) or
            (s.id in session_ids_with_quizzes) or
            (s.id in session_ids_with_events) or
            (s.literacy_score and s.literacy_score > 0) or
            (s.xp_earned and s.xp_earned > 0) or
            (s.finished_at is not None)
        )
        if is_active:
            active_sessions.append(s)
            
    if not active_sessions:
        active_sessions = sorted_sessions
    latest_active_session = active_sessions[-1]
    
    # 첫 세션 (케어 전 baseline)
    before_eng = first_session.engagement_score or 50.0
    before_comp = first_session.comprehension_score or 50.0
    before_lit = first_session.literacy_score or 50.0
    
    # 전체 세션 평균 (케어 적용 후)
    after_eng = sum((s.engagement_score or 50.0) for s in sessions) / len(sessions)
    after_comp = sum((s.comprehension_score or 50.0) for s in sessions) / len(sessions)
    after_lit = sum((s.literacy_score or 50.0) for s in sessions) / len(sessions)

    # 문해 5대 지표(v2): 저장된 literacy_domains 실측 평균. before=첫 세션, after=전체 평균.
    DOMAIN_LABELS = [
        ("comprehension", "이해도"),
        ("focus", "집중 유지"),
        ("closeReading", "정독 충실도"),
        ("challenge", "난이도 도전력"),
        ("stability", "읽기 안정성"),
    ]
    dsessions = [s for s in sorted_sessions if isinstance(s.literacy_domains, dict) and s.literacy_domains]

    def _dom(sess, key: str) -> float:
        return float((sess.literacy_domains or {}).get(key, 0) or 0)

    radar_data = []
    for key, label in DOMAIN_LABELS:
        if dsessions:
            after = round(sum(_dom(s, key) for s in dsessions) / len(dsessions), 1)
            before = round(_dom(dsessions[0], key), 1)
        else:
            after = before = 0.0
        radar_data.append({"subject": label, "before": before, "after": after})

    # M6: 어휘 보드 실데이터 연동 (사용자가 실제로 explain으로 조회한 단어들)
    words_data = []
    seen_words = set()
    
    # DB 및 Redis에서 실제로 찾아본 용어들 조회
    try:
        session_ids = [s.id for s in sessions]
        if session_ids:
            # 1. DB의 ReadingEvent lookup 이벤트들 조회
            lookup_events_result = await db.execute(
                select(ReadingEvent).filter(
                    ReadingEvent.session_id.in_(session_ids),
                    ReadingEvent.event_type == "lookup"
                ).order_by(ReadingEvent.id.desc())
            )
            lookup_events = lookup_events_result.scalars().all()
            for ev in lookup_events:
                meta = ev.metadata_json or {}
                word = meta.get("term") or meta.get("word")
                if word and word not in seen_words:
                    seen_words.add(word)
                    words_data.append({
                        "word": word,
                        "meaning": meta.get("definition") or meta.get("meaning") or "어휘 설명이 없습니다.",
                        "level": "상" if len(word) > 3 else "중",
                        "status": meta.get("status") or "review"
                    })
        
        # 2. 가장 최근 세션이 활성화 상태인 경우 Redis 버퍼에서 실시간 lookup 이벤트 추가 조회
        latest_session = latest_active_session
        active_events_raw = await redis_client.lrange(f"session:{latest_session.id}:events", 0, -1)
        for raw in active_events_raw:
            evt = json.loads(raw)
            if evt.get("type") == "lookup":
                word = evt.get("term")
                if word and word not in seen_words:
                    seen_words.add(word)
                    words_data.append({
                        "word": word,
                        "meaning": evt.get("definition") or "어휘 설명이 없습니다.",
                        "level": "상" if len(word) > 3 else "중",
                        "status": evt.get("status") or "review"
                    })
    except Exception as e:
        print(f"Failed to fetch real lookup terms: {e}")
        
    # 만약 실제로 찾아본 어휘가 없다면 기존 하드코딩 데이터로 깔끔하게 폴백
    if not words_data:
        words_data = [
            {"word": '인공지능전환 (AX)', "meaning": 'AI 기술을 도입해 기존의 비즈니스 구조를 근본적으로 바꾸는 과정.', "level": '상', "status": 'completed'},
            {"word": '카나리아 (Canary)', "meaning": '탄광의 낙반 위험을 미리 알려주는 조기 경보 체계를 의미함.', "level": '중', "status": 'review'},
        ]

    # 배지 동적 연동 계산
    badges_data = []
    total_sessions = len(sessions)
    if total_sessions >= 1:
        badges_data.append({
            "id": "first-read",
            "name": "첫 완독",
            "emoji": "📖",
            "description": "첫 번째 글을 끝까지 읽었어요!",
            "acquiredAt": sorted_sessions[0].created_at.isoformat() if sorted_sessions[0].created_at else datetime.now(timezone.utc).isoformat()
        })
    
    # 초집중 리더: 평균 집중도 90% 이상 혹은 단일 세션 90% 이상
    focus_master_sess = next((s for s in sorted_sessions if (s.engagement_score or 0) >= 90), None)
    if focus_master_sess:
        badges_data.append({
            "id": "focus-master",
            "name": "초집중 리더",
            "emoji": "🧘",
            "description": "평균 집중도 90% 이상 달성!",
            "acquiredAt": focus_master_sess.created_at.isoformat() if focus_master_sess.created_at else datetime.now(timezone.utc).isoformat()
        })
        
    # 어휘 마스터: 용어 툴팁 10번 이상 확인
    if len(seen_words) >= 10:
        # 10번째 lookup 이벤트 시간 구하기
        acq_time = datetime.now(timezone.utc).isoformat()
        try:
            if session_ids:
                lookup_events_result = await db.execute(
                    select(ReadingEvent).filter(
                        ReadingEvent.session_id.in_(session_ids),
                        ReadingEvent.event_type == "lookup"
                    ).order_by(ReadingEvent.id.asc())
                )
                l_evs = lookup_events_result.scalars().all()
                if len(l_evs) >= 10 and l_evs[9].created_at:
                    acq_time = l_evs[9].created_at.isoformat()
        except Exception:
            pass
            
        badges_data.append({
            "id": "vocab-master",
            "name": "어휘 마스터",
            "emoji": "🎯",
            "description": "용어 툴팁을 10번 이상 확인했어요!",
            "acquiredAt": acq_time
        })
        
    # 3일 연속 읽기 세션 완료
    dates = sorted(list({s.created_at.date() for s in sessions if s.created_at}))
    has_streak = False
    streak_date = None
    if len(dates) >= 3:
        for idx in range(len(dates) - 2):
            if (dates[idx+1] - dates[idx]).days == 1 and (dates[idx+2] - dates[idx+1]).days == 1:
                has_streak = True
                streak_date = dates[idx+2]
                break
    if has_streak:
        badges_data.append({
            "id": "streak-3",
            "name": "3일 연속",
            "emoji": "🔥",
            "description": "3일 연속 읽기 세션 완료!",
            "acquiredAt": datetime.combine(streak_date, datetime.min.time(), tzinfo=timezone.utc).isoformat() if streak_date else datetime.now(timezone.utc).isoformat()
        })
        
    # 만점왕: 리터러시 점수 95점 이상
    high_score_sess = next((s for s in sorted_sessions if (s.literacy_score or 0) >= 95), None)
    if high_score_sess:
        badges_data.append({
            "id": "high-score",
            "name": "만점왕",
            "emoji": "🏆",
            "description": "리터러시 점수 95점 이상 달성!",
            "acquiredAt": high_score_sess.created_at.isoformat() if high_score_sess.created_at else datetime.now(timezone.utc).isoformat()
        })

    # 최근 활성/완료 세션 요약 지표 빌드
    latest_session_summary = {
        "quiz_count": 0,
        "comprehension_score": 50,
        "progress": 0,
        "quiz_accuracy": 50
    }
    if sessions:
        try:
            latest_session = latest_active_session
            
            # 1. 퀴즈 제출 개수 및 정답률 집계
            quiz_results_result = await db.execute(
                select(QuizResult).filter(QuizResult.session_id == latest_session.id)
            )
            q_res = quiz_results_result.scalars().all()
            q_count = len(q_res)
            correct_q_count = sum(1 for qr in q_res if qr.is_correct)
            q_acc = int((correct_q_count / q_count * 100)) if q_count > 0 else 50
            
            # 2. 진행률 집계 (Redis 또는 DB 이벤트)
            progress_val = 0
            redis_key = f"session:{latest_session.id}:events"
            all_events_raw = await redis_client.lrange(redis_key, 0, -1)
            
            events_list = []
            if all_events_raw:
                events_list = [json.loads(raw) for raw in all_events_raw]
            else:
                db_evs = await db.execute(select(ReadingEvent).filter(ReadingEvent.session_id == latest_session.id))
                events_list = [ev.metadata_json for ev in db_evs.scalars().all() if ev.metadata_json]
                
            progress_events = [e for e in events_list if e.get("type") == "progress"]
            scroll_events = [e for e in events_list if e.get("type") == "scroll"]
            if progress_events:
                progress_val = progress_events[-1].get("progress", 0)
            elif scroll_events:
                max_pos = max((e.get("position") or 0.0) for e in scroll_events)
                progress_val = int(max_pos * 100)
            else:
                read_indices = {e.get("chunk_idx") for e in events_list if e.get("type") == "read" and e.get("chunk_idx") is not None}
                chunks_raw = await redis_client.get(f"session:{latest_session.id}:chunks")
                chunks_len = len(json.loads(chunks_raw)) if chunks_raw else 1
                if read_indices and chunks_len:
                    progress_val = int((len(read_indices) / chunks_len) * 100)
                    
            latest_session_summary = {
                "quiz_count": q_count,
                "comprehension_score": int(latest_session.comprehension_score or 50),
                "progress": min(100, progress_val),
                "quiz_accuracy": q_acc
            }
        except Exception as _sum_err:
            print(f"Failed to compile latest session summary: {_sum_err}")

    # Generate Prescription via LLM
    prescription_html = [
        f"학습자의 이번 주 총 집중 독해 시간은 <strong class=\"text-[var(--color-primary)]\">{total_duration_mins}분</strong>이며, 총 <strong>{total_xp} XP</strong>를 획득했습니다.",
        "기본적인 데이터 집계가 완료되었습니다."
    ]

    if is_snowchat_available():
        try:
            prompt = f"""
            사용자의 독해 학습 데이터:
            - 총 독해 시간: {total_duration_mins}분
            - 총 획득 XP: {total_xp}
            - 평균 집중도: {after_eng:.1f}점
            - 평균 이해도: {after_comp:.1f}점
            - 찾아본 단어 수: {len(words_data)}개

            위 데이터를 바탕으로 사용자에게 '주간 성장 처방전'을 작성해주세요.
            반드시 3개의 단락으로 작성하고, HTML 태그(<strong>, <strong class="text-[var(--color-primary)]"> 등)를 적절히 사용해 강조해주세요.
            마지막 단락은 "💡 성장 챌린지:" 로 시작하며 다음 주 목표를 제안해주세요.
            응답은 JSON 배열 형식의 문자열로 반환해주세요. 예: ["단락1", "단락2", "단락3"]
            """
            llm_response = _call_llm_via_snowchat(
                model="gemini-2.5-flash",
                prompt=prompt,
                system_instruction="당신은 AI 리터러시 코치입니다. 사용자를 격려하고 전문적인 분석을 제공하세요. JSON 배열로만 응답하세요."
            )
            # 파싱 시도
            try:
                import re
                clean_json = llm_response.replace("\n", " ")
                match = re.search(r'\[.*\]', clean_json)
                if match:
                    parsed = json.loads(match.group(0))
                    if isinstance(parsed, list) and len(parsed) > 0:
                        prescription_html = parsed
            except Exception as e:
                print(f"Failed to parse LLM prescription: {e}")
        except Exception as e:
            print(f"LLM call failed: {e}")

    # M1-2. 주간 리터러시 점수 추이 (주간 비교 차트용)
    weekly_score_series = []
    if sessions:
        for idx, day_name in enumerate(weekday_names):
            day_sessions = [s for s in sessions if s.created_at and s.created_at.weekday() == idx]
            active_day_sessions = [s for s in day_sessions if s.id != first_session.id]
            
            this_week_val = None
            if active_day_sessions:
                this_week_val = round(sum((s.literacy_score or 50.0) for s in active_day_sessions) / len(active_day_sessions), 1)
            elif day_sessions and len(sessions) == 1:
                this_week_val = round(first_session.literacy_score or 50.0, 1)
                
            last_week_val = round(before_lit, 1)
            weekly_score_series.append({
                "label": day_name,
                "thisWeek": this_week_val,
                "lastWeek": last_week_val
            })
    else:
        for day_name in weekday_names:
            weekly_score_series.append({
                "label": day_name,
                "thisWeek": None,
                "lastWeek": None
            })

    report = {
        "weekly": {
            "radarData": radar_data,
            "activityData": activity_data_weekly,
            "words": words_data,
            "prescription": prescription_html,
            "weeklyScoreSeries": weekly_score_series
        },
        "monthly": {
            "radarData": radar_data,
            "activityData": activity_data_weekly,
            "words": words_data,
            "prescription": prescription_html,
            "weeklyScoreSeries": weekly_score_series
        },
        "totalXp": total_xp,
        "level": total_xp // 100 + 1,
        "averageLiteracyScore": round(after_lit, 1),
        "averageFocusScore": round(after_eng, 1),
        "averageComprehensionScore": round(after_comp, 1),
        "latestSessionSummary": latest_session_summary,
        "badges": badges_data
    }

    # Cache the generated report in Redis for 24 hours to prevent slow page reloads
    # try:
    #     await redis_client.set(cache_key, json.dumps(report), ex=86400)
    # except Exception as cache_err:
    #     print(f"Failed to cache growth report: {cache_err}")

    await redis_client.aclose()
    return report

def generate_empty_growth_report():
    return {
        "weekly": {
            "radarData": [
                {"subject": '이해도', "before": 0, "after": 0},
                {"subject": '집중 유지', "before": 0, "after": 0},
                {"subject": '정독 충실도', "before": 0, "after": 0},
                {"subject": '난이도 도전력', "before": 0, "after": 0},
                {"subject": '읽기 안정성', "before": 0, "after": 0},
            ],
            "activityData": [],
            "words": [],
            "prescription": ["학습 데이터가 부족합니다. 먼저 글을 읽고 세션을 완료해주세요!"],
            "badges": []
        },
        "monthly": {
            "radarData": [],
            "activityData": [],
            "words": [],
            "prescription": ["학습 데이터가 부족합니다."],
            "badges": []
        },
        "badges": []
    }

class VocabUpdateRequest(BaseModel):
    word: str
    status: str  # "completed", "review", or "deleted"

@router.post("/{user_id}/vocab/update")
async def update_user_vocab(user_id: str, req: VocabUpdateRequest, db: AsyncSession = Depends(get_db)):
    """
    사용자 단어장의 개별 어휘 상태 변경 또는 삭제
    """
    # 사용자의 모든 세션 ID 조회
    sessions_result = await db.execute(select(ReadingSession).filter(ReadingSession.user_id == user_id))
    sessions = sessions_result.scalars().all()
    session_ids = [s.id for s in sessions]
    
    if not session_ids:
        return {"status": "success"}
        
    # 해당 단어의 lookup 이벤트 조회
    lookup_events_result = await db.execute(
        select(ReadingEvent).filter(
            ReadingEvent.session_id.in_(session_ids),
            ReadingEvent.event_type == "lookup"
        )
    )
    lookup_events = lookup_events_result.scalars().all()
    
    for ev in lookup_events:
        meta = ev.metadata_json or {}
        w = meta.get("term") or meta.get("word")
        if w == req.word:
            if req.status == "deleted":
                await db.delete(ev)
            else:
                meta["status"] = req.status
                ev.metadata_json = meta
                db.add(ev)
                
    await db.commit()

    # Invalidate growth report cache
    try:
        redis_client = await get_redis()
        await redis_client.delete(f"user:{user_id}:growth_report_cache")
        await redis_client.aclose()
    except Exception as cache_err:
        print(f"Failed to clear cache in update_user_vocab: {cache_err}")

    return {"status": "success"}
