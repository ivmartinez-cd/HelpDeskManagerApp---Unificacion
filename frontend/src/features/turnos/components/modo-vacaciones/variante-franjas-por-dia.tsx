"use client";

import { useMemo, useState } from "react";
import { Plus } from "lucide-react";
import { BrandButton } from "@/shared/components/ui/brand-form";
import type { SearchableSelectOption } from "@/shared/components/ui/searchable-select";
import type { Casilla } from "../../types/turnos";
import type { FranjaEditable } from "../../types/grilla-variantes";
import { cn } from "@/shared/utils/cn";
import { VarianteFranjaFila } from "./variante-franja-fila";

interface Props {
  casillas: Casilla[];
  diaLabel: string;
  franjasDelDia: FranjaEditable[];
  opcionesOperador: SearchableSelectOption[];
  keysConError: Set<string>;
  onAgregar: (casillaId: string) => void;
  onActualizar: (key: string, cambios: Partial<FranjaEditable>) => void;
  onEliminar: (key: string) => void;
}

interface CasillaTabItemProps {
  casilla: Casilla;
  isSelected: boolean;
  count: number;
  hasError: boolean;
  hasEmptyReq: boolean;
  onClick: () => void;
}

function CasillaTabItem({
  casilla,
  isSelected,
  count,
  hasError,
  hasEmptyReq,
  onClick,
}: CasillaTabItemProps) {
  return (
    <button
      type="button"
      role="tab"
      aria-selected={isSelected}
      onClick={onClick}
      className={cn(
        "relative inline-flex items-center gap-2 rounded-[8px] px-3.5 py-1.5 font-heading text-xs font-bold transition-colors",
        isSelected
          ? "bg-brand-orange text-white shadow-xs"
          : "bg-muted text-muted-foreground hover:bg-muted/80 hover:text-foreground",
      )}
    >
      <span>{casilla.nombre}</span>
      <span
        className={cn(
          "rounded-full px-1.5 py-0.5 text-[10.5px] font-semibold",
          isSelected ? "bg-white/20 text-white" : "bg-card text-muted-foreground",
        )}
      >
        {count}
      </span>
      {hasError && (
        <span
          className="h-2 w-2 rounded-full bg-destructive ring-2 ring-card"
          title="Contiene solapamientos o errores"
        />
      )}
      {!hasError && hasEmptyReq && (
        <span
          className="h-2 w-2 rounded-full bg-amber-400 ring-2 ring-card"
          title="Tiene turnos sin operador asignado"
        />
      )}
    </button>
  );
}

interface CasillaGrupoProps {
  casilla: Casilla;
  diaLabel: string;
  filas: FranjaEditable[];
  opcionesOperador: SearchableSelectOption[];
  keysConError: Set<string>;
  mostrarCabecera: boolean;
  onAgregar: (casillaId: string) => void;
  onActualizar: (key: string, cambios: Partial<FranjaEditable>) => void;
  onEliminar: (key: string) => void;
}

function CasillaGrupo({
  casilla,
  diaLabel,
  filas,
  opcionesOperador,
  keysConError,
  mostrarCabecera,
  onAgregar,
  onActualizar,
  onEliminar,
}: CasillaGrupoProps) {
  return (
    <div className="flex flex-col gap-2" data-testid={`casilla-${casilla.nombre}`}>
      {mostrarCabecera && (
        <div className="flex items-center justify-between">
          <span className="font-heading text-sm font-bold text-foreground">
            {casilla.nombre} · {diaLabel}
          </span>
          <BrandButton
            type="button"
            variant="outline"
            size="sm"
            onClick={() => onAgregar(casilla.id)}
          >
            <Plus className="h-3.5 w-3.5" />
            Agregar franja en {casilla.nombre}
          </BrandButton>
        </div>
      )}
      {filas.length === 0 ? (
        <div className="flex items-center justify-between rounded-[10px] border border-dashed border-border px-4 py-3">
          <p className="font-body text-xs text-muted-foreground">
            Sin franjas para {casilla.nombre} este día.
          </p>
          {!mostrarCabecera && (
            <BrandButton
              type="button"
              variant="outline"
              size="sm"
              onClick={() => onAgregar(casilla.id)}
            >
              <Plus className="h-3.5 w-3.5" />
              Agregar primera franja
            </BrandButton>
          )}
        </div>
      ) : (
        filas.map((f) => (
          <VarianteFranjaFila
            key={f.key}
            franja={f}
            casillaNombre={casilla.nombre}
            operadores={opcionesOperador}
            conError={keysConError.has(f.key)}
            onChange={(cambios) => onActualizar(f.key, cambios)}
            onRemove={() => onEliminar(f.key)}
          />
        ))
      )}
    </div>
  );
}

