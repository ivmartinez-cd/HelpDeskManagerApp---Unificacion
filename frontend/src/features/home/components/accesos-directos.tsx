"use client";

import Link from "next/link";
import { useSession } from "@/services/session-provider";
import { canAccessPath, type AccessChecks } from "@/shared/config/route-permissions";
import {
  ACCESOS_RESPALDO,
  findAcceso,
  type AccesoDirecto,
} from "../config/accesos-catalogo";
import { useAccesosRanking } from "../hooks/use-inicio-data";

const CANTIDAD = 6;

/** Filtra por módulo habilitado y por el mapa central de rutas (ADR-029/032):
 * un acceso a una pantalla concedible por función (p. ej. Clientes de insumos)
 * no se ofrece a quien no la tiene, igual que en el submenú. */
function accesiblesPara(
  hrefs: readonly string[],
  moduleKeys: Set<string>,
  checks: AccessChecks,
): AccesoDirecto[] {
  const vistos = new Set<string>();
  const result: AccesoDirecto[] = [];
  for (const href of hrefs) {
    const acceso = findAcceso(href);
    if (!acceso || vistos.has(acceso.href) || !moduleKeys.has(acceso.moduleKey)) continue;
    if (!canAccessPath(acceso.href, checks)) continue;
    vistos.add(acceso.href);
    result.push(acceso);
  }
  return result;
}

/** Accesos directos como chips de navegación en el encabezado (ranking
 * personal real de 30 días + respaldo fijo hasta 6). Son navegación, no
 * datos: por eso dejaron de ser cards con borde compitiendo con el dashboard. */
export function AccesosDirectos() {
  const { modules, can, hasFeature } = useSession();
  const ranking = useAccesosRanking();
  const moduleKeys = new Set(modules.map((m) => m.key));
  const checks = { can, hasFeature };

  const rankeados = accesiblesPara(ranking.data ?? [], moduleKeys, checks);
  const respaldo = accesiblesPara(ACCESOS_RESPALDO, moduleKeys, checks);
  const accesos = [
    ...rankeados,
    ...respaldo.filter((a) => !rankeados.some((r) => r.href === a.href)),
  ].slice(0, CANTIDAD);

  if (accesos.length === 0) return null;

  return (
    <nav aria-label="Accesos directos" className="flex flex-wrap items-center justify-end gap-1.5">
      {accesos.map((acceso) => {
        const Icon = acceso.icon;
        return (
          <Link
            key={acceso.href}
            href={acceso.href}
            className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-2.5 py-1 font-body text-[12px] font-semibold text-foreground no-underline transition-colors hover:border-brand-orange/50 hover:text-brand-orange"
          >
            <Icon className="h-3.5 w-3.5 text-brand-orange" aria-hidden="true" />
            <span className="truncate">{acceso.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
