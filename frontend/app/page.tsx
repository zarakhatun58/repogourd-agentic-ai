'use client';

import Link from 'next/link';
import {
  GitBranch,
  ClipboardCheck,
  Gauge,
  ShieldCheck,
  ArrowRight,
  BarChart3,
  ChevronRight,
} from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { PageHeader } from '@/components/page-header';
import { RiskBadge } from '@/components/severity-badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { LoadingState, ErrorState, EmptyState } from '@/components/state-views';

import { api, DEMO_MODE } from '@/src/lib/api';
import { useAsyncData } from '@/src/hooks/use-async-data';
import type { Analysis } from '@/src/types';

const STATS = [
  { label: 'Repositories Analyzed', value: '24', icon: GitBranch, color: 'text-info' },
  { label: 'Audits Completed', value: '41', icon: ClipboardCheck, color: 'text-success' },
  { label: 'Average Quality Score', value: '82/100', icon: Gauge, color: 'text-warning' },
  { label: 'Evidence-backed Findings', value: '94%', icon: ShieldCheck, color: 'text-info' },
];

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

export default function DashboardPage() {
 const { data: analyses, loading, error, refetch } = useAsyncData<Analysis[]>(
  () => api.listAnalyses(),
  []
);

  return (
    <div className="mx-auto max-w-7xl space-y-8 p-4 md:p-8">
      <PageHeader
        title="RepoGuard AI"
        subtitle="Evidence-backed software engineering audits."
        showDemo={DEMO_MODE}
        actions={
          <>
            <Link href="/new-audit">
              <Button size="sm">Start New Audit</Button>
            </Link>
            <Link href="/evaluation">
              <Button variant="outline" size="sm">
                <BarChart3 className="mr-2 h-4 w-4" />
                View Evaluation
              </Button>
            </Link>
          </>
        }
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {STATS.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.label}>
              <CardContent className="flex items-center justify-between p-5">
                <div className="space-y-1">
                  <p className="text-xs text-muted-foreground">{stat.label}</p>
                  <p className="text-2xl font-bold tabular-nums">{stat.value}</p>
                </div>
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
                  <Icon className={`h-5 w-5 ${stat.color}`} />
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Recent Audits</h3>
          <Link
            href="/audits"
            className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
          >
            View all
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        {loading ? (
          <LoadingState message="Loading audits…" rows={4} />
        ) : error ? (
          <ErrorState message="Unable to load audits" description={error} onRetry={refetch} />
        ) : !analyses || analyses.length === 0 ? (
          <EmptyState
            title="No audits yet"
            description="Start a new audit to see results here."
            action={
              <Link href="/new-audit">
                <Button size="sm">Start New Audit</Button>
              </Link>
            }
          />
        ) : (
          <Card>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Analysis ID</TableHead>
                  <TableHead>Repository ID</TableHead>
                  <TableHead>Agent</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="hidden md:table-cell">
                    Commit
                  </TableHead>
                  <TableHead className="hidden lg:table-cell">
                    Created
                  </TableHead>
                  <TableHead className="hidden xl:table-cell">
                    Completed
                  </TableHead>
                  <TableHead className="text-right">
                    Action
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {analyses.map((analysis: any) => (
                  <TableRow key={analysis.id}>
                    <TableCell className="font-medium">
                      <span className="font-mono text-xs">
                        {analysis.id.slice(0, 8)}...
                      </span>
                    </TableCell>

                    <TableCell>
                      <span className="font-mono text-xs">
                        {analysis.repository_id.slice(0, 8)}...
                      </span>
                    </TableCell>

                    <TableCell>
                      <span className="text-sm">
                        {analysis.agent_type || '—'}
                      </span>
                    </TableCell>

                    <TableCell>
                      <span
                        className={`inline-flex items-center gap-1.5 text-sm capitalize ${analysis.status === 'completed'
                          ? 'text-success'
                          : analysis.status === 'failed'
                            ? 'text-destructive'
                            : analysis.status === 'running'
                              ? 'text-warning'
                              : 'text-muted-foreground'
                          }`}
                      >
                        <span className="h-1.5 w-1.5 rounded-full bg-current" />
                        {analysis.status}
                      </span>
                    </TableCell>

                    <TableCell className="hidden md:table-cell">
                      <span className="font-mono text-xs">
                        {analysis.commit_sha
                          ? `${analysis.commit_sha.slice(0, 8)}...`
                          : '—'}
                      </span>
                    </TableCell>

                    <TableCell className="hidden lg:table-cell text-muted-foreground">
                      {formatDate(analysis.created_at)}
                    </TableCell>

                    <TableCell className="hidden xl:table-cell text-muted-foreground">
                      {formatDate(analysis.completed_at)}
                    </TableCell>

                    <TableCell className="text-right">
                      <Link href={`/analysis/${analysis.id}`}>
                        <Button variant="ghost" size="sm">
                          View
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
      </div>
    </div>
  );
}
