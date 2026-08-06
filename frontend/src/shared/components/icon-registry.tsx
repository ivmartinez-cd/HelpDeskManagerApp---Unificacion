import { Activity, Calendar, FileText, Package, Printer, Shield, type LucideIcon } from "lucide-react";

// Nombres tal como quedaron en el seed del catálogo (Etapa 4 del backend).
const ICONS: Record<string, LucideIcon> = {
  shield: Shield,
  package: Package,
  "file-text": FileText,
  calendar: Calendar,
  printer: Printer,
  activity: Activity,
};

export function resolveIcon(name: string): LucideIcon {
  return ICONS[name] ?? Shield;
}
