import { type HTMLAttributes } from "react";
import { type LucideIcon } from "lucide-react";
import { cn } from "@/shared/utils/cn";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "overflow-hidden rounded-2xl border border-black/10 dark:border-white/10 bg-card shadow-sm",
        className,
      )}
      {...props}
    />
  );
}

interface CardHeaderProps {
  title: string;
  description?: string;
  icon?: LucideIcon;
}

export function CardHeader({ title, description, icon: Icon }: CardHeaderProps) {
  return (
    <div className="flex items-start gap-3 border-b border-black/10 dark:border-white/10 p-6 pb-5">
      {Icon && (
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-accent/10 text-accent">
          <Icon className="h-5 w-5" />
        </span>
      )}
      <div>
        <h2 className="text-lg font-black uppercase tracking-tight text-foreground">{title}</h2>
        {description && <p className="mt-0.5 text-sm text-muted-foreground">{description}</p>}
      </div>
    </div>
  );
}

export function CardBody({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("p-6", className)} {...props} />;
}
