
'use client';

import { use, useMemo } from 'react';
import Link from 'next/link';
import {
  ArrowLeft,
  CheckCircle2,
  Clock,
  FileSearch,
  Lightbulb,
  MessageSquare,
  Search,
  ShieldCheck,
  Wrench,
} from 'lucide-react';

import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/page-header';
import { EmptyState, ErrorState, LoadingState } from '@/components/state-views';
import { cn } from '@/src/lib/utils';

import { api , DEMO_MODE} from '@/src/lib/api';
import { useAsyncData } from '@/src/hooks/use-async-data';

import type { Trajectory } from '@/src/types';

const STEP_ICONS: Record<string, React.ReactNode> = {
  analysis_started: (
    <MessageSquare className="h-3.5 w-3.5" />
  ),

  repository_inspection_started: (
    <Search className="h-3.5 w-3.5" />
  ),

  repository_inspected: (
    <Search className="h-3.5 w-3.5" />
  ),

  security_scan_started: (
    <ShieldCheck className="h-3.5 w-3.5" />
  ),

  findings_generated: (
    <FileSearch className="h-3.5 w-3.5" />
  ),

  evidence_collected: (
    <FileSearch className="h-3.5 w-3.5" />
  ),

  analysis_completed: (
    <CheckCircle2 className="h-3.5 w-3.5" />
  ),

  analysis_failed: (
    <Wrench className="h-3.5 w-3.5" />
  ),
};

const STEP_COLORS: Record<string, string> = {
  analysis_started:
    'bg-info/10 text-info',

  repository_inspection_started:
    'bg-warning/10 text-warning',

  repository_inspected:
    'bg-warning/10 text-warning',

  security_scan_started:
    'bg-destructive/10 text-destructive',

  findings_generated:
    'bg-primary/10 text-primary',

  evidence_collected:
    'bg-success/10 text-success',

  analysis_completed:
    'bg-success/10 text-success',

  analysis_failed:
    'bg-destructive/10 text-destructive',
};

function getStepIcon(eventType: string) {
  return (
    STEP_ICONS[eventType] ?? (
      <FileSearch className="h-3.5 w-3.5" />
    )
  );
}

function getStepColor(eventType: string) {
  return (
    STEP_COLORS[eventType] ??
    'bg-muted text-muted-foreground'
  );
}

