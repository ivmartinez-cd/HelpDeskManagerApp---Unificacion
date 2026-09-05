"use client";

import { useState } from "react";
import { toast } from "sonner";
import { BrandButton, BrandInput, BrandSelect } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { AcuerdoPrecioCliente, PrestadorLiquidacion } from "../types/liquidaciones";

const TIPOS = [
  "correctivo", "preventivo", "instalacion_desinstalacion",
  "pre_correctivo", "guardia", "sistemas",
];

/** Prefill al llegar desde una alerta ALT001 del detalle ("Cargar acuerdo
 * para este cliente"): cliente, tipo y el precio que el prestador cobró. */
export interface PlantillaAcuerdo {
  empresaNombre: string;
  tipoServicio: string;
  precioFijo: string;
}

type Modo = "factor" | "fijo";

function acuerdoAForm(
  a: AcuerdoPrecioCliente | null, defaultPrestadorId: string, plantilla: PlantillaAcuerdo | null,
) {
  const hoy = new Date().toISOString().split("T")[0];
  if (!a) {
    return {
      prestadorId: defaultPrestadorId,
      empresaNombre: plantilla?.empresaNombre ?? "",
      tipoServicio: plantilla?.tipoServicio ?? "",
      modo: (plantilla?.precioFijo ? "fijo" : "factor") as Modo,
      factor: "2",
      precioFijo: plantilla?.precioFijo ?? "",
      motivo: "",
      vigenciaDesde: hoy,
      vigenciaHasta: "",
    };
  }
  return {
    prestadorId: a.prestadorId,
    empresaNombre: a.empresaNombre,
    tipoServicio: a.tipoServicio ?? "",
    modo: (a.precioFijo !== null ? "fijo" : "factor") as Modo,
    factor: a.factor !== null ? String(a.factor) : "2",
    precioFijo: a.precioFijo !== null ? String(a.precioFijo) : "",
    motivo: a.motivo,
    vigenciaDesde: a.vigenciaDesde,
    vigenciaHasta: a.vigenciaHasta ?? "",
  };
}

/** Alta/edición de un acuerdo de precio por cliente. El caller lo monta con
 * una key derivada de editing/plantilla (mismo patrón que `TarifaModal`). */
export function AcuerdoModal({
  isOpen, onClose, prestadores, editing, plantilla, defaultPrestadorId, onSuccess,
}: {
  isOpen: boolean; onClose: () => void; prestadores: PrestadorLiquidacion[];
  editing: AcuerdoPrecioCliente | null; plantilla: PlantillaAcuerdo | null;
  defaultPrestadorId: string; onSuccess: () => void;
}) {
  const [form, setForm] = useState(() => acuerdoAForm(editing, defaultPrestadorId, plantilla));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleClose = () => { setError(null); onClose(); };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const body = {
        prestadorId: form.prestadorId,
        empresaNombre: form.empresaNombre.trim(),
        tipoServicio: form.tipoServicio || undefined,
        factor: form.modo === "factor" ? parseFloat(form.factor) : undefined,
        precioFijo: form.modo === "fijo" ? parseFloat(form.precioFijo) : undefined,
        motivo: form.motivo.trim(),
        vigenciaDesde: form.vigenciaDesde,
        vigenciaHasta: form.vigenciaHasta || undefined,
      };
      if (editing) {
        await liquidacionesApi.updateAcuerdo(editing.id, body);
        toast.success("Acuerdo actualizado — las liquidaciones abiertas se reanalizaron");
      } else {
        await liquidacionesApi.createAcuerdo(body);
        toast.success("Acuerdo creado — las liquidaciones abiertas se reanalizaron");
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
    <BrandModal isOpen={isOpen} onClose={handleClose} title={editing ? "Editar acuerdo" : "Nuevo acuerdo de precio"} error={error} widthPx={560}>
      <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-4">
        <div className="col-span-2">
          <BrandSelect label="Prestador *" required value={form.prestadorId} onChange={(e) => setForm((f) => ({ ...f, prestadorId: e.target.value }))}>
            <option value="">Seleccioná...</option>
            {prestadores.map((p) => <option key={p.id} value={p.id}>{p.nombreCorto} — {p.nombre}</option>)}
          </BrandSelect>
        </div>
        <div className="col-span-2">
          <BrandInput label="Cliente *" required hint="Tal como figura en los incidentes (empresa). Mayúsculas y acentos no importan." value={form.empresaNombre} onChange={(e) => setForm((f) => ({ ...f, empresaNombre: e.target.value }))} />
        </div>
        <BrandSelect label="Tipo de servicio (vacío = todos)" value={form.tipoServicio} onChange={(e) => setForm((f) => ({ ...f, tipoServicio: e.target.value }))}>
          <option value="">Todos</option>
          {TIPOS.map((t) => <option key={t} value={t}>{t}</option>)}
        </BrandSelect>
        <BrandSelect label="Cómo se calcula el precio *" value={form.modo} onChange={(e) => setForm((f) => ({ ...f, modo: e.target.value as Modo }))}>
          <option value="factor">Multiplicar el tarifario (ej. ×2 = precio doble)</option>
          <option value="fijo">Monto fijo acordado</option>
        </BrandSelect>
        {form.modo === "factor" ? (
          <BrandInput label="Factor *" type="number" step="0.01" min="0.01" required hint="2 = el doble del tarifario vigente." value={form.factor} onChange={(e) => setForm((f) => ({ ...f, factor: e.target.value }))} />
        ) : (
          <BrandInput label="Precio fijo (ARS) *" type="number" step="0.01" min="0" required value={form.precioFijo} onChange={(e) => setForm((f) => ({ ...f, precioFijo: e.target.value }))} />
        )}
        <BrandInput label="Motivo *" required hint="Quedará en cada alerta que se aparte del acuerdo." value={form.motivo} onChange={(e) => setForm((f) => ({ ...f, motivo: e.target.value }))} />
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
