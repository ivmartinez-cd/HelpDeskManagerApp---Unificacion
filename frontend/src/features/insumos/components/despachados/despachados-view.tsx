"use client";

import { useCallback, useMemo, useState } from "react";
import { AlertTriangle } from "lucide-react";
import { toast } from "sonner";
import { useSession } from "@/services/session-provider";
import type { DateRange } from "@/shared/types/date-range";
import { despachadosApi } from "../../api/despachados-api";
import { useDebouncedValue } from "../../hooks/use-debounced-value";
import { useDespachoDetalle } from "../../hooks/use-despacho-detalle";
import { useDespachadosActualizacion } from "../../hooks/use-despachados-actualizacion";
import { mensajeDeError, useDespachadosListado } from "../../hooks/use-despachados-listado";
import { useDespachadosTablero } from "../../hooks/use-despachados-tablero";
import type { FiltrosDespachos, NuevaAccionDespacho } from "../../types/despachados";
import { DespachadosCards, TARJETAS } from "./despachados-cards";
import { DespachadosHeader } from "./despachados-header";
import { DespachoDrawer } from "./despacho-drawer";
import { DespachosFilters } from "./despachos-filters";
import { DespachosTable, TAMANIOS_PAGINA } from "./despachos-table";
import { RegistrarAccionModal, type ObjetivoAccion } from "./registrar-accion-modal";
import { RequierenAccionTable } from "./requieren-accion-table";

/** Pantalla `/insumos/despachados`: seguimiento de los envíos por OCA.
 *
 * Todo sale de la base de HDM (lo que el job de fondo ya consultó a OCA); la
 * pantalla nunca espera a OCA. "Actualizar ahora" lanza la corrida en el
 * backend y la sigue por polling (`useDespachadosActualizacion`); al terminar
 * se refresca todo. Las tarjetas y el `<select>` de color comparten el mismo
 * filtro (`colores`). */
export function DespachadosView() {
  const { user, can } = useSession();
  const canUpdate = user.isSuperadmin || can("insumos", "update");

  const [colores, setColores] = useState("");
  const [texto, setTexto] = useState("");
  const [operativa, setOperativa] = useState("");
  const [rango, setRango] = useState<DateRange | null>(null);
  const [page, setPage] = useState(1);
  const [size, setSize] = useState<number>(TAMANIOS_PAGINA[0]);
  const [guiaAbierta, setGuiaAbierta] = useState<string | null>(null);
  const [objetivo, setObjetivo] = useState<ObjetivoAccion | null>(null);

  const textoDebounced = useDebouncedValue(texto.trim(), 350);
  const filtros = useMemo<FiltrosDespachos>(
    () => ({
      texto: textoDebounced,
      colores,
      operativa,
      remitoDesde: rango?.startDate ?? null,
      remitoHasta: rango?.endDate ?? null,
    }),
    [textoDebounced, colores, operativa, rango],
  );

  // Cualquier cambio de filtro vuelve a la página 1 (ajuste durante el render,
  // mismo patrón que historial-view).
  const claveFiltros = `${textoDebounced}|${colores}|${operativa}|${rango?.startDate}|${rango?.endDate}|${size}`;
  const [claveAnterior, setClaveAnterior] = useState(claveFiltros);
  if (claveFiltros !== claveAnterior) {
    setClaveAnterior(claveFiltros);
    setPage(1);
  }

  const tablero = useDespachadosTablero();
  const listado = useDespachadosListado({ filtros, page, size });
  const detalle = useDespachoDetalle(guiaAbierta);

  const refrescarTodo = useCallback(() => {
    void tablero.reload();
    void listado.reload();
    if (guiaAbierta) void detalle.reload();
  }, [tablero, listado, detalle, guiaAbierta]);

  const actualizacion = useDespachadosActualizacion(refrescarTodo);

  const seleccionarTarjeta = (clave: string) => {
    setColores(clave);
    if (!clave) return;
    const reducir = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    document
      .getElementById("despachados-todos")
      ?.scrollIntoView({ behavior: reducir ? "auto" : "smooth", block: "start" });
  };

  const limpiar = () => {
    setColores("");
    setTexto("");
    setOperativa("");
    setRango(null);
  };

  const guardarAccion = async (guia: string, body: NuevaAccionDespacho) => {
    await despachadosApi.registrarAccion(guia, body);
    setObjetivo(null);
    toast.success(body.cerrarAlerta ? "Acción registrada y alerta cerrada" : "Acción registrada");
    refrescarTodo();
  };

  const cerrarAlerta = async (guia: string) => {
    try {
      await despachadosApi.cerrarAlerta(guia);
      toast.success('Alerta cerrada. El envío sale de "Requieren acción".');
      refrescarTodo();
    } catch (err) {
      toast.error(mensajeDeError(err, "No se pudo cerrar la alerta"));
    }
  };

  const tarjeta = TARJETAS.find((t) => t.clave === colores);
  const subtitulo = tarjeta
    ? `Filtrado por la tarjeta "${tarjeta.label}". Tocala de nuevo para ver todos.`
    : "Remitos despachados por OCA en los últimos 30 días.";
  const error = tablero.error ?? listado.error;

  return (
    <div className="flex flex-col gap-6 px-4 py-5 sm:px-7 sm:py-7">
      <DespachadosHeader
        estado={actualizacion.estado}
        enCurso={actualizacion.enCurso}
        canUpdate={canUpdate}
        onActualizar={() => void actualizacion.actualizar()}
      />

      {error && (
        <div role="alert" className="flex items-start gap-2.5 rounded-[10px] border border-[rgba(239,68,68,.25)] bg-[rgba(239,68,68,.07)] p-3.5 font-body text-[13px] text-[#991b1b] dark:text-[#fca5a5]">
          <AlertTriangle className="h-4 w-4 flex-none" aria-hidden="true" />
          {error}
        </div>
      )}

      <DespachadosCards resumen={tablero.resumen} seleccion={colores} onSeleccion={seleccionarTarjeta} />

      <RequierenAccionTable
        filas={tablero.bandeja}
        loading={tablero.loading}
        seleccionada={guiaAbierta}
        canUpdate={canUpdate}
        onAbrir={setGuiaAbierta}
        onRegistrar={(f) => setObjetivo({ guia: f.guia, cliente: f.cliente, alertaAbierta: f.alertaAbierta })}
      />

      <DespachosTable
        subtitulo={subtitulo}
        filtros={
          <DespachosFilters
            texto={texto}
            onTexto={setTexto}
            colores={colores}
            onColores={setColores}
            operativa={operativa}
            onOperativa={setOperativa}
            operativas={tablero.resumen?.operativas ?? []}
            rango={rango}
            onRango={setRango}
            onLimpiar={limpiar}
          />
        }
        filas={listado.filas}
        total={listado.total}
        loading={listado.loading}
        page={page}
        size={size}
        onPage={setPage}
        onSize={setSize}
        seleccionada={guiaAbierta}
        onAbrir={setGuiaAbierta}
      />

      <DespachoDrawer
        guia={guiaAbierta}
        estado={detalle}
        canUpdate={canUpdate}
        onClose={() => setGuiaAbierta(null)}
        onRegistrar={(d) =>
          setObjetivo({ guia: d.envio.guia, cliente: d.envio.cliente, alertaAbierta: d.envio.alertaAbierta })
        }
        onCerrarAlerta={cerrarAlerta}
      />

      <RegistrarAccionModal objetivo={objetivo} onClose={() => setObjetivo(null)} onGuardar={guardarAccion} />
    </div>
  );
}
