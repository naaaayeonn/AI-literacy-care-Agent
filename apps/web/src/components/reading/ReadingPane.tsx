import React from 'react';
import { sampleArticle } from '../../mock/sampleArticle';

/**
 * ReadingPane Component Stub (TODO: 6/2x)
 * 사용자의 스크롤, 체류, 이탈을 측정하는 읽기 패널 뼈대입니다.
 */
export const ReadingPane: React.FC = () => {
  return (
    <div className="p-6 bg-surface rounded-lg border border-border shadow-sm">
      <div className="mb-4">
        <span className="inline-block px-2.5 py-0.5 text-xs font-weight-medium rounded-full bg-primary-tint text-primary mb-2">
          {sampleArticle.category}
        </span>
        <h1 className="text-2xl font-weight-bold text-text leading-tight font-sans">
          {sampleArticle.title}
        </h1>
        <p className="text-sm text-text-secondary mt-1">
          저자: {sampleArticle.author} · 발행일: {sampleArticle.publishedAt}
        </p>
      </div>

      <hr className="border-border my-4" />

      {/* 읽기 본문 영역 (.reading 유틸 사용) */}
      <div className="reading space-y-6 mx-auto text-text leading-reading text-reading font-sans">
        {sampleArticle.content.map((paragraph, index) => (
          <p key={index} className="text-justify">
            {paragraph}
          </p>
        ))}
      </div>
      
      <div className="mt-8 text-center text-xs text-text-muted">
        [읽기 감지 영역 - 스크롤 및 체류 시간 실시간 분석 중]
      </div>
    </div>
  );
};

export default ReadingPane;
