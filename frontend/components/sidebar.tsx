'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  FileSearch,
  ClipboardList,
  GitBranch,
  BarChart3,
  Route,
  Settings,
  ShieldCheck,
  CircleDot,
} from 'lucide-react';
import { cn } from '@/src/lib/utils';
import { useHealth } from '@/src/hooks/use-health';
import { DEMO_MODE } from '@/src/lib/api';

const NAV_ITEMS = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/new-audit', label: 'New Audit', icon: FileSearch },
  { href: '/audits', label: 'Audits', icon: ClipboardList },
  { href: '/repositories', label: 'Repositories', icon: GitBranch },
  { href: '/evaluation', label: 'Evaluation', icon: BarChart3 },
  { href: '/trajectories', label: 'Agent Traces', icon: Route },
  { href: '/settings', label: 'Settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { health } = useHealth();

  return (
    <aside className="flex h-full w-64 flex-col border-r bg-card">
      <div className="flex h-16 items-center gap-2.5 border-b px-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
          <ShieldCheck className="h-5 w-5 text-primary-foreground" />
        </div>
        <div className="flex flex-col">
          <span className="text-sm font-semibold leading-tight">RepoGuard AI</span>
          <span className="text-[10px] text-muted-foreground">Evidence-backed audits</span>
        </div>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto p-3 scrollbar-thin">
        {NAV_ITEMS.map((item) => {
          const active =
            item.href === '/'
              ? pathname === '/'
              : pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                active
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-accent hover:text-foreground'
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t p-4 space-y-3">
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <CircleDot
              className={cn(
                'h-3 w-3',
                health.connected
                  ? 'text-success'
                  : DEMO_MODE
                    ? 'text-warning'
                    : 'text-destructive'
              )}
            />
            <span className="text-muted-foreground">
              {health.connected
                ? 'Connected'
                : DEMO_MODE
                  ? 'Demo mode'
                  : 'Backend unavailable'}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2 rounded-md bg-muted/50 px-3 py-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-secondary text-xs font-semibold">
            EN
          </div>
          <div className="flex flex-col">
            <span className="text-xs font-medium leading-tight">Engineer</span>
            <span className="text-[10px] text-muted-foreground">
              {DEMO_MODE ? 'Demo environment' : health.environment ?? 'Production'}
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
}
