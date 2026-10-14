import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Section } from '../components/ui/Section';
import { StatusPill } from '../components/ui/StatusPill';
import { StatGrid } from '../components/ui/StatGrid';
import { Spinner } from '../components/ui/Spinner';
import { Modal } from '../components/ui/Modal';
import { agentMeta, artifactExportUrl, summariseContent } from '../lib/savia';
import type { RecommendedAgent, OutputPart } from '../lib/savia';
import { useRun } from '../state/run';
import { useConnectorEnds } from '../hooks/useConnectorEnds';
import styles from './WritingPage.module.css';

type SectionState = 'Done' | 'Writing' | 'Next';
type RunPhase = 'idle' | 'running' | 'done' | 'error';

// Helper to check if item is a structured object
function isObject(val: unknown): val is Record<string, unknown> {
  return typeof val === 'object' && val !== null && !Array.isArray(val);
}

export function WritingPage() {
  const navigate = useNavigate();
  const { upload, recommendation, selectedAgent, activeRun, agentRuns } = useRun();

  const [now, setNow] = useState(() => Date.now());
  const [selectedPart, setSelectedPart] = useState<OutputPart | null>(null);

  const agent: RecommendedAgent | null =
    recommendation?.recommended_agents.find((a) => a.agent === selectedAgent) ??
    recommendation?.recommended_agents[0] ??
    null;
  const meta = agent ? agentMeta(agent) : null;

  const runKey = agent && upload ? `${agent.agent}:${upload.workflow_id}` : null;
  const cached = runKey ? agentRuns[runKey] : undefined;

  const run = activeRun?.run ?? cached ?? null;
  const error = activeRun?.error ?? null;
  const phase: RunPhase = activeRun?.status ?? (run ? 'done' : 'idle');

  useEffect(() => {
    if (phase !== 'running') return;
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, [phase]);

  const elapsed =
    phase === 'running' && activeRun
      ? Math.max(0, Math.floor((now - activeRun.startedAt) / 1000))
      : 0;

  const pendingValue = phase === 'running' ? <Spinner label="Still running" /> : '—';
  
  // Filter out alias duplicate keys and empty items
  const rawParts = run ? summariseContent(run.content) : [];
  const parts = rawParts.filter((part) => {
    // Exclude redundant alias keys
    if (part.key === 'discussion_summary' || part.key === 'decisions') return false;
    // Exclude empty arrays or 0-count items
    if (part.count === 0) return false;
    if (!part.detail || !part.detail.trim()) return false;
    return true;
  });

  const steps: Array<{ id: string; title: string; state: SectionState; note?: string }> =
    phase === 'done'
      ? parts.map((part) => ({ id: part.key, title: part.title, state: 'Done' }))
      : [
          { id: 'context', title: 'Receive context packet', state: 'Done' },
          {
            id: 'run',
            title: meta ? `Run ${meta.label} agent` : 'Run agent',
            state: phase === 'error' ? 'Next' : 'Writing',
            note: phase === 'error' ? error ?? undefined : 'Grounding output in transcript',
          },
          { id: 'write', title: 'Write output', state: 'Next' },
        ];

  // Excel only makes sense when the output has tables (stories, actions, test cases…).
  const hasTables = Boolean(
    run && Object.values(run.content).some((v) => Array.isArray(v) && v.length > 0 && v.every(isObject)),
  );
  const download = (fmt: 'docx' | 'xlsx') => {
    if (run) window.location.assign(artifactExportUrl(run.artifact_id, fmt));
  };

  const outputsRef = useRef<HTMLDivElement>(null);
  const connectorRef = useRef<SVGSVGElement>(null);
  const outputYs = useConnectorEnds(outputsRef, connectorRef, ':scope > button', [parts.length, phase]);

  // Render formatted HTML content inside Modal (NO raw JSON strings)
  const renderFormattedModalContent = (part: OutputPart) => {
    if (part.items && part.items.length > 0) {
      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {part.items.map((item, idx) => {
            if (isObject(item)) {
              // Action Item Object
              if ('action' in item || 'action_id' in item) {
                const actionId = String(item.action_id || item.id || `ACT-${idx + 1}`);
                const actionText = String(item.action || item.description || '');
                const speaker = String(item.speaker || 'Discussion Participant');
                const assignee = String(item.assignee || 'Design Team');
                const priority = String(item.priority || 'Medium');
                const status = String(item.status || 'Pending');

                return (
                  <div key={idx} className={styles.modalItemCard}>
                    <div className={styles.modalItemCardHeader}>
                      <span className={styles.modalItemTag}>{actionId}</span>
                      <div style={{ display: 'flex', gap: '6px' }}>
                        <Badge tone={priority === 'High' ? 'runningSoft' : 'waiting'}>{priority} Priority</Badge>
                        <Badge tone="doneSoft">{status}</Badge>
                      </div>
                    </div>
                    <div className={styles.modalItemBody}>
                      <strong>Action:</strong> {actionText}
                    </div>
                    <div className={styles.modalItemMeta}>
                      Speaker: {speaker} · Assignee: {assignee}
                    </div>
                  </div>
                );
              }

              // Decision Object
              if ('decision' in item || 'decision_id' in item) {
                const decId = String(item.decision_id || item.id || `DEC-${idx + 1}`);
                const decText = String(item.decision || '');
                const speaker = String(item.speaker || 'Meeting Consensus');
                const context = String(item.context || 'Finalized during workshop');

                return (
                  <div key={idx} className={styles.modalItemCard}>
                    <div className={styles.modalItemCardHeader}>
                      <span className={styles.modalItemTag}>{decId}</span>
                      <Badge tone="doneSoft">Agreed Decision</Badge>
                    </div>
                    <div className={styles.modalItemBody}>
                      <strong>Decision:</strong> {decText}
                    </div>
                    <div className={styles.modalItemMeta}>
                      Decided by: {speaker} · Context: {context}
                    </div>
                  </div>
                );
              }

              // Generic Object fallback (formatted key-value pairs)
              return (
                <div key={idx} className={styles.modalItemCard}>
                  {Object.entries(item).map(([k, v]) => (
                    <div key={k} style={{ marginBottom: '4px', fontSize: '13px' }}>
                      <strong style={{ color: '#0F172A' }}>{k.replace(/_/g, ' ')}:</strong> {String(v)}
                    </div>
                  ))}
                </div>
              );
            }

            // String Item (Key points, Requirements, Open Questions)
            return (
              <div key={idx} className={styles.modalItemCard}>
                <div className={styles.modalItemBody}>
                  <span style={{ color: '#005EEB', fontWeight: 'bold', marginRight: '6px' }}>•</span>
                  {String(item)}
                </div>
              </div>
            );
          })}
        </div>
      );
    }

    return (
      <p style={{ fontSize: '15px', lineHeight: '1.6', color: '#1E293B', whiteSpace: 'pre-wrap' }}>
        {part.fullText || part.detail}
      </p>
    );
  };

  return (
    <Section
      id="writing"
      title={meta ? `${meta.label} is ${meta.working}` : 'No agent selected'}
      size="compact"
      titleClassName={styles.titleRed}
      subtitle="View produced outputs below. Click any category to view full structured formatted details."
      aside={
        phase === 'done' ? (
          <StatusPill tone="done">Complete</StatusPill>
        ) : phase === 'error' ? (
          <StatusPill tone="alert" dot>
            Run failed
          </StatusPill>
        ) : (
          <StatusPill tone="running" dot pulse>
            Working · {elapsed}s elapsed
          </StatusPill>
        )
      }
    >
      <Card panel className={styles.panel}>
        {phase === 'running' && (
          <div
            className={styles.progress}
            role="progressbar"
            aria-label={`The ${meta?.label ?? 'agent'} agent is running`}
          >
            <span className={styles.progressBar} />
          </div>
        )}
        <div className={styles.board}>
          <p className={`${styles.columnLabel} ${styles.labelGave}`}>What it received</p>
          <p className={`${styles.columnLabel} ${styles.labelWorking}`}>
            {meta ? `${meta.label} agent` : 'Agent'}
          </p>
          <p className={`${styles.columnLabel} ${styles.labelRecommends}`}>What it produced</p>

          <div className={styles.gave}>
            <article className={styles.inputCard}>
              <div className={styles.inputHead}>
                <h3 className={styles.inputTitle}>Context packet</h3>
                <Badge tone="solidGreen">Received</Badge>
              </div>
              <p className={styles.inputMeta}>
                {upload ? `${upload.filename} · workflow ${upload.workflow_id}` : 'Nothing received'}
              </p>
              <ul className={styles.inputList}>
                {(agent?.required_inputs ?? []).map((item) => item.replace(/_/g, ' ')).map((item) => (
                  <li key={item} className={styles.inputItem}>
                    <span className={styles.bullet} aria-hidden="true">·</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </article>

            <article className={styles.inputCard}>
              <div className={styles.inputHead}>
                <h3 className={styles.inputTitle}>J&amp;J design template</h3>
                <Badge tone="waiting">Loaded</Badge>
              </div>
              <p className={styles.inputMeta}>RICEFW design specification</p>
            </article>
          </div>

          <svg
            className={`${styles.connector} ${styles.connectorLeft}`}
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
            aria-hidden="true"
          >
            <path d="M0 25 C 45 25, 55 46, 100 46" fill="none" stroke="#C3C4C5" strokeWidth="1.2" vectorEffect="non-scaling-stroke" />
            <path d="M0 75 C 45 75, 55 54, 100 54" fill="none" stroke="#C3C4C5" strokeWidth="1.2" vectorEffect="non-scaling-stroke" />
          </svg>

          <section className={styles.orchestrator} aria-label="Agent progress">
            <div className={styles.orchestratorHead}>
              <h3 className={styles.orchestratorName}>{meta ? meta.label : 'Agent'}</h3>
              <p className={styles.orchestratorState}>
                {phase === 'done'
                  ? `${parts.length} parts produced`
                  : phase === 'error'
                    ? 'Run failed'
                    : 'Running'}
              </p>
            </div>
            {steps.map((item) => (
              <div key={item.id} className={styles.step}>
                <div className={styles.stepHead}>
                  <h4
                    className={`${styles.stepTitle} ${
                      item.state === 'Done'
                        ? styles.stepTitleDone
                        : item.state === 'Writing'
                          ? styles.stepTitleWriting
                          : ''
                    }`}
                  >
                    {item.title}
                  </h4>
                  <span
                    className={`${styles.statePill} ${
                      item.state === 'Writing' ? styles.stateWriting : styles.stateDone
                    }`}
                  >
                    {item.state === 'Writing' && <span className={styles.stateDot} aria-hidden="true" />}
                    {item.state}
                  </span>
                </div>
                {item.note && <p className={styles.stepNote}>{item.note}</p>}
              </div>
            ))}
          </section>

          <svg
            ref={connectorRef}
            className={`${styles.connector} ${styles.connectorRight}`}
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
            aria-hidden="true"
          >
            {outputYs.map((end, i) => {
              // Fan out from the middle of the agent box, one line per output card.
              const start = 50 + (i - (outputYs.length - 1) / 2) * 4;
              return (
                <path
                  key={i}
                  d={`M0 ${start} C 50 ${start}, 50 ${end}, 100 ${end}`}
                  fill="none"
                  stroke="#C3C4C5"
                  strokeWidth="1.2"
                  vectorEffect="non-scaling-stroke"
                />
              );
            })}
          </svg>

          <div ref={outputsRef} className={styles.outputs}>
            {phase === 'error' && <div className={styles.recommendError}>{error}</div>}

            {phase === 'idle' && (
              <div className={styles.recommendError}>
                No run started. Go to the plan and press “Approve and start”.
              </div>
            )}

            {phase !== 'error' && parts.length === 0 && (
              <div className={`${styles.recommend} ${phase === 'running' ? styles.pending : ''}`}>
                <div className={styles.outputHead}>
                  <h3 className={styles.outputTitle}>{meta ? meta.output : 'Agent output'}</h3>
                  <span className={styles.outputState}>
                    {phase === 'running' ? 'Building' : 'Waiting'}
                  </span>
                </div>
                <p className={styles.recommendText}>
                  {agent ? agent.agent_name : 'Waiting for a plan to approve'}
                </p>
              </div>
            )}

            {/* Non-empty produced parts */}
            {parts.map((part) => (
              <button
                key={part.key}
                type="button"
                className={`${styles.recommend} ${styles.outputCard}`}
                onClick={() => setSelectedPart(part)}
              >
                <h3 className={styles.outputTitle}>{part.title}</h3>
                <p className={`${styles.recommendText} ${styles.outputDetail}`}>
                  {part.count !== null ? `${part.count} items` : part.detail}
                </p>
                <span className={styles.outputLink}>
                  {part.count !== null ? 'View the list →' : 'Read it all →'}
                </span>
              </button>
            ))}
          </div>
        </div>

        <div className={styles.statsBorder}>
          <StatGrid
            label="What it has written so far"
            labelTone="ink"
            stats={[
              {
                value: run ? String(parts.length) : pendingValue,
                caption: 'parts produced',
                hint: meta ? meta.output : 'waiting on the agent',
              },
              {
                value: run ? String(parts.reduce((t, p) => t + (p.count ?? 0), 0)) : pendingValue,
                caption: 'items in total',
                hint: 'across every part',
              },
              {
                value: run ? `v${run.version}` : pendingValue,
                caption: 'artifact version',
                hint: run ? run.artifact_id : phase === 'running' ? 'saving when it finishes' : 'not saved yet',
              },
              {
                value: run ? run.stage : pendingValue,
                caption: 'lifecycle stage',
                hint: 'recorded on the workflow',
                tone: 'orange' as const,
              },
            ]}
          />
        </div>

        <div className={styles.footer}>
          <div className={styles.footerActions}>
            <Button variant="primary" onClick={() => navigate('/document')}>
              View Full {meta ? `${meta.label} Document Canvas` : 'Document Editor'}
            </Button>
            {run && <Button onClick={() => download('docx')}>Download Word</Button>}
            {run && hasTables && <Button onClick={() => download('xlsx')}>Download Excel</Button>}
            <Button onClick={() => navigate('/reading')}>Back to recommendations</Button>
          </div>
        </div>
      </Card>

      {/* Formatted Detail Modal (No JSON raw text) */}
      {selectedPart && (
        <Modal isOpen={Boolean(selectedPart)} onClose={() => setSelectedPart(null)} title={selectedPart.title}>
          <div style={{ padding: '10px 0', maxHeight: '60vh', overflowY: 'auto' }}>
            {renderFormattedModalContent(selectedPart)}
          </div>
          <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'flex-end' }}>
            <Button variant="primary" onClick={() => setSelectedPart(null)}>
              Close
            </Button>
          </div>
        </Modal>
      )}
    </Section>
  );
}
