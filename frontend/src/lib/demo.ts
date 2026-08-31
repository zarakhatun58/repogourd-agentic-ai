
import type {
  AuditSummary,
  AuditDetail,
  AuditStep,
  Finding,
  Evidence,
  AgentRun,
  EvaluationSummary,
  ChangelogEntry,
  Trajectory,
  Repository,
} from '@/src/types';

export const DEMO_AUDITS: AuditSummary[] = [
  {
    id: 'aud-001',
    repositoryId: '00000000-0000-0000-0000-000000000001',
    repositoryName: 'payments-api',
    status: 'completed',
    overallScore: 82,
    riskLevel: 'medium',
    evidenceCoverage: 94,
    criticalFindings: 0,
    highFindings: 3,
    mediumFindings: 7,
    lowFindings: 12,
    createdAt: '2026-08-24T10:12:00Z',
    completedAt: '2026-08-24T10:31:00Z',
  },
  {
    id: 'aud-002',
    repositoryId: '00000000-0000-0000-0000-000000000002',
    repositoryName: 'customer-portal',
    status: 'completed',
    overallScore: 71,
    riskLevel: 'high',
    evidenceCoverage: 88,
    criticalFindings: 1,
    highFindings: 5,
    mediumFindings: 9,
    lowFindings: 6,
    createdAt: '2026-08-22T14:05:00Z',
    completedAt: '2026-08-22T14:28:00Z',
  },
  {
    id: 'aud-003',
    repositoryId: '00000000-0000-0000-0000-000000000003',
    repositoryName: 'ecommerce-platform',
    status: 'completed',
    overallScore: 67,
    riskLevel: 'high',
    evidenceCoverage: 81,
    criticalFindings: 2,
    highFindings: 6,
    mediumFindings: 11,
    lowFindings: 8,
    createdAt: '2026-08-20T09:40:00Z',
    completedAt: '2026-08-20T10:08:00Z',
  },
  {
    id: 'aud-004',
    repositoryId: '00000000-0000-0000-0000-000000000004',
    repositoryName: 'task-management-api',
    status: 'completed',
    overallScore: 89,
    riskLevel: 'low',
    evidenceCoverage: 97,
    criticalFindings: 0,
    highFindings: 1,
    mediumFindings: 4,
    lowFindings: 9,
    createdAt: '2026-08-18T16:20:00Z',
    completedAt: '2026-08-18T16:35:00Z',
  },
];

export const DEMO_AUDIT_DETAIL: Record<string, AuditDetail> = {
  'aud-001': {
    ...DEMO_AUDITS[0],
    branch: 'main',
    commit: 'a1b2c3d',
    language: 'TypeScript',
    fileCount: 142,
    testCount: 58,
    config: {
      depth: 'deep',
      categories: [
        'architecture',
        'code_quality',
        'testing',
        'dependencies',
        'security',
      ],
    },
    categoryScores: [
      { category: 'architecture', score: 78, maxScore: 100 },
      { category: 'code_quality', score: 84, maxScore: 100 },
      { category: 'testing', score: 65, maxScore: 100 },
      { category: 'dependencies', score: 88, maxScore: 100 },
      { category: 'security', score: 81, maxScore: 100 },
    ],
  },

  'aud-002': {
    ...DEMO_AUDITS[1],
    branch: 'main',
    commit: 'e4f5g6h',
    language: 'JavaScript',
    fileCount: 98,
    testCount: 22,
    config: {
      depth: 'standard',
      categories: [
        'architecture',
        'code_quality',
        'testing',
        'dependencies',
      ],
    },
    categoryScores: [
      { category: 'architecture', score: 69, maxScore: 100 },
      { category: 'code_quality', score: 72, maxScore: 100 },
      { category: 'testing', score: 48, maxScore: 100 },
      { category: 'dependencies', score: 79, maxScore: 100 },
      { category: 'security', score: 74, maxScore: 100 },
    ],
  },
};

