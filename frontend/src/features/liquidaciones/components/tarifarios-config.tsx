"use client";

import { Briefcase } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { BrandButton, BrandEmptyState } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { Spinner } from "@/shared/components/ui/spinner";
import { useSession } from "@/services/session-provider";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { PrestadorLiquidacion, Tarifario } from "../types/liquidaciones";
import { agruparTarifarios, GrupoTarifaRow, type GrupoTarifa } from "./tarifario-history-timeline";
import { SigesTarifariosModal } from "./siges-tarifarios-modal";
import { type PlantillaTarifa, TarifaModal } from "./tarifa-modal";
import { CsvImportModal } from "./tarifarios-csv-import-modal";

export function TarifariosConfig() {
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
  const [filtroPst, setFiltroPst] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Tarifario | null>(null);
  const [plantilla, setPlantilla] = useState<PlantillaTarifa | null>(null);
  const [csvOpen, setCsvOpen] = useState(false);
  const [sigesOpen, setSigesOpen] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    void liquidacionesApi.listPrestadores(false)
      .then(setPrestadores)
      .finally(() => setLoadingPrestadores(false));
  }, []);

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
    if (!deletingId) return;
    try {
      await liquidacionesApi.deleteTarifario(deletingId);
      toast.success("Tarifa eliminada");
      setDeletingId(null);
      void loadTarifarios();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Error al eliminar");
    }
  };

  const handleDownload = async () => {
    try { await liquidacionesApi.exportTarifariosCsv(); }
    catch { toast.error("Error al descargar"); }
  };

  const abrirModal = (tarifa: Tarifario | null, prefill: PlantillaTarifa | null = null) => {
    setEditing(tarifa);
    setPlantilla(prefill);
    setModalOpen(true);
  };

  const handleActualizar = (grupo: GrupoTarifa) =>
    abrirModal(null, {
      tipoServicio: grupo.tipoServicio,
      zona: grupo.zona ?? "",
      costoServicio: String(grupo.vigente?.costoServicio ?? ""),
      costoKm: String(grupo.vigente?.costoKm ?? ""),
    });

  const pstSeleccionado = prestadores.find((p) => p.id === filtroPst) ?? null;
  const loadingTarifarios = filtroPst !== "" && filtroPst !== tarifariosPstId;
  const grupos = agruparTarifarios(tarifarios);

  const selectCls = "rounded-[8px] border border-border bg-card px-3 py-2 font-body text-sm text-foreground outline-none focus:border-brand-orange/70";

  return (
    <div className="flex flex-col gap-5 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-heading text-xl font-extrabold text-foreground">Estructura de Tarifarios</h1>
          <p className="font-body text-sm text-muted-foreground">
            {pstSeleccionado ? `${tarifarios.length} tarifas en ${grupos.length} servicios de ${pstSeleccionado.nombreCorto}` : "Seleccioná un prestador para ver sus tarifas"}
          </p>
        </div>
        <div className="flex gap-2">
          {puedeEditar && <BrandButton size="sm" variant="outline" onClick={() => setSigesOpen(true)}>Sincronizar</BrandButton>}
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
        <div className="overflow-hidden rounded-[12px] border border-border bg-card">
          <div className="divide-y divide-border">
            {grupos.map((grupo) => (
              <GrupoTarifaRow
                key={`${grupo.tipoServicio}::${grupo.zona ?? ""}`}
                grupo={grupo}
                canEdit={puedeEditar}
                onActualizar={handleActualizar}
                onEdit={(t) => abrirModal(t)}
                onDelete={setDeletingId}
              />
            ))}
          </div>
        </div>
      )}

      <TarifaModal key={editing?.id ?? (plantilla ? `plantilla:${Object.values(plantilla).join("::")}` : "nueva")} isOpen={modalOpen} onClose={() => { setModalOpen(false); setEditing(null); setPlantilla(null); }} prestadores={prestadores} editing={editing} plantilla={plantilla} defaultPrestadorId={filtroPst} onSuccess={loadTarifarios} />
      <CsvImportModal isOpen={csvOpen} onClose={() => setCsvOpen(false)} onSuccess={loadTarifarios} />
      {sigesOpen && (
        <SigesTarifariosModal onClose={() => setSigesOpen(false)} onChanged={loadTarifarios} />
      )}
      <BrandModal isOpen={!!deletingId} onClose={() => setDeletingId(null)} title="Eliminar tarifa">
        <p className="font-body text-sm text-muted-foreground mb-5">Esta acción no se puede deshacer. ¿Confirmás la eliminación?</p>
        <div className="flex justify-end gap-3">
          <BrandButton variant="outline" onClick={() => setDeletingId(null)}>Cancelar</BrandButton>
          <BrandButton onClick={handleDelete}>Sí, eliminar</BrandButton>
        </div>
      </BrandModal>
    </div>
  );
}
