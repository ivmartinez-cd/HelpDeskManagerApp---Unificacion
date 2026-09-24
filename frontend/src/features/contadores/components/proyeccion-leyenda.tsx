"use client";

import { cn } from "@/shared/utils/cn";

/** Leyendas al pie de la grilla (`GrillaEstimacion.razor` v1.7): semáforo y
 * coloreo, y la referencia colapsada para leer la Observación que el CSV
 * graba en SiGes (misma que docs/LEYENDA_OBSERVACION.md del Estimador). */

const SEMAFORO: { color: string; titulo: string; texto: string }[] = [
  { color: "bg-success", titulo: "Verde", texto: "entre dos reales recientes (regla 15d ok)" },
  {
    color: "bg-warning",
    titulo: "Amarillo",
    texto: "T4 (ST) en el cálculo · o confirmación requerida (receso, backup/tránsito, parque cliente-tec)",
  },
  {
    color: "bg-brand-orange",
    titulo: "Naranja",
    texto: "estimado fuera de rango del propio equipo (Impresiones < 0.6× o > 1.4× Prom6FC)",
  },
  {
    color: "bg-destructive",
    titulo: "Rojo",
    texto: "sin historia propia (cascada T19 por modelo) · o salto imposible (Vel×60×8 o >3× prom. modelo)",
  },
];

export function ProyeccionLeyenda() {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap gap-x-5 gap-y-2 rounded-[8px] bg-muted/30 px-4 py-3 font-body text-xs text-muted-foreground">
        {SEMAFORO.map((s) => (
          <span key={s.titulo} className="flex items-center gap-1.5">
            <span className={cn("inline-block h-2.5 w-2.5 rounded-full", s.color)} />
            <strong className="text-foreground">{s.titulo}</strong> — {s.texto}
          </span>
        ))}
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-3 w-5 rounded-[4px] border-2 border-dashed border-destructive" />
          <strong className="text-foreground">Borde rojo punteado</strong> en Impresiones = salto imposible
        </span>
        <span>
          <strong className="text-info">azul</strong> Impresiones &gt; 1.4× Prom6FC
        </span>
        <span>
          <strong className="text-brand-orange">naranja</strong> Impresiones &lt; 0.6× Prom6FC
        </span>
      </div>
      <LeyendaObservacion />
    </div>
  );
}

type Termino = [string, string];

const PREFIJO: Termino[] = [
  ["M+C:", "Mono y Color se estimaron igual — vale para los dos"],
  ["M: / C:", "cada clase por su lado (Mono / Color)"],
  ["(sin prefijo)", "la máquina tiene un solo contador"],
];

const METODO: Termino[] = [
  ["Entre reales", "regla de tres entre dos lecturas del propio equipo"],
  ["P/L manual", "el operador eligió la Partida y la Llegada a mano"],
  ["Parque cli/mod", "promedio del parque: mismo cliente, mismo modelo"],
  ["Parque grupo/mod", "mismo grupo económico, mismo modelo"],
  ["Parque cli/tec", "mismo cliente, misma tecnología"],
  ["Parque global/mod", "todo el parque, mismo modelo"],
  ["T4 ST proyectado", "informe de Servicio Técnico proyectado a la fecha"],
  ["T4 ST tal cual", "se tomó el valor del informe sin proyectar"],
  ["Backup / En transito sin movimiento", "se repite el contador anterior (0 impresiones)"],
];

const AVISOS: Termino[] = [
  ["(!)T4 sin revisar", "el T4 tiene Para_Facturar = 0 — confirmar antes de facturar"],
  ["sin par P/L", "no hubo dos lecturas separadas 15 días para proyectar"],
  ["usa T4", "hay un informe de ST en el par, no dos lecturas normales"],
  ["receso", "se descontaron los días de receso del cliente"],
  ["interp. atras", "la última lectura es posterior al cierre: se interpoló"],
  ["forzado op.", "el operador cambió el método que propuso el sistema"],
];

const ESTADISTICOS: Termino[] = [
  [
    "P80 14eq(-2 desc)",
    "mediana truncada al percentil 80 sobre 14 equipos del parque; 2 quedaron afuera por estar por encima del P80",
  ],
  ["mediana 3eq", "mediana sin truncar — con menos de 5 equipos no se descarta nada"],
  [
    "62d 3,4/dia extrap +28d",
    "62 días entre Partida y Llegada, 3,4 impresiones por día, proyectado 28 días más hasta la fecha de cierre",
  ],
];

const TRAZABILIDAD: Termino[] = [
  [
    // El legacy usa el Id entero de Estim_Log; HDM, los primeros 8
    // caracteres del id (UUID) de la decisión en la auditoría.
    "#1a2b3c4d",
    "identificador de la decisión en la auditoría: quién la tomó, cuándo y con qué datos. Solo aparece si el operador intervino sobre ese equipo",
  ],
];

function Bloque({ titulo, terminos }: { titulo: string; terminos: Termino[] }) {
  return (
    <div>
      <h4 className="mb-1 mt-3 text-[11px] font-bold uppercase tracking-wide text-foreground">{titulo}</h4>
      <dl className="grid grid-cols-[max-content_1fr] gap-x-3 gap-y-1">
        {terminos.map(([t, d]) => (
          <div key={t} className="contents">
            <dt className="font-mono font-semibold text-foreground">{t}</dt>
            <dd>{d}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

function LeyendaObservacion() {
  return (
    <details className="rounded-[8px] border border-border px-4 py-3 font-body text-xs text-muted-foreground">
      <summary className="cursor-pointer font-semibold text-foreground">
        Cómo leer la Observación que el CSV graba en SiGes
      </summary>
      <p className="mt-2">
        <strong>texto del operador</strong> | <strong>método</strong> | <strong>impresiones</strong> |{" "}
        <strong>estadísticos</strong> | <strong>#IdLog</strong> — entra en los 200 caracteres de SiGes. Si no entra
        todo, se sueltan los campos de derecha a izquierda: lo que escribió una persona nunca se pierde.
      </p>
      <div className="grid gap-x-8 md:grid-cols-2">
        <div>
          <Bloque titulo="Prefijo" terminos={PREFIJO} />
          <Bloque titulo="Método" terminos={METODO} />
        </div>
        <div>
          <Bloque titulo="Avisos" terminos={AVISOS} />
          <Bloque titulo="Estadísticos" terminos={ESTADISTICOS} />
          <Bloque titulo="Trazabilidad" terminos={TRAZABILIDAD} />
        </div>
      </div>
    </details>
  );
}
