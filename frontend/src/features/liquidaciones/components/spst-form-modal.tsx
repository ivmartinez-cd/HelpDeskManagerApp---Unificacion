"use client";

import { useState } from "react";
import { toast } from "sonner";
import { BrandButton, BrandInput, BrandSelect } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { useModalSubmit } from "@/shared/hooks/use-modal-submit";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { PrestadorLiquidacion, Spst } from "../types/liquidaciones";

/** Modal de alta/edición de un SPST (`spst: null` = alta). Se monta solo
 * mientras está abierto (el padre lo renderiza condicionalmente), así el
 * estado del formulario arranca fresco en cada apertura. */
export function SpstFormModal({
  spst,
  prestadores,
  onClose,
  onSuccess,
}: {
  spst: Spst | null;
  prestadores: PrestadorLiquidacion[];
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [form, setForm] = useState({
    prestadorId: spst?.prestadorId ?? "",
    nombre: spst?.nombre ?? "",
    domicilio: spst?.domicilio ?? "",
    localidad: spst?.localidad ?? "",
    provincia: spst?.provincia ?? "",
    zonaCobertura: spst?.zonaCobertura ?? "",
  });
  const { saving, error, submit } = useModalSubmit();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.prestadorId) return;
    void submit(async () => {
      const payload = {
        prestadorId: form.prestadorId,
        nombre: form.nombre,
        domicilio: form.domicilio || undefined,
        localidad: form.localidad || undefined,
        provincia: form.provincia || undefined,
        zonaCobertura: form.zonaCobertura || undefined,
      };
      if (spst) {
        await liquidacionesApi.updateSpst(spst.id, payload);
        toast.success("SPST actualizado");
      } else {
        await liquidacionesApi.createSpst(payload);
        toast.success("SPST creado");
      }
      onClose();
      onSuccess();
    }, "Error al guardar");
  };

  return (
    <BrandModal isOpen onClose={onClose} title={spst ? "Editar SPST" : "Nuevo SPST"} error={error}>
      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        <BrandSelect label="Prestador *" required value={form.prestadorId} onChange={(e) => setForm((f) => ({ ...f, prestadorId: e.target.value }))}>
          <option value="">Seleccioná...</option>
          {prestadores.map((p) => <option key={p.id} value={p.id}>{p.nombreCorto} — {p.nombre}</option>)}
        </BrandSelect>
        <BrandInput label="Nombre *" required value={form.nombre} onChange={(e) => setForm((f) => ({ ...f, nombre: e.target.value }))} />
        <BrandInput label="Domicilio base" value={form.domicilio} onChange={(e) => setForm((f) => ({ ...f, domicilio: e.target.value }))} />
        <BrandInput label="Localidad" value={form.localidad} onChange={(e) => setForm((f) => ({ ...f, localidad: e.target.value }))} />
        <BrandInput label="Provincia" value={form.provincia} onChange={(e) => setForm((f) => ({ ...f, provincia: e.target.value }))} />
        <BrandInput
          label="Zona de cobertura"
          hint="Solo texto de referencia — no afecta qué tarifa se cobra. La tarifa se asigna directo al SPST."
          value={form.zonaCobertura}
          placeholder="Córdoba Capital..."
          onChange={(e) => setForm((f) => ({ ...f, zonaCobertura: e.target.value }))}
        />
        <div className="flex justify-end gap-3 pt-1">
          <BrandButton type="button" variant="outline" onClick={onClose}>Cancelar</BrandButton>
          <BrandButton type="submit" loading={saving}>{spst ? "Guardar cambios" : "Crear SPST"}</BrandButton>
        </div>
      </form>
    </BrandModal>
  );
}
