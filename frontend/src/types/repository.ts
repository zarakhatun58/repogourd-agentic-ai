// export interface Repository {
//   id: string;
//   name: string;
//   url?: string;
//   language: string;
//   branch: string;
//   lastAuditDate: string | null;
//   lastScore: number | null;
//   status: 'active' | 'idle' | 'error';
//   fileCount: number;
// }
export interface Repository {
  id: string;
  name: string;
  source_type: string;
  source_url: string | null;
  default_branch: string;
}