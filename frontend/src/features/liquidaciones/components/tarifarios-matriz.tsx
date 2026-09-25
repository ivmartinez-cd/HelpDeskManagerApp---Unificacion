"use client";

import { ChevronDown, ChevronUp, History, Trash2 } from "lucide-react";
import { useCallback, useState } from "react";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { SortableHeader } from "@/shared/components/ui/sortable-header";
import { useOptionalTableSort, useSortedRows } from "@/shared/hooks/use-optional-table-sort";
import { formatARS, formatFechaDia } from "../lib/format";
import { labelTipo, type VigenciaZona, type ZonaTarifas } from "../lib/tarifarios-matriz";
import type { Tarifario } from "../types/liquidaciones";

// Matriz de tarifarios "como Siges": una fila por zona, una columna por tipo
// de servicio, historial de vigencias desplegable por zona. Misma estética de
// tabla que `spsts-config.tsx` (thCls/tdCls). La tabla principal ordena por
// cualquier encabezado (valores de la vigencia de hoy); el historial de cada
// zona queda cronológico, porque marca la variación contra la vigencia anterior.

const thCls =
  "py-3 px-3 font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground text-left whitespace-nowrap";
const tdCls = "py-3 px-3 font-body text-sm text-foreground whitespace-nowrap";
const tdNum = `${tdCls} text-right tabular-nums`;

export interface MatrizAcciones {
  /** Abre el modal de nueva vigencia (todos los tipos) para la zona. */
  onNuevaVigencia: (zona: ZonaTarifas) => void;
  /** Edita una tarifa puntual (celda) sin tocar el historial. */
  onEditarTarifa: (t: Tarifario) => void;
  /** Alta de una tarifa para un tipo que la zona no tiene en esa vigencia. */
  onNuevaTarifa: (zona: ZonaTarifas, tipo: string, vigencia: VigenciaZona | null) => void;
  /** Borra todas las tarifas de una vigencia de la zona. */
  onEliminarVigencia: (zona: ZonaTarifas, vigencia: VigenciaZona) => void;
}

function CeldaTarifa({
  tarifa, canEdit, onEditar, onNueva,
}: {
  tarifa: Tarifario | undefined;
  canEdit: boolean;
  onEditar: (t: Tarifario) => void;
  onNueva: () => void;
}) {
  if (!tarifa) {
    return canEdit ? (
      <button
        type="button"
        onClick={onNueva}
        title="Esta zona no tiene tarifa para este tipo en esta vigencia — cargarla"
        className="rounded-[6px] px-1.5 py-0.5 font-body text-xs text-muted-foreground transition-colors hover:bg-muted hover:text-brand-orange"
      >
        —
      </button>
    ) : (
      <span className="text-muted-foreground">—</span>
    );
  }
  if (!canEdit) return <span className="font-semibold">{formatARS(tarifa.costoServicio)}</span>;
  return (
    <button
      type="button"
      onClick={() => onEditar(tarifa)}
      title="Corrige este valor puntual sin crear una vigencia nueva"
      className="rounded-[6px] px-1.5 py-0.5 font-semibold transition-colors hover:bg-muted hover:text-brand-orange"
    >
      {formatARS(tarifa.costoServicio)}
    </button>
  );
}

function VariacionCorrectivo({ actual, anterior }: { actual?: Tarifario; anterior?: Tarifario }) {
  if (!actual || !anterior || !anterior.costoServicio) return null;
  const pct = ((actual.costoServicio - anterior.costoServicio) / anterior.costoServicio) * 100;
  const cls = pct > 0 ? "text-success" : pct < 0 ? "text-destructive" : "text-muted-foreground";
  return (
    <span className={`ml-1 font-body text-[10px] font-bold ${cls}`} title="Variación del correctivo contra la vigencia anterior">
      {pct === 0 ? "=" : `${pct > 0 ? "+" : ""}${pct.toFixed(1)}%`}
    </span>
  );
}

function FilaVigencia({
  zona, vigencia, anterior, tipos, canEdit, acciones,
}: {
  zona: ZonaTarifas;
  vigencia: VigenciaZona;
  anterior: VigenciaZona | undefined;
  tipos: string[];
  canEdit: boolean;
  acciones: MatrizAcciones;
}) {
  const esVigente = zona.vigente?.desde === vigencia.desde;
  return (
    <tr className={`border-t border-border/60 ${esVigente ? "bg-brand-orange/5" : ""}`}>
      <td className={`${tdCls} pl-8`}>
        <span className="font-semibold">{formatFechaDia(vigencia.desde)}</span>
        <span className="text-muted-foreground"> al {vigencia.hasta ? formatFechaDia(vigencia.hasta) : "actualidad"}</span>
        {esVigente && (
          <span className="ml-2 rounded-full bg-success/10 px-2 py-0.5 font-body text-[10px] font-bold text-success">Vigente hoy</span>
        )}
        {!anterior && (
          <span className="ml-2 rounded-full bg-muted px-2 py-0.5 font-body text-[10px] font-bold text-muted-foreground">Inicial</span>
        )}
      </td>
      {tipos.map((tipo, i) => (
        <td key={tipo} className={tdNum}>
          <CeldaTarifa
            tarifa={vigencia.porTipo[tipo]}
            canEdit={canEdit}
            onEditar={acciones.onEditarTarifa}
            onNueva={() => acciones.onNuevaTarifa(zona, tipo, vigencia)}
          />
          {i === 0 && <VariacionCorrectivo actual={vigencia.porTipo[tipo]} anterior={anterior?.porTipo[tipo]} />}
        </td>
      ))}
      <td className={tdNum}>{formatARS(vigencia.costoKm)}</td>
      <td className={`${tdCls} text-right`}>
        {canEdit && (
          <button
            type="button"
            onClick={() => acciones.onEliminarVigencia(zona, vigencia)}
            aria-label="Eliminar vigencia"
            title={`Elimina las ${vigencia.tarifas.length} tarifas de esta vigencia`}
            className="rounded-[6px] p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-destructive"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        )}
      </td>
    </tr>
  );
}

