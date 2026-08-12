"use client";

import { useState, type ChangeEvent } from "react";
import { Loader2 } from "lucide-react";
import { BrandInput } from "@/shared/components/ui/brand-form";
import { brandButtonClasses } from "@/shared/components/ui/brand-form";
import { cn } from "@/shared/utils/cn";
import type { ZoneContactRow } from "../../types";

export const EMPTY_CONTACT: ZoneContactRow = {
  zone: "",
  sol_apellido: "",
  sol_nombre: "",
  sol_telefono: "",
  sol_email: "",
  sol_sector: "",
  dest_apellido: "",
  dest_nombre: "",
  dest_telefono: "",
  dest_email: "",
  dest_sector: "",
  observaciones: "",
};

interface ContactFormProps {
  mode: "add" | "edit";
  initial: ZoneContactRow;
  saving: boolean;
  error: string | null;
  onSave: (row: ZoneContactRow) => void;
  onCancel: () => void;
}

/** Formulario para crear o editar los contactos de una zona.
 * En modo edit, el campo `zone` es de solo lectura para evitar la operación
 * no atómica de crear+borrar zona que habría que hacer si se editara el nombre. */
export function ContactForm({ mode, initial, saving, error, onSave, onCancel }: ContactFormProps) {
  const [form, setForm] = useState<ZoneContactRow>(initial);

  const set =
    (key: keyof ZoneContactRow) =>
    (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
      setForm((prev) => ({ ...prev, [key]: e.target.value }));

  const canSave = form.zone.trim() !== "" && !saving;

  return (
    <div className="flex flex-col gap-5">
      {error && (
        <div className="rounded-[8px] border border-[rgba(239,68,68,.25)] bg-[rgba(239,68,68,.07)] px-3 py-2.5 font-body text-sm text-[#991b1b] dark:text-[#fca5a5]">
          {error}
        </div>
      )}

      <BrandInput
        label="Zona"
        value={form.zone}
        onChange={set("zone")}
        placeholder="Ej: Administración, Sector Técnico…"
        disabled={mode === "edit" || saving}
        required
      />

      <div className="grid grid-cols-1 gap-x-5 gap-y-4 sm:grid-cols-2">
        <div className="flex flex-col gap-3">
          <p className="font-body text-[11px] font-bold uppercase tracking-wide text-brand-orange">
            Solicitante
          </p>
          <BrandInput label="Apellido" value={form.sol_apellido} onChange={set("sol_apellido")} disabled={saving} />
          <BrandInput label="Nombre" value={form.sol_nombre} onChange={set("sol_nombre")} disabled={saving} />
          <BrandInput label="Teléfono" value={form.sol_telefono} onChange={set("sol_telefono")} disabled={saving} />
          <BrandInput label="Email" type="email" value={form.sol_email} onChange={set("sol_email")} disabled={saving} />
          <BrandInput label="Sector" value={form.sol_sector} onChange={set("sol_sector")} disabled={saving} />
        </div>

        <div className="flex flex-col gap-3">
          <p className="font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
            Destinatario
          </p>
          <BrandInput label="Apellido" value={form.dest_apellido} onChange={set("dest_apellido")} disabled={saving} />
          <BrandInput label="Nombre" value={form.dest_nombre} onChange={set("dest_nombre")} disabled={saving} />
          <BrandInput label="Teléfono" value={form.dest_telefono} onChange={set("dest_telefono")} disabled={saving} />
          <BrandInput label="Email" type="email" value={form.dest_email} onChange={set("dest_email")} disabled={saving} />
          <BrandInput label="Sector" value={form.dest_sector} onChange={set("dest_sector")} disabled={saving} />
        </div>
      </div>

      <div className="flex flex-col gap-1.5">
        <label className="font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
          Observaciones
        </label>
        <textarea
          value={form.observaciones}
          onChange={set("observaciones")}
          disabled={saving}
          rows={2}
          className="rounded-[8px] border border-border bg-card px-[14px] py-[9px] font-body text-sm text-foreground outline-none focus:ring-2 focus:ring-brand-orange/40 disabled:opacity-50"
        />
      </div>

      <div className="flex gap-2.5 pt-1">
        <button
          type="button"
          onClick={onCancel}
          disabled={saving}
          className={brandButtonClasses({ variant: "outline", className: "flex-1 py-[11px]" })}
        >
          Cancelar
        </button>
        <button
          type="button"
          onClick={() => onSave(form)}
          disabled={!canSave}
          className={cn(
            "flex flex-1 items-center justify-center gap-2 rounded-[10px] bg-brand-orange py-[11px] font-body text-sm font-bold text-white transition-colors hover:bg-brand-orange-hover disabled:pointer-events-none disabled:opacity-50",
          )}
        >
          {saving && <Loader2 className="h-4 w-4 animate-spin" />}
          {mode === "add" ? "Agregar" : "Guardar"}
        </button>
      </div>
    </div>
  );
}
