"use client";

import { Map } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { BrandButton, BrandEmptyState } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { Spinner } from "@/shared/components/ui/spinner";
import { compareSortValues, useTableSort } from "@/shared/hooks/use-table-sort";
import { useSession } from "@/services/session-provider";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { PrestadorLiquidacion, Spst, SucursalSiges, Tarifario, TablaKm } from "../types/liquidaciones";
import { CsvImportModal, EntradaModal, type PlantillaEntrada } from "./tabla-km-modales";
import { KM_SORT_KEYS, kmSortValue, type KmSortKey, TablaKmTable } from "./tabla-km-table";
import { SigesTablaKmModal } from "./siges-tabla-km-modal";
import { TablaKmWizard } from "./tabla-km-wizard";
import { VincularSpstModal } from "./vincular-spst-modal";

export function TablaKmConfig({
  deepLinkFaltante = null,
  deepLinkBuscar = null,
}: {
  /** Llega desde un incidente "Sin tabla" en el detalle de liquidación —
   * precarga prestador + alta de la entrada con empresa/sucursal ya completos. */
  deepLinkFaltante?: { prestadorId: string; empresa: string; sucursal: string } | null;
  /** Llega desde una alerta sin SPST resuelto (ALT008/ALT009) — la fila ya
   * existe, solo hace falta encontrarla y vincularle el SPST a mano. */
  deepLinkBuscar?: { prestadorId: string; query: string } | null;
} = {}) {
  // Mutaciones = liquidaciones.update; descarga CSV = liquidaciones.export (ADR-029).
  const { can } = useSession();
  const puedeEditar = can("liquidaciones", "update");
  const puedeExportar = can("liquidaciones", "export");
  const [entradas, setEntradas] = useState<TablaKm[]>([]);
  // Las filas sin actividad en liquidaciones recientes vienen archivadas
  // (migración c3e8f1a9d2b4 + botón por fila): ocultas por default.
  const [mostrarArchivadas, setMostrarArchivadas] = useState(false);
  // Prestador al que corresponden las `entradas` ya cargadas — si no coincide con
  // `filtroPst` es que hay un fetch en vuelo para la nueva selección (deriva el
  // spinner sin setState sincrónico en el effect, prohibido por
  // react-hooks/set-state-in-effect).
  const [entradasPstId, setEntradasPstId] = useState<string | null>(null);
  const [prestadores, setPrestadores] = useState<PrestadorLiquidacion[]>([]);
  const [loadingPrestadores, setLoadingPrestadores] = useState(true);
  const [filtroPst, setFiltroPst] = useState(
    () => deepLinkFaltante?.prestadorId ?? deepLinkBuscar?.prestadorId ?? "",
  );
  const [busqueda, setBusqueda] = useState(() => deepLinkBuscar?.query ?? "");
  // El deep-link desde un incidente "Sin tabla" precarga prestador + alta de la
  // entrada faltante — lazy initializer (no effect) para no disparar setState
  // sincrónico al montar (prohibido por react-hooks/set-state-in-effect).
  const [modalOpen, setModalOpen] = useState(() => deepLinkFaltante !== null);
  const [editing, setEditing] = useState<TablaKm | null>(null);
  const [plantilla, setPlantilla] = useState<PlantillaEntrada | null>(() =>
    deepLinkFaltante
      ? {
          empresaNombre: deepLinkFaltante.empresa,
          sucursalNombre: deepLinkFaltante.sucursal,
          domicilioCliente: "",
          localidadCliente: "",
          provinciaCliente: "",
        }
      : null,
  );
  const [csvOpen, setCsvOpen] = useState(false);
  const [sigesOpen, setSigesOpen] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [wizardOpen, setWizardOpen] = useState(false);
  const [vincularSpstOpen, setVincularSpstOpen] = useState(false);

  const { sort, toggleSort } = useTableSort<KmSortKey>({
    initial: { key: "empresa", direction: "asc" },
    keys: KM_SORT_KEYS,
  });

  useEffect(() => {
    void liquidacionesApi.listPrestadores(false)
      .then(setPrestadores)
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

  // SPST y SPST-con-tarifario del prestador — insumo de la columna "SPST →
  // Tarifa" (hace visible en la propia tabla la cadena que resuelve el
  // precio, en vez de obligar a saltar a SPSTs/Tarifarios para adivinarla).
  const [spsts, setSpsts] = useState<Spst[]>([]);
  const [spstsConTarifa, setSpstsConTarifa] = useState<Set<string | null>>(new Set());
  useEffect(() => {
    let cancelado = false;
    const cargar = filtroPst
      ? Promise.all([
          liquidacionesApi.listSpsts({ prestadorId: filtroPst }),
          liquidacionesApi.listTarifarios(filtroPst),
        ])
      : Promise.resolve([[], []] as [Spst[], Tarifario[]]);
    void cargar.then(([spstsData, tarifariosData]) => {
      if (cancelado) return;
      setSpsts(spstsData);
      setSpstsConTarifa(new Set(tarifariosData.map((t) => t.spstId)));
    });
    return () => { cancelado = true; };
  }, [filtroPst]);
  // `Map` a secas choca con el ícono `Map` de lucide-react importado arriba.
  const spstsPorId = useMemo(() => new globalThis.Map(spsts.map((s) => [s.id, s])), [spsts]);

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
    try { await liquidacionesApi.exportTablaKmCsv(filtroPst || undefined); }
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
  const archivadas = entradas.filter((e) => e.archivada).length;
  const filtered = useMemo(() => {
    const visibles = mostrarArchivadas ? entradas : entradas.filter((e) => !e.archivada);
    const base = q
      ? visibles.filter((e) => e.empresaNombre.toLowerCase().includes(q) || e.sucursalNombre.toLowerCase().includes(q))
      : visibles;
    return [...base].sort((a, b) =>
      compareSortValues(kmSortValue(a, sort.key), kmSortValue(b, sort.key), sort.direction),
    );
  }, [entradas, q, sort, mostrarArchivadas]);

  const handleArchivar = async (t: TablaKm) => {
    try {
      await liquidacionesApi.setTablaKmArchivada(t.id, !t.archivada);
      toast.success(t.archivada ? "Fila restaurada" : "Fila archivada");
      void loadEntradas();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "No se pudo cambiar");
    }
  };

  const selectCls = "rounded-[8px] border border-border bg-card px-3 py-2 font-body text-sm text-foreground outline-none focus:border-brand-orange/70";

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
          {puedeEditar && (
            <>
              <BrandButton
                size="sm"
                variant="outline"
                disabled={!pstSeleccionado || pstSeleccionado.sigesEmpresaId == null}
                onClick={() => setSigesOpen(true)}
                title="Buscar sucursales del PST y precargar los datos en una entrada nueva"
              >
                Agregar sucursal
              </BrandButton>
              <BrandButton size="sm" variant="outline" onClick={() => setCsvOpen(true)}>Cargar CSV</BrandButton>
            </>
          )}
          {puedeExportar && (
            <BrandButton size="sm" variant="outline" onClick={handleDownload}>Descargar CSV</BrandButton>
          )}
          {puedeEditar && (
            <>
              <BrandButton
                size="sm"
                variant="outline"
                disabled={!filtroPst}
                onClick={() => setVincularSpstOpen(true)}
                title="Vincular filas sin SPST por coincidencia de localidad — necesario para que el motor resuelva precios. No toca el vínculo con Gestión (eso lo maneja el Asistente de KM)"
              >
                Vincular SPST
              </BrandButton>
              <BrandButton
                size="sm"
                variant="outline"
                disabled={!pstSeleccionado || pstSeleccionado.sigesEmpresaId == null}
                onClick={() => setWizardOpen(true)}
                title="Trae/actualiza sucursales desde Gestión (identidad, domicilio) y calcula km — no vincula el SPST de la tarifa, para eso usá 'Vincular SPST'"
              >
                Asistente de KM →
              </BrandButton>
              <BrandButton size="sm" onClick={() => { setEditing(null); setPlantilla(null); setModalOpen(true); }}>+ Nueva entrada</BrandButton>
            </>
          )}
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <select value={filtroPst} onChange={(e) => setFiltroPst(e.target.value)} className={selectCls} aria-label="Filtrar por PST" disabled={loadingPrestadores}>
          <option value="">Seleccioná un prestador...</option>
          {prestadores.map((p) => <option key={p.id} value={p.id}>{p.nombreCorto}</option>)}
        </select>
        <input value={busqueda} onChange={(e) => setBusqueda(e.target.value)} placeholder="Buscar por cliente o sucursal..." className={`${selectCls} min-w-[220px]`} aria-label="Buscar" disabled={!filtroPst} />
        {archivadas > 0 && (
          <label className="flex items-center gap-2 font-body text-sm text-muted-foreground">
            <input type="checkbox" checked={mostrarArchivadas} onChange={(e) => setMostrarArchivadas(e.target.checked)} />
            Mostrar {archivadas} archivada(s) sin actividad en 2026
          </label>
        )}
      </div>

      {!filtroPst ? (
        <BrandEmptyState icon={Map} title="Ningún prestador seleccionado" description="Elegí un prestador arriba para ver su tabla KM." />
      ) : loadingEntradas ? (
        <div className="flex h-40 items-center justify-center"><Spinner /></div>
      ) : filtered.length === 0 ? (
        <BrandEmptyState icon={Map} title="Sin entradas" description="No hay entradas para este prestador con los filtros actuales." />
      ) : (
        <TablaKmTable
          filtered={filtered}
          sort={sort}
          toggleSort={toggleSort}
          puedeEditar={puedeEditar}
          spstsPorId={spstsPorId}
          spstsConTarifa={spstsConTarifa}
          onEdit={(t) => { setEditing(t); setModalOpen(true); }}
          onDelete={setDeletingId}
          onArchivar={puedeEditar ? (t) => void handleArchivar(t) : undefined}
        />
      )}

      <EntradaModal key={editing?.id ?? (plantilla ? `plantilla:${plantilla.empresaNombre}::${plantilla.sucursalNombre}` : "nueva")} isOpen={modalOpen} onClose={() => { setModalOpen(false); setEditing(null); setPlantilla(null); }} prestadores={prestadores} editing={editing} defaultPrestadorId={filtroPst} onSuccess={loadEntradas} plantilla={plantilla} />
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
      {vincularSpstOpen && filtroPst && (
        <VincularSpstModal
          prestadorId={filtroPst}
          onClose={() => setVincularSpstOpen(false)}
          onVinculado={loadEntradas}
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
