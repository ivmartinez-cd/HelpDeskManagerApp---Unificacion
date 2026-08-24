"use client";

import { useState } from "react";
import { toast } from "sonner";
import { BrandButton, BrandInput } from "@/shared/components/ui/brand-form";
import { liquidacionesApi } from "@/features/liquidaciones/api/liquidaciones-api";
import type { PrestadorLiquidacion } from "@/features/liquidaciones/types/liquidaciones";

export function PasoDatos({ onCreado }: { onCreado: (p: PrestadorLiquidacion) => void }) {
  const [nombre, setNombre] = useState("");
  const [nombreCorto, setNombreCorto] = useState("");
  const [cuit, setCuit] = useState("");
  const [region, setRegion] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCrear = async () => {
    setSaving(true);
    setError(null);
    try {
      const creado = await liquidacionesApi.createPrestador({
        nombre,
        nombreCorto,
        cuit: cuit || undefined,
        region: region || undefined,
      });
      toast.success("Prestador creado");
      onCreado(creado);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al crear el prestador");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <p className="font-body text-sm text-muted-foreground">
        Datos básicos en el módulo Liquidaciones. Los siguientes pasos vinculan
        este mismo prestador a Siges, Canal Directo y al módulo de asignación SLA
        — todos opcionales, se pueden completar después desde la fila del
        prestador.
      </p>
      <BrandInput label="Nombre completo *" required value={nombre} onChange={(e) => setNombre(e.target.value)} />
      <BrandInput
        label="Clave *"
        required
        value={nombreCorto}
        placeholder="PENTACOM"
        onChange={(e) => setNombreCorto(e.target.value)}
      />
      <BrandInput label="CUIT" value={cuit} placeholder="30712345678" onChange={(e) => setCuit(e.target.value)} />
      <BrandInput
        label="Región / Plaza"
        value={region}
        placeholder="Córdoba, Rosario..."
        onChange={(e) => setRegion(e.target.value)}
      />
      {error && <p className="font-body text-sm text-destructive">{error}</p>}
      <div className="flex justify-end pt-1">
        <BrandButton type="button" loading={saving} disabled={!nombre || !nombreCorto} onClick={handleCrear}>
          Crear y continuar →
        </BrandButton>
      </div>
    </div>
  );
}
