"use client";

import { useEffect, useState } from "react";
import { X } from "lucide-react";
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
import {
  ProyeccionCalculoPanel,
  ProyeccionLecturasTabla,
  type Calculo,
  type Seleccion,
} from "./proyeccion-candidatos-panels";

interface ProyeccionCandidatosDrawerProps {
  fila: FilaProyeccion;
  solicitud: SolicitudTableroReal | undefined;
  onClose: () => void;
  onCambio: () => void;
}

function solicitudReal(solicitud: SolicitudTableroReal | undefined) {
  if (!solicitud) return {};
  return {
    nro_proceso: solicitud.nroProceso,
    id_grupo_economico: solicitud.idGrupoEconomico,
    id_anexo: solicitud.idAnexo,
    fecha_objetivo: solicitud.fechaObjetivo,
  };
}

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
  const [calculo, setCalculo] = useState<Calculo | null>(null);
  const [forzado, setForzado] = useState<Calculo | null>(null);
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
        ...solicitudReal(solicitud),
      })
      .then((r) => {
        if (!cancelado) {
          setCalculo({
            estim: r.estim_propuesto,
            impresiones: r.impresiones,
            tipoToma: r.tipo_toma,
            fuente: r.fuente,
            metodoDetalle: r.metodo_detalle,
          });
        }
      })
      .catch(() => {
        if (!cancelado) setCalculo(null);
      });
    return () => {
      cancelado = true;
    };
  }, [seleccion, fila.id_maquina, fila.clase, solicitud]);

  const calculoVisible = seleccion.partida && seleccion.llegada ? calculo : null;

  const elegir = (rol: "partida" | "llegada", lectura: CandidatoLectura) => {
    setForzado(null);
    setSeleccion((s) => ({ ...s, [rol]: lectura }));
  };

  const forzar = async (metodo: MetodoForzado) => {
    setSeleccion({ partida: null, llegada: null });
    setForzando(metodo);
    try {
      const r = await proyeccionApi.forzarMetodo({
        id_maquina: fila.id_maquina,
        clase: fila.clase,
        metodo,
        ...solicitudReal(solicitud),
      });
      setForzado({
        estim: r.estim_propuesto,
        impresiones: r.impresiones,
        tipoToma: r.tipo_toma,
        fuente: r.fuente,
        metodoDetalle: r.metodo_detalle,
      });
    } catch {
      setForzado(null);
    } finally {
      setForzando(null);
    }
  };

  // Lo que el operador ve en pantalla al momento de aceptar: P/L manual si
  // hay una pareja elegida, sino el método forzado si hay uno vigente, sino
  // ninguno (confirma el automático).
  const manualParaAceptar = calculoVisible ?? forzado;

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
          <ProyeccionLecturasTabla
            datos={datos}
            error={error}
            seleccion={seleccion}
            puedeGestionar={puedeGestionar}
            onElegir={elegir}
          />

          {!error && (
            <ProyeccionCalculoPanel
              seleccion={seleccion}
              calculoVisible={calculoVisible}
              forzado={forzado}
              puedeGestionar={puedeGestionar}
              forzando={forzando}
              onForzar={forzar}
            />
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
              onClick={() =>
                accion(() =>
                  proyeccionApi.aceptarPropuesta(
                    fila.id_maquina,
                    fila.clase,
                    manualParaAceptar
                      ? {
                          contador_propuesto: manualParaAceptar.estim,
                          tipo_toma: manualParaAceptar.tipoToma,
                          fuente: manualParaAceptar.fuente,
                          metodo_detalle: manualParaAceptar.metodoDetalle,
                        }
                      : undefined,
                  ),
                )
              }
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
