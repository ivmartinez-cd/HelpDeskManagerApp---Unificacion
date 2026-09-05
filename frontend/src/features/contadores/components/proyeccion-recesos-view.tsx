"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { BrandButton, BrandInput } from "@/shared/components/ui/brand-form";
import { SearchableSelect } from "@/shared/components/ui/searchable-select";
import { useSession } from "@/services/session-provider";
import { proyeccionApi } from "../api/proyeccion-api";
import type { AnexoOption, GrupoEconomicoOption, Receso } from "../types/proyeccion";

function formatFecha(iso: string): string {
  const [y, m, d] = iso.split("-");
  return `${d}/${m}/${y}`;
}

export function ProyeccionRecesosView() {
  const { can } = useSession();
  const puedeGestionar = can("contadores", "manage");
  const [grupos, setGrupos] = useState<GrupoEconomicoOption[]>([]);
  const [anexos, setAnexos] = useState<AnexoOption[]>([]);
  const [idGrupo, setIdGrupo] = useState<string | null>(null);
  const [idAnexo, setIdAnexo] = useState<string | null>(null);
  const [recesos, setRecesos] = useState<Receso[] | null>(null);
  const [desde, setDesde] = useState("");
  const [hasta, setHasta] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [guardando, setGuardando] = useState(false);

  useEffect(() => {
    void proyeccionApi.listGruposEconomicos().then(setGrupos);
  }, []);

  useEffect(() => {
    if (!idGrupo) return;
    void proyeccionApi.listAnexos(Number(idGrupo)).then(setAnexos);
  }, [idGrupo]);

  // Derivado en vez de resetear estado a mano en el efecto de arriba
  // (react-hooks/set-state-in-effect): sin grupo no hay anexos que mostrar.
  const anexosVisibles = idGrupo ? anexos : [];

  const cargar = () =>
    void proyeccionApi.listRecesos(idGrupo ? Number(idGrupo) : undefined).then(setRecesos);

  useEffect(cargar, [idGrupo]);

  const agregar = async () => {
    if (!desde || !hasta || !descripcion.trim()) return;
    setGuardando(true);
    try {
      await proyeccionApi.crearReceso({
        id_grupo_economico: idGrupo ? Number(idGrupo) : 1,
        id_anexo: idAnexo ? Number(idAnexo) : null,
        fecha_desde: desde,
        fecha_hasta: hasta,
        descripcion: descripcion.trim(),
      });
      setDesde("");
      setHasta("");
      setDescripcion("");
      cargar();
    } finally {
      setGuardando(false);
    }
  };

  const eliminar = async (id: number) => {
    await proyeccionApi.eliminarReceso(id, idGrupo ? Number(idGrupo) : undefined);
    cargar();
  };

  return (
    <div className="flex flex-col gap-6 px-9 py-8">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link href="/contadores" className="hover:text-foreground">Centro de Contadores</Link>
        <span>›</span>
        <Link href="/contadores/proyeccion" className="hover:text-foreground">Proyección</Link>
        <span>›</span>
        <span className="font-semibold text-foreground">Recesos</span>
      </div>

      <div>
        <h1 className="font-heading text-[25px] font-extrabold uppercase tracking-[-.03em] text-foreground">
          Calendario de recesos
        </h1>
        <p className="mt-1 max-w-3xl font-body text-sm text-muted-foreground">
          Períodos sin uso del cliente (recesos escolares de invierno/verano, etc.). Se descuentan de la
          estimación: no diluyen la tasa diaria ni se facturan como impresiones.
        </p>
      </div>

      <div className="flex flex-wrap items-end gap-3">
        <div className="w-[260px]">
          <SearchableSelect
            label="Grupo económico"
            placeholder="Elegí un grupo… (vacío = ejemplo)"
            options={grupos.map((g) => ({ id: String(g.id), label: g.descripcion }))}
            value={idGrupo}
            onChange={(id) => {
              setIdGrupo(id);
              setIdAnexo(null);
            }}
          />
        </div>
        <div className="w-[260px]">
          <SearchableSelect
            label="Anexo (opcional — vacío = todo el grupo)"
            placeholder={idGrupo ? "Todo el grupo…" : "Elegí primero un grupo"}
            disabled={!idGrupo}
            options={anexosVisibles.map((a) => ({ id: String(a.id_anexo), label: a.nombre_anexo }))}
            value={idAnexo}
            onChange={setIdAnexo}
          />
        </div>
      </div>

      <p className="text-xs text-muted-foreground">
        {idGrupo
          ? "Administrando recesos de un grupo económico real — persisten en la base."
          : "Sin grupo elegido: administrando los recesos de ejemplo (se pierden al reiniciar el backend)."}
      </p>

      <div className="grid gap-6 lg:grid-cols-[360px_1fr]">
        {puedeGestionar && (
          <div className="flex flex-col gap-3 rounded-[12px] border border-border bg-card p-5">
            <h2 className="font-heading text-sm font-bold">Nuevo receso</h2>
            <BrandInput label="Desde" type="date" value={desde} onChange={(e) => setDesde(e.target.value)} />
            <BrandInput label="Hasta" type="date" value={hasta} onChange={(e) => setHasta(e.target.value)} />
            <BrandInput
              label="Descripción"
              placeholder="Ej. Receso invierno 2026"
              value={descripcion}
              onChange={(e) => setDescripcion(e.target.value)}
            />
            <BrandButton
              loading={guardando}
              disabled={!desde || !hasta || !descripcion.trim()}
              onClick={agregar}
            >
              Agregar
            </BrandButton>
          </div>
        )}

        <div>
          {!recesos ? (
            <p className="text-sm text-muted-foreground">Cargando…</p>
          ) : recesos.length === 0 ? (
            <p className="text-sm text-muted-foreground">No hay recesos cargados todavía.</p>
          ) : (
            <div className="overflow-hidden rounded-[12px] border border-border bg-card">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-border text-[11px] font-bold uppercase text-muted-foreground">
                    <th className="px-4 py-2.5">Desde</th>
                    <th className="px-4 py-2.5">Hasta</th>
                    <th className="px-4 py-2.5">Descripción</th>
                    <th className="px-4 py-2.5" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {recesos.map((r) => (
                    <tr key={r.id}>
                      <td className="px-4 py-3">{formatFecha(r.fecha_desde)}</td>
                      <td className="px-4 py-3">{formatFecha(r.fecha_hasta)}</td>
                      <td className="px-4 py-3">{r.descripcion}</td>
                      <td className="px-4 py-3 text-right">
                        {puedeGestionar && (
                          <button
                            onClick={() => eliminar(r.id)}
                            className="text-xs font-bold text-destructive hover:underline"
                          >
                            Eliminar
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
