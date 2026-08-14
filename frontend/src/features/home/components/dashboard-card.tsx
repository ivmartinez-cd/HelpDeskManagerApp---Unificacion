import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { Spinner } from "@/shared/components/ui/spinner";

interface DashboardCardProps {
  icon?: LucideIcon;
  title: string;
  subtitle?: string;
  /** Contenido a la derecha del header (badge, total, etc.). */
  headerRight?: ReactNode;
  loading?: boolean;
  error?: string | null;
  children?: ReactNode;
}

/** Shell de card del dashboard de Inicio (handoff design_handoff_inicio):
 * caja de ícono 34px naranja, título Montserrat 15px + subtítulo, radio 14. */
export function DashboardCard({
  icon: Icon,
  title,
  subtitle,
  headerRight,
  loading,
  error,
  children,
}: DashboardCardProps) {
  return (
    <div className="flex w-full flex-col rounded-[14px] border border-border bg-card p-5">
      <div className="flex items-center gap-2.5">
        {Icon && (
          <span className="flex h-[34px] w-[34px] shrink-0 items-center justify-center rounded-[9px] bg-brand-orange/[0.15] text-brand-orange">
            <Icon className="h-4 w-4" />
          </span>
        )}
        <div className="flex min-w-0 flex-1 flex-col">
          <h2 className="font-heading text-[15px] font-extrabold text-foreground">{title}</h2>
          {subtitle && (
            <span className="truncate font-body text-[12px] text-muted-foreground">
              {subtitle}
            </span>
          )}
        </div>
        {headerRight}
      </div>

      {loading ? (
        <div className="flex justify-center py-6">
          <Spinner />
        </div>
      ) : error ? (
        <span className="pt-3 font-body text-[13px] text-destructive">{error}</span>
      ) : (
        children
      )}
    </div>
  );
}
