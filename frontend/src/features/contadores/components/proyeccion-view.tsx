"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { KpiGrid, KpiTile } from "@/shared/components/ui/kpi-tile";
import { SegmentedControl } from "@/shared/components/ui/segmented-control";
import { BrandButton, BrandInput } from "@/shared/components/ui/brand-form";
import { useTableSort } from "@/shared/hooks/use-table-sort";
import { proyeccionApi } from "../api/proyeccion-api";
import { useLoteAceptarProyeccion } from "../hooks/use-lote-aceptar-proyeccion";
import type {
  FilaProyeccion,
  GrupoEconomicoOption,
  ProcesoOption,
  SolicitudTableroReal,
  TableroProyeccion,
} from "../types/proyeccion";
import { ProyeccionBarraLote } from "./proyeccion-barra-lote";
import { ProyeccionCandidatosDrawer } from "./proyeccion-candidatos-drawer";
import { ProyeccionHistorialModal } from "./proyeccion-historial-modal";
import { ProyeccionSelectores } from "./proyeccion-selectores";
import { ProyeccionTabla, type ProyeccionSortKey } from "./proyeccion-tabla";

type FiltroChip = "todos" | "estimar" | "reales" | "sospechosos";

const FILTROS: { value: FiltroChip; label: string }[] = [
  { value: "todos", label: "Todos" },
  { value: "estimar", label: "A estimar" },
  { value: "reales", label: "Reales" },
  { value: "sospechosos", label: "Sospechosos" },
];

function coincideBusqueda(fila: FilaProyeccion, termino: string): boolean {
  const q = termino.toLowerCase();
  return (
    fila.nro_serie.toLowerCase().includes(q) ||
    fila.sucursal.toLowerCase().includes(q) ||
    fila.sector.toLowerCase().includes(q)
  );
}

function aplicaFiltro(fila: FilaProyeccion, filtro: FiltroChip): boolean {
  if (filtro === "estimar") return !fila.es_real;
  if (filtro === "reales") return fila.es_real;
  if (filtro === "sospechosos") return fila.borde_salto_imposible;
  return true;
}

function ordenar(filas: FilaProyeccion[], key: ProyeccionSortKey, dir: "asc" | "desc"): FilaProyeccion[] {
  const factor = dir === "asc" ? 1 : -1;
  const valor = (f: FilaProyeccion): string | number => {
    if (key === "ubicacion") return `${f.empresa} ${f.sucursal}`;
    if (key === "nro_serie") return f.nro_serie;
    if (key === "modelo") return f.modelo;
    return f.impresiones ?? Number.NEGATIVE_INFINITY;
  };
  return [...filas].sort((a, b) => {
    const va = valor(a);
    const vb = valor(b);
    if (va < vb) return -1 * factor;
    if (va > vb) return 1 * factor;
    return 0;
  });
}

