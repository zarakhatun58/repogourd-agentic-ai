export type AuditStatus =
  | 'pending'
  | 'indexing'
  | 'analyzing'
  | 'completed'
  | 'failed';

export type RiskLevel =
  | 'critical'
  | 'high'
  | 'medium'
  | 'low'
  | 'info';

export type AnalysisDepth =
  | 'standard'
  | 'deep';

export type AuditCategory =
  | 'architecture'
  | 'code_quality'
  | 'testing'
  | 'dependencies'
  | 'security';

export interface AuditCategoryScore {
  category: AuditCategory;
  score: number;
  maxScore: number;
}

export interface AuditSummary {
  id: string;
  repositoryId: string;
  repositoryName: string;
  status: AuditStatus;
  overallScore: number;
  riskLevel: RiskLevel;
  evidenceCoverage: number;
  criticalFindings: number;
  highFindings: number;
  mediumFindings: number;
  lowFindings: number;
  createdAt: string;
  completedAt: string | null;
}

export interface AuditConfig {
  depth: AnalysisDepth;
  categories: AuditCategory[];
}

export interface AuditDetail extends AuditSummary {
  branch: string;
  commit: string;
  language: string;
  fileCount: number;
  testCount: number;
  categoryScores: AuditCategoryScore[];
  config: AuditConfig;
}

export interface CreateAuditRequest {
  repositoryUrl?: string;
  uploadFileName?: string;
  config: AuditConfig;
}

export interface AuditStep {
  id: string;
  label: string;
  status:
    | 'pending'
    | 'running'
    | 'completed'
    | 'failed';
  startedAt?: string;
  completedAt?: string;
  message?: string;
}