import { cn } from "@/shared/utils/cn";

/** Esqueleto con la forma de una card (header + líneas), en vez de un
 * spinner centrado: no produce salto de layout al cargar y es el fallback
 * tanto de `next/dynamic` (card completa) como del estado `loading` del
 * shell (`inline`, solo el cuerpo). */
export function DashboardCardSkeleton({ inline = false }: { inline?: boolean }) {
  const cuerpo = (
    <div className="flex flex-col gap-2 pt-1" aria-hidden="true">
      <div className="h-3 w-1/2 rounded bg-muted" />
      <div className="h-3 w-3/4 rounded bg-muted" />
      <div className="h-3 w-2/3 rounded bg-muted" />
      <div className="h-3 w-1/3 rounded bg-muted" />
    </div>
  );
  if (inline) {
    return (
      <div role="status" aria-label="Cargando" className="animate-pulse">
        {cuerpo}
      </div>
    );
  }
  return (
    <div
      role="status"
      aria-label="Cargando"
      className={cn(
        "flex h-full min-h-0 w-full animate-pulse flex-col rounded-[12px] border border-border bg-card p-3.5",
      )}
    >
      <div className="flex items-center gap-2.5" aria-hidden="true">
        <div className="h-7 w-7 rounded-[8px] bg-muted" />
        <div className="h-3.5 w-40 rounded bg-muted" />
      </div>
      <div className="mt-3">{cuerpo}</div>
    </div>
  );
}