export const DEMO_AUDIT_STEPS: AuditStep[] = [
  { id: 's1', label: 'Repository received', status: 'completed' },
  { id: 's2', label: 'Repository indexed', status: 'completed' },
  { id: 's3', label: 'Files analyzed', status: 'completed' },
  { id: 's4', label: 'Tests inspected', status: 'completed' },
  { id: 's5', label: 'Dependencies inspected', status: 'completed' },
  { id: 's6', label: 'Findings generated', status: 'completed' },
  { id: 's7', label: 'Evidence verified', status: 'completed' },
  { id: 's8', label: 'Final report generated', status: 'completed' },
];

export const DEMO_FINDINGS: Finding[] = [
  {
    id: '00000000-0000-0000-0001-000000000001',
    analysis_run_id: '00000000-0000-0000-0010-000000000001',
    rule_id: 'AUTH-DUPLICATION',
    severity: 'high',
    title: 'Authentication logic is duplicated across multiple modules',
    description:
      'Token validation and session refresh logic is implemented independently in the auth service, API middleware, and websocket gateway.',
    file_path: 'src/auth/login.ts',
    line_start: 42,
    line_end: 67,
    status: 'open',
    created_at: '2026-08-24T10:12:16Z',
  },

  {
    id: '00000000-0000-0000-0001-000000000002',
    analysis_run_id: '00000000-0000-0000-0010-000000000001',
    rule_id: 'STACK-TRACE-LEAK',
    severity: 'medium',
    title: 'Error responses leak internal stack traces in production',
    description:
      'The global error handler serializes the full error stack into the response body when NODE_ENV is not strictly production.',
    file_path: 'src/server/errorHandler.ts',
    line_start: 24,
    line_end: 51,
    status: 'open',
    created_at: '2026-08-24T10:12:18Z',
  },

  {
    id: '00000000-0000-0000-0001-000000000003',
    analysis_run_id: '00000000-0000-0000-0010-000000000001',
    rule_id: 'REFUND-TEST-COVERAGE',
    severity: 'medium',
    title: 'Test coverage for payment refund flow is missing',
    description:
      'The refund module has no unit or integration tests covering partial-refund and failed-refund paths.',
    file_path: 'src/services/refund.ts',
    line_start: 1,
    line_end: 120,
    status: 'open',
    created_at: '2026-08-24T10:12:20Z',
  },

  {
    id: '00000000-0000-0000-0001-000000000004',
    analysis_run_id: '00000000-0000-0000-0010-000000000001',
    rule_id: 'OUTDATED-DEPENDENCY',
    severity: 'low',
    title: 'Outdated dependency: lodash 4.17.20',
    description:
      'lodash 4.17.20 has known prototype pollution vulnerabilities patched in later versions.',
    file_path: 'package.json',
    line_start: 34,
    line_end: 34,
    status: 'open',
    created_at: '2026-08-24T10:12:22Z',
  },
];

export const DEMO_EVIDENCE: Record<string, Evidence[]> = {
  '00000000-0000-0000-0001-000000000001': [
    {
      id: '00000000-0000-0000-0020-000000000001',
      finding_id: '00000000-0000-0000-0001-000000000001',
      evidence_type: 'code',
      file_path: 'src/auth/login.ts',
      line_start: 42,
      line_end: 67,
      content: `export async function validateToken(token: string): Promise<Session> {
  const payload = verify(token, SECRET);

  if (payload.exp < Date.now() / 1000) {
    throw new TokenExpiredError();
  }

  const session = await sessionStore.get(payload.sid);

  if (!session) {
    throw new InvalidSessionError();
  }

  return session;
}`,
      verification_status: 'verified',
      created_at: '2026-08-24T10:12:48Z',
    },
  ],

  '00000000-0000-0000-0001-000000000002': [
    {
      id: '00000000-0000-0000-0020-000000000002',
      finding_id: '00000000-0000-0000-0001-000000000002',
      evidence_type: 'code',
      file_path: 'src/server/errorHandler.ts',
      line_start: 24,
      line_end: 51,
      content: `app.use((err, req, res, next) => {
  logger.error(err);

  res.status(err.status || 500).json({
    message: err.message,
    stack: err.stack,
  });
});`,
      verification_status: 'verified',
      created_at: '2026-08-24T10:12:50Z',
    },
  ],
};

