"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { BrandInput } from "@/shared/components/ui/brand-form";
import { Badge } from "@/shared/components/ui/badge";
import { Spinner } from "@/shared/components/ui/spinner";
import { liquidacionesApi } from "@/features/liquidaciones/api/liquidaciones-api";
import type { PrestadorLiquidacion, SigesEmpresa, SucursalPropia } from "@/features/liquidaciones/types/liquidaciones";
import { PasoAcciones } from "./alta-prestador-wizard-ui";

function coincide(e: SigesEmpresa, q: string): boolean {
  const s = q.trim().toLowerCase();
  if (!s) return true;
  return (
    e.denComercial.toLowerCase().includes(s) ||
    (e.cuit ?? "").includes(s) ||
    String(e.sigesEmpresaId).includes(s)
  );
}

export function PasoSiges({
  prestador,
  onVinculado,
  onSaltear,
}: {
  prestador: PrestadorLiquidacion;
  onVinculado: (empresa: SigesEmpresa) => void;
  onSaltear: () => void;
}) {
  const [disponibles, setDisponibles] = useState<SigesEmpresa[] | null>(null);
  const [q, setQ] = useState("");
  const [seleccionada, setSeleccionada] = useState<SigesEmpresa | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    liquidacionesApi
      .getSigesPropuestas()
      .then((r) => setDisponibles(r.disponibles))
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Error al cargar Siges"));
  }, []);

  const confirmar = async () => {
    if (!seleccionada) return;
    setSaving(true);
    setError(null);
    try {
      await liquidacionesApi.vincularPrestadorSiges(prestador.id, seleccionada.sigesEmpresaId);
      toast.success("Vínculo Siges guardado");
      onVinculado(seleccionada);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al vincular");
    } finally {
      setSaving(false);
    }
  };

  const filtradas = (disponibles ?? []).filter((e) => coincide(e, q));

  return (
    <div className="flex flex-col gap-4">
      <p className="font-body text-sm text-muted-foreground">
        Buscá la empresa de {prestador.nombreCorto} en el catálogo PST/SPST de Siges.
        Este vínculo habilita el resto de los pasos (base de despacho y alta en el
        módulo SLA).
      </p>
      {disponibles === null ? (
        <div className="flex h-24 items-center justify-center"><Spinner /></div>
      ) : (
        <>
          <BrandInput label="Buscar" placeholder="Nombre, CUIT o id" value={q} onChange={(e) => setQ(e.target.value)} />
          <div className="max-h-64 overflow-y-auto rounded-[8px] border border-border">
            {filtradas.map((emp) => (
              <label
                key={emp.sigesEmpresaId}
                className={`flex cursor-pointer items-center gap-3 px-4 py-3 transition-colors hover:bg-muted/30 ${
                  seleccionada?.sigesEmpresaId === emp.sigesEmpresaId ? "bg-brand-orange/5" : ""
                }`}
              >
                <input
                  type="radio"
                  name="siges-empresa"
                  checked={seleccionada?.sigesEmpresaId === emp.sigesEmpresaId}
                  onChange={() => setSeleccionada(emp)}
                  className="accent-brand-orange"
                />
                <span className="flex-1 font-body text-sm">{emp.denComercial}</span>
                <Badge variant="neutral">#{emp.sigesEmpresaId}</Badge>
              </label>
            ))}
            {filtradas.length === 0 && (
              <p className="p-4 font-body text-sm text-muted-foreground italic">Sin resultados.</p>
            )}
          </div>
        </>
      )}
      {error && <p className="font-body text-sm text-destructive">{error}</p>}
      <PasoAcciones
        onSaltear={onSaltear}
        primario={confirmar}
        primarioTexto="Vincular y continuar →"
        primarioDisabled={!seleccionada}
        saving={saving}
      />
    </div>
  );
}

export function PasoBase({
  prestador,
  sigesVinculado,
  onVinculado,
  onSaltear,
}: {
  prestador: PrestadorLiquidacion;
  sigesVinculado: boolean;
  onVinculado: () => void;
  onSaltear: () => void;
}) {
  const [sucursales, setSucursales] = useState<SucursalPropia[] | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sigesVinculado) return;
    liquidacionesApi
      .listSucursalesPropiasPrestatdor(prestador.id)
      .then(setSucursales)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Error al cargar sucursales"));
  }, [prestador.id, sigesVinculado]);

  if (!sigesVinculado) {
    return (
      <div className="flex flex-col gap-4">
        <p className="font-body text-sm text-muted-foreground">
          Este paso necesita el vínculo Siges del paso anterior. Podés saltearlo y
          cargar la base de despacho más tarde desde la fila del prestador.
        </p>
        <PasoAcciones onSaltear={onSaltear} />
      </div>
    );
  }

  const confirmar = async () => {
    setSaving(true);
    setError(null);
    try {
      await liquidacionesApi.vincularBaseSucursal(prestador.id, selectedId);
      toast.success("Sucursal base guardada");
      onVinculado();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <p className="font-body text-sm text-muted-foreground">
        Sede desde donde se calculan las distancias a los clientes (necesita
        coordenadas cargadas en Gestión).
      </p>
      {sucursales === null ? (
        <div className="flex h-24 items-center justify-center"><Spinner /></div>
      ) : sucursales.length === 0 ? (
        <p className="font-body text-sm text-muted-foreground italic">
          No se encontraron sucursales propias del PST en Siges.
        </p>
      ) : (
        <div className="max-h-64 overflow-y-auto rounded-[8px] border border-border">
          {sucursales.map((s) => (
            <label
              key={s.sigesSucursalId}
              className={`flex cursor-pointer items-center gap-3 px-4 py-3 transition-colors hover:bg-muted/30 ${
                selectedId === s.sigesSucursalId ? "bg-brand-orange/5" : ""
              }`}
            >
              <input
                type="radio"
                name="base-sucursal"
                checked={selectedId === s.sigesSucursalId}
                onChange={() => setSelectedId(s.sigesSucursalId)}
                className="accent-brand-orange"
              />
              <span className="flex-1 font-body text-sm">{s.descripcion}</span>
              {s.tieneCoords ? <Badge variant="success">Con coords</Badge> : <Badge variant="neutral">Sin coords</Badge>}
            </label>
          ))}
        </div>
      )}
      {error && <p className="font-body text-sm text-destructive">{error}</p>}
      <PasoAcciones
        onSaltear={onSaltear}
        primario={confirmar}
        primarioTexto="Guardar y continuar →"
        primarioDisabled={selectedId === null}
        saving={saving}
      />
    </div>
  );
}
