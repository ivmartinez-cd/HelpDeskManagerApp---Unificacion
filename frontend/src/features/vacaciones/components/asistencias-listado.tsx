"use client";

import { useMemo, useState } from "react";
import { Search, ShieldAlert } from "lucide-react";
import { ApiError } from "@/services/http-client";
import { BrandEmptyState, BrandInput, BrandSelect } from "@/shared/components/ui/brand-form";
import { PaginationBar } from "@/shared/components/ui/pagination-bar";
import { SortableHeader } from "@/shared/components/ui/sortable-header";
import { compareSortValues, useTableSort } from "@/shared/hooks/use-table-sort";
import { asistenciasApi } from "../api/asistencias-api";
import { formatFecha, iniciales } from "../lib/fechas";
import { TIPO_AUSENCIA, horarioTexto } from "../lib/tipos-ausencia";
import type { Ausencia, TipoAusencia } from "../types/vacaciones";
import { SolicitudEstadoBadge } from "./solicitud-estado-badge";

const PAGE_SIZE = 25;

/** `daysCount` incluye la extensión LCT del backend (fin viernes +2, sábado +1)
 * salvo para HOME_OFFICE/CAMBIO_HORARIO; se avisa para que 2 días jue–vie
 * mostrados como 4 no desconcierten. */
function incluyeFinDeSemana(a: Ausencia): boolean {
  if (a.tipo === "HOME_OFFICE" || a.tipo === "CAMBIO_HORARIO") return false;
  const [y, m, d] = a.endDate.split("-").map(Number);
  const diaSemana = new Date(y, m - 1, d).getDay(); // 0=dom ... 6=sáb
  return diaSemana === 5 || diaSemana === 6;
}

function duracionTexto(a: Ausencia): string {
  const dias = `${a.daysCount} día${a.daysCount === 1 ? "" : "s"}`;
  const horario = horarioTexto(a);
  if (horario) return `${horario} · ${dias}`;
  if (a.halfDay) return "Medio día";
  return incluyeFinDeSemana(a) ? `${dias} (incluye fin de semana)` : dias;
}

type AusenciaSortKey = "empleado" | "fecha" | "tipo" | "duracion";
const AUSENCIA_SORT_KEYS: readonly AusenciaSortKey[] = ["empleado", "fecha", "tipo", "duracion"];

function ausenciaSortValue(a: Ausencia, key: AusenciaSortKey) {
  switch (key) {
    case "empleado": return a.empleadoNombre;
    case "fecha": return a.startDate;
    case "tipo": return TIPO_AUSENCIA[a.tipo].label;
    case "duracion": return a.halfDay ? 0.5 : a.daysCount;
  }
}

interface Props {
  ausencias: Ausencia[];
  puedeGestionar: boolean;
  onEditar: (ausencia: Ausencia) => void;
  onChanged: () => void;
}

