import { type LucideIcon } from "lucide-react";
import { cn } from "@/shared/utils/cn";

type Tone = "neutral" | "accent" | "success" | "warning" | "info";

const toneClasses: Record<Tone, string> = {
  neutral: "border-black/10 dark:border-white/10 bg-black/[0.02] dark:bg-white/[0.02] text-foreground",
  accent: "border-accent/20 bg-accent/5 text-accent",
  success: "border-success/20 bg-success/5 text-success",
  warning: "border-warning/20 bg-warning/5 text-warning",
  info: "border-info/20 bg-info/5 text-info",
};

interface StatCardProps {
  label: string;
  value: string | number;
  tone?: Tone;
  icon?: LucideIcon;
  hint?: string;
}

export function StatCard({ label, value, tone = "neutral", icon: Icon, hint }: StatCardProps) {
  return (
    <div className={cn("rounded-2xl border p-4", toneClasses[tone])}>
      <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wide opacity-80">
        {Icon && <Icon className="h-3.5 w-3.5" />}
        {label}
      </div>
      <p className="mt-2 text-2xl font-black tracking-tight">{value}</p>
      {hint && <p className="mt-1 text-xs opacity-70">{hint}</p>}
    </div>
  );
}
