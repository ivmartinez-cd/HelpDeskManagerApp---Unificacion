"use client";

import { useState } from "react";
import { Badge } from "@/shared/components/ui/badge";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";

/** Botón APB para toda acción que gasta la key paga de Google.
 *
 * - Estimación 0 → ejecuta directo (todo está en caché, no hay gasto).
 * - Estimación > 0 → modal de confirmación con el costo ANTES de ejecutar.
 * - Estimación > tope → advertencia de corte; con `bloquearSobreTope` el
 *   botón ni se habilita (para acciones que fallarían enteras, como el
 *   cálculo de distancias). */
export function BotonConsumoGoogle({
  children,
  estimacion,
  tope,
  onEjecutar,
  loading = false,
  disabled = false,
  bloquearSobreTope = false,
  variant = "primary",
  size,
  className,
}: {
  children: React.ReactNode;
  estimacion: number;
  tope: number;
  onEjecutar: () => void | Promise<void>;
  loading?: boolean;
  disabled?: boolean;
  bloquearSobreTope?: boolean;
  variant?: "primary" | "outline";
  size?: "sm";
  className?: string;
}) {
  const [confirmando, setConfirmando] = useState(false);
  const sobreTope = estimacion > tope;
  const bloqueado = bloquearSobreTope && sobreTope;

  const ejecutar = async () => {
    setConfirmando(false);
    await onEjecutar();
  };

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center gap-2">
        <BrandButton
          variant={variant}
          size={size}
          className={className}
          loading={loading}
          disabled={disabled || loading || bloqueado}
          onClick={() => (estimacion === 0 ? void ejecutar() : setConfirmando(true))}
        >
          {children}
        </BrandButton>
        {estimacion === 0 && !disabled && !bloqueado && (
          <Badge variant="success">sin costo — todo está en caché</Badge>
        )}
        {estimacion > 0 && !bloqueado && (
          <Badge variant={sobreTope ? "warning" : "info"}>~{estimacion} consultas a Google</Badge>
        )}
      </div>
      {bloqueado && (
        <p className="font-body text-xs text-destructive">
          Esta acción necesitaría ~{estimacion} consultas a Google y el tope por corrida
          es {tope} — no se puede ejecutar entera. Avisale al administrador si te pasa.
        </p>
      )}
      <BrandModal
        isOpen={confirmando}
        onClose={() => setConfirmando(false)}
        title="Esta acción consulta Google Maps"
        widthPx={460}
      >
        <div className="flex flex-col gap-4">
          <p className="font-body text-sm text-foreground">
            Se van a hacer aproximadamente{" "}
            <span className="font-bold text-brand-orange">{estimacion}</span> consultas a
            Google Maps (el tope por corrida es {tope}). Las consultas ya hechas quedan
            guardadas y no se repiten.
          </p>
          {sobreTope && (
            <p className="font-body text-sm text-foreground rounded-[8px] border border-warning/40 bg-warning/5 p-3">
              Supera el tope: la corrida se va a cortar al llegar a {tope}. Lo que quede
              pendiente se retoma en una próxima corrida sin costo repetido.
            </p>
          )}
          <div className="flex justify-end gap-2">
            <BrandButton variant="outline" onClick={() => setConfirmando(false)}>
              Cancelar
            </BrandButton>
            <BrandButton onClick={() => void ejecutar()}>Sí, consultar Google</BrandButton>
          </div>
        </div>
      </BrandModal>
    </div>
  );
}
