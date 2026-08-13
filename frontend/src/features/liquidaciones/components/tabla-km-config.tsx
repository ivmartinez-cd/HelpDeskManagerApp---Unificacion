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
  // Prestador al que corresponden las `entradas` ya cargadas — si no coincide con
  // `filtroPst` es que hay un fetch en vuelo para la nueva selección (deriva el
  // spinner sin setState sincrónico en el effect, prohibido por
  // react-hooks/set-state-in-effect).
  const [entradasPstId, setEntradasPstId] = useState<string | null>(null);
  const [prestadores, setPrestadores] = useState<PrestadorLiquidacion[]>([]);
  const [spsts, setSpsts] = useState<Spst[]>([]);
  const [loadingPrestadores, setLoadingPrestadores] = useState(true);
  const [filtroPst, setFiltroPst] = useState("");
  const [busqueda, setBusqueda] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<TablaKm | null>(null);
  const [csvOpen, setCsvOpen] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    void Promise.all([liquidacionesApi.listPrestadores(false), liquidacionesApi.listSpsts()])
      .then(([p, s]) => { setPrestadores(p); setSpsts(s); })
      .finally(() => setLoadingPrestadores(false));
  }, []);

  // Trae solo las entradas del prestador seleccionado — traer el catálogo completo
  // (1633 filas) truncaba a las 500 que trae el backend por default, ver
  // LIQUIDACION_PRESTADORES_MIGRACION_ESTADO.md.
  const loadEntradas = useCallback(async () => {
    if (!filtroPst) return;
    try {
      const data = await liquidacionesApi.listTablaKm({ prestadorId: filtroPst });
      setEntradas(data);
    } finally {
      setEntradasPstId(filtroPst);
    }
  }, [filtroPst]);

  useEffect(() => { void loadEntradas(); }, [loadEntradas]);

  const handleDelete = async () => {
    if (!deletingId) return;
    try {
      await liquidacionesApi.deleteTablaKm(deletingId);
      toast.success("Entrada eliminada");
      setDeletingId(null);
      void loadEntradas();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Error al eliminar");
    }
  };

  const handleDownload = async () => {
    try { await liquidacionesApi.exportTablaKmCsv(); }
    catch { toast.error("Error al descargar"); }
  };

  const pstSeleccionado = prestadores.find((p) => p.id === filtroPst) ?? null;
  const loadingEntradas = filtroPst !== "" && filtroPst !== entradasPstId;
  const q = busqueda.toLowerCase();
  const filtered = q
    ? entradas.filter((e) => e.empresaNombre.toLowerCase().includes(q) || e.sucursalNombre.toLowerCase().includes(q))
    : entradas;

  const selectCls = "rounded-[8px] border border-border bg-card px-3 py-2 font-body text-sm text-foreground outline-none focus:border-brand-orange/70";
  const thCls = "py-3 px-4 font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground text-left";
  const tdCls = "py-3 px-4 font-body text-sm text-foreground";

  return (
    <div className="flex flex-col gap-5 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-heading text-xl font-extrabold text-foreground">Tabla KM</h1>
          <p className="font-body text-sm text-muted-foreground">
            {pstSeleccionado ? `${filtered.length} entradas de ${pstSeleccionado.nombreCorto}` : "Seleccioná un prestador para ver sus entradas"}
          </p>
        </div>
        <div className="flex gap-2">
          <BrandButton size="sm" variant="outline" onClick={handleDownload}>Descargar CSV</BrandButton>
          <BrandButton size="sm" variant="outline" onClick={() => setCsvOpen(true)}>Cargar CSV</BrandButton>
          <BrandButton size="sm" onClick={() => { setEditing(null); setModalOpen(true); }}>+ Nueva entrada</BrandButton>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <select value={filtroPst} onChange={(e) => setFiltroPst(e.target.value)} className={selectCls} aria-label="Filtrar por PST" disabled={loadingPrestadores}>
          <option value="">Seleccioná un prestador...</option>
          {prestadores.map((p) => <option key={p.id} value={p.id}>{p.nombreCorto}</option>)}
        </select>
        <input value={busqueda} onChange={(e) => setBusqueda(e.target.value)} placeholder="Buscar por cliente o sucursal..." className={`${selectCls} min-w-[220px]`} aria-label="Buscar" disabled={!filtroPst} />
      </div>

      {!filtroPst ? (
        <BrandEmptyState icon={Map} title="Ningún prestador seleccionado" description="Elegí un prestador arriba para ver su tabla KM." />
      ) : loadingEntradas ? (
        <div className="flex h-40 items-center justify-center"><Spinner /></div>
      ) : filtered.length === 0 ? (
        <BrandEmptyState icon={Map} title="Sin entradas" description="No hay entradas para este prestador con los filtros actuales." />
      ) : (
        <div className="overflow-hidden rounded-[12px] border border-border bg-card">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-muted/40">
                  <th className={thCls}>Empresa</th>
                  <th className={thCls}>Sucursal</th>
                  <th className={`${thCls} text-right`}>KMs rec.</th>
                  <th className={`${thCls} text-right`}>KMs fact.</th>
                  <th className={thCls}>Viático</th>
                  <th className={`${thCls} text-right`}></th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((t) => (
                  <tr key={t.id} className="border-t border-border transition-colors hover:bg-muted/30">
                    <td className={tdCls}>{t.empresaNombre}</td>
                    <td className={tdCls}>{t.sucursalNombre}</td>
                    <td className={`${tdCls} text-right`}>{t.kmsRecorrido}</td>
                    <td className={`${tdCls} text-right`}>{t.kmsAFacturar}</td>
                    <td className={tdCls}>
                      {t.aplicaViatico
                        ? <span className="font-body text-xs text-success">Sí</span>
                        : <span className="font-body text-xs text-muted-foreground">No</span>}
                    </td>
                    <td className={`${tdCls} text-right`}>
                      <button onClick={() => { setEditing(t); setModalOpen(true); }} className="mr-3 font-body text-sm text-brand-orange hover:underline">Editar</button>
                      <button onClick={() => setDeletingId(t.id)} className="font-body text-sm text-destructive hover:underline">Eliminar</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <EntradaModal key={editing?.id ?? "nueva"} isOpen={modalOpen} onClose={() => { setModalOpen(false); setEditing(null); }} prestadores={prestadores} spsts={spsts} editing={editing} defaultPrestadorId={filtroPst} onSuccess={loadEntradas} />
      <CsvImportModal isOpen={csvOpen} onClose={() => setCsvOpen(false)} onSuccess={loadEntradas} />
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
