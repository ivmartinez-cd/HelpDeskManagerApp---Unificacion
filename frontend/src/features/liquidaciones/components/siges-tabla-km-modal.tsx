"use client";

import { useState } from "react";
import { toast } from "sonner";
import { BrandButton, BrandInput } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { Badge } from "@/shared/components/ui/badge";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { SucursalSiges } from "../types/liquidaciones";

// Alta asistida (ADR-014 DS3): solo búsqueda de lectura — el alta real la hace
// el usuario en el modal de Nueva Entrada, prefillado; nada se pisa ni se borra.
export function SigesTablaKmModal({
  prestadorId,
  onClose,
  onUsar,
}: {
  prestadorId: string;
  onClose: () => void;
  onUsar: (sucursal: SucursalSiges) => void;
}) {
  const [q, setQ] = useState("");
  const [resultados, setResultados] = useState<SucursalSiges[] | null>(null);
  const [total, setTotal] = useState(0);
  const [buscando, setBuscando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleBuscar = async (e: React.FormEvent) => {
    e.preventDefault();
    setBuscando(true);
    setError(null);
    try {
      const page = await liquidacionesApi.buscarSucursalesSiges(prestadorId, q);
      setResultados(page.items);
      setTotal(page.total);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al consultar Siges");
    } finally {
      setBuscando(false);
    }
  };

  const handleUsar = (sucursal: SucursalSiges) => {
    if (sucursal.yaCargada) {
      toast.info("Ese par ya está cargado en la Tabla KM");
      return;
    }
    onUsar(sucursal);
  };

  return (
    <BrandModal
      isOpen
      onClose={onClose}
      title="Agregar desde Siges"
      error={error}
      widthPx={580}
    >
      <div className="flex flex-col gap-4">
        <p className="font-body text-sm text-muted-foreground">
          Sucursales de cliente asignadas a este PST en Siges. Elegí una para precargar la
          entrada nueva — el km recorrido se completa a mano (no existe en Siges) y las
          entradas ya cargadas no se tocan.
        </p>
        <form onSubmit={handleBuscar} className="flex items-end gap-2">
          <div className="flex-1">
            <BrandInput
              label="Cliente o sucursal"
              value={q}
              placeholder="Ej.: Credicoop, Aeropuerto..."
              onChange={(e) => setQ(e.target.value)}
            />
          </div>
          <BrandButton type="submit" loading={buscando}>Buscar</BrandButton>
        </form>

        {resultados !== null && (
          <div className="max-h-[45vh] overflow-y-auto">
            {resultados.length === 0 && (
              <p className="font-body text-sm text-muted-foreground">Sin resultados.</p>
            )}
            {resultados.map((s) => (
              <div
                key={s.sigesSucursalId}
                className="flex items-center justify-between gap-3 border-t border-border py-2 first:border-t-0"
              >
                <div className="min-w-0">
                  <p className="truncate font-body text-sm text-foreground">
                    <span className="font-bold">{s.empresaNombre}</span> · {s.sucursalNombre}
                  </p>
                  <p className="truncate font-body text-xs text-muted-foreground">
                    {[s.domicilio, s.localidad, s.provincia].filter(Boolean).join(" · ") ||
                      "Sin domicilio cargado en Siges"}
                  </p>
                </div>
                {s.yaCargada ? (
                  <Badge variant="neutral">Ya cargada</Badge>
                ) : (
                  <BrandButton size="sm" variant="outline" onClick={() => handleUsar(s)}>
                    Usar
                  </BrandButton>
                )}
              </div>
            ))}
            {total > resultados.length && (
              <p className="mt-2 font-body text-xs text-muted-foreground">
                Mostrando {resultados.length} de {total} — refiná la búsqueda.
              </p>
            )}
          </div>
        )}

        <div className="flex justify-end pt-1">
          <BrandButton variant="outline" onClick={onClose}>Cerrar</BrandButton>
        </div>
      </div>
    </BrandModal>
  );
}
