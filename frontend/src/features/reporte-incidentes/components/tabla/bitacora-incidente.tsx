import type { Trabajo } from "../../types/reporte";
import { cn } from "@/shared/utils/cn";
import { CLASE_ETIQUETA } from "./estilos";

/** Color del estado de un trabajo de la bitácora (mismo criterio que el legacy). */
function claseEstadoTrabajo(estado: string): string {
  const e = estado.toLowerCase();
  if (e === "finalizado" || e === "cerrado" || e === "resuelto") return "text-success bg-success/10 border-success";
  if (e === "en curso" || e === "derivado") return "text-info bg-info/10 border-info";
  return "text-muted-foreground bg-muted border-border";
}

/** Historial de trabajos del caso, en orden; sin trabajos cae a la solución. */
export function BitacoraIncidente({ trabajos, solucion }: { trabajos: Trabajo[]; solucion: string | null }) {
  return (
    <div className="flex flex-col gap-2.5">
      <span className={CLASE_ETIQUETA}>Historial de trabajos (bitácora)</span>
      {trabajos.length === 0 ? (
        <p className="rounded-[10px] border border-border bg-card px-3.5 py-3 font-body text-sm text-foreground">
          {solucion || "—"}
        </p>
      ) : (
        <ol>
          {trabajos.map((trabajo, i) => (
            <EntradaBitacora key={i} trabajo={trabajo} numero={i + 1} ultima={i === trabajos.length - 1} />
          ))}
        </ol>
      )}
    </div>
  );
}

function EntradaBitacora({ trabajo, numero, ultima }: { trabajo: Trabajo; numero: number; ultima: boolean }) {
  const conTecnico = trabajo.tecnico && trabajo.tecnico !== "(Ninguno)";
  const clasePunto = trabajo.estado ? claseEstadoTrabajo(trabajo.estado) : "border-border";
  return (
    <li className="relative flex gap-3.5 pb-3.5">
      {!ultima && <span className="absolute top-[18px] -bottom-3.5 left-[5px] w-0.5 bg-border" aria-hidden="true" />}
      <span
        className={cn("mt-1 h-3 w-3 flex-none rounded-full border-2 bg-card", ultima ? "border-brand-orange" : clasePunto)}
        aria-hidden="true"
      />
      <div className="flex min-w-0 flex-col gap-1">
        <div className="flex flex-wrap items-center gap-2.5">
          <span className="font-body text-[13px] font-bold text-foreground">Instancia {numero}</span>
          {trabajo.estado && (
            <span
              className={cn(
                "rounded-full border px-2 py-px font-body text-[10px] font-bold uppercase tracking-[.025em]",
                claseEstadoTrabajo(trabajo.estado),
              )}
            >
              {trabajo.estado}
            </span>
          )}
          {trabajo.fecha && <span className="font-body text-xs tabular-nums text-muted-foreground">{trabajo.fecha}</span>}
          {conTecnico && <span className="font-body text-xs text-muted-foreground">Téc: {trabajo.tecnico}</span>}
        </div>
        {trabajo.descripcion ? (
          <p className="font-body text-sm text-foreground">{trabajo.descripcion}</p>
        ) : (
          <p className="font-body text-[13px] italic text-muted-foreground">Sin tareas registradas en esta instancia</p>
        )}
        {trabajo.observ?.trim() && (
          <p className="font-body text-[13px] text-muted-foreground">
            <strong className="font-semibold text-foreground">Obs:</strong> {trabajo.observ}
          </p>
        )}
      </div>
    </li>
  );
}
