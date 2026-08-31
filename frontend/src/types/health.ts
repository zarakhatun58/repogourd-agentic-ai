export interface HealthStatus {
  connected: boolean;
  version?: string;
  environment?: string;
  checkedAt: string;
}