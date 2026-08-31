export type EvaluationMode = 'baseline' | 'advanced';

export interface EvaluationMetric {
  key: string;
  label: string;
  unit: string;
  baseline: number;
  advanced: number;
  higherIsBetter: boolean;
}

export interface EvaluationCase {
  id: string;
  name: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  baselineScore: number;
  advancedScore: number;
  improvement: number;
  detailUrl?: string;
}

export interface EvaluationSummary {
  id: string;
  runAt: string;
  baselineOverall: number;
  advancedOverall: number;
  metrics: EvaluationMetric[];
  cases: EvaluationCase[];
}

export function mapEvaluationMetric(metric: {
  key: string;
  label: string;
  unit: string;
  baseline: number;
  advanced: number;
  higher_is_better: boolean;
}): EvaluationSummary['metrics'][number] {
  return {
    key: metric.key,
    label: metric.label,
    unit: metric.unit,
    baseline: metric.baseline,
    advanced: metric.advanced,
    higherIsBetter: metric.higher_is_better,
  };
}

export function mapEvaluationCase(item: {
  case_id: string;
  case_name: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | string;
  baseline_score: number;
  advanced_score: number;
  improvement: number;
}): EvaluationSummary['cases'][number] {
  return {
    id: item.case_id,
    name: item.case_name,
    description: item.description,
    status: item.status as EvaluationSummary['cases'][number]['status'],
    baselineScore: item.baseline_score,
    advancedScore: item.advanced_score,
    improvement: item.improvement,
  };
}

export type EvaluationApiResponse = {
  id: string;
  status: string;
  benchmark_version: string;
  primary_metric: string;
  baseline_overall: number;
  advanced_overall: number;
  human_time_baseline: number;
  human_time_advanced: number;
  cost_baseline: number;
  cost_advanced: number;
  configuration?: Record<string, unknown> | null;
  created_at: string;
};

export type EvaluationDetailApiResponse = EvaluationApiResponse & {
  metrics: Array<{
    key: string;
    label: string;
    unit: string;
    baseline: number;
    advanced: number;
    higher_is_better: boolean;
  }>;
  cases: Array<{
    case_id: string;
    case_name: string;
    description: string;
    status: string;
    baseline_score: number;
    advanced_score: number;
    improvement: number;
  }>;
};

export function mapEvaluation(
  evaluation: EvaluationDetailApiResponse
): EvaluationSummary {
  return {
    id: evaluation.id,
    runAt: evaluation.created_at,
    baselineOverall: evaluation.baseline_overall,
    advancedOverall: evaluation.advanced_overall,
    metrics: evaluation.metrics.map(mapEvaluationMetric),
    cases: evaluation.cases.map(mapEvaluationCase),
  };
}
