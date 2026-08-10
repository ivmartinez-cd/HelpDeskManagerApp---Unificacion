"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Download, FolderSync, Plus, SquarePen, Trash2 } from "lucide-react";
import { contadoresApi, type FtpClient } from "../api/contadores-api";
import { useFtpClients } from "../hooks/use-ftp-clients";
import { FtpClientModal } from "./ftp-client-modal";
import { ProcessClientModal } from "./process-client-modal";
import { Input } from "@/shared/components/ui/input";
import { Button } from "@/shared/components/ui/button";
import { Card } from "@/shared/components/ui/card";
import { EmptyState } from "@/shared/components/ui/empty-state";
import { Skeleton } from "@/shared/components/ui/skeleton";

export function FtpClientsTool() {
  const { clients, loading, refetch } = useFtpClients();
  const [searchQuery, setSearchQuery] = useState("");

  const [createEditOpen, setCreateEditOpen] = useState(false);
  const [editingClient, setEditingClient] = useState<FtpClient | null>(null);

  const [processOpen, setProcessOpen] = useState(false);
  const [processingClient, setProcessingClient] = useState<FtpClient | null>(null);

  const handleDelete = async (client: FtpClient) => {
    if (!confirm(`¿Estás seguro de eliminar el cliente FTP "${client.name}"?`)) {
      return;
    }
    try {
      await contadoresApi.deleteFtpClient(client.id);
      toast.success(`Cliente "${client.name}" eliminado`);
      refetch();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Error al eliminar cliente";
      toast.error(message);
    }
  };

  const filteredClients = clients.filter(
    (c) =>
      c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.host.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.username.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <Input
          id="ftp-search"
          aria-label="Buscar clientes FTP"
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Buscar por nombre, servidor o usuario..."
          className="max-w-md"
        />

        <Button
          onClick={() => {
            setEditingClient(null);
            setCreateEditOpen(true);
          }}
          className="shrink-0"
        >
          <Plus className="h-4 w-4" />
          Nuevo Cliente FTP
        </Button>
      </div>

      {loading ? (
        <div className="space-y-2">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </div>
      ) : filteredClients.length === 0 ? (
        <EmptyState icon={FolderSync} title="No se encontraron clientes FTP" />
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-black/10 dark:border-white/10 bg-muted/40 font-bold uppercase tracking-wider text-muted-foreground">
                <tr>
                  <th scope="col" className="px-4 py-3">
                    Nombre del Cliente
                  </th>
                  <th scope="col" className="px-4 py-3">
                    Servidor / Host
                  </th>
                  <th scope="col" className="px-4 py-3">
                    Usuario
                  </th>
                  <th scope="col" className="px-4 py-3">
                    Directorio
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
                    <td className="px-4 py-3 text-muted-foreground">
                      {client.host}:{client.port}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">{client.username}</td>
                    <td className="px-4 py-3 text-muted-foreground">{client.remote_dir}</td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          type="button"
                          onClick={() => {
                            setProcessingClient(client);
                            setProcessOpen(true);
                          }}
                          className="flex items-center gap-1 rounded-lg bg-success/10 px-2.5 py-1 font-semibold text-success transition-all hover:bg-success/20"
                          aria-label={`Descargar y procesar DB3 de ${client.name}`}
                        >
                          <Download className="h-3.5 w-3.5" />
                          Procesar DB3
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            setEditingClient(client);
                            setCreateEditOpen(true);
                          }}
                          className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground"
                          aria-label={`Editar ${client.name}`}
                          title="Editar"
                        >
                          <SquarePen className="h-4 w-4" />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDelete(client)}
                          className="rounded-lg p-1.5 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                          aria-label={`Eliminar ${client.name}`}
                          title="Eliminar"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      <FtpClientModal
        isOpen={createEditOpen}
        client={editingClient}
        onClose={() => setCreateEditOpen(false)}
        onSuccess={refetch}
      />

      {processingClient && (
        <ProcessClientModal
          isOpen={processOpen}
          type="ftp"
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
