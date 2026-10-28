import { API_BASE, ApiError, downloadFile, request, uploadFile } from './api';

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
  plan?: PlanStep[];
}

export interface PlanStep {
  step: number;
  agent: string;
  agent_name: string;
  after: string[];
  uses_existing: string[];
  approval_needed_before_next: boolean;
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
  /** The sections it writes, in order; screen 05 ticks through them while it runs. */
  sections: string[];
  /** Its accent: the screen 04 card and every screen of its run (05–11) take this colour. */
  color: string;
}

/** The one place agent names live; the catalog (data/agents.ts) and the backend use the same. */
export const AGENT_META: Record<string, AgentMeta> = {
  mom: {
    label: 'MOM',
    full: 'Minutes of Meeting (MoM) & Action Items Matrix',
    blurb: 'Minutes and actions',
    working: 'writing the minutes',
    output: 'Minutes, decision log, action matrix',
    approver: 'You',
    agentMinutes: 6,
    manualHours: 4,
    sections: ['Attendees and roles', 'Discussion summary', 'Decisions', 'Action items', 'Open questions'],
    color: '#EB1700',
  },
  'agile-stories': {
    label: 'Agile Stories',
    full: 'Agile User Stories & Backlog Epics',
    blurb: 'Stories and BDD criteria',
    working: 'writing the stories',
    output: 'Epics, INVEST stories, BDD criteria',
    approver: 'Product Owner',
    agentMinutes: 8,
    manualHours: 6,
    sections: ['Epics', 'User stories', 'Acceptance criteria', 'Priorities and estimates', 'Open questions'],
    color: '#7B3FE4',
  },
  'solution-analyzer': {
    label: 'Solution Analyzer',
    full: 'Solution Analyzer & Blueprint',
    blurb: 'Solution blueprint',
    working: 'designing the solution',
    output: 'Approach, components, risks, roadmap',
    approver: 'Solution Architect',
    agentMinutes: 9,
    manualHours: 8,
    sections: ['Problem and constraints', 'Proposed approach', 'Components', 'Risks', 'Roadmap', 'Open questions'],
    color: '#00897B',
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
    sections: ['Requirements read', 'Current state', 'Gaps found', 'Traceability matrix', 'Open questions'],
    color: '#005EEB',
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
    sections: ['Purpose and scope', 'Definitions', 'Design considerations', 'Field and table design', 'Validation and derivation', 'Impact and dependencies', 'Open questions'],
    color: '#EF6C00',
  },
  'kdd-dab': {
    label: 'KDD for DAB',
    full: 'KDD Package for DAB',
    blurb: 'DAB governance dossier',
    working: 'building the DAB pack',
    output: 'DAB-ready architecture dossier',
    approver: 'Solution Architect',
    agentMinutes: 10,
    manualHours: 8,
    sections: ['Key design decisions', 'Alternatives considered', 'Architecture principles', 'Compliance and DR', 'Validation before go-live'],
    color: '#E3175F',
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
    sections: ['The change', 'Impacted systems', 'Dependencies', 'Readiness', 'Open questions'],
    color: '#B07A00',
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
    sections: ['Test inventory', 'Test cases', 'Test data', 'Coverage', 'Open questions'],
    color: '#2F9E24',
  },
  'readiness-audit': {
    label: 'Readiness & Audit',
    full: 'Delivery Readiness Scoring & SDLC Audit',
    blurb: 'Readiness scorecard',
    working: 'scoring the deliverables',
    output: 'Scorecard, gaps, remediation list',
    approver: 'Delivery Lead',
    agentMinutes: 7,
    manualHours: 5,
    sections: ['Deliverables checked', 'Deficits', 'Readiness score', 'Remediation list'],
    color: '#455A64',
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
      sections: [],
      color: '#EB1700',
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

export function approveWorkflow(workflowId: string, approvedBy: string, artifactId: string) {
  return request<{ status: string; stage: string; artifact_id: string; version: number }>(
    `/workflows/${encodeURIComponent(workflowId)}/approve`,
    {
      method: 'POST',
      body: { artifact_id: artifactId, user_id: approvedBy, comments: `Approved by ${approvedBy}` },
    },
  );
}

/** POST /workflows/{id}/next-agent: the orchestrator's pick for who takes an output next. */
export interface NextAgentDecision {
  agent: string | null;
  agent_name?: string;
  reason: string;
  confidence?: number;
  builds_on_output?: boolean;
  alternatives?: string[];
  /** The recommendation the pages work from, with the chosen agent first. */
  recommendation: Recommendation;
}

export function getNextAgent(workflowId: string, artifactId: string): Promise<NextAgentDecision> {
  return request<NextAgentDecision>(`/workflows/${encodeURIComponent(workflowId)}/next-agent`, {
    method: 'POST',
    body: { artifact_id: artifactId },
  });
}

export interface QualityReport {
  unsupported_figures?: string[];
  dangling_references?: string[];
  checked?: boolean;
}

export interface AgentRun {
  workflow_id: string | null;
  artifact_id: string;
  agent_name: string;
  stage: string;
  version: number;
  content: Record<string, unknown>;
  quality?: QualityReport;
  approval_status?: 'pending' | 'approved' | 'rejected';
  upstream_used?: string[];
  upstream_unapproved?: string[];
  /** The orchestrator's verdict on this output, the same rubric in every iteration. */
  readiness?: { ready: boolean; score: number; issues: string[]; attempts: number } | null;
  run_id?: string | null;
}

interface RunStatus {
  id: string;
  status: 'queued' | 'running' | 'done' | 'failed';
  error: string | null;
  result: AgentRun | null;
}

const POLL_MS = 2000;
const RUN_LIMIT_MS = 15 * 60_000;

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export async function runAgent(
  agent: string,
  body: { workflow_id?: string | null; input_text?: string; source_artifact_id?: string },
): Promise<AgentRun> {
  const started = await request<RunStatus>(`/agents/${encodeURIComponent(agent)}/runs`, { method: 'POST', body });
  const deadline = Date.now() + RUN_LIMIT_MS;
  let run = started;
  while (run.status === 'queued' || run.status === 'running') {
    if (Date.now() > deadline) throw new ApiError('The agent is still working after 15 minutes. Try again later.', 0);
    await sleep(POLL_MS);
    run = await request<RunStatus>(`/agents/runs/${encodeURIComponent(started.id)}`);
  }
  if (run.status === 'failed' || !run.result) throw new ApiError(run.error || 'The agent run failed.', 0);
  return run.result;
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
/** The main file an agent's output downloads as: a deck for the Solution Analyzer (it gets presented), Word otherwise. */
export function documentFormat(agentId: string | null | undefined): { fmt: 'pptx' | 'docx'; label: string } {
  return agentId === 'solution-analyzer' ? { fmt: 'pptx', label: 'PowerPoint' } : { fmt: 'docx', label: 'Word' };
}

export function downloadArtifact(artifactId: string, fmt: 'docx' | 'xlsx' | 'pptx'): Promise<void> {
  return downloadFile(`/workflows/artifacts/${encodeURIComponent(artifactId)}/export.${fmt}`, `savia-${artifactId}.${fmt}`);
}

/** J&J brand roles, in document order. Styles come from backend/app/brand/jnj_tokens.py. */
export type BrandRole = 'eyebrow' | 'headline' | 'subhead' | 'section_heading' | 'item_title' | 'body' | 'footer';

export interface BrandDocument {
  /** The branded content, styles and fonts; validated by the backend exactly like the Word export. */
  document: {
    eyebrow: string | null;
    headline: string;
    subhead: string | null;
    sections: Array<{
      heading: string;
      body: string[];
      items: Array<{ title: string | null; fields: Array<{ label: string; value: string }> }>;
    }>;
    footer: string;
  };
  styles: Record<BrandRole, { font_family: string; size_pt: number; bold: boolean; color: string; background: string }>;
  fonts: Array<{ family: string; weight: number; file: string }>;
  page_background: string;
  rule_color: string;
}

/** GET /workflows/artifacts/{id}/brand-document */
export function getBrandDocument(artifactId: string): Promise<BrandDocument> {
  return request<BrandDocument>(`/workflows/artifacts/${encodeURIComponent(artifactId)}/brand-document`);
}

export function brandFontUrl(file: string): string {
  return `${API_BASE}/workflows/brand/fonts/${encodeURIComponent(file)}`;
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
      .map(([k, v]) => `${k.replace(/_/g, ' ').replace(/^./, (c) => c.toUpperCase())}:${Array.isArray(v) ? '\n' : ' '}${sectionText(v)}`)
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
