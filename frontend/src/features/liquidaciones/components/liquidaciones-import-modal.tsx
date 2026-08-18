"use client";

import { useCallback, useRef, useState } from "react";
import { Upload } from "lucide-react";
import { toast } from "sonner";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { PrestadorLiquidacion } from "../types/liquidaciones";

interface ImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  prestadores: PrestadorLiquidacion[];
  onSuccess: () => void;
}

export function LiquidacionesImportModal({
  isOpen,
  onClose,
  prestadores,
  onSuccess,
}: ImportModalProps) {
  const [prestadorId, setPrestadorId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const reset = useCallback(() => {
    setPrestadorId("");
    setFile(null);
    setError(null);
    if (fileRef.current) fileRef.current.value = "";
  }, []);

  const handleClose = () => {
    reset();
    onClose();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prestadorId || !file) return;
    setLoading(true);
    setError(null);
    try {
      const res = await liquidacionesApi.importar(prestadorId, file);
      toast.success(
        `Liquidación importada: ${res.totalIncidentes} incidentes, ${res.totalAlertas} alertas.`,
      );
      reset();
      onClose();
      onSuccess();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al importar";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const labelCls = "block font-body text-xs font-semibold text-muted-foreground mb-1.5 uppercase tracking-wide";
  const inputCls =
    "w-full rounded-[8px] border border-border bg-muted px-3 py-2.5 font-body text-sm text-foreground outline-none focus:border-brand-orange/70 disabled:opacity-60";

  return (
    <BrandModal isOpen={isOpen} onClose={handleClose} title="Importar liquidación" error={error}>
      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        <div>
          <label htmlFor="liq-prestador" className={labelCls}>
            Prestador *
          </label>
          <select
            id="liq-prestador"
            required
            value={prestadorId}
            onChange={(e) => setPrestadorId(e.target.value)}
            className={inputCls}
          >
            <option value="">Seleccioná un prestador...</option>
            {prestadores.map((p) => (
              <option key={p.id} value={p.id}>
                {p.nombreCorto} — {p.nombre}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className={labelCls}>Archivo (.xls / .xlsx / .html) *</label>
          <label
            className="flex cursor-pointer flex-col items-center gap-3 rounded-[10px] border-2 border-dashed border-border p-6 text-center transition-colors hover:border-brand-orange/50"
            htmlFor="liq-file"
          >
            <Upload className="h-7 w-7 text-muted-foreground" aria-hidden="true" />
            <span className="font-body text-sm text-muted-foreground">
              {file ? (
                <span className="font-semibold text-foreground">{file.name}</span>
              ) : (
                "Hacé click para seleccionar el archivo"
              )}
            </span>
            <input
              ref={fileRef}
              id="liq-file"
              type="file"
              accept=".xls,.xlsx,.html"
              required
              className="sr-only"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </label>
        </div>

        <div className="flex justify-end gap-3 pt-2">
          <button
            type="button"
            onClick={handleClose}
            className="rounded-[8px] border border-border px-4 py-2.5 font-body text-sm text-muted-foreground transition-colors hover:bg-muted"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={loading || !prestadorId || !file}
            className="rounded-[8px] bg-brand-orange px-5 py-2.5 font-body text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {loading ? "Importando..." : "Importar liquidación"}
          </button>
        </div>
      </form>
    </BrandModal>
  );
}
