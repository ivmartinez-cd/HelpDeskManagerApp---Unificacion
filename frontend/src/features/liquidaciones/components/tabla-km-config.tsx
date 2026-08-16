"use client";

import { Map } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { BrandButton, BrandEmptyState } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { SortableHeader } from "@/shared/components/ui/sortable-header";
import { Spinner } from "@/shared/components/ui/spinner";
import { compareSortValues, useTableSort } from "@/shared/hooks/use-table-sort";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { PrestadorLiquidacion, Spst, SucursalSiges, TablaKm } from "../types/liquidaciones";

type KmSortKey = "empresa" | "sucursal" | "kmsRec" | "kmsFact";
const KM_SORT_KEYS: readonly KmSortKey[] = ["empresa", "sucursal", "kmsRec", "kmsFact"];

function kmSortValue(t: TablaKm, key: KmSortKey) {
  switch (key) {
    case "empresa": return t.empresaNombre;
    case "sucursal": return t.sucursalNombre;
    case "kmsRec": return t.kmsRecorrido;
    case "kmsFact": return t.kmsAFacturar;
  }
}
import { CsvImportModal, EntradaModal, type PlantillaEntrada } from "./tabla-km-modales";
import { SigesTablaKmModal } from "./siges-tabla-km-modal";
import { TablaKmWizard } from "./tabla-km-wizard";

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
  const [plantilla, setPlantilla] = useState<PlantillaEntrada | null>(null);
  const [csvOpen, setCsvOpen] = useState(false);
  const [sigesOpen, setSigesOpen] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [wizardOpen, setWizardOpen] = useState(false);

  const { sort, toggleSort } = useTableSort<KmSortKey>({
    initial: { key: "empresa", direction: "asc" },
    keys: KM_SORT_KEYS,
  });

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

  const handleUsarSucursal = (s: SucursalSiges) => {
    setSigesOpen(false);
    setEditing(null);
    setPlantilla({
      empresaNombre: s.empresaNombre,
      sucursalNombre: s.sucursalNombre,
      domicilioCliente: s.domicilio ?? "",
      localidadCliente: s.localidad ?? "",
      provinciaCliente: s.provincia ?? "",
    });
    setModalOpen(true);
  };

  const pstSeleccionado = prestadores.find((p) => p.id === filtroPst) ?? null;
  const loadingEntradas = filtroPst !== "" && filtroPst !== entradasPstId;
  const q = busqueda.toLowerCase();
  const filtered = useMemo(() => {
    const base = q
      ? entradas.filter((e) => e.empresaNombre.toLowerCase().includes(q) || e.sucursalNombre.toLowerCase().includes(q))
      : entradas;
    return [...base].sort((a, b) =>
      compareSortValues(kmSortValue(a, sort.key), kmSortValue(b, sort.key), sort.direction),
    );
  }, [entradas, q, sort]);

  const selectCls = "rounded-[8px] border border-border bg-card px-3 py-2 font-body text-sm text-foreground outline-none focus:border-brand-orange/70";
  const thCls = "py-3 px-4 font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground text-left";
  const tdCls = "py-2 px-4 font-body text-sm text-foreground";

  // Para agrupar visualmente por empresa cuando el sort es por empresa
  const groupByEmpresa = sort.key === "empresa";
  function isFirstOfGroup(idx: number) {
    if (!groupByEmpresa) return true;
    return idx === 0 || filtered[idx - 1].empresaNombre !== filtered[idx].empresaNombre;
  }

  return (
    <div className="flex flex-col gap-5 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-heading text-xl font-extrabold text-foreground">Tabla KM</h1>
          <p className="font-body text-sm text-muted-foreground">
            {pstSeleccionado ? `${filtered.length} entradas de ${pstSeleccionado.nombreCorto}` : "Seleccioná un prestador para ver sus entradas"}
          </p>
        </div>
        <div className="flex flex-wrap justify-end gap-2">
          {/* Paso 1: agregar filas */}
          <BrandButton
            size="sm"
            variant="outline"
            disabled={!pstSeleccionado || pstSeleccionado.sigesEmpresaId == null}
            onClick={() => setSigesOpen(true)}
            title="Buscar sucursales del PST en Siges y precargar los datos en una entrada nueva"
          >
            Agregar desde Siges
          </BrandButton>
          <BrandButton size="sm" variant="outline" onClick={() => setCsvOpen(true)}>Cargar CSV</BrandButton>
          <BrandButton size="sm" variant="outline" onClick={handleDownload}>Descargar CSV</BrandButton>
          <BrandButton
            size="sm"
            variant="outline"
            disabled={!pstSeleccionado || pstSeleccionado.sigesEmpresaId == null}
            onClick={() => setWizardOpen(true)}
            title="Guía paso a paso: geocodificar → calcular km → auditar pines"
          >
            Configurar km →
          </BrandButton>
          <BrandButton size="sm" onClick={() => { setEditing(null); setPlantilla(null); setModalOpen(true); }}>+ Nueva entrada</BrandButton>
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
            <table className="w-full table-fixed">
              <colgroup>
                <col className="w-[22%]" />
                <col className="w-[38%]" />
                <col className="w-[10%]" />
                <col className="w-[10%]" />
                <col className="w-[8%]" />
                <col className="w-[12%]" />
              </colgroup>
              <thead>
                <tr className="bg-muted/40">
                  <SortableHeader column={{ key: "empresa", label: "Empresa" }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
                  <SortableHeader column={{ key: "sucursal", label: "Sucursal" }} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
                  <SortableHeader column={{ key: "kmsRec", label: "KMs rec." }} sort={sort} onToggleSort={toggleSort} thClassName={`${thCls} text-right`} />
                  <SortableHeader column={{ key: "kmsFact", label: "KMs fact." }} sort={sort} onToggleSort={toggleSort} thClassName={`${thCls} text-right`} />
                  <th className={`${thCls} text-center`}>Viático</th>
                  <th className={`${thCls} text-right`}></th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((t, i) => {
                  const firstOfGroup = isFirstOfGroup(i);
                  const lastOfGroup = !groupByEmpresa || i === filtered.length - 1 || filtered[i + 1].empresaNombre !== t.empresaNombre;
                  return (
                    <tr
                      key={t.id}
                      className={`transition-colors hover:bg-muted/30 ${firstOfGroup ? "border-t border-border" : "border-t border-transparent"}`}
                    >
                      <td className={`${tdCls} ${!firstOfGroup ? "text-transparent select-none" : ""}`}>
                        <span className={`block truncate ${firstOfGroup && lastOfGroup === false ? "font-semibold" : ""}`} title={t.empresaNombre}>
                          {firstOfGroup ? t.empresaNombre : "·"}
                        </span>
                      </td>
                      <td className={tdCls}>
                        <div className="flex items-center gap-2">
                          <span className="truncate" title={t.sucursalNombre}>{t.sucursalNombre}</span>
                          {t.urlMaps && (
                            <a href={t.urlMaps} target="_blank" rel="noopener noreferrer" className="shrink-0 text-muted-foreground hover:text-brand-orange" title="Ver en Maps">
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
                            </a>
                          )}
                        </div>
                      </td>
                      <td className={`${tdCls} text-right tabular-nums text-muted-foreground`}>
                        {t.kmsRecorrido > 0 ? Math.round(t.kmsRecorrido) : "—"}
                      </td>
                      <td className={`${tdCls} text-right tabular-nums`}>
                        {t.kmsAFacturar > 0 ? Math.ceil(t.kmsAFacturar) : "—"}
                      </td>
                      <td className={`${tdCls} text-center`}>
                        {t.aplicaViatico
                          ? <span className="inline-block rounded-full bg-success/10 px-2 py-0.5 font-body text-[10px] font-bold uppercase tracking-wide text-success">Sí</span>
                          : <span className="inline-block rounded-full bg-muted px-2 py-0.5 font-body text-[10px] font-bold uppercase tracking-wide text-muted-foreground">No</span>}
                      </td>
                      <td className={`${tdCls} text-right`}>
                        <button onClick={() => { setEditing(t); setModalOpen(true); }} className="mr-3 font-body text-sm text-brand-orange hover:underline">Editar</button>
                        <button onClick={() => setDeletingId(t.id)} className="font-body text-sm text-destructive hover:underline">Eliminar</button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <EntradaModal key={editing?.id ?? (plantilla ? `plantilla:${plantilla.empresaNombre}::${plantilla.sucursalNombre}` : "nueva")} isOpen={modalOpen} onClose={() => { setModalOpen(false); setEditing(null); setPlantilla(null); }} prestadores={prestadores} spsts={spsts} editing={editing} defaultPrestadorId={filtroPst} onSuccess={loadEntradas} plantilla={plantilla} />
      <CsvImportModal isOpen={csvOpen} onClose={() => setCsvOpen(false)} onSuccess={loadEntradas} />
      {sigesOpen && filtroPst && (
        <SigesTablaKmModal prestadorId={filtroPst} onClose={() => setSigesOpen(false)} onUsar={handleUsarSucursal} />
      )}
      {wizardOpen && pstSeleccionado && (
        <TablaKmWizard
          prestador={pstSeleccionado}
          onClose={() => setWizardOpen(false)}
          onAplicado={loadEntradas}
        />
      )}
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
