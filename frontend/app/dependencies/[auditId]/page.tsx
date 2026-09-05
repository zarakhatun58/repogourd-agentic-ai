'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import {
  ArrowLeft,
  Package,
  AlertTriangle,
  GitMerge,
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

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

import {
  ErrorState,
  LoadingState,
} from '@/components/state-views';

import { api, DEMO_MODE } from '@/src/lib/api';

import type {
  Analysis,
  DependencyAnalysis,
  DependencyPackage,
} from '@/src/types';

type SortKey =
  | 'package'
  | 'version'
  | 'type'
  | 'status'
  | 'risk';

type SortDir = 'asc' | 'desc';

const RISK_STYLES: Record<string, string> = {
  low: 'border-transparent bg-success/15 text-success',
  medium: 'border-transparent bg-warning/15 text-warning',
  high: 'border-transparent bg-destructive/15 text-destructive',
};

function normalizeDependencyPackage(
  pkg: Partial<DependencyPackage> | null | undefined
): DependencyPackage {
  return {
    package: pkg?.package ?? '',
    version: pkg?.version ?? '',
    type: pkg?.type ?? 'unknown',
    status: pkg?.status ?? 'unknown',
    risk: pkg?.risk ?? 'low',
  };
}

function normalizeDependencyAnalysis(
  data: DependencyAnalysis | null | undefined
): DependencyAnalysis {
  return {
    total: data?.total ?? 0,
    direct: data?.direct ?? 0,
    dev: data?.dev ?? 0,
    optional: data?.optional ?? 0,
    outdated: data?.outdated ?? 0,
    conflicts: data?.conflicts ?? 0,
    packages: Array.isArray(data?.packages)
      ? data.packages.map(normalizeDependencyPackage)
      : [],
  };
}

