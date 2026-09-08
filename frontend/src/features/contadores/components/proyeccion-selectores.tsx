"use client";

import { BrandButton, BrandInput } from "@/shared/components/ui/brand-form";
import { SearchableSelect } from "@/shared/components/ui/searchable-select";
import type { GrupoEconomicoOption, ProcesoOption } from "../types/proyeccion";

/** Selectores de Grupo económico / Proceso / Fecha objetivo + botón Cargar —
 * extraído de `ProyeccionView` para no pasar el máximo de 300 líneas
 * (ARCHITECTURE_GUIDE.md §4). */

interface ProyeccionSelectoresProps {
  grupos: GrupoEconomicoOption[];
  procesosVisibles: ProcesoOption[];
  idGrupo: string | null;
  idProcesoValido: string | null;
  fechaObjetivo: string;
  cargando: boolean;
  onChangeGrupo: (id: string | null) => void;
  onChangeProceso: (id: string | null, proceso: ProcesoOption | undefined) => void;
  onChangeFecha: (fecha: string) => void;
  onCargar: () => void;
}

export function ProyeccionSelectores({
  grupos,
  procesosVisibles,
  idGrupo,
  idProcesoValido,
  fechaObjetivo,
  cargando,
  onChangeGrupo,
  onChangeProceso,
  onChangeFecha,
  onCargar,
}: ProyeccionSelectoresProps) {
  return (
    <div className="flex flex-wrap items-end gap-3">
      <div className="w-[260px]">
        <SearchableSelect
          label="Grupo económico"
          placeholder="Buscar grupo económico…"
          options={grupos.map((g) => ({ id: String(g.id), label: g.descripcion }))}
          value={idGrupo}
          onChange={onChangeGrupo}
        />
      </div>
      <div className="w-[280px]">
        <SearchableSelect
          label="Proceso"
          placeholder={idGrupo ? "Elegir proceso…" : "Elegí primero un grupo"}
          disabled={!idGrupo}
          options={procesosVisibles.map((p) => ({
            id: String(p.nro_proceso),
            label: `${p.periodo_facturacion} · ${p.nombre_anexo}`,
            sublabel: `Proc. ${p.nro_proceso} · cierre ${p.periodo_hasta}`,
          }))}
          value={idProcesoValido}
          onChange={(id) => {
            const proceso = procesosVisibles.find((p) => String(p.nro_proceso) === id);
            onChangeProceso(id, proceso);
          }}
        />
      </div>
      <div className="w-[160px]">
        <BrandInput
          label="Fecha objetivo"
          type="date"
          value={fechaObjetivo}
          onChange={(e) => onChangeFecha(e.target.value)}
        />
      </div>
      <BrandButton loading={cargando} onClick={onCargar}>
        Cargar
      </BrandButton>
    </div>
  );
}
