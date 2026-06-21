import React from 'react';

/**
 * QuizCard Component Stub (TODO: 6/2x)
 * 읽기 완료 후 혹은 Hard Nudge 상황에서 팝업되는 퀴즈 카드입니다.
 */
export const QuizCard: React.FC<{ 
  question?: string; 
  options?: string[]; 
  onSubmit?: (selected: string) => void;
}> = ({ question, options = [], onSubmit }) => {
  return (
    <div className="p-6 bg-surface border border-border rounded-lg shadow-md max-w-md w-full z-quiz">
      <div className="flex items-center gap-2 mb-3">
        <span className="px-2 py-0.5 text-xs bg-primary-tint text-primary rounded-full font-weight-medium">이해도 평가</span>
        <span className="text-xs text-text-secondary">AI 생성 퀴즈</span>
      </div>
      <h3 className="text-base font-weight-semibold text-text mb-4">
        {question || "글의 주요 내용과 일치하지 않는 설명을 선택해 주세요."}
      </h3>
      <div className="space-y-2 mb-4">
        {options.length > 0 ? (
          options.map((option, i) => (
            <button
              key={i}
              onClick={() => onSubmit?.(option)}
              className="w-full text-left p-3 text-sm rounded-md border border-border hover:bg-surface-alt hover:border-primary-tint transition-all"
            >
              {option}
            </button>
          ))
        ) : (
          <>
            <button className="w-full text-left p-3 text-sm rounded-md border border-border hover:bg-surface-alt transition-all">
              ① 디지털 리터러시는 단순히 기술을 사용하는 능력이다. (정답예시)
            </button>
            <button className="w-full text-left p-3 text-sm rounded-md border border-border hover:bg-surface-alt transition-all">
              ② LLM 생성 모델의 환각 현상은 정보 신뢰를 방해한다.
            </button>
            <button className="w-full text-left p-3 text-sm rounded-md border border-border hover:bg-surface-alt transition-all">
              ③ 현대의 리터러시는 복합적 사고력이 결합된 형태다.
            </button>
          </>
        )}
      </div>
      <div className="text-center text-xs text-text-muted">
        [퀴즈 정답 결과는 실시간으로 Literacy Score에 반영됩니다]
      </div>
    </div>
  );
};

export default QuizCard;
