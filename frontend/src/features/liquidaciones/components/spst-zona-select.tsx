"use client";

import { BrandSelect } from "@/shared/components/ui/brand-form";
import { useSpstsZonas } from "../hooks/use-spsts-zonas";

/** Selector de SPST de un prestador con la zona de Siges de cada uno. La
 * opción vacía (spstId null) es la tarifa genérica del prestador y se muestra
 * con el nombre de su zona de Siges ("Villa Mercedes / Rio IV /Sgo Estero
 * /Bs.As. — tarifa genérica") en vez de "Sin vincular": para la TL esa zona es
 * una más, no una fila sin vincular (INFOMAC, 2026-09-07). */
export function SpstZonaSelect({
  prestadorId, value, onChange, label, hint, soloActivos = true, disabled = false,
}: {
  prestadorId: string;
  value: string;
  onChange: (spstId: string) => void;
  label: string;
  hint?: string;
  soloActivos?: boolean;
  disabled?: boolean;
}) {
  const { spsts, spstsConTarifa, zonaSigesPorSpst } = useSpstsZonas(prestadorId);
  const zonaGenerica = zonaSigesPorSpst.get("");
  const labelGenerica = zonaGenerica
    ? `${zonaGenerica} — tarifa genérica`
    : spstsConTarifa.has(null)
      ? "Tarifa genérica del prestador"
      : "Sin vincular (el prestador no tiene tarifa genérica)";
  const lista = soloActivos ? spsts.filter((s) => s.activo) : spsts;
  return (
    <BrandSelect label={label} hint={hint} value={value} disabled={disabled} onChange={(e) => onChange(e.target.value)}>
      <option value="">{labelGenerica}</option>
      {lista.map((s) => {
        const zona = zonaSigesPorSpst.get(s.id) ?? s.zonaCobertura;
        return (
          <option key={s.id} value={s.id}>
            {s.nombre}{zona ? ` — ${zona}` : ""}
          </option>
        );
      })}
    </BrandSelect>
  );
}