export const DEMO_AGENTS: AgentRun[] = [
  {
    id: 'agent-001',
    auditId: 'aud-001',
    agentType: 'repository',
    name: 'Repository Agent',
    description: 'Collects repository structure and metadata.',
    status: 'completed',
    durationMs: 4200,
    findingsCount: 0,
    evidenceCount: 12,
    startedAt: '2026-08-24T10:12:02Z',
    completedAt: '2026-08-24T10:12:06Z',
  },

  {
    id: 'agent-002',
    auditId: 'aud-001',
    agentType: 'code_quality',
    name: 'Code Quality Agent',
    description: 'Analyzes architecture and code quality.',
    status: 'completed',
    durationMs: 18400,
    findingsCount: 8,
    evidenceCount: 31,
    startedAt: '2026-08-24T10:12:07Z',
    completedAt: '2026-08-24T10:12:25Z',
  },

  {
    id: 'agent-003',
    auditId: 'aud-001',
    agentType: 'testing',
    name: 'Testing Agent',
    description: 'Examines tests and testing gaps.',
    status: 'completed',
    durationMs: 9800,
    findingsCount: 5,
    evidenceCount: 14,
    startedAt: '2026-08-24T10:12:26Z',
    completedAt: '2026-08-24T10:12:36Z',
  },

  {
    id: 'agent-004',
    auditId: 'aud-001',
    agentType: 'dependency',
    name: 'Dependency Agent',
    description: 'Examines dependency configuration and risks.',
    status: 'completed',
    durationMs: 6100,
    findingsCount: 4,
    evidenceCount: 9,
    startedAt: '2026-08-24T10:12:37Z',
    completedAt: '2026-08-24T10:12:43Z',
  },

  {
    id: 'agent-005',
    auditId: 'aud-001',
    agentType: 'verification',
    name: 'Verification Agent',
    description: 'Checks whether findings are supported by evidence.',
    status: 'completed',
    durationMs: 12300,
    findingsCount: 0,
    evidenceCount: 17,
    startedAt: '2026-08-24T10:12:44Z',
    completedAt: '2026-08-24T10:12:56Z',
  },

  {
    id: 'agent-006',
    auditId: 'aud-001',
    agentType: 'judge',
    name: 'Judge Agent',
    description: 'Produces the final engineering assessment.',
    status: 'completed',
    durationMs: 8700,
    findingsCount: 22,
    evidenceCount: 0,
    startedAt: '2026-08-24T10:12:57Z',
    completedAt: '2026-08-24T10:13:05Z',
  },
];

/**
 * Demo repositories matching the backend RepositoryResponse schema:
 *
 * id: UUID
 * name: string
 * source_type: string
 * source_url: string | null
 * default_branch: string
 */
export const DEMO_REPOSITORIES: Repository[] = [
  {
    id: '00000000-0000-0000-0000-000000000001',
    name: 'payments-api',
    source_type: 'github',
    source_url: 'https://github.com/example/payments-api',
    default_branch: 'main',
  },

  {
    id: '00000000-0000-0000-0000-000000000002',
    name: 'customer-portal',
    source_type: 'github',
    source_url: 'https://github.com/example/customer-portal',
    default_branch: 'main',
  },

  {
    id: '00000000-0000-0000-0000-000000000003',
    name: 'ecommerce-platform',
    source_type: 'github',
    source_url: 'https://github.com/example/ecommerce-platform',
    default_branch: 'develop',
  },

  {
    id: '00000000-0000-0000-0000-000000000004',
    name: 'task-management-api',
    source_type: 'github',
    source_url: 'https://github.com/example/task-management-api',
    default_branch: 'main',
  },
];

