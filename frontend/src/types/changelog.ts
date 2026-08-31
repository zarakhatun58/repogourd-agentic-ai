export type ChangelogDecision = 'kept' | 'revised' | 'removed';

export interface ChangelogEntry {
  id: string;
  iteration: string;
  title: string;
  whatChanged: string;
  whyChanged: string;
  result: string;
  evidence: string;
  decision: ChangelogDecision;
  order: number;
}