export function AsistenciasListado({
  ausencias,
  puedeGestionar,
  onEditar,
  onChanged,
}: Props) {
  const anioActual = new Date().getFullYear();
  const [busqueda, setBusqueda] = useState("");
  const [tipo, setTipo] = useState<TipoAusencia | "">("");
  const [anio, setAnio] = useState<string>(String(anioActual));

  const { sort, toggleSort } = useTableSort<AusenciaSortKey>({
    initial: { key: "fecha", direction: "desc" },
    keys: AUSENCIA_SORT_KEYS,
    descFirstKeys: ["fecha"],
  });
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);

  const anios = useMemo(() => {
    const desde = 2017;
    return Array.from({ length: anioActual + 2 - desde + 1 }, (_, i) => desde + i);
  }, [anioActual]);

  const filtradas = useMemo(() => {
    const q = busqueda.trim().toLowerCase();
    const base = ausencias.filter((a) => {
      if (tipo && a.tipo !== tipo) return false;
      if (anio && a.startDate.slice(0, 4) !== anio) return false;
      if (!q) return true;
      return (
        a.empleadoNombre.toLowerCase().includes(q) ||
        TIPO_AUSENCIA[a.tipo].label.toLowerCase().includes(q) ||
        (a.reason ?? "").toLowerCase().includes(q)
      );
    });
    return [...base].sort((a, b) =>
      compareSortValues(ausenciaSortValue(a, sort.key), ausenciaSortValue(b, sort.key), sort.direction),
    );
  }, [ausencias, busqueda, tipo, anio, sort]);

  // Volver a la página 1 en cada cambio de filtro/orden — en el punto donde
  // cambian, no en un efecto (react-hooks/set-state-in-effect).
  const handleBusquedaChange = (value: string) => { setBusqueda(value); setPage(1); };
  const handleTipoChange = (value: TipoAusencia | "") => { setTipo(value); setPage(1); };
  const handleAnioChange = (value: string) => { setAnio(value); setPage(1); };
  const handleToggleSort = (key: AusenciaSortKey) => { toggleSort(key); setPage(1); };

  const totalPaginas = Math.max(1, Math.ceil(filtradas.length / PAGE_SIZE));
  const paginaActual = Math.min(page, totalPaginas);
  const visibles = filtradas.slice((paginaActual - 1) * PAGE_SIZE, paginaActual * PAGE_SIZE);

  const eliminar = (a: Ausencia) => {
    if (!window.confirm(`¿Eliminar la baja de ${a.empleadoNombre}?`)) return;
    setError(null);
    asistenciasApi
      .remove(a.id)
      .then(onChanged)
      .catch((err: unknown) => {
        setError(err instanceof ApiError ? err.message : "No se pudo eliminar la baja.");
      });
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end gap-3">
        <div className="relative w-full max-w-[280px]">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <BrandInput
            label="Buscar"
            placeholder="Buscar baja…"
            value={busqueda}
            onChange={(e) => handleBusquedaChange(e.target.value)}
            className="pl-9"
          />
        </div>
        <div className="w-52">
          <BrandSelect
            label="Tipo"
            value={tipo}
            onChange={(e) => handleTipoChange(e.target.value as TipoAusencia | "")}
          >
            <option value="">Todos los tipos</option>
            {(Object.keys(TIPO_AUSENCIA) as TipoAusencia[]).map((t) => (
              <option key={t} value={t}>
                {TIPO_AUSENCIA[t].label}
              </option>
            ))}
          </BrandSelect>
        </div>
        <div className="w-36">
          <BrandSelect label="Año" value={anio} onChange={(e) => handleAnioChange(e.target.value)}>
            <option value="">Todos los años</option>
            {anios.map((y) => (
              <option key={y} value={String(y)}>
                {y}
              </option>
            ))}
          </BrandSelect>
        </div>
      </div>

      {error && (
        <p className="rounded-[8px] border border-destructive/20 bg-destructive/10 px-4 py-2.5 font-body text-sm text-foreground">
          {error}
        </p>
      )}

      {filtradas.length === 0 ? (
        <BrandEmptyState
          icon={ShieldAlert}
          title="No hay bajas registradas"
          description="Ajustá los filtros o registrá una baja nueva."
        />
      ) : (
        <div className="overflow-x-auto rounded-[12px] border border-border">
          <table className="w-full min-w-[720px] font-body text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/30 text-left font-heading text-[11px] uppercase tracking-[.06em] text-muted-foreground">
                <SortableHeader column={{ key: "empleado", label: "Empleado" }} sort={sort} onToggleSort={handleToggleSort} />
                <SortableHeader column={{ key: "fecha", label: "Fecha" }} sort={sort} onToggleSort={handleToggleSort} />
                <SortableHeader column={{ key: "tipo", label: "Tipo" }} sort={sort} onToggleSort={handleToggleSort} />
                <SortableHeader column={{ key: "duracion", label: "Duración" }} sort={sort} onToggleSort={handleToggleSort} />
                <th className="px-4 py-3">Observaciones</th>
                {puedeGestionar && <th className="px-4 py-3" />}
              </tr>
            </thead>
            <tbody>
              {visibles.map((a) => (
                <tr key={a.id} className="border-b border-border/60 last:border-0">
                  <td className="px-4 py-3">
                    <span className="flex items-center gap-2.5">
                      <span
                        className="flex h-7 w-7 flex-none items-center justify-center rounded-[7px] font-heading text-[10px] font-bold text-white"
                        style={{ backgroundColor: a.empleadoColor }}
                      >
                        {iniciales(a.empleadoNombre)}
                      </span>
                      <span className="font-semibold text-foreground">
                        {a.empleadoNombre}
                      </span>
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-foreground">
                    {a.startDate === a.endDate
                      ? formatFecha(a.startDate)
                      : `${formatFecha(a.startDate)} – ${formatFecha(a.endDate)}`}
                  </td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center gap-1.5">
                      <span
                        className="h-[7px] w-[7px] flex-none rounded-full"
                        style={{ backgroundColor: TIPO_AUSENCIA[a.tipo].color }}
                      />
                      <span className="text-foreground">{TIPO_AUSENCIA[a.tipo].label}</span>
                      {a.status !== "APPROVED" && <SolicitudEstadoBadge estado={a.status} />}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {duracionTexto(a)}
                  </td>
                  <td className="max-w-[200px] truncate px-4 py-3 text-muted-foreground" title={a.reason ?? ""}>
                    {a.reason ?? "—"}
                  </td>
                  {puedeGestionar && (
                    <td className="px-4 py-3">
                      <span className="flex justify-end gap-1.5">
                        <button
                          type="button"
                          onClick={() => onEditar(a)}
                          className="rounded-[6px] border border-border px-2.5 py-1 text-xs font-semibold text-foreground hover:bg-muted"
                        >
                          Editar
                        </button>
                        <button
                          type="button"
                          onClick={() => eliminar(a)}
                          className="rounded-[6px] border border-destructive/30 px-2.5 py-1 text-xs font-semibold text-destructive hover:bg-destructive/10"
                        >
                          Eliminar
                        </button>
                      </span>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {filtradas.length > 0 && (
        <PaginationBar
          page={paginaActual}
          total={filtradas.length}
          size={PAGE_SIZE}
          onPageChange={setPage}
          noun="bajas"
        />
      )}
    </div>
  );
}
