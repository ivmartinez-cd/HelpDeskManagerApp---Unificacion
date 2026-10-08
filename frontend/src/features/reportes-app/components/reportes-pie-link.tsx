"use client";

import Link from "next/link";
import { MessageSquareWarning } from "lucide-react";
import { cn } from "@/shared/utils/cn";
import { useReportesPendientes } from "../hooks/use-reportes-pendientes";

/** Ícono del pie del menú lateral hacia el panel de reportes (solo superadmin).
 * Se pinta de naranja con un puntito cuando hay reportes esperando su OK o
 * su Integrar: es el único aviso del circuito, no usa la campanita. */
export function ReportesPieLink({
  active,
  onNavigate,
}: {
  active: boolean;
  onNavigate: () => void;
}) {
  const { propuestos, resueltos } = useReportesPendientes();
  const partes = [
    propuestos > 0 && `${propuestos} esperan tu OK`,
    resueltos > 0 && `${resueltos} para integrar`,
  ].filter(Boolean);
  const hayPendientes = partes.length > 0;
  const titulo = ["Reportes de la app", ...partes].join(" · ");

  return (
    <Link
      href="/admin/reportes"
      onClick={onNavigate}
      title={titulo}
      aria-label={titulo}
      aria-current={active ? "page" : undefined}
      className={cn(
        "relative flex-none rounded-[6px] p-1 transition-colors",
        active || hayPendientes
          ? "text-brand-orange"
          : "text-muted-foreground hover:bg-muted",
      )}
    >
      <MessageSquareWarning className="h-3.5 w-3.5" aria-hidden="true" />
      {hayPendientes && (
        <span
          className="absolute right-0.5 top-0.5 h-1.5 w-1.5 rounded-full bg-brand-orange"
          aria-hidden="true"
        />
      )}
    </Link>
  );
}
