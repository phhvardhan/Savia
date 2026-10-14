import { createContext, useContext } from 'react';
import type { AgentRun, Recommendation, UploadResult } from '../lib/savia';

/** The result of the ingest + recommend round trip, shared across pages. */
export interface RunState {
  upload: UploadResult | null;
  recommendation: Recommendation | null;
  setRun: (upload: UploadResult, recommendation: Recommendation) => void;
  /** The agent the person picked, which defaults to SAVIA's own choice. */
  selectedAgent: string | null;
  selectAgent: (agent: string) => void;
  /**
   * Finished agent runs, keyed "<agent>:<workflow_id>". An agent run costs a
   * slow LLM call, so a result is kept rather than repeated when the page
   * remounts — including React StrictMode's double mount in development.
   */
  agentRuns: Record<string, AgentRun>;
  saveAgentRun: (key: string, run: AgentRun) => void;
  /** The run kicked off by "Approve and start", and how it is going. */
  activeRun: ActiveRun | null;
  /**
   * Calls POST /agents/{agentId} for the current workflow. Started from the
   * button rather than a page effect, so exactly one request goes out per
   * click and the writing page only has to display it.
   */
  startAgentRun: (agentId: string) => void;
  /** Erases all current run state to start a completely fresh run from the beginning. */
  resetAll: () => void;
}

export interface ActiveRun {
  key: string;
  agent: string;
  /** Epoch ms the request went out, so any page can show elapsed time. */
  startedAt: number;
  status: 'running' | 'done' | 'error';
  run: AgentRun | null;
  error: string | null;
}

export const RunContext = createContext<RunState | null>(null);

export function useRun(): RunState {
  const context = useContext(RunContext);
  if (!context) throw new Error('useRun must be used inside a RunProvider');
  return context;
}

/**
 * The agent output the review pages (Change, Suggestions, Decide) work on:
 * the chosen agent's latest saved version for this workflow.
 */
export function useCurrentRun() {
  const { upload, recommendation, selectedAgent, activeRun, agentRuns, saveAgentRun } = useRun();
  const agentId = selectedAgent || recommendation?.primary_agent || null;
  const runKey = agentId && upload ? `${agentId}:${upload.workflow_id}` : null;
  const run = (runKey && (agentRuns[runKey] ?? (activeRun?.key === runKey ? activeRun.run : null))) || null;
  const agent = recommendation?.recommended_agents.find((a) => a.agent === agentId) ?? null;
  const save = (next: AgentRun) => {
    if (runKey) saveAgentRun(runKey, next);
  };
  return { agentId, agent, run, save };
}
