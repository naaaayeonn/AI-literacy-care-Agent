export interface ScoreDataPoint {
  day: string;
  beforeCare: number;
  afterCare: number;
}

export const scoreSeries: ScoreDataPoint[] = [
  { day: "월", beforeCare: 45, afterCare: 60 },
  { day: "화", beforeCare: 48, afterCare: 65 },
  { day: "수", beforeCare: 42, afterCare: 72 },
  { day: "목", beforeCare: 50, afterCare: 78 },
  { day: "금", beforeCare: 47, afterCare: 85 },
  { day: "토", beforeCare: 55, afterCare: 88 },
  { day: "일", beforeCare: 52, afterCare: 92 },
];
