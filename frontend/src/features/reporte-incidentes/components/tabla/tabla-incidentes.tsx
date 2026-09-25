"use client";

import { ChevronsDownUp, ChevronsUpDown, Search } from "lucide-react";
import type { CampoOrden } from "../../types/reporte";
import type { EstadoDashboard } from "../../hooks/use-reporte";
import { TAMANO_PAGINA, useTablaIncidentes, type EstadoTabla } from "../../hooks/use-tabla-incidentes";
import { Button } from "@/shared/components/ui/button";
import { PaginationBar } from "@/shared/components/ui/pagination-bar";
import { SortableHeader, type SortableColumn } from "@/shared/components/ui/sortable-header";
import { cn } from "@/shared/utils/cn";
import { CANTIDAD_COLUMNAS, FilaIncidente } from "./fila-incidente";
import { CLASE_BOTON, CLASE_CONTROL } from "./estilos";

const COLUMNAS: SortableColumn<CampoOrden>[] = [
  { key: "numero", label: "Número", className: "w-[104px]" },
  { key: "fecha", label: "Fecha", className: "w-[100px]" },
  { key: "sucursal", label: "Sucursal", className: "w-[130px]" },
  { key: "descripcion", label: "Reporte del cliente" },
  { key: "causa", label: "Causa", className: "w-[150px]" },
  { key: "solucion", label: "Solución (técnico)" },
  { key: "categoria", label: "Tipificación", className: "w-[220px]", title: "Ordena por categoría" },
];

const TH =
  "border-b border-border px-3 py-3 text-left font-body text-[11px] font-bold uppercase tracking-[.05em] text-muted-foreground";

function subtitulo(tabla: EstadoTabla, estado: EstadoDashboard): string {
  const partes = [`${tabla.total.toLocaleString("es-AR")} incidentes`];
  if (estado.reporte?.filtros_activos) partes.push("filtrados");
  if (tabla.buscando) partes.push("con búsqueda");
  return partes.join(" · ");
}

function Encabezado({ tabla, estado }: { tabla: EstadoTabla; estado: EstadoDashboard }) {
  const Icono = tabla.todasExpandidas ? ChevronsDownUp : ChevronsUpDown;
  return (
    <header className="flex flex-wrap items-center justify-between gap-4 border-b border-border px-6 py-4">
      <div>
        <h2 className="font-heading text-base font-bold text-foreground">Detalle de incidentes</h2>
        <p className="mt-0.5 font-body text-[13px] text-muted-foreground">{subtitulo(tabla, estado)}</p>
      </div>
      <div className="flex w-full flex-wrap items-center gap-2.5 sm:w-auto">
        <div className="relative flex w-full sm:w-[280px]">
          <Search
            className="pointer-events-none absolute top-1/2 left-2.5 h-4 w-4 -translate-y-1/2 text-muted-foreground"
            aria-hidden="true"
          />
          <input
            type="search"
            aria-label="Buscar en la tabla"
            placeholder="Buscar en la tabla…"
            value={tabla.texto}
            onChange={(e) => tabla.setTexto(e.target.value)}
            className={cn(CLASE_CONTROL, "pl-[34px]")}
          />
        </div>
        <Button
          variant="outline"
          size="sm"
          className={CLASE_BOTON}
          disabled={tabla.filas.length === 0}
          onClick={tabla.alternarTodas}
        >
          <Icono className="h-3.5 w-3.5" aria-hidden="true" />
          {tabla.todasExpandidas ? "Colapsar todos" : "Expandir todos"}
        </Button>
      </div>
    </header>
  );
}

function Cuerpo({ tabla, estado }: { tabla: EstadoTabla; estado: EstadoDashboard }) {
  if (tabla.filas.length === 0) {
    const texto = tabla.cargando
      ? "Cargando incidentes…"
      : tabla.buscando
        ? "Sin incidentes que coincidan con la búsqueda."
        : "Sin incidentes para los filtros actuales.";
    return (
      <tbody>
        <tr>
          <td colSpan={CANTIDAD_COLUMNAS} className="px-6 py-8 text-center font-body text-sm text-muted-foreground">
            {texto}
          </td>
        </tr>
      </tbody>
    );
  }
  return (
    <tbody>
      {tabla.filas.map((incidente) => (
        <FilaIncidente
          key={incidente.id}
          incidente={incidente}
          estado={estado}
          expandida={tabla.expandidas.has(incidente.id)}
          onAlternar={() => tabla.alternarFila(incidente.id)}
        />
      ))}
    </tbody>
  );
}

/** Card "Detalle de incidentes" (port de `IncidentsTable`): búsqueda, orden y
 * paginación de a 50 van al backend, sobre la selección filtrada. */
export function TablaIncidentes({ estado }: { estado: EstadoDashboard }) {
  const tabla = useTablaIncidentes(estado);
  return (
    <section className="overflow-hidden rounded-[12px] border border-border bg-card" aria-busy={tabla.cargando}>
      <Encabezado tabla={tabla} estado={estado} />
      {tabla.error && (
        <p role="alert" className="border-b border-border px-6 py-3 font-body text-sm text-destructive">
          {tabla.error}
        </p>
      )}
      <div className={cn("overflow-x-auto transition-opacity", tabla.cargando && tabla.filas.length > 0 && "opacity-60")}>
        <table className="w-full min-w-[960px] table-fixed border-collapse">
          <thead>
            <tr>
              <th scope="col" className={cn(TH, "w-10")}>
                <span className="sr-only">Expandir</span>
              </th>
              {COLUMNAS.map((columna) => (
                <SortableHeader
                  key={columna.key}
                  column={columna}
                  sort={tabla.sort}
                  onToggleSort={tabla.alternarOrden}
                  thClassName={TH}
                />
              ))}
            </tr>
          </thead>
          <Cuerpo tabla={tabla} estado={estado} />
        </table>
      </div>
      {tabla.total > 0 && (
        <PaginationBar
          page={tabla.page}
          total={tabla.total}
          size={TAMANO_PAGINA}
          onPageChange={tabla.setPage}
          noun="incidentes"
          className="border-t border-border px-4 py-3"
        />
      )}
    </section>
  );
}
