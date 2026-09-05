"use client";

import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { cn } from "@/shared/utils/cn";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { useSession } from "@/services/session-provider";
import { proyeccionApi } from "../api/proyeccion-api";
import type {
  CandidatoLectura,
  CandidatosEquipo,
  FilaProyeccion,
  MetodoForzado,
  SolicitudTableroReal,
} from "../types/proyeccion";
import { ProyeccionBoxplot } from "./proyeccion-boxplot";

interface ProyeccionCandidatosDrawerProps {
  fila: FilaProyeccion;
  solicitud: SolicitudTableroReal | undefined;
  onClose: () => void;
  onCambio: () => void;
}

interface Seleccion {
  partida: CandidatoLectura | null;
  llegada: CandidatoLectura | null;
}

function formatFecha(iso: string): string {
  const [y, m, d] = iso.split("-");
  return `${d}/${m}/${y}`;
}

const numberFormat = new Intl.NumberFormat("es-AR");

export function ProyeccionCandidatosDrawer({
  fila,
  solicitud,
  onClose,
  onCambio,
}: ProyeccionCandidatosDrawerProps) {
  const { can } = useSession();
  const puedeGestionar = can("contadores", "manage");
  const [datos, setDatos] = useState<CandidatosEquipo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [seleccion, setSeleccion] = useState<Seleccion>({ partida: null, llegada: null });
  const [calculo, setCalculo] = useState<{ estim: number | null; impresiones: number | null } | null>(null);
  const [forzado, setForzado] = useState<{
    estim: number | null;
    impresiones: number | null;
    fuente: string;
    metodoDetalle: string;
  } | null>(null);
  const [forzando, setForzando] = useState<MetodoForzado | null>(null);
  const [nota, setNota] = useState("");
  const [guardando, setGuardando] = useState(false);

  // El padre monta este componente con `key={id_maquina-clase}` (ver
  // proyeccion-view.tsx): un cambio de equipo/clase remonta el componente en
  // vez de resetear estado a mano en un efecto (evita setState síncrono en
  // el cuerpo del efecto, ver react-hooks/set-state-in-effect).
  useEffect(() => {
    proyeccionApi
      .getCandidatos(fila.id_maquina, fila.clase)
      .then(setDatos)
      .catch(() => {
        setError("No se pudo cargar el panel de candidatos — puede ser lenta o falló la conexión a Siges.");
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!seleccion.partida || !seleccion.llegada) return;
    let cancelado = false;
    void proyeccionApi
      .recalcularCandidato({
        id_maquina: fila.id_maquina,
        clase: fila.clase,
        partida_fecha: seleccion.partida.fecha,
        partida_valor: seleccion.partida.valor,
        partida_tipo_toma: seleccion.partida.tipo_toma,
        llegada_fecha: seleccion.llegada.fecha,
        llegada_valor: seleccion.llegada.valor,
        llegada_tipo_toma: seleccion.llegada.tipo_toma,
        ...(solicitud
          ? {
              nro_proceso: solicitud.nroProceso,
              id_grupo_economico: solicitud.idGrupoEconomico,
              id_anexo: solicitud.idAnexo,
              fecha_objetivo: solicitud.fechaObjetivo,
            }
          : {}),
      })
      .then((r) => {
        if (!cancelado) setCalculo({ estim: r.estim_propuesto, impresiones: r.impresiones });
      })
      .catch(() => {
        if (!cancelado) setCalculo(null);
      });
    return () => {
      cancelado = true;
    };
  }, [seleccion, fila.id_maquina, fila.clase, solicitud]);

  const calculoVisible = seleccion.partida && seleccion.llegada ? calculo : null;

  const forzar = async (metodo: MetodoForzado) => {
    setSeleccion({ partida: null, llegada: null });
    setForzando(metodo);
    try {
      const r = await proyeccionApi.forzarMetodo({
        id_maquina: fila.id_maquina,
        clase: fila.clase,
        metodo,
        ...(solicitud
          ? {
              nro_proceso: solicitud.nroProceso,
              id_grupo_economico: solicitud.idGrupoEconomico,
              id_anexo: solicitud.idAnexo,
              fecha_objetivo: solicitud.fechaObjetivo,
            }
          : {}),
      });
      setForzado({
        estim: r.estim_propuesto,
        impresiones: r.impresiones,
        fuente: r.fuente,
        metodoDetalle: r.metodo_detalle,
      });
    } catch {
      setForzado(null);
    } finally {
      setForzando(null);
    }
  };

  const accion = async (fn: () => Promise<void>) => {
    setGuardando(true);
    try {
      await fn();
      onCambio();
    } finally {
      setGuardando(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex justify-end">
      <div className="absolute inset-0 bg-background/70 backdrop-blur-sm animate-fade-in" onClick={onClose} />
      <div className="relative flex w-full max-w-[420px] flex-col rounded-l-[20px] border-l border-border bg-card shadow-2xl animate-slide-from-right">
        <div className="relative border-b border-border p-6 pb-4">
          <button onClick={onClose} aria-label="Cerrar" className="absolute right-5 top-5 text-muted-foreground hover:text-foreground">
            <X className="h-4 w-4" />
          </button>
          <p className="text-[10.5px] font-bold uppercase tracking-[.08em] text-brand-orange">
            Candidatos · Cl. {fila.clase}
          </p>
          <h2 className="font-heading text-lg font-bold">{fila.nro_serie}</h2>
          <p className="text-xs text-muted-foreground">
            {fila.empresa} · {fila.sucursal} · Sector {fila.sector} · {fila.modelo} · {fila.tecnologia}
            {datos?.velocidad_ppm ? ` · ${datos.velocidad_ppm} ppm` : ""}
          </p>
        </div>

        <div className="flex-1 overflow-y-auto p-6 thin-scrollbar">
          <p className="mb-2 text-[10.5px] font-bold uppercase tracking-wide text-muted-foreground">
            Últimas lecturas
          </p>
          {error ? (
            <p className="text-sm text-warning">{error}</p>
          ) : !datos ? (
            <p className="text-sm text-muted-foreground">Cargando…</p>
          ) : (
            <table className="w-full text-xs">
              <thead>
                <tr className="text-left text-[10px] uppercase text-muted-foreground">
                  <th className="py-1.5">Fecha</th>
                  <th className="py-1.5">Tipo</th>
                  <th className="py-1.5 text-right">Valor</th>
                  <th className="py-1.5">Valid.</th>
                  <th className="py-1.5">P</th>
                  <th className="py-1.5">L</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {datos.lecturas.map((lectura) => (
                  <tr key={`${lectura.fecha}-${lectura.tipo_toma}-${lectura.valor}`}>
                    <td className="py-2">{formatFecha(lectura.fecha)}</td>
                    <td className="py-2">T{lectura.tipo_toma}</td>
                    <td className="py-2 text-right tabular-nums">{numberFormat.format(lectura.valor)}</td>
                    <td className={cn("py-2", lectura.valido ? "text-success" : "text-warning")}>
                      {lectura.valido ? "✓ ok" : lectura.motivo_invalidez}
                    </td>
                    <td className="py-2">
                      <button
                        disabled={!puedeGestionar}
                        onClick={() => {
                          setForzado(null);
                          setSeleccion((s) => ({ ...s, partida: lectura }));
                        }}
                        className={cn(
                          "h-6 w-6 rounded-[6px] border border-border bg-muted text-[10px] font-extrabold disabled:opacity-40",
                          seleccion.partida === lectura && "border-success bg-success text-background",
                        )}
                      >
                        P
                      </button>
                    </td>
                    <td className="py-2">
                      <button
                        disabled={!puedeGestionar}
                        onClick={() => {
                          setForzado(null);
                          setSeleccion((s) => ({ ...s, llegada: lectura }));
                        }}
                        className={cn(
                          "h-6 w-6 rounded-[6px] border border-border bg-muted text-[10px] font-extrabold disabled:opacity-40",
                          seleccion.llegada === lectura && "border-info bg-info text-background",
                        )}
                      >
                        L
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {!error && (
            <>
              <p className="mb-2 mt-6 text-[10.5px] font-bold uppercase tracking-wide text-muted-foreground">
                Cálculo
              </p>
              <dl className="grid grid-cols-2 gap-y-2 text-[12.5px]">
                <dt className="text-muted-foreground">P → L</dt>
                <dd className="text-right tabular-nums">
                  {seleccion.partida ? formatFecha(seleccion.partida.fecha) : "—"} →{" "}
                  {seleccion.llegada ? formatFecha(seleccion.llegada.fecha) : "—"}
                </dd>
                <dt className="text-muted-foreground">Estim. propuesto</dt>
                <dd className="text-right font-heading text-base font-extrabold text-brand-orange tabular-nums">
                  {calculoVisible?.estim !== null && calculoVisible?.estim !== undefined
                    ? numberFormat.format(calculoVisible.estim)
                    : forzado?.estim !== null && forzado?.estim !== undefined
                      ? numberFormat.format(forzado.estim)
                      : "—"}
                </dd>
                <dt className="text-muted-foreground">Impresiones del período</dt>
                <dd className="text-right font-heading text-base font-extrabold text-brand-orange tabular-nums">
                  {calculoVisible?.impresiones !== null && calculoVisible?.impresiones !== undefined
                    ? numberFormat.format(calculoVisible.impresiones)
                    : forzado?.impresiones !== null && forzado?.impresiones !== undefined
                      ? numberFormat.format(forzado.impresiones)
                      : "—"}
                </dd>
                {!calculoVisible && forzado && (
                  <>
                    <dt className="text-muted-foreground">Método forzado</dt>
                    <dd className="text-right text-xs text-muted-foreground">{forzado.metodoDetalle}</dd>
                  </>
                )}
              </dl>

              {puedeGestionar && (
                <div className="mt-3 flex gap-2">
                  <BrandButton
                    variant="outline"
                    className="flex-1 text-xs"
                    loading={forzando === "entre_reales"}
                    disabled={forzando !== null}
                    onClick={() => forzar("entre_reales")}
                  >
                    Forzar entre reales
                  </BrandButton>
                  <BrandButton
                    variant="outline"
                    className="flex-1 text-xs"
                    loading={forzando === "cascada_parque"}
                    disabled={forzando !== null}
                    onClick={() => forzar("cascada_parque")}
                  >
                    Forzar cascada de parque
                  </BrandButton>
                </div>
              )}
            </>
          )}

          {datos?.boxplot && (
            <>
              <p className="mb-2 mt-6 text-[10.5px] font-bold uppercase tracking-wide text-muted-foreground">
                Parque de referencia (cliente · modelo)
              </p>
              <ProyeccionBoxplot data={datos.boxplot} />
            </>
          )}

          {puedeGestionar && (
            <div className="mt-6">
              <label className="mb-1.5 block text-[10.5px] font-bold uppercase tracking-wide text-muted-foreground">
                Observación
              </label>
              <textarea
                value={nota}
                onChange={(e) => setNota(e.target.value)}
                rows={2}
                className="w-full rounded-[8px] border border-border bg-muted p-2 text-xs"
                placeholder="Texto libre para dejar documentado…"
              />
            </div>
          )}
        </div>

        {puedeGestionar && (
          <div className="flex gap-2 border-t border-border p-4">
            <BrandButton
              className="flex-1"
              loading={guardando}
              onClick={() => accion(() => proyeccionApi.aceptarPropuesta(fila.id_maquina, fila.clase))}
            >
              ✓ Aceptar
            </BrandButton>
            <BrandButton
              variant="outline"
              loading={guardando}
              onClick={() => accion(() => proyeccionApi.marcarPendiente(fila.id_maquina, fila.clase))}
            >
              Marcar pendiente
            </BrandButton>
            <BrandButton
              variant="outline"
              disabled={!nota.trim()}
              loading={guardando}
              onClick={() => accion(() => proyeccionApi.agregarNota(fila.id_maquina, fila.clase, nota.trim()))}
            >
              + Nota
            </BrandButton>
          </div>
        )}
      </div>
    </div>
  );
}
