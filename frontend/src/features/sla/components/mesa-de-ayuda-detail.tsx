"use client";

import { Headset, RefreshCw } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { mesaAyudaApi } from "../api/mesa-ayuda-api";
import { mesaDeAyudaColumns } from "./mesa-de-ayuda-columns";
import type { IncidenteMesaAyuda } from "../types/mesa-ayuda";
import { useSession } from "@/services/session-provider";
import { BrandButton, BrandSelect } from "@/shared/components/ui/brand-form";
import { PaginationBar } from "@/shared/components/ui/pagination-bar";
import { StatsTable } from "@/shared/components/ui/stats-table";
import { Spinner } from "@/shared/components/ui/spinner";
import { cn } from "@/shared/utils/cn";

const TODOS = "__todos__";
const PAGE_SIZE = 100;

/** El login de Siges es el prefijo del email corporativo (ej.
 * mjvela@canaldirecto.com.ar -> mjvela) — no hay un vínculo formal entre
 * app_user y Siges/UsuariosWeb, es la única heurística disponible (verificada
 * contra los usuarios reales de dev 2026-08-25). Solo se usa para
 * preseleccionar el filtro; si no matchea ningún operador de los resultados,
 * el selector arranca en "Todos". */
function loginDesdeEmail(email: string): string {
  return email.split("@")[0] ?? "";
}

function useOperadorOptions(incidentes: IncidenteMesaAyuda[]) {
  return useMemo(() => {
    const vistos = new Map<string, string>();
    for (const inc of incidentes) {
      if (inc.operador_login) vistos.set(inc.operador_login, inc.operador);
    }
    return [...vistos.entries()].sort((a, b) => a[1].localeCompare(b[1]));
  }, [incidentes]);
}

export function MesaDeAyudaDetail() {
  const { user } = useSession();
  const [operador, setOperador] = useState<string>(TODOS);
  const [operadorInicializado, setOperadorInicializado] = useState(false);
  const [todos, setTodos] = useState<IncidenteMesaAyuda[]>([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    mesaAyudaApi
      .listIncidentes()
      .then((items) => {
        if (!active) return;
        setTodos(items);
        if (!operadorInicializado) {
          setOperadorInicializado(true);
          const loginPropio = loginDesdeEmail(user.email);
          if (items.some((i) => i.operador_login === loginPropio)) {
            setOperador(loginPropio);
          }
        }
      })
      .catch((err: unknown) => {
        if (!active) return;
        console.error("Error al cargar incidentes de Mesa de Ayuda:", err);
        setError(
          err instanceof Error ? err.message : "No se pudieron cargar los incidentes.",
        );
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    setError(null);
    mesaAyudaApi
      .listIncidentes()
      .then((items) => setTodos(items))
      .catch((err: unknown) => {
        console.error("Error al actualizar incidentes de Mesa de Ayuda:", err);
        setError(err instanceof Error ? err.message : "No se pudo actualizar.");
      })
      .finally(() => setRefreshing(false));
  };

  const operadorOptions = useOperadorOptions(todos);
  const filtrados = useMemo(
    () => (operador === TODOS ? todos : todos.filter((i) => i.operador_login === operador)),
    [todos, operador],
  );
  const [prevOperador, setPrevOperador] = useState(operador);
  if (operador !== prevOperador) {
    setPrevOperador(operador);
    setPage(1);
  }
  const totalPaginas = Math.max(1, Math.ceil(filtrados.length / PAGE_SIZE));
  const paginaActual = Math.min(page, totalPaginas);
  const incidentes = filtrados.slice(
    (paginaActual - 1) * PAGE_SIZE,
    paginaActual * PAGE_SIZE,
  );

  return (
    <div className="flex flex-col gap-6 px-9 py-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <Headset className="h-6 w-6 shrink-0 text-brand-orange" aria-hidden="true" />
          <div className="flex flex-col gap-1">
            <h1 className="font-heading text-[25px] font-extrabold text-foreground">
              Incidentes Mesa de Ayuda
            </h1>
            <p className="font-body text-sm text-muted-foreground">
              Incidentes asignados a Mesa de Ayuda (CD) que todavía no fueron cerrados.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap items-end gap-3">
          <BrandSelect
            label="Operador"
            value={operador}
            onChange={(e) => setOperador(e.target.value)}
            className="min-w-[200px]"
          >
            <option value={TODOS}>Todos</option>
            {operadorOptions.map(([login, nombre]) => (
              <option key={login} value={login}>
                {nombre}
              </option>
            ))}
          </BrandSelect>
          <BrandButton onClick={handleRefresh} loading={refreshing} disabled={loading}>
            {!refreshing && <RefreshCw className="h-4 w-4" />}
            Actualizar
          </BrandButton>
        </div>
      </div>

      {loading && (
        <div className="flex h-64 items-center justify-center">
          <Spinner />
        </div>
      )}

      {!loading && error && (
        <p className="rounded-[12px] border border-destructive/40 bg-destructive/5 px-6 py-5 font-body text-sm text-foreground">
          {error}
        </p>
      )}

      {!loading && !error && (
        <>
          <StatsTable
            title="Incidentes de Mesa de Ayuda sin cerrar"
            subtitle={
              filtrados.length > 0
                ? `${filtrados.length} incidente${filtrados.length !== 1 ? "s" : ""} — ordenados por días transcurridos (mayor primero)`
                : undefined
            }
            columns={mesaDeAyudaColumns}
            rows={incidentes}
            rowKey={(row) => String(row.id_incidente)}
            rowClassName={(row) =>
              cn(row.demorado && "bg-[#dc2626]/[0.07] dark:bg-[#f87171]/[0.08]")
            }
            emptyLabel="Sin incidentes de Mesa de Ayuda pendientes de cierre."
          />
          {filtrados.length > 0 && (
            <PaginationBar
              page={paginaActual}
              total={filtrados.length}
              size={PAGE_SIZE}
              onPageChange={setPage}
              noun="incidentes"
            />
          )}
        </>
      )}
    </div>
  );
}
