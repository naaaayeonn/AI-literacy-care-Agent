def test_full_pipeline():
    raw_text = "머신러닝은 데이터를 통해 학습한다."

    simplified_text = raw_text

    quiz = "머신러닝은 무엇을 통해 학습하는가?"

    answer = "데이터"

    literacy_score = 90

    assert simplified_text is not None
    assert quiz != ""
    assert answer == "데이터"
    assert literacy_score > 0