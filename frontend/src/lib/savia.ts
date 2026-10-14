import { API_BASE, request, uploadFile } from './api';

/** Response of POST /ingestion/upload. */
export interface UploadResult {
  workflow_id: string;
  filename: string;
  input_type: string;
  metadata: {
    filename: string;
    input_type: string;
    file_size_bytes: number;
    character_count: number;
    word_count: number;
  };
  full_normalized_text: string;
}

export interface RecommendedAgent {
  agent: string;
  agent_name: string;
  reason: string;
  required_inputs: string[];
  confidence: number;
  /** True when a keyword in the document actually triggered this agent. */
  matched: boolean;
}

/** Response of POST /savia/recommend. */
export interface Recommendation {
  workflow_id: string | null;
  input_type: string;
  current_stage: string;
  recommended_agents: RecommendedAgent[];
  primary_agent: string;
  primary_reason: string;
  missing_information: string[];
  /** With source 'llm', a sentence on how to use the top agent; else a status code. */
  next_action: string;
  /** 'llm' when an AI model chose the agents; 'keyword' when it fell back to keyword scoring. */
  source?: 'llm' | 'keyword';
}

/**
 * Facts about each agent that the API does not return. `label` and `full` are
 * naming; `output` and `approver` describe the agent itself, not the document.
 *
 * `agentMinutes` and `manualHours` are PLANNING ESTIMATES held here on the
 * client — the backend exposes no timing data, so the plan cost is computed
 * from these rather than measured.
 */
interface AgentMeta {
  label: string;
  full: string;
  /** Short description of what the agent produces, for tight card copy. */
  blurb: string;
  /** Completes "<label> is …" in the run page heading. */
  working: string;
  output: string;
  approver: string;
  agentMinutes: number;
  manualHours: number;
}

const AGENT_META: Record<string, AgentMeta> = {
  mom: {
    label: 'MOM',
    full: 'Minutes of Meeting (MoM) & Action Items Matrix',
    blurb: 'Minutes and actions',
    working: 'writing the minutes',
    output: 'Minutes, decision log, action matrix',
    approver: 'You',
    agentMinutes: 6,
    manualHours: 4,
  },
  'user-stories': {
    label: 'Agile Stories',
    full: 'Agile User Stories & Backlog Epics',
    blurb: 'Stories and BDD criteria',
    working: 'writing the stories',
    output: 'Epics, INVEST stories, BDD criteria',
    approver: 'Product Owner',
    agentMinutes: 8,
    manualHours: 6,
  },
  'gap-analysis': {
    label: 'Gap Analysis & RTM',
    full: 'Requirement Gap Analysis & RTM',
    blurb: 'Gaps and traceability',
    working: 'mapping the gaps',
    output: 'Gap list and the traceability matrix',
    approver: 'You',
    agentMinutes: 9,
    manualHours: 7,
  },
  ddl3: {
    label: 'DDL3',
    full: 'DDL3 (Design Document Lifecycle)',
    blurb: 'Design documents',
    working: 'writing the design',
    output: 'Functional design, then technical',
    approver: 'Design Lead',
    agentMinutes: 12,
    manualHours: 10,
  },
  'kdd-package': {
    label: 'KDD for DAB',
    full: 'KDD Package for DAB',
    blurb: 'DAB governance dossier',
    working: 'building the DAB pack',
    output: 'DAB-ready architecture dossier',
    approver: 'Solution Architect',
    agentMinutes: 10,
    manualHours: 8,
  },
  'change-impact': {
    label: 'Change Impact',
    full: 'Change Impact Assessment & Interdependency Matrix',
    blurb: 'Impact and dependencies',
    working: 'assessing the impact',
    output: 'Impact analysis and dependency matrix',
    approver: 'Solution Architect',
    agentMinutes: 9,
    manualHours: 6,
  },
  test: {
    label: 'TEST',
    full: 'TEST — End-to-end Test Preparation',
    blurb: 'Test inventory and cases',
    working: 'writing the test cases',
    output: 'Inventory, cases, coverage',
    approver: 'Test Lead',
    agentMinutes: 11,
    manualHours: 9,
  },
  'readiness-scoring': {
    label: 'Readiness & Audit',
    full: 'Delivery Readiness Scoring & SDLC Audit',
    blurb: 'Readiness scorecard',
    working: 'scoring the deliverables',
    output: 'Scorecard, gaps, remediation list',
    approver: 'Delivery Lead',
    agentMinutes: 7,
    manualHours: 5,
  },
};

