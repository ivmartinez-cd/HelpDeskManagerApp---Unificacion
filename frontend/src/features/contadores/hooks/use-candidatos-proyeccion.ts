import { useEffect, useMemo, useState } from "react";
import { mensajeError, proyeccionApi, seleccionBody } from "../api/proyeccion-api";
import type {
  CandidatoLectura,
  CandidatosEquipo,
  FilaProyeccion,
  LecturaElegidaBody,
  ContextoProceso,
  RecalcularCandidatoBody,
  RecalcularCandidatoResponse,
} from "../types/proyeccion";
import { diasEntre } from "../components/proyeccion-formato";

/** Estado del panel de candidatos (`PanelCandidatos.razor` v1.7): lecturas,
 * Partida/Llegada elegidas y la vista previa del motor para esa pareja.
 *
 * - Al llegar las lecturas se preseleccionan P/L con las que usó el motor
 *   (último real = L, real anterior = P), si el tablero las informa
 *   (`PreseleccionarPL`): con esa pareja el botón principal es "Aceptar P/L
 *   manual" y no se muestra "Sugerencia actual".
 * - Volver a tocar P o L sobre la misma lectura la deselecciona.
 * - La vista previa solo se pide si el motor la calcularía (15 días
 *   calendario o más y Llegada no menor que Partida). */

export interface Seleccion {
  partida: CandidatoLectura | null;
  llegada: CandidatoLectura | null;
}

export function claveLectura(l: CandidatoLectura, i: number): string {
  return l.id_contador !== null ? `c${l.id_contador}` : `i${i}`;
}

function buscar(lecturas: CandidatoLectura[], fecha?: string | null, tipo?: number | null) {
  if (!fecha) return null;
  return lecturas.find((c) => c.fecha === fecha && c.tipo_toma === (tipo ?? 0)) ?? null;
}

function preseleccion(fila: FilaProyeccion, lecturas: CandidatoLectura[]): Seleccion {
  return {
    llegada: buscar(lecturas, fila.ultimo_real_fecha, fila.ultimo_real_tipo),
    partida: buscar(lecturas, fila.real_anterior_fecha, fila.real_anterior_tipo),
  };
}

export function elegida(l: CandidatoLectura): LecturaElegidaBody {
  return { fecha: l.fecha, valor: l.valor, tipo_toma: l.tipo_toma, id_contador: l.id_contador, para_facturar: l.para_facturar };
}

/** Días calendario P → L, `null` sin pareja o con el orden invertido. */
export function diasParCalendario({ partida, llegada }: Seleccion): number | null {
  if (!partida || !llegada || partida.fecha >= llegada.fecha) return null;
  return diasEntre(partida.fecha, llegada.fecha);
}

/** Guarda de `RecalcularConPL`: 15 días calendario o más y L ≥ P. Sin ella
 * el motor no da vista previa. */
function hayVistaPrevia(s: Seleccion): boolean {
  const dias = diasParCalendario(s);
  return dias !== null && dias >= 15 && s.llegada!.valor >= s.partida!.valor;
}

/** `PLValida` (habilita "Aceptar P/L manual"): además, Δ contador positivo. */
export function plValida(s: Seleccion): boolean {
  return hayVistaPrevia(s) && s.llegada!.valor - s.partida!.valor > 0;
}

function cuerpoRecalculo(fila: FilaProyeccion, s: Seleccion, contexto: ContextoProceso): RecalcularCandidatoBody {
  const { partida, llegada } = s as { partida: CandidatoLectura; llegada: CandidatoLectura };
  return {
    id_maquina: fila.id_maquina,
    clase: fila.clase,
    partida_fecha: partida.fecha,
    partida_valor: partida.valor,
    partida_tipo_toma: partida.tipo_toma,
    partida_id_contador: partida.id_contador,
    partida_para_facturar: partida.para_facturar,
    llegada_fecha: llegada.fecha,
    llegada_valor: llegada.valor,
    llegada_tipo_toma: llegada.tipo_toma,
    llegada_id_contador: llegada.id_contador,
    llegada_para_facturar: llegada.para_facturar,
    ...seleccionBody(contexto),
  };
}

/** Lecturas del equipo, una sola vez: el padre remonta el panel con `key`
 * por equipo/clase. `onCargadas` recibe las lecturas para preseleccionar. */
function useLecturas(fila: FilaProyeccion, contexto: ContextoProceso, onCargadas: (l: CandidatoLectura[]) => void) {
  const [datos, setDatos] = useState<CandidatosEquipo | null>(null);
  const [errorCarga, setErrorCarga] = useState<string | null>(null);
  useEffect(() => {
    proyeccionApi
      .getCandidatos(fila.id_maquina, fila.clase, contexto)
      .then((d) => {
        setDatos(d);
        onCargadas(d.lecturas);
      })
      .catch((err) => setErrorCarga(mensajeError(err, "No se pudieron cargar las lecturas del equipo.")));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return { datos, errorCarga };
}

type Resultado<T> = { para: Seleccion; valor: T } | null;

/** Vista previa del motor (`RecomputarPreview`) para la pareja elegida; el
 * resultado solo vale mientras la selección siga siendo la misma. */
function useVistaPrevia(fila: FilaProyeccion, contexto: ContextoProceso, seleccion: Seleccion) {
  const [preview, setPreview] = useState<Resultado<RecalcularCandidatoResponse>>(null);
  const [errorPreview, setErrorPreview] = useState<Resultado<string>>(null);
  useEffect(() => {
    if (!hayVistaPrevia(seleccion)) return;
    let cancelado = false;
    proyeccionApi
      .recalcularCandidato(cuerpoRecalculo(fila, seleccion, contexto))
      .then((valor) => !cancelado && setPreview({ para: seleccion, valor }))
      .catch((err) => !cancelado && setErrorPreview({ para: seleccion, valor: mensajeError(err, "No se pudo calcular la vista previa.") }));
    return () => {
      cancelado = true;
    };
  }, [seleccion, fila, contexto]);
  return useMemo(
    () => ({
      preview: preview?.para === seleccion ? preview.valor : null,
      errorPreview: errorPreview?.para === seleccion ? errorPreview.valor : null,
    }),
    [preview, errorPreview, seleccion],
  );
}

export function useCandidatosProyeccion(fila: FilaProyeccion, contexto: ContextoProceso) {
  const [seleccion, setSeleccion] = useState<Seleccion>({ partida: null, llegada: null });
  const { datos, errorCarga } = useLecturas(fila, contexto, (lecturas) => setSeleccion(preseleccion(fila, lecturas)));
  const vistaPrevia = useVistaPrevia(fila, contexto, seleccion);
  // `TogglePartida`/`ToggleLlegada`: la misma lectura otra vez la deselecciona.
  const toggle = (rol: keyof Seleccion, lectura: CandidatoLectura) =>
    setSeleccion((s) => ({ ...s, [rol]: s[rol] === lectura ? null : lectura }));
  return { datos, errorCarga, seleccion, toggle, ...vistaPrevia };
}
