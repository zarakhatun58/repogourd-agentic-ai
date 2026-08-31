import { cn } from '@/src/lib/utils';
import { FlaskConical } from 'lucide-react';

export function DemoIndicator({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-md bg-warning/10 px-2.5 py-1 text-xs font-medium text-warning',
        className
      )}
    >
      <FlaskConical className="h-3 w-3" />
      Demo data
    </span>
  );
}
