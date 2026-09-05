"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { BrandButton, BrandInput, BrandSelect } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { PrestadorLiquidacion, Spst, Tarifario } from "../types/liquidaciones";

const TIPOS = [
  "correctivo", "preventivo", "instalacion_desinstalacion",
  "pre_correctivo", "guardia", "sistemas",
];

// Prefill del botón "Actualizar" de un grupo: nueva vigencia desde hoy con el
// tipo/SPST/costos de la tarifa vigente (el recadenado cierra la anterior).
export interface PlantillaTarifa {
  tipoServicio: string;
  spstId: string;
  costoServicio: string;
  costoKm: string;
}

function tarifaAForm(t: Tarifario | null, defaultPrestadorId: string, plantilla: PlantillaTarifa | null) {
  if (!t) {
    const hoy = new Date().toISOString().split("T")[0];
    return {
      prestadorId: defaultPrestadorId,
      tipoServicio: plantilla?.tipoServicio ?? "",
      spstId: plantilla?.spstId ?? "",
      costoServicio: plantilla?.costoServicio ?? "",
      costoKm: plantilla?.costoKm ?? "",
      vigenciaDesde: plantilla ? hoy : "",
      vigenciaHasta: "",
    };
  }
  return {
    prestadorId: t.prestadorId,
    tipoServicio: t.tipoServicio,
    spstId: t.spstId ?? "",
    costoServicio: String(t.costoServicio),
    costoKm: String(t.costoKm),
    vigenciaDesde: t.vigenciaDesde,
    vigenciaHasta: t.vigenciaHasta ?? "",
  };
}

/** Modal de alta/edición de tarifa, extraído de `tarifarios-config.tsx`
 * porque ese archivo ya superaba el tamaño máximo de archivo (§4). El caller
 * lo monta con una key derivada de editing/plantilla para que el estado
 * inicial del form se recalcule al cambiar de tarifa o de prefill. */
export function TarifaModal({
  isOpen, onClose, prestadores, editing, plantilla, defaultPrestadorId, onSuccess,
}: {
  isOpen: boolean; onClose: () => void; prestadores: PrestadorLiquidacion[]; editing: Tarifario | null; plantilla: PlantillaTarifa | null; defaultPrestadorId: string; onSuccess: () => void;
}) {
  const [form, setForm] = useState(() => tarifaAForm(editing, defaultPrestadorId, plantilla));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [spsts, setSpsts] = useState<Spst[]>([]);

  // SPST del prestador seleccionado — sin esto una tarifa solo puede quedar
  // genérica (spstId vacío) al no haber forma de elegir una específica.
  useEffect(() => {
    let cancelado = false;
    const cargar = form.prestadorId
      ? liquidacionesApi.listSpsts({ prestadorId: form.prestadorId, soloActivos: true })
      : Promise.resolve([]);
    void cargar.then((data) => { if (!cancelado) setSpsts(data); });
    return () => { cancelado = true; };
  }, [form.prestadorId]);

  const handleClose = () => { setForm(tarifaAForm(editing, defaultPrestadorId, plantilla)); setError(null); onClose(); };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const body = {
        prestadorId: form.prestadorId,
        tipoServicio: form.tipoServicio,
        spstId: form.spstId || undefined,
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
          <BrandSelect label="Prestador *" required value={form.prestadorId} onChange={(e) => setForm((f) => ({ ...f, prestadorId: e.target.value, spstId: "" }))}>
            <option value="">Seleccioná...</option>
            {prestadores.map((p) => <option key={p.id} value={p.id}>{p.nombreCorto} — {p.nombre}</option>)}
          </BrandSelect>
        </div>
        <BrandSelect label="Tipo de servicio *" required value={form.tipoServicio} onChange={(e) => setForm((f) => ({ ...f, tipoServicio: e.target.value }))}>
          <option value="">Seleccioná...</option>
          {TIPOS.map((t) => <option key={t} value={t}>{t}</option>)}
        </BrandSelect>
        <BrandSelect
          label="SPST (vacío = todos)"
          hint="Tarifa genérica del prestador si no elegís uno específico."
          value={form.spstId}
          onChange={(e) => setForm((f) => ({ ...f, spstId: e.target.value }))}
        >
          <option value="">Genérica</option>
          {spsts.map((s) => (
            <option key={s.id} value={s.id}>
              {s.nombre}{s.zonaCobertura ? ` — ${s.zonaCobertura}` : ""}
            </option>
          ))}
        </BrandSelect>
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
