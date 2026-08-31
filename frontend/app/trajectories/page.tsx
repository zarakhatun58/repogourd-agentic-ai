'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

import { api } from '@/src/lib/api';
import type { Analysis } from '@/src/types';

export default function TrajectoriesPage() {
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.listAnalyses()
      .then(setAnalyses)
      .catch((err) => {
        setError(
          err instanceof Error
            ? err.message
            : 'Unable to load analyses'
        );
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <main className="mx-auto max-w-5xl p-8">
        <h1 className="text-2xl font-semibold">
          Agent Trajectories
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Loading analyses…
        </p>
      </main>
    );
  }

  if (error) {
    return (
      <main className="mx-auto max-w-5xl p-8">
        <h1 className="text-2xl font-semibold">
          Agent Trajectories
        </h1>
        <p className="mt-2 text-sm text-destructive">
          {error}
        </p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-5xl space-y-6 p-8">
      <div>
        <h1 className="text-2xl font-semibold">
          Agent Trajectories
        </h1>

        <p className="mt-1 text-sm text-muted-foreground">
          Select an analysis to inspect its execution trajectory.
        </p>
      </div>

      {!analyses.length ? (
        <p className="text-sm text-muted-foreground">
          No analyses available.
        </p>
      ) : (
        <div className="space-y-3">
          {analyses.map((analysis) => (
            <Link
              key={analysis.id}
              href={`/trajectories/${analysis.id}`}
              className="block rounded-lg border p-4 transition hover:bg-muted"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">
                    Analysis {analysis.id}
                  </p>

                  <p className="text-sm text-muted-foreground">
                    Status: {analysis.status}
                  </p>
                </div>

                <span className="text-sm text-primary">
                  View trajectory →
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </main>
  );
}