export const DEMO_EVALUATIONS: EvaluationSummary[] = [
  {
    id: 'eval-001',
    runAt: '2026-08-25T08:00:00Z',
    baselineOverall: 61,
    advancedOverall: 88,

    metrics: [
      {
        key: 'primary_outcome',
        label: 'Primary outcome',
        unit: '%',
        baseline: 61,
        advanced: 88,
        higherIsBetter: true,
      },
      {
        key: 'evidence_supported',
        label: 'Evidence-supported findings',
        unit: '%',
        baseline: 34,
        advanced: 92,
        higherIsBetter: true,
      },
      {
        key: 'false_positives',
        label: 'False positives',
        unit: '%',
        baseline: 27,
        advanced: 6,
        higherIsBetter: false,
      },
      {
        key: 'critical_detection',
        label: 'Critical issue detection',
        unit: '%',
        baseline: 40,
        advanced: 85,
        higherIsBetter: true,
      },
      {
        key: 'human_time',
        label: 'Human time per task',
        unit: 'min',
        baseline: 42,
        advanced: 9,
        higherIsBetter: false,
      },
      {
        key: 'cost_per_task',
        label: 'Cost per task',
        unit: '$',
        baseline: 0.12,
        advanced: 0.38,
        higherIsBetter: false,
      },
    ],

    cases: [
      {
        id: 'case-01',
        name: 'Case 01 — Clean React application',
        description: 'A well-structured React app with good practices.',
        status: 'completed',
        baselineScore: 78,
        advancedScore: 92,
        improvement: 14,
      },
      {
        id: 'case-02',
        name: 'Case 02 — Poor React architecture',
        description: 'Prop drilling, duplicated state, no separation.',
        status: 'completed',
        baselineScore: 44,
        advancedScore: 81,
        improvement: 37,
      },
      {
        id: 'case-03',
        name: 'Case 03 — Node API',
        description: 'Express API with mixed concerns.',
        status: 'completed',
        baselineScore: 58,
        advancedScore: 86,
        improvement: 28,
      },
      {
        id: 'case-04',
        name: 'Case 04 — TypeScript backend',
        description: 'TypeScript service with type safety gaps.',
        status: 'completed',
        baselineScore: 62,
        advancedScore: 84,
        improvement: 22,
      },
      {
        id: 'case-05',
        name: 'Case 05 — Next.js application',
        description: 'Next.js app with server/client boundary issues.',
        status: 'completed',
        baselineScore: 55,
        advancedScore: 83,
        improvement: 28,
      },
      {
        id: 'case-06',
        name: 'Case 06 — Missing tests',
        description: 'Repository with almost no test coverage.',
        status: 'completed',
        baselineScore: 38,
        advancedScore: 79,
        improvement: 41,
      },
      {
        id: 'case-07',
        name: 'Case 07 — Dependency issues',
        description: 'Outdated and conflicting dependencies.',
        status: 'completed',
        baselineScore: 48,
        advancedScore: 87,
        improvement: 39,
      },
      {
        id: 'case-08',
        name: 'Case 08 — Architecture problems',
        description: 'Layering violations and circular dependencies.',
        status: 'completed',
        baselineScore: 41,
        advancedScore: 82,
        improvement: 41,
      },
      {
        id: 'case-09',
        name: 'Case 09 — Security/configuration signals',
        description: 'Hardcoded secrets and insecure defaults.',
        status: 'completed',
        baselineScore: 52,
        advancedScore: 89,
        improvement: 37,
      },
      {
        id: 'case-10',
        name: 'Case 10 — Mixed difficult case',
        description: 'A repository combining several issue classes.',
        status: 'completed',
        baselineScore: 33,
        advancedScore: 77,
        improvement: 44,
      },
    ],
  },
];