export function ProyeccionView() {
  const [tablero, setTablero] = useState<TableroProyeccion | null>(null);
  const [filtro, setFiltro] = useState<FiltroChip>("todos");
  const [busqueda, setBusqueda] = useState("");
  const [seleccion, setSeleccion] = useState<FilaProyeccion | null>(null);
  const [verHistorial, setVerHistorial] = useState<FilaProyeccion | null>(null);
  const { sort, toggleSort } = useTableSort<ProyeccionSortKey>({
    initial: { key: "ubicacion", direction: "asc" },
    keys: ["ubicacion", "nro_serie", "modelo", "impresiones"],
  });

  // Combos reales contra Siges (MODELO_DE_DATOS §3.1/§3.2) — el tablero de
  // abajo todavía carga datos de ejemplo (ver nota al pie): sirven para
  // dejar el circuito de selección probado mientras se porta la consulta
  // real de la grilla (la compleja, MODELO_DE_DATOS §3.4).
  const [grupos, setGrupos] = useState<GrupoEconomicoOption[]>([]);
  const [procesos, setProcesos] = useState<ProcesoOption[]>([]);
  const [idGrupo, setIdGrupo] = useState<string | null>(null);
  const [idProceso, setIdProceso] = useState<string | null>(null);
  const [fechaObjetivo, setFechaObjetivo] = useState("");
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [exportando, setExportando] = useState(false);
  const [errorExport, setErrorExport] = useState<string | null>(null);

  useEffect(() => {
    void proyeccionApi.listGruposEconomicos().then(setGrupos);
  }, []);

  useEffect(() => {
    if (idGrupo == null) return;
    void proyeccionApi.listProcesos(Number(idGrupo)).then(setProcesos);
  }, [idGrupo]);

  // Derivados en vez de resetear estado a mano en el efecto de arriba
  // (react-hooks/set-state-in-effect): sin grupo no hay procesos que
  // mostrar, y si el proceso elegido ya no está en la lista del grupo
  // actual (porque el grupo cambió) se trata como null.
  const procesosVisibles = idGrupo == null ? [] : procesos;
  const idProcesoValido = procesosVisibles.some((p) => String(p.nro_proceso) === idProceso)
    ? idProceso
    : null;
  const procesoElegido = procesosVisibles.find((p) => String(p.nro_proceso) === idProcesoValido);

  const solicitudActual: SolicitudTableroReal | undefined = useMemo(
    () =>
      idGrupo && procesoElegido && fechaObjetivo
        ? {
            nroProceso: procesoElegido.nro_proceso,
            idGrupoEconomico: Number(idGrupo),
            idAnexo: procesoElegido.id_anexo,
            fechaObjetivo,
          }
        : undefined,
    [idGrupo, procesoElegido, fechaObjetivo],
  );

  const cargar = useCallback(() => {
    setCargando(true);
    setError(null);
    proyeccionApi
      .getTablero(solicitudActual)
      .then(setTablero)
      .catch(() => setError("No se pudo cargar la grilla — puede ser lenta o falló la conexión a Siges."))
      .finally(() => setCargando(false));
  }, [solicitudActual]);

  const filasVisibles = useMemo(() => {
    if (!tablero) return [];
    const filtradas = tablero.filas
      .filter((f) => aplicaFiltro(f, filtro))
      .filter((f) => (busqueda ? coincideBusqueda(f, busqueda) : true));
    return ordenar(filtradas, sort.key, sort.direction);
  }, [tablero, filtro, busqueda, sort]);

  const {
    seleccionadas,
    aceptando: aceptandoLote,
    toggleSeleccion,
    toggleSeleccionTodas,
    limpiarSeleccion,
    aceptarSeleccionadas,
  } = useLoteAceptarProyeccion(tablero, filasVisibles, cargar);

  const contador = (f: FiltroChip) =>
    tablero ? tablero.filas.filter((fila) => aplicaFiltro(fila, f)).length : 0;

  const exportarCsv = useCallback(() => {
    if (!solicitudActual) return;
    setExportando(true);
    setErrorExport(null);
    proyeccionApi
      .exportarCsv(solicitudActual)
      .catch(() => setErrorExport("No se pudo generar el CSV."))
      .finally(() => setExportando(false));
  }, [solicitudActual]);

  return (
    <div className="flex flex-col gap-6 px-9 py-8">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link href="/contadores" className="hover:text-foreground">
          Centro de Contadores
        </Link>
        <span>›</span>
        <span className="font-semibold text-foreground">Proyección</span>
        <Link href="/contadores/proyeccion/recesos" className="ml-auto hover:text-foreground">
          Recesos →
        </Link>
      </div>

      <h1 className="font-heading text-[25px] font-extrabold uppercase tracking-[-.03em] text-foreground">
        Proyección de contadores
      </h1>

      <ProyeccionSelectores
        grupos={grupos}
        procesosVisibles={procesosVisibles}
        idGrupo={idGrupo}
        idProcesoValido={idProcesoValido}
        fechaObjetivo={fechaObjetivo}
        cargando={cargando}
        onChangeGrupo={setIdGrupo}
        onChangeProceso={(id, proceso) => {
          setIdProceso(id);
          if (proceso) setFechaObjetivo(proceso.periodo_hasta);
        }}
        onChangeFecha={setFechaObjetivo}
        onCargar={cargar}
      />

      {error && (
        <p className="rounded-[8px] bg-destructive/10 px-4 py-3 font-body text-xs text-destructive">
          {error}
        </p>
      )}

      {tablero && (
        <KpiGrid className="sm:grid-cols-3 lg:grid-cols-5">
          <KpiTile label="Reales" value={String(tablero.resumen.reales)} />
          <KpiTile label="Estimados" value={String(tablero.resumen.estimados)} tone="orange" />
          <KpiTile label="Pendientes" value={String(tablero.resumen.pendientes)} tone="danger" />
          <KpiTile label="Sospechosos" value={String(tablero.resumen.sospechosos)} tone="danger" />
          <KpiTile label="Total equipos" value={String(tablero.resumen.total)} />
        </KpiGrid>
      )}

      <div className="flex flex-wrap items-end gap-3">
        <SegmentedControl
          options={FILTROS.map((f) => ({ value: f.value, label: `${f.label} (${contador(f.value)})` }))}
          value={filtro}
          onChange={(v) => setFiltro(v as FiltroChip)}
        />
        <div className="min-w-[260px]">
          <BrandInput
            label="Buscar"
            type="search"
            placeholder="Nro. serie / sucursal / sector…"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
          />
        </div>
        <BrandButton
          variant="outline"
          loading={exportando}
          disabled={!solicitudActual}
          title={solicitudActual ? undefined : "Elegí un grupo económico y un proceso real para exportar"}
          onClick={exportarCsv}
          className="ml-auto"
        >
          Exportar CSV
        </BrandButton>
      </div>

      {errorExport && (
        <p className="rounded-[8px] bg-destructive/10 px-4 py-3 font-body text-xs text-destructive">
          {errorExport}
        </p>
      )}

      <ProyeccionBarraLote
        cantidad={seleccionadas.size}
        aceptando={aceptandoLote}
        onAceptar={aceptarSeleccionadas}
        onCancelar={limpiarSeleccion}
      />

      {!tablero ? (
        <p className="text-sm text-muted-foreground">
          {cargando
            ? "Cargando…"
            : "Elegí un grupo económico y un proceso (o dejalo en blanco para ver datos de ejemplo) y apretá Cargar."}
        </p>
      ) : (
        <ProyeccionTabla
          filas={filasVisibles}
          sort={sort}
          onToggleSort={toggleSort}
          onVerCandidatos={setSeleccion}
          onVerHistorial={setVerHistorial}
          fechaObjetivo={fechaObjetivo || null}
          seleccionadas={seleccionadas}
          onToggleSeleccion={toggleSeleccion}
          onToggleSeleccionTodas={toggleSeleccionTodas}
        />
      )}

      <p className="rounded-[8px] bg-muted/30 px-4 py-3 font-body text-xs text-muted-foreground">
        Con Grupo económico y Proceso elegidos, la grilla consulta Siges en vivo (puede tardar —
        sin los índices recomendados en `MIGRACION_SISTEMAS.md`). Sin selección, muestra datos de
        ejemplo.
      </p>

      {seleccion && (
        <ProyeccionCandidatosDrawer
          key={`${seleccion.id_maquina}-${seleccion.clase}`}
          fila={seleccion}
          solicitud={solicitudActual}
          onClose={() => setSeleccion(null)}
          onCambio={() => {
            cargar();
          }}
        />
      )}

      {verHistorial && (
        <ProyeccionHistorialModal
          key={`${verHistorial.id_maquina}-${verHistorial.clase}`}
          fila={verHistorial}
          onClose={() => setVerHistorial(null)}
        />
      )}
    </div>
  );
}