/** Falls back to the API's own naming for an agent we have no entry for. */
export function agentMeta(agent: RecommendedAgent): AgentMeta {
  return (
    AGENT_META[agent.agent] ?? {
      label: agent.agent_name,
      full: agent.agent_name,
      blurb: agent.agent_name,
      working: 'running',
      output: 'See the agent output',
      approver: 'You',
      agentMinutes: 8,
      manualHours: 5,
    }
  );
}

export function agentLabel(agent: RecommendedAgent): string {
  return agentMeta(agent).label;
}

/** Adds up the planning estimates for the agents in a plan. */
export function planCost(agents: RecommendedAgent[]) {
  const agentMinutes = agents.reduce((total, a) => total + agentMeta(a).agentMinutes, 0);
  const manualHours = agents.reduce((total, a) => total + agentMeta(a).manualHours, 0);
  return {
    count: agents.length,
    agentMinutes,
    // An 8-hour working day.
    manualDays: Math.round((manualHours / 8) * 10) / 10,
  };
}

export function ingestFile(files: File[]): Promise<UploadResult> {
  return uploadFile<UploadResult>('/ingestion/upload', files);
}

/** Response of POST /ingestion/analyze. */
export interface Analysis {
  character_count: number;
  word_count: number;
  is_audio_transcript: boolean;
  detected_entities: {
    has_action_items: boolean;
    has_user_stories: boolean;
    has_design_specs: boolean;
    has_test_cases: boolean;
  };
  summary_snippet: string;
}

/** Human labels for the four signals the backend detects. */
export const ENTITY_LABELS: Record<keyof Analysis['detected_entities'], string> = {
  has_user_stories: 'user stories',
  has_action_items: 'action items',
  has_design_specs: 'design specs',
  has_test_cases: 'test cases',
};

export function analyzeText(text: string): Promise<Analysis> {
  return request<Analysis>('/ingestion/analyze', { method: 'POST', body: { text } });
}

export function recommendAgents(body: {
  workflow_id?: string | null;
  raw_text?: string;
  input_type?: string;
  filename?: string;
}): Promise<Recommendation> {
  return request<Recommendation>('/savia/recommend', { method: 'POST', body });
}

/** Response of POST /agents/{agent}. */
export interface AgentRun {
  workflow_id: string | null;
  artifact_id: string;
  agent_name: string;
  stage: string;
  version: number;
  content: Record<string, unknown>;
}

export function runAgent(
  agent: string,
  body: { workflow_id?: string | null; input_text?: string },
): Promise<AgentRun> {
  return request<AgentRun>(`/agents/${agent}`, {
    method: 'POST',
    // Without this the stage gate rejects a workflow that has not reached
    // this agent's stage yet (agent_route.py checks can_advance).
    body: { ...body, bypass_approval: true },
    // An LLM run on a long document takes tens of seconds.
    timeoutMs: 180_000,
  });
}

export interface OutputPart {
  key: string;
  title: string;
  detail: string;
  count: number | null;
  fullText?: string;
  items?: unknown[];
}

export interface DashboardCounter {
  id: string;
  value: string;
  label: string;
  hint: string;
  accent: string;
}

export interface DashboardRun {
  id: string;
  title: string;
  meta: string;
  metricLabel: string;
  metricValue: string;
  state: string;
  stateTone: string;
  accent: string;
}

export interface WeeklyRun {
  id: string;
  title: string;
  text: string;
  stage: string;
  stageHref?: string | null;
  usage: string;
  image: string;
  accent: string;
}

export interface DashboardSummaryResponse {
  counters: DashboardCounter[];
  runs: DashboardRun[];
  ran_this_week: WeeklyRun[];
  total_workflows: number;
}

export function fetchDashboardSummary(): Promise<DashboardSummaryResponse> {
  return request<DashboardSummaryResponse>('/savia/dashboard');
}

export interface JiraIssueDetails {
  key: string;
  summary: string;
  description: string;
  status: string;
  project: string;
  assignee: string;
  stories_count: number;
  valid: boolean;
}

