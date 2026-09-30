import { incidentUrl } from "@/shared/utils/incident-link";

/** Chip de aviso con el caso relacionado de la misma sucursal (link a
 *  WebAgentes) y cuántos más hay además de ese. */
export function AvisoCasoSucursal({ id, total }: { id: number; total: number }) {
  const extra = total - 1;
  return (
    <span className="w-fit rounded px-1.5 py-0.5 text-xs font-semibold bg-warning/20 text-warning-foreground dark:text-warning">
      <a href={incidentUrl(id)} target="_blank" rel="noopener noreferrer" className="tabular-nums hover:underline">
        {id}
      </a>
      {extra > 0 ? ` +${extra}` : ""}
    </span>
  );
}
