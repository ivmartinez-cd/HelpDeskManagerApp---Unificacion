"use client";

import { Check, Search } from "lucide-react";
import { useEffect, useState } from "react";
import { contadoresApi } from "../api/contadores-api";
import type { EmpresaSiges } from "../types/calendario";
import { BrandButton, BrandInput } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { Spinner } from "@/shared/components/ui/spinner";

const DEBOUNCE_MS = 350;

interface ClienteCruceModalProps {
  /** Clientes del mes sin cruce contra Siges, dedupe entre operadores. */
  clientes: string[];
  onClose: () => void;
  /** Se llama al cerrar si se guardó al menos un mapeo (para refetch). */
  onSaved: () => void;
}

/** Resuelve clientes sin cruce: para cada nombre de Gestión, buscar la(s)
 * empresa(s) reales en Siges y guardar el mapeo. Aparecen clientes nuevos
 * todos los meses — esta es la herramienta para que el badge "sin cruce"
 * no dependa de un INSERT a mano. */
export function ClienteCruceModal({ clientes, onClose, onSaved }: ClienteCruceModalProps) {
  const [pendientes, setPendientes] = useState<string[]>(clientes);
  const [activo, setActivo] = useState<string | null>(clientes[0] ?? null);
  const [query, setQuery] = useState("");
  const [resultados, setResultados] = useState<EmpresaSiges[]>([]);
  const [buscando, setBuscando] = useState(false);
  const [seleccion, setSeleccion] = useState<Map<number, EmpresaSiges>>(new Map());
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [huboCambios, setHuboCambios] = useState(false);

  useEffect(() => {
    const texto = query.trim();
    const timer = setTimeout(() => {
      if (texto.length < 2) {
        setResultados([]);
        return;
      }
      setBuscando(true);
      contadoresApi
        .searchEmpresasSiges(texto)
        .then(setResultados)
        .catch((err: unknown) => {
          console.error("Error buscando empresas en Siges:", err);
          setError(err instanceof Error ? err.message : "No se pudo buscar.");
        })
        .finally(() => setBuscando(false));
    }, DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [query]);

  const elegirCliente = (cliente: string) => {
    setActivo(cliente);
    setQuery(cliente);
    setSeleccion(new Map());
    setError(null);
  };

  const toggleEmpresa = (empresa: EmpresaSiges) => {
    setSeleccion((prev) => {
      const next = new Map(prev);
      if (next.has(empresa.id)) next.delete(empresa.id);
      else next.set(empresa.id, empresa);
      return next;
    });
  };

  const guardar = () => {
    if (!activo || seleccion.size === 0) return;
    setGuardando(true);
    setError(null);
    contadoresApi
      .setClienteSigesMap(activo, [...seleccion.keys()])
      .then(() => {
        setHuboCambios(true);
        const restantes = pendientes.filter((c) => c !== activo);
        setPendientes(restantes);
        setSeleccion(new Map());
        if (restantes.length > 0) elegirCliente(restantes[0]);
        else setActivo(null);
      })
      .catch((err: unknown) => {
        console.error("Error guardando el mapeo:", err);
        setError(err instanceof Error ? err.message : "No se pudo guardar el mapeo.");
      })
      .finally(() => setGuardando(false));
  };

  const cerrar = () => {
    if (huboCambios) onSaved();
    onClose();
  };

  return (
    <BrandModal isOpen onClose={cerrar} title="Resolver clientes sin cruce" widthPx={560} error={error}>
      <div className="flex flex-col gap-4">
        {pendientes.length === 0 ? (
          <span className="font-body text-[13px] text-muted-foreground">
            No quedan clientes sin cruce este mes.
          </span>
        ) : (
          <>
            <div className="flex flex-wrap gap-1.5">
              {pendientes.map((cliente) => (
                <button
                  key={cliente}
                  type="button"
                  onClick={() => elegirCliente(cliente)}
                  className={`rounded-full px-2.5 py-1 font-body text-[11.5px] font-semibold transition-colors ${
                    cliente === activo
                      ? "bg-brand-orange text-white"
                      : "bg-muted text-muted-foreground hover:bg-muted/70"
                  }`}
                >
                  {cliente}
                </button>
              ))}
            </div>

            {activo && (
              <>
                <BrandInput
                  label={`Empresa para "${activo}"`}
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  hint="Buscá por denominación comercial. Podés marcar varias: el cliente suma todas."
                  placeholder="Mínimo 2 caracteres…"
                />
                {buscando ? (
                  <div className="flex justify-center py-2">
                    <Spinner />
                  </div>
                ) : resultados.length === 0 && query.trim().length >= 2 ? (
                  <span className="font-body text-[12.5px] text-muted-foreground">
                    Sin resultados para esa búsqueda.
                  </span>
                ) : (
                  <ul className="flex max-h-56 flex-col gap-1 overflow-y-auto">
                    {resultados.map((empresa) => {
                      const marcada = seleccion.has(empresa.id);
                      return (
                        <li key={empresa.id}>
                          <button
                            type="button"
                            onClick={() => toggleEmpresa(empresa)}
                            className={`flex w-full items-center justify-between gap-2 rounded-[8px] border px-2.5 py-1.5 text-left transition-colors ${
                              marcada
                                ? "border-brand-orange bg-brand-orange/[0.08]"
                                : "border-border hover:bg-muted/50"
                            }`}
                          >
                            <span className="flex min-w-0 items-center gap-1.5">
                              {marcada ? (
                                <Check className="h-3.5 w-3.5 shrink-0 text-brand-orange" />
                              ) : (
                                <Search className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                              )}
                              <span className="truncate font-body text-[13px] text-foreground">
                                {empresa.den_comercial}
                              </span>
                            </span>
                            <span className="shrink-0 font-body text-[11.5px] text-muted-foreground">
                              #{empresa.id} · {empresa.impresoras} imp.
                            </span>
                          </button>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </>
            )}
          </>
        )}

        <div className="mt-1 flex justify-end gap-2">
          <BrandButton type="button" variant="outline" onClick={cerrar}>
            Cerrar
          </BrandButton>
          {pendientes.length > 0 && (
            <BrandButton
              type="button"
              loading={guardando}
              disabled={!activo || seleccion.size === 0}
              onClick={guardar}
            >
              Guardar mapeo ({seleccion.size})
            </BrandButton>
          )}
        </div>
      </div>
    </BrandModal>
  );
}
