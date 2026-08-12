"use client";

import { Pencil, Plus, Trash2 } from "lucide-react";
import type { Contacto } from "../types/prestadores";
import { brandButtonClasses } from "@/shared/components/ui/brand-form";

interface PrestadorContactosListProps {
  contactos: Contacto[];
  onAdd: () => void;
  onEdit: (contacto: Contacto) => void;
  onDelete: (contacto: Contacto) => void;
}

export function PrestadorContactosList({
  contactos,
  onAdd,
  onEdit,
  onDelete,
}: PrestadorContactosListProps) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <h3 className="font-heading text-sm font-bold uppercase tracking-wide text-foreground">
          Contactos
        </h3>
        <button type="button" onClick={onAdd} className={brandButtonClasses({ variant: "outline", size: "sm" })}>
          <Plus className="h-3.5 w-3.5" />
          Agregar
        </button>
      </div>
      {contactos.length === 0 && (
        <p className="font-body text-xs text-muted-foreground">Sin contactos cargados.</p>
      )}
      <ul className="flex flex-col gap-2">
        {contactos.map((contacto) => (
          <li
            key={contacto.id}
            className="flex items-center justify-between gap-3 rounded-[10px] border border-border bg-muted/50 px-3 py-2"
          >
            <div className="flex flex-col">
              <span className="font-body text-sm font-semibold text-foreground">
                {contacto.nombre}
                {contacto.isPrincipal && (
                  <span className="ml-1.5 font-body text-[10px] font-bold uppercase text-brand-orange">
                    principal
                  </span>
                )}
              </span>
              <span className="font-body text-xs text-muted-foreground">
                {[contacto.telefono, contacto.email].filter(Boolean).join(" · ") || "—"}
              </span>
            </div>
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => onEdit(contacto)}
                aria-label={`Editar ${contacto.nombre}`}
                className="rounded-[6px] p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              >
                <Pencil className="h-3.5 w-3.5" />
              </button>
              <button
                type="button"
                onClick={() => onDelete(contacto)}
                aria-label={`Eliminar ${contacto.nombre}`}
                className="rounded-[6px] p-1.5 text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
