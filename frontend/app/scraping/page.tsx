"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  Database,
  Gauge,
  Play,
  RefreshCw,
  ShieldCheck,
  Users,
  Zap,
  Globe,
} from "lucide-react";
import { api } from "@/src/lib/api";

type RuntimeInfo = {
  worker_id?: string;
  session_id?: string;
  proxy_id?: string | null;
  attempt?: number;
  http_status?: number | null;
  latency_ms?: number;
  status?: string;
  blocked?: boolean;
  challenge_detected?: boolean;
  timestamp?: string;
};

type Job = {
  id: string;
  name: string;
  status: string;
  target_count: number;
  max_concurrency: number;
  processed_count: number;
  success_count: number;
  failed_count: number;
  records_per_second: number;
  proxy_configured: boolean;
};

type RecordItem = {
  id: string;
  url: string;
  status: string;
  worker_id: string;
  http_status?: number | null;
  latency_ms?: number | null;
  data?: Record<string, any> | null;
  error?: string | null;
  created_at?: string;
};

const DEFAULT_SCRAPE_URLS =
  process.env.NEXT_PUBLIC_SCRAPE_TARGET_URL ||
  "http://127.0.0.1:8100";

export default function ScrapingPage() {
  const [job, setJob] = useState<Job | null>(null);
  const [records, setRecords] = useState<RecordItem[]>([]);
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);


  const [urls, setUrls] = useState(
    Array.from(
      { length: 50 },
      (_, i) => `${DEFAULT_SCRAPE_URLS}/item/${i + 1}`
    ).join("\n")
  );

  async function refresh(id = job?.id) {
    if (!id) return;

    const [nextJob, nextRecords, nextEvents] =
      await Promise.all([
        api.getScrapeJob(id),
        api.getScrapeRecords(id),
        api.getScrapeEvents(id),
      ]);

    setJob(nextJob);
    setRecords(nextRecords);
    setEvents(nextEvents.events);
  }

  async function start() {
    setLoading(true);

    try {
      const created = await api.createScrapeJob({
        name: "Authorized Playwright Batch Benchmark",
        urls: urls
          .split("\n")
          .map((x) => x.trim())
          .filter(Boolean),

        selector_map: {
          title: ".item-title",
          description: ".item-description",
          category: ".category",
          price: ".price",
          item_id: ".item-id",
          timestamp: ".timestamp",
        },

        max_concurrency: 10,
        delay_ms: 100,
        timeout_ms: 15000,
      });

      setJob(created);
      setRecords([]);
      setEvents([]);

      await refresh(created.id);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!job || job.status === "completed") {
      return;
    }

    const timer = window.setInterval(() => {
      refresh(job.id);
    }, 750);

    return () => {
      window.clearInterval(timer);
    };
  }, [job?.id, job?.status]);

  const progress = useMemo(() => {
    if (!job) return 0;

    return Math.min(
      100,
      Math.round(
        (job.processed_count /
          Math.max(job.target_count, 1)) *
          100
      )
    );
  }, [job]);

  const runtimeRecords = useMemo(() => {
    return records
      .map((record) => ({
        record,
        runtime:
          record.data?._scrape_runtime as RuntimeInfo | undefined,
      }))
      .filter((item) => item.runtime);
  }, [records]);

  const activeWorkers = useMemo(() => {
    return new Set(
      runtimeRecords
        .map((item) => item.runtime?.worker_id)
        .filter(Boolean)
    ).size;
  }, [runtimeRecords]);

  const sessions = useMemo(() => {
    return new Set(
      runtimeRecords
        .map((item) => item.runtime?.session_id)
        .filter(Boolean)
    ).size;
  }, [runtimeRecords]);

  const proxyCount = useMemo(() => {
    return new Set(
      runtimeRecords
        .map((item) => item.runtime?.proxy_id)
        .filter(Boolean)
    ).size;
  }, [runtimeRecords]);

  return (
    <div className="space-y-6 p-6">
      <div>
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold">
            Web Automation
          </h1>

          {job?.status === "running" && (
            <span className="inline-flex items-center gap-2 rounded-full bg-green-500/10 px-3 py-1 text-xs font-medium text-green-600">
              <span className="h-2 w-2 animate-pulse rounded-full bg-green-500" />
              Live
            </span>
          )}
        </div>

        <p className="text-sm text-muted-foreground">
          Authorized Playwright extraction with bounded async
          concurrency, isolated sessions, and structured telemetry.
        </p>
      </div>

      <div className="rounded-xl border p-5 space-y-4">
        <div className="flex items-center gap-2 font-medium">
          <ShieldCheck className="h-5 w-5" />
          Local authorized benchmark target
        </div>

        <textarea
          className="min-h-40 w-full rounded-lg border bg-transparent p-3 text-sm"
          value={urls}
          onChange={(e) => setUrls(e.target.value)}
        />

        <button
          onClick={start}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-primary-foreground disabled:opacity-50"
        >
          <Play className="h-4 w-4" />

          {loading
            ? "Starting..."
            : "Start Playwright Batch"}
        </button>
      </div>

      {job && (
        <>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Metric
              icon={<Activity />}
              label="Processed"
              value={`${job.processed_count}/${job.target_count}`}
            />

            <Metric
              icon={<Users />}
              label="Workers"
              value={job.max_concurrency}
            />

            <Metric
              icon={<Gauge />}
              label="Throughput"
              value={`${job.records_per_second}/s`}
            />

            <Metric
              icon={<Database />}
              label="Success"
              value={job.success_count}
            />
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <Metric
              icon={<Zap />}
              label="Active Workers"
              value={activeWorkers}
            />

            <Metric
              icon={<Globe />}
              label="Sessions"
              value={sessions}
            />

            <Metric
              icon={<ShieldCheck />}
              label="Proxy IDs"
              value={
                job.proxy_configured
                  ? proxyCount
                  : "Direct"
              }
            />
          </div>

          <div className="rounded-xl border p-5">
            <div className="mb-2 flex justify-between text-sm">
              <span>
                Status:{" "}
                <strong>{job.status}</strong>
              </span>

              <span>{progress}%</span>
            </div>

            <div className="h-2 overflow-hidden rounded-full bg-muted">
              <div
                className="h-full bg-primary transition-all"
                style={{
                  width: `${progress}%`,
                }}
              />
            </div>

            <div className="mt-3 flex flex-wrap gap-4 text-xs text-muted-foreground">
              <span>
                Targets: {job.target_count}
              </span>

              <span>
                Success: {job.success_count}
              </span>

              <span>
                Failed: {job.failed_count}
              </span>

              <span>
                Concurrency: {job.max_concurrency}
              </span>
            </div>
          </div>

          <div className="rounded-xl border p-5">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h2 className="font-semibold">
                  Live execution telemetry
                </h2>

                <p className="text-xs text-muted-foreground">
                  Worker, session, proxy, latency and HTTP
                  execution data.
                </p>
              </div>

              <button
                onClick={() => refresh()}
                className="rounded-md p-2 hover:bg-muted"
                title="Refresh"
              >
                <RefreshCw className="h-4 w-4" />
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b text-muted-foreground">
                    <th className="px-3 py-2">
                      Worker
                    </th>

                    <th className="px-3 py-2">
                      Session
                    </th>

                    <th className="px-3 py-2">
                      Proxy
                    </th>

                    <th className="px-3 py-2">
                      HTTP
                    </th>

                    <th className="px-3 py-2">
                      Latency
                    </th>

                    <th className="px-3 py-2">
                      Attempt
                    </th>

                    <th className="px-3 py-2">
                      Status
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {runtimeRecords
                    .slice(-25)
                    .reverse()
                    .map(({ record, runtime }) => (
                      <tr
                        key={record.id}
                        className="border-b last:border-0"
                      >
                        <td className="px-3 py-2 font-medium">
                          {runtime?.worker_id ?? "-"}
                        </td>

                        <td className="px-3 py-2 font-mono">
                          {runtime?.session_id
                            ? runtime.session_id.slice(-12)
                            : "-"}
                        </td>

                        <td className="px-3 py-2">
                          {runtime?.proxy_id ?? "Direct"}
                        </td>

                        <td className="px-3 py-2">
                          {runtime?.http_status ?? "-"}
                        </td>

                        <td className="px-3 py-2">
                          {runtime?.latency_ms != null
                            ? `${runtime.latency_ms} ms`
                            : "-"}
                        </td>

                        <td className="px-3 py-2">
                          {runtime?.attempt ?? "-"}
                        </td>

                        <td className="px-3 py-2">
                          <span
                            className={
                              runtime?.status ===
                              "success"
                                ? "font-medium text-green-600"
                                : "font-medium text-red-600"
                            }
                          >
                            {runtime?.status ?? record.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <section className="rounded-xl border p-5">
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <h2 className="font-semibold">
                    Execution events
                  </h2>

                  <p className="text-xs text-muted-foreground">
                    Scraper lifecycle events.
                  </p>
                </div>

                <button
                  onClick={() => refresh()}
                  className="rounded-md p-2 hover:bg-muted"
                  title="Refresh"
                >
                  <RefreshCw className="h-4 w-4" />
                </button>
              </div>

              <div className="space-y-2 text-sm">
                {events.map((event, index) => (
                  <div
                    key={`${event.step}-${event.event_type}-${index}`}
                    className="rounded-lg bg-muted/40 p-3"
                  >
                    <div className="font-medium">
                      {event.step}.{" "}
                      {event.event_type}
                    </div>

                    <div className="text-xs text-muted-foreground">
                      {event.at}
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <section className="rounded-xl border p-5">
              <h2 className="mb-4 font-semibold">
                Structured JSON records
              </h2>

              <div className="max-h-96 space-y-2 overflow-auto text-xs">
                {records
                  .slice(-50)
                  .reverse()
                  .map((record) => (
                    <pre
                      key={record.id}
                      className="rounded-lg bg-muted/40 p-3 whitespace-pre-wrap"
                    >
                      {JSON.stringify(
                        record,
                        null,
                        2
                      )}
                    </pre>
                  ))}
              </div>
            </section>
          </div>
        </>
      )}
    </div>
  );
}

function Metric({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border p-5">
      <div className="mb-3 flex items-center gap-2 text-muted-foreground">
        {icon}
        <span>{label}</span>
      </div>

      <div className="text-2xl font-semibold">
        {value}
      </div>
    </div>
  );
}