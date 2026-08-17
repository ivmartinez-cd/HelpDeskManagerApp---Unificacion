import { cn } from "@/shared/utils/cn";

export function KpiTile({
  icon,
  label,
  value,
  warn,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  warn?: boolean;
}) {
  return (
    <div
      className={cn(
        "flex min-w-[130px] items-start gap-3 rounded-[10px] border px-4 py-3",
        warn ? "border-brand-orange/30 bg-brand-orange/5" : "border-border bg-background/20",
      )}
    >
      <div className={cn("mt-0.5 flex-shrink-0", warn ? "text-brand-orange" : "text-muted-foreground")}>
        {icon}
      </div>
      <div className="flex flex-col gap-0.5">
        <span className="font-body text-[10px] font-bold uppercase tracking-[.08em] text-muted-foreground">
          {label}
        </span>
        <span className={cn("font-heading text-2xl font-extrabold", warn ? "text-brand-orange" : "text-foreground")}>
          {value}
        </span>
      </div>
    </div>
  );
}
