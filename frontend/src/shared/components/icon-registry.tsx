import {
  Activity,
  Calendar,
  FileText,
  Gauge,
  Package,
  Printer,
  Shield,
  Wrench,
  type LucideIcon,
} from "lucide-react";

// Nombres tal como quedaron en el seed del catálogo (Etapa 4 del backend).
const ICONS: Record<string, LucideIcon> = {
  shield: Shield,
  package: Package,
  "file-text": FileText,
  calendar: Calendar,
  printer: Printer,
  activity: Activity,
  // "gauge" (sla) y "wrench" (prestadores) faltaban acá — sin entrada caían
  // en el fallback Shield en vez de su ícono real.
  gauge: Gauge,
  wrench: Wrench,
};

export function resolveIcon(name: string): LucideIcon {
  return ICONS[name] ?? Shield;
}
