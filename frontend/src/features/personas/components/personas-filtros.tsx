"use client";

import { BrandInput, BrandSelect } from "@/shared/components/ui/brand-form";
import type { FiltrosPersonas } from "../hooks/use-personas";

interface Props {
  filtros: FiltrosPersonas;
  onChange: (filtros: FiltrosPersonas) => void;
  sectores: [string, string][];
}

export function PersonasFiltros({ filtros, onChange, sectores }: Props) {
  const set = <K extends keyof FiltrosPersonas>(key: K, value: FiltrosPersonas[K]) =>
    onChange({ ...filtros, [key]: value });
  return (
    <div className="flex flex-wrap items-end gap-3">
      <div className="min-w-[260px] flex-1">
        <BrandInput
          label="Buscar"
          type="search"
          placeholder="Por nombre, email o cargo…"
          value={filtros.busqueda}
          onChange={(e) => set("busqueda", e.target.value)}
        />
      </div>
      <div className="min-w-[200px]">
        <BrandSelect label="Sector" value={filtros.sectorId} onChange={(e) => set("sectorId", e.target.value)}>
          <option value="">Todos los sectores</option>
          {sectores.map(([id, nombre]) => (
            <option key={id} value={id}>
              {nombre}
            </option>
          ))}
        </BrandSelect>
      </div>
      <div className="min-w-[170px]">
        <BrandSelect
          label="Entra a la app"
          value={filtros.acceso}
          onChange={(e) => set("acceso", e.target.value as FiltrosPersonas["acceso"])}
        >
          <option value="">Todas</option>
          <option value="si">Sí</option>
          <option value="no">No</option>
        </BrandSelect>
      </div>
      <div className="min-w-[150px]">
        <BrandSelect
          label="Estado"
          value={filtros.estado}
          onChange={(e) => set("estado", e.target.value as FiltrosPersonas["estado"])}
        >
          <option value="">Todas</option>
          <option value="activa">Activas</option>
          <option value="inactiva">Inactivas</option>
        </BrandSelect>
      </div>
    </div>
  );
}
