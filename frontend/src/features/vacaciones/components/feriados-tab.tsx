"use client";

import { useState } from "react";
import { CalendarDays, CloudDownload, Download } from "lucide-react";
import { ApiError } from "@/services/http-client";
import {
  BrandBadge,
  BrandButton,
  BrandEmptyState,
  BrandInput,
} from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { gestionApi } from "../api/gestion-api";
import { formatFecha, hoyIso } from "../lib/fechas";
import type { Feriado, FeriadoPayload } from "../types/vacaciones";

interface Props {
  feriados: Feriado[];
  puedeGestionar: boolean;
  abrirAlta: boolean;
  onCerrarAlta: () => void;
  onChanged: () => void;
}

export function FeriadosTab({
  feriados,
  puedeGestionar,
  abrirAlta,
  onCerrarAlta,
  onChanged,
}: Props) {
  const [editando, setEditando] = useState<Feriado | null>(null);
  const [anioImport, setAnioImport] = useState(new Date().getFullYear());
  const [importando, setImportando] = useState(false);
  const [mensaje, setMensaje] = useState<string | null>(null);

  const importar = () => {
    setImportando(true);
    setMensaje(null);
    gestionApi
      .importarFeriados(anioImport)
      .then((r) => {
        setMensaje(r.message);
        onChanged();
      })
      .catch((err: unknown) => {
        setMensaje(
          err instanceof ApiError ? err.message : "No se pudieron importar los feriados.",
        );
      })
      .finally(() => setImportando(false));
  };

  return (
    <div className="flex flex-col gap-4">
      {puedeGestionar && (
        <div className="flex flex-wrap items-end justify-between gap-4 rounded-[12px] border border-border bg-card p-5">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-[10px] bg-brand-orange/15 text-brand-orange">
              <CloudDownload className="h-5 w-5" />
            </span>
            <div>
              <p className="font-heading text-sm font-bold text-foreground">
                Importar feriados de Argentina
              </p>
              <p className="font-body text-xs text-muted-foreground">
                Carga automática desde api.argentinadatos.com — pisa nombres por fecha
              </p>
            </div>
          </div>
          <div className="flex items-end gap-2">
            <div className="w-24">
              <BrandInput
                label="Año"
                type="number"
                value={anioImport}
                onChange={(e) => setAnioImport(Number(e.target.value))}
              />
            </div>
            <BrandButton onClick={importar} loading={importando}>
              <CloudDownload className="h-4 w-4" />
              Importar {anioImport}
            </BrandButton>
            <BrandButton
              variant="outline"
              onClick={() => void gestionApi.exportFeriados()}
            >
              <Download className="h-4 w-4" />
              Exportar backup
            </BrandButton>
          </div>
        </div>
      )}

      {mensaje && (
        <p className="rounded-[8px] bg-muted/30 px-4 py-3 font-body text-xs text-muted-foreground">
          {mensaje}
        </p>
      )}

      {feriados.length === 0 ? (
        <BrandEmptyState
          icon={CalendarDays}
          title="No hay feriados cargados"
          description="Importá los feriados del año o cargá uno manualmente."
        />
      ) : (
        <div className="overflow-x-auto rounded-[12px] border border-border">
          <table className="w-full min-w-[560px] font-body text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/30 text-left font-heading text-[11px] uppercase tracking-[.06em] text-muted-foreground">
                <th className="px-4 py-3">Fecha</th>
                <th className="px-4 py-3">Nombre</th>
                <th className="px-4 py-3">Cómputo</th>
                {puedeGestionar && <th className="px-4 py-3" />}
              </tr>
            </thead>
            <tbody>
              {feriados.map((f) => (
                <tr key={f.id} className="border-b border-border/60 last:border-0">
                  <td className="px-4 py-3 font-semibold text-foreground">
                    {formatFecha(f.date)}
                  </td>
                  <td className="px-4 py-3 text-foreground">{f.name}</td>
                  <td className="px-4 py-3">
                    <BrandBadge variant={f.deductsVacation ? "neutral" : "accent"}>
                      {f.deductsVacation ? "Cuenta como día" : "Desplaza inicio"}
                    </BrandBadge>
                  </td>
                  {puedeGestionar && (
                    <td className="px-4 py-3 text-right">
                      <button
                        type="button"
                        onClick={() => setEditando(f)}
                        className="rounded-[8px] border border-border px-3 py-1.5 text-xs font-semibold text-foreground hover:bg-muted"
                      >
                        Editar
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {(abrirAlta || editando) && (
        <FeriadoModal
          feriado={editando}
          onClose={() => {
            onCerrarAlta();
            setEditando(null);
          }}
          onSaved={() => {
            onCerrarAlta();
            setEditando(null);
            onChanged();
          }}
        />
      )}
    </div>
  );
}

function FeriadoModal({
  feriado,
  onClose,
  onSaved,
}: {
  feriado: Feriado | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [form, setForm] = useState<FeriadoPayload>({
    name: feriado?.name ?? "",
    date: feriado?.date ?? hoyIso(),
    deductsVacation: feriado?.deductsVacation ?? false,
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const guardar = () => {
    setBusy(true);
    setError(null);
    const req = feriado
      ? gestionApi.updateFeriado(feriado.id, form)
      : gestionApi.createFeriado(form);
    req
      .then(onSaved)
      .catch((err: unknown) => {
        setError(err instanceof ApiError ? err.message : "No se pudo guardar el feriado.");
      })
      .finally(() => setBusy(false));
  };

  const eliminar = () => {
    if (!feriado) return;
    setBusy(true);
    gestionApi
      .deleteFeriado(feriado.id)
      .then(onSaved)
      .catch((err: unknown) => {
        setError(err instanceof ApiError ? err.message : "No se pudo eliminar el feriado.");
      })
      .finally(() => setBusy(false));
  };

  return (
    <BrandModal
      isOpen
      onClose={onClose}
      title={feriado ? "Editar feriado" : "Nuevo feriado"}
      widthPx={440}
      error={error}
    >
      <div className="flex flex-col gap-4">
        <BrandInput
          label="Nombre"
          value={form.name}
          onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
        />
        <BrandInput
          label="Fecha"
          type="date"
          value={form.date}
          onChange={(e) => setForm((f) => ({ ...f, date: e.target.value }))}
        />
        <label className="flex items-start gap-2.5 font-body text-sm text-foreground">
          <input
            type="checkbox"
            checked={form.deductsVacation}
            onChange={(e) => setForm((f) => ({ ...f, deductsVacation: e.target.checked }))}
            className="mt-0.5 h-4 w-4 accent-brand-orange"
          />
          <span>
            Cuenta como día de vacaciones
            <span className="block text-xs text-muted-foreground">
              Si queda destildado y el feriado cae en el inicio de una solicitud, desplaza el
              comienzo (resta 1 día del cómputo).
            </span>
          </span>
        </label>
        <div className="mt-1 flex items-center justify-between gap-2">
          {feriado ? (
            <BrandButton
              variant="outline"
              onClick={eliminar}
              disabled={busy}
              className="border-destructive/40 text-destructive hover:bg-destructive/10"
            >
              Eliminar
            </BrandButton>
          ) : (
            <span />
          )}
          <div className="flex gap-2">
            <BrandButton variant="outline" onClick={onClose} disabled={busy}>
              Cancelar
            </BrandButton>
            <BrandButton onClick={guardar} loading={busy}>
              {feriado ? "Guardar cambios" : "Crear feriado"}
            </BrandButton>
          </div>
        </div>
      </div>
    </BrandModal>
  );
}
