
'use client';

import Link from 'next/link';
import { useCallback, useEffect, useState } from 'react';
import {
  Plus,
  MoreHorizontal,
  FileSearch,
  FileText,
  Trash2,
  RefreshCw,
} from 'lucide-react';

import { Card } from '@/components/ui/card';
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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

import { api } from '@/src/lib/api';

import type { Repository } from '@/src/types';

export default function RepositoriesPage() {
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadRepositories = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await api.listRepositories();

      /*
       * Always use the real backend response.
       * An empty array means there are currently
       * no repositories in the backend.
       */
      setRepositories(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Failed to load repositories:', err);

      setRepositories([]);

      setError(
        err instanceof Error
          ? err.message
          : 'Failed to load repositories.'
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadRepositories();
  }, [loadRepositories]);

  return (
    <div className="mx-auto max-w-7xl space-y-8 p-4 md:p-8">
      <PageHeader
        title="Repositories"
        subtitle="Manage repositories connected to RepoGuard."
        showDemo={false}
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={loadRepositories}
              disabled={loading}
            >
              <RefreshCw
                className={`mr-2 h-4 w-4 ${
                  loading ? 'animate-spin' : ''
                }`}
              />
              Refresh
            </Button>

            <Button size="sm" asChild>
              <Link href="/new-audit">
                <Plus className="mr-2 h-4 w-4" />
                Add Repository
              </Link>
            </Button>
          </div>
        }
      />

      {error && (
        <Card className="p-4">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="font-medium text-destructive">
                Unable to load repositories
              </p>

              <p className="mt-1 text-sm text-muted-foreground">
                {error}
              </p>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={loadRepositories}
              disabled={loading}
            >
              Try again
            </Button>
          </div>
        </Card>
      )}

      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Repository</TableHead>

              <TableHead>Source</TableHead>

              <TableHead className="hidden md:table-cell">
                URL
              </TableHead>

              <TableHead>Branch</TableHead>

              <TableHead className="text-right">
                Actions
              </TableHead>
            </TableRow>
          </TableHeader>

          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell
                  colSpan={5}
                  className="h-32 text-center text-muted-foreground"
                >
                  Loading repositories...
                </TableCell>
              </TableRow>
            ) : repositories.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={5}
                  className="h-32 text-center"
                >
                  <div className="flex flex-col items-center gap-2">
                    <p className="font-medium">
                      No repositories found
                    </p>

                    <p className="text-sm text-muted-foreground">
                      Upload or connect a repository to get started.
                    </p>

                    <Button size="sm" asChild>
                      <Link href="/new-audit">
                        <Plus className="mr-2 h-4 w-4" />
                        Add Repository
                      </Link>
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              repositories.map((repo) => (
                <TableRow key={repo.id}>
                  <TableCell>
                    <div className="min-w-0">
                      <p className="font-medium">
                        {repo.name || 'Unnamed Repository'}
                      </p>

                      {repo.source_url && (
                        <p className="max-w-[260px] truncate text-xs text-muted-foreground">
                          {repo.source_url}
                        </p>
                      )}
                    </div>
                  </TableCell>

                  <TableCell>
                    <Badge
                      variant="secondary"
                      className="text-xs capitalize"
                    >
                      {repo.source_type || 'unknown'}
                    </Badge>
                  </TableCell>

                  <TableCell className="hidden md:table-cell">
                    {repo.source_url ? (
                      <a
                        href={repo.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block max-w-[300px] truncate text-sm text-muted-foreground hover:text-foreground hover:underline"
                      >
                        {repo.source_url}
                      </a>
                    ) : (
                      <span className="text-sm text-muted-foreground">
                        —
                      </span>
                    )}
                  </TableCell>

                  <TableCell>
                    <code className="text-xs font-mono text-muted-foreground">
                      {repo.default_branch || '—'}
                    </code>
                  </TableCell>

                  <TableCell className="text-right">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                        >
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>

                      <DropdownMenuContent align="end">
                        <DropdownMenuItem asChild>
                          <Link href="/new-audit">
                            <FileSearch className="mr-2 h-4 w-4" />
                            Audit
                          </Link>
                        </DropdownMenuItem>

                        <DropdownMenuItem asChild>
                          <Link href={`/audits/${repo.id}`}>
                            <FileText className="mr-2 h-4 w-4" />
                            View Report
                          </Link>
                        </DropdownMenuItem>

                        <DropdownMenuItem
                          className="text-destructive"
                          disabled
                        >
                          <Trash2 className="mr-2 h-4 w-4" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}

