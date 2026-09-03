"use client";

import { useState } from "react";
import { ArrowLeftRight, X } from "lucide-react";
import { ApiError } from "@/services/http-client";
import { BrandButton, BrandSelect } from "@/shared/components/ui/brand-form";
import { configApi } from "../api/config-api";
import { gestionApi } from "../api/gestion-api";
import { ordenarPorNombre } from "../lib/empleados";
import { iniciales } from "../lib/fechas";
import type { Cargo, EmpleadoListItem, Exclusion } from "../types/vacaciones";

interface Props {
  exclusiones: Exclusion[];
  empleados: EmpleadoListItem[];
  cargos: Cargo[];
  onChanged: () => void;
}

export function ConfigSolapamientosTab({
  exclusiones,
  empleados,
  cargos,
  onChanged,
}: Props) {
  return (
    <div className="grid items-start gap-4 lg:grid-cols-2">
      <ExclusionesCard exclusiones={exclusiones} empleados={empleados} onChanged={onChanged} />
      <LimitesCargoCard cargos={cargos} onChanged={onChanged} />
    </div>
  );
}

function ExclusionesCard({
  exclusiones,
  empleados,
  onChanged,
}: {
  exclusiones: Exclusion[];
  empleados: EmpleadoListItem[];
  onChanged: () => void;
}) {
  const [empleadoA, setEmpleadoA] = useState("");
  const [empleadoB, setEmpleadoB] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const empleadosOrdenados = ordenarPorNombre(empleados);

  const colorDe = (id: string) =>
    empleados.find((e) => e.id === id)?.color ?? "#475569";

  const agregar = () => {
    if (!empleadoA || !empleadoB || empleadoA === empleadoB) {
      setError("Elegí dos empleados distintos.");
      return;
    }
    setBusy(true);
    setError(null);
    configApi
      .createExclusion(empleadoA, empleadoB)
      .then(() => {
        setEmpleadoA("");
        setEmpleadoB("");
        onChanged();
      })
      .catch((err: unknown) => {
        setError(err instanceof ApiError ? err.message : "No se pudo agregar la exclusión.");
      })
      .finally(() => setBusy(false));
  };

  const eliminar = (id: string) => {
    configApi
      .deleteExclusion(id)
      .then(onChanged)
      .catch((err: unknown) => {
        setError(err instanceof ApiError ? err.message : "No se pudo eliminar la exclusión.");
      });
  };

  return (
    <div className="rounded-[12px] border border-border bg-card p-5">
      <h3 className="font-heading text-sm font-bold text-foreground">Exclusiones Mutuas</h3>
      <p className="mb-4 mt-0.5 font-body text-[12.5px] leading-snug text-muted-foreground">
        Pares de empleados que no pueden estar de vacaciones simultáneamente.
      </p>
      <div className="mb-3 grid grid-cols-2 gap-2">
        <BrandSelect label="Empleado A" value={empleadoA} onChange={(e) => setEmpleadoA(e.target.value)}>
          <option value="">Elegir…</option>
          {empleadosOrdenados.map((e) => (
            <option key={e.id} value={e.id}>
              {e.firstName} {e.lastName}
            </option>
          ))}
        </BrandSelect>
        <BrandSelect label="Empleado B" value={empleadoB} onChange={(e) => setEmpleadoB(e.target.value)}>
          <option value="">Elegir…</option>
          {empleadosOrdenados
            .filter((e) => e.id !== empleadoA)
            .map((e) => (
              <option key={e.id} value={e.id}>
                {e.firstName} {e.lastName}
              </option>
            ))}
        </BrandSelect>
      </div>
      <BrandButton variant="outline" size="sm" onClick={agregar} loading={busy}>
        + Agregar exclusión
      </BrandButton>
      {error && (
        <p className="mt-2 font-body text-xs text-destructive">{error}</p>
      )}
      <div className="mt-4 flex flex-col gap-2">
        {exclusiones.length === 0 && (
          <p className="font-body text-xs text-muted-foreground">Sin exclusiones cargadas.</p>
        )}
        {exclusiones.map((ex) => (
          <div
            key={ex.id}
            className="flex items-center gap-2 rounded-[8px] border border-border/60 bg-muted/20 px-3 py-2"
          >
            <span
              className="flex h-6 w-6 flex-none items-center justify-center rounded-[6px] font-heading text-[9px] font-bold text-white"
              style={{ backgroundColor: colorDe(ex.empleadoAId) }}
            >
              {iniciales(ex.empleadoANombre)}
            </span>
            <span className="font-body text-[13px] font-semibold text-foreground">
              {ex.empleadoANombre}
            </span>
            <ArrowLeftRight className="h-3 w-3 flex-none text-muted-foreground" />
            <span
              className="flex h-6 w-6 flex-none items-center justify-center rounded-[6px] font-heading text-[9px] font-bold text-white"
              style={{ backgroundColor: colorDe(ex.empleadoBId) }}
            >
              {iniciales(ex.empleadoBNombre)}
            </span>
            <span className="font-body text-[13px] font-semibold text-foreground">
              {ex.empleadoBNombre}
            </span>
            <button
              type="button"
              onClick={() => eliminar(ex.id)}
              aria-label="Eliminar exclusión"
              className="ml-auto flex h-6 w-6 items-center justify-center rounded text-muted-foreground hover:text-destructive"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

function LimitesCargoCard({ cargos, onChanged }: { cargos: Cargo[]; onChanged: () => void }) {
  const [cargoId, setCargoId] = useState("");
  const [limite, setLimite] = useState(1);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const conLimite = cargos.filter((c) => c.maxSimultaneos !== null);
  const sinLimite = cargos.filter((c) => c.maxSimultaneos === null);

  const setMax = (cargo: Cargo, max: number | null) => {
    setBusy(true);
    setError(null);
    gestionApi
      .updateCargo(cargo.id, { name: cargo.name, maxSimultaneos: max })
      .then(() => {
        setCargoId("");
        setLimite(1);
        onChanged();
      })
      .catch((err: unknown) => {
        setError(err instanceof ApiError ? err.message : "No se pudo actualizar el cargo.");
      })
      .finally(() => setBusy(false));
  };

  return (
    <div className="rounded-[12px] border border-border bg-card p-5">
      <h3 className="font-heading text-sm font-bold text-foreground">Límites por Cargo</h3>
      <p className="mb-4 mt-0.5 font-body text-[12.5px] leading-snug text-muted-foreground">
        Máximo de personas del mismo cargo que pueden estar ausentes simultáneamente.
      </p>
      <div className="mb-3 flex items-end gap-2">
        <div className="flex-1">
          <BrandSelect label="Cargo" value={cargoId} onChange={(e) => setCargoId(e.target.value)}>
            <option value="">Seleccioná cargo…</option>
            {sinLimite.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </BrandSelect>
        </div>
        <input
          type="number"
          min={1}
          value={limite}
          onChange={(e) => setLimite(Math.max(1, Number(e.target.value)))}
          aria-label="Límite máximo simultáneo"
          className="h-[38px] w-20 rounded-[8px] border border-border bg-card px-3 text-center font-body text-sm font-semibold text-foreground outline-none focus:ring-2 focus:ring-brand-orange/40"
        />
        <BrandButton
          size="sm"
          onClick={() => {
            const cargo = cargos.find((c) => c.id === cargoId);
            if (cargo) setMax(cargo, limite);
          }}
          disabled={!cargoId}
          loading={busy}
        >
          + Agregar
        </BrandButton>
      </div>
      {error && <p className="mb-2 font-body text-xs text-destructive">{error}</p>}
      <div className="flex flex-col gap-2">
        {conLimite.length === 0 && (
          <p className="font-body text-xs text-muted-foreground">Sin límites configurados.</p>
        )}
        {conLimite.map((c) => (
          <div
            key={c.id}
            className="flex items-center gap-2.5 rounded-[8px] border border-border/60 bg-muted/20 px-3 py-2"
          >
            <span className="flex-1 font-body text-[13px] font-semibold text-foreground">
              {c.name}
            </span>
            <span className="font-body text-[12.5px] text-muted-foreground">
              Máx. <strong className="text-brand-orange">{c.maxSimultaneos}</strong>{" "}
              simultáneo{(c.maxSimultaneos ?? 0) === 1 ? "" : "s"}
            </span>
            <button
              type="button"
              onClick={() => setMax(c, null)}
              aria-label="Quitar límite"
              className="flex h-6 w-6 items-center justify-center rounded text-muted-foreground hover:text-destructive"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
