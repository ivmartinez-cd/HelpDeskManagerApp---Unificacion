"use client";

import { useMemo, useState } from "react";
import { Users } from "lucide-react";
import { BrandBadge, BrandEmptyState, BrandInput, BrandSelect } from "@/shared/components/ui/brand-form";
import { SortableHeader } from "@/shared/components/ui/sortable-header";
import { compareSortValues, useTableSort } from "@/shared/hooks/use-table-sort";
import { gestionApi } from "../api/gestion-api";
import { formatAntiguedad, formatFecha, hoyIso, iniciales } from "../lib/fechas";
import type { Cargo, EmpleadoListItem, Sector, UsuarioOption } from "../types/vacaciones";
import { EmpleadoModal } from "./empleado-modal";

type EmpleadoSortKey =
  | "nombre" | "email" | "sector" | "cargo" | "ingreso" | "disponibles" | "estado";
const EMPLEADO_SORT_KEYS: readonly EmpleadoSortKey[] = [
  "nombre", "email", "sector", "cargo", "ingreso", "disponibles", "estado",
];

function empleadoSortValue(e: EmpleadoListItem, key: EmpleadoSortKey) {
  switch (key) {
    case "nombre": return `${e.firstName} ${e.lastName}`;
    case "email": return e.email;
    case "sector": return e.sectorNombre;
    case "cargo": return e.cargoNombre;
    case "ingreso": return e.hireDate;
    case "disponibles": return e.saldo.available;
    case "estado": return e.status;
  }
}

interface Props {
  empleados: EmpleadoListItem[];
  sectores: Sector[];
  cargos: Cargo[];
  usuarios: UsuarioOption[];
  puedeGestionar: boolean;
  abrirAlta: boolean;
  onCerrarAlta: () => void;
  onChanged: () => void;
}

