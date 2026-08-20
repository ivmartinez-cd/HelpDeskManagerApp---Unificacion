"use client";

import { CalendarClock, Edit2, Plus, Trash2, Users } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { turnosApi } from "../../api/turnos-api";
import type { Casilla, Slot, UserOption } from "../../types/turnos";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Modal } from "@/shared/components/ui/modal";
import { Spinner } from "@/shared/components/ui/spinner";

const DIAS_SEMANA = [
  "Lunes",
  "Martes",
  "Miércoles",
  "Jueves",
  "Viernes",
  "Sábado",
  "Domingo",
];

export function CasillasManager() {
  const [casillas, setCasillas] = useState<Casilla[]>([]);
  const [slots, setSlots] = useState<Slot[]>([]);
  const [users, setUsers] = useState<UserOption[]>([]);
  const [selectedCasillaId, setSelectedCasillaId] = useState<string | null>(null);
  const [selectedDia, setSelectedDia] = useState<number>(0); // 0=Lunes
  const [loading, setLoading] = useState(true);

  // Modal Casilla
  const [casillaModalOpen, setCasillaModalOpen] = useState(false);
  const [editingCasilla, setEditingCasilla] = useState<Casilla | null>(null);
  const [casillaNombre, setCasillaNombre] = useState("");

  // Modal Slot
  const [slotModalOpen, setSlotModalOpen] = useState(false);
  const [editingSlot, setEditingSlot] = useState<Slot | null>(null);
  const [horaInicio, setHoraInicio] = useState("08:00");
  const [horaFin, setHoraFin] = useState("11:00");
  const [selectedUserIds, setSelectedUserIds] = useState<string[]>([]);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [cList, sList, uList] = await Promise.all([
        turnosApi.listCasillas(),
        turnosApi.listSlots(),
        turnosApi.listAssignableUsers(),
      ]);
      setCasillas(cList);
      setSlots(sList);
      setUsers(uList);
      // Forma funcional: si ya hay una casilla seleccionada, la conserva;
      // si no, auto-selecciona la primera. No cierra sobre selectedCasillaId.
      setSelectedCasillaId((prev) => prev ?? (cList[0]?.id ?? null));
    } catch (err) {
      console.error("Error al cargar datos de turnos:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadData();
  }, [loadData]);

  const handleSaveCasilla = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!casillaNombre.trim()) return;
    try {
      if (editingCasilla) {
        await turnosApi.updateCasilla(editingCasilla.id, { nombre: casillaNombre });
      } else {
        await turnosApi.createCasilla({ nombre: casillaNombre });
      }
      setCasillaModalOpen(false);
      setCasillaNombre("");
      setEditingCasilla(null);
      await loadData();
    } catch (err) {
      console.error("Error al guardar casilla:", err);
    }
  };

  const handleDeleteCasilla = async (id: string) => {
    if (!confirm("¿Eliminar esta casilla y sus franjas horarias?")) return;
    try {
      await turnosApi.deleteCasilla(id);
      if (selectedCasillaId === id) setSelectedCasillaId(null);
      await loadData();
    } catch (err) {
      console.error("Error al eliminar casilla:", err);
    }
  };

  const handleOpenSlotModal = (slot?: Slot) => {
    if (slot) {
      setEditingSlot(slot);
      setHoraInicio(slot.horaInicio.slice(0, 5));
      setHoraFin(slot.horaFin.slice(0, 5));
      setSelectedUserIds(Array.from(new Set(slot.asignaciones.map((a) => a.userId))));
    } else {
      setEditingSlot(null);
      setHoraInicio("08:00");
      setHoraFin("11:00");
      setSelectedUserIds([]);
    }
    setSlotModalOpen(true);
  };

  const handleSaveSlot = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCasillaId) return;
    try {
      let slotId = editingSlot?.id;
      if (editingSlot) {
        await turnosApi.updateSlot(editingSlot.id, {
          casillaId: selectedCasillaId,
          horaInicio,
          horaFin,
          diaSemana: selectedDia,
        });
      } else {
        const created = await turnosApi.createSlot({
          casillaId: selectedCasillaId,
          horaInicio,
          horaFin,
          diaSemana: selectedDia,
        });
        slotId = created.id;
      }

      if (slotId) {
        const todayStr = new Date().toISOString().slice(0, 10);
        await turnosApi.replaceAssignments(slotId, selectedUserIds, todayStr);
      }

      setSlotModalOpen(false);
      await loadData();
    } catch (err) {
      console.error("Error al guardar slot:", err);
    }
  };

  const handleDeleteSlot = async (id: string) => {
    if (!confirm("¿Eliminar esta franja horaria?")) return;
    try {
      await turnosApi.deleteSlot(id);
      await loadData();
    } catch (err) {
      console.error("Error al eliminar slot:", err);
    }
  };

  if (loading && casillas.length === 0) {
    return (
      <div className="flex justify-center p-8">
        <Spinner />
      </div>
    );
  }

  const activeSlots = slots.filter(
    (s) => s.casillaId === selectedCasillaId && s.diaSemana === selectedDia
  );

  return (
    <div className="flex flex-col gap-6">
      {/* Selector de Casillas y botón de crear */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border pb-4">
        <div className="flex flex-wrap items-center gap-2">
          {casillas.map((c) => (
            <div key={c.id} className="flex items-center gap-1">
              <button
                onClick={() => setSelectedCasillaId(c.id)}
                className={`rounded-[8px] px-3.5 py-2 font-heading text-xs font-bold transition-colors ${
                  selectedCasillaId === c.id
                    ? "bg-brand-orange text-white"
                    : "bg-muted text-muted-foreground hover:bg-muted/80"
                }`}
              >
                {c.nombre}
              </button>
              <button
                onClick={() => {
                  setEditingCasilla(c);
                  setCasillaNombre(c.nombre);
                  setCasillaModalOpen(true);
                }}
                className="p-1 text-muted-foreground hover:text-foreground"
                title="Editar nombre de casilla"
              >
                <Edit2 className="h-3.5 w-3.5" />
              </button>
              <button
                onClick={() => handleDeleteCasilla(c.id)}
                className="p-1 text-muted-foreground hover:text-destructive"
                title="Eliminar casilla"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}
          {casillas.length === 0 && (
            <span className="font-body text-xs text-muted-foreground">
              No hay casillas creadas.
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <Link href="/admin/turnos/coberturas">
            <Button variant="outline" size="sm" className="gap-1.5">
              <CalendarClock className="h-4 w-4" />
              Modo vacaciones
            </Button>
          </Link>
          <Button
            onClick={() => {
              setEditingCasilla(null);
              setCasillaNombre("");
              setCasillaModalOpen(true);
            }}
            size="sm"
            className="gap-1.5"
          >
            <Plus className="h-4 w-4" />
            Nueva Casilla
          </Button>
        </div>
      </div>

      {selectedCasillaId && (
        <div className="flex flex-col gap-4">
          {/* Días de la semana */}
          <div className="flex flex-wrap items-center gap-1 border-b border-border/50 pb-2">
            {DIAS_SEMANA.map((dia, idx) => (
              <button
                key={dia}
                onClick={() => setSelectedDia(idx)}
                className={`rounded-[6px] px-3 py-1.5 font-body text-xs font-semibold transition-colors ${
                  selectedDia === idx
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-muted"
                }`}
              >
                {dia}
              </button>
            ))}
          </div>

          {/* Tabla de Franjas Horarias */}
          <div className="flex items-center justify-between">
            <span className="font-heading text-sm font-bold text-foreground">
              Horarios para {DIAS_SEMANA[selectedDia]}
            </span>
            <Button onClick={() => handleOpenSlotModal()} size="sm" variant="outline" className="gap-1.5">
              <Plus className="h-3.5 w-3.5" />
              Agregar Franja
            </Button>
          </div>

          <div className="overflow-x-auto rounded-[12px] border border-border bg-card">
            <table className="w-full text-left font-body text-xs">
              <thead className="border-b border-border bg-muted/50 font-heading text-muted-foreground">
                <tr>
                  <th className="p-3 font-semibold">Hora Inicio</th>
                  <th className="p-3 font-semibold">Hora Fin</th>
                  <th className="p-3 font-semibold">Operadores Asignados</th>
                  <th className="p-3 text-right font-semibold">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {activeSlots.length > 0 ? (
                  activeSlots.map((s) => (
                    <tr key={s.id} className="hover:bg-muted/30">
                      <td className="p-3 font-mono font-medium">{s.horaInicio.slice(0, 5)}</td>
                      <td className="p-3 font-mono font-medium">{s.horaFin.slice(0, 5)}</td>
                      <td className="p-3">
                        <div className="flex flex-wrap gap-1">
                          {s.asignaciones.length > 0 ? (
                            s.asignaciones.map((a) => (
                              <span
                                key={a.id}
                                className="rounded-full bg-brand-orange/10 text-brand-orange border border-brand-orange/20 px-2.5 py-0.5 font-medium"
                              >
                                {a.userName || "Desconocido"}
                              </span>
                            ))
                          ) : (
                            <span className="italic text-muted-foreground">Sin operadores</span>
                          )}
                        </div>
                      </td>
                      <td className="p-3 text-right">
                        <div className="flex justify-end items-center gap-2">
                          <button
                            onClick={() => handleOpenSlotModal(s)}
                            className="p-1 text-muted-foreground hover:text-foreground"
                            title="Editar franja/asignaciones"
                          >
                            <Users className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleDeleteSlot(s.id)}
                            className="p-1 text-muted-foreground hover:text-destructive"
                            title="Eliminar franja"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={4} className="p-6 text-center text-muted-foreground">
                      No hay horarios configurados para este día.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modal Casilla */}
      <Modal
        isOpen={casillaModalOpen}
        onClose={() => setCasillaModalOpen(false)}
        title={editingCasilla ? "Editar Casilla" : "Nueva Casilla"}
      >
        <form onSubmit={handleSaveCasilla} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="font-body text-xs font-semibold text-foreground">
              Nombre de la Casilla (ej. INSUMOS, ST)
            </label>
            <Input
              value={casillaNombre}
              onChange={(e) => setCasillaNombre(e.target.value)}
              placeholder="Nombre"
              required
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => setCasillaModalOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit">Guardar</Button>
          </div>
        </form>
      </Modal>

      {/* Modal Slot & Asignación */}
      <Modal
        isOpen={slotModalOpen}
        onClose={() => setSlotModalOpen(false)}
        title={editingSlot ? "Editar Franja Horaria" : "Nueva Franja Horaria"}
      >
        <form onSubmit={handleSaveSlot} className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <label className="font-body text-xs font-semibold text-foreground">
                Hora Inicio (HH:MM)
              </label>
              <Input
                type="time"
                value={horaInicio}
                onChange={(e) => setHoraInicio(e.target.value)}
                required
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="font-body text-xs font-semibold text-foreground">
                Hora Fin (HH:MM)
              </label>
              <Input
                type="time"
                value={horaFin}
                onChange={(e) => setHoraFin(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="font-body text-xs font-semibold text-foreground">
              Seleccionar Operadores para este horario
            </label>
            <div className="max-h-48 overflow-y-auto rounded-[8px] border border-border bg-muted/30 p-2.5 flex flex-col gap-1.5">
              {users.map((u) => {
                const checked = selectedUserIds.includes(u.id);
                return (
                  <label
                    key={u.id}
                    className="flex items-center gap-2 cursor-pointer rounded-md p-1.5 hover:bg-muted"
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedUserIds([...selectedUserIds, u.id]);
                        } else {
                          setSelectedUserIds(selectedUserIds.filter((id) => id !== u.id));
                        }
                      }}
                      className="rounded border-border text-brand-orange focus:ring-brand-orange"
                    />
                    <span className="font-body text-xs text-foreground font-medium">
                      {u.fullName}
                    </span>
                  </label>
                );
              })}
              {users.length === 0 && (
                <span className="font-body text-xs text-muted-foreground">
                  No hay operadores disponibles.
                </span>
              )}
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => setSlotModalOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit">Guardar</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
