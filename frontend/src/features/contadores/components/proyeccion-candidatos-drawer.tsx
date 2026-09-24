"use client";

import { X } from "lucide-react";
import type { ContextoProceso, FilaProyeccion } from "../types/proyeccion";
import { useCandidatosProyeccion } from "../hooks/use-candidatos-proyeccion";
import { useAccionesProyeccion } from "../hooks/use-acciones-proyeccion";
import { ProyeccionBoxplot } from "./proyeccion-boxplot";
import { ProyeccionCandidatosAcciones } from "./proyeccion-candidatos-acciones";
import { ProyeccionCalculoPanel, ProyeccionLecturasTabla } from "./proyeccion-candidatos-panels";
import { TEC_LABEL } from "./proyeccion-formato";

/** Panel lateral de candidatos — `PanelCandidatos.razor` (v1.7) sobre la
 * fila tal como se ve en la grilla (con la decisión del operador aplicada).
 * El padre lo monta con `key` por equipo/clase. */

interface ProyeccionCandidatosDrawerProps {
  fila: FilaProyeccion;
  // Proceso cargado + descarte vigente: el panel ve la fila de la grilla.
  contexto: ContextoProceso;
  fechaObjetivo: string | null;
  puedeGestionar: boolean;
  onClose: () => void;
  // Acción guardada: el panel se cierra y la grilla se relee.
  onCambio: () => void;
}

function Titulo({ children }: { children: React.ReactNode }) {
  return <p className="mb-2 mt-5 text-[10.5px] font-bold uppercase tracking-wide text-muted-foreground">{children}</p>;
}

function InfoEquipo({ fila, velocidad }: { fila: FilaProyeccion; velocidad: number | null }) {
  const m = fila.meses_sin_real;
  return (
    <div className="text-xs">
      <p className="font-semibold text-foreground">{fila.empresa}</p>
      <p className="text-muted-foreground">
        {fila.sucursal}
        {fila.sector && <span> · Sector: {fila.sector}</span>}
      </p>
      <p className="mt-1">
        Nro serie: <strong>{fila.nro_serie}</strong>
      </p>
      <p className="text-muted-foreground">
        {fila.modelo} · <span className="font-semibold">{TEC_LABEL[fila.tecnologia]}</span>
        {velocidad !== null && <span> · {velocidad} ppm</span>}
      </p>
      {m !== null && (
        <p className={fila.meses_sin_real_en_alerta ? "mt-1 font-semibold text-destructive" : "mt-1 text-muted-foreground"}>
          {fila.meses_sin_real_en_alerta && "⚠ "}Última lectura real hace {m} mes{m === 1 ? "" : "es"}
        </p>
      )}
    </div>
  );
}

export function ProyeccionCandidatosDrawer({
  fila,
  contexto,
  fechaObjetivo,
  puedeGestionar,
  onClose,
  onCambio,
}: ProyeccionCandidatosDrawerProps) {
  const { datos, errorCarga, seleccion, toggle, preview, errorPreview } = useCandidatosProyeccion(fila, contexto);
  const acciones = useAccionesProyeccion(fila, contexto, onCambio);
  const boxplot = datos?.boxplot ?? null;

  return (
    <div className="fixed inset-0 z-[100] flex justify-end">
      <div className="absolute inset-0 bg-background/70 backdrop-blur-sm animate-fade-in" onClick={onClose} />
      <div className="relative flex w-full max-w-[440px] flex-col rounded-l-[20px] border-l border-border bg-card shadow-2xl animate-slide-from-right">
        <div className="relative border-b border-border p-6 pb-4">
          <button onClick={onClose} aria-label="Cerrar panel" title="Cerrar panel" className="absolute right-5 top-5 text-muted-foreground hover:text-foreground">
            <X className="h-4 w-4" />
          </button>
          <p className="mb-2 text-[10.5px] font-bold uppercase tracking-[.08em] text-brand-orange">Candidatos · Cl.{fila.clase}</p>
          <InfoEquipo fila={fila} velocidad={datos?.velocidad_ppm ?? null} />
        </div>

        <div className="flex-1 overflow-y-auto px-6 pb-6 thin-scrollbar">
          <Titulo>Lecturas recientes (últimas 24)</Titulo>
          <ProyeccionLecturasTabla datos={datos} error={errorCarga} seleccion={seleccion} puedeGestionar={puedeGestionar} onToggle={toggle} />

          <Titulo>Cálculo</Titulo>
          <ProyeccionCalculoPanel
            seleccion={seleccion}
            preview={preview}
            errorPreview={errorPreview}
            fechaObjetivo={fechaObjetivo}
            ultimoFacturado={fila.ultimo_facturado_valor}
          />

          {boxplot && (
            <ProyeccionBoxplot
              data={boxplot}
              estimacion={preview?.impresiones ?? fila.impresiones}
              titulo={<Titulo>Parque del cliente ({TEC_LABEL[fila.tecnologia]}) — últimos 6 meses</Titulo>}
            />
          )}
        </div>

        {puedeGestionar && <ProyeccionCandidatosAcciones fila={fila} datos={datos} seleccion={seleccion} acciones={acciones} />}
      </div>
    </div>
  );
}
