"use client";

import { use } from "react";

/** SCAFFOLD — Detalle de cliente en Estadísticas
 * (`/insumos/estadisticas/clientes/[id]`).
 *
 * Placeholder de la fundación: reemplazar por la pantalla real
 * (`/api/insumos/estadisticas/clientes/{customerId}`). El `id` de la ruta es
 * el `customerId` numérico de HP SDS (el mismo de `CustomerStat.customerId`).
 *
 * `params` llega como Promise y se desenvuelve con `use()` — misma convención
 * que `app/(app)/admin/usuarios/[id]/permisos/page.tsx`. */
export default function InsumosEstadisticasClientePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  return <div className="px-9 py-8">Estadísticas del cliente {id}</div>;
}
