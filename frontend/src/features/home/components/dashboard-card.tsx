import type { LucideIcon } from "lucide-react";
import { RotateCw } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/shared/utils/cn";
import { useScrollShadow } from "../hooks/use-scroll-shadow";
import { DashboardCardSkeleton } from "./dashboard-card-skeleton";

interface DashboardCardProps {
  icon?: LucideIcon;
  title: string;
  subtitle?: string;
  /** Contenido a la derecha del header (badge, total, acciones). */
  headerRight?: ReactNode;
  loading?: boolean;
  error?: string | null;
  /** Si se pasa, el estado de error muestra "Reintentar". */
  onRetry?: () => void;
  /** Pie fijo (frescura + link), fuera del área con scroll. */
  footer?: ReactNode;
  /** Clases extra del cuerpo con scroll (p. ej. `@container`). */
  bodyClassName?: string;
  children?: ReactNode;
}

/** Shell único de las cards de Inicio. Llena SIEMPRE la celda que le toca
 * (h-full, min-h-0): el alto lo dicta el grid de viewport fijo, y lo que no
 * entra scrollea adentro del cuerpo — nunca la página. Header compacto
 * (ícono 28, título 14), cuerpo `flex-1 overflow-y-auto`, pie opcional. */
export function DashboardCard({
  icon: Icon,
  title,
  subtitle,
  headerRight,
  loading,
  error,
  onRetry,
  footer,
  bodyClassName,
  children,
}: DashboardCardProps) {
  const { ref: bodyRef, bottom: cortado } = useScrollShadow<HTMLDivElement>();

  return (
    <section
      aria-label={title}
      className="flex h-full min-h-0 w-full flex-col rounded-[12px] border border-border bg-card p-3.5 short:p-3"
    >
      <header className="flex flex-none items-center gap-2.5">
        {Icon && (
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-[8px] bg-brand-orange/[0.12] text-brand-orange short:hidden">
            <Icon className="h-[15px] w-[15px]" />
          </span>
        )}
        <div className="flex min-w-0 flex-1 flex-col leading-tight">
          <h2 className="truncate font-heading text-[14px] font-bold text-foreground">{title}</h2>
          {subtitle && (
            <span className="truncate font-body text-[12px] text-muted-foreground short:hidden">{subtitle}</span>
          )}
        </div>
        {headerRight && <div className="flex shrink-0 items-center gap-1.5">{headerRight}</div>}
      </header>

      <div
        ref={bodyRef}
        className={cn(
          "mt-2.5 flex min-h-0 flex-1 flex-col overflow-y-auto thin-scrollbar short:mt-2",
          cortado && !loading && !error && "mask-fade-bottom",
          bodyClassName,
        )}
      >
        {loading ? (
          <DashboardCardSkeleton inline />
        ) : error ? (
          <CardError mensaje={error} onRetry={onRetry} />
        ) : (
          children
        )}
      </div>

      {footer && !loading && (
        <footer className="mt-2 flex flex-none flex-wrap items-center justify-between gap-x-3 gap-y-1 border-t border-border/60 pt-2 short:mt-1.5 short:pt-1.5">
          {footer}
        </footer>
      )}
    </section>
  );
}

function CardError({ mensaje, onRetry }: { mensaje: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-start gap-2 pt-1">
      <span className="font-body text-[12.5px] text-destructive">{mensaje}</span>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="inline-flex items-center gap-1.5 rounded-[8px] border border-border px-2.5 py-1 font-body text-[12px] font-semibold text-foreground hover:bg-muted"
        >
          <RotateCw className="h-3 w-3" />
          Reintentar
        </button>
      )}
    </div>
  );
}
