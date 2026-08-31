export type Severity =
  | 'critical'
  | 'high'
  | 'medium'
  | 'low'
  | 'info';

export type VerificationStatus =
  | 'verified'
  | 'unverified'
  | 'partial';

export interface Finding {
  id: string;
  analysis_run_id: string;
  rule_id: string;
  severity: Severity;
  title: string;
  description: string | null;
  file_path: string | null;
  line_start: number | null;
  line_end: number | null;
  status: string;
  created_at: string;
}

export type FindingFilter =
  | 'all'
  | 'critical'
  | 'high'
  | 'medium'
  | 'low';