"use client";

import { BrandModal } from "@/shared/components/ui/brand-modal";
import { SegmentedControl } from "@/shared/components/ui/segmented-control";
import { Switch } from "@/shared/components/ui/switch";
import {
  CARD_LABELS,
  VIEWS,
  cardsDeVista,
  type CardId,
  type ModuleAccess,
  type ViewKey,
} from "../config/dashboard-registry";
import type { DashboardPrefs } from "../hooks/use-dashboard-prefs";

/** "Personalizar" de Inicio: qué paneles ve cada usuario (por vista) y con
 * qué vista abre. Los paneles que el usuario no tiene por permisos no
 * aparecen acá — esto solo resta sobre lo que ya puede ver. */
export function PersonalizarModal({
  isOpen,
  onClose,
  access,
  prefs,
  onOculto,
  onVistaInicial,
  onRestablecer,
}: {
  isOpen: boolean;
  onClose: () => void;
  access: ModuleAccess;
  prefs: DashboardPrefs;
  onOculto: (id: CardId, oculto: boolean) => void;
  onVistaInicial: (v: ViewKey) => void;
  onRestablecer: () => void;
}) {
  const ocultos = new Set(prefs.ocultos);
  return (
    <BrandModal isOpen={isOpen} onClose={onClose} title="Personalizar Inicio" widthPx={460}>
      <div className="flex flex-col gap-5">
        <section className="flex flex-col gap-2">
          <h3 className="font-heading text-[11px] font-bold uppercase tracking-[.05em] text-muted-foreground">
            Vista al entrar
          </h3>
          <SegmentedControl
            label="Vista al entrar"
            size="sm"
            value={prefs.vistaInicial}
            onChange={(v) => onVistaInicial(v as ViewKey)}
            options={VIEWS.map((v) => ({ value: v.key, label: v.label }))}
          />
        </section>

        {VIEWS.map((vista) => {
          const cards = cardsDeVista(vista.key, access);
          if (cards.length === 0) return null;
          return (
            <section key={vista.key} className="flex flex-col gap-1.5">
              <h3 className="font-heading text-[11px] font-bold uppercase tracking-[.05em] text-muted-foreground">
                Paneles · {vista.label}
              </h3>
              <ul className="flex flex-col divide-y divide-border/60 rounded-[10px] border border-border">
                {cards.map((id) => (
                  <li key={id} className="flex items-center justify-between gap-3 px-3 py-2">
                    <span className="font-body text-[13px] text-foreground">{CARD_LABELS[id]}</span>
                    <Switch
                      label={`Mostrar ${CARD_LABELS[id]}`}
                      checked={!ocultos.has(id)}
                      onCheckedChange={(checked) => onOculto(id, !checked)}
                    />
                  </li>
                ))}
              </ul>
            </section>
          );
        })}

        <div className="flex items-center justify-between">
          <button
            type="button"
            onClick={onRestablecer}
            className="font-body text-[12.5px] font-semibold text-muted-foreground hover:text-foreground"
          >
            Restablecer
          </button>
          <button
            type="button"
            onClick={onClose}
            className="rounded-[10px] bg-brand-orange px-4 py-2 font-body text-sm font-bold text-white hover:bg-brand-orange-hover"
          >
            Listo
          </button>
        </div>
      </div>
    </BrandModal>
  );
}
