"use client";

import { useEffect, useRef, useState } from "react";
import { History, Loader2, Search } from "lucide-react";
import { cn } from "@/shared/utils/cn";
import type { Empresa } from "../../types/reporte";
import { formatearEntero } from "../../lib/periodos";
import { guardarReciente, leerRecientes } from "./clientes-recientes";
import { MAX_RESULTADOS, useBusquedaEmpresas } from "./use-busqueda-empresas";
import { ETIQUETA } from "./estilos";

interface Props {
  onSeleccionar: (empresa: Empresa | null) => void;
}

/** Buscador de cliente (patrón combobox + listbox, port de `ClientPicker`):
 * busca mientras se escribe, se maneja con ↑ ↓ Enter Esc y, con el campo
 * vacío, ofrece los últimos clientes elegidos. */
export function BuscadorCliente({ onSeleccionar }: Props) {
  const [consulta, setConsulta] = useState("");
  const [abierto, setAbierto] = useState(false);
  const [activo, setActivo] = useState(0);
  // Solo se muestran con el listbox abierto (nunca en el primer render), así
  // que leerlos en el init no genera diferencias de hidratación.
  const [recientes, setRecientes] = useState<Empresa[]>(leerRecientes);
  const listaRef = useRef<HTMLUListElement>(null);
  const { resultados, total, cargando, error } = useBusquedaEmpresas(consulta);

  const mostrandoRecientes = consulta.trim() === "" && recientes.length > 0;
  const opciones = mostrandoRecientes ? recientes : resultados;
  const expandido = abierto && opciones.length > 0;

  useEffect(() => {
    if (!abierto) return;
    listaRef.current
      ?.querySelector<HTMLElement>(`#ri-cliente-${activo}`)
      ?.scrollIntoView({ block: "nearest" });
  }, [activo, abierto]);

  function elegir(empresa: Empresa) {
    setRecientes((actuales) => guardarReciente(empresa, actuales));
    setConsulta(empresa.nombre);
    setAbierto(false);
    onSeleccionar(empresa);
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setAbierto(true);
      setActivo((i) => Math.min(i + 1, opciones.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActivo((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      const elegida = opciones[activo];
      // Como el legacy: Enter elige aunque la lista esté cerrada.
      if (elegida) elegir(elegida);
    } else if (e.key === "Escape") {
      setAbierto(false);
    }
  }

  const pista = error
    ? error
    : consulta.trim()
      ? `${formatearEntero(total)}${total > MAX_RESULTADOS ? ` (se muestran ${MAX_RESULTADOS})` : ""} coincidencia${total === 1 ? "" : "s"}`
      : `${formatearEntero(total)} clientes disponibles`;

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor="ri-cliente" className={ETIQUETA}>
        Cliente
      </label>
      <div className="relative flex">
        <Search
          className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
          aria-hidden="true"
        />
        <input
          id="ri-cliente"
          type="text"
          role="combobox"
          aria-expanded={expandido}
          aria-controls="ri-clientes-lista"
          aria-autocomplete="list"
          aria-activedescendant={expandido ? `ri-cliente-${activo}` : undefined}
          autoComplete="off"
          spellCheck={false}
          placeholder="Buscar cliente por nombre o ID…"
          value={consulta}
          onChange={(e) => {
            setConsulta(e.target.value);
            onSeleccionar(null);
            setActivo(0);
            setAbierto(true);
          }}
          onFocus={() => setAbierto(true)}
          onBlur={() => setAbierto(false)}
          onKeyDown={onKeyDown}
          className="w-full rounded-[8px] border border-border bg-card py-2.5 pl-10 pr-9 font-body text-[15px] text-foreground outline-none focus:border-brand-orange focus:ring-2 focus:ring-brand-orange/40"
        />
        {cargando && (
          <Loader2
            className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 animate-spin text-muted-foreground"
            aria-hidden="true"
          />
        )}
        {expandido && (
          <div className="absolute left-0 right-0 top-full z-20 mt-1 rounded-[10px] border border-border bg-card p-1.5 shadow-xl">
            {mostrandoRecientes && <p className={cn(ETIQUETA, "px-3 py-1.5 text-[10px]")}>Recientes</p>}
            <ul
              ref={listaRef}
              id="ri-clientes-lista"
              role="listbox"
              aria-label={mostrandoRecientes ? "Clientes recientes" : "Resultados de clientes"}
              className="max-h-72 overflow-y-auto"
            >
              {opciones.map((empresa, i) => (
                <li
                  key={empresa.id}
                  id={`ri-cliente-${i}`}
                  role="option"
                  aria-selected={i === activo}
                  onMouseEnter={() => setActivo(i)}
                  onMouseDown={(ev) => {
                    ev.preventDefault(); // evita el blur antes del click
                    elegir(empresa);
                  }}
                  className={cn(
                    "flex cursor-pointer items-center gap-2.5 rounded-[8px] px-3 py-2 font-body text-sm text-foreground",
                    i === activo && "bg-muted",
                  )}
                >
                  {mostrandoRecientes && (
                    <History className="h-3.5 w-3.5 flex-none text-muted-foreground" aria-hidden="true" />
                  )}
                  <span className="flex-1 truncate">{empresa.nombre}</span>
                  <span className="font-body text-xs tabular-nums text-muted-foreground">ID {empresa.id}</span>
                </li>
              ))}
            </ul>
            <p className="mt-1.5 border-t border-border px-3 pb-1 pt-2 font-body text-xs text-muted-foreground">
              Escribí nombre o ID · ↑ ↓ para moverte · Enter para elegir
            </p>
          </div>
        )}
      </div>
      <p className={cn("font-body text-xs", error ? "text-destructive" : "text-muted-foreground")} aria-live="polite">
        {pista}
      </p>

      {abierto && !cargando && !error && consulta.trim() && resultados.length === 0 && (
        <p className="font-body text-sm text-muted-foreground">
          Sin resultados para &quot;{consulta}&quot;. Probá con otro nombre o ID.
        </p>
      )}
    </div>
  );
}
