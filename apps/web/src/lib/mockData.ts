import { sampleArticle } from '../mock/sampleArticle';
import { scoreSeries } from '../mock/scoreSeries';

/**
 * 데모용 Mock 데이터 라이브러리 스텁 (TODO: 6/2x)
 */

export const mockData = {
  getSampleArticle: () => sampleArticle,
  getScoreSeries: () => scoreSeries,
};
