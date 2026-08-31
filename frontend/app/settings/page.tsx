'use client';

import {
  Settings as SettingsIcon,
  Server,
  SlidersHorizontal,
  Palette,
  BarChart3,
  Info,
  CircleDot,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { PageHeader } from '@/components/page-header';
import { ThemeToggle } from '@/components/theme-toggle';
import { useHealth } from '@/src/hooks/use-health';
import { DEMO_MODE } from '@/src/lib/api';

export default function SettingsPage() {
  const { health, loading, check } = useHealth();

  return (
    <div className="mx-auto max-w-3xl space-y-8 p-4 md:p-8">
      <PageHeader title="Settings" showDemo={DEMO_MODE} />

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <SettingsIcon className="h-4 w-4 text-muted-foreground" />
            <CardTitle className="text-base">General</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label className="text-sm font-medium">Organization name</Label>
              <p className="text-xs text-muted-foreground">Displayed in reports and exports.</p>
            </div>
            <span className="text-sm text-muted-foreground">Engineering Team</span>
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div>
              <Label className="text-sm font-medium">Default analysis depth</Label>
              <p className="text-xs text-muted-foreground">Used for new audits.</p>
            </div>
            <Badge variant="secondary">Standard</Badge>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Server className="h-4 w-4 text-muted-foreground" />
            <CardTitle className="text-base">API Configuration</CardTitle>
          </div>
          <CardDescription>Connection status to the RepoGuard backend.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between rounded-lg border p-3">
            <div className="flex items-center gap-2">
              <CircleDot
                className={`h-3 w-3 ${
                  health.connected
                    ? 'text-success'
                    : DEMO_MODE
                      ? 'text-warning'
                      : 'text-destructive'
                }`}
              />
              <span className="text-sm font-medium">
                {health.connected
                  ? 'Connected'
                  : DEMO_MODE
                    ? 'Demo mode — backend not checked'
                    : 'Backend unavailable'}
              </span>
            </div>
            <Button variant="outline" size="sm" onClick={check} disabled={loading}>
              {loading ? 'Checking…' : 'Check now'}
            </Button>
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">API URL</span>
              <code className="font-mono text-xs">{apiBaseUrl()}</code>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Demo mode</span>
              <Badge variant={DEMO_MODE ? 'secondary' : 'outline'}>
                {DEMO_MODE ? 'Enabled' : 'Disabled'}
              </Badge>
            </div>
            {health.version && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Backend version</span>
                <span className="font-mono text-xs">{health.version}</span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="h-4 w-4 text-muted-foreground" />
            <CardTitle className="text-base">Analysis Defaults</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {['Architecture', 'Code Quality', 'Testing', 'Dependencies', 'Security Signals'].map(
            (cat, i) => (
              <div key={cat} className="flex items-center justify-between">
                <Label className="text-sm">{cat}</Label>
                <Switch defaultChecked={i < 4} />
              </div>
            )
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Palette className="h-4 w-4 text-muted-foreground" />
            <CardTitle className="text-base">Appearance</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <Label className="text-sm font-medium">Theme</Label>
              <p className="text-xs text-muted-foreground">Switch between light and dark.</p>
            </div>
            <ThemeToggle />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
            <CardTitle className="text-base">Evaluation</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label className="text-sm font-medium">Auto-run on new audits</Label>
              <p className="text-xs text-muted-foreground">
                Automatically evaluate baseline vs advanced after each audit.
              </p>
            </div>
            <Switch />
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div>
              <Label className="text-sm font-medium">Include cost metrics</Label>
              <p className="text-xs text-muted-foreground">
                Track cost per task in evaluations.
              </p>
            </div>
            <Switch defaultChecked />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Info className="h-4 w-4 text-muted-foreground" />
            <CardTitle className="text-base">About</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <p>RepoGuard AI — Evidence-backed software engineering audits.</p>
          <p>Version 1.0.0</p>
          <p>
            AI analysis backed by repository evidence. Findings are verified against
            source code before being reported.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

function apiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
}
