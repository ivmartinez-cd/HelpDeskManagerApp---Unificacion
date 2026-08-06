import { type HTMLAttributes } from "react";
import { cn } from "@/shared/utils/cn";

type Variant = "neutral" | "success" | "danger" | "accent";

const variants: Record<Variant, string> = {
  neutral: "bg-black/5 dark:bg-white/10 text-muted-foreground",
  success: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
  danger: "bg-destructive/10 text-destructive",
  accent: "bg-accent/10 text-accent",
};

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: Variant;
}

export function Badge({ variant = "neutral", className, children, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-1 text-[10px] font-black uppercase tracking-wide",
        variants[variant],
        className,
      )}
      {...props}
    >
      {children}
    </span>
  );
}
