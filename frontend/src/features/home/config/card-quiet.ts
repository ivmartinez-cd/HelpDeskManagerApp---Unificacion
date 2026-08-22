import type { DashboardData } from "../hooks/use-dashboard-data";
import { getCicloCierre } from "../components/facturacion-parts";
import type { CardId } from "./dashboard-registry";

export interface QuietInfo {
  id: CardId;
  /** Nombre corto de la card en la tira "sin novedades". */
  label: string;
  /** Qué quiere decir "sin novedades" acá ("sin chats esperando"). */
  texto: string;
  href: string;
}

/** Paneles que se "callan" cuando no hay nada que hacer: en vez de ocupar
 * una celda entera para decir "Sin pendientes", bajan a una tira de una
 * línea al pie y las demás cards se agrandan. Un día tranquilo se ve
 * tranquilo. Solo se decide con dato cargado y sin error (mientras carga o
 * si falló, la card se muestra normal con su estado). */
export function quietCards(d: DashboardData): Map<CardId, QuietInfo> {
  const out = new Map<CardId, QuietInfo>();
  const add = (q: QuietInfo) => out.set(q.id, q);

  const w = d.watiPendientes;
  if (!w.loading && !w.error && w.resumen && w.resumen.total === 0) {
    add({ id: "wati-pendientes", label: "WhatsApp", texto: "sin chats esperando", href: "/wati" });
  }

  const ins = d.insumosDashboard;
  if (!ins.loading && !ins.error && ins.data && (ins.data.totals.pending ?? 0) === 0) {
    add({ id: "insumos", label: "Insumos", texto: "sin solicitudes pendientes", href: "/insumos" });
  }

  const cal = d.calendario;
  const arrastre = d.pendientesPeriodo;
  if (!cal.loading && !cal.error && cal.data && cal.data.pendientes.length === 0) {
    const { enArrastre } = getCicloCierre(new Date());
    const arrastreResuelto =
      !enArrastre || (!arrastre.loading && !arrastre.error && arrastre.data?.cantidad === 0);
    if (arrastreResuelto) {
      add({
        id: "facturacion",
        label: "Facturación",
        texto: "todo cerrado",
        href: "/contadores/anexos-pendientes",
      });
    }
  }

  const pc = d.pendientesResumen;
  if (!pc.loading && !pc.error && pc.data && pc.data.total === 0) {
    add({
      id: "pendientes-cerrar",
      label: "Pendientes a cerrar",
      texto: "sin incidentes",
      href: "/sla/pendientes-a-cerrar",
    });
  }

  const liq = d.liquidacionesPendientes;
  if (!liq.loading && !liq.error && liq.data && liq.data.pendientes === 0) {
    add({ id: "liquidaciones", label: "Liquidaciones", texto: "al día", href: "/liquidaciones" });
  }

  const eq = d.proximosEquipo;
  if (
    !eq.loading &&
    !eq.error &&
    eq.data &&
    eq.data.vacaciones.length === 0 &&
    eq.data.homeOffice.length === 0
  ) {
    add({ id: "proximos-equipo", label: "Equipo", texto: "nada agendado", href: "/vacaciones" });
  }

  return out;
}
