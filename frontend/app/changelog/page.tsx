
'use client';

import {
  GitCommitVertical,
  Check,
  RotateCcw,
  Trash2,
} from 'lucide-react';

import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/page-header';
import {
  EmptyState,
  ErrorState,
  LoadingState,
} from '@/components/state-views';

import { api, DEMO_MODE } from '@/src/lib/api';
import { useAsyncData } from '@/src/hooks/use-async-data';

import type {
  ChangelogDecision,
  ChangelogEntry,
} from '@/src/types';

const DECISION_STYLES: Record<
  ChangelogDecision,
  {
    className: string;
    icon: React.ReactNode;
  }
> = {
  kept: {
    className: 'border-success/30 text-success',
    icon: <Check className="h-3 w-3" />,
  },
  revised: {
    className: 'border-warning/30 text-warning',
    icon: <RotateCcw className="h-3 w-3" />,
  },
  removed: {
    className: 'border-destructive/30 text-destructive',
    icon: <Trash2 className="h-3 w-3" />,
  },
};

export default function ChangelogPage() {
  const {
    data: changelog,
    loading,
    error,
    refetch,
  } = useAsyncData<ChangelogEntry[]>(
    () => api.getChangelog(),
    [],
    []
  );

  if (loading) {
    return (
      <div className="mx-auto max-w-4xl space-y-8 p-4 md:p-8">
        <PageHeader
          title="Improvement Changelog"
          subtitle="How the workflow evolved from baseline to the final combined solution."
          showDemo={DEMO_MODE}
        />

        <LoadingState
          message="Loading changelog…"
          rows={5}
        />
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-4xl space-y-8 p-4 md:p-8">
        <PageHeader
          title="Improvement Changelog"
          subtitle="How the workflow evolved from baseline to the final combined solution."
          showDemo={DEMO_MODE}
        />

        <ErrorState
          message="Unable to load changelog"
          description={error}
          onRetry={refetch}
        />
      </div>
    );
  }

  const entries = changelog ?? [];

  if (entries.length === 0) {
    return (
      <div className="mx-auto max-w-4xl space-y-8 p-4 md:p-8">
        <PageHeader
          title="Improvement Changelog"
          showDemo={DEMO_MODE}
        />

        <EmptyState title="No changelog entries yet." />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-8 p-4 md:p-8">
      <PageHeader
        title="Improvement Changelog"
        subtitle="How the workflow evolved from baseline to the final combined solution."
        showDemo={DEMO_MODE}
      />

      <div className="relative">
        <div className="absolute left-4 top-0 bottom-0 w-px bg-border" />

        <div className="space-y-6">
          {entries.map((entry) => {
            const decision =
              DECISION_STYLES[entry.decision];

            return (
              <div
                key={entry.id}
                className="relative pl-12"
              >
                <div className="absolute left-0 flex h-8 w-8 items-center justify-center rounded-full border-2 border-border bg-card">
                  <GitCommitVertical className="h-4 w-4 text-muted-foreground" />
                </div>

                <Card>
                  <CardContent className="space-y-3 p-5">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <p className="text-xs text-muted-foreground">
                          {entry.iteration}
                        </p>

                        <h4 className="font-semibold">
                          {entry.title}
                        </h4>
                      </div>

                      <Badge
                        variant="outline"
                        className={`gap-1 capitalize ${decision?.className ?? ''}`}
                      >
                        {decision?.icon}
                        {entry.decision}
                      </Badge>
                    </div>

                    <div className="grid gap-3 sm:grid-cols-2">
                      <div>
                        <p className="text-xs font-medium text-muted-foreground">
                          What changed
                        </p>

                        <p className="text-sm">
                          {entry.whatChanged}
                        </p>
                      </div>

                      <div>
                        <p className="text-xs font-medium text-muted-foreground">
                          Why it changed
                        </p>

                        <p className="text-sm">
                          {entry.whyChanged}
                        </p>
                      </div>

                      <div>
                        <p className="text-xs font-medium text-muted-foreground">
                          Result
                        </p>

                        <p className="text-sm">
                          {entry.result}
                        </p>
                      </div>

                      <div>
                        <p className="text-xs font-medium text-muted-foreground">
                          Evidence
                        </p>

                        <p className="text-xs font-mono">
                          {entry.evidence}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

