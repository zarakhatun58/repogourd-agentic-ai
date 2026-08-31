'use client';

import Link from 'next/link';
import {
  ArrowLeft,
  TestTube,
  CheckCircle2,
  XCircle,
  Gauge,
  AlertCircle,
} from 'lucide-react';

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/page-header';
import { ScoreBar } from '@/components/score-display';

import {
  ErrorState,
  LoadingState,
} from '@/components/state-views';

import { api, DEMO_MODE } from '@/src/lib/api';
import { useAsyncData } from '@/src/hooks/use-async-data';

import type { TestingAnalysis } from '@/src/types';

export default function TestingPage({
  params,
}: {
  params: { auditId: string };
}) {
  const { auditId } = params;

  const {
    data: testing,
    loading,
    error,
    refetch,
  } = useAsyncData<TestingAnalysis | null>(
    () => api.getTestingAnalysis(auditId),
    null,
    [auditId]
  );

  if (loading) {
    return (
      <div className="mx-auto max-w-7xl space-y-8 p-4 md:p-8">
        <LoadingState
          message="Loading testing analysis…"
          rows={5}
        />
      </div>
    );
  }

  if (error || !testing) {
    return (
      <div className="mx-auto max-w-4xl space-y-8 p-4 md:p-8">
        <ErrorState
          message="Unable to load testing analysis"
          description={
            error ??
            `Testing analysis for audit ${auditId} was not found.`
          }
          onRetry={refetch}
        />
      </div>
    );
  }

  /*
   * Backend uses snake_case.
   *
   * Keep the backend response shape intact.
   * Only normalize nullable/array fields so the UI
   * never crashes when the backend returns null/undefined.
   */
  const categories = Array.isArray(testing.categories)
    ? testing.categories
    : [];

  const missingAreas = Array.isArray(testing.missing_areas)
    ? testing.missing_areas
    : [];

  /*
   * Backend coverage is:
   *
   * coverage: float | None
   *
   * null means coverage is unavailable.
   */
  const coverage =
    typeof testing.coverage === 'number'
      ? testing.coverage
      : 0;

  const coverageLabel =
    testing.coverage === null
      ? 'Not available'
      : `${testing.coverage}%`;

  const coverageSource =
    testing.coverage_source || 'not_available';

  const framework =
    testing.framework || 'unknown';

  const executionStatus =
    testing.execution_status || 'not_run';

  return (
    <div className="mx-auto max-w-7xl space-y-8 p-4 md:p-8">
      <div className="flex items-center justify-between">
        <Link href={`/audits/${auditId}`}>
          <Button variant="ghost" size="sm">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Report
          </Button>
        </Link>
      </div>

      <PageHeader
        title="Testing Analysis"
        subtitle="Test coverage, detected frameworks, and testing gaps."
        showDemo={DEMO_MODE}
      />

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4 lg:grid-cols-5">
        {[
          {
            label: 'Tests detected',
            value: testing.test_files,
            icon: TestTube,
          },
          {
            label: 'Test suites',
            value: testing.test_suites,
            icon: TestTube,
          },
          {
            label: 'Passed',
            value: testing.passed,
            icon: CheckCircle2,
            color: 'text-success',
          },
          {
            label: 'Failed',
            value: testing.failed,
            icon: XCircle,
            color: 'text-destructive',
          },
          {
            label: 'Coverage',
            value: coverageLabel,
            icon: Gauge,
            color: 'text-warning',
          },
        ].map((stat) => {
          const Icon = stat.icon;

          return (
            <Card key={stat.label}>
              <CardContent className="p-5">
                <Icon
                  className={`h-5 w-5 ${
                    stat.color ??
                    'text-muted-foreground'
                  }`}
                />

                <p className="mt-3 text-2xl font-bold tabular-nums">
                  {stat.value}
                </p>

                <p className="text-xs text-muted-foreground">
                  {stat.label}
                </p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              Test Framework & Coverage
            </CardTitle>
          </CardHeader>

          <CardContent className="space-y-4">
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">
                Framework:
              </span>

              <Badge variant="secondary">
                {framework}
              </Badge>
            </div>

            <div>
              <div className="mb-2 flex items-center justify-between">
                <span className="text-sm text-muted-foreground">
                  Coverage
                </span>

                <Badge
                  variant="outline"
                  className="text-xs capitalize"
                >
                  {coverageSource}
                </Badge>
              </div>

              <ScoreBar score={coverage} />
            </div>

            <p className="text-xs text-muted-foreground">
              Coverage is labeled as{' '}
              {coverageSource}.
              {testing.coverage === null
                ? ' Actual coverage values were not supplied by the backend.'
                : ' Coverage value was supplied by the backend.'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              Test Categories
            </CardTitle>
          </CardHeader>

          <CardContent>
            <div className="space-y-3">
              {categories.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No test categories detected.
                </p>
              ) : (
                categories.map((cat, index) => (
                  <div
                    key={`${cat.name}-${index}`}
                    className="flex items-center justify-between"
                  >
                    <span className="text-sm font-medium">
                      {cat.name}
                    </span>

                    <span className="text-sm tabular-nums text-muted-foreground">
                      {cat.count} tests
                    </span>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <AlertCircle className="h-4 w-4 text-warning" />
            Missing Test Areas
          </CardTitle>
        </CardHeader>

        <CardContent>
          {missingAreas.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No missing test areas detected.
            </p>
          ) : (
            <ul className="space-y-2">
              {missingAreas.map((area, index) => (
                <li
                  key={`${area}-${index}`}
                  className="flex items-start gap-2 text-sm"
                >
                  <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-warning" />

                  {area}
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Test Execution Status
          </CardTitle>
        </CardHeader>

        <CardContent>
          <span className="inline-flex items-center gap-2 text-sm">
            <span
              className={`h-2 w-2 rounded-full ${
                executionStatus === 'completed'
                  ? 'bg-success'
                  : 'bg-warning'
              }`}
            />

            <span className="capitalize">
              {executionStatus}
            </span>
          </span>
        </CardContent>
      </Card>
    </div>
  );
}