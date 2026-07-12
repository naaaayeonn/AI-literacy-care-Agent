import json
import asyncio
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..core.db import get_db
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
    sessions_result = await db.execute(select(ReadingSession).filter(ReadingSession.user_id == user_id))
    sessions = sessions_result.scalars().all()
    
    # Basic fallbacks if no sessions exist
    if not sessions:
        return generate_empty_growth_report()

    total_xp = sum((s.xp_earned or 0) for s in sessions)
    total_duration = sum((s.duration_seconds or 0) for s in sessions)
    total_duration_mins = total_duration // 60

    # M2: 요일별 실제 데이터 집계 (요일 순으로 정렬)
    weekday_names = ["월", "화", "수", "목", "금", "토", "일"]
    weekly_activity = {name: {"time": 0, "xp": 0} for name in weekday_names}
    
    for s in sessions:
        if s.created_at:
            day_idx = s.created_at.weekday()  # 월요일=0, 일요일=6
            day_name = weekday_names[day_idx]
            weekly_activity[day_name]["time"] += (s.duration_seconds or 0) // 60
            weekly_activity[day_name]["xp"] += (s.xp_earned or 0)
            
    activity_data_weekly = [
        {"label": name, "time": data["time"], "xp": data["xp"]}
        for name, data in weekly_activity.items()
    ]

    # M1: 5대 지표 실측 신호 기반 정직한 파생
    sorted_sessions = sorted(sessions, key=lambda s: s.created_at if s.created_at else datetime.min.replace(tzinfo=timezone.utc))
    first_session = sorted_sessions[0]
    
    # 첫 세션 (케어 전 baseline)
    before_eng = first_session.engagement_score or 50.0
    before_comp = first_session.comprehension_score or 50.0
    before_lit = first_session.literacy_score or 50.0
    
    # 전체 세션 평균 (케어 적용 후)
    after_eng = sum((s.engagement_score or 50.0) for s in sessions) / len(sessions)
    after_comp = sum((s.comprehension_score or 50.0) for s in sessions) / len(sessions)
    after_lit = sum((s.literacy_score or 50.0) for s in sessions) / len(sessions)

    # 문해 5대 지표(v2): 저장된 literacy_domains 실측 평균. before=첫 세션, after=전체 평균.
    # (어휘력/추론능력 등 가짜 +offset 매핑 폐기 → 우리가 실제 측정하는 신호로 정직하게 파생)
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

    # M6: 어휘 보드 실데이터 연동 (가장 최근 세션의 cached chunks에서 어휘 추출)
    latest_session = sorted_sessions[-1]
    words_data = []
    
    redis_client = await get_redis()
    try:
        chunks_raw = await redis_client.get(f"session:{latest_session.id}:chunks")
        if chunks_raw:
            chunks = json.loads(chunks_raw)
            seen_words = set()
            for c in chunks:
                for t in c.get("terms", []):
                    word = t.get("term")
                    if word and word not in seen_words:
                        seen_words.add(word)
                        words_data.append({
                            "word": word,
                            "meaning": t.get("definition", "어휘 설명이 없습니다."),
                            "level": "상" if len(word) > 3 else "중",
                            "status": "review"
                        })
    except Exception as e:
        print(f"Failed to fetch real vocab terms from Redis: {e}")
    finally:
        await redis_client.aclose()
        
    # 만약 Redis 캐시에 어휘가 없다면 기존 하드코딩 데이터로 깔끔하게 폴백
    if not words_data:
        words_data = [
            {"word": '인공지능전환 (AX)', "meaning": 'AI 기술을 도입해 기존의 비즈니스 구조를 근본적으로 바꾸는 과정.', "level": '상', "status": 'completed'},
            {"word": '카나리아 (Canary)', "meaning": '탄광의 낙반 위험을 미리 알려주는 조기 경보 체계를 의미함.', "level": '중', "status": 'review'},
        ]
    else:
        words_data = words_data[:4]  # 최대 4개 제한

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

    report = {
        "weekly": {
            "radarData": radar_data,
            "activityData": activity_data_weekly,
            "words": words_data,
            "prescription": prescription_html
        },
        "monthly": {
            "radarData": radar_data,
            "activityData": activity_data_weekly,
            "words": words_data,
            "prescription": prescription_html
        }
    }
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
            "prescription": ["학습 데이터가 부족합니다. 먼저 글을 읽고 세션을 완료해주세요!"]
        },
        "monthly": {
            "radarData": [],
            "activityData": [],
            "words": [],
            "prescription": ["학습 데이터가 부족합니다."]
        }
    }
