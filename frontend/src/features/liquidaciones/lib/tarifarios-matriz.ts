import type { Tarifario } from "../types/liquidaciones";

// Modelo de la matriz de tarifarios "como Siges" (decisión de Iván,
// 2026-09-07): una fila por zona tarifaria (SPST o genérica) con una columna
// por tipo de servicio, igual que `dbo.CostoServicio`, donde cada vigencia es
// UNA fila con todos los tipos. Antes la pantalla listaba tipo × zona (24
// filas para INFOMAC) y repetía cada zona seis veces.

/** Orden canónico de columnas (mismo orden que las columnas de Siges). */
export const TIPOS_SERVICIO = [
  "correctivo",
  "preventivo",
  "instalacion_desinstalacion",
  "pre_correctivo",
  "guardia",
  "sistemas",
] as const;

export const LABEL_TIPO: Record<string, string> = {
  correctivo: "Correctivo",
  preventivo: "Preventivo",
  instalacion_desinstalacion: "Instalación",
  pre_correctivo: "Pre correctivo",
  guardia: "Guardia",
  sistemas: "Sistemas",
};

export function labelTipo(tipo: string): string {
  return LABEL_TIPO[tipo] ?? tipo.replace(/_/g, " ");
}

/** Una vigencia de una zona: todas las tarifas que arrancan el mismo día. */
export interface VigenciaZona {
  desde: string;
  /** null si alguna de las tarifas sigue abierta. */
  hasta: string | null;
  porTipo: Record<string, Tarifario>;
  tarifas: Tarifario[];
  /** Costo por km de la vigencia (en Siges es uno por zona y fecha; si las
   * tarifas difieren entre sí, se muestra el mayor). */
  costoKm: number;
}

export interface ZonaTarifas {
  spstId: string | null;
  /** Vigencias de la más nueva a la más vieja. */
  vigencias: VigenciaZona[];
  vigente: VigenciaZona | null;
}

/** Tipos presentes en las tarifas, en orden canónico y con los desconocidos al final. */
export function tiposPresentes(tarifarios: Tarifario[]): string[] {
  const presentes = new Set(tarifarios.map((t) => t.tipoServicio));
  const canonicos = TIPOS_SERVICIO.filter((t) => presentes.has(t));
  const extras = [...presentes].filter((t) => !(TIPOS_SERVICIO as readonly string[]).includes(t)).sort();
  return [...canonicos, ...extras];
}

function armarVigencia(desde: string, tarifas: Tarifario[]): VigenciaZona {
  const porTipo: Record<string, Tarifario> = {};
  for (const t of tarifas) porTipo[t.tipoServicio] = t;
  const abierta = tarifas.some((t) => t.vigenciaHasta === null);
  const hasta = abierta ? null : tarifas.map((t) => t.vigenciaHasta as string).sort().at(-1) ?? null;
  return { desde, hasta, porTipo, tarifas, costoKm: Math.max(...tarifas.map((t) => t.costoKm)) };
}

function vigenteHoy(vigencias: VigenciaZona[], hoy: string): VigenciaZona | null {
  return (
    vigencias.find((v) => v.desde <= hoy && (v.hasta === null || v.hasta >= hoy)) ??
    vigencias[0] ??
    null
  );
}

export function agruparPorZona(tarifarios: Tarifario[]): ZonaTarifas[] {
  const hoy = new Date().toISOString().split("T")[0];
  const porZona = new Map<string, Map<string, Tarifario[]>>();
  for (const t of tarifarios) {
    const zona = porZona.get(t.spstId ?? "") ?? new Map<string, Tarifario[]>();
    zona.set(t.vigenciaDesde, [...(zona.get(t.vigenciaDesde) ?? []), t]);
    porZona.set(t.spstId ?? "", zona);
  }
  return [...porZona.entries()].map(([key, porDesde]) => {
    const vigencias = [...porDesde.entries()]
      .sort(([a], [b]) => b.localeCompare(a))
      .map(([desde, tarifas]) => armarVigencia(desde, tarifas));
    return { spstId: key || null, vigencias, vigente: vigenteHoy(vigencias, hoy) };
  });
}
