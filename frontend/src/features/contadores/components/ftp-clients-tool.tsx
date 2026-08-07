"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import {
  Download,
  Edit2,
  FolderSync,
  Loader2,
  Plus,
  Search,
  Trash2,
} from "lucide-react";
import { contadoresApi, type FtpClient } from "../api/contadores-api";
import { FtpClientModal } from "./ftp-client-modal";
import { ProcessClientModal } from "./process-client-modal";

export function FtpClientsTool() {
  const [clients, setClients] = useState<FtpClient[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  // Modal states
  const [createEditOpen, setCreateEditOpen] = useState(false);
  const [editingClient, setEditingClient] = useState<FtpClient | null>(null);

  const [processOpen, setProcessOpen] = useState(false);
  const [processingClient, setProcessingClient] = useState<FtpClient | null>(null);

  const fetchClients = async () => {
    setLoading(true);
    try {
      const data = await contadoresApi.listFtpClients();
      setClients(data);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Error al cargar clientes FTP";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let active = true;
    contadoresApi
      .listFtpClients()
      .then((data) => {
        if (active) {
          setClients(data);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          const message = err instanceof Error ? err.message : "Error al cargar clientes FTP";
          toast.error(message);
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  const handleDelete = async (client: FtpClient) => {
    if (!confirm(`¿Estás seguro de eliminar el cliente FTP "${client.name}"?`)) {
      return;
    }
    try {
      await contadoresApi.deleteFtpClient(client.id);
      toast.success(`Cliente "${client.name}" eliminado`);
      fetchClients();
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
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Buscar por nombre, servidor o usuario..."
            className="w-full rounded-xl border border-input bg-background pl-9 pr-3 py-2 text-sm"
          />
        </div>

        <button
          onClick={() => {
            setEditingClient(null);
            setCreateEditOpen(true);
          }}
          className="flex items-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-xs font-bold uppercase tracking-wider text-primary-foreground shadow-md shadow-primary/20 hover:bg-primary/90 transition-all shrink-0"
        >
          <Plus className="h-4 w-4" />
          Nuevo Cliente FTP
        </button>
      </div>

      {loading ? (
        <div className="flex h-48 items-center justify-center rounded-2xl border border-border bg-card">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </div>
      ) : filteredClients.length === 0 ? (
        <div className="flex h-48 flex-col items-center justify-center rounded-2xl border border-dashed border-border bg-card p-6 text-center">
          <FolderSync className="h-10 w-10 text-muted-foreground/40 mb-2" />
          <p className="text-sm font-medium text-muted-foreground">
            No se encontraron clientes FTP
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-border bg-muted/40 uppercase tracking-wider text-muted-foreground font-bold">
                <tr>
                  <th className="px-4 py-3">Nombre del Cliente</th>
                  <th className="px-4 py-3">Servidor / Host</th>
                  <th className="px-4 py-3">Usuario</th>
                  <th className="px-4 py-3">Directorio</th>
                  <th className="px-4 py-3 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filteredClients.map((client) => (
                  <tr key={client.id} className="hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-3 font-semibold text-foreground">{client.name}</td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {client.host}:{client.port}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">{client.username}</td>
                    <td className="px-4 py-3 text-muted-foreground">{client.remote_dir}</td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => {
                            setProcessingClient(client);
                            setProcessOpen(true);
                          }}
                          className="flex items-center gap-1 rounded-lg bg-emerald-500/10 px-2.5 py-1 text-emerald-600 dark:text-emerald-400 font-semibold hover:bg-emerald-500/20 transition-all"
                          title="Descargar y Procesar DB3"
                        >
                          <Download className="h-3.5 w-3.5" />
                          Procesar DB3
                        </button>
                        <button
                          onClick={() => {
                            setEditingClient(client);
                            setCreateEditOpen(true);
                          }}
                          className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground"
                          title="Editar"
                        >
                          <Edit2 className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(client)}
                          className="rounded-lg p-1.5 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
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
        </div>
      )}

      {/* Modal CRUD */}
      <FtpClientModal
        isOpen={createEditOpen}
        client={editingClient}
        onClose={() => setCreateEditOpen(false)}
        onSuccess={fetchClients}
      />

      {/* Modal Procesar */}
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
