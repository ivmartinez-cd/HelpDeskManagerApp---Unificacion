"use client";

import { Briefcase } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { BrandButton, BrandEmptyState } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { Spinner } from "@/shared/components/ui/spinner";
import { useSession } from "@/services/session-provider";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type {
  PrestadorLiquidacion,
  Spst,
  Tarifario,
  ZonaSigesEstado,
} from "../types/liquidaciones";
import { agruparPorZona, tiposPresentes, type VigenciaZona, type ZonaTarifas } from "../lib/tarifarios-matriz";
import { SigesTarifariosModal } from "./siges-tarifarios-modal";
import { type PlantillaTarifa, TarifaModal } from "./tarifa-modal";
import { CsvImportModal } from "./tarifarios-csv-import-modal";
import { TarifariosMatriz } from "./tarifarios-matriz";
import { VigenciaZonaModal } from "./vigencia-zona-modal";

export function TarifariosConfig({
  deepLinkFaltante = null,
}: {
  /** Llega desde una alerta ALT008 ("Sin tarifario") en el detalle de
   * liquidación — precarga prestador + alta de la tarifa con tipo/SPST ya
   * completos. */
  deepLinkFaltante?: { prestadorId: string; tipoServicio: string; spstId: string } | null;
} = {}) {
  // Mutaciones = liquidaciones.update; descarga CSV = liquidaciones.export (ADR-029).
  const { can } = useSession();
  const puedeEditar = can("liquidaciones", "update");
  const puedeExportar = can("liquidaciones", "export");
  const [tarifarios, setTarifarios] = useState<Tarifario[]>([]);
  // Prestador al que corresponden los `tarifarios` ya cargados — si no coincide con
  // `filtroPst` es que hay un fetch en vuelo para la nueva selección (deriva el
  // spinner sin setState sincrónico en el effect, prohibido por
  // react-hooks/set-state-in-effect).
  const [tarifariosPstId, setTarifariosPstId] = useState<string | null>(null);
  const [prestadores, setPrestadores] = useState<PrestadorLiquidacion[]>([]);
  const [loadingPrestadores, setLoadingPrestadores] = useState(true);
  const [filtroPst, setFiltroPst] = useState(() => deepLinkFaltante?.prestadorId ?? "");
  // Lazy initializer (no effect) para no disparar setState sincrónico al
  // montar — mismo criterio que el deep-link de Tabla KM.
  const [modalOpen, setModalOpen] = useState(() => deepLinkFaltante !== null);
  const [editing, setEditing] = useState<Tarifario | null>(null);
  const [plantilla, setPlantilla] = useState<PlantillaTarifa | null>(() =>
    deepLinkFaltante
      ? {
          tipoServicio: deepLinkFaltante.tipoServicio,
          spstId: deepLinkFaltante.spstId,
          costoServicio: "",
          costoKm: "",
        }
      : null,
  );
  const [csvOpen, setCsvOpen] = useState(false);
  const [sigesOpen, setSigesOpen] = useState(false);
  // Borrado por vigencia completa de una zona (todas sus tarifas), como se
  // borra una fila en Siges.
  const [deletingVigencia, setDeletingVigencia] = useState<VigenciaZona | null>(null);
  const [vigenciaZona, setVigenciaZona] = useState<ZonaTarifas | null>(null);
  const [spsts, setSpsts] = useState<Spst[]>([]);
  const [zonasSiges, setZonasSiges] = useState<ZonaSigesEstado[]>([]);

  useEffect(() => {
    void liquidacionesApi.listPrestadores(false)
      .then(setPrestadores)
      .finally(() => setLoadingPrestadores(false));
  }, []);

  // SPST del prestador seleccionado — solo para resolver el nombre de la zona
  // cuando no tiene mapeo a Siges; la tarifa en sí guarda el spstId crudo.
  useEffect(() => {
    let cancelado = false;
    const cargar = filtroPst
      ? liquidacionesApi.listSpsts({ prestadorId: filtroPst })
      : Promise.resolve([]);
    void cargar.then((data) => { if (!cancelado) setSpsts(data); });
    return () => { cancelado = true; };
  }, [filtroPst]);
  const spstsPorId = useMemo(() => new Map(spsts.map((s) => [s.id, s])), [spsts]);

  // Zonas de Siges mapeadas a cada SPST (o a la genérica, spstId null): el
  // tarifario se muestra con el nombre de zona tal cual está en Siges, que es
  // lo que la TL compara (pedido de Iván, 2026-09-07). Sin vínculo a Siges no
  // hay zonas y cada grupo cae al nombre del SPST.
  useEffect(() => {
    let cancelado = false;
    const cargar = filtroPst
      ? liquidacionesApi.getSigesZonas(filtroPst).then((r) => r.zonas)
      : Promise.resolve([]);
    void cargar
      .catch(() => [] as ZonaSigesEstado[])
      .then((data) => { if (!cancelado) setZonasSiges(data); });
    return () => { cancelado = true; };
  }, [filtroPst]);
  const zonaSigesPorSpst = useMemo(
    () => new Map(zonasSiges.filter((z) => z.mapeada).map((z) => [z.spstId ?? "", z.descripcionSiges])),
    [zonasSiges],
  );

  // Trae solo las tarifas del prestador seleccionado — traer el catálogo completo
  // (4832 filas) truncaba a las 500 que trae el backend por default, ver
  // LIQUIDACION_PRESTADORES_MIGRACION_ESTADO.md.
  const loadTarifarios = useCallback(async () => {
    if (!filtroPst) return;
    try {
      const data = await liquidacionesApi.listTarifarios(filtroPst);
      setTarifarios(data);
    } finally {
      setTarifariosPstId(filtroPst);
    }
  }, [filtroPst]);

  useEffect(() => { void loadTarifarios(); }, [loadTarifarios]);

  const handleDelete = async () => {
    if (!deletingVigencia) return;
    try {
      for (const t of deletingVigencia.tarifas) await liquidacionesApi.deleteTarifario(t.id);
      toast.success(`Vigencia eliminada (${deletingVigencia.tarifas.length} tarifas)`);
      setDeletingVigencia(null);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Error al eliminar");
    } finally {
      void loadTarifarios();
    }
  };

  const handleDownload = async () => {
    try { await liquidacionesApi.exportTarifariosCsv(filtroPst || undefined); }
    catch { toast.error("Error al descargar"); }
  };

  const abrirModal = (tarifa: Tarifario | null, prefill: PlantillaTarifa | null = null) => {
    setEditing(tarifa);
    setPlantilla(prefill);
    setModalOpen(true);
  };

  const labelZona = (spstId: string | null) =>
    zonaSigesPorSpst.get(spstId ?? "") ??
    (spstId ? spstsPorId.get(spstId)?.nombre ?? "SPST eliminado" : "Tarifa genérica");

  const pstSeleccionado = prestadores.find((p) => p.id === filtroPst) ?? null;
  const loadingTarifarios = filtroPst !== "" && filtroPst !== tarifariosPstId;
  const tipos = tiposPresentes(tarifarios);
  // Mismo orden que Siges: por descripción de zona.
  const zonas = agruparPorZona(tarifarios).sort((a, b) =>
    labelZona(a.spstId).localeCompare(labelZona(b.spstId)),
  );

  const acciones = {
    onNuevaVigencia: setVigenciaZona,
    onEditarTarifa: (t: Tarifario) => abrirModal(t),
    onNuevaTarifa: (zona: ZonaTarifas, tipo: string, vigencia: VigenciaZona | null) =>
      abrirModal(null, {
        tipoServicio: tipo,
        spstId: zona.spstId ?? "",
        costoServicio: "",
        costoKm: String(vigencia?.costoKm ?? ""),
      }),
    onEliminarVigencia: (_zona: ZonaTarifas, vigencia: VigenciaZona) => setDeletingVigencia(vigencia),
  };

  const selectCls = "rounded-[8px] border border-border bg-card px-3 py-2 font-body text-sm text-foreground outline-none focus:border-brand-orange/70";

  return (
    <div className="flex flex-col gap-5 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-heading text-xl font-extrabold text-foreground">Estructura de Tarifarios</h1>
          <p className="font-body text-sm text-muted-foreground">
            {pstSeleccionado ? `${pstSeleccionado.nombreCorto}: ${zonas.length} zonas, ${tipos.length} tipos de servicio, ${tarifarios.length} tarifas` : "Seleccioná un prestador para ver sus tarifas"}
          </p>
        </div>
        <div className="flex gap-2">
          {puedeEditar && (
            <BrandButton
              size="sm"
              variant="outline"
              disabled={!filtroPst}
              title={!filtroPst ? "Seleccioná un prestador primero" : undefined}
              onClick={() => setSigesOpen(true)}
            >
              Sincronizar
            </BrandButton>
          )}
          {puedeExportar && <BrandButton size="sm" variant="outline" onClick={handleDownload}>Descargar CSV</BrandButton>}
          {puedeEditar && (
            <>
              <BrandButton size="sm" variant="outline" onClick={() => setCsvOpen(true)}>Cargar CSV</BrandButton>
              <BrandButton size="sm" onClick={() => abrirModal(null)}>+ Nueva tarifa</BrandButton>
            </>
          )}
        </div>
      </div>

      <div className="flex items-center gap-3">
        <select value={filtroPst} onChange={(e) => setFiltroPst(e.target.value)} className={selectCls} aria-label="Filtrar por prestador" disabled={loadingPrestadores}>
          <option value="">Seleccioná un prestador...</option>
          {prestadores.map((p) => <option key={p.id} value={p.id}>{p.nombreCorto}</option>)}
        </select>
      </div>

      {!filtroPst ? (
        <BrandEmptyState icon={Briefcase} title="Ningún prestador seleccionado" description="Elegí un prestador arriba para ver su estructura de tarifarios." />
      ) : loadingTarifarios ? (
        <div className="flex h-40 items-center justify-center"><Spinner /></div>
      ) : tarifarios.length === 0 ? (
        <BrandEmptyState icon={Briefcase} title={`${pstSeleccionado?.nombreCorto} no tiene tarifas cargadas`} description="Usá el botón '+ Nueva tarifa' para configurar." />
      ) : (
        <TarifariosMatriz zonas={zonas} tipos={tipos} labelZona={labelZona} canEdit={puedeEditar} acciones={acciones} />
      )}

      <TarifaModal key={editing?.id ?? (plantilla ? `plantilla:${Object.values(plantilla).join("::")}` : `nueva:${filtroPst}`)} isOpen={modalOpen} onClose={() => { setModalOpen(false); setEditing(null); setPlantilla(null); }} prestadores={prestadores} editing={editing} plantilla={plantilla} defaultPrestadorId={filtroPst} onSuccess={loadTarifarios} />
      <CsvImportModal isOpen={csvOpen} onClose={() => setCsvOpen(false)} onSuccess={loadTarifarios} />
      {sigesOpen && filtroPst && (
        <SigesTarifariosModal
          prestadorId={filtroPst}
          prestadorNombre={pstSeleccionado?.nombreCorto ?? ""}
          onClose={() => setSigesOpen(false)}
          onChanged={loadTarifarios}
        />
      )}
      {vigenciaZona && filtroPst && (
        <VigenciaZonaModal
          prestadorId={filtroPst}
          spstId={vigenciaZona.spstId}
          zonaLabel={labelZona(vigenciaZona.spstId)}
          tipos={tipos}
          base={vigenciaZona.vigente}
          onClose={() => setVigenciaZona(null)}
          onSuccess={loadTarifarios}
        />
      )}
      <BrandModal isOpen={!!deletingVigencia} onClose={() => setDeletingVigencia(null)} title="Eliminar vigencia">
        <p className="font-body text-sm text-muted-foreground mb-5">
          Se eliminan las {deletingVigencia?.tarifas.length ?? 0} tarifas de la vigencia {deletingVigencia?.desde ?? ""} de esta zona. Esta acción no se puede deshacer. ¿Confirmás?
        </p>
        <div className="flex justify-end gap-3">
          <BrandButton variant="outline" onClick={() => setDeletingVigencia(null)}>Cancelar</BrandButton>
          <BrandButton onClick={handleDelete}>Sí, eliminar</BrandButton>
        </div>
      </BrandModal>
    </div>
  );
}
