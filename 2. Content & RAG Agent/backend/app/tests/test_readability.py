"""
test_readability.py — 가독성 분석 모듈 단위 테스트 (M0)

pytest로 실행:
  python -m pytest backend/app/tests/test_readability.py -v
"""
import pytest

from backend.app.agents.content_reducer.readability import (
    analyze_readability,
    calculate_difficulty_score,
    get_readability_label,
)


# ---------------------------------------------------------------------------
# analyze_readability 테스트
# ---------------------------------------------------------------------------

class TestAnalyzeReadability:

    def test_returns_float_in_range(self):
        """반환값이 0~100 사이의 float이어야 한다."""
        score = analyze_readability("안녕하세요. 오늘 날씨가 좋네요.")
        assert isinstance(score, float)
        assert 0.0 <= score <= 100.0

    def test_easy_text_has_high_score(self):
        """짧고 쉬운 문장은 높은 점수를 받아야 한다."""
        easy = "오늘은 날씨가 맑습니다. 바람도 시원합니다."
        score = analyze_readability(easy)
        assert score >= 50.0, f"쉬운 문장 점수가 너무 낮습니다: {score}"

    def test_hard_text_has_lower_score(self):
        """전문 용어가 많은 긴 문장은 낮은 점수를 받아야 한다."""
        hard = (
            "LLM 기반 하이브리드 라우팅 알고리즘의 레이턴시 최적화를 위한 "
            "파인튜닝 및 프롬프트 엔지니어링 기법의 비교 분석적 고찰에 관한 연구."
        )
        easy = "오늘은 날씨가 맑습니다."
        score_hard = analyze_readability(hard)
        score_easy = analyze_readability(easy)
        assert score_hard < score_easy, (
            f"어려운 텍스트({score_hard:.1f})가 쉬운 텍스트({score_easy:.1f})보다 높으면 안 됩니다"
        )

    def test_empty_string_returns_midpoint(self):
        """빈 문자열은 중간값 50.0을 반환해야 한다."""
        assert analyze_readability("") == 50.0

    def test_whitespace_only_returns_midpoint(self):
        """공백만 있는 문자열도 50.0을 반환해야 한다."""
        assert analyze_readability("   \n  ") == 50.0

    def test_same_input_returns_same_output(self):
        """같은 입력은 항상 같은 출력을 반환해야 한다 (순수 함수)."""
        text = "인공지능은 컴퓨터 과학의 한 분야로, 인간의 지능을 모방한다."
        score1 = analyze_readability(text)
        score2 = analyze_readability(text)
        assert score1 == score2

    def test_score_clamp_upper_bound(self):
        """점수는 100을 초과하지 않아야 한다."""
        score = analyze_readability("아.")
        assert score <= 100.0

    def test_score_clamp_lower_bound(self):
        """점수는 0 미만이어서는 안 된다."""
        very_hard = " ".join(["hyperparameter optimization algorithm"] * 20)
        score = analyze_readability(very_hard)
        assert score >= 0.0


# ---------------------------------------------------------------------------
# calculate_difficulty_score 테스트
# ---------------------------------------------------------------------------

class TestCalculateDifficultyScore:

    def test_difficulty_is_inverse_of_readability(self):
        """difficulty_score = 100 - readability_score여야 한다."""
        readability = 72.5
        difficulty = calculate_difficulty_score(readability)
        assert abs(difficulty - (100.0 - readability)) < 0.001

    def test_returns_in_range(self):
        """결과가 0~100 범위에 있어야 한다."""
        for r in [0.0, 25.0, 50.0, 75.0, 100.0]:
            d = calculate_difficulty_score(r)
            assert 0.0 <= d <= 100.0


# ---------------------------------------------------------------------------
# get_readability_label 테스트
# ---------------------------------------------------------------------------

class TestGetReadabilityLabel:

    @pytest.mark.parametrize("score,expected_label", [
        (80.0, "쉬움"),
        (70.0, "쉬움"),
        (69.9, "보통"),
        (50.0, "보통"),
        (49.9, "어려움"),
        (30.0, "어려움"),
        (29.9, "매우 어려움"),
        (0.0, "매우 어려움"),
    ])
    def test_labels_by_score(self, score, expected_label):
        assert get_readability_label(score) == expected_label
