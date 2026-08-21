export interface ConversacionPendiente {
  wa_id: string;
  nombre: string;
  operador_nombre: string | null;
  operador_email: string | null;
  sin_asignar: boolean;
  esperando_desde: string;
  minutos_esperando: number;
  ultimo_mensaje_cliente_at: string | null;
  ultimo_texto_cliente: string;
}

export interface OperadorPendientes {
  operador: string;
  cantidad: number;
}

export interface WatiPendientesResumen {
  total: number;
  sin_asignar: number;
  max_minutos_esperando: number;
  por_operador: OperadorPendientes[];
  sincronizado_at: string | null;
  inbox_url: string | null;
}

export interface WatiSyncResultado {
  contactos_revisados: number;
  esperando: number;
  descartados: number;
}