export function fetchJiraIssue(issueKey: string): Promise<JiraIssueDetails> {
  return request<JiraIssueDetails>(`/jira-agent/issue/${encodeURIComponent(issueKey)}`);
}

/** Turns an agent's content into something readable, whatever its shape. */
export function summariseContent(content: Record<string, unknown>): OutputPart[] {
  return Object.entries(content)
    .filter(([, value]) => value !== null && value !== undefined && value !== '')
    .map(([key, value]) => {
      const title = key.replace(/_/g, ' ').replace(/^./, (c) => c.toUpperCase());

      if (Array.isArray(value)) {
        return {
          key,
          title,
          count: value.length,
          detail: `${value.length} item${value.length === 1 ? '' : 's'}`,
          items: value,
        };
      }
      if (typeof value === 'object' && value !== null) {
        const fields = Object.keys(value as object).length;
        return {
          key,
          title,
          count: fields,
          detail: `${fields} field${fields === 1 ? '' : 's'}`,
          items: [value],
        };
      }
      const text = String(value);
      return {
        key,
        title,
        count: null,
        detail: text,
        fullText: text,
      };
    });
}

/** Direct download link for an agent's output as a styled Word or Excel file. */
export function artifactExportUrl(artifactId: string, fmt: 'docx' | 'xlsx'): string {
  return `${API_BASE}/workflows/artifacts/${encodeURIComponent(artifactId)}/export.${fmt}`;
}

/** POST /workflows/artifacts/{id}/suggest-edit — an AI draft of one section, not yet saved. */
export interface EditSuggestion {
  section: string;
  original: unknown;
  revised: unknown;
  summary: string;
  /** Statements in the revision the source input does not support. */
  unsupported_claims: string[];
  /** Questions Savia needs answered instead of guessing; the section is left unchanged. */
  needs_info: string[];
}

export function suggestEdit(artifactId: string, section: string, instruction: string): Promise<EditSuggestion> {
  return request<EditSuggestion>(`/workflows/artifacts/${encodeURIComponent(artifactId)}/suggest-edit`, {
    method: 'POST',
    body: { section, instruction },
  });
}

/** Saves an accepted section as a new artifact version (older versions are kept). */
export function applyEdit(artifactId: string, section: string, value: unknown): Promise<AgentRun> {
  return request<AgentRun>(`/workflows/artifacts/${encodeURIComponent(artifactId)}/apply-edit`, {
    method: 'POST',
    body: { section, value },
  });
}

export interface OpenDecision {
  question: string;
  evidence: string;
  section: string;
  options: { title: string; text: string; cost: string }[];
  /** 0 or 1 when the text points towards an option, else null. */
  leaning: number | null;
  leaning_reason: string;
}

export function findOpenDecisions(artifactId: string): Promise<{ decisions: OpenDecision[] }> {
  return request<{ decisions: OpenDecision[] }>(
    `/workflows/artifacts/${encodeURIComponent(artifactId)}/open-decisions`,
    { method: 'POST' },
  );
}

/** Readable plain text for any section value: strings, lists, records. */
export function sectionText(value: unknown): string {
  if (value === null || value === undefined) return '';
  if (Array.isArray(value)) return value.map((item) => `• ${sectionText(item).replace(/\n/g, '\n  ')}`).join('\n');
  if (typeof value === 'object') {
    return Object.entries(value as Record<string, unknown>)
      .filter(([, v]) => v !== null && v !== '' && !(Array.isArray(v) && v.length === 0))
      .map(([k, v]) => `${k.replace(/_/g, ' ').replace(/^./, (c) => c.toUpperCase())}: ${sectionText(v)}`)
      .join('\n');
  }
  return String(value);
}

/** Section key → readable title, e.g. "action_items" → "Action items". */
export function sectionTitle(key: string): string {
  return key.replace(/_/g, ' ').replace(/^./, (c) => c.toUpperCase());
}

/** Records a chosen option: adds it to the decisions, resolves the open question, saves a new version. */
export function recordDecision(artifactId: string, question: string, chosenTitle: string, chosenText: string): Promise<AgentRun> {
  return request<AgentRun>(`/workflows/artifacts/${encodeURIComponent(artifactId)}/record-decision`, {
    method: 'POST',
    body: { question, chosen_title: chosenTitle, chosen_text: chosenText },
  });
}
