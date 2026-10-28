import { useCallback, useEffect, useRef, useState } from 'react';
import type { CSSProperties } from 'react';
import { useNavigate } from 'react-router-dom';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Section } from '../components/ui/Section';
import { StatusPill } from '../components/ui/StatusPill';
import { StatGrid } from '../components/ui/StatGrid';
import { DataTable } from '../components/ui/DataTable';
import { formatBytes, useAttachment } from '../state/attachment';
import { useRun } from '../state/run';
import { FanConnector } from '../components/ui/FanConnector';
import { AGENT_META, agentLabel, agentMeta, ingestFile, recommendAgents } from '../lib/savia';
import { readDocStats } from '../lib/docStats';
import { ApiError } from '../lib/api';
import { claim, isClaimed, release, resetOnce } from '../lib/once';
import { ReadingLoader } from './ReadingLoader';
import type { UploadResult } from '../lib/savia';
import styles from './ReadingPage.module.css';

type StepState = 'Done' | 'Now' | 'Next';
type Phase = 'idle' | 'reading' | 'recommending' | 'done' | 'error';

const STEP_TITLES = ['Read the input', 'Work out the stage', 'Choose the agents'];

/** Figma screen 04: each agent has its own colour; only the chosen card lights up in it. */
const tone = (agent: string) => ({ '--tone': AGENT_META[agent]?.color ?? '#005EEB' }) as CSSProperties;

/** Step states straight from the two real calls: ingest, then one AI call that
 *  works out the stage and the agents together. */
const STEP_STATES: Record<Phase, StepState[]> = {
  idle: ['Next', 'Next', 'Next'],
  reading: ['Now', 'Next', 'Next'],
  recommending: ['Done', 'Now', 'Now'],
  done: ['Done', 'Done', 'Done'],
  error: ['Next', 'Next', 'Next'],
};

/**
 * The reveal is a one-off. Module scope means it survives re-renders and
 * re-visits within this page load, and resets only on a real reload.
 */
let hasRevealed = false;

/** Lets long file names wrap after _ or - rather than mid-word ("…105526.mp" / "4"). */
function withBreaks(name: string) {
  return name.split(/(?<=[_-])/).flatMap((part, i) => (i ? [<wbr key={i} />, part] : [part]));
}

