"use client";

import { useState } from "react";
import { toast } from "sonner";
import { BrandButton, BrandInput } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { PrestadorLiquidacion } from "../types/liquidaciones";

/** Edición de los datos básicos de un prestador ya existente. El alta se hace
 * por `AltaPrestadorWizard` (features/alta-prestador) — cruza Siges/Canal
 * Directo/módulo SLA, este modal se quedó solo con la edición simple. Se
 * monta solo mientras está abierto (el padre lo renderiza
 * condicionalmente), así el estado del formulario arranca fresco en cada
 * apertura. */
export function PrestadorFormModal({
  prestador,
  onClose,
  onSuccess,
}: {
  prestador: PrestadorLiquidacion;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [form, setForm] = useState({
    nombre: prestador.nombre,
    nombreCorto: prestador.nombreCorto,
    cuit: prestador.cuit ?? "",
    region: prestador.region ?? "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await liquidacionesApi.updatePrestador(prestador.id, {
        nombre: form.nombre,
        nombreCorto: form.nombreCorto,
        cuit: form.cuit || undefined,
        region: form.region || undefined,
      });
      toast.success("Prestador actualizado");
      onClose();
      onSuccess();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  return (
    <BrandModal isOpen onClose={onClose} title="Editar prestador" error={error}>
      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        <BrandInput label="Nombre completo *" required value={form.nombre} onChange={(e) => setForm((f) => ({ ...f, nombre: e.target.value }))} />
        <BrandInput label="Clave *" required value={form.nombreCorto} placeholder="PENTACOM" onChange={(e) => setForm((f) => ({ ...f, nombreCorto: e.target.value }))} />
        <BrandInput label="CUIT" value={form.cuit} placeholder="30712345678" onChange={(e) => setForm((f) => ({ ...f, cuit: e.target.value }))} />
        <BrandInput label="Región / Plaza" value={form.region} placeholder="Córdoba, Rosario..." onChange={(e) => setForm((f) => ({ ...f, region: e.target.value }))} />
        <div className="flex justify-end gap-3 pt-1">
          <BrandButton type="button" variant="outline" onClick={onClose}>Cancelar</BrandButton>
          <BrandButton type="submit" loading={saving}>Guardar cambios</BrandButton>
        </div>
      </form>
    </BrandModal>
  );
}
