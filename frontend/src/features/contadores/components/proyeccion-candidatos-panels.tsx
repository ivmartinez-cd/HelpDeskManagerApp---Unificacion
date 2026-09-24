"use client";

import { Fragment } from "react";
import { cn } from "@/shared/utils/cn";
import type { CandidatoLectura, CandidatosEquipo, RecalcularCandidatoResponse } from "../types/proyeccion";
import { claveLectura, diasParCalendario, type Seleccion } from "../hooks/use-candidatos-proyeccion";
import { diasEntre, fechaCorta, n0, n2, redondeoBancario } from "./proyeccion-formato";

/** Lista de lecturas y caja "Cálculo" de `PanelCandidatos.razor` (v1.7). */

function abrev(desc: string): string {
  return desc.length <= 12 ? desc : `${desc.slice(0, 12)}…`;
}

/** `ValidCss`: estimados en gris, T4 y WebCliente en amarillo, resto ok. */
function tonoValidacion(l: CandidatoLectura): string {
  if (l.tipo_toma === 14 || l.tipo_toma === 19) return "text-muted-foreground";
  if (l.tipo_toma === 4 || l.tipo_toma === 18) return "text-warning";
  return "text-success";
}

const DIVISORIA: { campo: keyof CandidatoLectura; texto: string; clase: string }[] = [
  { campo: "cambio_empresa_vs_anterior", texto: "cambio de empresa", clase: "border-t-2 border-destructive text-destructive" },
  { campo: "cambio_sucursal_vs_anterior", texto: "cambio de sucursal", clase: "border-t-2 border-brand-orange text-brand-orange" },
  { campo: "cambio_anexo_vs_anterior", texto: "cambio de anexo", clase: "border-t border-dashed border-warning text-warning" },
];

/** Línea que marca dónde el equipo cambió de ubicación (empresa > sucursal > anexo). */
function Divisoria({ lectura }: { lectura: CandidatoLectura }) {
  const d = DIVISORIA.find((x) => lectura[x.campo] === true);
  if (!d) return null;
  return (
    <tr aria-hidden>
      <td colSpan={6} className={cn("px-2 pb-0.5 pt-0 text-[10px] font-semibold", d.clase)}>
        {d.texto}
      </td>
    </tr>
  );
}

function BotonPL({ rol, activa, puede, onClick }: { rol: "P" | "L"; activa: boolean; puede: boolean; onClick: () => void }) {
  return (
    <button
      type="button"
      disabled={!puede}
      title={rol === "P" ? "Asignar como Partida" : "Asignar como Llegada"}
      onClick={onClick}
      className={cn(
        "h-6 w-6 rounded-[6px] border border-border bg-muted text-[10px] font-extrabold disabled:opacity-40",
        activa && (rol === "P" ? "border-success bg-success text-background" : "border-info bg-info text-background"),
      )}
    >
      {rol}
    </button>
  );
}

interface LecturasProps {
  datos: CandidatosEquipo | null;
  error: string | null;
  seleccion: Seleccion;
  puedeGestionar: boolean;
  onToggle: (rol: keyof Seleccion, lectura: CandidatoLectura) => void;
}

