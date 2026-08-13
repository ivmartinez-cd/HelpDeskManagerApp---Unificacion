"use client";

import { Map } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { BrandButton, BrandEmptyState } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { Spinner } from "@/shared/components/ui/spinner";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { PrestadorLiquidacion, Spst, TablaKm } from "../types/liquidaciones";
import { CsvImportModal, EntradaModal } from "./tabla-km-modales";

export function TablaKmConfig() {
  const [entradas, setEntradas] = useState<TablaKm[]>([]);
  const [prestadores, setPrestadores] = useState<PrestadorLiquidacion[]>([]);
  const [spsts, setSpsts] = useState<Spst[]>([]);
  const [loading, setLoading] = useState(true);
  const [filtroPst, setFiltroPst] = useState("");
  const [busqueda, setBusqueda] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<TablaKm | null>(null);
  const [csvOpen, setCsvOpen] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [expandidos, setExpandidos] = useState<Record<string, boolean>>({});

  // Sin setLoading(true) sincrónico — ver nota en liquidaciones-lista.tsx.
  const load = useCallback(async () => {
    try {
      const [e, p, s] = await Promise.all([
        liquidacionesApi.listTablaKm(),
        liquidacionesApi.listPrestadores(false),
        liquidacionesApi.listSpsts(),
      ]);
      setEntradas(e);
      setPrestadores(p);
      setSpsts(s);
      setExpandidos(Object.fromEntries(p.map((pst) => [pst.id, true])));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const handleDelete = async () => {
    if (!deletingId) return;
    try {
      await liquidacionesApi.deleteTablaKm(deletingId);
      toast.success("Entrada eliminada");
      setDeletingId(null);
      void load();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Error al eliminar");
    }
  };

  const handleDownload = async () => {
    try { await liquidacionesApi.exportTablaKmCsv(); }
    catch { toast.error("Error al descargar"); }
  };

  const toggleExpand = (id: string) => setExpandidos((prev) => ({ ...prev, [id]: !prev[id] }));

  const q = busqueda.toLowerCase();
  const pstList = filtroPst ? prestadores.filter((p) => p.id === filtroPst) : prestadores;
  const filtered = entradas.filter((e) => {
    if (filtroPst && e.prestadorId !== filtroPst) return false;
    if (q && !e.empresaNombre.toLowerCase().includes(q) && !e.sucursalNombre.toLowerCase().includes(q)) return false;
    return true;
  });
  const byPst = Object.fromEntries(pstList.map((p) => [p.id, filtered.filter((e) => e.prestadorId === p.id)]));

  const selectCls = "rounded-[8px] border border-border bg-card px-3 py-2 font-body text-sm text-foreground outline-none focus:border-brand-orange/70";
  const thCls = "py-3 px-4 font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground text-left";
  const tdCls = "py-3 px-4 font-body text-sm";

  return (
    <div className="flex flex-col gap-5 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-heading text-xl font-extrabold text-foreground">Tabla KM</h1>
          <p className="font-body text-sm text-muted-foreground">{filtered.length} entradas</p>
        </div>
        <div className="flex gap-2">
          <BrandButton size="sm" variant="outline" onClick={handleDownload}>Descargar CSV</BrandButton>
          <BrandButton size="sm" variant="outline" onClick={() => setCsvOpen(true)}>Cargar CSV</BrandButton>
          <BrandButton size="sm" onClick={() => { setEditing(null); setModalOpen(true); }}>+ Nueva entrada</BrandButton>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <select value={filtroPst} onChange={(e) => setFiltroPst(e.target.value)} className={selectCls} aria-label="Filtrar por PST">
          <option value="">Todos los prestadores</option>
          {prestadores.map((p) => <option key={p.id} value={p.id}>{p.nombreCorto}</option>)}
        </select>
        <input value={busqueda} onChange={(e) => setBusqueda(e.target.value)} placeholder="Buscar por cliente o sucursal..." className={`${selectCls} min-w-[220px]`} aria-label="Buscar" />
      </div>

      {loading ? (
        <div className="flex h-40 items-center justify-center"><Spinner /></div>
      ) : (
        <div className="flex flex-col gap-3">
          {pstList.map((pst) => {
            const rows = byPst[pst.id] ?? [];
            const open = expandidos[pst.id] ?? true;
            return (
              <div key={pst.id} className="overflow-hidden rounded-[12px]" style={{ background: "#1e1e1e", border: "1px solid rgba(255,255,255,.07)" }}>
                <button
                  type="button"
                  onClick={() => toggleExpand(pst.id)}
                  className="flex w-full items-center justify-between px-4 py-3 transition-colors hover:bg-white/[0.04]"
                >
                  <div className="flex items-center gap-2">
                    <span className="font-body text-[10px] font-bold uppercase tracking-[.08em] text-brand-orange">{pst.nombreCorto}</span>
                    <span className="font-body text-sm text-foreground">{pst.nombre}</span>
                    <span className="rounded-full px-2 py-0.5 font-body text-[10px]" style={{ background: "rgba(255,255,255,.08)", color: "rgba(255,255,255,.5)" }}>{rows.length}</span>
                  </div>
                  <span className="font-body text-xs text-muted-foreground">{open ? "▾" : "▸"}</span>
                </button>
                {open && rows.length === 0 && (
                  <div className="px-4 pb-4"><BrandEmptyState icon={Map} title="Sin entradas" description="No hay entradas para este prestador con los filtros actuales." /></div>
                )}
                {open && rows.length > 0 && (
                  <div className="overflow-x-auto border-t" style={{ borderColor: "rgba(255,255,255,.07)" }}>
                    <table className="w-full">
                      <thead>
                        <tr style={{ background: "rgba(0,0,0,.2)" }}>
                          <th className={thCls}>Empresa</th>
                          <th className={thCls}>Sucursal</th>
                          <th className={`${thCls} text-right`}>KMs rec.</th>
                          <th className={`${thCls} text-right`}>KMs fact.</th>
                          <th className={thCls}>Viático</th>
                          <th className={`${thCls} text-right`}></th>
                        </tr>
                      </thead>
                      <tbody>
                        {rows.map((t) => (
                          <tr key={t.id} className="border-t transition-colors hover:bg-white/[0.03]" style={{ borderColor: "rgba(255,255,255,.07)" }}>
                            <td className={tdCls} style={{ color: "#e0e0e0" }}>{t.empresaNombre}</td>
                            <td className={tdCls} style={{ color: "#e0e0e0" }}>{t.sucursalNombre}</td>
                            <td className={`${tdCls} text-right`} style={{ color: "rgba(255,255,255,.7)" }}>{t.kmsRecorrido}</td>
                            <td className={`${tdCls} text-right`} style={{ color: "rgba(255,255,255,.7)" }}>{t.kmsAFacturar}</td>
                            <td className={tdCls}>
                              {t.aplicaViatico
                                ? <span className="font-body text-xs" style={{ color: "#4ade80" }}>Sí</span>
                                : <span className="font-body text-xs" style={{ color: "rgba(255,255,255,.35)" }}>No</span>}
                            </td>
                            <td className={`${tdCls} text-right`}>
                              <button onClick={() => { setEditing(t); setModalOpen(true); }} className="mr-3 font-body text-sm text-brand-orange hover:underline">Editar</button>
                              <button onClick={() => setDeletingId(t.id)} className="font-body text-sm hover:underline" style={{ color: "#ef4444" }}>Eliminar</button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            );
          })}
          {pstList.length === 0 && <p className="py-10 text-center font-body text-sm text-muted-foreground">No hay prestadores cargados.</p>}
        </div>
      )}

      <EntradaModal key={editing?.id ?? "nueva"} isOpen={modalOpen} onClose={() => { setModalOpen(false); setEditing(null); }} prestadores={prestadores} spsts={spsts} editing={editing} onSuccess={load} />
      <CsvImportModal isOpen={csvOpen} onClose={() => setCsvOpen(false)} onSuccess={load} />
      <BrandModal isOpen={!!deletingId} onClose={() => setDeletingId(null)} title="Eliminar entrada">
        <p className="font-body text-sm text-muted-foreground mb-5">Esta acción no se puede deshacer. ¿Confirmás la eliminación?</p>
        <div className="flex justify-end gap-3">
          <BrandButton variant="outline" onClick={() => setDeletingId(null)}>Cancelar</BrandButton>
          <BrandButton onClick={handleDelete}>Sí, eliminar</BrandButton>
        </div>
      </BrandModal>
    </div>
  );
}
