"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import {
  BrandButton,
  BrandFileInput,
  BrandInput,
  BrandSelect,
} from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { Badge } from "@/shared/components/ui/badge";
import { Spinner } from "@/shared/components/ui/spinner";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { PrestadorLiquidacion, Spst } from "../types/liquidaciones";

const thCls = "py-3 px-4 font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground text-left";
const tdCls = "py-3 px-4 font-body text-sm text-foreground";

type FormState = {
  prestadorId: string; nombre: string; domicilio: string;
  localidad: string; provincia: string; zona: string;
};
const EMPTY: FormState = { prestadorId: "", nombre: "", domicilio: "", localidad: "", provincia: "", zona: "" };

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
      const res = await liquidacionesApi.importSpstsCsv(file);
      toast.success(`${res.creados} SPSTs importados`);
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

export function SpstsConfig() {
  const [spsts, setSpsts] = useState<Spst[]>([]);
  const [prestadores, setPrestadores] = useState<PrestadorLiquidacion[]>([]);
  const [loading, setLoading] = useState(true);
  const [filtroPst, setFiltroPst] = useState("");
  const [form, setForm] = useState<FormState>(EMPTY);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [csvOpen, setCsvOpen] = useState(false);

  // Sin setLoading(true) sincrónico — ver nota en liquidaciones-lista.tsx.
  const load = useCallback(async () => {
    try {
      const [s, p] = await Promise.all([
        liquidacionesApi.listSpsts(),
        liquidacionesApi.listPrestadores(false),
      ]);
      setSpsts(s);
      setPrestadores(p);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const prestadorMap = Object.fromEntries(prestadores.map((p) => [p.id, p]));
  const visible = filtroPst ? spsts.filter((s) => s.prestadorId === filtroPst) : spsts;

  const startEdit = (s: Spst) => {
    setEditingId(s.id);
    setForm({ prestadorId: s.prestadorId, nombre: s.nombre, domicilio: s.domicilio ?? "", localidad: s.localidad ?? "", provincia: s.provincia ?? "", zona: s.zona ?? "" });
  };

  const cancelEdit = () => { setEditingId(null); setForm(EMPTY); };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.prestadorId) return;
    setSaving(true);
    try {
      const payload = { prestadorId: form.prestadorId, nombre: form.nombre, domicilio: form.domicilio || undefined, localidad: form.localidad || undefined, provincia: form.provincia || undefined, zona: form.zona || undefined };
      if (editingId) {
        await liquidacionesApi.updateSpst(editingId, payload);
        toast.success("SPST actualizado");
      } else {
        await liquidacionesApi.createSpst(payload);
        toast.success("SPST creado");
      }
      cancelEdit();
      void load();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  const handleToggle = async (s: Spst) => {
    try {
      await liquidacionesApi.toggleSpstActivo(s.id, !s.activo);
      void load();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Error");
    }
  };

  const handleDownload = async () => {
    try { await liquidacionesApi.exportSpstsCsv(); }
    catch { toast.error("Error al descargar"); }
  };

  const selectCls = "rounded-[8px] border border-border bg-card px-3 py-2 font-body text-sm text-foreground outline-none focus:border-brand-orange/70";

  return (
    <div className="flex flex-col gap-5 p-6">
      <div className="flex items-center justify-between">
        <h1 className="font-heading text-xl font-extrabold text-foreground">SPSTs</h1>
        <div className="flex gap-2">
          <BrandButton size="sm" variant="outline" onClick={handleDownload}>Descargar CSV</BrandButton>
          <BrandButton size="sm" onClick={() => setCsvOpen(true)}>Cargar CSV</BrandButton>
        </div>
      </div>

      {/* Formulario inline */}
      <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-3 rounded-[12px] border border-border bg-card p-4 lg:grid-cols-3">
        <BrandSelect label="Prestador *" required value={form.prestadorId} onChange={(e) => setForm((f) => ({ ...f, prestadorId: e.target.value }))}>
          <option value="">Seleccioná...</option>
          {prestadores.map((p) => <option key={p.id} value={p.id}>{p.nombreCorto} — {p.nombre}</option>)}
        </BrandSelect>
        <BrandInput label="Nombre *" required value={form.nombre} onChange={(e) => setForm((f) => ({ ...f, nombre: e.target.value }))} />
        <BrandInput label="Domicilio base" value={form.domicilio} onChange={(e) => setForm((f) => ({ ...f, domicilio: e.target.value }))} />
        <BrandInput label="Localidad" value={form.localidad} onChange={(e) => setForm((f) => ({ ...f, localidad: e.target.value }))} />
        <BrandInput label="Provincia" value={form.provincia} onChange={(e) => setForm((f) => ({ ...f, provincia: e.target.value }))} />
        <BrandInput label="Zona" value={form.zona} placeholder="Córdoba Capital..." onChange={(e) => setForm((f) => ({ ...f, zona: e.target.value }))} />
        <div className="col-span-2 flex gap-2 lg:col-span-3">
          <BrandButton type="submit" loading={saving}>{editingId ? "Guardar cambios" : "Crear SPST"}</BrandButton>
          {editingId && <BrandButton type="button" variant="outline" onClick={cancelEdit}>Cancelar</BrandButton>}
        </div>
      </form>

      {/* Filtro */}
      <div className="flex items-center gap-3">
        <select value={filtroPst} onChange={(e) => setFiltroPst(e.target.value)} className={selectCls} aria-label="Filtrar por PST">
          <option value="">Todos los PSTs</option>
          {prestadores.map((p) => <option key={p.id} value={p.id}>{p.nombreCorto}</option>)}
        </select>
        <span className="ml-auto font-body text-sm text-muted-foreground">{visible.length} SPSTs</span>
      </div>

      {loading ? (
        <div className="flex h-40 items-center justify-center"><Spinner /></div>
      ) : (
        <div className="overflow-hidden rounded-[12px] border border-border bg-card">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-muted/40">
                  <th className={thCls}>PST</th>
                  <th className={thCls}>Nombre</th>
                  <th className={thCls}>Localidad</th>
                  <th className={thCls}>Zona</th>
                  <th className={thCls}>Estado</th>
                  <th className={`${thCls} text-right`}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {visible.map((s) => {
                  const pst = prestadorMap[s.prestadorId];
                  return (
                    <tr key={s.id} className="border-t border-border transition-colors hover:bg-muted/30">
                      <td className={tdCls}><span className="font-heading text-sm font-bold uppercase text-foreground">{pst?.nombreCorto ?? "—"}</span></td>
                      <td className={tdCls}><span className="text-brand-orange">{s.nombre}</span></td>
                      <td className={`${tdCls} text-muted-foreground`}>{s.localidad || "—"}</td>
                      <td className={`${tdCls} text-muted-foreground`}>{s.zona || "—"}</td>
                      <td className={tdCls}>
                        <Badge variant={s.activo ? "success" : "neutral"}>{s.activo ? "Activo" : "Inactivo"}</Badge>
                      </td>
                      <td className={`${tdCls} text-right`}>
                        <button onClick={() => startEdit(s)} className="font-body text-sm text-brand-orange hover:underline mr-3">Editar</button>
                        <button onClick={() => handleToggle(s)} className={`font-body text-sm hover:underline ${s.activo ? "text-destructive" : "text-success"}`}>
                          {s.activo ? "Desactivar" : "Activar"}
                        </button>
                      </td>
                    </tr>
                  );
                })}
                {visible.length === 0 && (
                  <tr><td colSpan={6} className="py-10 text-center font-body text-sm text-muted-foreground">No hay SPSTs con los filtros seleccionados.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <CsvImportModal isOpen={csvOpen} onClose={() => setCsvOpen(false)} onSuccess={load} />
    </div>
  );
}
