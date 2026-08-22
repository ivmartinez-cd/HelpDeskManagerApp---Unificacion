import type { PrestadoresResumen } from "@/features/prestadores/types/prestadores";
import { FALLBACK_COLOR } from "./inicio-format";

export interface ParqueFila {
  id: string;
  nombre: string;
  detalle: string;
  color: string;
  valor: number;
}

/** Suma el parque (equipos de los PST activos) por operador — el conteo de
 * equipos viene en vivo desde Siges. "Sin asignar" va al final. */
export function agruparParque(resumen: PrestadoresResumen): ParqueFila[] {
  const filas = resumen.grupos.flatMap((grupo) => {
    const activos = grupo.prestadores.filter((p) => p.isActive);
    if (activos.length === 0) return [];
    return [
      {
        id: grupo.operadorId ?? "sin-asignar",
        nombre: grupo.operadorNombre ?? "Sin asignar",
        detalle: `${activos.length} PST`,
        color: grupo.operadorColor ?? FALLBACK_COLOR,
        valor: activos.reduce((sum, p) => sum + (p.equipos ?? 0), 0),
      },
    ];
  });
  return filas.sort((a, b) => {
    if (a.id === "sin-asignar") return 1;
    if (b.id === "sin-asignar") return -1;
    return b.valor - a.valor;
  });
}