function FilaZona({
  zona, label, tipos, canEdit, acciones,
}: {
  zona: ZonaTarifas;
  label: string;
  tipos: string[];
  canEdit: boolean;
  acciones: MatrizAcciones;
}) {
  const [abierta, setAbierta] = useState(false);
  const Chevron = abierta ? ChevronUp : ChevronDown;
  const vigente = zona.vigente;
  const columnas = tipos.length + 3;
  return (
    <>
      <tr className="border-t border-border transition-colors hover:bg-muted/30">
        <td className={`${tdCls} whitespace-normal font-semibold`}>{label}</td>
        {tipos.map((tipo) => (
          <td key={tipo} className={tdNum}>
            <CeldaTarifa
              tarifa={vigente?.porTipo[tipo]}
              canEdit={canEdit}
              onEditar={acciones.onEditarTarifa}
              onNueva={() => acciones.onNuevaTarifa(zona, tipo, vigente)}
            />
          </td>
        ))}
        <td className={tdNum}>{vigente ? `${formatARS(vigente.costoKm)}/km` : "—"}</td>
        <td className={tdCls}>{vigente ? formatFechaDia(vigente.desde) : "—"}</td>
        <td className={`${tdCls} text-right`}>
          <div className="flex items-center justify-end gap-1.5">
            {canEdit && (
              <BrandButton
                size="sm"
                variant="outline"
                onClick={() => acciones.onNuevaVigencia(zona)}
                title="Carga una vigencia nueva desde hoy para todos los tipos de la zona y cierra la anterior"
              >
                Nueva vigencia
              </BrandButton>
            )}
            <BrandButton size="sm" variant="outline" onClick={() => setAbierta((v) => !v)}>
              <History className="h-3.5 w-3.5" />
              Historial ({zona.vigencias.length})
              <Chevron className="h-3 w-3" />
            </BrandButton>
          </div>
        </td>
      </tr>
      {abierta && (
        <tr className="bg-muted/20">
          <td colSpan={columnas} className="p-0">
            <table className="w-full">
              <thead>
                <tr>
                  <th className={`${thCls} pl-8`}>Vigencia</th>
                  {tipos.map((tipo) => <th key={tipo} className={`${thCls} text-right`}>{labelTipo(tipo)}</th>)}
                  <th className={`${thCls} text-right`}>$/km</th>
                  <th className={thCls} />
                </tr>
              </thead>
              <tbody>
                {zona.vigencias.map((v, i) => (
                  <FilaVigencia key={v.desde} zona={zona} vigencia={v} anterior={zona.vigencias[i + 1]} tipos={tipos} canEdit={canEdit} acciones={acciones} />
                ))}
              </tbody>
            </table>
          </td>
        </tr>
      )}
    </>
  );
}

/** "zona", "km", "desde" o `tipo:<tipo de servicio>`. */
type SortKey = string;

function valorOrden(zona: ZonaTarifas, key: SortKey, labelZona: (spstId: string | null) => string) {
  const vigente = zona.vigente;
  if (key === "zona") return labelZona(zona.spstId);
  if (key === "km") return vigente?.costoKm;
  if (key === "desde") return vigente?.desde;
  return vigente?.porTipo[key.slice("tipo:".length)]?.costoServicio;
}

export function TarifariosMatriz({
  zonas, tipos, labelZona, canEdit, acciones,
}: {
  zonas: ZonaTarifas[];
  tipos: string[];
  labelZona: (spstId: string | null) => string;
  canEdit: boolean;
  acciones: MatrizAcciones;
}) {
  const { sort, toggleSort } = useOptionalTableSort<SortKey>();
  const valor = useCallback((z: ZonaTarifas, key: SortKey) => valorOrden(z, key, labelZona), [labelZona]);
  const filas = useSortedRows(zonas, sort, valor);
  const col = (key: SortKey, label: string, alinear = "") => (
    <SortableHeader key={key} column={{ key, label }} sort={sort} onToggleSort={toggleSort} thClassName={`${thCls} ${alinear}`} />
  );
  return (
    <div className="overflow-x-auto rounded-[12px] border border-border bg-card">
      <table className="w-full">
        <thead>
          <tr className="bg-muted/40">
            {col("zona", "Zona Siges")}
            {tipos.map((tipo) => col(`tipo:${tipo}`, labelTipo(tipo), "text-right"))}
            {col("km", "$/km", "text-right")}
            {col("desde", "Desde")}
            <th className={`${thCls} text-right`}>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {filas.map((zona) => (
            <FilaZona key={zona.spstId ?? ""} zona={zona} label={labelZona(zona.spstId)} tipos={tipos} canEdit={canEdit} acciones={acciones} />
          ))}
        </tbody>
      </table>
    </div>
  );
}