/** Franjas del día activo agrupadas con selector de pestañas internas por casilla. */
export function VarianteFranjasPorDia({
  casillas,
  diaLabel,
  franjasDelDia,
  opcionesOperador,
  keysConError,
  onAgregar,
  onActualizar,
  onEliminar,
}: Props) {
  const [tabCasilla, setTabCasilla] = useState<string>(() => casillas[0]?.id ?? "todas");

  const tabValido = useMemo(() => {
    if (tabCasilla === "todas") return "todas";
    return casillas.some((c) => c.id === tabCasilla) ? tabCasilla : (casillas[0]?.id ?? "todas");
  }, [tabCasilla, casillas]);

  const casillasFiltradas = useMemo(() => {
    if (tabValido === "todas") return casillas;
    return casillas.filter((c) => c.id === tabValido);
  }, [tabValido, casillas]);

  const casillaActivaObj = casillas.find((c) => c.id === tabValido);

  return (
    <div className="flex flex-col gap-4">
      {casillas.length > 1 && (
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/50 pb-3">
          <div
            role="tablist"
            aria-label="Casillas del día"
            className="flex flex-wrap items-center gap-1.5"
          >
            {casillas.map((c) => (
              <CasillaTabItem
                key={c.id}
                casilla={c}
                isSelected={tabValido === c.id}
                count={franjasDelDia.filter((f) => f.casillaId === c.id).length}
                hasError={franjasDelDia.some(
                  (f) => f.casillaId === c.id && keysConError.has(f.key),
                )}
                hasEmptyReq={franjasDelDia.some(
                  (f) => f.casillaId === c.id && f.requiereCobertura && !f.userIds.length,
                )}
                onClick={() => setTabCasilla(c.id)}
              />
            ))}
            <button
              type="button"
              role="tab"
              aria-selected={tabValido === "todas"}
              onClick={() => setTabCasilla("todas")}
              className={cn(
                "inline-flex items-center gap-1.5 rounded-[8px] px-3 py-1.5 font-heading text-xs font-medium transition-colors",
                tabValido === "todas"
                  ? "bg-foreground text-background shadow-xs"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground",
              )}
            >
              <span>Ver todas</span>
              <span className="text-[10.5px] opacity-70">({franjasDelDia.length})</span>
            </button>
          </div>

          {tabValido !== "todas" && casillaActivaObj && (
            <BrandButton
              type="button"
              variant="outline"
              size="sm"
              onClick={() => onAgregar(tabValido)}
            >
              <Plus className="h-3.5 w-3.5" />
              Agregar franja en {casillaActivaObj.nombre}
            </BrandButton>
          )}
        </div>
      )}

      {casillasFiltradas.map((casilla) => {
        const filas = franjasDelDia
          .filter((f) => f.casillaId === casilla.id)
          .sort((a, b) => a.horaInicio.localeCompare(b.horaInicio));
        return (
          <CasillaGrupo
            key={casilla.id}
            casilla={casilla}
            diaLabel={diaLabel}
            filas={filas}
            opcionesOperador={opcionesOperador}
            keysConError={keysConError}
            mostrarCabecera={tabValido === "todas" || casillas.length <= 1}
            onAgregar={onAgregar}
            onActualizar={onActualizar}
            onEliminar={onEliminar}
          />
        );
      })}
    </div>
  );
}
