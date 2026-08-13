"use client";

import { useState } from "react";
import { toast } from "sonner";
import { BrandButton, BrandFileInput } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { ImportExcelMaestroResult } from "../types/liquidaciones";

function mensajeExito(res: ImportExcelMaestroResult): string {
  const prestador = res.prestadorCreado ? "creado" : "existente";
  const tablaKm = res.hojaTablaKm
    ? `${res.tablaKmCreadas} filas (${res.tablaKmOmitidas} omitidas)`
    : "sin hoja de Tabla KM en el archivo";
  return (
    `Prestador: ${prestador} | SPSTs: ${res.spstsCreados} nuevos | ` +
    `Tarifarios: ${res.tarifariosCreados} nuevos (${res.tarifariosOmitidos} omitidos) | ` +
    `Tabla KM: ${tablaKm}`
  );
}

export function PrestadoresExcelImportModal({
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
      const res = await liquidacionesApi.importExcelMaestro(file);
      toast.success(mensajeExito(res), { duration: 8000 });
      handleClose();
      onSuccess();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al importar");
    } finally {
      setLoading(false);
    }
  };

  return (
    <BrandModal isOpen={isOpen} onClose={handleClose} title="Cargar Excel maestro" error={error}>
      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        <p className="font-body text-sm text-muted-foreground">
          Un único archivo por prestador/mes (ej. &quot;PENTACOM 202601.xlsx&quot;) con
          Prestador, SPSTs, Tarifarios y Tabla KM en distintas hojas.
        </p>
        <BrandFileInput
          label="Archivo Excel *"
          accept=".xlsx,.xls"
          required
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
        <div className="flex justify-end gap-3 pt-1">
          <BrandButton type="button" variant="outline" onClick={handleClose}>Cancelar</BrandButton>
          <BrandButton type="submit" loading={loading} disabled={!file}>Importar</BrandButton>
        </div>
      </form>
    </BrandModal>
  );
}
