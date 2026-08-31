
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { z } from 'zod';
import {
  Upload,
  FileArchive,
  X,
  Loader2,
  Play,
} from 'lucide-react';

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '@/components/ui/card';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import {
  RadioGroup,
  RadioGroupItem,
} from '@/components/ui/radio-group';

import { PageHeader } from '@/components/page-header';
import { Stepper } from '@/components/stepper';
import { toast } from 'sonner';

import { api, DEMO_MODE } from '@/src/lib/api';
import { DEMO_AUDIT_STEPS } from '@/src/lib/demo';

import type {
  AuditStep,
  AnalysisDepth,
  AuditCategory,
  Repository,
  Analysis,
} from '@/src/types';

const GITHUB_URL_SCHEMA = z
  .string()
  .trim()
  .url('Enter a valid GitHub URL')
  .refine(
    (value) => {
      try {
        const url = new URL(value);

        return (
          url.hostname === 'github.com' ||
          url.hostname === 'www.github.com'
        );
      } catch {
        return false;
      }
    },
    {
      message: 'URL must point to github.com',
    }
  );

const ALL_CATEGORIES: {
  key: AuditCategory;
  label: string;
}[] = [
  {
    key: 'architecture',
    label: 'Architecture',
  },
  {
    key: 'code_quality',
    label: 'Code Quality',
  },
  {
    key: 'testing',
    label: 'Testing',
  },
  {
    key: 'dependencies',
    label: 'Dependencies',
  },
  {
    key: 'security',
    label: 'Security Signals',
  },
];

type UploadFile = {
  file: File;
  name: string;
  size: number;
};

type GithubApi = {
  ingestGithubRepository: (
    url: string
  ) => Promise<Repository>;
};

function getGithubApi(): GithubApi {
  return api as typeof api & GithubApi;
}

