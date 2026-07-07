# 한국어 가독성 지수 계산 공식

> **문서 목적**: `readability.py`의 계산 공식을 수식과 함께 설명한다.  
> 발표 시 "가독성 측정의 객관성" 질문에 대한 기술적 근거로 활용한다.

---

## 1. 개요

이 프로젝트는 Flesch-Kincaid 가독성 공식을 **한국어 특성에 맞게 보정**하여 사용한다.

영어 원본 공식:

```
Flesch Reading Ease = 206.835 - 1.015 × (문장당 단어 수) - 84.6 × (단어당 음절 수)
```

한국어는 교착어(조사/어미가 어절에 붙는 언어)이므로 음절 계수와 전문 용어 비율을 별도로 반영한다.

---

## 2. 적용 공식

```
readability_score =
  100
  - (avg_words_per_sentence × 1.015)
  - (avg_syllables_per_word × 8.0)
  - (technical_term_ratio × 35.0)

readability_score = clamp(readability_score, 0, 100)
difficulty_score = 100 - readability_score
```

---

## 3. 구성 요소 정의

### 3.1 avg_words_per_sentence (문장당 평균 어절 수)

- **어절**: 공백으로 구분되는 단위 (한국어의 기본 음운 단위)
- **문장 분리 패턴**: `다.`, `요.`, `.`, `!`, `?` 뒤 공백
- 문장이 없으면 전체 어절 수를 문장 1개로 계산

```
avg_words_per_sentence = Σ(각 문장의 어절 수) / 전체 문장 수
```

**해석**:
- 5 이하: 짧은 문장 (읽기 쉬움)
- 10~15: 일반적인 문장
- 20 이상: 긴 복잡한 문장

### 3.2 avg_syllables_per_word (어절당 평균 음절 수)

- **음절**: 한글 자모 결합 단위 (`가-힣` 범위의 유니코드 문자 1개)
- 영어/숫자는 음절 계산에서 제외

```
avg_syllables_per_word = Σ(각 어절의 한글 음절 수) / 전체 어절 수
```

**해석**:
- 2 이하: 짧은 어절 (읽기 쉬움)
- 3~4: 일반적인 어절
- 5 이상: 긴 복합어 (읽기 어려움)

### 3.3 technical_term_ratio (전문 용어 비율)

두 가지 패턴을 합산하여 추정한다:

1. **영어 단어**: 3자 이상 (`LLM`, `API`, `GPU` 등)
2. **한국어 전문 용어 접미사**: `화`, `율`, `성`, `도`, `적`, `론`, `법`, `형`, `식`, `계`, `기`, `학`

```
technical_count = len(영어_단어) + len(접미사_패턴)
technical_term_ratio = min(technical_count / 전체_어절_수, 1.0)
```

---

## 4. 점수 해석표

| readability_score | difficulty_score | 수준 | 대상 독자 |
|---|---|---|---|
| 70 이상 | 30 이하 | 쉬움 | 초중등학생 |
| 50 ~ 69 | 31 ~ 50 | 보통 | 일반 성인 |
| 30 ~ 49 | 51 ~ 70 | 어려움 | 대학생/전문가 입문 |
| 30 미만 | 70 초과 | 매우 어려움 | 해당 분야 전문가 |

---

## 5. 계산 예시

### 예시 A: 쉬운 문장

```
텍스트: "오늘은 날씨가 맑습니다. 바람도 시원합니다."

avg_words_per_sentence = (4 + 3) / 2 = 3.5
avg_syllables_per_word ≈ 2.5
technical_term_ratio ≈ 0.0

readability_score = 100 - (3.5 × 1.015) - (2.5 × 8.0) - (0.0 × 35.0)
                  = 100 - 3.55 - 20.0 - 0
                  = 76.45 → "쉬움"
```

### 예시 B: 전문적인 문장

```
텍스트: "LLM 기반 하이브리드 라우팅 알고리즘의 레이턴시 최적화를 위한 파인튜닝 기법."

avg_words_per_sentence = 7
avg_syllables_per_word ≈ 3.8
technical_term_ratio ≈ 0.6

readability_score = 100 - (7 × 1.015) - (3.8 × 8.0) - (0.6 × 35.0)
                  = 100 - 7.1 - 30.4 - 21.0
                  = 41.5 → "어려움"
```

---

## 6. Literacy Score와의 연결

`difficulty_score`는 1번 Orchestrator의 Literacy Score 계산에 직접 사용된다:

```python
literacy_score =
  comprehension_score * 0.50
  + engagement_score * 0.35
  + difficulty_score * 0.15      # ← 2번이 제공
  - cross_validation_penalty
```

난이도가 높은 글에서 높은 이해도를 보이면 더 높은 점수를 얻을 수 있다.

---

## 7. 한계 및 개선 방향

| 한계 | 현재 대응 | 향후 개선 |
|---|---|---|
| 구어체/신조어 미반영 | 접미사 패턴으로 근사 | 한국어 코퍼스 기반 학습 모델 |
| 문맥 무시 | 표면적 특징만 분석 | 의미 기반 가독성 모델 |
| 도메인별 차이 미반영 | 단일 공식 적용 | 도메인별 보정 계수 |
