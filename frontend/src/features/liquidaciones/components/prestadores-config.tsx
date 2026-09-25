"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { BrandButton, BrandFileInput } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { Spinner } from "@/shared/components/ui/spinner";
import { useSession } from "@/services/session-provider";
import { prestadoresApi } from "@/features/prestadores/api/prestadores-api";
import { AltaPrestadorWizard } from "./alta-prestador/alta-prestador-wizard";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { PrestadorLiquidacion } from "../types/liquidaciones";
import { PrestadorBaseSucursalModal } from "./prestador-base-sucursal-modal";
import { PrestadorCdModal } from "./prestador-cd-modal";
import { PrestadorFormModal } from "./prestador-form-modal";
import { PrestadorSlaModal } from "./prestador-sla-modal";
import { PrestadoresTabla } from "./prestadores-tabla";
import { PrestadoresExcelImportModal } from "./prestadores-excel-import-modal";
import { SigesSyncModal } from "./siges-sync-modal";

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
  // Mutaciones = liquidaciones.update; descarga CSV = liquidaciones.export (ADR-029).
  const { can } = useSession();
  const puedeEditar = can("liquidaciones", "update");
  const puedeExportar = can("liquidaciones", "export");
  const [prestadores, setPrestadores] = useState<PrestadorLiquidacion[]>([]);
  const [loading, setLoading] = useState(true);
  const [formPrestador, setFormPrestador] = useState<PrestadorLiquidacion | undefined>(undefined);
  const [wizardOpen, setWizardOpen] = useState(false);
  const [csvOpen, setCsvOpen] = useState(false);
  const [excelOpen, setExcelOpen] = useState(false);
  const [sigesOpen, setSigesOpen] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [basePrestador, setBasePrestador] = useState<PrestadorLiquidacion | null>(null);
  const [cdPrestador, setCdPrestador] = useState<PrestadorLiquidacion | null>(null);
  const [slaPrestador, setSlaPrestador] = useState<PrestadorLiquidacion | null>(null);
  // Ids de Siges ya dados de alta en el módulo SLA (otro módulo, catálogo
  // aparte) — sin esto no hay forma de saber si falta completar ese paso del
  // asistente, que a diferencia de Siges/Base/CD no tiene botón de vuelta.
  // `null` = todavía no se pudo consultar (o el usuario no tiene permiso sobre
  // `prestadores` — permiso distinto al de este módulo): en ese caso no se
  // ofrece el botón, para no arriesgar una alta SLA duplicada por un dato que
  // no se pudo verificar.
  const [sigesConAltaSla, setSigesConAltaSla] = useState<Set<number> | null>(null);

  // Sin setLoading(true) sincrónico — ver nota en liquidaciones-lista.tsx.
  const load = useCallback(async () => {
    try {
      setPrestadores(await liquidacionesApi.listPrestadores(false));
    } finally {
      setLoading(false);
    }
  }, []);

  // Promise-chain en vez de async/await: react-hooks/set-state-in-effect solo
  // acepta setState en callbacks .then/.catch (ver nota en siges-sync-modal.tsx).
  const loadAltasSla = useCallback(
    () =>
      prestadoresApi
        .getResumen()
        .then((resumen) => {
          const ids = resumen.grupos.flatMap((g) => g.prestadores.map((p) => p.sigesEmpresaId));
          setSigesConAltaSla(new Set(ids));
        })
        .catch((err: unknown) => {
          // Sin permiso sobre `prestadores`, u otro error — se oculta el botón
          // "Completar alta SLA" en vez de arriesgar una alta duplicada.
          console.error("No se pudo consultar el módulo SLA:", err);
        }),
    [],
  );

  useEffect(() => { void load(); }, [load]);
  useEffect(() => { void loadAltasSla(); }, [loadAltasSla]);

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
          {puedeEditar && <BrandButton size="sm" variant="outline" onClick={() => setSigesOpen(true)}>Sincronizar</BrandButton>}
          {puedeExportar && <BrandButton size="sm" variant="outline" onClick={handleDownload}>Descargar CSV</BrandButton>}
          {puedeEditar && (
            <>
              <BrandButton size="sm" variant="outline" onClick={() => setExcelOpen(true)}>Cargar Excel maestro</BrandButton>
              <BrandButton size="sm" variant="outline" onClick={() => setCsvOpen(true)}>Cargar CSV</BrandButton>
              <BrandButton size="sm" onClick={() => setWizardOpen(true)}>Nuevo prestador</BrandButton>
            </>
          )}
        </div>
      </div>

      {/* Tabla */}
      {loading ? (
        <div className="flex h-40 items-center justify-center"><Spinner /></div>
      ) : (
        <PrestadoresTabla
          prestadores={prestadores}
          puedeEditar={puedeEditar}
          sigesConAltaSla={sigesConAltaSla}
          acciones={{
            onEditar: setFormPrestador,
            onCd: setCdPrestador,
            onBase: setBasePrestador,
            onSla: setSlaPrestador,
            onToggle: (p) => void handleToggle(p),
            onEliminar: setDeletingId,
          }}
        />
      )}

      {formPrestador !== undefined && (
        <PrestadorFormModal prestador={formPrestador} onClose={() => setFormPrestador(undefined)} onSuccess={load} />
      )}
      {wizardOpen && (
        <AltaPrestadorWizard onClose={() => setWizardOpen(false)} onCreado={load} />
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
      {cdPrestador && (
        <PrestadorCdModal
          prestador={cdPrestador}
          onClose={() => setCdPrestador(null)}
          onSuccess={load}
        />
      )}
      {slaPrestador && (
        <PrestadorSlaModal
          prestador={slaPrestador}
          onClose={() => setSlaPrestador(null)}
          onCreado={() => { setSlaPrestador(null); void loadAltasSla(); }}
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
