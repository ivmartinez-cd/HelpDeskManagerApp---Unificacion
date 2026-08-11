"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { Switch } from "@/shared/components/ui/switch";
import { BrandSkeleton } from "@/shared/components/ui/brand-form";
import { contadoresApi } from "../api/contadores-api";
import type { PickerClientType } from "./client-picker-process-modal";

interface MeterClient {
  id: string;
  name: string;
  suma_color: boolean;
}

const TITLE: Record<"sds" | "ers", string> = {
  sds: "Clientes HP SDS",
  ers: "Grupos Epson ERS",
};

interface Props {
  isOpen: boolean;
  type: Exclude<PickerClientType, "ftp">;
  onClose: () => void;
}

/** Gestión (solo lectura + Suma Color) de clientes SDS/ERS — no tienen alta
 * manual, se sincronizan desde el API del proveedor (HP/Epson), a diferencia
 * de FTP (ver manage-ftp-clients-modal.tsx). */
export function ManageMeterClientsModal({ isOpen, type, onClose }: Props) {
  const [clients, setClients] = useState<MeterClient[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    if (!isOpen) return;
    let active = true;
    const list = type === "sds" ? contadoresApi.listSdsClients : contadoresApi.listErsClients;
    list()
      .then((data) => {
        if (active) setClients(data);
      })
      .catch((err: unknown) => {
        if (active) toast.error(err instanceof Error ? err.message : "Error al cargar clientes");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [isOpen, type]);

  const handleToggle = async (client: MeterClient, value: boolean) => {
    try {
      const update = type === "sds" ? contadoresApi.updateSdsConfig : contadoresApi.updateErsConfig;
      await update(client.id, { customer_name: client.name, suma_color: value });
      setClients((prev) => prev.map((c) => (c.id === client.id ? { ...c, suma_color: value } : c)));
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Error al actualizar configuración");
    }
  };

  const filtered = clients.filter((c) => c.name.toLowerCase().includes(search.toLowerCase()));

  return (
    <BrandModal isOpen={isOpen} onClose={onClose} title={TITLE[type]} widthPx={560}>
      <div className="flex flex-col gap-4">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Buscar cliente..."
          aria-label="Buscar cliente"
          className="rounded-[8px] border border-border px-[14px] py-[9px] font-body text-sm text-foreground outline-none focus:ring-2 focus:ring-brand-orange/40"
        />

        {loading ? (
          <div className="flex flex-col gap-2">
            <BrandSkeleton className="h-10 w-full" />
            <BrandSkeleton className="h-10 w-full" />
            <BrandSkeleton className="h-10 w-full" />
          </div>
        ) : filtered.length === 0 ? (
          <p className="py-6 text-center font-body text-sm text-muted-foreground">
            No se encontraron clientes.
          </p>
        ) : (
          <div className="max-h-[50vh] overflow-y-auto thin-scrollbar rounded-[10px] border border-border">
            <table className="w-full text-left font-body text-[13px]">
              <thead className="sticky top-0 border-b border-border bg-muted text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
                <tr>
                  <th className="px-3 py-2.5">Cliente</th>
                  <th className="px-3 py-2.5">Suma Color</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filtered.map((client) => (
                  <tr key={client.id}>
                    <td className="px-3 py-2.5 font-semibold text-foreground">{client.name}</td>
                    <td className="px-3 py-2.5">
                      <Switch
                        checked={client.suma_color}
                        onCheckedChange={(checked) => handleToggle(client, checked)}
                        label={`Suma Color para ${client.name}`}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </BrandModal>
  );
}
