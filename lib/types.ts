export type Fixture = "outbreak" | "control";
export type Health = {
  status: string;
  mode: "demo" | "live";
  integrations: { name: string; configured: boolean; detail: string }[];
};
export type SectorReport = {
  sector: string;
  sensors: unknown;
  sighting: unknown;
  civilian_status: unknown;
  containment_state: unknown;
};
export type Run = {
  id: string;
  mode: "demo" | "live";
  created_at: string;
  tick: {
    tick_id: string | number;
    facility_id: string;
    sector_reports: SectorReport[];
    swarm_budget?: unknown;
    [key: string]: unknown;
  };
  decision: {
    action: "contain" | "evacuate" | "observe";
    rationale: string;
    evidence: string[];
  };
  agents: { role: string; summary: string }[];
  submission: { status: string; detail?: string };
  dispatch: { status: string; detail?: string };
};
