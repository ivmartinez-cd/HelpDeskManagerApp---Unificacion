"use client";

import Link from "next/link";
import { Download } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { KpiGrid, KpiTile } from "@/shared/components/ui/kpi-tile";
import { SegmentedControl } from "@/shared/components/ui/segmented-control";
import { SearchableSelect } from "@/shared/components/ui/searchable-select";
import { BrandButton, brandButtonClasses } from "@/shared/components/ui/brand-form";
import { SortableHeader } from "@/shared/components/ui/sortable-header";
import { compareSortValues, useTableSort, type SortValue } from "@/shared/hooks/use-table-sort";
import { cn } from "@/shared/utils/cn";
import { proyeccionApi } from "../api/proyeccion-api";
import { detalleContadorProcesoApi, type AlcanceReporte } from "../api/detalle-contador-proceso-api";
import type { GrupoEconomicoOption, ProcesoOption } from "../types/proyeccion";
import type { DetalleContadorProceso, DetalleContadorRow } from "../types/detalle-contador-proceso";

const ALCANCES: { value: AlcanceReporte; label: string }[] = [
  { value: "todos", label: "Todo el proceso" },
  { value: "falta_contador", label: "Solo Falta Contador" },
];

type SortKey =
  | "empresa"
  | "sucursal"
  | "modelo"
  | "serie"
  | "sector"
  | "fecha_toma_anterior"
  | "contador_anterior"
  | "fecha_toma_actual"
  | "contador_actual"
  | "impresiones_reales"
  | "tipo"
  | "nombre_clase"
  | "estado_maquina"
  | "direccion_ip"
  | "mascara_ip";

const SORT_KEYS: readonly SortKey[] = [
  "empresa",
  "sucursal",
  "modelo",
  "serie",
  "sector",
  "fecha_toma_anterior",
  "contador_anterior",
  "fecha_toma_actual",
  "contador_actual",
  "impresiones_reales",
  "tipo",
  "nombre_clase",
  "estado_maquina",
  "direccion_ip",
  "mascara_ip",
];

/** Ancho de cada columna en % — `table-layout: fixed` (pedido explícito:
 * "que entre en el viewport sin generar scrollbar y se acomode según la
 * resolución de cada monitor"). Suman 100%, así el ancho real de cada
 * columna escala con el monitor en vez de un `min-width` fijo que
 * disparaba scroll horizontal en pantallas angostas. El contenido más
 * largo que su columna se trunca con "…" (`title` muestra el valor
 * completo al pasar el mouse). */
const ANCHOS_COL = [
  8, // Empresa
  9.4, // Sucursal
  9.4, // Modelo
  7.2, // Serie
  8, // Sector
  5.8, // Toma Ant.
  5.4, // Cont. Ant.
  5.8, // Toma Act.
  5.4, // Cont. Act.
  5.4, // Impr.
  8, // Tipo
  4, // Clase
  7.2, // Estado
  5.4, // Dir. IP
  5.4, // Másc. IP
] as const;

const numberFormat = new Intl.NumberFormat("es-AR");

function formatFecha(iso: string | null): string {
  if (!iso) return "—";
  const [y, m, d] = iso.split("-");
  return `${d}/${m}/${y}`;
}

function valorOrdenable(fila: DetalleContadorRow, key: SortKey): SortValue {
  return fila[key];
}

/** Reporte "Detalle de contadores por nro de proceso" — reconstrucción del
 * reporte legacy SSRS (`reportes.cdsa.com.ar:8090`), con el mismo circuito
 * de selección Grupo económico → Proceso que ya usa Proyección/Estimador
 * (misma noción de "cliente" del resto del módulo). Toda columna es
 * ordenable (pedido del usuario: "toda tabla se tiene que poder filtrar
 * por la columna" — acá se resolvió como orden ascendente/descendente al
 * click del título, mismo patrón que `proyeccion-tabla.tsx`). */
