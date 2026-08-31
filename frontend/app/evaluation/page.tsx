'use client';

import { useEffect, useState } from 'react';
import {
  Play,
  TrendingUp,
  TrendingDown,
  ChevronRight,
  BarChart3,
  Loader2,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/page-header';
import { EmptyState, ErrorState } from '@/components/state-views';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { api } from '@/src/lib/api';
import type { EvaluationCase, EvaluationSummary } from '@/src/types';

export default function EvaluationPage() {
  const [evaluation, setEvaluation] = useState<EvaluationSummary | null>(null);
  const [selectedCase, setSelectedCase] = useState<EvaluationCase | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadEvaluation() {
    try {
      setLoading(true);
      setError(null);

      const evaluations = await api.listEvaluations();
      const latest = evaluations[0] ?? null;
      setEvaluation(latest);
    } catch (err) {
      console.error('Failed to load evaluations:', err);
      setError(err instanceof Error ? err.message : 'Unable to load evaluations.');
      setEvaluation(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadEvaluation();
  }, []);

  async function handleRunEvaluation() {
    try {
      setRunning(true);
      setError(null);

      const result = await api.runEvaluation();
      setEvaluation(result);
    } catch (err) {
      console.error('Evaluation failed:', err);
      setError(err instanceof Error ? err.message : 'Evaluation failed.');
    } finally {
      setRunning(false);
    }
  }

  const chartData =
    evaluation?.metrics.map((m) => ({
      name: m.label,
      Baseline: m.baseline,
      Advanced: m.advanced,
    })) ?? [];

  if (loading) {
    return (
      <div className="mx-auto max-w-7xl space-y-8 p-4 md:p-8">
        <PageHeader
          title="Benchmark Evaluation"
          subtitle="Compare the simple baseline against the advanced agentic workflow."
          showDemo={false}
        />
        <Card>
          <CardContent className="flex h-40 items-center justify-center text-sm text-muted-foreground">
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Loading evaluation results...
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl space-y-8 p-4 md:p-8">
      <PageHeader
        title="Benchmark Evaluation"
        subtitle="Compare the simple baseline against the advanced agentic workflow."
        showDemo={false}
        actions={
          <Button
            size="sm"
            onClick={handleRunEvaluation}
            disabled={running}
          >
            {running ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Play className="mr-2 h-4 w-4" />
            )}
            {running ? 'Running...' : 'Run Evaluation'}
          </Button>
        }
      />

      {error && (
        <ErrorState
          message="Unable to load evaluation"
          description={error}
          onRetry={loadEvaluation}
        />
      )}

      {!error && !evaluation ? (
        <EmptyState
          title="No benchmark results yet."
          description="Run an evaluation to compare baseline vs advanced agentic workflow."
          action={
            <Button size="sm" onClick={handleRunEvaluation} disabled={running}>
              {running ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Play className="mr-2 h-4 w-4" />
              )}
              {running ? 'Running...' : 'Run Evaluation'}
            </Button>
          }
        />
      ) : evaluation ? (
        <>
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-muted-foreground">Baseline Overall</p>
                    <p className="text-3xl font-bold tabular-nums">
                      {evaluation.baselineOverall}%
                    </p>
                  </div>
                  <BarChart3 className="h-8 w-8 text-muted-foreground" />
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-muted-foreground">Advanced Overall</p>
                    <p className="text-3xl font-bold tabular-nums text-success">
                      {evaluation.advancedOverall}%
                    </p>
                  </div>
                  <TrendingUp className="h-8 w-8 text-success" />
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Baseline vs Advanced — Metrics</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-80 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                    <XAxis
                      dataKey="name"
                      tick={{ fontSize: 10 }}
                      className="text-muted-foreground"
                      interval={0}
                      angle={-15}
                      textAnchor="end"
                      height={60}
                    />
                    <YAxis tick={{ fontSize: 11 }} className="text-muted-foreground" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: 'hsl(var(--popover))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '0.5rem',
                        fontSize: '12px',
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    <Bar dataKey="Baseline" fill="hsl(var(--muted-foreground))" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="Advanced" fill="hsl(var(--chart-1))" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Metric Comparison</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {evaluation.metrics.map((m) => {
                const diff = m.advanced - m.baseline;
                const better = m.higherIsBetter ? diff > 0 : diff < 0;
                return (
                  <div
                    key={m.key}
                    className="flex items-center justify-between rounded-lg border p-3"
                  >
                    <span className="text-sm font-medium">{m.label}</span>
                    <div className="flex items-center gap-4">
                      <span className="text-sm tabular-nums text-muted-foreground">
                        {m.baseline}{m.unit}
                      </span>
                      <span className="text-muted-foreground">→</span>
                      <span className="text-sm font-semibold tabular-nums">
                        {m.advanced}{m.unit}
                      </span>
                      <span
                        className={`flex items-center gap-0.5 text-xs font-medium ${
                          better ? 'text-success' : 'text-destructive'
                        }`}
                      >
                        {better ? (
                          <TrendingUp className="h-3 w-3" />
                        ) : (
                          <TrendingDown className="h-3 w-3" />
                        )}
                        {diff > 0 ? '+' : ''}{diff}{m.unit}
                      </span>
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>

          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Evaluation Cases</h3>
            <div className="grid gap-4 md:grid-cols-2">
              {evaluation.cases.map((caseItem) => (
                <Card
                  key={caseItem.id}
                  className="cursor-pointer transition-colors hover:border-primary/30"
                  onClick={() => setSelectedCase(caseItem)}
                >
                  <CardContent className="p-5">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">{caseItem.name}</span>
                      <ChevronRight className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {caseItem.description}
                    </p>
                    <div className="mt-4 flex items-center gap-4">
                      <div>
                        <p className="text-xs text-muted-foreground">Baseline</p>
                        <p className="text-lg font-semibold tabular-nums">
                          {caseItem.baselineScore}%
                        </p>
                      </div>
                      <div className="text-muted-foreground">→</div>
                      <div>
                        <p className="text-xs text-muted-foreground">Advanced</p>
                        <p className="text-lg font-semibold tabular-nums text-success">
                          {caseItem.advancedScore}%
                        </p>
                      </div>
                      <div className="ml-auto">
                        <Badge
                          variant="outline"
                          className="border-success/30 text-success"
                        >
                          {caseItem.improvement >= 0 ? '+' : ''}
                          {caseItem.improvement}%
                        </Badge>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          <Dialog
            open={!!selectedCase}
            onOpenChange={(open) => !open && setSelectedCase(null)}
          >
            <DialogContent>
              <DialogHeader>
                <DialogTitle>{selectedCase?.name}</DialogTitle>
                <DialogDescription>{selectedCase?.description}</DialogDescription>
              </DialogHeader>
              {selectedCase && (
                <div className="grid grid-cols-3 gap-4 py-2">
                  <div className="rounded-lg border p-4 text-center">
                    <p className="text-xs text-muted-foreground">Baseline</p>
                    <p className="text-2xl font-bold tabular-nums">
                      {selectedCase.baselineScore}%
                    </p>
                  </div>
                  <div className="rounded-lg border p-4 text-center">
                    <p className="text-xs text-muted-foreground">Advanced</p>
                    <p className="text-2xl font-bold tabular-nums text-success">
                      {selectedCase.advancedScore}%
                    </p>
                  </div>
                  <div className="rounded-lg border p-4 text-center">
                    <p className="text-xs text-muted-foreground">Improvement</p>
                    <p className="text-2xl font-bold tabular-nums text-success">
                      {selectedCase.improvement >= 0 ? '+' : ''}
                      {selectedCase.improvement}%
                    </p>
                  </div>
                </div>
              )}
            </DialogContent>
          </Dialog>
        </>
      ) : null}
    </div>
  );
}
