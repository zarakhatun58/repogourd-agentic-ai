export interface Evidence {
  id: string;
  finding_id: string;
  evidence_type: string;
  file_path: string | null;
  line_start: number | null;
  line_end: number | null;
  content: string | null;
  verification_status: string;
  created_at: string;
}