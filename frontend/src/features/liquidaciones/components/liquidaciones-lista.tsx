"use client";

import { useCallback, useEffect, useState, type ChangeEvent } from "react";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { Spinner } from "@/shared/components/ui/spinner";
import { useSession } from "@/services/session-provider";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { Liquidacion, PrestadorLiquidacion } from "../types/liquidaciones";
import { LiquidacionesImportModal } from "./liquidaciones-import-modal";
import { LiquidacionesTabla } from "./liquidaciones-tabla";

const ESTADOS: { value: string; label: string }[] = [
  { value: "", label: "-- Todos --" },
  { value: "abierta", label: "Abierta" },
  { value: "preliquidada", label: "Preliquidada" },
  { value: "recibida", label: "Recibida" },
  { value: "observada", label: "Observada" },
  { value: "aprobada", label: "Aprobada" },
  { value: "cerrada", label: "Cerrada" },
];

const PAGE_SIZE = 50;

export function LiquidacionesLista() {
  // Importar = liquidaciones.create; DELETE /{id} (baja local) = update (ADR-029).
  const { can } = useSession();
  const puedeImportar = can("liquidaciones", "create");
  const puedeEliminar = can("liquidaciones", "update");
  const [liquidaciones, setLiquidaciones] = useState<Liquidacion[]>([]);
  const [prestadores, setPrestadores] = useState<PrestadorLiquidacion[]>([]);
  const [periodos, setPeriodos] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [filtroEstado, setFiltroEstado] = useState("");
  const [filtroPrestador, setFiltroPrestador] = useState("");
  const [filtroPeriodo, setFiltroPeriodo] = useState("");
  const [filtroAnio, setFiltroAnio] = useState("");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [importOpen, setImportOpen] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [deleteInProgress, setDeleteInProgress] = useState(false);

  // Sin setLoading(true) sincrónico — ver nota en liquidaciones-dashboard.tsx.
  const loadLiquidaciones = useCallback(
    async (p: number) => {
      try {
        const res = await liquidacionesApi.list({
          prestadorId: filtroPrestador || undefined,
          estado: filtroEstado || undefined,
          periodo: filtroPeriodo || undefined,
          anio: filtroAnio ? Number(filtroAnio) : undefined,
          page: p,
          size: PAGE_SIZE,
        });
        setLiquidaciones(res.items);
        setTotal(res.total);
      } finally {
        setLoading(false);
      }
    },
    [filtroPrestador, filtroEstado, filtroPeriodo, filtroAnio],
  );

  useEffect(() => {
    void Promise.all([
      liquidacionesApi.listPrestadores().then(setPrestadores),
      liquidacionesApi.listPeriodos().then(setPeriodos),
    ]);
  }, []);

  useEffect(() => {
    void loadLiquidaciones(1);
  }, [loadLiquidaciones]);

  const handleConfirmDelete = async () => {
    if (!deletingId) return;
    setDeleteInProgress(true);
    try {
      await liquidacionesApi.delete(deletingId);
      setDeletingId(null);
      void loadLiquidaciones(page);
    } finally {
      setDeleteInProgress(false);
    }
  };

  const prestadorMap = Object.fromEntries(prestadores.map((p) => [p.id, p]));
  const anios = Array.from(new Set(periodos.map((p) => p.slice(0, 4)))).sort().reverse();

  const selectCls =
    "rounded-[8px] border border-border bg-card px-3 py-2 font-body text-sm text-foreground outline-none focus:border-brand-orange/70";

  const handleFilter = (setter: (v: string) => void) => (e: ChangeEvent<HTMLSelectElement>) => {
    setter(e.target.value);
    setPage(1);
  };

  return (
    <div className="flex flex-col gap-5 p-6">
      <div className="flex items-center justify-between">
        <h1 className="font-heading text-xl font-extrabold text-foreground">Liquidaciones</h1>
        {puedeImportar && (
          <button
            onClick={() => setImportOpen(true)}
            className="rounded-[8px] bg-brand-orange px-4 py-2.5 font-body text-sm font-semibold text-white transition-opacity hover:opacity-90"
          >
            + Importar
          </button>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <select
          value={filtroEstado}
          onChange={handleFilter(setFiltroEstado)}
          className={selectCls}
          aria-label="Filtrar por estado"
        >
          {ESTADOS.map((e) => (
            <option key={e.value} value={e.value}>
              {e.label}
            </option>
          ))}
        </select>

        <select
          value={filtroPrestador}
          onChange={handleFilter(setFiltroPrestador)}
          className={selectCls}
          aria-label="Filtrar por prestador"
        >
          <option value="">Todos los prestadores</option>
          {prestadores.map((p) => (
            <option key={p.id} value={p.id}>
              {p.nombreCorto}
            </option>
          ))}
        </select>

        <select
          value={filtroPeriodo}
          onChange={handleFilter(setFiltroPeriodo)}
          className={selectCls}
          aria-label="Filtrar por período"
        >
          <option value="">Todos los períodos</option>
          {periodos.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>

        <select
          value={filtroAnio}
          onChange={handleFilter(setFiltroAnio)}
          className={selectCls}
          aria-label="Filtrar por año"
        >
          <option value="">Todos los años</option>
          {anios.map((a) => (
            <option key={a} value={a}>
              {a}
            </option>
          ))}
        </select>

        <span className="ml-auto font-body text-sm text-muted-foreground">
          {total.toLocaleString("es-AR")} liquidaciones
        </span>
      </div>

      {loading ? (
        <div className="flex h-48 items-center justify-center">
          <Spinner />
        </div>
      ) : liquidaciones.length === 0 ? (
        <p className="py-12 text-center font-body text-sm text-muted-foreground">
          No hay liquidaciones con los filtros seleccionados.
        </p>
      ) : (
        <>
          <LiquidacionesTabla
            items={liquidaciones}
            prestadorMap={prestadorMap}
            onDelete={puedeEliminar ? setDeletingId : undefined}
          />

          {total > PAGE_SIZE && (
            <div className="flex items-center justify-between">
              <span className="font-body text-sm text-muted-foreground">
                Mostrando {(page - 1) * PAGE_SIZE + 1}–
                {Math.min(page * PAGE_SIZE, total)} de {total}
              </span>
              <div className="flex gap-2">
                <button
                  disabled={page <= 1}
                  onClick={() => {
                    const p = page - 1;
                    setPage(p);
                    void loadLiquidaciones(p);
                  }}
                  className="rounded-[8px] border border-border px-3 py-1.5 font-body text-sm text-muted-foreground transition-colors hover:bg-muted disabled:opacity-40"
                >
                  Anterior
                </button>
                <button
                  disabled={page * PAGE_SIZE >= total}
                  onClick={() => {
                    const p = page + 1;
                    setPage(p);
                    void loadLiquidaciones(p);
                  }}
                  className="rounded-[8px] border border-border px-3 py-1.5 font-body text-sm text-muted-foreground transition-colors hover:bg-muted disabled:opacity-40"
                >
                  Siguiente
                </button>
              </div>
            </div>
          )}
        </>
      )}

      <LiquidacionesImportModal
        isOpen={importOpen}
        onClose={() => setImportOpen(false)}
        prestadores={prestadores}
        onSuccess={() => void loadLiquidaciones(page)}
      />

      <BrandModal
        isOpen={deletingId !== null}
        onClose={() => setDeletingId(null)}
        title="Eliminar liquidación"
        widthPx={420}
      >
        <p className="font-body text-sm text-muted-foreground">
          Esta acción eliminará la liquidación y todos sus incidentes, alertas y observaciones.
          No se puede deshacer.
        </p>
        {deletingId && (() => {
          const liq = liquidaciones.find((l) => l.id === deletingId);
          return liq ? (
            <p className="mt-2 font-body text-sm font-semibold text-foreground">
              {liq.nombreArchivo ?? `Liquidación ${liq.periodo}`}
            </p>
          ) : null;
        })()}
        <div className="mt-6 flex justify-end gap-3">
          <button
            onClick={() => setDeletingId(null)}
            className="rounded-[8px] border border-border px-4 py-2 font-body text-sm text-muted-foreground transition-colors hover:bg-muted"
          >
            Cancelar
          </button>
          <button
            onClick={() => void handleConfirmDelete()}
            disabled={deleteInProgress}
            className="rounded-[8px] bg-destructive px-4 py-2 font-body text-sm font-semibold text-destructive-foreground transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {deleteInProgress ? "Eliminando..." : "Eliminar"}
          </button>
        </div>
      </BrandModal>
    </div>
  );
}
