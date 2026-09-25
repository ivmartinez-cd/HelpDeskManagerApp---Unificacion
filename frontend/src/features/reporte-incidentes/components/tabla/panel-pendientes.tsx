"use client";

import { ChevronDown, ChevronRight } from "lucide-react";
import type { Incidente } from "../../types/reporte";
import type { EstadoDashboard } from "../../hooks/use-reporte";
import { TAMANO_PAGINA_PENDIENTES, usePendientes } from "../../hooks/use-pendientes";
import { PaginationBar } from "@/shared/components/ui/pagination-bar";
import { cn } from "@/shared/utils/cn";
import { DetalleIncidente } from "./detalle-incidente";
import { EditorTipificacion } from "./editor-tipificacion";
import { URL_WEBAGENTES } from "./estilos";

function FilaPendiente({
  incidente,
  estado,
  expandida,
  onAlternar,
}: {
  incidente: Incidente;
  estado: EstadoDashboard;
  expandida: boolean;
  onAlternar: () => void;
}) {
  const Chevron = expandida ? ChevronDown : ChevronRight;
  return (
    <li className={cn("border-t border-border", expandida && "bg-surface-2")}>
      <div className="grid grid-cols-[28px_minmax(0,1fr)] gap-x-3 gap-y-3 px-4 py-3.5 sm:px-6 lg:grid-cols-[28px_120px_minmax(0,1fr)_minmax(0,560px)] lg:items-center">
        <button
          type="button"
          aria-label={expandida ? "Contraer detalle" : "Expandir detalle"}
          aria-expanded={expandida}
          onClick={onAlternar}
          className={cn("flex cursor-pointer rounded-[6px] p-1", expandida ? "text-brand-orange" : "text-muted-foreground")}
        >
          <Chevron className="h-4 w-4" aria-hidden="true" />
        </button>
        <div>
          <a
            href={`${URL_WEBAGENTES}${incidente.numero}`}
            target="_blank"
            rel="noopener noreferrer"
            className="font-body text-[13px] font-semibold tabular-nums text-brand-orange hover:underline"
          >
            {incidente.numero}
          </a>
          <div className="font-body text-xs text-muted-foreground">
            {incidente.fecha}
            {incidente.sucursal && ` · ${incidente.sucursal}`}
          </div>
        </div>
        <div className="col-span-2 font-body text-[13px] leading-[18px] lg:col-span-1">
          <p className="line-clamp-2 text-foreground">{incidente.descripcion || "—"}</p>
          <p className="line-clamp-2 text-muted-foreground">{incidente.solucion || incidente.causa || "—"}</p>
        </div>
        {estado.canUpdate && (
          <div className="col-span-2 lg:col-span-1">
            <EditorTipificacion
              incidente={incidente}
              taxonomia={estado.reporte?.taxonomia ?? []}
              onGuardado={estado.recargar}
              variante="fila"
            />
          </div>
        )}
      </div>
      {expandida && (
        <div className="px-4 pb-6 sm:pr-6 sm:pl-14">
          <DetalleIncidente incidente={incidente} estado={estado} />
        </div>
      )}
    </li>
  );
}

/** Cola "Pendientes de revisión" (port de `RevisionPanel`): casos que la IA
 * no tipificó con confianza alta. Colapsable; oculta si no hay ninguno. */
export function PanelPendientes({ estado }: { estado: EstadoDashboard }) {
  const panel = usePendientes(estado);
  const cantidad = estado.reporte?.pendientes_revision ?? 0;
  if (cantidad <= 0) return null;
  const Chevron = panel.abierto ? ChevronDown : ChevronRight;
  return (
    <section className="overflow-hidden rounded-[12px] border border-border bg-card" aria-busy={panel.cargando}>
      <header className="flex flex-wrap items-center gap-3 px-6 py-4">
        <button
          type="button"
          aria-expanded={panel.abierto}
          onClick={panel.alternarAbierto}
          className="flex cursor-pointer items-center gap-2.5 font-heading text-base font-bold text-foreground"
        >
          <Chevron className="h-[18px] w-[18px]" aria-hidden="true" />
          Pendientes de revisión ({cantidad.toLocaleString("es-AR")})
        </button>
        <span className="rounded-full bg-warning/10 px-2 py-0.5 font-body text-[10px] font-bold uppercase tracking-[.025em] text-warning">
          Requiere revisión
        </span>
        <span className="font-body text-[13px] text-muted-foreground lg:ml-auto">
          {estado.canUpdate
            ? "La IA no los tipificó con confianza alta. Elegí categoría y subcategoría y guardá."
            : "La IA no los tipificó con confianza alta. Los corrige alguien con permiso de edición."}
        </span>
      </header>
      {panel.abierto && <ListaPendientes panel={panel} estado={estado} />}
    </section>
  );
}

function ListaPendientes({ panel, estado }: { panel: ReturnType<typeof usePendientes>; estado: EstadoDashboard }) {
  if (panel.error) {
    return <p role="alert" className="border-t border-border px-6 py-4 font-body text-sm text-destructive">{panel.error}</p>;
  }
  if (panel.filas.length === 0) {
    return (
      <p className="border-t border-border px-6 py-6 text-center font-body text-sm text-muted-foreground">
        {panel.cargando ? "Cargando pendientes…" : "No quedan casos pendientes de revisión."}
      </p>
    );
  }
  return (
    <>
      <ul className={cn("transition-opacity", panel.cargando && "opacity-60")}>
        {panel.filas.map((incidente) => (
          <FilaPendiente
            key={incidente.id}
            incidente={incidente}
            estado={estado}
            expandida={panel.expandidas.has(incidente.id)}
            onAlternar={() => panel.alternarFila(incidente.id)}
          />
        ))}
      </ul>
      {panel.total > TAMANO_PAGINA_PENDIENTES && (
        <PaginationBar
          page={panel.page}
          total={panel.total}
          size={TAMANO_PAGINA_PENDIENTES}
          onPageChange={panel.setPage}
          noun="pendientes"
          className="border-t border-border px-4 py-3"
        />
      )}
    </>
  );
}
