// Field names follow auditor/schema/report.schema.json (schema_version 1.1.0).
export type Band = "critical" | "high" | "medium" | "low";
export const BANDS: Band[] = ["critical", "high", "medium", "low"];

export interface Evidence {
  file: string;
  start_line: number;
  end_line: number;
  excerpt: string;
}
export interface FlowStep {
  operation: string;
  evidence: Evidence;
  note?: string;
}
export interface Element {
  name: string;
  data_category: string;
  evidence: Evidence;
}
export interface LlmField {
  status: string;
  value?: unknown;
  cache_key?: string;
  provider?: string;
  model?: string;
}
export interface Finding {
  id: string;
  issue_type: string;
  kind: string;
  classification: string;
  evidence: Evidence[];
  data_flow: FlowStep[];
  personal_data_element: Element | null;
  data_category: string;
  processing_operation: string;
  primary_provision: string;
  other_provisions: string[];
  penalty_ceiling: { parent_section: string; amount_inr_crore: number };
  enforceable_from: string;
  severity: { band: Band; justification: string };
  recommended_fix: { guidance: string; tailored?: LlmField };
  llm_triage: LlmField;
  status: string;
}
export interface MapEntry {
  element: Element;
  operations: FlowStep[];
}
export interface Report {
  target: { name: string; source: string; commit?: string };
  llm: { mode: string };
  personal_data_map: MapEntry[];
  findings: Finding[];
}
export interface ScanEvent {
  run_id: string;
  ordinal: number;
  mode: "live" | "cache-only" | "recorded";
  type: "stage" | "completed" | "failed";
  stage?: string;
  elapsed_ms: number;
  message?: string;
  finding_count?: number;
}
export interface Provision {
  id: string;
  citation: string;
  title: string;
  excerpt: string;
  penalty_ceiling_inr_crore: number | null;
  enforceable_from: string | null;
}
