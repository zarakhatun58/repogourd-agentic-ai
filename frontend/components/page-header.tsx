import { cn } from '@/src/lib/utils';
import { DemoIndicator } from '@/components/demo-indicator';

export function PageHeader({
  title,
  subtitle,
  actions,
  showDemo = false,
  className,
}: {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
  showDemo?: boolean;
  className?: string;
}) {
  return (
    <div
      className={cn(
        'flex flex-col gap-4 border-b pb-6 md:flex-row md:items-center md:justify-between',
        className
      )}
    >
      <div className="space-y-1">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-bold tracking-tight md:text-2xl">{title}</h2>
          {showDemo && <DemoIndicator />}
        </div>
        {subtitle && (
          <p className="text-sm text-muted-foreground">{subtitle}</p>
        )}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}
