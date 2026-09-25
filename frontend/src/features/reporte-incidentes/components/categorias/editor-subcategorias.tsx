"use client";

import { useState, type KeyboardEvent } from "react";
import { X } from "lucide-react";

interface EditorSubcategoriasProps {
  id: string;
  valores: string[];
  onChange: (valores: string[]) => void;
  disabled?: boolean;
}

/** Subcategorías como etiquetas: Enter o coma agrega (sin duplicados, sin
 * distinguir mayúsculas), la X quita. Al salir del campo agrega lo tipeado. */
export function EditorSubcategorias({ id, valores, onChange, disabled }: EditorSubcategoriasProps) {
  const [texto, setTexto] = useState("");

  const agregar = () => {
    const valor = texto.replace(/,/g, "").trim();
    if (!valor) return;
    if (!valores.some((v) => v.toLowerCase() === valor.toLowerCase())) onChange([...valores, valor]);
    setTexto("");
  };

  const alTeclear = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      agregar();
    } else if (e.key === "Backspace" && !texto && valores.length > 0) {
      onChange(valores.slice(0, -1));
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-1.5 rounded-[8px] border border-border bg-card p-2 focus-within:border-brand-orange focus-within:ring-2 focus-within:ring-brand-orange/40">
      {valores.map((valor, i) => (
        <span
          key={valor}
          className="inline-flex items-center gap-1 rounded-full bg-brand-orange/10 py-0.5 pr-1.5 pl-2.5 font-body text-xs font-semibold text-brand-orange"
        >
          {valor}
          <button
            type="button"
            aria-label={`Quitar ${valor}`}
            disabled={disabled}
            onClick={() => onChange(valores.filter((_, j) => j !== i))}
            className="flex cursor-pointer rounded-full p-0.5 hover:bg-brand-orange/20 disabled:cursor-not-allowed"
          >
            <X className="h-3 w-3" aria-hidden="true" />
          </button>
        </span>
      ))}
      <input
        id={id}
        type="text"
        value={texto}
        disabled={disabled}
        placeholder="Agregá una y apretá Enter"
        onChange={(e) => setTexto(e.target.value)}
        onKeyDown={alTeclear}
        onBlur={agregar}
        className="min-w-[180px] grow border-0 bg-transparent px-1.5 py-1 font-body text-sm text-foreground outline-none"
      />
    </div>
  );
}
