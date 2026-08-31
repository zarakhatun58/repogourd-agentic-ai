export type AgentType =
  | 'repository'
  | 'code_quality'
  | 'testing'
  | 'dependency'
  | 'verification'
  | 'judge';

export type AgentStatus =
  | 'pending'
  | 'running'
  | 'completed'
  | 'failed'
  | 'skipped';

export interface AgentRun {
  id: string;
  auditId: string;
  agentType: AgentType;
  name: string;
  description: string;
  status: AgentStatus;
  durationMs: number;
  findingsCount: number;
  evidenceCount: number;
  startedAt: string;
  completedAt: string | null;
}

export const AGENT_LABELS: Record<AgentType, string> = {
  repository: 'Repository Agent',
  code_quality: 'Code Quality Agent',
  testing: 'Testing Agent',
  dependency: 'Dependency Agent',
  verification: 'Verification Agent',
  judge: 'Judge Agent',
};

export const AGENT_DESCRIPTIONS: Record<AgentType, string> = {
  repository: 'Collects repository structure and metadata.',
  code_quality: 'Analyzes architecture and code quality.',
  testing: 'Examines tests and testing gaps.',
  dependency: 'Examines dependency configuration and risks.',
  verification: 'Checks whether findings are supported by evidence.',
  judge: 'Produces the final engineering assessment.',
};