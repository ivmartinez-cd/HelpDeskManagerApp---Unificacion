"use client";

import { Briefcase } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import {
  BrandButton,
  BrandEmptyState,
  BrandFileInput,
  BrandInput,
  BrandSelect,
} from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { Spinner } from "@/shared/components/ui/spinner";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { PrestadorLiquidacion, Tarifario } from "../types/liquidaciones";

const TIPOS = [
  "correctivo", "preventivo", "instalacion_desinstalacion",
  "pre_correctivo", "guardia", "sistemas",
];

function formatARS(n: number) {
  return n.toLocaleString("es-AR", { style: "currency", currency: "ARS", maximumFractionDigits: 2 });
}

function tarifaAForm(t: Tarifario | null, defaultPrestadorId: string) {
  if (!t) return { prestadorId: defaultPrestadorId, tipoServicio: "", zona: "", costoServicio: "", costoKm: "", vigenciaDesde: "", vigenciaHasta: "" };
  return {
    prestadorId: t.prestadorId,
    tipoServicio: t.tipoServicio,
    zona: t.zona ?? "",
    costoServicio: String(t.costoServicio),
    costoKm: String(t.costoKm),
    vigenciaDesde: t.vigenciaDesde,
    vigenciaHasta: t.vigenciaHasta ?? "",
  };
}

// El caller lo monta con key={editing?.id ?? "nueva"} para que el estado inicial
// del form se recalcule al cambiar de tarifa.
function TarifaModal({
  isOpen, onClose, prestadores, editing, defaultPrestadorId, onSuccess,
}: {
  isOpen: boolean; onClose: () => void; prestadores: PrestadorLiquidacion[]; editing: Tarifario | null; defaultPrestadorId: string; onSuccess: () => void;
}) {
  const [form, setForm] = useState(() => tarifaAForm(editing, defaultPrestadorId));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleClose = () => { setForm(tarifaAForm(editing, defaultPrestadorId)); setError(null); onClose(); };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const body = {
        prestadorId: form.prestadorId,
        tipoServicio: form.tipoServicio,
        zona: form.zona || undefined,
        costoServicio: parseFloat(form.costoServicio),
        costoKm: parseFloat(form.costoKm),
        vigenciaDesde: form.vigenciaDesde,
        vigenciaHasta: form.vigenciaHasta || undefined,
      };
      if (editing) {
        await liquidacionesApi.updateTarifario(editing.id, body);
        toast.success("Tarifa actualizada");
      } else {
        await liquidacionesApi.createTarifario(body);
        toast.success("Tarifa creada");
      }
      handleClose();
      onSuccess();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al guardar");
    } finally {
      setLoading(false);
    }
  };

  return (
    <BrandModal isOpen={isOpen} onClose={handleClose} title={editing ? "Editar tarifa" : "Nueva tarifa"} error={error} widthPx={520}>
      <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-4">
        <div className="col-span-2">
          <BrandSelect label="Prestador *" required value={form.prestadorId} onChange={(e) => setForm((f) => ({ ...f, prestadorId: e.target.value }))}>
            <option value="">Seleccioná...</option>
            {prestadores.map((p) => <option key={p.id} value={p.id}>{p.nombreCorto} — {p.nombre}</option>)}
          </BrandSelect>
        </div>
        <BrandSelect label="Tipo de servicio *" required value={form.tipoServicio} onChange={(e) => setForm((f) => ({ ...f, tipoServicio: e.target.value }))}>
          <option value="">Seleccioná...</option>
          {TIPOS.map((t) => <option key={t} value={t}>{t}</option>)}
        </BrandSelect>
        <BrandInput label="Zona (vacío = todas)" value={form.zona} placeholder="Villa Mercedes..." onChange={(e) => setForm((f) => ({ ...f, zona: e.target.value }))} />
        <BrandInput label="Costo servicio (ARS) *" type="number" step="0.01" required value={form.costoServicio} onChange={(e) => setForm((f) => ({ ...f, costoServicio: e.target.value }))} />
        <BrandInput label="Costo km (ARS) *" type="number" step="0.01" required value={form.costoKm} onChange={(e) => setForm((f) => ({ ...f, costoKm: e.target.value }))} />
        <BrandInput label="Vigencia desde *" type="date" required value={form.vigenciaDesde} onChange={(e) => setForm((f) => ({ ...f, vigenciaDesde: e.target.value }))} />
        <BrandInput label="Vigencia hasta" type="date" value={form.vigenciaHasta} onChange={(e) => setForm((f) => ({ ...f, vigenciaHasta: e.target.value }))} />
        <div className="col-span-2 flex justify-end gap-3 pt-1">
          <BrandButton type="button" variant="outline" onClick={handleClose}>Cancelar</BrandButton>
          <BrandButton type="submit" loading={loading}>Guardar</BrandButton>
        </div>
      </form>
    </BrandModal>
  );
}