export function ProyeccionLecturasTabla({ datos, error, seleccion, puedeGestionar, onToggle }: LecturasProps) {
  if (error) return <p className="rounded-[8px] bg-destructive/10 px-3 py-2 text-xs text-destructive">{error}</p>;
  if (!datos) return <p className="text-sm text-muted-foreground">Cargando lecturas…</p>;
  if (datos.lecturas.length === 0) return <p className="text-sm text-muted-foreground">Sin lecturas registradas para este equipo.</p>;
  return (
    <div className="max-h-72 overflow-y-auto rounded-[8px] border border-border thin-scrollbar">
      <table className="w-full text-xs">
        <thead className="sticky top-0 bg-muted">
          <tr className="text-left text-[10px] uppercase text-muted-foreground">
            <th className="py-1.5 pl-2">Fecha</th>
            <th className="py-1.5">Tipo</th>
            <th className="py-1.5 text-right">Valor</th>
            <th className="py-1.5 text-center">Valid.</th>
            <th className="py-1.5 text-center">P</th>
            <th className="py-1.5 pr-2 text-center">L</th>
          </tr>
        </thead>
        <tbody>
          {datos.lecturas.map((l, i) => (
            <Fragment key={claveLectura(l, i)}>
              <tr className={cn("border-t border-border", !l.usable && "opacity-55")}>
                <td className="py-1.5 pl-2">{fechaCorta(l.fecha)}</td>
                <td className="py-1.5" title={l.desc_tipo_toma}>
                  T{l.tipo_toma}
                  <span className="block text-[10px] text-muted-foreground">{abrev(l.desc_tipo_toma)}</span>
                </td>
                <td className="py-1.5 text-right font-semibold tabular-nums">{n0(l.valor)}</td>
                <td className={cn("whitespace-nowrap py-1.5 text-center text-[11px] font-semibold", tonoValidacion(l))}>
                  {l.etiqueta_validacion}
                </td>
                {(["partida", "llegada"] as const).map((rol) => (
                  <td key={rol} className={cn("py-1.5 text-center", rol === "llegada" && "pr-2")}>
                    {l.usable ? (
                      <BotonPL rol={rol === "partida" ? "P" : "L"} activa={seleccion[rol] === l} puede={puedeGestionar} onClick={() => onToggle(rol, l)} />
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </td>
                ))}
              </tr>
              <Divisoria lectura={l} />
            </Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Fila({ label, children, destacado }: { label: string; children: React.ReactNode; destacado?: boolean }) {
  return (
    <>
      <dt className="text-muted-foreground">{label}</dt>
      <dd className={cn("text-right tabular-nums", destacado && "font-heading text-base font-extrabold text-brand-orange")}>{children}</dd>
    </>
  );
}

function Aviso({ tono, children }: { tono: "warning" | "info"; children: React.ReactNode }) {
  const color = tono === "warning" ? "bg-warning/10 text-warning" : "bg-info/10 text-info";
  return <p className={cn("col-span-2 rounded-[6px] px-2 py-1.5 text-[11px]", color)}>{children}</p>;
}

function Referencia({ rol, lectura }: { rol: "P" | "L"; lectura: CandidatoLectura | null }) {
  return (
    <Fila label={rol}>
      {lectura ? `${fechaCorta(lectura.fecha)}  T${lectura.tipo_toma}  →  ${n0(lectura.valor)}` : <span className="text-muted-foreground">— Sin seleccionar —</span>}
    </Fila>
  );
}

/** Días activos con los calendario al lado si el receso los redujo. */
function DiasConReceso({ activos, calendario, ajusto }: { activos: number | null; calendario: number | null; ajusto: boolean }) {
  if (activos === null) return <>—</>;
  return (
    <>
      {activos}
      {ajusto && calendario !== null && calendario !== activos && <span className="text-info"> (de {calendario} cal.)</span>}
    </>
  );
}

interface CalculoProps {
  seleccion: Seleccion;
  preview: RecalcularCandidatoResponse | null;
  errorPreview: string | null;
  fechaObjetivo: string | null;
  ultimoFacturado: number | null;
}

export function ProyeccionCalculoPanel({ seleccion, preview, errorPreview, fechaObjetivo, ultimoFacturado }: CalculoProps) {
  const { partida, llegada } = seleccion;
  const invertido = !!partida && !!llegada && partida.fecha >= llegada.fecha;
  const diasCal = diasParCalendario(seleccion);
  const diasObjCal = llegada && fechaObjetivo ? diasEntre(llegada.fecha, fechaObjetivo) : null;
  const diasPar = preview?.dias_par_pl ?? null;
  const diasObj = preview?.dias_proyectados ?? null;
  const ajusto = !!preview && ((diasCal !== null && diasPar !== null && diasPar < diasCal) || (diasObjCal !== null && diasObj !== null && diasObj < diasObjCal));
  const delta = partida && llegada && !invertido ? llegada.valor - partida.valor : null;
  const tasa = preview?.tasa_diaria ?? null;
  return (
    <dl className="grid grid-cols-2 gap-y-1.5 text-[12.5px]">
      <Referencia rol="P" lectura={partida} />
      <Referencia rol="L" lectura={llegada} />
      {invertido && <Aviso tono="warning">⚠ Partida posterior a Llegada — intercambiá las selecciones</Aviso>}
      {!invertido && diasCal !== null && diasCal < 15 && <Aviso tono="warning">⚠ Separación {diasCal} días — mínimo recomendado: 15 días</Aviso>}
      {ajusto && <Aviso tono="info">↺ Ajustado por receso — se descuentan los días sin uso</Aviso>}
      {diasObj !== null && diasObj < 0 && (
        <Aviso tono="warning">
          ⚠ La Llegada es posterior a la fecha objetivo — el estimado se interpola hacia atrás (queda por debajo de la lectura)
        </Aviso>
      )}
      {errorPreview && <Aviso tono="warning">{errorPreview}</Aviso>}
      <Fila label="Δ días (P → L)"><DiasConReceso activos={diasPar} calendario={diasCal} ajusto={ajusto} /></Fila>
      <Fila label="Δ contador">{n0(delta)}</Fila>
      <Fila label="Promedio diario">{n2(tasa)} /día</Fila>
      <Fila label="Imp. 30d">{n0(tasa === null ? null : redondeoBancario(tasa * 30))}</Fila>
      <Fila label="Días L → fecha obj."><DiasConReceso activos={diasObj} calendario={diasObjCal} ajusto={ajusto} /></Fila>
      <Fila label="Estim. propuesto" destacado>{n0(preview?.estim_propuesto)}</Fila>
      <Fila label="Últ. facturado">{n0(ultimoFacturado)}</Fila>
      <Fila label="Impresiones" destacado>{n0(preview?.impresiones)}</Fila>
    </dl>
  );
}
