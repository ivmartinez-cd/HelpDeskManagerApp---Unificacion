"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Download, type LucideIcon } from "lucide-react";
import { ProcessClientModal } from "./process-client-modal";
import { Input } from "@/shared/components/ui/input";
import { Card } from "@/shared/components/ui/card";
import { EmptyState } from "@/shared/components/ui/empty-state";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { Switch } from "@/shared/components/ui/switch";

interface MeterClient {
  id: string;
  name: string;
  suma_color: boolean;
}

interface MeterClientsToolProps<T extends MeterClient> {
  processType: "sds" | "ers";
  listClients: () => Promise<T[]>;
  updateConfig: (id: string, payload: { customer_name: string; suma_color: boolean }) => Promise<unknown>;
  loadErrorMessage: string;
  searchAriaLabel: string;
  searchPlaceholder: string;
  emptyIcon: LucideIcon;
  emptyTitle: string;
  clientColumnLabel: string;
  idColumnLabel: string;
  downloadButtonLabel: string;
}

export function MeterClientsTool<T extends MeterClient>({
  processType,
  listClients,
  updateConfig,
  loadErrorMessage,
  searchAriaLabel,
  searchPlaceholder,
  emptyIcon,
  emptyTitle,
  clientColumnLabel,
  idColumnLabel,
  downloadButtonLabel,
}: MeterClientsToolProps<T>) {
  const [clients, setClients] = useState<T[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  const [processOpen, setProcessOpen] = useState(false);
  const [processingClient, setProcessingClient] = useState<T | null>(null);

  useEffect(() => {
    let active = true;
    listClients()
      .then((data) => {
        if (active) {
          setClients(data);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          const message = err instanceof Error ? err.message : loadErrorMessage;
          toast.error(message);
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleToggleSumaColor = async (client: T, newValue: boolean) => {
    try {
      await updateConfig(client.id, { customer_name: client.name, suma_color: newValue });
      setClients((prev) =>
        prev.map((c) => (c.id === client.id ? { ...c, suma_color: newValue } : c)),
      );
      toast.success(
        `Configuración de ${client.name} actualizada (${newValue ? "Suma Color activada" : "Suma Color desactivada"})`,
      );
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Error al actualizar configuración";
      toast.error(message);
    }
  };

  const filteredClients = clients.filter((c) =>
    c.name.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  return (
    <div className="space-y-6">
      <Input
        id={`${processType}-search`}
        aria-label={searchAriaLabel}
        type="text"
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        placeholder={searchPlaceholder}
        className="max-w-md"
      />

      {loading ? (
        <div className="space-y-2">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </div>
      ) : filteredClients.length === 0 ? (
        <EmptyState icon={emptyIcon} title={emptyTitle} />
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-black/10 dark:border-white/10 bg-muted/40 font-bold uppercase tracking-wider text-muted-foreground">
                <tr>
                  <th scope="col" className="px-4 py-3">
                    {clientColumnLabel}
                  </th>
                  <th scope="col" className="px-4 py-3">
                    {idColumnLabel}
                  </th>
                  <th scope="col" className="px-4 py-3">
                    Suma Color
                  </th>
                  <th scope="col" className="px-4 py-3 text-right">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-black/10 dark:divide-white/10">
                {filteredClients.map((client) => (
                  <tr key={client.id} className="transition-colors hover:bg-muted/30">
                    <td className="px-4 py-3 font-semibold text-foreground">{client.name}</td>
                    <td className="px-4 py-3 font-mono text-[11px] text-muted-foreground">
                      {client.id}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <Switch
                          checked={client.suma_color}
                          onCheckedChange={(checked) => handleToggleSumaColor(client, checked)}
                          label={`Suma Color para ${client.name}`}
                        />
                        <span className="text-xs text-muted-foreground">
                          {client.suma_color ? "Sí" : "No"}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        type="button"
                        onClick={() => {
                          setProcessingClient(client);
                          setProcessOpen(true);
                        }}
                        className="inline-flex items-center gap-1 rounded-lg bg-success/10 px-2.5 py-1 font-semibold text-success transition-all hover:bg-success/20"
                      >
                        <Download className="h-3.5 w-3.5" />
                        {downloadButtonLabel}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {processingClient && (
        <ProcessClientModal
          isOpen={processOpen}
          type={processType}
          targetId={processingClient.id}
          targetName={processingClient.name}
          onClose={() => {
            setProcessOpen(false);
            setProcessingClient(null);
          }}
        />
      )}
    </div>
  );
}
