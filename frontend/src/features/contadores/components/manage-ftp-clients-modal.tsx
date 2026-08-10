"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Plus, SquarePen, Trash2 } from "lucide-react";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { BrandSkeleton } from "@/shared/components/ui/brand-form";
import { contadoresApi, type FtpClient } from "../api/contadores-api";
import { useFtpClients } from "../hooks/use-ftp-clients";
import { FtpClientModal } from "./ftp-client-modal";

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

/** Gestión completa (alta/edición/borrado) de clientes FTP — a diferencia de
 * SDS/ERS, estos sí se cargan a mano (ver manage-meter-clients-modal.tsx
 * para el equivalente de solo lectura). El "Procesar DB3" puntual vive en
 * client-picker-process-modal.tsx, no acá. */
export function ManageFtpClientsModal({ isOpen, onClose }: Props) {
  const { clients, loading, refetch } = useFtpClients();
  const [search, setSearch] = useState("");
  const [editOpen, setEditOpen] = useState(false);
  const [editingClient, setEditingClient] = useState<FtpClient | null>(null);

  const handleDelete = async (client: FtpClient) => {
    if (!confirm(`¿Eliminar el cliente FTP "${client.name}"?`)) return;
    try {
      await contadoresApi.deleteFtpClient(client.id);
      toast.success(`Cliente "${client.name}" eliminado`);
      refetch();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Error al eliminar cliente");
    }
  };

  const filtered = clients.filter(
    (c) =>
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      c.host.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <>
      <BrandModal isOpen={isOpen} onClose={onClose} title="Clientes FTP" widthPx={640}>
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-3">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Buscar por nombre o servidor..."
              aria-label="Buscar cliente FTP"
              className="flex-1 rounded-[8px] border border-black/[0.14] px-[14px] py-[9px] font-body text-sm text-brand-charcoal outline-none focus:ring-2 focus:ring-brand-orange/40"
            />
            <button
              type="button"
              onClick={() => {
                setEditingClient(null);
                setEditOpen(true);
              }}
              className="flex flex-none items-center gap-1.5 rounded-[8px] bg-brand-orange px-3 py-2 font-body text-xs font-bold text-white transition-colors hover:bg-brand-orange-hover"
            >
              <Plus className="h-3.5 w-3.5" />
              Nuevo
            </button>
          </div>

          {loading ? (
            <div className="flex flex-col gap-2">
              <BrandSkeleton className="h-10 w-full" />
              <BrandSkeleton className="h-10 w-full" />
              <BrandSkeleton className="h-10 w-full" />
            </div>
          ) : filtered.length === 0 ? (
            <p className="py-6 text-center font-body text-sm text-[#9a9a9a]">
              No se encontraron clientes.
            </p>
          ) : (
            <div className="max-h-[50vh] overflow-y-auto thin-scrollbar rounded-[10px] border border-black/[0.08]">
              <table className="w-full text-left font-body text-[13px]">
                <thead className="sticky top-0 border-b border-black/[0.08] bg-brand-surface text-[11px] font-bold uppercase tracking-wide text-[#7a7a7a]">
                  <tr>
                    <th className="px-3 py-2.5">Cliente</th>
                    <th className="px-3 py-2.5">Servidor</th>
                    <th className="px-3 py-2.5 text-right">Acciones</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-black/[0.06]">
                  {filtered.map((client) => (
                    <tr key={client.id}>
                      <td className="px-3 py-2.5 font-semibold text-brand-charcoal">
                        {client.name}
                      </td>
                      <td className="px-3 py-2.5 text-[#6b6b6b]">
                        {client.host}:{client.port}
                      </td>
                      <td className="px-3 py-2.5">
                        <div className="flex items-center justify-end gap-1">
                          <button
                            type="button"
                            onClick={() => {
                              setEditingClient(client);
                              setEditOpen(true);
                            }}
                            aria-label={`Editar ${client.name}`}
                            title="Editar"
                            className="rounded-[6px] p-1.5 text-[#9a9a9a] hover:bg-black/5 hover:text-brand-charcoal"
                          >
                            <SquarePen className="h-4 w-4" />
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDelete(client)}
                            aria-label={`Eliminar ${client.name}`}
                            title="Eliminar"
                            className="rounded-[6px] p-1.5 text-[#9a9a9a] hover:bg-destructive/10 hover:text-destructive"
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
          )}
        </div>
      </BrandModal>

      <FtpClientModal
        isOpen={editOpen}
        client={editingClient}
        onClose={() => setEditOpen(false)}
        onSuccess={refetch}
      />
    </>
  );
}
