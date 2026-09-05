export type AnalysisStatus =
  | 'pending'
  | 'queued'
  | 'running'
  | 'completed'
  | 'failed';
export interface AnalysisCategoryScore {
  category: string;
  score: number | null;
  max_score: number;
}
export interface Analysis {
  id: string;
  repository_id: string;
  status: AnalysisStatus;
  agent_type: string | null;
  commit_sha: string | null;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  created_at: string;
}

export interface CreateAnalysisRequest {
  repository_id: string;
  agent_type?: string;
}

export interface ArchitectureLayer {
  name: string;
  module: string;
}

export interface ArchitectureModule {
  id: string;
  name: string;
  layer: string;
  files: string[];
  responsibilities: string[];
  dependencies: string[];
  findings: string[];
}

export interface ArchitectureRelationship {
  source: string;
  target: string;
  relationship_type: string;
}

export interface ArchitectureAnalysis {
  analysis_id: string;
  technologies: string[];
  layers: ArchitectureLayer[];
  modules: ArchitectureModule[];
  relationships: ArchitectureRelationship[];
  risks: string[];
  files_scanned: number;
}
export type DependencyType =
  | 'prod'
  | 'dev'
  | 'optional'
  | 'unknown';

export type DependencyStatus =
  | 'ok'
  | 'outdated'
  | 'conflict'
  | 'unknown';

export type DependencyRisk =
  | 'low'
  | 'medium'
  | 'high';

export interface DependencyPackage {
  package: string;
  version: string;
  type: DependencyType;
  status: DependencyStatus;
  risk: DependencyRisk;
}

export interface DependencyAnalysis {
  total: number;
  direct: number;
  dev: number;
  optional: number;
  outdated: number;
  conflicts: number;
  packages: DependencyPackage[];
}

export interface TestingCategory {
  name: string;
  count: number;
}

export type TestingStatus =
  | 'completed'
  | 'partial'
  | 'failed';

export interface TestingAnalysis {
  analysis_id: string;

  status: TestingStatus;

  test_files: number;
  test_suites: number;

  passed: number;
  failed: number;

  coverage: number | null;

  coverage_source: string;

  framework: string;

  categories: TestingCategory[];

  missing_areas: string[];

  execution_status: string;

  files_scanned: number;
}