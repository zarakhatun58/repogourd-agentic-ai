import { cn } from '@/src/lib/utils';
import { Badge } from '@/components/ui/badge';
import type { Severity, RiskLevel } from '@/src/types';

const SEVERITY_STYLES: Record<Severity, string> = {
  critical:
    'border-transparent bg-destructive/15 text-destructive',

  high:
    'border-transparent bg-destructive/10 text-destructive',

  medium:
    'border-transparent bg-warning/15 text-warning',

  low:
    'border-transparent bg-info/15 text-info',

  info:
    'border-transparent bg-muted text-muted-foreground',
};

const RISK_STYLES: Record<RiskLevel, string> = {
  critical:
    'border-transparent bg-destructive/15 text-destructive',

  high:
    'border-transparent bg-destructive/10 text-destructive',

  medium:
    'border-transparent bg-warning/15 text-warning',

  low:
    'border-transparent bg-success/15 text-success',

  info:
    'border-transparent bg-info/15 text-info',
};

export function SeverityBadge({
  severity,
  className,
}: {
  severity: Severity;
  className?: string;
}) {
  return (
    <Badge
      variant="outline"
      className={cn(
        'font-semibold uppercase tracking-wide',
        SEVERITY_STYLES[severity],
        className
      )}
    >
      {severity}
    </Badge>
  );
}

export function RiskBadge({
  risk,
  className,
}: {
  risk: RiskLevel;
  className?: string;
}) {
  return (
    <Badge
      variant="outline"
      className={cn(
        'font-semibold uppercase tracking-wide',
        RISK_STYLES[risk],
        className
      )}
    >
      {risk}
    </Badge>
  );
}