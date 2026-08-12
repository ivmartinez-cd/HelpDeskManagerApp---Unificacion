"use client";

import { useState } from "react";
import { prestadoresApi } from "../api/prestadores-api";
import type { Contacto, OperadorOption, Prestador } from "../types/prestadores";
import { AssignOperadorModal } from "./assign-operador-modal";
import { ContactoFormModal } from "./contacto-form-modal";
import { PrestadorContactosList } from "./prestador-contactos-list";
import { PrestadorFormModal } from "./prestador-form-modal";
import { PrestadorHistorialPanel } from "./prestador-historial-panel";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { BrandBadge, BrandButton } from "@/shared/components/ui/brand-form";
import { UserAvatar } from "@/shared/components/ui/user-avatar";

type Overlay = "edit" | "assign" | { contacto: Contacto | null };

interface PrestadorDetailModalProps {
  prestador: Prestador;
  operadores: OperadorOption[];
  canEdit: boolean;
  canDelete: boolean;
  onClose: () => void;
  onChanged: () => void;
}

/** Detalle de un PST: contacto(s), operador asignado, historial y las
 * acciones de edición/reasignación/alta-baja — todo en un solo modal, como
 * pide el patrón de la app (cadena de modales apilados, no páginas nuevas). */
export function PrestadorDetailModal({
  prestador,
  operadores,
  canEdit,
  canDelete,
  onClose,
  onChanged,
}: PrestadorDetailModalProps) {
  const [overlay, setOverlay] = useState<Overlay | null>(null);
  const [togglingActive, setTogglingActive] = useState(false);
  // El historial no se re-consulta solo (su efecto depende de `prestadorId`,
  // que no cambia al reasignar) -- forzar remount cambiando esta key es lo
  // que le hace pedir el historial de nuevo tras cualquier cambio.
  const [historialKey, setHistorialKey] = useState(0);

  const handleChanged = () => {
    setHistorialKey((k) => k + 1);
    onChanged();
  };

  const handleToggleActive = () => {
    setTogglingActive(true);
    prestadoresApi
      .setActive(prestador.id, !prestador.isActive)
      .then(handleChanged)
      .catch((err: unknown) => console.error("Error al cambiar el estado del PST:", err))
      .finally(() => setTogglingActive(false));
  };

  const handleDeleteContacto = (contacto: Contacto) => {
    prestadoresApi
      .deleteContacto(prestador.id, contacto.id)
      .then(handleChanged)
      .catch((err: unknown) => console.error("Error al eliminar el contacto:", err));
  };

  return (
    <>
      <BrandModal isOpen onClose={onClose} title={prestador.denComercial} widthPx={520}>
        <div className="flex flex-col gap-5">
          <div className="flex flex-wrap items-center gap-2">
            <BrandBadge variant={prestador.isActive ? "success" : "neutral"}>
              {prestador.isActive ? "Activo" : "Inactivo"}
            </BrandBadge>
            <BrandBadge variant="neutral">Siges #{prestador.sigesEmpresaId}</BrandBadge>
          </div>

          <div className="grid grid-cols-2 gap-3 font-body text-sm">
            <div>
              <p className="text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
                Razón social
              </p>
              <p className="text-foreground">{prestador.razonSocial ?? "—"}</p>
            </div>
            <div>
              <p className="text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
                CUIT
              </p>
              <p className="text-foreground">{prestador.cuit ?? "—"}</p>
            </div>
          </div>

          <div className="flex items-center justify-between rounded-[10px] border border-border bg-muted/50 px-3 py-2.5">
            <div className="flex items-center gap-2.5">
              {prestador.operadorId ? (
                <UserAvatar
                  fullName={prestador.operadorNombre ?? "?"}
                  color={prestador.operadorColor}
                  size="sm"
                />
              ) : null}
              <span className="font-body text-sm font-semibold text-foreground">
                {prestador.operadorNombre ?? "Sin operador asignado"}
              </span>
            </div>
            {canEdit && (
              <button
                type="button"
                onClick={() => setOverlay("assign")}
                className="font-body text-xs font-bold uppercase tracking-wide text-brand-orange hover:underline"
              >
                Reasignar
              </button>
            )}
          </div>

          <PrestadorContactosList
            contactos={prestador.contactos}
            onAdd={() => setOverlay({ contacto: null })}
            onEdit={(contacto) => setOverlay({ contacto })}
            onDelete={handleDeleteContacto}
          />

          <div>
            <h3 className="mb-2 font-heading text-sm font-bold uppercase tracking-wide text-foreground">
              Historial de asignación
            </h3>
            <PrestadorHistorialPanel key={historialKey} prestadorId={prestador.id} />
          </div>

          {canEdit && (
            <div className="flex justify-end gap-2 border-t border-border pt-4">
              {canDelete && (
                <BrandButton
                  type="button"
                  variant="outline"
                  loading={togglingActive}
                  onClick={handleToggleActive}
                >
                  {prestador.isActive ? "Dar de baja" : "Reactivar"}
                </BrandButton>
              )}
              <BrandButton type="button" onClick={() => setOverlay("edit")}>
                Editar
              </BrandButton>
            </div>
          )}
        </div>
      </BrandModal>

      {overlay === "edit" && (
        <PrestadorFormModal
          prestador={prestador}
          operadores={operadores}
          onClose={() => setOverlay(null)}
          onSaved={() => {
            setOverlay(null);
            handleChanged();
          }}
        />
      )}
      {overlay === "assign" && (
        <AssignOperadorModal
          prestador={prestador}
          operadores={operadores}
          onClose={() => setOverlay(null)}
          onAssigned={() => {
            setOverlay(null);
            handleChanged();
          }}
        />
      )}
      {overlay !== null && typeof overlay === "object" && (
        <ContactoFormModal
          prestadorId={prestador.id}
          contacto={overlay.contacto}
          onClose={() => setOverlay(null)}
          onSaved={() => {
            setOverlay(null);
            handleChanged();
          }}
        />
      )}
    </>
  );
}
