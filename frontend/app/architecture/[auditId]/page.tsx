'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  ArrowLeft,
  Layers,
  Boxes,
  AlertTriangle,
  FileCode,
  ChevronRight,
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
  ErrorState,
  LoadingState,
} from '@/components/state-views';

import { api, DEMO_MODE } from '@/src/lib/api';
import { useAsyncData } from '@/src/hooks/use-async-data';

import type { ArchitectureAnalysis } from '@/src/types';

export default function ArchitecturePage({
  params,
}: {
  params: { auditId: string };
}) {
  const { auditId } = params;

  const [selectedModule, setSelectedModule] =
    useState<string | null>(null);

  const {
    data: architecture,
    loading,
    error,
    refetch,
  } = useAsyncData<ArchitectureAnalysis | null>(
    () => api.getArchitectureAnalysis(auditId),
    null,
    [auditId]
  );
console.log('ARCHITECTURE API RESPONSE:', architecture);
  if (loading) {
    return (
      <div className="mx-auto max-w-7xl space-y-8 p-4 md:p-8">
        <LoadingState
          message="Loading architecture analysis…"
          rows={5}
        />
      </div>
    );
  }

  if (error || !architecture) {
    return (
      <div className="mx-auto max-w-4xl space-y-8 p-4 md:p-8">
        <ErrorState
          message="Unable to load architecture analysis"
          description={
            error ??
            `Architecture analysis for audit ${auditId} was not found.`
          }
          onRetry={refetch}
        />
      </div>
    );
  }

  /*
   * Backend field names intentionally remain unchanged.
   *
   * Backend:
   * technologies
   * layers
   * modules
   * relationships
   * risks
   * files_scanned
   * analysis_id
   */

  const technologies = architecture.technologies ?? [];
  const layers = architecture.layers ?? [];
  const modules = architecture.modules ?? [];
  const relationships = architecture.relationships ?? [];
  const risks = architecture.risks ?? [];

  const selectedMod = modules.find(
    (module) => module.id === selectedModule
  );

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
        title="Architecture"
        subtitle="Detected technologies, application layers, and module relationships."
        showDemo={DEMO_MODE}
      />

      <div className="grid gap-6 lg:grid-cols-3">
       <Card>
  <CardHeader>
    <CardTitle className="text-base">
      Detected Technologies
    </CardTitle>
  </CardHeader>

  <CardContent>
    {technologies.length === 0 ? (
      <p className="text-sm text-muted-foreground">
        No technologies detected.
      </p>
    ) : (
      <div className="flex flex-wrap gap-2">
        {technologies.map((technology) => (
          <Badge
            key={technology}
            variant="secondary"
          >
            {technology}
          </Badge>
        ))}
      </div>
    )}
  </CardContent>
</Card>
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">
              Application Layers
            </CardTitle>
          </CardHeader>

          <CardContent>
            {layers.length === 0 ? (
              <p className="text-center text-sm text-muted-foreground">
                No application layers detected.
              </p>
            ) : (
              <div className="flex flex-col items-center gap-2">
                {layers.map((layer, index) => (
                  <div
                    key={`${layer.name}-${index}`}
                    className="flex flex-col items-center"
                  >
                    <div className="w-full max-w-xs rounded-lg border bg-muted/30 p-4 text-center">
                      <div className="flex items-center justify-center gap-2">
                        <Layers className="h-4 w-4 text-muted-foreground" />

                        <span className="text-sm font-medium">
                          {layer.name}
                        </span>
                      </div>

                      <code className="mt-1 block text-xs text-muted-foreground">
                        {layer.module}
                      </code>
                    </div>

                    {index < layers.length - 1 && (
                      <div className="h-6 w-px bg-border" />
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="space-y-4">
        <h3 className="text-lg font-semibold">
          Modules
        </h3>

        {modules.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center text-sm text-muted-foreground">
              No architecture modules detected.
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {modules.map((module) => {
              const moduleFindings =
                module.findings ?? [];

              const moduleDependencies =
                module.dependencies ?? [];

              return (
                <Card
                  key={module.id}
                  className="cursor-pointer transition-colors hover:border-primary/30"
                  onClick={() =>
                    setSelectedModule(module.id)
                  }
                >
                  <CardContent className="p-5">
                    <div className="flex items-center gap-2">
                      <Boxes className="h-4 w-4 text-muted-foreground" />

                      <span className="font-medium">
                        {module.name}
                      </span>

                      {moduleFindings.length > 0 && (
                        <Badge
                          variant="outline"
                          className="ml-auto text-xs"
                        >
                          {moduleFindings.length} finding
                          {moduleFindings.length > 1
                            ? 's'
                            : ''}
                        </Badge>
                      )}
                    </div>

                    <p className="mt-2 text-xs text-muted-foreground">
                      {module.layer}
                    </p>

                    <div className="mt-3 flex flex-wrap gap-1">
                      {moduleDependencies.length === 0 ? (
                        <span className="text-xs text-muted-foreground">
                          No dependencies
                        </span>
                      ) : (
                        moduleDependencies.map(
                          (dependency) => (
                            <Badge
                              key={dependency}
                              variant="secondary"
                              className="text-xs"
                            >
                              {dependency}
                            </Badge>
                          )
                        )
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>

      {selectedMod && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              {selectedMod.name}
            </CardTitle>
          </CardHeader>

          <CardContent className="space-y-4">
            <div>
              <p className="mb-2 text-xs font-medium text-muted-foreground">
                Files
              </p>

              <div className="space-y-1">
                {(selectedMod.files ?? []).length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No files detected.
                  </p>
                ) : (
                  (selectedMod.files ?? []).map(
                    (file) => (
                      <div
                        key={file}
                        className="flex items-center gap-2"
                      >
                        <FileCode className="h-3.5 w-3.5 text-muted-foreground" />

                        <code className="text-xs font-mono">
                          {file}
                        </code>
                      </div>
                    )
                  )
                )}
              </div>
            </div>

            <div>
              <p className="mb-2 text-xs font-medium text-muted-foreground">
                Responsibilities
              </p>

              {(selectedMod.responsibilities ?? []).length ===
              0 ? (
                <p className="text-sm text-muted-foreground">
                  No responsibilities detected.
                </p>
              ) : (
                <ul className="list-inside list-disc space-y-1 text-sm">
                  {(selectedMod.responsibilities ?? []).map(
                    (responsibility) => (
                      <li key={responsibility}>
                        {responsibility}
                      </li>
                    )
                  )}
                </ul>
              )}
            </div>

            <div>
              <p className="mb-2 text-xs font-medium text-muted-foreground">
                Dependencies
              </p>

              <div className="flex flex-wrap gap-1">
                {(selectedMod.dependencies ?? []).length ===
                0 ? (
                  <p className="text-sm text-muted-foreground">
                    No dependencies detected.
                  </p>
                ) : (
                  (selectedMod.dependencies ?? []).map(
                    (dependency) => (
                      <Badge
                        key={dependency}
                        variant="secondary"
                        className="text-xs"
                      >
                        {dependency}
                      </Badge>
                    )
                  )
                )}
              </div>
            </div>

            {(selectedMod.findings ?? []).length > 0 && (
              <div>
                <p className="mb-2 text-xs font-medium text-muted-foreground">
                  Findings
                </p>

                <div className="space-y-1">
                  {(selectedMod.findings ?? []).map(
                    (findingId) => (
                      <Link
                        key={findingId}
                        href={`/audits/${auditId}`}
                        className="flex items-center gap-1 text-sm text-info hover:underline"
                      >
                        {findingId}

                        <ChevronRight className="h-3.5 w-3.5" />
                      </Link>
                    )
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <AlertTriangle className="h-4 w-4 text-warning" />
            Architectural Risks
          </CardTitle>
        </CardHeader>

        <CardContent>
          {risks.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No architectural risks detected.
            </p>
          ) : (
            <ul className="space-y-2">
              {risks.map((risk, index) => (
                <li
                  key={`${risk}-${index}`}
                  className="flex items-start gap-2 text-sm"
                >
                  <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
                  {risk}
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      {/* Backend metadata is available but does not alter the existing UI. */}
      {/*
        architecture.analysis_id
        architecture.files_scanned
        relationships
      */}
    </div>
  );
}