function CsvImportModal({ isOpen, onClose, onSuccess }: { isOpen: boolean; onClose: () => void; onSuccess: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const handleClose = () => { setFile(null); setError(null); onClose(); };
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const res = await liquidacionesApi.importTarifariosCsv(file);
      toast.success(`${res.creados} tarifas importadas`);
      handleClose();
      onSuccess();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al importar");
    } finally {
      setLoading(false);
    }
  };
  return (
    <BrandModal isOpen={isOpen} onClose={handleClose} title="Cargar planilla CSV" error={error}>
      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        <BrandFileInput label="Archivo CSV *" accept=".csv" required onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        <div className="flex justify-end gap-3 pt-1">
          <BrandButton type="button" variant="outline" onClick={handleClose}>Cancelar</BrandButton>
          <BrandButton type="submit" loading={loading} disabled={!file}>Importar</BrandButton>
        </div>
      </form>
    </BrandModal>
  );
}

export function TarifariosConfig() {
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
  const [csvOpen, setCsvOpen] = useState(false);
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

  const pstSeleccionado = prestadores.find((p) => p.id === filtroPst) ?? null;
  const loadingTarifarios = filtroPst !== "" && filtroPst !== tarifariosPstId;

  const selectCls = "rounded-[8px] border border-border bg-card px-3 py-2 font-body text-sm text-foreground outline-none focus:border-brand-orange/70";
  const thCls = "py-3 px-4 font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground text-left";
  const tdCls = "py-3 px-4 font-body text-sm text-foreground";

  return (
    <div className="flex flex-col gap-5 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-heading text-xl font-extrabold text-foreground">Estructura de Tarifarios</h1>
          <p className="font-body text-sm text-muted-foreground">
            {pstSeleccionado ? `${tarifarios.length} tarifas de ${pstSeleccionado.nombreCorto}` : "Seleccioná un prestador para ver sus tarifas"}
          </p>
        </div>
        <div className="flex gap-2">
          <BrandButton size="sm" variant="outline" onClick={handleDownload}>Descargar CSV</BrandButton>
          <BrandButton size="sm" variant="outline" onClick={() => setCsvOpen(true)}>Cargar CSV</BrandButton>
          <BrandButton size="sm" onClick={() => { setEditing(null); setModalOpen(true); }}>+ Nueva tarifa</BrandButton>
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
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-muted/40">
                  <th className={thCls}>Tipo servicio</th>
                  <th className={thCls}>Zona</th>
                  <th className={`${thCls} text-right`}>Costo serv.</th>
                  <th className={`${thCls} text-right`}>Costo KM</th>
                  <th className={thCls}>Vigencia desde</th>
                  <th className={thCls}>Vigencia hasta</th>
                  <th className={`${thCls} text-right`}></th>
                </tr>
              </thead>
              <tbody>
                {tarifarios.map((t) => (
                  <tr key={t.id} className="border-t border-border transition-colors hover:bg-muted/30">
                    <td className={tdCls}>{t.tipoServicio}</td>
                    <td className={`${tdCls} text-muted-foreground`}>{t.zona || "—"}</td>
                    <td className={`${tdCls} text-right`}>{formatARS(t.costoServicio)}</td>
                    <td className={`${tdCls} text-right`}>{formatARS(t.costoKm)}</td>
                    <td className={`${tdCls} text-muted-foreground`}>{t.vigenciaDesde}</td>
                    <td className={`${tdCls} text-muted-foreground`}>{t.vigenciaHasta || "—"}</td>
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

      <TarifaModal key={editing?.id ?? "nueva"} isOpen={modalOpen} onClose={() => { setModalOpen(false); setEditing(null); }} prestadores={prestadores} editing={editing} defaultPrestadorId={filtroPst} onSuccess={loadTarifarios} />
      <CsvImportModal isOpen={csvOpen} onClose={() => setCsvOpen(false)} onSuccess={loadTarifarios} />
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