export function ReadingPage() {
  const navigate = useNavigate();
  const { attachment, setAttachment } = useAttachment();
  const { upload, recommendation, setRun, selectedAgent, selectAgent, startAgentRun, resetAll } = useRun();

  const [reveal] = useState(() => !hasRevealed);

  // Starts in 'reading' when there is already a file, so the first paint shows
  // the run underway rather than setting that state from inside the effect.
  const [phase, setPhase] = useState<Phase>(() =>
    recommendation ? 'done' : attachment ? 'reading' : 'idle',
  );
  const [error, setError] = useState<string | null>(null);
  // For the loading screen: what has been read so far, and when each call started.
  const [ingestedNow, setIngestedNow] = useState<UploadResult | null>(null);
  const [startedAt] = useState(() => Date.now());
  const [recommendingSince, setRecommendingSince] = useState<number | null>(null);
  // The loading screen stays until its steps have played out (instantly when re-visiting).
  const [loaderDone, setLoaderDone] = useState(() => Boolean(recommendation));
  const finishLoader = useCallback(() => setLoaderDone(true), []);

  // The real run: ingest the file, then ask SAVIA which agent fits.
  useEffect(() => {
    if (!attachment) return;

    // One ingest + recommend per file; a second would create a second workflow.
    const key = `ingest:${attachment.files.map((f) => `${f.name}:${f.size}:${f.lastModified}`).join('|')}`;
    if (!claim(key)) return;

    // No "cancelled" guard: the request is claimed once per file, so StrictMode's
    // dev remount skips it and only this first run can report progress. Setting
    // state after a real unmount is a harmless no-op in React 18+.
    (async () => {
      try {
        const ingested = await ingestFile(attachment.files);
        if (!isClaimed(key)) return; // cancelled while reading
        setIngestedNow(ingested);
        setRecommendingSince(Date.now());
        setPhase('recommending');
        const result = await recommendAgents({
          workflow_id: ingested.workflow_id,
          raw_text: ingested.full_normalized_text,
          input_type: ingested.input_type,
          filename: ingested.filename,
        });
        if (!isClaimed(key)) return; // cancelled: don't bring the old run back
        setRun(ingested, result);
        setPhase('done');
      } catch (caught) {
        if (!isClaimed(key)) return;
        release(key);
        setError(caught instanceof ApiError ? caught.message : 'Something went wrong.');
        setPhase('error');
      }
    })();
  }, [attachment, setRun]);

  const steps = STEP_TITLES.map((title, index) => ({
    id: title,
    title,
    state: STEP_STATES[phase][index],
    note:
      index === 1 && recommendation?.current_stage
        ? `Detected stage · ${recommendation.current_stage}`
        : undefined,
  }));
  const doneSteps = steps.filter((step) => step.state === 'Done').length;
  const currentStepNumber = Math.min(doneSteps + 1, STEP_TITLES.length);
  // The API decides the chosen agent; the two below it stay as designed.
  // Only agents the document actually triggered belong on this screen.
  const recommends = (recommendation?.recommended_agents ?? [])
    .filter((agent) => agent.matched)
    .slice(0, 5);
  const byAI = recommendation?.source === 'llm';
  const missing = recommendation?.missing_information ?? [];
  const chosen = recommends.find((agent) => agent.agent === selectedAgent) ?? recommends[0] ?? null;
  const countWord = ['no', 'one', 'two', 'three', 'four', 'five'][recommends.length] ?? String(recommends.length);

  // Right-hand connector ends, measured from where each card actually sits
  // (cards vary in height and count), as % of the connector's height.
  const recommendsRef = useRef<HTMLUListElement>(null);
  const gaveRef = useRef<HTMLDivElement>(null);
  const hubRef = useRef<HTMLElement>(null);
  const lineDeps = [recommends.length, chosen?.agent, missing.length, phase];

  // Counted from the document's own text, not from fixed copy.
  const stats = upload ? readDocStats(upload.full_normalized_text) : null;

  const found = [
    {
      value: stats ? String(stats.userStories) : '—',
      caption: 'User Stories',
      hint: stats ? stats.notes.userStories : 'waiting on the document',
      tone: 'blue' as const,
    },
    {
      value: stats ? String(stats.acceptanceCriteria) : '—',
      caption: 'Acceptance Criteria',
      hint: stats ? stats.notes.acceptanceCriteria : 'waiting on the document',
      tone: 'orange' as const,
    },
    {
      value: stats ? String(stats.systemsTouched) : '—',
      caption: 'Systems Touched',
      hint: stats ? stats.notes.systemsTouched : 'waiting on the document',
      tone: 'green' as const,
    },
    {
      value: stats ? String(stats.openQuestions) : '—',
      caption: 'Open Questions',
      hint: stats ? stats.notes.openQuestions : 'waiting on the document',
      tone: 'red' as const,
    },
  ];

  // Marked only once the sequence has finished, so React StrictMode's
  // immediate dev remount still plays it rather than swallowing it.
  useEffect(() => {
    if (!reveal) return;
    const timer = setTimeout(() => {
      hasRevealed = true;
    }, 3200);
    return () => clearTimeout(timer);
  }, [reveal]);

  // Screen 03: a loading screen, not a page, until the recommendation is in.
  if (attachment && phase !== 'idle' && !(phase === 'done' && loaderDone)) {
    return (
      <ReadingLoader
        files={attachment.files}
        ingested={ingestedNow}
        recommendingSince={recommendingSince}
        startedAt={startedAt}
        error={error}
        finished={phase === 'done'}
        onFinished={finishLoader}
        onCancel={() => {
          resetAll();
          setAttachment(null);
          resetOnce();
          navigate('/work');
        }}
        onRetry={() => navigate('/intake')}
      />
    );
  }

  return (
    <Section
      id="reading"
      title={
        phase === 'done'
          ? `Savia read it and recommends ${countWord} agent${recommends.length === 1 ? '' : 's'}`
          : 'SAVIA is reading it'
      }
      size="compact"
      titleClassName={styles.titleRed}
      subtitle="It reads what you gave it, works out where you are in the lifecycle and which agents fit, then you approve the plan."
      aside={
        phase === 'done' ? (
          <StatusPill tone="alert" dot>
            Your turn · approve the plan
          </StatusPill>
        ) : phase === 'error' ? (
          <StatusPill tone="alert" dot>
            Run failed
          </StatusPill>
        ) : (
          <StatusPill tone="info" dot pulse>
            Working…
          </StatusPill>
        )
      }
    >
      <Card panel className={styles.panel}>
        <div className={`${styles.board} ${reveal ? styles.reveal : ''}`}>
          <p className={`${styles.columnLabel} ${styles.labelGave}`}>What you gave it</p>
          <p className={`${styles.columnLabel} ${styles.labelWorking}`}>Savia is working it out</p>
          <p className={`${styles.columnLabel} ${styles.labelRecommends}`}>What it recommends</p>

          <div ref={gaveRef} className={styles.gave}>
            <article className={styles.inputCard}>
              <div className={styles.inputHead}>
                <h3 className={styles.inputTitle}>
                  {!attachment
                    ? 'Nothing attached'
                    : attachment.files.length === 1
                      ? withBreaks(attachment.name)
                      : `${attachment.files.length} files`}
                </h3>
                <Badge tone={attachment ? 'solidGreen' : 'waiting'}>
                  {attachment ? 'Read' : 'Waiting'}
                </Badge>
              </div>
              {/* Page and word counts only exist once the backend has parsed the
                  file, so this shows what the browser can actually tell us. */}
              <p className={styles.inputMeta}>
                {attachment
                  ? [
                      formatBytes(attachment.size),
                      attachment.kind,
                      upload ? `${upload.metadata.word_count.toLocaleString()} words` : null,
                    ]
                      .filter(Boolean)
                      .join(' · ')
                  : 'Attach a document or recording to start a run'}
              </p>
              {attachment && (
                <ul className={styles.inputList}>
                  {attachment.files.length > 1 &&
                    attachment.files.map((f) => (
                      <li key={`${f.name}:${f.lastModified}`} className={styles.inputItem}>
                        <span className={styles.bullet} aria-hidden="true">·</span>
                        <span>{withBreaks(f.name)}</span>
                      </li>
                    ))}
                  <li className={styles.inputItem}>
                    <span className={styles.bullet} aria-hidden="true">·</span>
                    <span>Added by you, just now</span>
                  </li>
                </ul>
              )}
            </article>

            {missing.length > 0 && (
              <article className={styles.inputCard}>
                <div className={styles.inputHead}>
                  <h3 className={styles.inputTitle}>What Savia still needs</h3>
                  <Badge tone="waiting">To add</Badge>
                </div>
                <ul className={styles.inputList}>
                  {missing.map((item) => (
                    <li key={item} className={styles.inputItem}>
                      <span className={styles.bullet} aria-hidden="true">·</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </article>
            )}
          </div>

          <FanConnector
            className={`${styles.connector} ${styles.connectorLeft}`}
            cards={gaveRef}
            cardSelector=":scope > article"
            hub={hubRef}
            hubSide="right"
            deps={lineDeps}
          />

          <section ref={hubRef} className={styles.orchestrator} aria-label="Savia agent recommender progress">
            <div className={styles.orchestratorHead}>
              <h3 className={styles.orchestratorName}>Savia · Agent Recommender</h3>
              <p className={styles.orchestratorState}>
                Step {currentStepNumber} of {STEP_TITLES.length}
              </p>
            </div>
            {steps.map((step) => (
              <div key={step.id} className={styles.step}>
                <div className={styles.stepHead}>
                  <h4
                    className={`${styles.stepTitle} ${step.state === 'Next' ? styles.stepTitleNext : ''}`}
                  >
                    {step.title}
                  </h4>
                  <span
                    className={`${styles.statePill} ${
                      step.state === 'Now'
                        ? styles.stateNow
                        : step.state === 'Next'
                          ? styles.stateNext
                          : styles.stateDone
                    }`}
                  >
                    {step.state === 'Now' && <span className={styles.stateDot} aria-hidden="true" />}
                    {step.state}
                  </span>
                </div>
                {step.note && <p className={styles.stepNote}>{step.note}</p>}
              </div>
            ))}
          </section>

          <FanConnector
            className={`${styles.connector} ${styles.connectorRight}`}
            cards={recommendsRef}
            cardSelector=":scope > li > button"
            hub={hubRef}
            hubSide="left"
            deps={lineDeps}
            line={(i) => {
              const isChosen = recommends[i]?.agent === chosen?.agent;
              return {
                stroke: isChosen ? AGENT_META[recommends[i].agent]?.color ?? '#005EEB' : '#C3C4C5',
                strokeWidth: isChosen ? 1.6 : 1.2,
                strokeDasharray: !isChosen && (recommends[i]?.confidence ?? 1) < 0.5 ? '3 3' : undefined,
              };
            }}
          />

          <ul ref={recommendsRef} className={styles.recommends}>
            {error && <li className={styles.recommendError}>{error}</li>}

            {!error && recommends.length === 0 && (
              <li className={styles.recommendPending}>
                {!attachment
                  ? 'Nothing to analyse yet.'
                  : !recommendation
                    ? 'Asking SAVIA which agents fit…'
                    : 'No agent fits this input yet.'}
                {recommendation && recommendation.missing_information.length > 0 && (
                  <>
                    {' '}To get a recommendation, add:
                    <ul>
                      {recommendation.missing_information.map((item) => (
                        <li key={item}>· {item}</li>
                      ))}
                    </ul>
                  </>
                )}
              </li>
            )}

            {recommends.map((item, index) => {
              const isChosen = item.agent === chosen?.agent;
              const isBest = item.agent === recommendation?.primary_agent;
              return (
                <li key={item.agent}>
                  <button
                    type="button"
                    aria-pressed={isChosen}
                    style={tone(item.agent)}
                    className={`${styles.recommend} ${styles.recommendButton} ${
                      isChosen ? styles.recommendChosen : ''
                    }`}
                    onClick={() => selectAgent(item.agent)}
                  >
                    <span className={styles.recommendHead}>
                      <span className={styles.recommendTitle}>{index + 1} · {agentLabel(item)}</span>
                      {isChosen && (
                        <span className={styles.chosenPill}>
                          <span className={styles.stateDot} aria-hidden="true" />
                          Chosen
                        </span>
                      )}
                    </span>
                    {/* Short on purpose: the Plan page's "Why Savia chose it" carries the full reason. */}
                    <span className={styles.recommendText}>
                      {agentMeta(item).blurb} · {isBest ? 'best match for this input' : 'also fits this input'}
                    </span>
                    <span className={styles.confidence}>
                      {byAI
                        ? `${Math.round(item.confidence * 100)}% · AI estimate`
                        : 'Keyword match · AI unavailable'}
                    </span>
                  </button>
                </li>
              );
            })}

            {byAI && recommends.length > 0 && recommendation?.next_action && (
              <li className={styles.recommendPending}>
                <strong>Next step:</strong> {recommendation.next_action}
              </li>
            )}
          </ul>
        </div>

        {phase === 'done' && recommends.length > 0 && (
          <DataTable
            caption="The recommended agents, why each was chosen and who approves it"
            columns={[
              { key: 'rank', label: '', width: '5%' },
              { key: 'agent', label: 'Agent', width: '22%' },
              { key: 'why', label: 'Why Savia chose it' },
              { key: 'get', label: 'What you get', width: '22%' },
              { key: 'approval', label: 'Approval', width: '13%' },
            ]}
            rows={recommends.map((agent, index) => {
              const meta = agentMeta(agent);
              return {
                id: agent.agent,
                cells: [
                  <span key="rank" className={styles.rank} style={tone(agent.agent)}>{index + 1}</span>,
                  meta.full,
                  agent.reason,
                  meta.output,
                  <span key="approval" className={styles.approvalPill}>
                    <span className={styles.approvalDot} aria-hidden="true" />
                    {meta.approver}
                  </span>,
                ],
              };
            })}
          />
        )}

        <div className={styles.statsBorder}>
          <StatGrid label="What it has found so far" stats={found} />
        </div>

        <div className={styles.footer}>
          <div>
            <h2 className={styles.footerTitle}>
              {chosen ? `Run ${agentLabel(chosen)} first` : 'Approve the plan'}
            </h2>
            <p className={styles.footerBody}>
              {chosen
                ? 'Pick a different card above to run another agent. You review its output before anything is saved or shared.'
                : 'The plan appears here once Savia has read your input.'}
            </p>
          </div>
          <div className={styles.footerActions}>
            <Button
              variant="primary"
              disabled={phase !== 'done' || !upload || !chosen}
              onClick={() => {
                // Fire the agent and move on: the writing page shows its progress.
                if (chosen) startAgentRun(chosen.agent);
                // Every agent, TEST included, runs for real and opens its own document.
                navigate('/writing');
              }}
            >
              Approve and start
            </Button>
          </div>
        </div>
      </Card>
    </Section>
  );
}
