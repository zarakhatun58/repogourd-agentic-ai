import { cn } from '@/src/lib/utils';

export function CodeBlock({
  code,
  language,
  className,
}: {
  code: string;
  language?: string;
  className?: string;
}) {
  return (
    <div
      className={cn(
        'overflow-x-auto rounded-md border bg-muted/50 p-4 scrollbar-thin',
        className
      )}
    >
      {language && (
        <div className="mb-2 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
          {language}
        </div>
      )}
      <pre className="text-xs leading-relaxed">
        <code className="font-mono">{code}</code>
      </pre>
    </div>
  );
}
