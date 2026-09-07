"use client";

import { useState } from "react";
import { toast } from "sonner";
import { BrandButton, BrandInput } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { liquidacionesApi } from "../api/liquidaciones-api";
import { labelTipo, type VigenciaZona } from "../lib/tarifarios-matriz";

/** Nueva vigencia de una zona completa (todos los tipos de servicio de una
 * vez), como una fila de `dbo.CostoServicio`. Precarga los valores de la
 * vigencia vigente; cada tipo con importe crea una tarifa y el backend
 * recadena el grupo (cierra la vigencia anterior). Un tipo en blanco no se
 * carga. */
export function VigenciaZonaModal({
  prestadorId, spstId, zonaLabel, tipos, base, onClose, onSuccess,
}: {
  prestadorId: string;
  spstId: string | null;
  zonaLabel: string;
  tipos: string[];
  base: VigenciaZona | null;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const hoy = new Date().toISOString().split("T")[0];
  const [costos, setCostos] = useState<Record<string, string>>(() =>
    Object.fromEntries(tipos.map((t) => [t, base?.porTipo[t] ? String(base.porTipo[t].costoServicio) : ""])),
  );
  const [costoKm, setCostoKm] = useState(base ? String(base.costoKm) : "");
  const [desde, setDesde] = useState(hoy);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const aCrear = tipos.filter((t) => costos[t].trim() !== "");
    if (aCrear.length === 0) { setError("Cargá al menos un tipo de servicio."); return; }
    setLoading(true);
    setError(null);
    let creados = 0;
    try {
      for (const tipo of aCrear) {
        await liquidacionesApi.createTarifario({
          prestadorId,
          tipoServicio: tipo,
          spstId: spstId ?? undefined,
          costoServicio: parseFloat(costos[tipo]),
          costoKm: parseFloat(costoKm),
          vigenciaDesde: desde,
        });
        creados += 1;
      }
      toast.success(`Vigencia cargada: ${creados} tarifas desde ${desde}`);
      onSuccess();
      onClose();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al guardar";
      setError(`${msg} (se crearon ${creados} de ${aCrear.length} tarifas; las creadas quedaron cargadas)`);
      if (creados > 0) onSuccess();
    } finally {
      setLoading(false);
    }
  };

  return (
    <BrandModal isOpen onClose={onClose} title={`Nueva vigencia — ${zonaLabel}`}>
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-3">
          <BrandInput label="Vigente desde *" type="date" required value={desde} onChange={(e) => setDesde(e.target.value)} />
          <BrandInput label="Costo por km *" type="number" step="0.01" min="0" required value={costoKm} onChange={(e) => setCostoKm(e.target.value)} />
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {tipos.map((tipo) => (
            <BrandInput
              key={tipo}
              label={labelTipo(tipo)}
              type="number"
              step="0.01"
              min="0"
              value={costos[tipo]}
              onChange={(e) => setCostos((c) => ({ ...c, [tipo]: e.target.value }))}
            />
          ))}
        </div>
        <p className="font-body text-xs text-muted-foreground">
          Cada tipo con importe crea una tarifa nueva y cierra la anterior de esa zona. Un tipo en blanco no se toca.
        </p>
        {error && <p className="font-body text-sm text-destructive">{error}</p>}
        <div className="flex justify-end gap-3">
          <BrandButton type="button" variant="outline" onClick={onClose} disabled={loading}>Cancelar</BrandButton>
          <BrandButton type="submit" disabled={loading}>{loading ? "Guardando..." : "Guardar vigencia"}</BrandButton>
        </div>
      </form>
    </BrandModal>
  );
}
