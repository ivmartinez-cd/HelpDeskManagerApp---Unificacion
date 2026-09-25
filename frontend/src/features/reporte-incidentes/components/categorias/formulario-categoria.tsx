"use client";

import { useId, useState, type FormEvent, type ReactNode } from "react";
import { AlertTriangle, Check, Trash2 } from "lucide-react";
import type { CategoriaDetalle } from "../../types/reporte";
import { COLOR_HEX, type EstadoCategorias } from "../../hooks/use-categorias";
import { Button } from "@/shared/components/ui/button";
import { cn } from "@/shared/utils/cn";
import { CLASE_BOTON, CLASE_BOTON_NARANJA, CLASE_CONTROL, CLASE_ETIQUETA } from "../tabla/estilos";
import { EditorSubcategorias } from "./editor-subcategorias";

function Campo({ etiqueta, htmlFor, ayuda, children }: { etiqueta: string; htmlFor: string; ayuda?: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={htmlFor} className={CLASE_ETIQUETA}>{etiqueta}</label>
      {children}
      {ayuda && <span className="font-body text-xs text-muted-foreground">{ayuda}</span>}
    </div>
  );
}

function ConfirmarEliminacion({ cat }: { cat: EstadoCategorias }) {
  const categoria = cat.categorias.find((c) => c.nombre === cat.aEliminar);
  const subs = categoria?.subcategorias.length ?? 0;
  return (
    <div
      role="alertdialog"
      aria-label="Confirmar eliminación"
      className="flex flex-wrap items-center gap-3 rounded-[10px] border border-destructive/30 bg-destructive/10 px-3.5 py-3"
    >
      <AlertTriangle className="h-[18px] w-[18px] flex-none text-destructive" aria-hidden="true" />
      <div className="min-w-0 grow font-body">
        <p className="text-sm font-bold text-foreground">¿Eliminar la categoría {cat.aEliminar}?</p>
        <p className="text-xs text-muted-foreground">
          Se borran sus {subs} subcategorías. Los casos tipificados con ella vuelven a quedar sin tipificar hasta el
          próximo análisis.
        </p>
      </div>
      <Button type="button" size="sm" variant="outline" className={CLASE_BOTON} disabled={cat.guardando} onClick={cat.cancelarEliminar}>
        Cancelar
      </Button>
      <Button type="button" size="sm" variant="danger" className={CLASE_BOTON} loading={cat.guardando} onClick={() => void cat.eliminar()}>
        {!cat.guardando && <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />}
        Eliminar
      </Button>
    </div>
  );
}

/** Alta/edición de una categoría. Monta con los datos de `inicial` (el padre
 * le cambia la `key` al cambiar de categoría). */
export function FormularioCategoria({ inicial, cat }: { inicial: CategoriaDetalle; cat: EstadoCategorias }) {
  const id = useId();
  const [datos, setDatos] = useState<CategoriaDetalle>(inicial);
  const [hex, setHex] = useState(inicial.color);
  const esNueva = !cat.edicion?.nombreAnterior;
  const set = (cambios: Partial<CategoriaDetalle>) => setDatos((d) => ({ ...d, ...cambios }));

  const cambiarHex = (valor: string) => {
    setHex(valor);
    if (COLOR_HEX.test(valor)) set({ color: valor.toLowerCase() });
  };

  const enviar = (e: FormEvent) => {
    e.preventDefault();
    void cat.guardar({ ...datos, color: COLOR_HEX.test(hex) ? hex.toLowerCase() : hex });
  };

  return (
    <form onSubmit={enviar} className="flex flex-col gap-[18px]">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-[minmax(0,1fr)_220px]">
        <Campo etiqueta="Nombre de categoría" htmlFor={`${id}-nombre`}>
          <input
            id={`${id}-nombre`}
            type="text"
            className={CLASE_CONTROL}
            placeholder="Ej: Impresión móvil"
            value={datos.nombre}
            disabled={cat.guardando}
            onChange={(e) => set({ nombre: e.target.value })}
          />
        </Campo>
        <Campo etiqueta="Color en gráficos y tabla" htmlFor={`${id}-color`}>
          <div className="flex gap-2">
            <input
              type="color"
              aria-label="Elegir color"
              value={datos.color}
              disabled={cat.guardando}
              onChange={(e) => cambiarHex(e.target.value)}
              className="h-[38px] w-[38px] flex-none cursor-pointer rounded-[8px] border border-border bg-card p-0.5"
            />
            <input
              id={`${id}-color`}
              type="text"
              className={cn(CLASE_CONTROL, "tabular-nums")}
              value={hex}
              maxLength={7}
              placeholder="#0275d8"
              disabled={cat.guardando}
              onChange={(e) => cambiarHex(e.target.value.trim())}
            />
          </div>
        </Campo>
      </div>
      <Campo
        etiqueta="Pauta e instrucciones para la IA"
        htmlFor={`${id}-pauta`}
        ayuda="Obligatoria. Describí qué casos entran en esta categoría, qué palabras clave buscar o en qué soluciones técnicas fijarse."
      >
        <textarea
          id={`${id}-pauta`}
          rows={4}
          className={cn(CLASE_CONTROL, "resize-y leading-normal")}
          value={datos.descripcion}
          disabled={cat.guardando}
          onChange={(e) => set({ descripcion: e.target.value })}
        />
      </Campo>
      <Campo
        etiqueta="Subcategorías (modelos de falla)"
        htmlFor={`${id}-subs`}
        ayuda="Enter o coma agrega la subcategoría a las opciones válidas para la IA."
      >
        <EditorSubcategorias
          id={`${id}-subs`}
          valores={datos.subcategorias}
          disabled={cat.guardando}
          onChange={(subcategorias) => set({ subcategorias })}
        />
      </Campo>

      {cat.aEliminar && <ConfirmarEliminacion cat={cat} />}

      <div className="flex flex-wrap items-center gap-2.5 border-t border-border pt-4">
        {!esNueva && !cat.aEliminar && (
          <Button
            type="button"
            variant="outline"
            className={cn(CLASE_BOTON, "border-destructive/40 text-destructive hover:bg-destructive/10")}
            disabled={cat.guardando}
            onClick={() => cat.pedirEliminar(cat.edicion?.nombreAnterior ?? "")}
          >
            <Trash2 className="h-4 w-4" aria-hidden="true" />
            Eliminar categoría
          </Button>
        )}
        <div className="grow" />
        <Button type="button" variant="outline" className={CLASE_BOTON} disabled={cat.guardando} onClick={cat.cancelar}>
          Cancelar
        </Button>
        <Button type="submit" className={CLASE_BOTON_NARANJA} disabled={cat.guardando} loading={cat.guardando && !cat.aEliminar}>
          {!cat.guardando && <Check className="h-4 w-4" aria-hidden="true" />}
          {esNueva ? "Crear categoría" : "Guardar cambios"}
        </Button>
      </div>
    </form>
  );
}
