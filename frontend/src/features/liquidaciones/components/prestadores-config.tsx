"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import {
  BrandButton,
  BrandFileInput,
  BrandInput,
} from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { Spinner } from "@/shared/components/ui/spinner";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { PrestadorLiquidacion } from "../types/liquidaciones";
import { PrestadoresExcelImportModal } from "./prestadores-excel-import-modal";

const thCls = "py-3 px-4 font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground text-left";
const tdCls = "py-3 px-4 font-body text-sm";

type FormState = { nombre: string; nombreCorto: string; cuit: string; region: string };

const EMPTY: FormState = { nombre: "", nombreCorto: "", cuit: "", region: "" };

function CsvImportModal({
  isOpen,
  onClose,
  onSuccess,
}: {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}) {
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
      const res = await liquidacionesApi.importPrestadoresCsv(file);
      toast.success(`${res.creados} prestadores importados`);
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

export function PrestadoresConfig() {
  const [prestadores, setPrestadores] = useState<PrestadorLiquidacion[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState<FormState>(EMPTY);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [csvOpen, setCsvOpen] = useState(false);
  const [excelOpen, setExcelOpen] = useState(false);

  // Sin setLoading(true) sincrónico — ver nota en liquidaciones-lista.tsx.
  const load = useCallback(async () => {
    try {
      setPrestadores(await liquidacionesApi.listPrestadores(false));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const startEdit = (p: PrestadorLiquidacion) => {
    setEditingId(p.id);
    setForm({ nombre: p.nombre, nombreCorto: p.nombreCorto, cuit: p.cuit ?? "", region: p.region ?? "" });
  };

  const cancelEdit = () => { setEditingId(null); setForm(EMPTY); };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = { nombre: form.nombre, nombreCorto: form.nombreCorto, cuit: form.cuit || undefined, region: form.region || undefined };
      if (editingId) {
        await liquidacionesApi.updatePrestador(editingId, payload);
        toast.success("Prestador actualizado");
      } else {
        await liquidacionesApi.createPrestador(payload);
        toast.success("Prestador creado");
      }
      cancelEdit();
      void load();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  const handleToggle = async (p: PrestadorLiquidacion) => {
    try {
      await liquidacionesApi.togglePrestadorActivo(p.id, !p.activo);
      void load();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Error");
    }
  };

  const handleDownload = async () => {
    try { await liquidacionesApi.exportPrestadoresCsv(); }
    catch { toast.error("Error al descargar"); }
  };

  return (
    <div className="flex flex-col gap-5 p-6">
      <div className="flex items-center justify-between">
        <h1 className="font-heading text-xl font-extrabold text-foreground">Prestadores</h1>
        <div className="flex gap-2">
          <BrandButton size="sm" variant="outline" onClick={handleDownload}>Descargar CSV</BrandButton>
          <BrandButton size="sm" variant="outline" onClick={() => setExcelOpen(true)}>Cargar Excel maestro</BrandButton>
          <BrandButton size="sm" onClick={() => setCsvOpen(true)}>Cargar CSV</BrandButton>
        </div>
      </div>

      {/* Formulario inline */}
      <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-3 rounded-[12px] border border-border bg-card p-4 lg:grid-cols-4">
        <BrandInput label="Nombre completo *" required value={form.nombre} onChange={(e) => setForm((f) => ({ ...f, nombre: e.target.value }))} />
        <BrandInput label="Clave *" required value={form.nombreCorto} placeholder="PENTACOM" onChange={(e) => setForm((f) => ({ ...f, nombreCorto: e.target.value }))} />
        <BrandInput label="CUIT" value={form.cuit} placeholder="30712345678" onChange={(e) => setForm((f) => ({ ...f, cuit: e.target.value }))} />
        <BrandInput label="Región / Plaza" value={form.region} placeholder="Córdoba, Rosario..." onChange={(e) => setForm((f) => ({ ...f, region: e.target.value }))} />
        <div className="col-span-2 flex gap-2 lg:col-span-4">
          <BrandButton type="submit" loading={saving}>{editingId ? "Guardar cambios" : "Crear prestador"}</BrandButton>
          {editingId && <BrandButton type="button" variant="outline" onClick={cancelEdit}>Cancelar</BrandButton>}
        </div>
      </form>

      {/* Tabla */}
      {loading ? (
        <div className="flex h-40 items-center justify-center"><Spinner /></div>
      ) : (
        <div className="overflow-hidden rounded-[12px]" style={{ background: "#1e1e1e", border: "1px solid rgba(255,255,255,.07)" }}>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr style={{ background: "rgba(0,0,0,.2)" }}>
                  <th className={thCls}>Clave</th>
                  <th className={thCls}>Nombre</th>
                  <th className={thCls}>CUIT</th>
                  <th className={thCls}>Región</th>
                  <th className={thCls}>Estado</th>
                  <th className={`${thCls} text-right`}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {prestadores.map((p) => (
                  <tr key={p.id} className="border-t transition-colors hover:bg-white/[0.03]" style={{ borderColor: "rgba(255,255,255,.07)" }}>
                    <td className={tdCls}><span className="font-heading text-sm font-bold uppercase text-foreground">{p.nombreCorto}</span></td>
                    <td className={tdCls} style={{ color: "#e0e0e0" }}>{p.nombre}</td>
                    <td className={tdCls} style={{ color: "rgba(255,255,255,.5)" }}>{p.cuit || "—"}</td>
                    <td className={tdCls} style={{ color: "rgba(255,255,255,.5)" }}>{p.region?.toUpperCase() || "—"}</td>
                    <td className={tdCls}>
                      <span className="inline-flex items-center rounded-full px-2.5 py-1 font-body text-[10px] font-bold uppercase tracking-wide"
                        style={p.activo ? { background: "rgba(34,197,94,.15)", color: "#4ade80" } : { background: "rgba(255,255,255,.08)", color: "rgba(255,255,255,.45)" }}>
                        {p.activo ? "Activo" : "Inactivo"}
                      </span>
                    </td>
                    <td className={`${tdCls} text-right`}>
                      <button onClick={() => startEdit(p)} className="font-body text-sm text-brand-orange hover:underline mr-3">Editar</button>
                      <button onClick={() => handleToggle(p)} className="font-body text-sm hover:underline" style={{ color: p.activo ? "#ef4444" : "#4ade80" }}>
                        {p.activo ? "Desactivar" : "Activar"}
                      </button>
                    </td>
                  </tr>
                ))}
                {prestadores.length === 0 && (
                  <tr><td colSpan={6} className="py-10 text-center font-body text-sm text-muted-foreground">No hay prestadores cargados.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <CsvImportModal isOpen={csvOpen} onClose={() => setCsvOpen(false)} onSuccess={load} />
      <PrestadoresExcelImportModal isOpen={excelOpen} onClose={() => setExcelOpen(false)} onSuccess={load} />
    </div>
  );
}
