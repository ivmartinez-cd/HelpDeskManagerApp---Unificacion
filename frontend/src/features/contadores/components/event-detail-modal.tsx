"use client";

import { BrandModal } from "@/shared/components/ui/brand-modal";
import { Calendar, MapPin, User, Package, Clock, Truck, FileText } from "lucide-react";
import type { CalendarEvent } from "../types/calendario";

interface Props {
  event: CalendarEvent | null;
  onClose: () => void;
}

function cleanTitle(title: string | null | undefined): string {
  if (!title) return "";
  return title.replace(/<[^>]*>/g, "").trim();
}

function formatDateString(dateStr: string | null | undefined): string {
  if (!dateStr) return "";
  const parts = dateStr.split("T")[0].split("-");
  if (parts.length === 3) {
    const d = new Date(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[2], 10));
    return d.toLocaleDateString("es-AR", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  }
  return dateStr;
}

export function EventDetailModal({ event, onClose }: Props) {
  if (!event) return null;

  const displayTitle = event.cliente || cleanTitle(event.title);
  const cleanHeaderTitle = cleanTitle(event.title);

  return (
    <BrandModal
      isOpen
      onClose={onClose}
      title={displayTitle}
      widthPx={640}
    >
      <div className="flex flex-col gap-5 py-2">
        <div className="rounded-lg border border-border bg-muted/30 p-4">
          <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
            <span className="inline-block h-2.5 w-2.5 rounded-full bg-emerald-500" />
            <span>{cleanHeaderTitle}</span>
          </div>
          {event.tittle_tooltip && (
            <p className="mt-1 text-xs text-muted-foreground">{cleanTitle(event.tittle_tooltip)}</p>
          )}
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          {event.cliente && (
            <div className="flex items-start gap-3">
              <User className="mt-0.5 h-4 w-4 text-primary shrink-0" />
              <div>
                <p className="text-xs text-muted-foreground font-medium">Cliente</p>
                <p className="text-sm font-semibold text-foreground">{event.cliente}</p>
              </div>
            </div>
          )}

          {event.start && (
            <div className="flex items-start gap-3">
              <Calendar className="mt-0.5 h-4 w-4 text-primary shrink-0" />
              <div>
                <p className="text-xs text-muted-foreground font-medium">Fecha Programada</p>
                <p className="text-sm font-semibold text-foreground">
                  {formatDateString(event.start)}
                </p>
              </div>
            </div>
          )}

          {event.string_tipo_evento && (
            <div className="flex items-start gap-3">
              <FileText className="mt-0.5 h-4 w-4 text-primary shrink-0" />
              <div>
                <p className="text-xs text-muted-foreground font-medium">Tipo de Evento</p>
                <span className="inline-flex items-center rounded-md bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                  {event.string_tipo_evento}
                </span>
              </div>
            </div>
          )}

          {event.vendedor && (
            <div className="flex items-start gap-3">
              <User className="mt-0.5 h-4 w-4 text-muted-foreground shrink-0" />
              <div>
                <p className="text-xs text-muted-foreground font-medium">Vendedor</p>
                <p className="text-sm text-foreground">{event.vendedor}</p>
              </div>
            </div>
          )}

          {event.sucursal_entrega && (
            <div className="flex items-start gap-3">
              <MapPin className="mt-0.5 h-4 w-4 text-primary shrink-0" />
              <div>
                <p className="text-xs text-muted-foreground font-medium">Sucursal de Entrega</p>
                <p className="text-sm text-foreground">{event.sucursal_entrega}</p>
              </div>
            </div>
          )}

          {event.sucursal_despacho && (
            <div className="flex items-start gap-3">
              <Truck className="mt-0.5 h-4 w-4 text-primary shrink-0" />
              <div>
                <p className="text-xs text-muted-foreground font-medium">Sucursal Despacho</p>
                <p className="text-sm text-foreground">{event.sucursal_despacho}</p>
              </div>
            </div>
          )}

          {event.contacto_entrega && (
            <div className="flex items-start gap-3">
              <Clock className="mt-0.5 h-4 w-4 text-muted-foreground shrink-0" />
              <div>
                <p className="text-xs text-muted-foreground font-medium">Contacto de Entrega</p>
                <p className="text-sm text-foreground">{event.contacto_entrega}</p>
              </div>
            </div>
          )}

          {event.bultos !== undefined && event.bultos !== null && (
            <div className="flex items-start gap-3">
              <Package className="mt-0.5 h-4 w-4 text-primary shrink-0" />
              <div>
                <p className="text-xs text-muted-foreground font-medium">Bultos / Items</p>
                <p className="text-sm font-semibold text-foreground">{event.bultos}</p>
              </div>
            </div>
          )}
        </div>

        {event.content_tooltip && (
          <div className="mt-2 rounded-lg border border-border bg-background p-3 text-xs text-muted-foreground">
            <p className="font-medium text-foreground mb-1">Información Adicional:</p>
            <div
              className="prose prose-xs max-w-none text-muted-foreground"
              dangerouslySetInnerHTML={{ __html: event.content_tooltip }}
            />
          </div>
        )}
      </div>
    </BrandModal>
  );
}
