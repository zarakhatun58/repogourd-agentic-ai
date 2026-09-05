'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';
import {
  ArrowLeft,
  FileText,
  Layers,
  ArrowRight,
} from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet';

import { PageHeader } from '@/components/page-header';
import { ScoreRing, ScoreBar } from '@/components/score-display';
import { SeverityBadge, RiskBadge } from '@/components/severity-badge';
import { VerificationBadge } from '@/components/verification-badge';
import { CodeBlock } from '@/components/code-block';
import { ErrorState, LoadingState } from '@/components/state-views';

import {
  Tabs,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';

import type {
  Finding,
  FindingFilter,
  Evidence,
  Analysis,
} from '@/src/types';

import { useAsyncData } from '@/src/hooks/use-async-data';
import { api, DEMO_MODE } from '@/src/lib/api';

const CATEGORY_LABELS: Record<string, string> = {
  architecture: 'Architecture',
  code_quality: 'Code Quality',
  testing: 'Testing',
  dependencies: 'Dependencies',
  security: 'Security',
};

const FILTERS: FindingFilter[] = [
  'all',
  'critical',
  'high',
  'medium',
  'low',
];

function filterFindings(
  findings: Finding[],
  filter: FindingFilter
): Finding[] {
  if (filter === 'all') {
    return findings;
  }

  return findings.filter(
    (finding) => finding.severity === filter
  );
}
function calculateScore(findings: Finding[]): number {
  if (findings.length === 0) { return 100; }
  const weights: Record<string, number> =
    { critical: 20, high: 10, medium: 5, low: 2, };
  const deduction = findings.reduce((total, finding) =>
    total + (weights[finding.severity] ?? 0), 0);
  return Math.max(0, Math.min(100, 100 - deduction));
}

function getRiskLevel( score: number ): 'critical' | 'high' | 'medium' | 'low' { if (score < 40) return 'critical'; if (score < 60) return 'high'; if (score < 80) return 'medium'; return 'low'; }

function formatRepositoryName(
  repositoryId?: string
): string {
  if (!repositoryId) {
    return 'Repository';
  }

  return `Repository ${repositoryId.slice(0, 8)}`;
}

export default function AuditReportPage({
  params,
}: {
  params: { auditId: string };
}) {
  const { auditId } = params;

  const [filter, setFilter] =
    useState<FindingFilter>('all');

  const [selectedFinding, setSelectedFinding] =
    useState<Finding | null>(null);


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
    data: findings,
    loading: findingsLoading,
    error: findingsError,
    refetch: refetchFindings,
  } = useAsyncData<Finding[]>(
    () => api.getAnalysisFindings(auditId),
    [],
    [auditId]
  );

  const actualFindings = findings ?? [];

  const filtered = useMemo(
    () =>
      filterFindings(
        actualFindings,
        filter
      ),
    [actualFindings, filter]
  );

  const criticalFindings = actualFindings.filter(
    (finding) => finding.severity === 'critical'
  ).length;

  const highFindings = actualFindings.filter(
    (finding) => finding.severity === 'high'
  ).length;

  const mediumFindings = actualFindings.filter(
    (finding) => finding.severity === 'medium'
  ).length;

  const lowFindings = actualFindings.filter(
    (finding) => finding.severity === 'low'
  ).length;

  const totalFindings = actualFindings.length;

 const overallScore = useMemo( () => calculateScore(actualFindings), [actualFindings] ); 
 const riskLevel = getRiskLevel(overallScore);

  const [evidenceCache, setEvidenceCache] =
    useState<Record<string, Evidence[]>>({});

  const [evidenceLoading, setEvidenceLoading] =
    useState(false);

  const [evidenceError, setEvidenceError] =
    useState<string | null>(null);

  async function handleFindingClick(
    finding: Finding
  ) {
    setSelectedFinding(finding);
    setEvidenceError(null);

    if (evidenceCache[finding.id]) {
      return;
    }

    setEvidenceLoading(true);

    try {

      const evidence =
        await api.getEvidence(finding.id);

      setEvidenceCache((current) => ({
        ...current,
        [finding.id]: evidence,
      }));
    } catch (error) {
      setEvidenceError(
        error instanceof Error
          ? error.message
          : 'Unable to load evidence'
      );
    } finally {
      setEvidenceLoading(false);
    }


  }

  const findingsWithEvidence =
    Object.keys(evidenceCache).filter(
      (findingId) =>
        (evidenceCache[findingId]?.length ?? 0) > 0
    ).length;

  const evidenceCoverage =
    actualFindings.length === 0
      ? 0
      : Math.round(
        (findingsWithEvidence /
          actualFindings.length) *
        100
      );

  const isLoading =
    analysisLoading || findingsLoading;

  if (isLoading) {
    return (

      <div className="mx-auto max-w-7xl space-y-8 p-4 md:p-8">
        <LoadingState
          message="Loading audit report…"
          rows={4}
        />
      </div>

    );

  }

  if (analysisError || !analysis) {
    return (

      <div className="mx-auto max-w-4xl space-y-8 p-4 md:p-8">
        <ErrorState
          message="Unable to load audit"
          description={
            analysisError ??
            `Analysis ${auditId} was not found.`
          }
          onRetry={refetchAnalysis}
        />
      </div>
    );

  }

  const repositoryName =
    formatRepositoryName(
      analysis.repository_id
    );

  return (<div className="mx-auto max-w-7xl space-y-8 p-4 md:p-8">

    {/* Navigation */}
    <div className="flex items-center justify-between">
      <Link href="/audits">
        <Button
          variant="ghost"
          size="sm"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Audits
        </Button>
      </Link>

      <div className="flex gap-2">
        <Link
          href={`/architecture/${auditId}`}
        >
          <Button
            variant="outline"
            size="sm"
          >
            <Layers className="mr-2 h-4 w-4" />
            Architecture
          </Button>
        </Link>

        <Link
          href={`/testing/${auditId}`}
        >
          <Button
            variant="outline"
            size="sm"
          >
            Testing
          </Button>
        </Link>

        <Link
          href={`/dependencies/${auditId}`}
        >
          <Button
            variant="outline"
            size="sm"
          >
            Dependencies
          </Button>
        </Link>
      </div>
    </div>

    {/* Header */}
    <PageHeader
      title="Engineering Audit Report"
      subtitle={`Repository: ${repositoryName}`}
      showDemo={DEMO_MODE}
    />

    {/* Analysis information */}
    <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
      <Card>
        <CardContent className="p-4">
          <p className="text-xs text-muted-foreground">
            Analysis ID
          </p>
          <p className="mt-1 truncate font-mono text-xs">
            {analysis.id}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <p className="text-xs text-muted-foreground">
            Repository ID
          </p>
          <p className="mt-1 truncate font-mono text-xs">
            {analysis.repository_id}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <p className="text-xs text-muted-foreground">
            Agent
          </p>
          <p className="mt-1 text-sm font-semibold">
            {analysis.agent_type}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <p className="text-xs text-muted-foreground">
            Status
          </p>
          <p className="mt-1 text-sm font-semibold capitalize">
            {analysis.status}
          </p>
        </CardContent>
      </Card>
    </div>

    {/* Score + Finding Summary */}
    <div className="grid gap-6 lg:grid-cols-3">

      <Card className="lg:col-span-1">
        <CardContent className="flex flex-col items-center gap-4 p-6">

          <ScoreRing
            score={overallScore}
            size={140}
          />

          <RiskBadge
            risk={riskLevel}
          />

          <div className="grid w-full grid-cols-2 gap-3 text-center">

            <div className="rounded-lg bg-muted/50 p-3">
              <p className="text-xs text-muted-foreground">
                Evidence Coverage
              </p>

              <p className="text-lg font-bold tabular-nums">
                {findingsWithEvidence > 0
                  ? `${evidenceCoverage}%`
                  : totalFindings === 0
                    ? '0%'
                    : '—'}
              </p>
            </div>

            <div className="rounded-lg bg-muted/50 p-3">
              <p className="text-xs text-muted-foreground">
                Total Findings
              </p>

              <p className="text-lg font-bold tabular-nums">
                {totalFindings}
              </p>
            </div>

          </div>
        </CardContent>
      </Card>

      <Card className="lg:col-span-2">

        <CardHeader>
          <CardTitle className="text-base">
            Finding Summary
          </CardTitle>
        </CardHeader>

        <CardContent>
          <div className="grid grid-cols-4 gap-3">

            <div className="rounded-lg border p-4 text-center">
              <p className="text-2xl font-bold tabular-nums text-destructive">
                {criticalFindings}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                Critical
              </p>
            </div>

            <div className="rounded-lg border p-4 text-center">
              <p className="text-2xl font-bold tabular-nums text-destructive">
                {highFindings}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                High
              </p>
            </div>

            <div className="rounded-lg border p-4 text-center">
              <p className="text-2xl font-bold tabular-nums text-warning">
                {mediumFindings}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                Medium
              </p>
            </div>

            <div className="rounded-lg border p-4 text-center">
              <p className="text-2xl font-bold tabular-nums text-info">
                {lowFindings}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                Low
              </p>
            </div>

          </div>
        </CardContent>
      </Card>

    </div>
    {/* <Card>
      <CardHeader>
        <CardTitle className="text-base">
          Score Breakdown
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {analysis.category_scores?.map((cat) => (
          <div
            key={cat.category}
            className="space-y-1"
          >
            {cat.score === null ? (
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">
                  {CATEGORY_LABELS[cat.category] ??
                    cat.category}
                </span>

                <span className="text-xs text-muted-foreground">
                  Not available
                </span>
              </div>
            ) : (
              <ScoreBar
                label={
                  CATEGORY_LABELS[cat.category] ??
                  cat.category
                }
                score={cat.score}
                maxScore={cat.max_score}
              />
            )}
          </div>
        ))}

        {(!analysis.category_scores ||
          analysis.category_scores.length === 0) && (
            <p className="text-sm text-muted-foreground">
              Score breakdown is not available for this analysis.
            </p>
          )}
      </CardContent>
    </Card> */}
    {/* Analysis details */}
    <Card>
      <CardHeader>
        <CardTitle className="text-base">
          Analysis Details
        </CardTitle>
      </CardHeader>

      <CardContent>
        <div className="grid gap-4 md:grid-cols-3">

          <div>
            <p className="text-xs text-muted-foreground">
              Commit
            </p>
            <code className="mt-1 block text-xs">
              {analysis.commit_sha || '—'}
            </code>
          </div>

          <div>
            <p className="text-xs text-muted-foreground">
              Started
            </p>
            <p className="mt-1 text-sm">
              {analysis.started_at
                ? new Date(
                  analysis.started_at
                ).toLocaleString()
                : '—'}
            </p>
          </div>

          <div>
            <p className="text-xs text-muted-foreground">
              Completed
            </p>
            <p className="mt-1 text-sm">
              {analysis.completed_at
                ? new Date(
                  analysis.completed_at
                ).toLocaleString()
                : '—'}
            </p>
          </div>

        </div>
      </CardContent>
    </Card>

    {/* Findings */}
    <div className="space-y-4">

      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">
          Findings
        </h3>

        {findingsError && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetchFindings()}
          >
            Retry
          </Button>
        )}
      </div>

      {findingsError && (
        <ErrorState
          message="Unable to load findings"
          description={findingsError}
          onRetry={refetchFindings}
        />
      )}

      <Tabs
        value={filter}
        onValueChange={(value) =>
          setFilter(
            value as FindingFilter
          )
        }
      >
        <div className="overflow-x-auto scrollbar-thin">
          <TabsList>
            {FILTERS.map((item) => (
              <TabsTrigger
                key={item}
                value={item}
                className="capitalize"
              >
                {item}
              </TabsTrigger>
            ))}
          </TabsList>
        </div>
      </Tabs>

      <div className="space-y-3">

        {filtered.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center text-sm text-muted-foreground">
              {findingsLoading
                ? 'Loading findings…'
                : 'No findings match this filter.'}
            </CardContent>
          </Card>
        ) : (
          filtered.map((finding) => (
            <Card
              key={finding.id}
              className="cursor-pointer transition-colors hover:border-primary/30"
              onClick={() =>
                handleFindingClick(
                  finding
                )
              }
            >
              <CardContent className="p-5">

                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">

                  <div className="min-w-0 space-y-2">

                    <div className="flex flex-wrap items-center gap-2">

                      <SeverityBadge
                        severity={
                          finding.severity
                        }
                      />

                      <span className="rounded bg-muted px-2 py-0.5 text-xs font-mono text-muted-foreground">
                        {finding.rule_id}
                      </span>

                      <span className="rounded bg-muted px-2 py-0.5 text-xs capitalize text-muted-foreground">
                        {finding.status}
                      </span>

                    </div>

                    <h4 className="font-semibold">
                      {finding.title}
                    </h4>

                    <p className="text-sm text-muted-foreground">
                      {finding.description ||
                        'No description available.'}
                    </p>

                    {finding.file_path && (
                      <div className="pt-1">
                        <code className="max-w-full truncate rounded bg-muted px-2 py-0.5 text-xs font-mono text-muted-foreground">
                          {finding.file_path}

                          {finding.line_start !== null &&
                            `:${finding.line_start}`}

                          {finding.line_end !== null &&
                            finding.line_end !==
                            finding.line_start &&
                            `-${finding.line_end}`}
                        </code>
                      </div>
                    )}

                  </div>

                  <Button
                    variant="ghost"
                    size="sm"
                    className="shrink-0"
                    onClick={(event) => {
                      event.stopPropagation();
                      handleFindingClick(
                        finding
                      );
                    }}
                  >
                    Evidence
                    <ArrowRight className="ml-1 h-4 w-4" />
                  </Button>

                </div>

              </CardContent>
            </Card>
          ))
        )}

      </div>
    </div>

    {/* Evidence panel */}
    <Sheet
      open={!!selectedFinding}
      onOpenChange={(open) => {
        if (!open) {
          setSelectedFinding(null);
          setEvidenceError(null);
        }
      }}
    >
      <SheetContent
        side="right"
        className="w-full overflow-y-auto scrollbar-thin sm:max-w-lg"
      >
        {selectedFinding && (
          <EvidencePanel
            finding={selectedFinding}
            evidence={
              evidenceCache[
              selectedFinding.id
              ] ?? []
            }
            loading={evidenceLoading}
            error={evidenceError}
          />
        )}
      </SheetContent>
    </Sheet>

  </div>


  );
}