export function DetalleContadorProcesoView() {
  const [grupos, setGrupos] = useState<GrupoEconomicoOption[]>([]);
  const [procesos, setProcesos] = useState<ProcesoOption[]>([]);
  const [idGrupo, setIdGrupo] = useState<string | null>(null);
  const [idProceso, setIdProceso] = useState<string | null>(null);
  const [alcance, setAlcance] = useState<AlcanceReporte>("falta_contador");

  const [detalle, setDetalle] = useState<DetalleContadorProceso | null>(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { sort, toggleSort } = useTableSort<SortKey>({
    initial: { key: "empresa", direction: "asc" },
    keys: SORT_KEYS,
  });

  useEffect(() => {
    void proyeccionApi.listGruposEconomicos().then(setGrupos);
  }, []);

  useEffect(() => {
    if (idGrupo == null) return;
    void proyeccionApi.listProcesos(Number(idGrupo)).then(setProcesos);
  }, [idGrupo]);

  const procesosVisibles = idGrupo == null ? [] : procesos;
  const idProcesoValido = procesosVisibles.some((p) => String(p.nro_proceso) === idProceso)
    ? idProceso
    : null;

  const cargar = () => {
    if (!idProcesoValido) return;
    setCargando(true);
    setError(null);
    setDetalle(null);
    detalleContadorProcesoApi
      .getDetalle(Number(idProcesoValido))
      .then(setDetalle)
      .catch((err: unknown) =>
        setError(err instanceof Error ? err.message : "No se pudo cargar el proceso."),
      )
      .finally(() => setCargando(false));
  };

  const filasVisibles = useMemo(() => {
    if (!detalle) return [];
    const filtradas =
      alcance === "todos" ? detalle.filas : detalle.filas.filter((f) => f.falta_contador);
    return [...filtradas].sort((a, b) =>
      compareSortValues(valorOrdenable(a, sort.key), valorOrdenable(b, sort.key), sort.direction),
    );
  }, [detalle, alcance, sort]);

  const faltantes = detalle ? detalle.filas.filter((f) => f.falta_contador).length : 0;

  return (
    <div className="flex flex-col gap-6 px-9 py-8">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link href="/contadores" className="hover:text-foreground">
          Centro de Contadores
        </Link>
        <span>›</span>
        <span className="font-semibold text-foreground">Detalle por Proceso</span>
      </div>

      <div className="flex flex-col gap-1.5">
        <h1 className="font-heading text-[25px] font-extrabold uppercase tracking-[-.03em] text-foreground">
          Detalle de contadores por proceso
        </h1>
        <p className="font-body text-sm text-muted-foreground">
          Reconstrucción del reporte &ldquo;Detalle de contadores por nro de proceso&rdquo; — elegí
          el proceso y mostrá todo el parque o solo los equipos con falta de contador.
        </p>
      </div>

      <div className="flex flex-wrap items-end gap-3">
        <div className="w-[260px]">
          <SearchableSelect
            label="Cliente (grupo económico)"
            placeholder="Buscar cliente…"
            options={grupos.map((g) => ({ id: String(g.id), label: g.descripcion }))}
            value={idGrupo}
            onChange={(id) => {
              setIdGrupo(id);
              setIdProceso(null);
              setDetalle(null);
            }}
          />
        </div>
        <div className="w-[280px]">
          <SearchableSelect
            label="Proceso"
            placeholder={idGrupo ? "Elegir proceso…" : "Elegí primero un cliente"}
            disabled={!idGrupo}
            options={procesosVisibles.map((p) => ({
              id: String(p.nro_proceso),
              label: `${p.periodo_facturacion} · ${p.nombre_anexo}`,
              sublabel: `Proc. ${p.nro_proceso} · cierre ${p.periodo_hasta}`,
            }))}
            value={idProcesoValido}
            onChange={setIdProceso}
          />
        </div>
        <BrandButton loading={cargando} disabled={!idProcesoValido} onClick={cargar}>
          Cargar
        </BrandButton>
      </div>

      {error && (
        <p className="rounded-[8px] bg-destructive/10 px-4 py-3 font-body text-xs text-destructive">
          {error}
        </p>
      )}

      {detalle && (
        <>
          <KpiGrid className="sm:grid-cols-3">
            <KpiTile label="Cliente" value={detalle.cliente} />
            <KpiTile label="Falta contador" value={String(faltantes)} tone="danger" />
            <KpiTile label="Total equipos" value={String(detalle.filas.length)} />
          </KpiGrid>

          <div className="flex flex-wrap items-end justify-between gap-3">
            <SegmentedControl
              label="Alcance"
              options={ALCANCES.map((a) => ({
                value: a.value,
                label:
                  a.value === "todos"
                    ? `${a.label} (${detalle.filas.length})`
                    : `${a.label} (${faltantes})`,
              }))}
              value={alcance}
              onChange={(v) => setAlcance(v as AlcanceReporte)}
            />
            <a
              href={detalleContadorProcesoApi.getXlsxUrl(Number(idProcesoValido), alcance)}
              className={brandButtonClasses({ variant: "outline" })}
              title="Descarga el mismo listado de abajo en un Excel, listo para mandarle al cliente"
            >
              <Download className="h-4 w-4" />
              Descargar XLSX
            </a>
          </div>

          <div className="overflow-hidden rounded-[12px] border border-border bg-card">
            <table className="w-full table-fixed text-left text-sm">
              <colgroup>
                {ANCHOS_COL.map((ancho, i) => (
                  <col key={i} style={{ width: `${ancho}%` }} />
                ))}
              </colgroup>
              <thead>
                <tr className="border-b border-border font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
                  <SortableHeader column={{ key: "empresa", label: "Empresa" }} sort={sort} onToggleSort={toggleSort} thClassName="truncate px-2.5 py-2.5" />
                  <SortableHeader column={{ key: "sucursal", label: "Sucursal" }} sort={sort} onToggleSort={toggleSort} thClassName="truncate px-2.5 py-2.5" />
                  <SortableHeader column={{ key: "modelo", label: "Modelo" }} sort={sort} onToggleSort={toggleSort} thClassName="truncate px-2.5 py-2.5" />
                  <SortableHeader column={{ key: "serie", label: "Serie" }} sort={sort} onToggleSort={toggleSort} thClassName="truncate px-2.5 py-2.5" />
                  <SortableHeader column={{ key: "sector", label: "Sector" }} sort={sort} onToggleSort={toggleSort} thClassName="truncate px-2.5 py-2.5" />
                  <SortableHeader column={{ key: "fecha_toma_anterior", label: "Toma Ant." }} sort={sort} onToggleSort={toggleSort} thClassName="truncate px-2.5 py-2.5" />
                  <SortableHeader column={{ key: "contador_anterior", label: "Cont. Ant." }} sort={sort} onToggleSort={toggleSort} thClassName="truncate px-2.5 py-2.5 text-right" />
                  <SortableHeader column={{ key: "fecha_toma_actual", label: "Toma Act." }} sort={sort} onToggleSort={toggleSort} thClassName="truncate px-2.5 py-2.5" />
                  <SortableHeader column={{ key: "contador_actual", label: "Cont. Act." }} sort={sort} onToggleSort={toggleSort} thClassName="truncate px-2.5 py-2.5 text-right" />
                  <SortableHeader column={{ key: "impresiones_reales", label: "Impr." }} sort={sort} onToggleSort={toggleSort} thClassName="truncate px-2.5 py-2.5 text-right" />
                  <SortableHeader column={{ key: "tipo", label: "Tipo" }} sort={sort} onToggleSort={toggleSort} thClassName="truncate px-2.5 py-2.5" />
                  <SortableHeader column={{ key: "nombre_clase", label: "Clase" }} sort={sort} onToggleSort={toggleSort} thClassName="truncate px-2.5 py-2.5" />
                  <SortableHeader column={{ key: "estado_maquina", label: "Estado" }} sort={sort} onToggleSort={toggleSort} thClassName="truncate px-2.5 py-2.5" />
                  <SortableHeader column={{ key: "direccion_ip", label: "Dir. IP" }} sort={sort} onToggleSort={toggleSort} thClassName="truncate px-2.5 py-2.5" />
                  <SortableHeader column={{ key: "mascara_ip", label: "Másc. IP" }} sort={sort} onToggleSort={toggleSort} thClassName="truncate px-2.5 py-2.5" />
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filasVisibles.length === 0 ? (
                  <tr>
                    <td colSpan={15} className="px-2.5 py-6 text-center text-muted-foreground">
                      Sin filas para este alcance.
                    </td>
                  </tr>
                ) : (
                  filasVisibles.map((fila, i) => (
                    <tr key={`${fila.serie}-${fila.nombre_clase}-${i}`} className="hover:bg-muted/30">
                      <td className="truncate px-2.5 py-2" title={fila.empresa}>
                        {fila.empresa}
                      </td>
                      <td className="truncate px-2.5 py-2" title={fila.sucursal}>
                        {fila.sucursal}
                      </td>
                      <td className="truncate px-2.5 py-2" title={fila.modelo}>
                        {fila.modelo}
                      </td>
                      <td className="truncate px-2.5 py-2 font-mono text-xs" title={fila.serie}>
                        {fila.serie}
                      </td>
                      <td className="truncate px-2.5 py-2" title={fila.sector ?? undefined}>
                        {fila.sector ?? "—"}
                      </td>
                      <td className="truncate px-2.5 py-2">{formatFecha(fila.fecha_toma_anterior)}</td>
                      <td className="truncate px-2.5 py-2 text-right tabular-nums">
                        {numberFormat.format(fila.contador_anterior)}
                      </td>
                      <td className="truncate px-2.5 py-2">{formatFecha(fila.fecha_toma_actual)}</td>
                      <td className="truncate px-2.5 py-2 text-right tabular-nums">
                        {numberFormat.format(fila.contador_actual)}
                      </td>
                      <td className="truncate px-2.5 py-2 text-right tabular-nums">
                        {numberFormat.format(fila.impresiones_reales)}
                      </td>
                      <td
                        className={cn(
                          "truncate px-2.5 py-2",
                          fila.falta_contador && "font-bold text-destructive",
                        )}
                        title={fila.tipo ?? undefined}
                      >
                        {fila.tipo ?? "—"}
                      </td>
                      <td className="truncate px-2.5 py-2">{fila.nombre_clase ?? "—"}</td>
                      <td className="truncate px-2.5 py-2" title={fila.estado_maquina ?? undefined}>
                        {fila.estado_maquina ?? "—"}
                      </td>
                      <td className="truncate px-2.5 py-2" title={fila.direccion_ip ?? undefined}>
                        {fila.direccion_ip ?? "—"}
                      </td>
                      <td className="truncate px-2.5 py-2" title={fila.mascara_ip ?? undefined}>
                        {fila.mascara_ip ?? "—"}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </>
      )}

      {!detalle && !cargando && (
        <p className="text-sm text-muted-foreground">
          Elegí un cliente y un proceso, y apretá Cargar.
        </p>
      )}
    </div>
  );
}
