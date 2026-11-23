// Field names follow auditor/schema/report.schema.json (schema_version 1.2.0).
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
export interface LlmField<Value = unknown> {
  status: string;
  value?: Value;
  cache_key?: string;
  provider?: string;
  model?: string;
}
export interface LlmTriageValue {
  verdict: "true-positive" | "false-positive" | "uncertain";
  reason: string;
  citations?: string[];
}
export interface LlmConsentValue {
  assessment: string;
  criteria?: {
    criterion: string;
    reading: "met" | "not met" | "not determinable";
    reason: string;
    citations: string[];
  }[];
  citations?: string[];
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
  llm_triage: LlmField<LlmTriageValue>;
  live_probe?: { result: "Confirmed" | "Refuted" | "inconclusive"; method: string; route: string; reason: string; request: string; response: string } | null;
  fix_patch?: { status: "generated" | "accepted" | "rejected"; diff: string; reason: string; provenance?: "generated" | "authored" } | null;
  status: string;
}
export interface MapEntry {
  element: Element;
  operations: FlowStep[];
}
export interface ConsentProbe {
  status: "Confirmed" | "Not Confirmed" | "Inconclusive";
  meaning: string;
  assertion: string;
  reason: string;
}
export interface ConsentCriterion {
  criterion: string;
  applicability: "applicable" | "not applicable" | "not determinable";
  reason: string;
  assessment: string;
  linked_identifiers: string[];
  issue_types: string[];
  evidence: Evidence[];
  step_counts: { grant: (number | null)[]; withdrawal: (number | null)[] } | null;
  live_probes?: ConsentProbe[];
}
export interface ConsentAssessmentData {
  criteria: ConsentCriterion[];
  llm_reasoning: LlmField<LlmConsentValue>;
  live_probe_run?: { target: string; commit: string | null; observed_at: string };
}
export interface CeilingRow {
  provision: string;
  citation: string;
  schedule_entry: string | null;
  statutory_maximum_inr_crore: number | null;
  statutory_maximum_text: string | null;
  finding_ids: string[];
  finding_ids_by_applicability: {
    applicable_primary: string[];
    related: string[];
    conditional: string[];
    needs_legal_review: string[];
  };
  severity_mix: Record<string, number>;
}
export interface LegalViewData {
  as_of: string;
  note: string;
  ceilings: CeilingRow[];
  highest_applicable_ceiling: { amount_inr_crore: number; provisions: string[]; finding_ids: string[] } | null;
  timeline: {
    enforceable_from: string;
    finding_ids: string[];
    basis: string | null;
    days_until: number;
    already_enforceable: boolean;
  }[];
}

export interface Report {
  target: { name: string; source: string; commit?: string };
  llm: { mode: string };
  personal_data_map: MapEntry[];
  findings: Finding[];
  consent_assessment: ConsentAssessmentData | null;
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
