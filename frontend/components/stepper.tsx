import { cn } from '@/src/lib/utils';
import {
  Check,
  Loader2,
  X,
  Circle,
} from 'lucide-react';
import type { AuditStep } from '@/src/types';

const STATUS_ICON: Record<AuditStep['status'], React.ReactNode> = {
  completed: <Check className="h-3.5 w-3.5 text-success" />,
  running: <Loader2 className="h-3.5 w-3.5 animate-spin text-info" />,
  failed: <X className="h-3.5 w-3.5 text-destructive" />,
  pending: <Circle className="h-3.5 w-3.5 text-muted-foreground" />,
};

const STATUS_LABEL: Record<AuditStep['status'], string> = {
  completed: 'Completed',
  running: 'Running',
  failed: 'Failed',
  pending: 'Pending',
};

export function Stepper({ steps }: { steps: AuditStep[] }) {
  return (
    <ol className="relative space-y-4">
      {steps.map((step, idx) => (
        <li key={step.id} className="flex gap-4">
          <div className="flex flex-col items-center">
            <div
              className={cn(
                'flex h-8 w-8 items-center justify-center rounded-full border-2',
                step.status === 'completed' && 'border-success/30 bg-success/10',
                step.status === 'running' && 'border-info/30 bg-info/10',
                step.status === 'failed' && 'border-destructive/30 bg-destructive/10',
                step.status === 'pending' && 'border-border bg-muted'
              )}
            >
              {STATUS_ICON[step.status]}
            </div>
            {idx < steps.length - 1 && (
              <div
                className={cn(
                  'mt-1 h-full min-h-[2rem] w-0.5',
                  step.status === 'completed' ? 'bg-success/30' : 'bg-border'
                )}
              />
            )}
          </div>
          <div className="flex flex-col pb-2">
            <span className="text-sm font-medium">{step.label}</span>
            <span className="text-xs text-muted-foreground capitalize">
              {STATUS_LABEL[step.status]}
              {step.message && ` — ${step.message}`}
            </span>
          </div>
        </li>
      ))}
    </ol>
  );
}
