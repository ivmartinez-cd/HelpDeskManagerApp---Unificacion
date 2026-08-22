import { Spinner } from "@/shared/components/ui/spinner";

/** Fallback de `next/dynamic` para las cards del dashboard de Inicio que
 * cargan chart.js (bundle pesado, code-split fuera del chunk inicial de la
 * ruta) — mismo shell que `DashboardCard` en estado `loading`, sin título
 * porque en este punto todavía no cargó el componente real. */
export function DashboardCardSkeleton() {
  return (
    <div className="flex w-full flex-col rounded-[14px] border border-border bg-card p-4">
      <div className="flex justify-center py-6">
        <Spinner />
      </div>
    </div>
  );
}
