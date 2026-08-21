"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { BrandButton, BrandFileInput } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { Badge } from "@/shared/components/ui/badge";
import { Spinner } from "@/shared/components/ui/spinner";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { PrestadorLiquidacion } from "../types/liquidaciones";
import { PrestadorBaseSucursalModal } from "./prestador-base-sucursal-modal";
import { PrestadorFormModal } from "./prestador-form-modal";
import { PrestadoresExcelImportModal } from "./prestadores-excel-import-modal";
import { SigesSyncModal } from "./siges-sync-modal";

const thCls = "py-3 px-4 font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground text-left";
const tdCls = "py-3 px-4 font-body text-sm text-foreground";

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
  // `undefined` = cerrado; `null` = alta; un prestador = edición.
  const [formPrestador, setFormPrestador] = useState<PrestadorLiquidacion | null | undefined>(undefined);
  const [csvOpen, setCsvOpen] = useState(false);
  const [excelOpen, setExcelOpen] = useState(false);
  const [sigesOpen, setSigesOpen] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [basePrestador, setBasePrestador] = useState<PrestadorLiquidacion | null>(null);

  // Sin setLoading(true) sincrónico — ver nota en liquidaciones-lista.tsx.
  const load = useCallback(async () => {
    try {
      setPrestadores(await liquidacionesApi.listPrestadores(false));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

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

  const handleDelete = async () => {
    if (!deletingId) return;
    try {
      await liquidacionesApi.deletePrestador(deletingId);
      toast.success("Prestador eliminado");
      setDeletingId(null);
      void load();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Error al eliminar");
    }
  };

  return (
    <div className="flex flex-col gap-5 p-6">
      <div className="flex items-center justify-between">
        <h1 className="font-heading text-xl font-extrabold text-foreground">Prestadores</h1>
        <div className="flex gap-2">
          <BrandButton size="sm" variant="outline" onClick={() => setSigesOpen(true)}>Sincronizar</BrandButton>
          <BrandButton size="sm" variant="outline" onClick={handleDownload}>Descargar CSV</BrandButton>
          <BrandButton size="sm" variant="outline" onClick={() => setExcelOpen(true)}>Cargar Excel maestro</BrandButton>
          <BrandButton size="sm" variant="outline" onClick={() => setCsvOpen(true)}>Cargar CSV</BrandButton>
          <BrandButton size="sm" onClick={() => setFormPrestador(null)}>Nuevo prestador</BrandButton>
        </div>
      </div>

      {/* Tabla */}
      {loading ? (
        <div className="flex h-40 items-center justify-center"><Spinner /></div>
      ) : (
        <div className="overflow-hidden rounded-[12px] border border-border bg-card">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-muted/40">
                  <th className={thCls}>Clave</th>
                  <th className={thCls}>Nombre</th>
                  <th className={thCls}>CUIT</th>
                  <th className={thCls}>Región</th>
                  <th className={thCls}>Vínculo</th>
                  <th className={thCls}>Estado</th>
                  <th className={`${thCls} text-right`}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {prestadores.map((p) => (
                  <tr key={p.id} className="border-t border-border transition-colors hover:bg-muted/30">
                    <td className={tdCls}><span className="font-heading text-sm font-bold uppercase text-foreground">{p.nombreCorto}</span></td>
                    <td className={tdCls}>{p.nombre}</td>
                    <td className={`${tdCls} text-muted-foreground`}>{p.cuit || "—"}</td>
                    <td className={`${tdCls} text-muted-foreground`}>{p.region?.toUpperCase() || "—"}</td>
                    <td className={tdCls}>
                      {p.sigesEmpresaId != null ? (
                        <Badge variant="success">#{p.sigesEmpresaId}</Badge>
                      ) : (
                        <Badge variant="neutral">Sin vínculo</Badge>
                      )}
                    </td>
                    <td className={tdCls}>
                      <Badge variant={p.activo ? "success" : "neutral"}>{p.activo ? "Activo" : "Inactivo"}</Badge>
                    </td>
                    <td className={`${tdCls} text-right`}>
                      <button onClick={() => setFormPrestador(p)} className="font-body text-sm text-brand-orange hover:underline mr-3">Editar</button>
                      {p.sigesEmpresaId != null && (
                        <button onClick={() => setBasePrestador(p)} className="font-body text-sm text-brand-orange hover:underline mr-3">
                          {p.sigesBaseSucursalId != null ? "Distancias" : "Base"}
                        </button>
                      )}
                      <button onClick={() => handleToggle(p)} className={`font-body text-sm hover:underline mr-3 ${p.activo ? "text-destructive" : "text-success"}`}>
                        {p.activo ? "Desactivar" : "Activar"}
                      </button>
                      <button onClick={() => setDeletingId(p.id)} className="font-body text-sm text-destructive hover:underline">Eliminar</button>
                    </td>
                  </tr>
                ))}
                {prestadores.length === 0 && (
                  <tr><td colSpan={7} className="py-10 text-center font-body text-sm text-muted-foreground">No hay prestadores cargados.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {formPrestador !== undefined && (
        <PrestadorFormModal prestador={formPrestador} onClose={() => setFormPrestador(undefined)} onSuccess={load} />
      )}
      <CsvImportModal isOpen={csvOpen} onClose={() => setCsvOpen(false)} onSuccess={load} />
      <PrestadoresExcelImportModal isOpen={excelOpen} onClose={() => setExcelOpen(false)} onSuccess={load} />
      {sigesOpen && (
        <SigesSyncModal isOpen onClose={() => setSigesOpen(false)} onChanged={load} />
      )}
      {basePrestador && (
        <PrestadorBaseSucursalModal
          prestador={basePrestador}
          onClose={() => setBasePrestador(null)}
          onChanged={() => { setBasePrestador(null); void load(); }}
        />
      )}
      <BrandModal isOpen={!!deletingId} onClose={() => setDeletingId(null)} title="Eliminar prestador">
        <p className="font-body text-sm text-muted-foreground mb-5">
          Esta acción no se puede deshacer. Si el prestador tiene liquidaciones asociadas,
          el borrado va a quedar bloqueado — desactivalo en su lugar. ¿Confirmás la eliminación?
        </p>
        <div className="flex justify-end gap-3">
          <BrandButton variant="outline" onClick={() => setDeletingId(null)}>Cancelar</BrandButton>
          <BrandButton onClick={handleDelete}>Sí, eliminar</BrandButton>
        </div>
      </BrandModal>
    </div>
  );
}
