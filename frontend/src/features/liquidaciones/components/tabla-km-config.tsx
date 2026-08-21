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
import type { PrestadorLiquidacion, SucursalSiges, TablaKm } from "../types/liquidaciones";
import { CsvImportModal, EntradaModal, type PlantillaEntrada } from "./tabla-km-modales";
import { KM_SORT_KEYS, kmSortValue, type KmSortKey, TablaKmTable } from "./tabla-km-table";
import { SigesTablaKmModal } from "./siges-tabla-km-modal";
import { TablaKmWizard } from "./tabla-km-wizard";
import { VincularSpstModal } from "./vincular-spst-modal";

export function TablaKmConfig() {
  // Mutaciones = liquidaciones.update; descarga CSV = liquidaciones.export (ADR-029).
  const { can } = useSession();
  const puedeEditar = can("liquidaciones", "update");
  const puedeExportar = can("liquidaciones", "export");
  const [entradas, setEntradas] = useState<TablaKm[]>([]);
  // Prestador al que corresponden las `entradas` ya cargadas — si no coincide con
  // `filtroPst` es que hay un fetch en vuelo para la nueva selección (deriva el
  // spinner sin setState sincrónico en el effect, prohibido por
  // react-hooks/set-state-in-effect).
  const [entradasPstId, setEntradasPstId] = useState<string | null>(null);
  const [prestadores, setPrestadores] = useState<PrestadorLiquidacion[]>([]);
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
                title="Vincular filas sin SPST por coincidencia de localidad — necesario para que el motor resuelva precios por zona"
              >
                Vincular SPST
              </BrandButton>
              <BrandButton
                size="sm"
                variant="outline"
                disabled={!pstSeleccionado || pstSeleccionado.sigesEmpresaId == null}
                onClick={() => setWizardOpen(true)}
                title="Traer sucursales de Gestión, revisar pendientes y calcular km"
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
          onEdit={(t) => { setEditing(t); setModalOpen(true); }}
          onDelete={setDeletingId}
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
