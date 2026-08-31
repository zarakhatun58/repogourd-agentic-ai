
'use client';

import Link from 'next/link';
import { Plus, ChevronRight } from 'lucide-react';

import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { PageHeader } from '@/components/page-header';
import { DemoIndicator } from '@/components/demo-indicator';
import {
  LoadingState,
  ErrorState,
  EmptyState,
} from '@/components/state-views';

import type { Analysis } from '@/src/types';

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

import { api, DEMO_MODE } from '@/src/lib/api';
import { useAsyncData } from '@/src/hooks/use-async-data';

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

export default function AuditsPage() {
  const {
    data: analyses,
    loading,
    error,
    refetch,
  } = useAsyncData<Analysis[]>(
    () => api.listAnalyses(),
    []
  );

  return (
    <div className="mx-auto max-w-7xl space-y-8 p-4 md:p-8">
      <PageHeader
        title="Audits"
        subtitle="All engineering analysis runs across your repositories."
        showDemo={DEMO_MODE}
        actions={
          <Link href="/new-audit">
            <Button size="sm">
              <Plus className="mr-2 h-4 w-4" />
              New Audit
            </Button>
          </Link>
        }
      />

      {loading ? (
        <LoadingState
          message="Loading analyses…"
          rows={4}
        />
      ) : error ? (
        <ErrorState
          message="Unable to load analyses"
          description={error}
          onRetry={refetch}
        />
      ) : !analyses || analyses.length === 0 ? (
        <EmptyState
          title="No analyses yet"
          description="Start a new audit to create an analysis run."
          action={
            <Link href="/new-audit">
              <Button size="sm">
                New Audit
              </Button>
            </Link>
          }
        />
      ) : (
        <Card>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Repository ID</TableHead>

                <TableHead>
                  Agent
                </TableHead>

                <TableHead>
                  Status
                </TableHead>

                <TableHead className="hidden md:table-cell">
                  Commit
                </TableHead>

                <TableHead className="hidden lg:table-cell">
                  Started
                </TableHead>

                <TableHead className="hidden md:table-cell">
                  Created
                </TableHead>

                <TableHead className="text-right">
                  Action
                </TableHead>
              </TableRow>
            </TableHeader>

            <TableBody>
              {analyses.map((analysis) => (
                <TableRow key={analysis.id}>
                  {/* Repository */}
                  <TableCell className="font-medium">
                    <code className="text-xs">
                      {analysis.repository_id}
                    </code>
                  </TableCell>

                  {/* Agent */}
                  <TableCell>
                    {analysis.agent_type ?? '—'}
                  </TableCell>

                  {/* Status */}
                  <TableCell>
                    <span className="inline-flex items-center gap-1.5 text-sm capitalize">
                      <span
                        className={`h-1.5 w-1.5 rounded-full ${
                          analysis.status === 'completed'
                            ? 'bg-success'
                            : analysis.status === 'failed'
                              ? 'bg-destructive'
                              : 'bg-warning'
                        }`}
                      />

                      {analysis.status}
                    </span>
                  </TableCell>

                  {/* Commit */}
                  <TableCell className="hidden md:table-cell">
                    {analysis.commit_sha ? (
                      <code className="rounded bg-muted px-2 py-1 text-xs font-mono">
                        {analysis.commit_sha.slice(0, 8)}
                      </code>
                    ) : (
                      '—'
                    )}
                  </TableCell>

                  {/* Started */}
                  <TableCell className="hidden lg:table-cell text-muted-foreground">
                    {analysis.started_at
                      ? formatDate(analysis.started_at)
                      : '—'}
                  </TableCell>

                  {/* Created */}
                  <TableCell className="hidden md:table-cell text-muted-foreground">
                    {formatDate(analysis.created_at)}
                  </TableCell>

                  {/* Action */}
                  <TableCell className="text-right">
                    <Link href={`/audits/${analysis.id}`}>
                      <Button
                        variant="ghost"
                        size="sm"
                      >
                        View Report
                        <ChevronRight className="ml-1 h-4 w-4" />
                      </Button>
                    </Link>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}

      {DEMO_MODE && !loading && !error && (
        <div className="flex items-center justify-center">
          <DemoIndicator />
        </div>
      )}
    </div>
  );
}

