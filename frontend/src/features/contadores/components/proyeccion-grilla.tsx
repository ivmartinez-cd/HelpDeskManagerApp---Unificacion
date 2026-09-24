"use client";

import { useCallback, useMemo, useState } from "react";
import { useTableSort } from "@/shared/hooks/use-table-sort";
import { useExportCsvProyeccion } from "../hooks/use-export-csv-proyeccion";
import type { ContextoProceso, FilaProyeccion, TableroProyeccion } from "../types/proyeccion";
import { ProyeccionCandidatosDrawer } from "./proyeccion-candidatos-drawer";
import { ProyeccionDetalleModelo } from "./proyeccion-detalle-modelo";
import { ProyeccionDetalleModeloHistorico } from "./proyeccion-detalle-modelo-historico";
import { ProyeccionHistorialModal } from "./proyeccion-historial-modal";
import { ProyeccionLeyenda } from "./proyeccion-leyenda";
import { ProyeccionKpis } from "./proyeccion-resumen";
import { ordenarGrupos, PROYECCION_DESC_PRIMERO, PROYECCION_SORT_KEYS, type ProyeccionSortKey } from "./proyeccion-orden";
import { agruparPorEquipo, ProyeccionTabla } from "./proyeccion-tabla";
import { aplicaFiltro, coincideBusqueda, type FiltroChip, ProyeccionToolbar } from "./proyeccion-toolbar";

/** `GrillaEstimacion.razor` (v1.7) de un tablero ya cargado. El padre la
 * monta solo con tablero, así que "Cargar" o cambiar de proceso la
 * recrea: vuelve al chip "Todos", sin búsqueda, orden Ubicación ↑, sin
 * panel abierto. Una relectura tras una acción la
 * conserva. "Descartar y empezar limpio" (`descartes`) cierra el panel. */

interface ProyeccionGrillaProps {
  tablero: TableroProyeccion;
  contexto: ContextoProceso;
  descartes: number;
  puedeOperar: boolean;
  recargar: () => void;
}

function Alerta({ titulo, detalle }: { titulo: string; detalle: string }) {
  return (
    <div className="rounded-[8px] bg-destructive/10 px-4 py-3 font-body text-xs text-destructive">
      <strong>{titulo}</strong>
      <p className="text-muted-foreground">{detalle}</p>
    </div>
  );
}

function usePanel(descartes: number, recargar: () => void) {
  const [abierto, setAbierto] = useState<{ fila: FilaProyeccion; descartes: number } | null>(null);
  const panel = abierto?.descartes === descartes ? abierto.fila : null;
  // Un segundo clic en el ojo de la misma fila cierra el panel.
  const abrir = (fila: FilaProyeccion) =>
    setAbierto(panel?.id_maquina === fila.id_maquina && panel.clase === fila.clase ? null : { fila, descartes });
  const cerrar = useCallback(() => setAbierto(null), []);
  const trasAccion = useCallback(() => {
    setAbierto(null);
    recargar();
  }, [recargar]);
  return { panel, abrir, cerrar, trasAccion };
}

export function ProyeccionGrilla({ tablero, contexto, descartes, puedeOperar, recargar }: ProyeccionGrillaProps) {
  const [filtro, setFiltro] = useState<FiltroChip>("todos");
  const [busqueda, setBusqueda] = useState("");
  const [historial, setHistorial] = useState<FilaProyeccion | null>(null);
  const { sort, toggleSort } = useTableSort<ProyeccionSortKey>({
    initial: { key: "ubicacion", direction: "asc" },
    keys: PROYECCION_SORT_KEYS,
    descFirstKeys: PROYECCION_DESC_PRIMERO,
  });
  const panel = usePanel(descartes, recargar);
  const exportCsv = useExportCsvProyeccion(contexto);
  const filasVisibles = useMemo(
    () => tablero.filas.filter((f) => aplicaFiltro(f, filtro) && coincideBusqueda(f, busqueda)),
    [tablero, filtro, busqueda],
  );
  const grupos = useMemo(() => ordenarGrupos(agruparPorEquipo(filasVisibles), sort), [filasVisibles, sort]);
  // La fecha con la que se calculó la grilla (el modo ejemplo usa la suya).
  const fechaCargada = contexto.solicitud?.fechaObjetivo ?? null;

  if (tablero.filas.length === 0) {
    return <p className="text-sm text-muted-foreground">Sin equipos para mostrar en este proceso.</p>;
  }
  return (
    <>
      <ProyeccionKpis tablero={tablero} />
      <ProyeccionDetalleModelo filas={tablero.filas} />
      <ProyeccionDetalleModeloHistorico filas={tablero.filas} />
      <ProyeccionToolbar
        filas={tablero.filas}
        filtro={filtro}
        onFiltro={setFiltro}
        busqueda={busqueda}
        onBusqueda={setBusqueda}
        exportar={{
          visible: puedeOperar,
          habilitado: !!contexto.solicitud,
          exportando: exportCsv.exportando,
          totalFilas: tablero.filas.length,
          estimados: tablero.resumen.estimados,
          onExportar: exportCsv.exportar,
        }}
      />
      {exportCsv.error && <Alerta titulo="No se pudo exportar el CSV." detalle={exportCsv.error} />}
      <ProyeccionTabla
        grupos={grupos}
        sort={sort}
        onToggleSort={toggleSort}
        activa={panel.panel}
        onVerCandidatos={panel.abrir}
        onVerHistorial={setHistorial}
        fechaObjetivo={fechaCargada}
      />
      {grupos.length === 0 && (
        <p className="text-center text-sm text-muted-foreground">Sin equipos que coincidan con el filtro actual.</p>
      )}
      <ProyeccionLeyenda />

      {panel.panel && (
        <ProyeccionCandidatosDrawer
          key={`${panel.panel.id_maquina}-${panel.panel.clase}-${contexto.descartarHasta}`}
          fila={panel.panel}
          contexto={contexto}
          fechaObjetivo={fechaCargada}
          puedeGestionar={puedeOperar}
          onClose={panel.cerrar}
          onCambio={panel.trasAccion}
        />
      )}
      {historial && (
        <ProyeccionHistorialModal
          key={`${historial.id_maquina}-${historial.clase}`}
          fila={historial}
          onClose={() => setHistorial(null)}
        />
      )}
    </>
  );
}