export function EmpleadosTab({
  empleados,
  sectores,
  cargos,
  usuarios,
  puedeGestionar,
  abrirAlta,
  onCerrarAlta,
  onChanged,
}: Props) {
  const [busqueda, setBusqueda] = useState("");
  const [sectorId, setSectorId] = useState("");
  const [editando, setEditando] = useState<EmpleadoListItem | null>(null);
  const anioActual = Number(hoyIso().slice(0, 4));

  const { sort, toggleSort } = useTableSort<EmpleadoSortKey>({
    initial: { key: "nombre", direction: "asc" },
    keys: EMPLEADO_SORT_KEYS,
    descFirstKeys: ["ingreso"],
  });

  const visibles = useMemo(() => {
    const q = busqueda.trim().toLowerCase();
    const base = empleados.filter((e) => {
      if (sectorId && e.departmentId !== sectorId) return false;
      if (!q) return true;
      return [`${e.firstName} ${e.lastName}`, e.email, e.cargoNombre].some((v) =>
        v.toLowerCase().includes(q),
      );
    });
    return [...base].sort((a, b) =>
      compareSortValues(empleadoSortValue(a, sort.key), empleadoSortValue(b, sort.key), sort.direction),
    );
  }, [empleados, busqueda, sectorId, sort]);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end gap-3">
        <div className="min-w-[260px] flex-1">
          <BrandInput
            label="Buscar"
            type="search"
            placeholder="Por nombre, email o cargo…"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
          />
        </div>
        <div className="min-w-[200px]">
          <BrandSelect
            label="Sector"
            value={sectorId}
            onChange={(e) => setSectorId(e.target.value)}
          >
            <option value="">Todos los sectores</option>
            {sectores.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </BrandSelect>
        </div>
      </div>

      {visibles.length === 0 ? (
        <BrandEmptyState
          icon={Users}
          title="No se encontraron empleados"
          description="Ajustá la búsqueda o creá un empleado nuevo."
        />
      ) : (
        <div className="overflow-x-auto rounded-[12px] border border-border">
          <table className="w-full min-w-[860px] font-body text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/30 text-left font-heading text-[11px] uppercase tracking-[.06em] text-muted-foreground">
                <SortableHeader column={{ key: "nombre", label: "Nombre" }} sort={sort} onToggleSort={toggleSort} />
                <SortableHeader column={{ key: "email", label: "Email" }} sort={sort} onToggleSort={toggleSort} />
                <SortableHeader column={{ key: "sector", label: "Sector" }} sort={sort} onToggleSort={toggleSort} />
                <SortableHeader column={{ key: "cargo", label: "Cargo" }} sort={sort} onToggleSort={toggleSort} />
                <SortableHeader column={{ key: "ingreso", label: "Ingreso / Antigüedad" }} sort={sort} onToggleSort={toggleSort} />
                <SortableHeader column={{ key: "disponibles", label: "Disponibles" }} sort={sort} onToggleSort={toggleSort} />
                <SortableHeader column={{ key: "estado", label: "Estado" }} sort={sort} onToggleSort={toggleSort} />
                {puedeGestionar && <th className="px-4 py-3" />}
              </tr>
            </thead>
            <tbody>
              {visibles.map((e) => (
                <tr key={e.id} className="border-b border-border/60 last:border-0">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2.5">
                      <span
                        className="flex h-8 w-8 shrink-0 items-center justify-center rounded-[8px] font-heading text-[11px] font-bold text-white"
                        style={{ backgroundColor: e.color }}
                      >
                        {iniciales(`${e.firstName} ${e.lastName}`)}
                      </span>
                      <span className="font-semibold text-foreground">
                        {e.firstName} {e.lastName}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">{e.email}</td>
                  <td className="px-4 py-3">
                    <span
                      className="inline-block rounded-[20px] px-2.5 py-1 text-xs font-semibold text-white"
                      style={{ backgroundColor: e.sectorColor }}
                    >
                      {e.sectorNombre}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-foreground">{e.cargoNombre}</td>
                  <td className="px-4 py-3">
                    <div className="text-foreground">{formatFecha(e.hireDate)}</div>
                    <div className="text-xs text-muted-foreground">
                      {formatAntiguedad(e.antiguedadAnios)}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div>
                      <span className="mr-1 text-[10px] font-semibold uppercase text-muted-foreground">
                        {anioActual}:
                      </span>
                      <span className="font-heading font-bold text-brand-orange">
                        {e.saldo.available}
                      </span>
                      <span className="text-muted-foreground">
                        /{e.saldo.annual + e.saldo.carryOver}
                      </span>
                    </div>
                    {e.saldoSiguiente && (
                      <div className="mt-0.5 text-xs">
                        <span className="mr-1 text-[10px] font-semibold uppercase text-muted-foreground">
                          {anioActual + 1}:
                        </span>
                        <span className="font-semibold text-foreground">
                          {e.saldoSiguiente.available}
                        </span>
                        <span className="text-muted-foreground">
                          /{e.saldoSiguiente.annual + e.saldoSiguiente.carryOver}
                        </span>
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <BrandBadge variant={e.status === "ACTIVE" ? "success" : "neutral"}>
                      {e.status === "ACTIVE" ? "Activo" : "Inactivo"}
                    </BrandBadge>
                  </td>
                  {puedeGestionar && (
                    <td className="px-4 py-3 text-right">
                      <button
                        type="button"
                        onClick={() => setEditando(e)}
                        className="rounded-[8px] border border-border px-3 py-1.5 text-xs font-semibold text-foreground hover:bg-muted"
                      >
                        Editar
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {(abrirAlta || editando) && (
        <EmpleadoModal
          empleado={editando}
          sectores={sectores}
          cargos={cargos}
          usuarios={usuarios}
          onClose={() => {
            onCerrarAlta();
            setEditando(null);
          }}
          onSaved={() => {
            onCerrarAlta();
            setEditando(null);
            onChanged();
          }}
          onDeleted={() => {
            setEditando(null);
            onChanged();
          }}
          deleteFn={editando ? () => gestionApi.deleteEmpleado(editando.id) : undefined}
        />
      )}
    </div>
  );
}
