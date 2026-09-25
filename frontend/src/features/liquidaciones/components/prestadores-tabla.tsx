"use client";

import { Badge } from "@/shared/components/ui/badge";
import { SortableHeader, type SortableColumn } from "@/shared/components/ui/sortable-header";
import { boolSortValue, useOptionalTableSort, useSortedRows } from "@/shared/hooks/use-optional-table-sort";
import type { PrestadorLiquidacion } from "../types/liquidaciones";

/** Tabla del catálogo de prestadores, extraída de `prestadores-config.tsx`
 * (tamaño máximo de archivo, §4). Arranca en el orden del backend y ordena
 * por cualquier encabezado salvo Acciones. */

const thCls = "py-3 px-4 font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground text-left";
const tdCls = "py-3 px-4 font-body text-sm text-foreground";

type SortKey = "clave" | "nombre" | "cuit" | "region" | "vinculo" | "canalDirecto" | "estado";

const COLUMNAS: SortableColumn<SortKey>[] = [
  { key: "clave", label: "Clave" },
  { key: "nombre", label: "Nombre" },
  { key: "cuit", label: "CUIT" },
  {
    key: "region",
    label: "Región",
    title: "Solo informativa — no la usa ningún cálculo (distinto de la 'Zona de cobertura' del SPST, que tampoco define precios desde el refactor a SPST)",
  },
  { key: "vinculo", label: "Vínculo" },
  { key: "canalDirecto", label: "Canal Directo" },
  { key: "estado", label: "Estado" },
];

/** Estado: el primer clic pone los activos arriba. */
const DESC_PRIMERO: readonly SortKey[] = ["estado"];

function valorOrden(p: PrestadorLiquidacion, key: SortKey) {
  switch (key) {
    case "clave": return p.nombreCorto;
    case "nombre": return p.nombre;
    case "cuit": return p.cuit;
    case "region": return p.region;
    case "vinculo": return p.sigesEmpresaId;
    case "canalDirecto": return p.cdPrestadorId;
    case "estado": return boolSortValue(p.activo);
  }
}

export interface PrestadorAcciones {
  onEditar: (p: PrestadorLiquidacion) => void;
  onCd: (p: PrestadorLiquidacion) => void;
  onBase: (p: PrestadorLiquidacion) => void;
  onSla: (p: PrestadorLiquidacion) => void;
  onToggle: (p: PrestadorLiquidacion) => void;
  onEliminar: (id: string) => void;
}

function BadgeVinculo({ id }: { id: number | null }) {
  return id != null ? <Badge variant="success">#{id}</Badge> : <Badge variant="neutral">Sin vínculo</Badge>;
}

function CeldaAcciones({ p, sigesConAltaSla, acciones }: {
  p: PrestadorLiquidacion;
  sigesConAltaSla: Set<number> | null;
  acciones: PrestadorAcciones;
}) {
  return (
    <>
      <button onClick={() => acciones.onEditar(p)} className="font-body text-sm text-brand-orange hover:underline mr-3">Editar</button>
      <button onClick={() => acciones.onCd(p)} className="font-body text-sm text-brand-orange hover:underline mr-3">
        {p.cdPrestadorId != null ? "CD" : "Vincular CD"}
      </button>
      {p.sigesEmpresaId != null && (
        <button onClick={() => acciones.onBase(p)} className="font-body text-sm text-brand-orange hover:underline mr-3">
          {p.sigesBaseSucursalId != null ? "Distancias" : "Base"}
        </button>
      )}
      {p.sigesEmpresaId != null
        && sigesConAltaSla !== null
        && !sigesConAltaSla.has(p.sigesEmpresaId) && (
        <button
          onClick={() => acciones.onSla(p)}
          className="font-body text-sm text-warning hover:underline mr-3"
          title="El asistente de alta se salteó (o nunca tuvo) el paso del módulo SLA — completalo acá"
        >
          Completar alta SLA
        </button>
      )}
      <button onClick={() => acciones.onToggle(p)} className={`font-body text-sm hover:underline mr-3 ${p.activo ? "text-destructive" : "text-success"}`}>
        {p.activo ? "Desactivar" : "Activar"}
      </button>
      <button onClick={() => acciones.onEliminar(p.id)} className="font-body text-sm text-destructive hover:underline">Eliminar</button>
    </>
  );
}

export function PrestadoresTabla({ prestadores, puedeEditar, sigesConAltaSla, acciones }: {
  prestadores: PrestadorLiquidacion[];
  puedeEditar: boolean;
  /** Ver `PrestadoresConfig`: `null` = no se pudo consultar el módulo SLA. */
  sigesConAltaSla: Set<number> | null;
  acciones: PrestadorAcciones;
}) {
  const { sort, toggleSort } = useOptionalTableSort(DESC_PRIMERO);
  const filas = useSortedRows(prestadores, sort, valorOrden);
  return (
    <div className="overflow-hidden rounded-[12px] border border-border bg-card">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-muted/40">
              {COLUMNAS.map((c) => (
                <SortableHeader key={c.key} column={c} sort={sort} onToggleSort={toggleSort} thClassName={thCls} />
              ))}
              <th className={`${thCls} text-right`}>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {filas.map((p) => (
              <tr key={p.id} className="border-t border-border transition-colors hover:bg-muted/30">
                <td className={tdCls}><span className="font-heading text-sm font-bold uppercase text-foreground">{p.nombreCorto}</span></td>
                <td className={tdCls}>{p.nombre}</td>
                <td className={`${tdCls} text-muted-foreground`}>{p.cuit || "—"}</td>
                <td className={`${tdCls} text-muted-foreground`}>{p.region?.toUpperCase() || "—"}</td>
                <td className={tdCls}><BadgeVinculo id={p.sigesEmpresaId} /></td>
                <td className={tdCls}><BadgeVinculo id={p.cdPrestadorId} /></td>
                <td className={tdCls}>
                  <Badge variant={p.activo ? "success" : "neutral"}>{p.activo ? "Activo" : "Inactivo"}</Badge>
                </td>
                <td className={`${tdCls} text-right`}>
                  {puedeEditar && <CeldaAcciones p={p} sigesConAltaSla={sigesConAltaSla} acciones={acciones} />}
                </td>
              </tr>
            ))}
            {prestadores.length === 0 && (
              <tr><td colSpan={8} className="py-10 text-center font-body text-sm text-muted-foreground">No hay prestadores cargados.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
