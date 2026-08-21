"use client";

import Link from "next/link";
import { useSession } from "@/services/session-provider";
import {
  ACCESOS_RESPALDO,
  findAcceso,
  type AccesoDirecto,
} from "../config/accesos-catalogo";
import { useAccesosRanking } from "../hooks/use-inicio-data";

const CANTIDAD = 6;

function accesiblesPara(hrefs: readonly string[], moduleKeys: Set<string>): AccesoDirecto[] {
  const vistos = new Set<string>();
  const result: AccesoDirecto[] = [];
  for (const href of hrefs) {
    const acceso = findAcceso(href);
    if (!acceso || vistos.has(acceso.href) || !moduleKeys.has(acceso.moduleKey)) continue;
    vistos.add(acceso.href);
    result.push(acceso);
  }
  return result;
}

/** Fila de accesos directos: ranking personal real (30 días, backend) +
 * respaldo fijo del catálogo para completar hasta 6 mientras no hay
 * suficiente historial. No se muestra nada si el usuario no tiene acceso
 * a ningún módulo con accesos catalogados. */
export function AccesosDirectos() {
  const { modules } = useSession();
  const ranking = useAccesosRanking();
  const moduleKeys = new Set(modules.map((m) => m.key));

  const rankeados = accesiblesPara(ranking.data ?? [], moduleKeys);
  const respaldo = accesiblesPara(ACCESOS_RESPALDO, moduleKeys);
  const accesos = [
    ...rankeados,
    ...respaldo.filter((a) => !rankeados.some((r) => r.href === a.href)),
  ].slice(0, CANTIDAD);

  if (accesos.length === 0) return null;

  return (
    <div className="flex-none">
      <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3 lg:grid-cols-6">
        {accesos.map((acceso) => {
          const Icon = acceso.icon;
          return (
            <Link
              key={acceso.href}
              href={acceso.href}
              className="flex items-center gap-2 rounded-[10px] border border-border bg-card px-3 py-2.5 no-underline transition-colors hover:border-brand-orange/40"
            >
              <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-[8px] bg-brand-orange/[0.13] text-brand-orange">
                <Icon className="h-3.5 w-3.5" />
              </span>
              <span className="truncate font-body text-[12.5px] font-semibold text-foreground">
                {acceso.label}
              </span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
