export type Severity = "ERROR" | "WARNING" | "INFO" | "UNKNOWN";

export interface LogEvent {
  type: string;
  code: string;
  timestamp: string;
  counter: number;
  firmware: string | null;
  help_reference: string | null;
  code_severity: Severity | null;
  code_description: string | null;
  code_solution_url: string | null;
}

export interface Incident {
  id: string;
  code: string;
  classification: string;
  severity: Severity;
  severity_weight: number;
  occurrences: number;
  start_time: string;
  end_time: string;
  counter_range: [number, number];
  sds_link: string | null;
  code_description?: string | null;
}

export interface ParserError {
  line_number: number;
  raw_line: string;
  reason: string;
}

export interface AnalysisResult {
  events: LogEvent[];
  incidents: Incident[];
  global_severity: Severity;
  events_count: number;
  codes_new: string[];
  errors: ParserError[];
}

export interface SdsExtractResult {
  device_id: string;
  model_name: string;
  tsv: string;
  help_urls_updated: number;
}

export interface ResolvedDevice {
  device_id: number;
  serial: string;
  model: string;
  customer_name: string | null;
  location: string | null;
}

export interface SavedAnalysis {
  id: string;
  name: string;
  equipment_identifier: string | null;
  global_severity: Severity;
  created_at: string;
}

export interface SavedAnalysisDetail extends SavedAnalysis {
  incidents: Incident[];
  ai_diagnosis: string | null;
}

export interface ErrorCode {
  code: string;
  severity: Severity;
  description: string | null;
  solution_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface AiDiagnoseResult {
  diagnosis: string;
  tokens: Record<string, number>;
  cost_usd: number;
}

export interface DeviceHealth {
  status: string;
  label: string;
  reason: string;
  recommendation: string;
  triggered_rule: string | null;
  events_count: number;
}

export interface FleetClient {
  customer_id: number;
  name: string;
  device_count: number;
}

export interface ClientDevice {
  device_id: number;
  serial: string;
  location: string | null;
  model: string | null;
}

export interface CdsReplacement {
  articulo: string;
  cantidad: number;
}

export interface CdsIncident {
  id: string;
  numero_incidente: string;
  fecha: string;
  fecha_cierre: string | null;
  tipo: string;
  estado: string;
  motivo: string;
  contador: string | null;
  repuestos: CdsReplacement[];
  tareas_realizadas: string[];
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}
