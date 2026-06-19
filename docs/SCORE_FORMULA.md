# Literacy Score 계산식 (작성 예정: 6/26)

`backend/app/orchestrator/score.py` 구현과 1:1로 맞춘다.

초기 계산식 (ARCHITECTURE §6.5):

```
comprehension_score   = quiz_correct_rate * 100
engagement_score      = focus_score
difficulty_adjustment = difficulty_score * 0.15
penalty               = abnormal_reading_penalty

literacy_score = comprehension_score*0.50 + engagement_score*0.35
               + difficulty_adjustment - penalty   (→ 0~100 clamp)
```

보정 로직 / 가중치 근거 / score_breakdown 예시는 6/26 구현과 함께 채운다.
