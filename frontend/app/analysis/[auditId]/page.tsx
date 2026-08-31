
'use client';

import Link from 'next/link';
import {
  GitBranch,
  FileCode,
  TestTube,
  Package,
  ShieldCheck,
  Gavel,
  Clock,
  FileText,
  Database,
  ChevronRight,
  ArrowLeft,
  Play,
  RefreshCw,
} from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { PageHeader } from '@/components/page-header';
import {
  LoadingState,
  ErrorState,
} from '@/components/state-views';

import {

  api,
} from '@/src/lib/api';


import type {
  AgentType,
  AgentRun,
  Analysis,
  Repository,
} from '@/src/types';

import { useAsyncData } from '@/src/hooks/use-async-data';

const AGENT_ICONS: Record<
  AgentType,
  React.ComponentType<{ className?: string }>
> = {
  repository: GitBranch,
  code_quality: FileCode,
  testing: TestTube,
  dependency: Package,
  verification: ShieldCheck,
  judge: Gavel,
};

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function formatDate(iso: string | null): string {
  if (!iso) return '—';

  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function AgentCard({
  agent,
}: {
  agent: AgentRun;
}) {
  const Icon = AGENT_ICONS[agent.agentType];

  return (
    <Card className="transition-colors hover:border-primary/30">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-muted">
              <Icon className="h-4 w-4" />
            </div>

            <div>
              <CardTitle className="text-sm">
                {agent.name}
              </CardTitle>

              <p className="text-xs text-muted-foreground">
                {agent.description}
              </p>
            </div>
          </div>

          <span
            className={`inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs font-medium capitalize ${agent.status === 'completed'
                ? 'bg-success/15 text-success'
                : agent.status === 'running'
                  ? 'bg-info/15 text-info'
                  : agent.status === 'failed'
                    ? 'bg-destructive/15 text-destructive'
                    : 'bg-muted text-muted-foreground'
              }`}
          >
            <span
              className={`h-1.5 w-1.5 rounded-full ${agent.status === 'completed'
                  ? 'bg-success'
                  : agent.status === 'running'
                    ? 'bg-info animate-pulse'
                    : agent.status === 'failed'
                      ? 'bg-destructive'
                      : 'bg-muted-foreground'
                }`}
            />

            {agent.status}
          </span>
        </div>
      </CardHeader>

      <CardContent className="grid grid-cols-3 gap-3 pt-0">
        <div className="flex items-center gap-2 text-sm">
          <Clock className="h-3.5 w-3.5 text-muted-foreground" />
          <span className="tabular-nums">
            {formatDuration(agent.durationMs)}
          </span>
        </div>

        <div className="flex items-center gap-2 text-sm">
          <FileText className="h-3.5 w-3.5 text-muted-foreground" />
          <span className="tabular-nums">
            {agent.findingsCount} findings
          </span>
        </div>

        <div className="flex items-center gap-2 text-sm">
          <Database className="h-3.5 w-3.5 text-muted-foreground" />
          <span className="tabular-nums">
            {agent.evidenceCount} evidence
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
export default function AnalysisPage({
  params,
}: {
  params: { auditId: string };
}) {
  const { auditId } = params;

  const {
    data: analysis,
    loading: analysisLoading,
    error: analysisError,
    refetch: refetchAnalysis,
  } = useAsyncData<Analysis | null>(
    () => api.getAnalysis(auditId),
    null,
    [auditId]
  );

  const {
    data: repository,
    loading: repositoryLoading,
    error: repositoryError,
  } = useAsyncData<Repository | null>(
    async () => {
      if (!analysis?.repository_id) {
        return null;
      }

      return api.getRepository(analysis.repository_id);
    },
    null,
    [analysis?.repository_id]
  );

  if (analysisLoading) {
    return (
      <div className="mx-auto max-w-7xl p-4 md:p-8">
        <LoadingState message="Loading analysis..." rows={4} />
      </div>
    );
  }

  if (analysisError || !analysis) {
    return (
      <div className="mx-auto max-w-4xl space-y-8 p-4 md:p-8">
        <ErrorState
          message="Unable to load analysis"
          description={analysisError || `Analysis ${auditId} was not found.`}
          onRetry={refetchAnalysis}
        />
      </div>
    );
  }

  const repoName =
    repository?.name || `Repository ${analysis.repository_id}`;

  const branch = repository?.default_branch || '—';
  const sourceUrl = repository?.source_url || '—';

  return (
    <div className="mx-auto max-w-7xl space-y-8 p-4 md:p-8">
      <div className="flex items-center gap-3">
        <Link href="/audits">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
        </Link>

        <Button variant="outline" size="sm" onClick={refetchAnalysis}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      <PageHeader
        title="Analysis"
        subtitle={repoName}
        showDemo={false}
      />

      {repositoryError && (
        <div className="rounded-lg border border-dashed p-3 text-sm text-muted-foreground">
          Repository details could not be loaded.
        </div>
      )}

      {repositoryLoading && (
        <div className="rounded-lg border border-dashed p-3 text-sm text-muted-foreground">
          Loading repository details...
        </div>
      )}

      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-muted-foreground">Repository</p>
            <p className="mt-1 truncate text-sm font-semibold">{repoName}</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-muted-foreground">Branch</p>
            <p className="mt-1 truncate text-sm font-semibold">{branch}</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-muted-foreground">Commit</p>
            <p className="mt-1 truncate text-sm font-semibold">
              {analysis.commit_sha || '—'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-muted-foreground">Source</p>
            <p className="mt-1 truncate text-sm font-semibold">{sourceUrl}</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-muted-foreground">Agent</p>
            <p className="mt-1 truncate text-sm font-semibold">
              {analysis.agent_type || '—'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-muted-foreground">Status</p>
            <p className="mt-1 text-sm font-semibold capitalize">
              {analysis.status || '—'}
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Analysis Status</CardTitle>
        </CardHeader>

        <CardContent>
          <div className="flex flex-wrap items-center gap-4">
            <span
              className={`inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium ${
                analysis.status === 'completed'
                  ? 'bg-success/15 text-success'
                  : analysis.status === 'running'
                    ? 'bg-info/15 text-info'
                    : analysis.status === 'failed'
                      ? 'bg-destructive/15 text-destructive'
                      : 'bg-muted text-muted-foreground'
              }`}
            >
              <span
                className={`h-2 w-2 rounded-full ${
                  analysis.status === 'completed'
                    ? 'bg-success'
                    : analysis.status === 'running'
                      ? 'bg-info animate-pulse'
                      : analysis.status === 'failed'
                        ? 'bg-destructive'
                        : 'bg-muted-foreground'
                }`}
              />
              {analysis.status}
            </span>

            {analysis.error_message && (
              <p className="text-sm text-destructive">
                {analysis.error_message}
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold">Analysis Details</h3>
            <p className="text-sm text-muted-foreground">
              Analysis ID: {analysis.id}
            </p>
          </div>

          <Link href={`/audits/${analysis.id}`}>
            <Button variant="outline" size="sm">
              View Report
              <ChevronRight className="ml-1 h-4 w-4" />
            </Button>
          </Link>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground">Repository ID</p>
              <p className="mt-1 break-all text-sm font-semibold">
                {analysis.repository_id}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground">Analysis ID</p>
              <p className="mt-1 break-all text-sm font-semibold">
                {analysis.id}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground">Started</p>
              <p className="mt-1 text-sm font-semibold">
                {analysis.started_at
                  ? new Date(analysis.started_at).toLocaleString()
                  : '—'}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground">Completed</p>
              <p className="mt-1 text-sm font-semibold">
                {analysis.completed_at
                  ? new Date(analysis.completed_at).toLocaleString()
                  : '—'}
              </p>
            </CardContent>
          </Card>
        </div>
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Agent Workflow</h3>

          <Link href={`/audits/${analysis.id}`}>
            <Button variant="outline" size="sm">
              View Report
              <ChevronRight className="ml-1 h-4 w-4" />
            </Button>
          </Link>
        </div>

        <div className="rounded-lg border border-dashed p-6 text-center">
          <p className="text-sm text-muted-foreground">
            Analysis status: {analysis.status}
          </p>

          {analysis.completed_at && (
            <p className="mt-1 text-xs text-muted-foreground">
              Completed at {new Date(analysis.completed_at).toLocaleString()}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
