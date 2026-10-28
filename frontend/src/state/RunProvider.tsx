import { useCallback, useMemo, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import { ApiError } from '../lib/api';
import { runAgent } from '../lib/savia';
import { RunContext } from './run';
import type { ActiveRun } from './run';
import type { AgentRun, Recommendation, UploadResult } from '../lib/savia';

export function RunProvider({ children }: { children: ReactNode }) {
  const [upload, setUpload] = useState<UploadResult | null>(null);
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [agentRuns, setAgentRuns] = useState<Record<string, AgentRun>>({});
  const [activeRun, setActiveRun] = useState<ActiveRun | null>(null);
  /** Which workflow the cached runs belong to. */
  const currentWorkflow = useRef<string | null>(null);

  const setRun = useCallback((nextUpload: UploadResult, nextRecommendation: Recommendation) => {
    // Only a genuinely different workflow invalidates what agents produced.
    // Re-reading the same document must not wipe a run that is in flight.
    if (currentWorkflow.current !== nextUpload.workflow_id) {
      currentWorkflow.current = nextUpload.workflow_id;
      setAgentRuns({});
      setActiveRun(null);
    }
    setUpload(nextUpload);
    setRecommendation(nextRecommendation);
    // A fresh read resets the choice to whatever SAVIA picked.
    setSelectedAgent(nextRecommendation.primary_agent);
  }, []);

  const selectAgent = useCallback((agent: string) => setSelectedAgent(agent), []);

  const saveAgentRun = useCallback((key: string, run: AgentRun) => {
    setAgentRuns((current) => ({ ...current, [key]: run }));
    // Pages read the active run first, so an edited version must replace it there too.
    setActiveRun((current) => (current && current.key === key ? { ...current, status: 'done', run } : current));
  }, []);

  const startAgentRun = useCallback(
    (agentId: string, input?: UploadResult, sourceArtifactId?: string) => {
      // `input` is for a hand-off: setRun has not rendered yet, so the new document is passed in directly.
      const source = input ?? upload;
      if (!source) return;
      const key = `${agentId}:${source.workflow_id}`;

      // Already produced for this document — show it rather than pay again.
      const startedAt = Date.now();
      const existing = agentRuns[key];
      if (existing) {
        setActiveRun({ key, agent: agentId, startedAt, status: 'done', run: existing, error: null });
        return;
      }

      setActiveRun({ key, agent: agentId, startedAt, status: 'running', run: null, error: null });

      runAgent(agentId, {
        workflow_id: source.workflow_id,
        input_text: source.full_normalized_text,
        // A hand-off: the server builds the input from that output and checks the agent may take it.
        ...(sourceArtifactId ? { source_artifact_id: sourceArtifactId } : {}),
      })
        .then((run) => {
          setAgentRuns((current) => ({ ...current, [key]: run }));
          setActiveRun({ key, agent: agentId, startedAt, status: 'done', run, error: null });
        })
        .catch((caught: unknown) => {
          setActiveRun({
            key,
            agent: agentId,
            startedAt,
            status: 'error',
            run: null,
            error: caught instanceof ApiError ? caught.message : 'The agent run failed.',
          });
        });
    },
    [upload, agentRuns],
  );

  const resetAll = useCallback(() => {
    currentWorkflow.current = null;
    setUpload(null);
    setRecommendation(null);
    setSelectedAgent(null);
    setAgentRuns({});
    setActiveRun(null);
  }, []);

  const value = useMemo(
    () => ({
      upload,
      recommendation,
      setRun,
      selectedAgent,
      selectAgent,
      agentRuns,
      saveAgentRun,
      activeRun,
      startAgentRun,
      resetAll,
    }),
    [
      upload,
      recommendation,
      setRun,
      selectedAgent,
      selectAgent,
      agentRuns,
      saveAgentRun,
      activeRun,
      startAgentRun,
      resetAll,
    ],
  );
  return <RunContext.Provider value={value}>{children}</RunContext.Provider>;
}
