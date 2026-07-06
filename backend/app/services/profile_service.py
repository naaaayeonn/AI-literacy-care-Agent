"""리터러시 프로필 서비스 (6/30 구현)

세션 완료 시 호출되어 사용자의 장기 리터러시 프로필을 갱신합니다.
- 누적 세션 수, 평균 점수 업데이트
- 취약점 분석 (퀴즈 정답률 기반)
- 성장 추세 계산 (최근 5세션 vs 이전 5세션)
"""

from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func as sql_func

from ..models.models import LiteracyProfile, ReadingSession, QuizResult


async def update_profile_on_session_complete(
    db: AsyncSession,
    user_id: str,
    session_literacy_score: float,
    session_comprehension: float,
    session_engagement: float,
    xp_earned: int,
) -> dict:
    """세션 완료 후 프로필 갱신. 프로필이 없으면 생성."""

    # 기존 프로필 조회 또는 생성
    result = await db.execute(
        select(LiteracyProfile).filter(LiteracyProfile.user_id == user_id)
    )
    profile = result.scalars().first()

    if not profile:
        profile = LiteracyProfile(
            user_id=user_id,
            total_sessions=0,
            avg_literacy_score=0.0,
            avg_comprehension=0.0,
            avg_engagement=0.0,
            total_xp=0,
            current_level=1,
        )
        db.add(profile)

    # 누적 평균 갱신 (incremental average)
    n = profile.total_sessions
    profile.total_sessions = n + 1
    profile.avg_literacy_score = (profile.avg_literacy_score * n + session_literacy_score) / (n + 1)
    profile.avg_comprehension = (profile.avg_comprehension * n + session_comprehension) / (n + 1)
    profile.avg_engagement = (profile.avg_engagement * n + session_engagement) / (n + 1)
    profile.total_xp = (profile.total_xp or 0) + xp_earned

    # 레벨 갱신
    from .reward_service import get_level_for_xp
    profile.current_level = get_level_for_xp(profile.total_xp)

    # 추세 계산 (간소화: 현재 점수 vs 평균)
    if session_literacy_score > profile.avg_literacy_score + 3:
        profile.trend = "improving"
    elif session_literacy_score < profile.avg_literacy_score - 3:
        profile.trend = "declining"
    else:
        profile.trend = "stable"

    # 취약점 분석 (간소화)
    weaknesses = {}
    if session_comprehension < 60:
        weaknesses["comprehension"] = round(session_comprehension, 1)
    if session_engagement < 60:
        weaknesses["focus"] = round(session_engagement, 1)
    if weaknesses:
        profile.weaknesses = weaknesses

    strengths = {}
    if session_comprehension >= 80:
        strengths["comprehension"] = round(session_comprehension, 1)
    if session_engagement >= 80:
        strengths["focus"] = round(session_engagement, 1)
    if strengths:
        profile.strengths = strengths

    await db.flush()

    return {
        "total_sessions": profile.total_sessions,
        "avg_literacy_score": round(profile.avg_literacy_score, 1),
        "current_level": profile.current_level,
        "total_xp": profile.total_xp,
        "trend": profile.trend,
    }


async def get_profile(db: AsyncSession, user_id: str) -> dict | None:
    """프로필 조회."""
    result = await db.execute(
        select(LiteracyProfile).filter(LiteracyProfile.user_id == user_id)
    )
    profile = result.scalars().first()
    if not profile:
        return None
    return {
        "user_id": profile.user_id,
        "total_sessions": profile.total_sessions,
        "avg_literacy_score": round(profile.avg_literacy_score, 1),
        "avg_comprehension": round(profile.avg_comprehension, 1),
        "avg_engagement": round(profile.avg_engagement, 1),
        "current_level": profile.current_level,
        "total_xp": profile.total_xp,
        "weaknesses": profile.weaknesses,
        "strengths": profile.strengths,
        "trend": profile.trend,
    }