function EvidencePanel({
  finding,
  evidence,
  loading,
  error,
}: {
  finding: Finding;
  evidence: Evidence[];
  loading: boolean;
  error: string | null;
}) {
  return (<div className="space-y-6">

    <SheetHeader>
      <SheetTitle className="text-base">
        {finding.title}
      </SheetTitle>

      <SheetDescription>
        <div className="flex flex-wrap items-center gap-2 pt-1">

          <SeverityBadge
            severity={finding.severity}
          />

          <span className="rounded-md bg-muted px-2 py-1 text-xs capitalize">
            {finding.status}
          </span>

        </div>
      </SheetDescription>
    </SheetHeader>

    <div className="space-y-2">
      <h4 className="text-sm font-semibold">
        Finding
      </h4>

      <p className="text-sm text-muted-foreground">
        {finding.description ||
          'No description available.'}
      </p>
    </div>

    {(finding.file_path ||
      finding.line_start ||
      finding.line_end) && (
        <div className="space-y-2">

          <h4 className="text-sm font-semibold">
            Source Location
          </h4>

          <div className="rounded-lg bg-muted/50 p-3">

            <div className="flex items-center gap-2">

              <FileText className="h-4 w-4 text-muted-foreground" />

              <code className="text-xs font-mono">
                {finding.file_path ||
                  'Unknown file'}

                {finding.line_start !== null &&
                  `:${finding.line_start}`}

                {finding.line_end !== null &&
                  finding.line_end !==
                  finding.line_start &&
                  `-${finding.line_end}`}
              </code>

            </div>
          </div>
        </div>
      )}

    <div className="space-y-3">

      <h4 className="text-sm font-semibold">
        Evidence
      </h4>

      {loading ? (
        <p className="text-sm text-muted-foreground">
          Loading evidence…
        </p>
      ) : error ? (
        <p className="text-sm text-destructive">
          {error}
        </p>
      ) : evidence.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          No evidence available.
        </p>
      ) : (
        evidence.map((ev) => (
          <div
            key={ev.id}
            className="space-y-3 rounded-lg border p-4"
          >

            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">

              <div className="flex items-center gap-2">

                <FileText className="h-3.5 w-3.5 text-muted-foreground" />

                <code className="text-xs font-mono">
                  {ev.file_path ||
                    'Unknown file'}
                </code>

              </div>

              {ev.line_start !== null && (
                <span className="text-xs text-muted-foreground">
                  Lines {ev.line_start}

                  {ev.line_end !== null &&
                    ev.line_end !==
                    ev.line_start &&
                    `–${ev.line_end}`}
                </span>
              )}

            </div>

            <div className="flex flex-wrap items-center gap-2">

              <span className="rounded-md bg-muted px-2 py-1 text-xs capitalize">
                {ev.evidence_type}
              </span>

              <VerificationBadge
                status={
                  ev.verification_status as
                  | 'verified'
                  | 'unverified'
                  | 'partial'
                }
              />

            </div>

            {ev.content && (
              <CodeBlock
                code={ev.content}
                language="text"
              />
            )}

          </div>
        ))
      )}

    </div>

    <div className="space-y-2">

      <h4 className="text-sm font-semibold">
        Status
      </h4>

      <span className="inline-flex rounded-md bg-muted px-3 py-1.5 text-sm capitalize">
        {finding.status}
      </span>

    </div>

    <div className="space-y-2">

      <h4 className="text-sm font-semibold">
        Rule
      </h4>

      <code className="inline-flex rounded-md bg-muted px-3 py-1.5 text-xs font-mono">
        {finding.rule_id}
      </code>

    </div>

    <div className="space-y-2">

      <h4 className="text-sm font-semibold">
        Analysis Run
      </h4>

      <code className="block break-all rounded-md bg-muted px-3 py-1.5 text-xs font-mono">
        {finding.analysis_run_id}
      </code>

    </div>

  </div>


  );
}
