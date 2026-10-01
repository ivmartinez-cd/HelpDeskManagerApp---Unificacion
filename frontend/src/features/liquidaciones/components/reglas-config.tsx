"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Badge } from "@/shared/components/ui/badge";
import { SortableHeader, type SortableColumn } from "@/shared/components/ui/sortable-header";
import { Spinner } from "@/shared/components/ui/spinner";
import { Tooltip } from "@/shared/components/ui/tooltip";
import { boolSortValue, useOptionalTableSort, useSortedRows } from "@/shared/hooks/use-optional-table-sort";
import { cn } from "@/shared/utils/cn";
import { liquidacionesApi } from "../api/liquidaciones-api";
import { useReglasAlerta } from "../hooks/use-reglas-alerta";
import type { ReglaAlerta } from "../types/liquidaciones";

const thCls =
  "py-3 px-4 font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground text-left";
const tdCls = "py-3 px-4 font-body text-sm text-foreground";

type SortKey = "codigo" | "nombre" | "descripcion" | "riesgoBase" | "activa" | "observaciones";

const COLUMNAS: SortableColumn<SortKey>[] = [
  { key: "codigo", label: "Código" },
  { key: "nombre", label: "Nombre" },
  { key: "descripcion", label: "Descripción" },
  { key: "riesgoBase", label: "Riesgo base", className: "text-right" },
  { key: "activa", label: "Activa" },
  {
    key: "observaciones",
    label: "Observaciones",
    title: "Segundo switch, solo para ALT005: además de la Alerta por-incidente, agrupa por corredor en otra alerta aparte",
  },
];

const DESC_PRIMERO: readonly SortKey[] = ["riesgoBase", "activa", "observaciones"];

function valorOrden(r: ReglaAlerta, key: SortKey) {
  if (key === "activa") return boolSortValue(r.activa);
  // Solo ALT005 tiene el switch; el resto muestra "—" y va al final.
  if (key === "observaciones") return r.codigo === "ALT005" ? boolSortValue(r.generaObservaciones) : null;
  return r[key];
}

function ToggleSwitch({ checked, onToggle, disabled }: {
  checked: boolean;
  onToggle: () => void;
  disabled: boolean;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={onToggle}
      className={cn(
        "relative h-5 w-9 rounded-full transition-colors disabled:opacity-50",
        checked ? "bg-brand-orange" : "bg-border",
      )}
    >
      <span
        className={cn(
          "absolute top-0.5 h-4 w-4 rounded-full bg-white transition-all",
          checked ? "left-[18px]" : "left-0.5",
        )}
      />
    </button>
  );
}

export function ReglasConfig() {
  const { reglas, loading, refetch: load } = useReglasAlerta();
  const [togglingCodigo, setTogglingCodigo] = useState<string | null>(null);
  const { sort, toggleSort } = useOptionalTableSort(DESC_PRIMERO);
  const filas = useSortedRows(reglas, sort, valorOrden);

  const handleToggle = async (regla: ReglaAlerta) => {
    setTogglingCodigo(regla.codigo);
    try {
      await liquidacionesApi.updateReglaActiva(regla.codigo, !regla.activa);
      toast.success(
        `${regla.codigo} ${regla.activa ? "desactivada — no genera más alertas" : "activada"}`,
      );
      void load();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Error al cambiar la regla");
    } finally {
      setTogglingCodigo(null);
    }
  };

  const handleToggleObservaciones = async (regla: ReglaAlerta) => {
    setTogglingCodigo(regla.codigo);
    try {
      await liquidacionesApi.updateReglaGeneraObservaciones(
        regla.codigo,
        !regla.generaObservaciones,
      );
      toast.success(
        regla.generaObservaciones
          ? `${regla.codigo}: dejó de generar Observaciones agrupadas (la Alerta por-incidente sigue igual)`
          : `${regla.codigo}: vuelve a generar Observaciones agrupadas`,
      );
      void load();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Error al cambiar la regla");
    } finally {
      setTogglingCodigo(null);
    }
  };

  if (loading) {
    return (
      <div className="flex h-48 items-center justify-center">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-5 p-6">
      <div>
        <h1 className="font-heading text-2xl font-extrabold text-foreground">Reglas de alerta</h1>
        <p className="mt-1 font-body text-sm text-muted-foreground">
          Qué controles corre el motor sobre cada liquidación. Desactivar una regla hace
          que deje de generar alertas <span className="font-semibold text-foreground">a
          partir del próximo re-análisis</span> — las alertas ya generadas no se tocan.
          ALT005 además genera Observaciones agrupadas por corredor, con su propio
          switch independiente (columna &quot;Observaciones&quot;) — solo tiene efecto
          mientras la regla esté activa.
        </p>
      </div>
      <div className="overflow-hidden rounded-[12px] border border-border bg-card">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-muted/40">
                {COLUMNAS.map((c) => (
                  <SortableHeader key={c.key} column={c} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
                ))}
              </tr>
            </thead>
            <tbody>
              {filas.map((r) => (
                <tr key={r.codigo} className={cn("border-t border-border", !r.activa && "opacity-60")}>
                  <td className={`${tdCls} font-semibold`}>
                    <span className="flex items-center gap-2">
                      {r.codigo}
                      {!r.tieneEvaluador && (
                        <Tooltip content={
                          <span className="font-body text-xs">
                            Esta regla existe en el catálogo pero todavía no tiene lógica
                            implementada: activarla no genera ninguna alerta.
                          </span>
                        }>
                          <Badge variant="neutral">Sin evaluador</Badge>
                        </Tooltip>
                      )}
                    </span>
                  </td>
                  <td className={tdCls}>{r.nombre}</td>
                  <td className={`${tdCls} text-muted-foreground`}>{r.descripcion ?? "—"}</td>
                  <td className={`${tdCls} text-right tabular-nums`}>{r.riesgoBase}</td>
                  <td className={tdCls}>
                    <ToggleSwitch
                      checked={r.activa}
                      disabled={togglingCodigo === r.codigo}
                      onToggle={() => void handleToggle(r)}
                    />
                  </td>
                  <td className={tdCls}>
                    {r.codigo === "ALT005" ? (
                      <ToggleSwitch
                        checked={r.generaObservaciones}
                        disabled={togglingCodigo === r.codigo || !r.activa}
                        onToggle={() => void handleToggleObservaciones(r)}
                      />
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
