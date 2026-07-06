"""리워드 서비스 - XP/레벨/배지 처리 (7/1 구현)

XP 산출 공식:
    base_xp = literacy_score * 1.5
    completion_bonus = 20 if completed else 0
    streak_bonus = min(streak_days * 5, 25)
    total_xp = base_xp + completion_bonus + streak_bonus

레벨 시스템:
    Level 1: 0 ~ 99 XP
    Level 2: 100 ~ 299 XP
    Level 3: 300 ~ 599 XP
    Level 4: 600 ~ 999 XP
    Level 5: 1000+ XP
"""

from __future__ import annotations
from typing import Optional

# 레벨 임계값
LEVEL_THRESHOLDS = [
    (1, 0),
    (2, 100),
    (3, 300),
    (4, 600),
    (5, 1000),
]

# 배지 정의
BADGE_DEFINITIONS = [
    {"id": "first-read", "name": "첫 완독", "emoji": "📖", "description": "첫 번째 글을 완독했어요!", "condition": lambda sessions: sessions >= 1},
    {"id": "five-reads", "name": "독서왕", "emoji": "👑", "description": "5개의 글을 완독했어요!", "condition": lambda sessions: sessions >= 5},
    {"id": "ten-reads", "name": "독서 마스터", "emoji": "🏆", "description": "10개의 글을 완독했어요!", "condition": lambda sessions: sessions >= 10},
    {"id": "high-score", "name": "만점왕", "emoji": "⭐", "description": "리터러시 점수 95점 이상 달성!", "condition": lambda sessions: False},  # 별도 체크
    {"id": "focus-master", "name": "집중 달인", "emoji": "🧘", "description": "집중도 90점 이상으로 완독!", "condition": lambda sessions: False},  # 별도 체크
]


def calculate_xp(
    *,
    literacy_score: float,
    completed: bool = True,
    streak_days: int = 0,
) -> int:
    """세션 완료 시 획득 XP 계산."""
    base_xp = literacy_score * 1.5
    completion_bonus = 20.0 if completed else 0.0
    streak_bonus = min(streak_days * 5, 25)
    total = base_xp + completion_bonus + streak_bonus
    return max(0, int(round(total)))


def get_level_for_xp(total_xp: int) -> int:
    """누적 XP에 해당하는 레벨 반환."""
    level = 1
    for lv, threshold in LEVEL_THRESHOLDS:
        if total_xp >= threshold:
            level = lv
    return level


def check_level_up(old_xp: int, new_xp: int) -> tuple[bool, int]:
    """레벨업 여부와 새 레벨 반환."""
    old_level = get_level_for_xp(old_xp)
    new_level = get_level_for_xp(new_xp)
    return new_level > old_level, new_level


def check_badges(
    *,
    total_sessions: int,
    literacy_score: float = 0.0,
    engagement_score: float = 0.0,
    existing_badge_ids: Optional[list[str]] = None,
) -> list[dict]:
    """새로 획득한 배지 목록 반환."""
    existing = set(existing_badge_ids or [])
    new_badges = []

    for badge_def in BADGE_DEFINITIONS:
        bid = badge_def["id"]
        if bid in existing:
            continue

        # 특수 조건 배지
        if bid == "high-score" and literacy_score >= 95:
            new_badges.append({"id": bid, "name": badge_def["name"], "emoji": badge_def["emoji"], "description": badge_def["description"]})
        elif bid == "focus-master" and engagement_score >= 90:
            new_badges.append({"id": bid, "name": badge_def["name"], "emoji": badge_def["emoji"], "description": badge_def["description"]})
        elif badge_def["condition"](total_sessions):
            new_badges.append({"id": bid, "name": badge_def["name"], "emoji": badge_def["emoji"], "description": badge_def["description"]})

    return new_badges
