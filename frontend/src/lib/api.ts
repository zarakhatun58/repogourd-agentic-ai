import type {
  AuditSummary,
  AuditDetail,
  CreateAuditRequest,
  Finding,
  Evidence,
  AgentRun,
  EvaluationSummary,
  EvaluationApiResponse,
  ChangelogEntry,
  Trajectory,
  HealthStatus,
  Repository,
  Analysis,
  CreateAnalysisRequest,
  EvaluationDetailApiResponse,
  ArchitectureAnalysis,
  DependencyAnalysis,
  TestingAnalysis,
} from '@/src/types';
import {
  mapEvaluation,
} from '@/src/types/evaluation';

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || 'https://repogourd-agentic-ai.onrender.com';

export const DEMO_MODE =
  process.env.NEXT_PUBLIC_DEMO_MODE !== 'false';

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const headers = new Headers(options?.headers);

  if (!(options?.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const message = await res
      .json()
      .then((b: { detail?: string }) => b.detail ?? res.statusText)
      .catch(() => res.statusText);

    throw new Error(message);
  }

  return res.json() as Promise<T>;
}

export const api = {
  baseUrl: API_URL,

  async getHealth(): Promise<HealthStatus> {
    try {
      const data = await request<{
        status: string;
        version?: string;
        environment?: string;
      }>('/health');
      return {
        connected: data.status === 'ok' || data.status === 'healthy',
        version: data.version,
        environment: data.environment,
        checkedAt: new Date().toISOString(),
      };
    } catch {
      return {
        connected: false,
        checkedAt: new Date().toISOString(),
      };
    }
  },

  async createAudit(body: CreateAuditRequest): Promise<AuditSummary> {
    return request<AuditSummary>('/audits', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  },

  async listAudits(): Promise<AuditSummary[]> {
    return request<AuditSummary[]>('/audits');
  },

  async getAudit(id: string): Promise<AuditDetail> {
    return request<AuditDetail>(`/audits/${id}`);
  },

async getFindings(analysisId: string): Promise<Finding[]> {
  return request<Finding[]>(
    `/analyses/${analysisId}/findings`
  );
},
 async getEvidence(findingId: string): Promise<Evidence[]> {
  return request<Evidence[]>(
    `/findings/${findingId}/evidence`
  );
},

  async getAgents(auditId: string): Promise<AgentRun[]> {
    return request<AgentRun[]>(`/audits/${auditId}/agents`);
  },
async createAnalysis(
  body: CreateAnalysisRequest
): Promise<Analysis> {
  return request<Analysis>('/analyses', {
    method: 'POST',
    body: JSON.stringify(body),
  });
},

async getAnalysis(
  analysisId: string
): Promise<Analysis> {
  return request<Analysis>(
    `/analyses/${analysisId}`
  );
},
async getAnalysisFindings(analysisId: string): Promise<Finding[]> {
  return request<Finding[]>(
    `/analyses/${analysisId}/findings`
  );
},
async listAnalyses(): Promise<Analysis[]> {
  return request<Analysis[]>('/analyses');
},

async runAnalysis(
  analysisId: string
): Promise<Analysis> {
  return request<Analysis>(
    `/analyses/${analysisId}/run`,
    {
      method: 'POST',
    }
  );
},
async ingestGithubRepository(url: string): Promise<Repository> {
 return request<Repository>('/repositories/github',
   { method: 'POST', 
    headers: { 'Content-Type': 'application/json', }, 
  body: JSON.stringify({ url, }),
 }); 
},
async uploadRepository(file: File): Promise<Repository> {
  const formData = new FormData();
  formData.append('file', file);

  return request<Repository>('/repositories/upload', {
    method: 'POST',
    body: formData,
  });
},

async getRepository(repositoryId: string): Promise<Repository> {
  return request<Repository>(
    `/repositories/${repositoryId}`
  );
},
  async listRepositories(): Promise<Repository[]> {
    return request<Repository[]>('/repositories');
  },

   async listEvaluations(): Promise<EvaluationSummary[]> {
    const evaluations = await request<EvaluationApiResponse[]>('/evaluations');
    return Promise.all(
      evaluations.map(async (evaluation) => {
        const detail = await request<EvaluationDetailApiResponse>(
          `/evaluations/${evaluation.id}`
        );
        return mapEvaluation(detail);
      })
    );
  },

  async getEvaluation(id: string): Promise<EvaluationSummary> {
    const evaluation = await request<EvaluationDetailApiResponse>(
      `/evaluations/${id}`
    );
    return mapEvaluation(evaluation);
  },

  async runEvaluation(): Promise<EvaluationSummary> {
    const evaluation = await request<EvaluationApiResponse>('/evaluations/run', {
      method: 'POST',
    });
    return this.getEvaluation(evaluation.id);
  },
  async getArchitectureAnalysis(
    analysisId: string
  ): Promise<ArchitectureAnalysis> {
    return request<ArchitectureAnalysis>(
      `/analyses/${analysisId}/architecture`
    );
  },

  async getDependencyAnalysis(
    analysisId: string
  ): Promise<DependencyAnalysis> {
    return request<DependencyAnalysis>(
      `/analyses/${analysisId}/dependencies`
    );
  },

  async getTestingAnalysis(
    analysisId: string
  ): Promise<TestingAnalysis> {
    return request<TestingAnalysis>(
      `/analyses/${analysisId}/testing`
    );
  },

  async getChangelog(): Promise<ChangelogEntry[]> {
    return request<ChangelogEntry[]>('/changelog');
  },

  async getTrajectories(analysisId: string): Promise<Trajectory[]> {
  return request<Trajectory[]>(
    `/analyses/${analysisId}/trajectory`
  );
},
};