export default function DependenciesPage({
  params,
}: {
  params: { auditId: string };
}) {
  const { auditId } = params;

  const [dependencies, setDependencies] =
    useState<DependencyAnalysis | null>(null);

  const [loading, setLoading] = useState(true);

  const [error, setError] =
    useState<string | null>(null);

  const [sortKey, setSortKey] =
    useState<SortKey>('package');

  const [sortDir, setSortDir] =
    useState<SortDir>('asc');

  const [typeFilter, setTypeFilter] =
    useState<string>('all');

  useEffect(() => {
    let cancelled = false;

    async function loadDependencyAnalysis() {
      try {
        setLoading(true);
        setError(null);

        /*
         * Find the analysis associated with this audit.
         */
        const analyses = await api.listAnalyses();
console.log('AUDIT ID:', auditId);
console.log('ALL ANALYSES:', analyses);
        if (cancelled) {
          return;
        }

        const analysis = analyses.find(
  (item: Analysis) =>
    item.id === auditId
);

        if (!analysis) {
          throw new Error(
            `No analysis found for audit ${auditId}.`
          );
        }

        const result =
          await api.getDependencyAnalysis(
            analysis.id
          );
console.log(
  'DEPENDENCY API RESPONSE:',
  result
);
        if (cancelled) {
          return;
        }

       setDependencies(
  normalizeDependencyAnalysis(
    result?.dependencies
  )
);
      } catch (err) {
        if (cancelled) {
          return;
        }

        setDependencies(null);

        setError(
          err instanceof Error
            ? err.message
            : 'Unable to load dependency analysis.'
        );
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadDependencyAnalysis();

    return () => {
      cancelled = true;
    };
  }, [auditId]);

  const filteredPackages = useMemo(() => {
    if (!dependencies) {
      return [];
    }

    let list = [...dependencies.packages];

    if (typeFilter !== 'all') {
      list = list.filter(
        (pkg) => pkg.type === typeFilter
      );
    }

    list.sort((a, b) => {
      const aValue = String(
        a[sortKey] ?? ''
      ).toLowerCase();

      const bValue = String(
        b[sortKey] ?? ''
      ).toLowerCase();

      const comparison =
        aValue.localeCompare(bValue);

      return sortDir === 'asc'
        ? comparison
        : -comparison;
    });

    return list;
  }, [
    dependencies,
    sortKey,
    sortDir,
    typeFilter,
  ]);

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir((current) =>
        current === 'asc'
          ? 'desc'
          : 'asc'
      );

      return;
    }

    setSortKey(key);
    setSortDir('asc');
  }

  /*
   * Loading
   */
  if (loading) {
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
          title="Dependency Analysis"
          subtitle="Total dependencies, outdated packages, conflicts, and risk signals."
          showDemo={DEMO_MODE}
        />

        <LoadingState
          message="Loading dependency analysis…"
          rows={6}
        />
      </div>
    );
  }

  /*
   * Error
   */
  if (error || !dependencies) {
    return (
      <div className="mx-auto max-w-4xl space-y-8 p-4 md:p-8">
        <div className="flex items-center justify-between">
          <Link href={`/audits/${auditId}`}>
            <Button variant="ghost" size="sm">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Report
            </Button>
          </Link>
        </div>

        <PageHeader
          title="Dependency Analysis"
          subtitle="Total dependencies, outdated packages, conflicts, and risk signals."
          showDemo={DEMO_MODE}
        />

        <ErrorState
          message="Unable to load dependency analysis"
          description={
            error ??
            `Dependency analysis for audit ${auditId} was not found.`
          }
          onRetry={() => {
            window.location.reload();
          }}
        />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl space-y-8 p-4 md:p-8">
      {/* Back */}
      <div className="flex items-center justify-between">
        <Link href={`/audits/${auditId}`}>
          <Button variant="ghost" size="sm">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Report
          </Button>
        </Link>
      </div>

      {/* Header */}
      <PageHeader
        title="Dependency Analysis"
        subtitle="Total dependencies, outdated packages, conflicts, and risk signals."
        showDemo={DEMO_MODE}
      />

      {/* Statistics */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
        {[
          {
            label: 'Total',
            value: dependencies.total,
            icon: Package,
          },
          {
            label: 'Direct',
            value: dependencies.direct,
            icon: Package,
          },
          {
            label: 'Dev',
            value: dependencies.dev,
            icon: Package,
          },
          {
            label: 'Optional',
            value: dependencies.optional,
            icon: Package,
          },
          {
            label: 'Outdated',
            value: dependencies.outdated,
            icon: AlertTriangle,
            color: 'text-warning',
          },
          {
            label: 'Conflicts',
            value: dependencies.conflicts,
            icon: GitMerge,
            color: 'text-destructive',
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

      {/* Dependency table */}
      <Card>
        <CardHeader>
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <CardTitle className="text-base">
              Dependencies
            </CardTitle>

            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">
                Filter:
              </span>

              <Select
                value={typeFilter}
                onValueChange={setTypeFilter}
              >
                <SelectTrigger className="h-8 w-32 text-xs">
                  <SelectValue />
                </SelectTrigger>

                <SelectContent>
                  <SelectItem value="all">
                    All
                  </SelectItem>

                  <SelectItem value="prod">
                    Production
                  </SelectItem>

                  <SelectItem value="dev">
                    Dev
                  </SelectItem>

                  <SelectItem value="optional">
                    Optional
                  </SelectItem>

                  <SelectItem value="unknown">
                    Unknown
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>

        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                {(
                  [
                    'package',
                    'version',
                    'type',
                    'status',
                    'risk',
                  ] as SortKey[]
                ).map((key) => (
                  <TableHead
                    key={key}
                    className="cursor-pointer select-none capitalize"
                    onClick={() =>
                      toggleSort(key)
                    }
                  >
                    {key}

                    {sortKey === key && (
                      <span className="ml-1 text-xs">
                        {sortDir === 'asc'
                          ? '↑'
                          : '↓'}
                      </span>
                    )}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>

            <TableBody>
              {filteredPackages.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={5}
                    className="py-8 text-center text-sm text-muted-foreground"
                  >
                    No dependencies found.
                  </TableCell>
                </TableRow>
              ) : (
                filteredPackages.map((pkg) => (
                  <TableRow
                    key={`${pkg.package}-${pkg.version}`}
                  >
                    <TableCell className="font-mono text-xs font-medium">
                      {pkg.package}
                    </TableCell>

                    <TableCell className="font-mono text-xs">
                      {pkg.version}
                    </TableCell>

                    <TableCell>
                      <Badge
                        variant="secondary"
                        className="text-xs"
                      >
                        {pkg.type}
                      </Badge>
                    </TableCell>

                    <TableCell>
                      <span
                        className={`inline-flex items-center gap-1.5 text-xs capitalize ${
                          pkg.status === 'ok'
                            ? 'text-success'
                            : pkg.status === 'conflict'
                              ? 'text-destructive'
                              : pkg.status === 'outdated'
                                ? 'text-warning'
                                : 'text-muted-foreground'
                        }`}
                      >
                        <span
                          className={`h-1.5 w-1.5 rounded-full ${
                            pkg.status === 'ok'
                              ? 'bg-success'
                              : pkg.status === 'conflict'
                                ? 'bg-destructive'
                                : pkg.status === 'outdated'
                                  ? 'bg-warning'
                                  : 'bg-muted-foreground'
                          }`}
                        />

                        {pkg.status}
                      </span>
                    </TableCell>

                    <TableCell>
                      <Badge
                        variant="outline"
                        className={`text-xs capitalize ${
                          RISK_STYLES[pkg.risk] ??
                          ''
                        }`}
                      >
                        {pkg.risk}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}