import {
  Check,
  Clock,
  FileText,
  Mail,
  MapPin,
  MessageSquare,
  Phone,
  TriangleAlert,
  Truck,
  Undo2,
  type LucideIcon,
} from "lucide-react";
import type {
  ColorSemaforo,
  ResultadoAccion,
  TipoAccion,
} from "../../types/despachados";

/** Paleta del semáforo del handoff (`despachados.html`, `--s-*`): colores de
 * ESTADO, no de marca, con contraste ≥4.5:1 sobre `card` en los dos temas.
 * Van como clases literales (Tailwind solo genera lo que ve escrito entero). */
interface ToneClasses {
  /** Texto del color. */
  text: string;
  /** Chip: texto + fondo del mismo color al 14 %. */
  chip: string;
  /** Punto del timeline. */
  dot: string;
  /** Borde de la tarjeta presionada y hover. */
  cardPressed: string;
  cardHover: string;
  /** Recuadro de alerta del panel (borde 35 %, fondo 8 %). */
  alertBox: string;
}

export const TONO: Record<ColorSemaforo, ToneClasses> = {
  verde: {
    text: "text-[#047857] dark:text-[#34d399]",
    chip: "text-[#047857] bg-[#047857]/[.14] dark:text-[#34d399] dark:bg-[#34d399]/[.14]",
    dot: "bg-[#047857] dark:bg-[#34d399]",
    cardPressed: "border-[#047857] ring-1 ring-[#047857] dark:border-[#34d399] dark:ring-[#34d399]",
    cardHover: "hover:border-[#047857]/55 dark:hover:border-[#34d399]/55",
    alertBox: "border-[#047857]/35 bg-[#047857]/[.08] dark:border-[#34d399]/35 dark:bg-[#34d399]/[.08]",
  },
  amarillo: {
    text: "text-[#a16207] dark:text-[#facc15]",
    chip: "text-[#a16207] bg-[#a16207]/[.14] dark:text-[#facc15] dark:bg-[#facc15]/[.14]",
    dot: "bg-[#a16207] dark:bg-[#facc15]",
    cardPressed: "border-[#a16207] ring-1 ring-[#a16207] dark:border-[#facc15] dark:ring-[#facc15]",
    cardHover: "hover:border-[#a16207]/55 dark:hover:border-[#facc15]/55",
    alertBox: "border-[#a16207]/35 bg-[#a16207]/[.08] dark:border-[#facc15]/35 dark:bg-[#facc15]/[.08]",
  },
  naranja: {
    text: "text-[#c2410c] dark:text-[#fb923c]",
    chip: "text-[#c2410c] bg-[#c2410c]/[.14] dark:text-[#fb923c] dark:bg-[#fb923c]/[.14]",
    dot: "bg-[#c2410c] dark:bg-[#fb923c]",
    cardPressed: "border-[#c2410c] ring-1 ring-[#c2410c] dark:border-[#fb923c] dark:ring-[#fb923c]",
    cardHover: "hover:border-[#c2410c]/55 dark:hover:border-[#fb923c]/55",
    alertBox: "border-[#c2410c]/35 bg-[#c2410c]/[.08] dark:border-[#fb923c]/35 dark:bg-[#fb923c]/[.08]",
  },
  rojo: {
    text: "text-[#b91c1c] dark:text-[#f87171]",
    chip: "text-[#b91c1c] bg-[#b91c1c]/[.14] dark:text-[#f87171] dark:bg-[#f87171]/[.14]",
    dot: "bg-[#b91c1c] dark:bg-[#f87171]",
    cardPressed: "border-[#b91c1c] ring-1 ring-[#b91c1c] dark:border-[#f87171] dark:ring-[#f87171]",
    cardHover: "hover:border-[#b91c1c]/55 dark:hover:border-[#f87171]/55",
    alertBox: "border-[#b91c1c]/35 bg-[#b91c1c]/[.08] dark:border-[#f87171]/35 dark:bg-[#f87171]/[.08]",
  },
  gris: {
    text: "text-[#52525b] dark:text-[#a1a1aa]",
    chip: "text-[#52525b] bg-[#52525b]/[.14] dark:text-[#a1a1aa] dark:bg-[#a1a1aa]/[.14]",
    dot: "bg-[#52525b] dark:bg-[#a1a1aa]",
    cardPressed: "border-[#52525b] ring-1 ring-[#52525b] dark:border-[#a1a1aa] dark:ring-[#a1a1aa]",
    cardHover: "hover:border-[#52525b]/55 dark:hover:border-[#a1a1aa]/55",
    alertBox: "border-[#52525b]/35 bg-[#52525b]/[.08] dark:border-[#a1a1aa]/35 dark:bg-[#a1a1aa]/[.08]",
  },
  // Azul "cerrado" del handoff: color de estado, a confirmar con el usuario
  // (ver README del handoff, "Decisiones y desvíos").
  cerrado: {
    text: "text-[#1d4ed8] dark:text-[#93c5fd]",
    chip: "text-[#1d4ed8] bg-[#1d4ed8]/[.14] dark:text-[#93c5fd] dark:bg-[#93c5fd]/[.14]",
    dot: "bg-[#1d4ed8] dark:bg-[#93c5fd]",
    cardPressed: "border-[#1d4ed8] ring-1 ring-[#1d4ed8] dark:border-[#93c5fd] dark:ring-[#93c5fd]",
    cardHover: "hover:border-[#1d4ed8]/55 dark:hover:border-[#93c5fd]/55",
    alertBox: "border-[#1d4ed8]/35 bg-[#1d4ed8]/[.08] dark:border-[#93c5fd]/35 dark:bg-[#93c5fd]/[.08]",
  },
};

