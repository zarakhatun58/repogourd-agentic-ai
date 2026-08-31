export type TrajectoryStepType =
  | 'instruction'
  | 'tool_call'
  | 'tool_response'
  | 'reasoning'
  | 'finding'
  | 'verification'
  | 'result';

export interface TrajectoryStep {
  id: string;
  order: number;
  type: TrajectoryStepType;
  label: string;
  detail: string;
  evidenceRef?: string;
  toolName?: string;
  toolInput?: string;
  toolOutput?: string;
  retry?: boolean;
  timestamp: string;
}

export type TrajectoryEventType =
  | 'analysis_started'
  | 'repository_inspected'
  | 'security_scan_completed'
  | 'analysis_completed'
  | string;

export type Trajectory = {
  id: string;
  analysis_run_id: string;
  step_number: number;
  event_type: string;
  tool_name: string | null;
  input_data: Record<string, unknown> | null;
  output_data: Record<string, unknown> | null;
  observation: string | null;
  created_at: string;
};