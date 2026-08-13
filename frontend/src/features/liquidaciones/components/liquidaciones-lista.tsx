"use client";

import { useCallback, useEffect, useState } from "react";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { Spinner } from "@/shared/components/ui/spinner";
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
  const [liquidaciones, setLiquidaciones] = useState<Liquidacion[]>([]);
  const [prestadores, setPrestadores] = useState<PrestadorLiquidacion[]>([]);
  const [loading, setLoading] = useState(true);
  const [filtroEstado, setFiltroEstado] = useState("");
  const [filtroPrestador, setFiltroPrestador] = useState("");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [importOpen, setImportOpen] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [deleteInProgress, setDeleteInProgress] = useState(false);

  // Sin setLoading(true) sincrónico: `loading` arranca en true y los reloads
  // posteriores muestran los datos viejos hasta que llega la respuesta
  // (react-hooks/set-state-in-effect prohíbe setState sincrónico en effects).
  const loadLiquidaciones = useCallback(
    async (p: number) => {
      try {
        const res = await liquidacionesApi.list({
          prestadorId: filtroPrestador || undefined,
          page: p,
          size: PAGE_SIZE,
        });
        setLiquidaciones(res.items);
        setTotal(res.total);
      } finally {
        setLoading(false);
      }
    },
    [filtroPrestador],
  );

  useEffect(() => {
    void liquidacionesApi.listPrestadores().then(setPrestadores);
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
  const filtered = filtroEstado
    ? liquidaciones.filter((l) => l.estado === filtroEstado)
    : liquidaciones;

  const selectCls =
    "rounded-[8px] border border-border bg-card px-3 py-2 font-body text-sm text-foreground outline-none focus:border-brand-orange/70";

  return (
    <div className="flex flex-col gap-5 p-6">
      <div className="flex items-center justify-between">
        <h1 className="font-heading text-xl font-extrabold text-foreground">Liquidaciones</h1>
        <button
          onClick={() => setImportOpen(true)}
          className="rounded-[8px] bg-brand-orange px-4 py-2.5 font-body text-sm font-semibold text-white transition-opacity hover:opacity-90"
        >
          + Importar
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <select
          value={filtroEstado}
          onChange={(e) => setFiltroEstado(e.target.value)}
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
          onChange={(e) => { setFiltroPrestador(e.target.value); setPage(1); }}
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

        <span className="ml-auto font-body text-sm text-muted-foreground">
          {total.toLocaleString("es-AR")} liquidaciones
        </span>
      </div>

      {loading ? (
        <div className="flex h-48 items-center justify-center">
          <Spinner />
        </div>
      ) : filtered.length === 0 ? (
        <p className="py-12 text-center font-body text-sm text-muted-foreground">
          No hay liquidaciones con los filtros seleccionados.
        </p>
      ) : (
        <>
          <LiquidacionesTabla
            items={filtered}
            prestadorMap={prestadorMap}
            onDelete={setDeletingId}
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
        <p className="font-body text-sm" style={{ color: "rgba(255,255,255,.7)" }}>
          Esta acción eliminará la liquidación y todos sus incidentes, alertas y observaciones.
          No se puede deshacer.
        </p>
        {deletingId && (() => {
          const liq = liquidaciones.find((l) => l.id === deletingId);
          return liq ? (
            <p className="mt-2 font-body text-sm font-semibold" style={{ color: "#e0e0e0" }}>
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
            className="rounded-[8px] px-4 py-2 font-body text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-50"
            style={{ background: "#ef4444" }}
          >
            {deleteInProgress ? "Eliminando..." : "Eliminar"}
          </button>
        </div>
      </BrandModal>
    </div>
  );
}