export const ICONO_COLOR: Record<ColorSemaforo, LucideIcon> = {
  rojo: MapPin,
  naranja: TriangleAlert,
  amarillo: Clock,
  verde: Truck,
  gris: Undo2,
  cerrado: Check,
};

const ETIQUETA_COLOR: Record<ColorSemaforo, string> = {
  rojo: "En sucursal",
  naranja: "Visita fallida",
  amarillo: "Sin movimiento",
  verde: "En tránsito",
  gris: "Devuelto",
  cerrado: "Entregado",
};

/** Texto del chip. Los matices salen del estado de OCA y de la observación que
 * arma el backend ("Estado nuevo, revisar", "Sin datos en OCA",
 * "Pendiente de retiro por OCA"). */
export function etiquetaChip(color: ColorSemaforo, estado: string, observacion: string): string {
  if (color === "gris" && /cancelad/i.test(estado)) return "Cancelado";
  if (color === "amarillo" && observacion === "Estado nuevo, revisar") return "Estado desconocido";
  if (color === "amarillo" && observacion === "Sin datos en OCA") return "Sin datos";
  if (color === "verde" && observacion === "Pendiente de retiro por OCA") return "Por retirar";
  return ETIQUETA_COLOR[color];
}

/** `YYYY-MM-DD` → `24/09`. */
export function fechaCorta(iso: string): string {
  const [, mes, dia] = iso.split("-");
  return `${dia}/${mes}`;
}

/** Texto del límite de retiro de un rojo, a partir de los días hábiles que
 * calcula el backend (con feriados): "vence hoy (25/09)", "quedan 3 días
 * hábiles (29/09)", "vencido el 22/09". */
export function textoLimite(fechaLimite: string | null, diasHabiles: number | null): string {
  if (!fechaLimite || diasHabiles === null) return "";
  const cuando = fechaCorta(fechaLimite);
  if (diasHabiles < 0) return `vencido el ${cuando}`;
  if (diasHabiles === 0) return `vence hoy (${cuando})`;
  if (diasHabiles === 1) return `vence mañana (${cuando})`;
  return `quedan ${diasHabiles} días hábiles (${cuando})`;
}

export const SIN_MOTIVO = "Sin Motivo";

/** Motivo que cuenta como problema (vacío o "Sin Motivo" no). */
export function tieneMotivo(motivo: string): boolean {
  const limpio = motivo.trim().toLowerCase();
  return limpio !== "" && limpio !== SIN_MOTIVO.toLowerCase();
}

export const TIPOS_ACCION: { value: TipoAccion; label: string; icon: LucideIcon }[] = [
  { value: "llamado_cliente", label: "Llamado al cliente", icon: Phone },
  { value: "mail_cliente", label: "Mail al cliente", icon: Mail },
  { value: "reclamo_oca", label: "Reclamo a OCA", icon: MessageSquare },
  { value: "otro", label: "Otro", icon: FileText },
];

export function etiquetaTipo(tipo: TipoAccion): string {
  return TIPOS_ACCION.find((t) => t.value === tipo)?.label ?? tipo;
}

export const RESULTADOS: { value: ResultadoAccion; label: string }[] = [
  { value: "resuelto", label: "Resuelto" },
  { value: "pendiente", label: "Pendiente" },
  { value: "sin_respuesta", label: "Sin respuesta" },
];

export const CLASE_RESULTADO: Record<ResultadoAccion, string> = {
  resuelto: TONO.verde.chip,
  pendiente: TONO.amarillo.chip,
  sin_respuesta: TONO.gris.chip,
};

export function etiquetaResultado(resultado: ResultadoAccion): string {
  return RESULTADOS.find((r) => r.value === resultado)?.label ?? resultado;
}
