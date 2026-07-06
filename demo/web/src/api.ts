export type ProposalMethod =
  | "MANUAL_TRANSLATION"
  | "MODEL_ASSISTED"
  | "DETERMINISTIC_PARSER";

export interface Scenario {
  field_name: string;
  unit_id: string;
  value: string;
  proposal_method: ProposalMethod;
  ratified: boolean;
  independent_review: boolean;
}

export interface Stage {
  key: string;
  title: string;
  status: string;
  summary: string;
  record_type: string | null;
  record: Record<string, unknown> | null;
}

export interface PipelineResult {
  verdict: "PASSED" | "BLOCKED";
  verdict_reason: string;
  gate_status: string;
  gate_reason_id: string | null;
  crossed_firewall: boolean;
  stages: Stage[];
}

// Dev proxies /api to the FastAPI backend; production serves under /gptl/api.
const API_ROOT =
  import.meta.env.VITE_API_BASE || (import.meta.env.DEV ? "/api" : "/gptl/api");

export async function runPipeline(scenario: Scenario): Promise<PipelineResult> {
  const res = await fetch(`${API_ROOT}/pipeline/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(scenario),
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail =
        typeof body.detail === "string"
          ? body.detail
          : (body.detail?.[0]?.msg ?? detail);
    } catch {
      /* keep statusText */
    }
    throw new Error(detail);
  }
  return res.json();
}