function formatEventType(eventType: string) {
  return eventType
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatJson(
  value: Record<string, unknown> | null
) {
  if (!value) {
    return null;
  }

  return JSON.stringify(value, null, 2);
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

function calculateDuration(trajectory: Trajectory[]) {
  if (trajectory.length < 2) {
    return 0;
  }

  const first = new Date(
    trajectory[0].created_at
  ).getTime();

  const last = new Date(
    trajectory[trajectory.length - 1].created_at
  ).getTime();

  return Math.max(0, last - first);
}

function formatDuration(ms: number) {
  if (ms < 1000) {
    return `${ms}ms`;
  }

  return `${(ms / 1000).toFixed(1)}s`;
}

export default function TrajectoriesPage({
  params,
}: {
  params: { analysisId: string };
}) {
  const { analysisId } = params;

  const {
    data: trajectory,
    loading,
    error,
    refetch,
  } = useAsyncData<Trajectory[]>(
    () => api.getTrajectories(analysisId),
    []
  );

  const sortedTrajectory = useMemo(() => {
    if (!trajectory) {
      return [];
    }

    return [...trajectory].sort(
      (a, b) => a.step_number - b.step_number
    );
  }, [trajectory]);

  const duration = useMemo(
    () => calculateDuration(sortedTrajectory),
    [sortedTrajectory]
  );

  if (loading) {
    return (
      <div className="mx-auto max-w-5xl space-y-8 p-4 md:p-8">
        <PageHeader
          title="Agent Trajectory"
          subtitle={`Execution trace for analysis ${analysisId}`}
          showDemo={DEMO_MODE}
        />

        <LoadingState
          message="Loading trajectory…"
          rows={5}
        />
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-5xl space-y-8 p-4 md:p-8">
        <ErrorState
          message="Unable to load trajectory"
          description={error}
          onRetry={refetch}
        />
      </div>
    );
  }

  if (!sortedTrajectory.length) {
    return (
      <div className="mx-auto max-w-5xl space-y-8 p-4 md:p-8">
        <Link href="/audits">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Audits
          </Button>
        </Link>

        <PageHeader
          title="Agent Trajectory"
          subtitle={`Execution trace for analysis ${analysisId}`}
          showDemo={DEMO_MODE}
        />

        <EmptyState
          title="No trajectory available"
          description="This analysis has not produced any execution trace yet."
        />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl space-y-8 p-4 md:p-8">
      <div className="flex items-center justify-between">
        <Link href="/audits">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Audits
          </Button>
        </Link>
      </div>

      <PageHeader
        title="Agent Trajectory"
        subtitle={`Execution trace for analysis ${analysisId}`}
        showDemo={DEMO_MODE}
      />

      <Card>
        <CardContent className="flex items-center justify-between p-5">
          <div>
            <p className="font-semibold">
              RepoGuard Agent
            </p>

            <p className="text-sm text-muted-foreground">
              {sortedTrajectory.length} execution steps
            </p>
          </div>

          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Clock className="h-4 w-4" />
            {formatDuration(duration)}
          </div>
        </CardContent>
      </Card>

      <div className="relative">
        <div className="absolute left-4 top-0 bottom-0 w-px bg-border" />

        <div className="space-y-3">
          {sortedTrajectory.map((step) => {
            const input = formatJson(step.input_data);
            const output = formatJson(step.output_data);

            return (
              <div
                key={step.id}
                className="relative pl-12"
              >
                <div
                  className={cn(
                    'absolute left-0 flex h-8 w-8 items-center justify-center rounded-full border-2 border-border',
                    getStepColor(step.event_type)
                  )}
                >
                  {getStepIcon(step.event_type)}
                </div>

                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <Badge
                          variant="outline"
                          className={cn(
                            'text-xs',
                            getStepColor(step.event_type)
                          )}
                        >
                          Step {step.step_number}
                        </Badge>

                        <Badge
                          variant="outline"
                          className="text-xs"
                        >
                          {formatEventType(
                            step.event_type
                          )}
                        </Badge>
                      </div>

                      <span className="text-xs text-muted-foreground">
                        {formatTime(step.created_at)}
                      </span>
                    </div>

                    <p className="mt-3 text-sm font-medium">
                      {step.observation}
                    </p>

                    {step.tool_name && (
                      <div className="mt-3">
                        <p className="text-xs font-medium text-muted-foreground">
                          Tool
                        </p>

                        <code className="mt-1 inline-block rounded bg-muted px-2 py-1 text-xs font-mono">
                          {step.tool_name}
                        </code>
                      </div>
                    )}

                    {input && (
                      <div className="mt-3 space-y-1">
                        <p className="text-xs font-medium text-muted-foreground">
                          Input
                        </p>

                        <pre className="overflow-x-auto rounded bg-muted p-3 text-xs font-mono scrollbar-thin">
                          <code>{input}</code>
                        </pre>
                      </div>
                    )}

                    {output && (
                      <div className="mt-3 space-y-1">
                        <p className="text-xs font-medium text-muted-foreground">
                          Output
                        </p>

                        <pre className="overflow-x-auto rounded bg-muted p-3 text-xs font-mono scrollbar-thin">
                          <code>{output}</code>
                        </pre>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            );
          })}
        </div>
      </div>

      <p className="text-xs text-muted-foreground">
        Trajectories show user-facing execution information
        such as tools, observations, inputs, outputs, and
        analysis decisions. Hidden chain-of-thought is never
        displayed.
      </p>
    </div>
  );
}

