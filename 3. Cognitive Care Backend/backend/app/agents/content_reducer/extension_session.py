"""
extension_session.py — 크롬 확장 및 PDF 대응 인입 정규화 모듈 (Phase E)

웹(Readability) 및 PDF(pdf.js)에서 넘어온 content[] 배열을 정제하고,
반복되는 머리말/꼬리말(쪽번호, 반복되는 논문명 등)을 필터링하여 하나의 raw_text로 변환한다.
"""
from __future__ import annotations

import re
from collections import Counter


def remove_repeated_lines(paragraphs: list[str]) -> list[str]:
    """
    여러 문단에 걸쳐 반복되는 짧은 라인(머리말, 꼬리말, 쪽번호 등)을 분석하여 제거한다.
    
    규칙:
      - 각 문단을 개행(\\n) 기준으로 줄 분리
      - 전체 문서에서 특정 줄의 등장 빈도 측정
      - 등장 빈도가 3회 이상(혹은 전체 문단 수의 10% 이상)이고, 길이가 50자 이하인 줄은 
        헤더/푸터 또는 쪽번호 후보로 간주하여 각 문단에서 제거한다.
    """
    if not paragraphs:
        return []

    # 1. 모든 줄의 빈도 계산
    line_counter = Counter()
    for para in paragraphs:
        lines = [line.strip() for line in para.split("\n") if line.strip()]
        # 한 문단 내의 중복 줄은 1회로 간주 (문단 내 반복 단어 보호)
        for unique_line in set(lines):
            line_counter[unique_line] += 1

    # 2. 제거 대상 머리말/꼬리말 후보 확정 (빈도 >= 3 이고 길이 <= 50자)
    num_paras = len(paragraphs)
    min_frequency = max(3, int(num_paras * 0.1))
    
    repeated_lines = {
        line for line, count in line_counter.items()
        if count >= min_frequency and len(line) <= 50
    }

    # 3. 각 문단에서 제거 대상 줄 제외 후 재결합
    cleaned_paragraphs = []
    for para in paragraphs:
        lines = para.split("\n")
        filtered_lines = [
            line for line in lines 
            if line.strip() not in repeated_lines
        ]
        cleaned_para = "\n".join(filtered_lines).strip()
        if cleaned_para:
            cleaned_paragraphs.append(cleaned_para)
            
    return cleaned_paragraphs


def _content_to_raw_text(content: list[str]) -> str:
    """
    정규화 규칙:
      - 문단별 strip() 수행 및 빈 문단 필터링
      - 반복 헤더/푸터 제거 알고리즘 실행
      - 문단 간 이중 개행(\\n\\n)으로 결합
    """
    if not content:
        return ""
        
    # 1. 기본적인 strip 및 공백 문단 정리
    cleaned = [p.strip() for p in content if p.strip()]
    
    # 2. 반복 머리말/꼬리말 제거
    cleaned = remove_repeated_lines(cleaned)
    
    # 3. 이중 개행으로 결합
    return "\n\n".join(cleaned)
