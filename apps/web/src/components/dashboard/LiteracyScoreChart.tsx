import React from 'react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { scoreSeries } from '../../mock/scoreSeries';

/**
 * LiteracyScoreChart Component Stub (TODO: 6/2x)
 * 케어 적용 전/후 리터러시 점수의 변화 추이를 보여주는 데모 시각화 그래프입니다.
 */
export const LiteracyScoreChart: React.FC = () => {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart
        data={scoreSeries}
        margin={{ top: 10, right: 10, left: -25, bottom: 0 }}
      >
        <CartesianGrid strokeDasharray="4 4" stroke="var(--color-border)" />
        <XAxis 
          dataKey="day" 
          stroke="var(--color-text-secondary)" 
          fontSize={11} 
          tickLine={false}
        />
        <YAxis 
          stroke="var(--color-text-secondary)" 
          fontSize={11} 
          tickLine={false} 
          domain={[30, 100]}
        />
        <Tooltip 
          contentStyle={{ 
            backgroundColor: 'var(--color-surface)', 
            borderColor: 'var(--color-border)',
            borderRadius: 'var(--radius-md)',
            color: 'var(--color-text)',
            fontSize: '12px'
          }} 
        />
        <Line 
          type="monotone" 
          dataKey="beforeCare" 
          stroke="var(--color-comprehension)" 
          strokeWidth={2.5}
          activeDot={{ r: 6 }}
          name="케어 전" 
        />
        <Line 
          type="monotone" 
          dataKey="afterCare" 
          stroke="var(--color-growth)" 
          strokeWidth={2.5}
          activeDot={{ r: 6 }}
          name="케어 후" 
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

export default LiteracyScoreChart;
