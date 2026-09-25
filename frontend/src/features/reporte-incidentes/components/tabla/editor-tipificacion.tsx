"use client";

import { useEffect, useEffectEvent, useId, useState, type ReactNode } from "react";
import { Check } from "lucide-react";
import { reporteIncidentesApi } from "../../api/reporte-incidentes-api";
import { PENDIENTE, type CategoriaTaxonomia, type Incidente } from "../../types/reporte";
import { Button } from "@/shared/components/ui/button";
import { cn } from "@/shared/utils/cn";
import { CLASE_BOTON, CLASE_BOTON_NARANJA, CLASE_CONTROL, CLASE_ETIQUETA } from "./estilos";

const MS_CONFIRMACION = 1500;

interface EditorTipificacionProps {
  incidente: Incidente;
  taxonomia: CategoriaTaxonomia[];
  /** Tras guardar (y mostrar la confirmación): típicamente `estado.recargar()`. */
  onGuardado: () => void;
  /** Solo en el detalle: muestra "Cancelar". */
  onCancelar?: () => void;
  /** `fila` = compacto, sin etiquetas (panel de pendientes). */
  variante?: "detalle" | "fila";
}

function inicial(incidente: Incidente) {
  const categoria = incidente.categoria && incidente.categoria !== PENDIENTE ? incidente.categoria : "";
  return { categoria, subcategoria: categoria ? (incidente.subcategoria ?? "") : "" };
}

/** Selector categoría → subcategoría de la taxonomía + Guardar. La corrección
 * vale para todos los casos con el mismo reporte, causa y solución. */
export function EditorTipificacion({
  incidente,
  taxonomia,
  onGuardado,
  onCancelar,
  variante = "detalle",
}: EditorTipificacionProps) {
  const id = useId();
  const [seleccion, setSeleccion] = useState(() => inicial(incidente));
  const [guardando, setGuardando] = useState(false);
  const [guardado, setGuardado] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const subcategorias = taxonomia.find((c) => c.nombre === seleccion.categoria)?.subcategorias ?? [];
  const bloqueado = guardando || guardado;

  const alConfirmar = useEffectEvent(() => onGuardado());
  useEffect(() => {
    if (!guardado) return;
    const handle = setTimeout(() => alConfirmar(), MS_CONFIRMACION);
    return () => clearTimeout(handle);
  }, [guardado]);

  const guardar = async () => {
    if (!seleccion.categoria || !seleccion.subcategoria) return;
    setGuardando(true);
    setError(null);
    try {
      await reporteIncidentesApi.corregirTipificacion(incidente, seleccion.categoria, seleccion.subcategoria);
      setGuardado(true);
    } catch (err: unknown) {
      console.error("Error al guardar la tipificación:", err);
      setError(err instanceof Error ? err.message : "No se pudo guardar la tipificación.");
    } finally {
      setGuardando(false);
    }
  };

  const fila = variante === "fila";
  const selects = (
    <>
      <Campo etiqueta={fila ? null : "Categoría"} htmlFor={`${id}-cat`} className={fila ? "" : "sm:w-[260px]"}>
        <select
          id={`${id}-cat`}
          aria-label="Categoría"
          className={CLASE_CONTROL}
          value={seleccion.categoria}
          disabled={bloqueado}
          onChange={(e) => setSeleccion({ categoria: e.target.value, subcategoria: "" })}
        >
          <option value="">— Categoría —</option>
          {taxonomia.map((c) => (
            <option key={c.nombre} value={c.nombre}>{c.nombre}</option>
          ))}
        </select>
      </Campo>
      <Campo etiqueta={fila ? null : "Subcategoría"} htmlFor={`${id}-sub`} className={fila ? "" : "sm:w-[320px]"}>
        <select
          id={`${id}-sub`}
          aria-label="Subcategoría"
          className={CLASE_CONTROL}
          value={seleccion.subcategoria}
          disabled={bloqueado || !seleccion.categoria}
          onChange={(e) => setSeleccion((s) => ({ ...s, subcategoria: e.target.value }))}
        >
          <option value="">— Subcategoría —</option>
          {subcategorias.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </Campo>
    </>
  );

  return (
    <div className="flex flex-col gap-2">
      <div className={cn("flex flex-col gap-3", fila ? "lg:grid lg:grid-cols-[1fr_1fr_auto] lg:items-center" : "sm:flex-row sm:items-end")}>
        {selects}
        <div className="flex gap-2">
          <Button
            size="sm"
            variant={guardado ? "success" : "primary"}
            className={cn(guardado ? CLASE_BOTON : CLASE_BOTON_NARANJA, "h-9")}
            loading={guardando}
            disabled={bloqueado || !seleccion.categoria || !seleccion.subcategoria}
            onClick={() => void guardar()}
          >
            {!guardando && <Check className="h-3.5 w-3.5" aria-hidden="true" />}
            {guardado ? "Guardado" : fila ? "Guardar" : "Guardar tipificación"}
          </Button>
          {onCancelar && (
            <Button size="sm" variant="outline" className={cn(CLASE_BOTON, "h-9")} disabled={bloqueado} onClick={onCancelar}>
              Cancelar
            </Button>
          )}
        </div>
      </div>
      {error && <p role="alert" className="font-body text-xs text-destructive">{error}</p>}
      {guardado && (
        <p role="status" className="font-body text-xs text-success">
          Tipificación guardada. Actualizando el reporte…
        </p>
      )}
    </div>
  );
}

function Campo({
  etiqueta,
  htmlFor,
  className,
  children,
}: {
  etiqueta: string | null;
  htmlFor: string;
  className?: string;
  children: ReactNode;
}) {
  return (
    <div className={cn("flex min-w-0 flex-col gap-1.5", className)}>
      {etiqueta && (
        <label htmlFor={htmlFor} className={CLASE_ETIQUETA}>
          {etiqueta}
        </label>
      )}
      {children}
    </div>
  );
}