export const DEMO_CHANGELOG: ChangelogEntry[] = [
  {
    id: 'cl-0',
    iteration: 'Baseline',
    title: 'Single-pass LLM review',
    whatChanged: 'Sent the whole repository to one model prompt.',
    whyChanged:
      'Establish a reference point for the simplest possible approach.',
    result:
      'Fast but produced unsupported claims and many false positives.',
    evidence: '34% of findings had no file:line evidence.',
    decision: 'kept',
    order: 0,
  },

  {
    id: 'cl-1',
    iteration: 'Iteration 1 — Better repository context',
    title: 'Structured repository indexing',
    whatChanged:
      'Indexed the repo into a file tree and sent scoped context per finding.',
    whyChanged: 'The model hallucinated files that did not exist.',
    result:
      'Fewer hallucinated references; evidence rate rose to 58%.',
    evidence:
      'eval-001 metrics: evidence-supported findings 34% -> 58%.',
    decision: 'kept',
    order: 1,
  },

  {
    id: 'cl-2',
    iteration: 'Iteration 2 — Evidence verification',
    title: 'Dedicated verification agent',
    whatChanged:
      'Added a verification step that reads the cited lines before accepting a finding.',
    whyChanged:
      'Findings still cited the wrong line numbers.',
    result: 'False positives dropped from 27% to 11%.',
    evidence:
      'eval-001 metrics: false positives 27% -> 11%.',
    decision: 'kept',
    order: 2,
  },

  {
    id: 'cl-3',
    iteration: 'Iteration 3 — Specialized agents',
    title: 'Role-specific analysis agents',
    whatChanged:
      'Split analysis into repository, code quality, testing, dependency, and verification agents.',
    whyChanged:
      'A single prompt missed category-specific signals.',
    result:
      'Critical issue detection rose from 40% to 85%.',
    evidence:
      'eval-001 metrics: critical detection 40% -> 85%.',
    decision: 'kept',
    order: 3,
  },

  {
    id: 'cl-4',
    iteration: 'Final — Combined workflow',
    title: 'Judge agent + evidence-first report',
    whatChanged:
      'A judge agent reconciles agent outputs into the final report with per-finding evidence.',
    whyChanged:
      'Findings needed a single reconciled assessment and confidence score.',
    result:
      'Advanced overall score reached 88% vs baseline 61%.',
    evidence:
      'eval-001 overall: baseline 61% -> advanced 88%.',
    decision: 'kept',
    order: 4,
  },
];

export const DEMO_TRAJECTORIES: Trajectory[] = [
  {
    id: '00000000-0000-0000-0030-000000000001',
    analysis_run_id:
      '00000000-0000-0000-0010-000000000001',
    step_number: 0,
    event_type: 'analysis_started',
    tool_name: null,
    input_data: {
      agent_type: 'code_quality',
    },
    output_data: null,
    observation:
      'Code Quality Agent started analysis of the repository.',
    created_at: '2026-08-24T10:12:07Z',
  },

  {
    id: '00000000-0000-0000-0030-000000000002',
    analysis_run_id:
      '00000000-0000-0000-0010-000000000001',
    step_number: 1,
    event_type: 'repository_inspected',
    tool_name: 'list_files',
    input_data: {
      path: 'src/',
    },
    output_data: {
      count: 142,
      directories: 18,
    },
    observation:
      'Returned 142 files across 18 directories.',
    created_at: '2026-08-24T10:12:09Z',
  },

  {
    id: '00000000-0000-0000-0030-000000000003',
    analysis_run_id:
      '00000000-0000-0000-0010-000000000001',
    step_number: 2,
    event_type: 'repository_inspected',
    tool_name: 'read_file',
    input_data: {
      file: 'src/auth/login.ts',
    },
    output_data: {
      lines: 120,
    },
    observation:
      'Read src/auth/login.ts and inspected the authentication implementation.',
    created_at: '2026-08-24T10:12:11Z',
  },

  {
    id: '00000000-0000-0000-0030-000000000004',
    analysis_run_id:
      '00000000-0000-0000-0010-000000000001',
    step_number: 3,
    event_type: 'security_scan_completed',
    tool_name: null,
    input_data: null,
    output_data: {
      finding_count: 8,
      evidence_count: 31,
    },
    observation:
      'Authentication logic was identified as a duplication candidate.',
    created_at: '2026-08-24T10:12:16Z',
  },

  {
    id: '00000000-0000-0000-0030-000000000005',
    analysis_run_id:
      '00000000-0000-0000-0010-000000000001',
    step_number: 4,
    event_type: 'analysis_completed',
    tool_name: null,
    input_data: null,
    output_data: {
      findings: 8,
      evidence_refs: 31,
      confidence: 0.91,
    },
    observation:
      'Analysis completed with 8 findings and 31 evidence references.',
    created_at: '2026-08-24T10:12:25Z',
  },

  {
    id: '00000000-0000-0000-0030-000000000006',
    analysis_run_id:
      '00000000-0000-0000-0010-000000000001',
    step_number: 5,
    event_type: 'analysis_started',
    tool_name: 'read_file',
    input_data: {
      file: 'src/auth/login.ts',
      start: 42,
      end: 67,
    },
    output_data: {
      lines: '42-67',
    },
    observation:
      'Verification Agent inspected the cited authentication code.',
    created_at: '2026-08-24T10:12:46Z',
  },

  {
    id: '00000000-0000-0000-0030-000000000007',
    analysis_run_id:
      '00000000-0000-0000-0010-000000000001',
    step_number: 6,
    event_type: 'analysis_completed',
    tool_name: null,
    input_data: null,
    output_data: {
      verified_evidence: 17,
      partial_evidence: 1,
    },
    observation:
      'Verification confirmed that the cited code supports the duplication finding.',
    created_at: '2026-08-24T10:12:56Z',
  },
];

