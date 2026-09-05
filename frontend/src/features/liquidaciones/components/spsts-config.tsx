"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { BrandButton, BrandFileInput } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { Badge } from "@/shared/components/ui/badge";
import { Spinner } from "@/shared/components/ui/spinner";
import { useSession } from "@/services/session-provider";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { PrestadorLiquidacion, Spst } from "../types/liquidaciones";
import { SpstBaseSucursalModal } from "./spst-base-sucursal-modal";
import { SpstFormModal } from "./spst-form-modal";

const thCls = "py-3 px-4 font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground text-left";
const tdCls = "py-3 px-4 font-body text-sm text-foreground";

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
  // Mutaciones = liquidaciones.update; descarga CSV = liquidaciones.export (ADR-029).
  const { can } = useSession();
  const puedeEditar = can("liquidaciones", "update");
  const puedeExportar = can("liquidaciones", "export");
  const [spsts, setSpsts] = useState<Spst[]>([]);
  const [prestadores, setPrestadores] = useState<PrestadorLiquidacion[]>([]);
  const [loading, setLoading] = useState(true);
  const [filtroPst, setFiltroPst] = useState("");
  // `undefined` = cerrado; `null` = alta; un SPST = edición.
  const [formSpst, setFormSpst] = useState<Spst | null | undefined>(undefined);
  const [baseSucursalSpst, setBaseSucursalSpst] = useState<Spst | null>(null);
  const [csvOpen, setCsvOpen] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

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

  const handleDelete = async () => {
    if (!deletingId) return;
    try {
      await liquidacionesApi.deleteSpst(deletingId);
      toast.success("SPST eliminado");
      setDeletingId(null);
      void load();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Error al eliminar");
    }
  };

  const selectCls = "rounded-[8px] border border-border bg-card px-3 py-2 font-body text-sm text-foreground outline-none focus:border-brand-orange/70";

  return (
    <div className="flex flex-col gap-5 p-6">
      <div className="flex items-center justify-between">
        <h1 className="font-heading text-xl font-extrabold text-foreground">SPSTs</h1>
        <div className="flex gap-2">
          {puedeExportar && <BrandButton size="sm" variant="outline" onClick={handleDownload}>Descargar CSV</BrandButton>}
          {puedeEditar && (
            <>
              <BrandButton size="sm" variant="outline" onClick={() => setCsvOpen(true)}>Cargar CSV</BrandButton>
              <BrandButton size="sm" onClick={() => setFormSpst(null)}>Nuevo SPST</BrandButton>
            </>
          )}
        </div>
      </div>

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
                  <th className={thCls}>Zona de cobertura</th>
                  <th className={thCls} title="A diferencia del vínculo Siges del Prestador, este no sincroniza datos — solo saca al SPST de la lista de 'disponibles' para vincular a otro">Vínculo Siges</th>
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
                      <td className={`${tdCls} text-muted-foreground`}>{s.zonaCobertura || "—"}</td>
                      <td className={tdCls}>
                        {s.sigesEmpresaId != null ? (
                          <Badge variant="success">#{s.sigesEmpresaId}</Badge>
                        ) : (
                          <Badge variant="neutral">Sin vínculo</Badge>
                        )}
                      </td>
                      <td className={tdCls}>
                        <Badge variant={s.activo ? "success" : "neutral"}>{s.activo ? "Activo" : "Inactivo"}</Badge>
                      </td>
                      <td className={`${tdCls} text-right`}>
                        {puedeEditar && (
                          <>
                            {pst?.sigesEmpresaId != null && (
                              <button onClick={() => setBaseSucursalSpst(s)} className={`font-body text-sm hover:underline mr-3 ${s.sigesBaseSucursalId ? "text-success" : "text-muted-foreground"}`}>
                                Base despacho
                              </button>
                            )}
                            <button onClick={() => setFormSpst(s)} className="font-body text-sm text-brand-orange hover:underline mr-3">Editar</button>
                            <button onClick={() => handleToggle(s)} className={`font-body text-sm hover:underline mr-3 ${s.activo ? "text-destructive" : "text-success"}`}>
                              {s.activo ? "Desactivar" : "Activar"}
                            </button>
                            <button onClick={() => setDeletingId(s.id)} className="font-body text-sm text-destructive hover:underline">Eliminar</button>
                          </>
                        )}
                      </td>
                    </tr>
                  );
                })}
                {visible.length === 0 && (
                  <tr><td colSpan={7} className="py-10 text-center font-body text-sm text-muted-foreground">No hay SPSTs con los filtros seleccionados.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {formSpst !== undefined && (
        <SpstFormModal spst={formSpst} prestadores={prestadores} onClose={() => setFormSpst(undefined)} onSuccess={load} />
      )}
      {baseSucursalSpst && (() => {
        const pst = prestadorMap[baseSucursalSpst.prestadorId];
        return pst ? (
          <SpstBaseSucursalModal
            spst={baseSucursalSpst}
            prestador={pst}
            onClose={() => setBaseSucursalSpst(null)}
            onChanged={() => { setBaseSucursalSpst(null); void load(); }}
          />
        ) : null;
      })()}
      <CsvImportModal isOpen={csvOpen} onClose={() => setCsvOpen(false)} onSuccess={load} />
      <BrandModal isOpen={!!deletingId} onClose={() => setDeletingId(null)} title="Eliminar SPST">
        <p className="font-body text-sm text-muted-foreground mb-5">
          Esta acción no se puede deshacer. Las filas de Tabla KM que apunten a este SPST
          quedan sin SPST asignado, no se borran. ¿Confirmás la eliminación?
        </p>
        <div className="flex justify-end gap-3">
          <BrandButton variant="outline" onClick={() => setDeletingId(null)}>Cancelar</BrandButton>
          <BrandButton onClick={handleDelete}>Sí, eliminar</BrandButton>
        </div>
      </BrandModal>
    </div>
  );
}
