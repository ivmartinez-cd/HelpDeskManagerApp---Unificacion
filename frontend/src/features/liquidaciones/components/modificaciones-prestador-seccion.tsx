"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { SortableHeader } from "@/shared/components/ui/sortable-header";
import { compareSortValues, useTableSort } from "@/shared/hooks/use-table-sort";
import { modificacionesApi } from "../api/modificaciones-api";
import type { ModificacionPrestador } from "../types/modificacion";
import { retirarToastModificacion } from "../utils/toast-modificaciones";

type SortKey = "incidente" | "tipo" | "campo" | "antes" | "despues" | "cuando";

const SORT_KEYS: readonly SortKey[] = ["incidente", "tipo", "campo", "antes", "despues", "cuando"];

const TIPO_LABEL: Record<ModificacionPrestador["tipoCambio"], string> = {
  alta: "Alta",
  baja: "Baja",
  modificacion: "Modificación",
};

const thCls =
  "py-3 px-4 font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground text-left";

function formatFecha(iso: string): string {
  return new Date(iso).toLocaleString("es-AR", { dateStyle: "short", timeStyle: "short" });
}

/** Historial de cambios que el prestador aplicó sobre esta liquidación
 * (ADR-038) — no son alertas del motor de reglas: son eventos que ya no se
 * pueden recalcular (el valor anterior se pierde en cuanto se aplica el
 * diff), por eso viven acá aparte de la tabla de incidentes/alertas. */
export function ModificacionesPrestadorSeccion({ liquidacionId }: { liquidacionId: string }) {
  const [items, setItems] = useState<ModificacionPrestador[]>([]);
  const [loading, setLoading] = useState(true);
  const [marcando, setMarcando] = useState(false);
  const { sort, toggleSort } = useTableSort<SortKey>({
    initial: { key: "cuando", direction: "desc" },
    keys: SORT_KEYS,
    descFirstKeys: ["cuando"],
  });

  const cargar = useCallback(() => {
    setLoading(true);
    modificacionesApi
      .listByLiquidacion(liquidacionId, 1, 500)
      .then((pagina) => setItems(pagina.items))
      .catch((err: unknown) => {
        console.error("Error al cargar modificaciones del prestador:", err);
      })
      .finally(() => setLoading(false));
  }, [liquidacionId]);

  useEffect(() => {
    cargar();
  }, [cargar]);

  const sinVer = items.filter((m) => m.vistaEn === null).length;

  const marcarVistas = async () => {
    setMarcando(true);
    try {
      await modificacionesApi.marcarVistas(liquidacionId);
      retirarToastModificacion(`modificaciones:${liquidacionId}`);
      cargar();
    } catch (err) {
      console.error("Error al marcar modificaciones como vistas:", err);
    } finally {
      setMarcando(false);
    }
  };

  const sorted = useMemo(() => {
    return [...items].sort((a, b) => {
      const getSv = (m: ModificacionPrestador) => {
        switch (sort.key) {
          case "incidente": return m.numeroIncidente;
          case "tipo": return TIPO_LABEL[m.tipoCambio];
          case "campo": return m.campo;
          case "antes": return m.valorAnterior;
          case "despues": return m.valorNuevo;
          case "cuando": return m.detectadaEn;
        }
      };
      return compareSortValues(getSv(a), getSv(b), sort.direction);
    });
  }, [items, sort]);

  if (loading) return null;
  if (items.length === 0) return null;

  return (
    <div className="overflow-hidden rounded-[12px] border border-border bg-card">
      <div className="flex items-center justify-between gap-3 border-b border-border px-4 py-3">
        <p className="font-body text-sm font-semibold text-foreground">
          Modificaciones del prestador
          {sinVer > 0 && (
            <span className="ml-2 rounded-full bg-brand-orange px-2 py-0.5 font-heading text-[11px] font-bold text-white">
              {sinVer} sin ver
            </span>
          )}
        </p>
        {sinVer > 0 && (
          <button
            type="button"
            onClick={marcarVistas}
            disabled={marcando}
            className="rounded-[6px] border border-border px-3 py-1.5 font-body text-xs font-semibold text-foreground hover:bg-muted disabled:opacity-50"
          >
            Marcar como vistas
          </button>
        )}
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-muted/40">
              <SortableHeader column={{ key: "incidente", label: "Incidente" }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
              <SortableHeader column={{ key: "tipo", label: "Tipo" }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
              <SortableHeader column={{ key: "campo", label: "Campo" }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
              <SortableHeader column={{ key: "antes", label: "Antes" }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
              <SortableHeader column={{ key: "despues", label: "Después" }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
              <SortableHeader column={{ key: "cuando", label: "Cuándo" }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
            </tr>
          </thead>
          <tbody>
            {sorted.map((m) => (
              <tr key={m.id} className={m.vistaEn === null ? "bg-brand-orange/[0.05]" : undefined}>
                <td className="px-4 py-2 font-body text-sm text-foreground">{m.numeroIncidente}</td>
                <td className="px-4 py-2 font-body text-sm text-foreground">{TIPO_LABEL[m.tipoCambio]}</td>
                <td className="px-4 py-2 font-body text-sm text-foreground">{m.campo ?? "—"}</td>
                <td className="px-4 py-2 font-body text-sm text-muted-foreground">{m.valorAnterior ?? "—"}</td>
                <td className="px-4 py-2 font-body text-sm text-foreground">{m.valorNuevo ?? "—"}</td>
                <td className="px-4 py-2 font-body text-sm text-muted-foreground">{formatFecha(m.detectadaEn)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