export const DEMO_ARCHITECTURE = {
  technologies: [
    'Next.js',
    'Express',
    'PostgreSQL',
    'Redis',
    'TypeScript',
  ],

  layers: [
    { name: 'Frontend', module: 'web' },
    { name: 'API Layer', module: 'api' },
    { name: 'Services', module: 'services' },
    { name: 'Database', module: 'db' },
  ],

  modules: [
    {
      id: 'mod-auth',
      name: 'auth',
      layer: 'Services',
      files: [
        'src/auth/login.ts',
        'src/middleware/auth.ts',
      ],
      responsibilities: [
        'Token validation',
        'Session management',
      ],
      dependencies: ['db', 'redis'],
      findings: ['find-001'],
    },

    {
      id: 'mod-payments',
      name: 'payments',
      layer: 'Services',
      files: ['src/services/payments.ts'],
      responsibilities: [
        'Charge processing',
        'Refund handling',
      ],
      dependencies: ['db', 'auth'],
      findings: [],
    },

    {
      id: 'mod-api',
      name: 'api',
      layer: 'API Layer',
      files: [
        'src/server/index.ts',
        'src/server/errorHandler.ts',
      ],
      responsibilities: [
        'Routing',
        'Error handling',
      ],
      dependencies: ['auth', 'payments'],
      findings: ['find-002'],
    },
  ],

  risks: [
    'Circular dependency between auth and payments modules.',
    'Error handler leaks stack traces in non-production environments.',
  ],
};

export const DEMO_TESTING = {
  framework: 'Jest',
  testFiles: 58,
  testSuites: 24,
  passed: 312,
  failed: 3,
  coverage: 65,
  coverageSource: 'estimated' as const,

  categories: [
    { name: 'Unit', count: 180 },
    { name: 'Integration', count: 96 },
    { name: 'E2E', count: 36 },
  ],

  missingAreas: [
    'Payment refund flow (partial and failed refunds)',
    'Websocket reconnection logic',
    'Rate limiter edge cases',
  ],

  executionStatus: 'completed' as const,
};

export const DEMO_DEPENDENCIES = {
  total: 84,
  direct: 32,
  dev: 52,
  outdated: 7,
  conflicts: 1,

  packages: [
    {
      package: 'express',
      version: '4.18.2',
      type: 'prod',
      status: 'ok',
      risk: 'low',
    },
    {
      package: 'lodash',
      version: '4.17.20',
      type: 'prod',
      status: 'outdated',
      risk: 'high',
    },
    {
      package: 'react',
      version: '18.2.0',
      type: 'prod',
      status: 'ok',
      risk: 'low',
    },
    {
      package: 'zod',
      version: '3.21.0',
      type: 'prod',
      status: 'ok',
      risk: 'low',
    },
    {
      package: 'jest',
      version: '29.0.0',
      type: 'dev',
      status: 'ok',
      risk: 'low',
    },
    {
      package: 'eslint',
      version: '8.40.0',
      type: 'dev',
      status: 'outdated',
      risk: 'medium',
    },
    {
      package: 'axios',
      version: '1.4.0',
      type: 'prod',
      status: 'ok',
      risk: 'low',
    },
    {
      package: 'redis',
      version: '4.5.0',
      type: 'prod',
      status: 'ok',
      risk: 'low',
    },
    {
      package: 'bcrypt',
      version: '5.0.1',
      type: 'prod',
      status: 'ok',
      risk: 'low',
    },
    {
      package: 'typescript',
      version: '5.0.0',
      type: 'dev',
      status: 'outdated',
      risk: 'low',
    },
  ],
};

export type DemoArchitecture = typeof DEMO_ARCHITECTURE;
export type DemoTesting = typeof DEMO_TESTING;
export type DemoDependencies = typeof DEMO_DEPENDENCIES;

