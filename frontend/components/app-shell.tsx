'use client';

import { usePathname } from 'next/navigation';
import { Sidebar } from '@/components/sidebar';
import { MobileNav } from '@/components/mobile-nav';
import { ThemeToggle } from '@/components/theme-toggle';

const PAGE_TITLES: Record<string, string> = {
  '/': 'Dashboard',
  '/new-audit': 'New Audit',
  '/audits': 'Audits',
  '/repositories': 'Repositories',
  '/evaluation': 'Evaluation',
  '/trajectories': 'Agent Traces',
  '/settings': 'Settings',
};

function getPageTitle(pathname: string): string {
  if (PAGE_TITLES[pathname]) return PAGE_TITLES[pathname];
  if (pathname.startsWith('/audits/')) return 'Audit Report';
  if (pathname.startsWith('/analysis/')) return 'Analysis';
  if (pathname.startsWith('/architecture/')) return 'Architecture';
  if (pathname.startsWith('/testing/')) return 'Testing Analysis';
  if (pathname.startsWith('/dependencies/')) return 'Dependencies';
  return 'RepoGuard AI';
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="flex h-screen overflow-hidden">
      <div className="hidden md:flex">
        <Sidebar />
      </div>
      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-16 items-center justify-between border-b bg-card px-4 md:px-6">
          <div className="flex items-center gap-3">
            <div className="md:hidden">
              <MobileNav />
            </div>
            <h1 className="text-base font-semibold md:text-lg">
              {getPageTitle(pathname)}
            </h1>
          </div>
          <div className="hidden md:flex">
            <ThemeToggle />
          </div>
        </header>
        <main className="flex-1 overflow-y-auto scrollbar-thin">
          {children}
        </main>
      </div>
    </div>
  );
}
