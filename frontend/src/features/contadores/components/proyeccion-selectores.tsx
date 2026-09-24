"use client";

import { BrandButton, BrandInput } from "@/shared/components/ui/brand-form";
import { SearchableSelect } from "@/shared/components/ui/searchable-select";
import type { GrupoEconomicoOption, ProcesoOption } from "../types/proyeccion";
import { fechaLarga } from "./proyeccion-formato";

/** Selectores de Grupo económico / Proceso / Fecha objetivo + Cargar, y el
 * resumen del proceso elegido (`Index.razor` v1.7). Sin proceso, "Cargar"
 * muestra el tablero de ejemplo (solo HDM). */

interface ProyeccionSelectoresProps {
  grupos: GrupoEconomicoOption[];
  procesosVisibles: ProcesoOption[];
  idGrupo: string | null;
  idProcesoValido: string | null;
  procesoElegido: ProcesoOption | undefined;
  fechaObjetivo: string;
  cargando: boolean;
  onChangeGrupo: (id: string | null) => void;
  onChangeProceso: (id: string | null, proceso: ProcesoOption | undefined) => void;
  onChangeFecha: (fecha: string) => void;
  onCargar: () => void;
}

export function ProyeccionSelectores(props: ProyeccionSelectoresProps) {
  const { grupos, procesosVisibles, idGrupo, idProcesoValido, procesoElegido, fechaObjetivo, cargando } = props;
  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-end gap-3">
        <div className="w-[260px]">
          <SearchableSelect
            label="Grupo económico"
            placeholder="Buscar grupo económico…"
            options={grupos.map((g) => ({ id: String(g.id), label: g.descripcion }))}
            value={idGrupo}
            onChange={props.onChangeGrupo}
          />
        </div>
        <div className="w-[320px]">
          <SearchableSelect
            label="Proceso"
            placeholder={idGrupo ? "Elegir proceso…" : "Elegí primero un grupo"}
            disabled={!idGrupo}
            options={procesosVisibles.map((p) => ({
              id: String(p.nro_proceso),
              label: `${p.periodo_facturacion} – ${p.nombre_anexo} – Proc. ${p.nro_proceso}`,
              sublabel: `cierre ${fechaLarga(p.periodo_hasta)}`,
            }))}
            value={idProcesoValido}
            onChange={(id) => props.onChangeProceso(id, procesosVisibles.find((p) => String(p.nro_proceso) === id))}
          />
        </div>
        <div className="w-[170px]">
          <BrandInput
            label="Fecha objetivo (editable)"
            type="date"
            value={fechaObjetivo}
            onChange={(e) => props.onChangeFecha(e.target.value)}
          />
        </div>
        <BrandButton loading={cargando} disabled={cargando} onClick={props.onCargar} title="Cargar / recargar grilla">
          Cargar
        </BrandButton>
      </div>
      {procesoElegido && (
        <ResumenProceso grupo={grupos.find((g) => String(g.id) === idGrupo)} proceso={procesoElegido} fecha={fechaObjetivo} />
      )}
    </div>
  );
}

function ResumenProceso({ grupo, proceso, fecha }: { grupo?: GrupoEconomicoOption; proceso: ProcesoOption; fecha: string }) {
  const modificada = fecha !== proceso.periodo_hasta;
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-[8px] bg-info/10 px-4 py-2 font-body text-xs text-foreground">
      <span>
        <strong>Grupo:</strong> {grupo?.descripcion ?? "—"}
      </span>
      <span className="text-muted-foreground">|</span>
      <span>
        <strong>Proceso:</strong> {proceso.nro_proceso} · {proceso.periodo_facturacion} · {proceso.nombre_anexo}
      </span>
      <span className="text-muted-foreground">|</span>
      <span>
        <strong>Fecha objetivo:</strong> {fechaLarga(fecha)}
      </span>
      {modificada && (
        <span className="rounded-full bg-warning/20 px-2 py-0.5 font-semibold text-warning">
          Modificada (original: {fechaLarga(proceso.periodo_hasta)})
        </span>
      )}
    </div>
  );
}
