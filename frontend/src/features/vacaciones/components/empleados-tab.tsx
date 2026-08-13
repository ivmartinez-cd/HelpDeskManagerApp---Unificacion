"use client";

import { useMemo, useState } from "react";
import { Users } from "lucide-react";
import { BrandBadge, BrandEmptyState, BrandInput, BrandSelect } from "@/shared/components/ui/brand-form";
import { gestionApi } from "../api/gestion-api";
import { formatAntiguedad, formatFecha, iniciales } from "../lib/fechas";
import type { Cargo, EmpleadoListItem, Sector, UsuarioOption } from "../types/vacaciones";
import { EmpleadoModal } from "./empleado-modal";

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

  const visibles = useMemo(() => {
    const q = busqueda.trim().toLowerCase();
    return empleados.filter((e) => {
      if (sectorId && e.departmentId !== sectorId) return false;
      if (!q) return true;
      return [`${e.firstName} ${e.lastName}`, e.email, e.cargoNombre].some((v) =>
        v.toLowerCase().includes(q),
      );
    });
  }, [empleados, busqueda, sectorId]);

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
                <th className="px-4 py-3">Nombre</th>
                <th className="px-4 py-3">Email</th>
                <th className="px-4 py-3">Sector</th>
                <th className="px-4 py-3">Cargo</th>
                <th className="px-4 py-3">Ingreso / Antigüedad</th>
                <th className="px-4 py-3 text-right">Días</th>
                <th className="px-4 py-3">Estado</th>
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
                  <td className="px-4 py-3 text-right font-heading font-bold text-brand-orange">
                    {e.diasAnuales}
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