export default function NewAuditPage() {
  const router = useRouter();

  const [mode, setMode] = useState<'github' | 'upload'>(
    'github'
  );

  const [githubUrl, setGithubUrl] = useState('');
  const [urlError, setUrlError] = useState<string | null>(
    null
  );

  const [uploadFile, setUploadFile] =
    useState<UploadFile | null>(null);

  const [uploadProgress, setUploadProgress] = useState(0);

  const [error, setError] = useState<string | null>(null);

  const [isLoading, setIsLoading] = useState(false);

  const [depth, setDepth] =
    useState<AnalysisDepth>('standard');

  const [categories, setCategories] =
    useState<AuditCategory[]>([
      'architecture',
      'code_quality',
      'testing',
      'dependencies',
      'security',
    ]);

  const [started, setStarted] = useState(false);

  const [steps, setSteps] =
    useState<AuditStep[]>(DEMO_AUDIT_STEPS);

  function toggleCategory(cat: AuditCategory) {
    setCategories((prev) =>
      prev.includes(cat)
        ? prev.filter((c) => c !== cat)
        : [...prev, cat]
    );
  }

  function handleFile(file: File) {
    const maxSize = 100 * 1024 * 1024;

    if (file.size > maxSize) {
      setError(
        'The repository archive must be smaller than 100 MB.'
      );
      return;
    }

    const validArchive =
      file.name.toLowerCase().endsWith('.zip') ||
      file.name.toLowerCase().endsWith('.tar') ||
      file.name.toLowerCase().endsWith('.tar.gz') ||
      file.name.toLowerCase().endsWith('.tgz');

    if (!validArchive) {
      setError(
        'Please select a ZIP, TAR, TAR.GZ, or TGZ repository archive.'
      );
      return;
    }

    setError(null);

    setUploadFile({
      file,
      name: file.name,
      size: file.size,
    });

    setUploadProgress(0);

    const interval = window.setInterval(() => {
      setUploadProgress((progress) => {
        if (progress >= 100) {
          window.clearInterval(interval);
          return 100;
        }

        return progress + 10;
      });
    }, 150);
  }

  async function createAndRunAnalysis(
    repositoryId: string
  ): Promise<Analysis> {
    const analysis = await api.createAnalysis({
      repository_id: repositoryId,
      agent_type: 'repoguard-agent',
    });

    return api.runAnalysis(analysis.id);
  }

  async function handleGithubAudit() {
    const value = githubUrl.trim();

    const validation =
      GITHUB_URL_SCHEMA.safeParse(value);

    if (!validation.success) {
      const message =
        validation.error.issues[0]?.message ||
        'Enter a valid GitHub URL.';

      setUrlError(message);
      setError(message);

      return;
    }

    setUrlError(null);
    setError(null);

    try {
      setIsLoading(true);

      /*
       * 1. Clone and register GitHub repository.
       *
       * Backend:
       * POST /repositories/github
       * body: { url }
       */
      const githubApi = getGithubApi();

      const repository =
        await githubApi.ingestGithubRepository(value);

      if (!repository?.id) {
        throw new Error(
          'GitHub repository was registered but no repository ID was returned.'
        );
      }

      /*
       * 2. Create analysis.
       */
      const analysis =
        await createAndRunAnalysis(repository.id);

      /*
       * 3. Navigate to the actual analysis.
       */
      if (!analysis?.id) {
        throw new Error(
          'Analysis was created but no analysis ID was returned.'
        );
      }

      toast.success('GitHub repository analysis started.');

      router.push(`/analysis/${analysis.id}`);
    } catch (err) {
      console.error(
        'GitHub audit failed:',
        err
      );

      const message =
        err instanceof Error
          ? err.message
          : 'Failed to analyze the GitHub repository.';

      setError(message);

      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleUploadAudit() {
    if (!uploadFile) {
      setError(
        'Please select a ZIP repository.'
      );
      return;
    }

    if (uploadProgress < 100) {
      setError(
        'Please wait for the repository upload to finish.'
      );
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      /*
       * 1. Upload repository.
       */
      const repository =
        await api.uploadRepository(
          uploadFile.file
        );

      if (!repository?.id) {
        throw new Error(
          'Repository upload succeeded but no repository ID was returned.'
        );
      }

      /*
       * 2. Create analysis.
       */
      const analysis =
        await createAndRunAnalysis(repository.id);

      /*
       * 3. Navigate to actual analysis.
       */
      if (!analysis?.id) {
        throw new Error(
          'Analysis was created but no analysis ID was returned.'
        );
      }

      toast.success('Repository analysis started.');

      router.push(`/analysis/${analysis.id}`);
    } catch (err) {
      console.error(
        'Repository upload audit failed:',
        err
      );

      const message =
        err instanceof Error
          ? err.message
          : 'Failed to start repository analysis.';

      setError(message);

      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  }

const handleStartAudit = async () => {
  setError(null);
  setUrlError(null);

  if (mode === 'github') {
    const url = githubUrl.trim();

    const validation = GITHUB_URL_SCHEMA.safeParse(url);

    if (!validation.success) {
      setUrlError(
        validation.error.issues[0]?.message ??
          'Enter a valid GitHub repository URL.'
      );
      return;
    }

    try {
      setIsLoading(true);

      const repository =
        await api.ingestGithubRepository(url);

      const analysis = await api.createAnalysis({
        repository_id: repository.id,
        agent_type: 'repoguard-agent',
      });

      const completedAnalysis =
        await api.runAnalysis(analysis.id);

      router.push(
        `/analysis/${completedAnalysis.id}`
      );
    } catch (err) {
      console.error('GitHub audit failed:', err);

      setError(
        err instanceof Error
          ? err.message
          : 'Failed to ingest GitHub repository.'
      );
    } finally {
      setIsLoading(false);
    }

    return;
  }

  // ZIP upload flow
  if (!uploadFile) {
    setError('Please select a ZIP repository.');
    return;
  }

  try {
    setIsLoading(true);

    const repository =
      await api.uploadRepository(uploadFile.file);

    const analysis = await api.createAnalysis({
      repository_id: repository.id,
      agent_type: 'repoguard-agent',
    });

    const completedAnalysis =
      await api.runAnalysis(analysis.id);

    router.push(
      `/analysis/${completedAnalysis.id}`
    );
  } catch (err) {
    console.error('Upload audit failed:', err);

    setError(
      err instanceof Error
        ? err.message
        : 'Failed to start analysis.'
    );
  } finally {
    setIsLoading(false);
  }
};



  function runDemoProgress() {
    setStarted(true);

    setSteps(
      DEMO_AUDIT_STEPS.map((step) => ({
        ...step,
        status: 'pending',
      }))
    );

    DEMO_AUDIT_STEPS.forEach(
      (step, idx) => {
        window.setTimeout(() => {
          setSteps((prev) =>
            prev.map((current, i) =>
              i === idx
                ? {
                    ...current,
                    status: 'running',
                  }
                : current
            )
          );
        }, idx * 800);

        window.setTimeout(
          () => {
            setSteps((prev) =>
              prev.map((current, i) =>
                i === idx
                  ? {
                      ...current,
                      status: 'completed',
                    }
                  : current
              )
            );

            if (
              idx ===
              DEMO_AUDIT_STEPS.length - 1
            ) {
              window.setTimeout(() => {
                router.push(
                  '/analysis/aud-001'
                );
              }, 600);
            }
          },
          idx * 800 + 600
        );
      }
    );
  }

  function formatBytes(bytes: number): string {
    if (bytes < 1024) {
      return `${bytes} B`;
    }

    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`;
    }

    return `${(
      bytes /
      (1024 * 1024)
    ).toFixed(1)} MB`;
  }

  if (started) {
    return (
      <div className="mx-auto max-w-2xl space-y-8 p-4 md:p-8">
        <PageHeader
          title="Audit in Progress"
          subtitle="Following the analysis pipeline. Each step is tracked with real status."
          showDemo={DEMO_MODE}
        />

        <Card>
          <CardContent className="p-6">
            <Stepper steps={steps} />
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-8 p-4 md:p-8">
      <PageHeader
        title="Start a Repository Audit"
        subtitle="Analyze architecture, code quality, testing, dependencies and engineering risks."
        showDemo={DEMO_MODE}
      />

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">
                Source Repository
              </CardTitle>

              <CardDescription>
                Choose how to provide the codebase.
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  disabled={isLoading}
                  onClick={() => {
                    setMode('github');
                    setError(null);
                    setUrlError(null);
                  }}
                  className={`flex items-center gap-3 rounded-lg border p-4 text-left transition-colors ${
                    mode === 'github'
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:bg-accent'
                  }`}
                >
                  <svg
                    className="h-5 w-5"
                    viewBox="0 0 24 24"
                    fill="currentColor"
                    aria-hidden="true"
                  >
                    <path d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.604-3.369-1.342-3.369-1.342-.454-1.153-1.11-1.46-1.11-1.46-.908-.62.069-.608.069-.608 1.004.07 1.532 1.032 1.532 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.339-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.564 9.564 0 0 1 12 6.844a9.58 9.58 0 0 1 2.504.337c1.909-1.294 2.748-1.025 2.748-1.025.546 1.377.202 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.936.359.309.678.92.678 1.855 0 1.339-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.001 10.001 0 0 0 22 12C22 6.477 17.523 2 12 2Z" />
                  </svg>

                  <div>
                    <p className="text-sm font-medium">
                      GitHub Repository
                    </p>

                    <p className="text-xs text-muted-foreground">
                      Provide a URL
                    </p>
                  </div>
                </button>

                <button
                  type="button"
                  disabled={isLoading}
                  onClick={() => {
                    setMode('upload');
                    setError(null);
                    setUrlError(null);
                  }}
                  className={`flex items-center gap-3 rounded-lg border p-4 text-left transition-colors ${
                    mode === 'upload'
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:bg-accent'
                  }`}
                >
                  <Upload className="h-5 w-5" />

                  <div>
                    <p className="text-sm font-medium">
                      Upload Repository
                    </p>

                    <p className="text-xs text-muted-foreground">
                      ZIP or TAR archive
                    </p>
                  </div>
                </button>
              </div>

              {error && (
                <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
                  {error}
                </div>
              )}

              {mode === 'github' && (
                <div className="space-y-2">
                  <Label htmlFor="github-url">
                    GitHub repository URL
                  </Label>

                  <Input
                    id="github-url"
                    placeholder="https://github.com/example/project"
                    value={githubUrl}
                    disabled={isLoading}
                    onChange={(e) => {
                      setGithubUrl(
                        e.target.value
                      );

                      setUrlError(null);
                      setError(null);
                    }}
                    onKeyDown={(e) => {
                      if (
                        e.key === 'Enter' &&
                        !isLoading
                      ) {
                        e.preventDefault();
                        void handleStartAudit();
                      }
                    }}
                    aria-invalid={!!urlError}
                  />

                  {urlError && (
                    <p className="text-xs text-destructive">
                      {urlError}
                    </p>
                  )}

                  <Button
                    onClick={() =>
                      void handleStartAudit()
                    }
                    disabled={isLoading}
                    className="w-full"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Analyzing Repository...
                      </>
                    ) : (
                      <>
                        <Play className="mr-2 h-4 w-4" />
                        Analyze Repository
                      </>
                    )}
                  </Button>
                </div>
              )}

              {mode === 'upload' && (
                <div className="space-y-3">
                  {!uploadFile ? (
                    <label
                      htmlFor="file-upload"
                      className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border border-dashed p-8 text-center transition-colors hover:bg-accent"
                    >
                      <FileArchive className="h-8 w-8 text-muted-foreground" />

                      <p className="text-sm font-medium">
                        Click to upload a ZIP or TAR archive
                      </p>

                      <p className="text-xs text-muted-foreground">
                        Maximum 100 MB
                      </p>

                      <input
                        id="file-upload"
                        type="file"
                        accept=".zip,.tar,.tar.gz,.tgz"
                        className="hidden"
                        disabled={isLoading}
                        onChange={(e) => {
                          const file =
                            e.target.files?.[0];

                          if (file) {
                            handleFile(file);
                          }

                          e.target.value = '';
                        }}
                      />
                    </label>
                  ) : (
                    <div className="space-y-3">
                      <div className="flex items-center justify-between rounded-lg border p-3">
                        <div className="flex items-center gap-3">
                          <FileArchive className="h-5 w-5 text-muted-foreground" />

                          <div>
                            <p className="text-sm font-medium">
                              {uploadFile.name}
                            </p>

                            <p className="text-xs text-muted-foreground">
                              {formatBytes(
                                uploadFile.size
                              )}
                            </p>
                          </div>
                        </div>

                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          disabled={isLoading}
                          onClick={() => {
                            setUploadFile(
                              null
                            );

                            setUploadProgress(
                              0
                            );

                            setError(null);
                          }}
                          aria-label="Remove file"
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>

                      {uploadProgress < 100 && (
                        <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
                          <div
                            className="h-full bg-primary transition-all"
                            style={{
                              width: `${uploadProgress}%`,
                            }}
                          />
                        </div>
                      )}

                      <Button
                        onClick={() =>
                          void handleStartAudit()
                        }
                        disabled={
                          isLoading ||
                          uploadProgress < 100
                        }
                        className="w-full"
                      >
                        {isLoading ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Analyzing Repository...
                          </>
                        ) : uploadProgress < 100 ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Preparing Upload...
                          </>
                        ) : (
                          <>
                            <Play className="mr-2 h-4 w-4" />
                            Start Audit
                          </>
                        )}
                      </Button>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">
                Analysis Depth
              </CardTitle>
            </CardHeader>

            <CardContent>
              <RadioGroup
                value={depth}
                onValueChange={(value) =>
                  setDepth(
                    value as AnalysisDepth
                  )
                }
              >
                <div className="space-y-2">
                  <label
                    className={`flex cursor-pointer items-start gap-3 rounded-lg border p-3 transition-colors ${
                      depth === 'standard'
                        ? 'border-primary bg-primary/5'
                        : 'border-border'
                    }`}
                  >
                    <RadioGroupItem
                      value="standard"
                      className="mt-1"
                    />

                    <div>
                      <p className="text-sm font-medium">
                        Standard
                      </p>

                      <p className="text-xs text-muted-foreground">
                        Faster analysis of key files.
                      </p>
                    </div>
                  </label>

                  <label
                    className={`flex cursor-pointer items-start gap-3 rounded-lg border p-3 transition-colors ${
                      depth === 'deep'
                        ? 'border-primary bg-primary/5'
                        : 'border-border'
                    }`}
                  >
                    <RadioGroupItem
                      value="deep"
                      className="mt-1"
                    />

                    <div>
                      <p className="text-sm font-medium">
                        Deep
                      </p>

                      <p className="text-xs text-muted-foreground">
                        Full repository deep analysis.
                      </p>
                    </div>
                  </label>
                </div>
              </RadioGroup>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">
                Include
              </CardTitle>
            </CardHeader>

            <CardContent className="space-y-3">
              {ALL_CATEGORIES.map((cat) => (
                <div
                  key={cat.key}
                  className="flex items-center space-x-3"
                >
                  <Checkbox
                    id={`cat-${cat.key}`}
                    checked={categories.includes(
                      cat.key
                    )}
                    disabled={isLoading}
                    onCheckedChange={() =>
                      toggleCategory(
                        cat.key
                      )
                    }
                  />

                  <Label
                    htmlFor={`cat-${cat.key}`}
                    className="cursor-pointer text-sm"
                  >
                    {cat.label}
                  </Label>
                </div>
              ))}

              {categories.includes(
                'security'
              ) && (
                <p className="text-xs text-muted-foreground">
                  Security signals are informational, not a definitive vulnerability scan.
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

