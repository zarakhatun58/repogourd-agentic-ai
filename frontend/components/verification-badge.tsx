import { cn } from '@/src/lib/utils';
import { Badge } from '@/components/ui/badge';
import { CheckCircle2, AlertCircle, HelpCircle } from 'lucide-react';
import type { VerificationStatus } from '@/src/types';

const STYLES: Record<VerificationStatus, { className: string; icon: React.ReactNode }> = {
  verified: {
    className: 'border-transparent bg-success/15 text-success',
    icon: <CheckCircle2 className="h-3 w-3" />,
  },
  unverified: {
    className: 'border-transparent bg-destructive/15 text-destructive',
    icon: <AlertCircle className="h-3 w-3" />,
  },
  partial: {
    className: 'border-transparent bg-warning/15 text-warning',
    icon: <HelpCircle className="h-3 w-3" />,
  },
};

export function VerificationBadge({
  status,
  className,
}: {
  status: VerificationStatus;
  className?: string;
}) {
  const style = STYLES[status];
  return (
    <Badge
      variant="outline"
      className={cn('gap-1 font-medium capitalize', style.className, className)}
    >
      {style.icon}
      {status}
    </Badge>
  );
}
