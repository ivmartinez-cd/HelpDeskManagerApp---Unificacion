"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Download, Loader2, Radio, Search } from "lucide-react";
import { contadoresApi, type ErsClient } from "../api/contadores-api";
import { ProcessClientModal } from "./process-client-modal";

export function ErsTool() {
  const [clients, setClients] = useState<ErsClient[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  const [processOpen, setProcessOpen] = useState(false);
  const [processingClient, setProcessingClient] = useState<ErsClient | null>(null);

  useEffect(() => {
    let active = true;
    contadoresApi
      .listErsClients()
      .then((data) => {
        if (active) {
          setClients(data);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          const message = err instanceof Error ? err.message : "Error al cargar grupos Epson ERS";
          toast.error(message);
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  const handleToggleSumaColor = async (client: ErsClient, newValue: boolean) => {
    try {
      await contadoresApi.updateErsConfig(client.id, {
        customer_name: client.name,
        suma_color: newValue,
      });
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
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Buscar por grupo Epson ERS..."
            className="w-full rounded-xl border border-input bg-background pl-9 pr-3 py-2 text-sm"
          />
        </div>
      </div>

      {loading ? (
        <div className="flex h-48 items-center justify-center rounded-2xl border border-border bg-card">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </div>
      ) : filteredClients.length === 0 ? (
        <div className="flex h-48 flex-col items-center justify-center rounded-2xl border border-dashed border-border bg-card p-6 text-center">
          <Radio className="h-10 w-10 text-muted-foreground/40 mb-2" />
          <p className="text-sm font-medium text-muted-foreground">
            No se encontraron grupos Epson ERS
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-border bg-muted/40 uppercase tracking-wider text-muted-foreground font-bold">
                <tr>
                  <th className="px-4 py-3">Grupo de Equipos Epson ERS</th>
                  <th className="px-4 py-3">ID de Grupo</th>
                  <th className="px-4 py-3">Suma Color</th>
                  <th className="px-4 py-3 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filteredClients.map((client) => (
                  <tr key={client.id} className="hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-3 font-semibold text-foreground">{client.name}</td>
                    <td className="px-4 py-3 text-muted-foreground font-mono text-[11px]">
                      {client.id}
                    </td>
                    <td className="px-4 py-3">
                      <label className="relative inline-flex cursor-pointer items-center">
                        <input
                          type="checkbox"
                          checked={client.suma_color}
                          onChange={(e) => handleToggleSumaColor(client, e.target.checked)}
                          className="peer sr-only"
                        />
                        <div className="h-5 w-9 rounded-full bg-muted peer-checked:bg-primary peer-focus:outline-none transition-colors after:absolute after:left-[2px] after:top-[2px] after:h-4 after:w-4 after:rounded-full after:bg-white after:transition-all peer-checked:after:translate-x-full" />
                        <span className="ml-2 text-xs text-muted-foreground">
                          {client.suma_color ? "Sí" : "No"}
                        </span>
                      </label>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => {
                          setProcessingClient(client);
                          setProcessOpen(true);
                        }}
                        className="inline-flex items-center gap-1 rounded-lg bg-emerald-500/10 px-2.5 py-1 text-emerald-600 dark:text-emerald-400 font-semibold hover:bg-emerald-500/20 transition-all"
                      >
                        <Download className="h-3.5 w-3.5" />
                        Descargar Telemetría
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modal Procesar */}
      {processingClient && (
        <ProcessClientModal
          isOpen={processOpen}
          type="ers"
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
