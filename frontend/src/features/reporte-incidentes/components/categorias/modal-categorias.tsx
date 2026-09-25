"use client";

import { Loader2, Plus, Settings } from "lucide-react";
import { useCategorias, type EstadoCategorias } from "../../hooks/use-categorias";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { Button } from "@/shared/components/ui/button";
import { cn } from "@/shared/utils/cn";
import { CLASE_BOTON } from "../tabla/estilos";
import { FormularioCategoria } from "./formulario-categoria";

function ListaCategorias({ cat }: { cat: EstadoCategorias }) {
  const actual = cat.edicion?.nombreAnterior.toLowerCase();
  return (
    <div className="flex flex-col gap-2.5">
      <Button variant="outline" size="sm" className={cn(CLASE_BOTON, "w-full")} disabled={cat.guardando} onClick={cat.nueva}>
        <Plus className="h-3.5 w-3.5" aria-hidden="true" />
        Nueva categoría
      </Button>
      <div className="flex max-h-[52vh] flex-col gap-0.5 overflow-y-auto rounded-[10px] border border-border p-1.5 thin-scrollbar">
        {cat.cargando ? (
          <p className="flex items-center gap-2 px-3 py-4 font-body text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            Cargando taxonomía…
          </p>
        ) : cat.categorias.length === 0 ? (
          <p className="px-3 py-4 font-body text-sm text-muted-foreground">Todavía no hay categorías.</p>
        ) : (
          cat.categorias.map((c) => {
            const activa = actual === c.nombre.toLowerCase();
            return (
              <button
                key={c.nombre}
                type="button"
                aria-current={activa}
                disabled={cat.guardando}
                onClick={() => cat.editar(c)}
                className={cn(
                  "flex w-full cursor-pointer items-center gap-2.5 rounded-[8px] px-3 py-2.5 text-left font-body transition-colors hover:bg-muted",
                  activa && "bg-surface-2",
                )}
              >
                <span className="h-3 w-3 flex-none rounded-[4px]" style={{ background: c.color }} aria-hidden="true" />
                <span className="min-w-0 grow">
                  <span className={cn("block truncate text-sm font-semibold", activa ? "text-brand-orange" : "text-foreground")}>
                    {c.nombre}
                  </span>
                  <span className="block text-xs text-muted-foreground">
                    {c.subcategorias.length} subcategoría{c.subcategorias.length === 1 ? "" : "s"}
                  </span>
                </span>
              </button>
            );
          })
        )}
      </div>
      <p className="px-0.5 font-body text-xs leading-normal text-muted-foreground">
        Elegí una categoría para editarla. Los cambios valen para las próximas tipificaciones; lo ya tipificado no se modifica.
      </p>
    </div>
  );
}

function SinSeleccion() {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-[12px] border border-dashed border-border px-6 py-12 text-center">
      <Settings className="h-8 w-8 text-muted-foreground" aria-hidden="true" />
      <p className="max-w-[380px] font-body text-sm text-muted-foreground">
        Elegí una categoría de la lista para editarla o tocá <strong className="text-foreground">Nueva categoría</strong>{" "}
        para agregar pautas para la IA.
      </p>
    </div>
  );
}

/** Configuración de tipificación (port de `ConfigModal`, sin la bandeja de
 * sugerencias de la IA): lista de categorías a la izquierda, formulario de
 * alta/edición a la derecha. `onCambio` corre tras cada cambio guardado. */
export function ModalCategorias({ isOpen, onClose, onCambio }: { isOpen: boolean; onClose: () => void; onCambio: () => void }) {
  return (
    <BrandModal isOpen={isOpen} onClose={onClose} title="Configuración de tipificación" widthPx={1000}>
      {isOpen && <ContenidoModal onCambio={onCambio} />}
    </BrandModal>
  );
}

function ContenidoModal({ onCambio }: { onCambio: () => void }) {
  const cat = useCategorias(onCambio);
  return (
    <div className="flex flex-col gap-4">
      <p className="-mt-2 font-body text-sm text-muted-foreground">
        Categorías y subcategorías que usa la IA para tipificar los incidentes.
      </p>
      {cat.error && (
        <p role="alert" className="rounded-[10px] border border-destructive/20 bg-destructive/10 px-3 py-2.5 font-body text-xs font-semibold text-destructive">
          {cat.error}
        </p>
      )}
      {cat.exito && (
        <p role="status" className="rounded-[10px] border border-success/20 bg-success/10 px-3 py-2.5 font-body text-xs font-semibold text-success">
          {cat.exito}
        </p>
      )}
      <div className="grid grid-cols-1 gap-7 md:grid-cols-[290px_minmax(0,1fr)]">
        <ListaCategorias cat={cat} />
        {cat.edicion ? (
          <FormularioCategoria key={cat.edicion.serie} inicial={cat.edicion.datos} cat={cat} />
        ) : (
          <SinSeleccion />
        )}
      </div>
    </div>
  );
}
