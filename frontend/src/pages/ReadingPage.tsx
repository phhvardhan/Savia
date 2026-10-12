import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Section } from '../components/ui/Section';
import { StatusPill } from '../components/ui/StatusPill';
import { StatGrid } from '../components/ui/StatGrid';
import { formatBytes, useAttachment } from '../state/attachment';
import { useRun } from '../state/run';
import { agentLabel, agentMeta, ingestFile, recommendAgents } from '../lib/savia';
import { readDocStats } from '../lib/docStats';
import { ApiError } from '../lib/api';
import { claim, release } from '../lib/once';
import styles from './ReadingPage.module.css';

type StepState = 'Done' | 'Now' | 'Next';
type Phase = 'idle' | 'reading' | 'recommending' | 'done' | 'error';

const STEP_TITLES = [
  'Read the document',
  'Match it to the project',
  'Work out the stage',
  'Choose the agents',
];

/** How long each step sits on "Now" before it flips to "Done". */
const STEP_DURATION_MS = 900;

/**
 * The reveal is a one-off. Module scope means it survives re-renders and
 * re-visits within this page load, and resets only on a real reload.
 */
let hasRevealed = false;

export function ReadingPage() {
  const navigate = useNavigate();
  const { attachment } = useAttachment();
  const { upload, recommendation, setRun, selectedAgent, selectAgent } = useRun();

  const [reveal] = useState(() => !hasRevealed);

  // Starts in 'reading' when there is already a file, so the first paint shows
  // the run underway rather than setting that state from inside the effect.
  const [phase, setPhase] = useState<Phase>(() =>
    recommendation ? 'done' : attachment ? 'reading' : 'idle',
  );
  const [error, setError] = useState<string | null>(null);

  /** Index of the step currently showing "Now"; 4 means every step is done. */
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    if (!attachment || activeStep >= STEP_TITLES.length) return;
    const timer = setTimeout(() => setActiveStep((current) => current + 1), STEP_DURATION_MS);
    return () => clearTimeout(timer);
  }, [attachment, activeStep]);

  // The real run: ingest the file, then ask SAVIA which agent fits.
  useEffect(() => {
    if (!attachment) return;

    // One ingest + recommend per file; a second would create a second workflow.
    const key = `ingest:${attachment.name}:${attachment.size}`;
    if (!claim(key)) return;

    let cancelled = false;

    (async () => {
      try {
        const ingested = await ingestFile(attachment.file);
        if (!cancelled) setPhase('recommending');
        const result = await recommendAgents({
          workflow_id: ingested.workflow_id,
          raw_text: ingested.full_normalized_text,
          input_type: ingested.input_type,
          filename: attachment.name || ingested.filename,
        });
        // Written to the context first: it outlives this component, so the
        // result is not lost if StrictMode unmounted us mid-flight.
        setRun(ingested, result);
        if (cancelled) return;
        setPhase('done');
      } catch (caught) {
        release(key);
        if (cancelled) return;
        setError(caught instanceof ApiError ? caught.message : 'Something went wrong.');
        setPhase('error');
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [attachment, setRun]);

  const lastIndex = STEP_TITLES.length - 1;
  const steps = STEP_TITLES.map((title, index) => {
    let state: StepState = index < activeStep ? 'Done' : index === activeStep ? 'Now' : 'Next';
    // The final step only finishes once SAVIA has actually answered.
    if (index === lastIndex && state === 'Done' && phase !== 'done') state = 'Now';

    return {
      id: title,
      title,
      state,
      note:
        index === 2 && recommendation?.current_stage
          ? `Detected stage · ${recommendation.current_stage}`
          : undefined,
    };
  });
  const currentStepNumber = Math.min(activeStep + 1, STEP_TITLES.length);
  // The API decides the chosen agent; the two below it stay as designed.
  // Only agents the document actually triggered belong on this screen.
  const recommends = (recommendation?.recommended_agents ?? [])
    .filter((agent) => agent.matched)
    .slice(0, 3);

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

  return (
    <Section
      id="reading"
      title="SAVIA is reading it"
      size="compact"
      titleClassName={styles.titleRed}
      subtitle="It reads the document first, then works out where you are in the lifecycle and which agents fit."
      aside={
        <StatusPill tone="info" dot pulse>
          Working · about 40 seconds left
        </StatusPill>
      }
    >
      <Card panel className={styles.panel}>
        <div className={`${styles.board} ${reveal ? styles.reveal : ''}`}>
          <p className={`${styles.columnLabel} ${styles.labelGave}`}>What you gave it</p>
          <p className={`${styles.columnLabel} ${styles.labelWorking}`}>Savia is working it out</p>
          <p className={`${styles.columnLabel} ${styles.labelRecommends}`}>What it recommends</p>

          <div className={styles.gave}>
            <article className={styles.inputCard}>
              <div className={styles.inputHead}>
                <h3 className={styles.inputTitle}>
                  {attachment ? attachment.name : 'Nothing attached'}
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
                  <li className={styles.inputItem}>
                    <span className={styles.bullet} aria-hidden="true">·</span>
                    <span>Added by you, just now</span>
                  </li>
                </ul>
              )}
            </article>

            <article className={styles.inputCard}>
              <div className={styles.inputHead}>
                <h3 className={styles.inputTitle}>Project context</h3>
                <Badge tone="waiting">Loaded</Badge>
              </div>
              <p className={styles.inputMeta}>TIME · Release 2.1 · Finance</p>
              <ul className={styles.inputList}>
                {['12 approved BUS', 'RICEFW FIN-0002', 'Jira · OTC board'].map((item) => (
                  <li key={item} className={styles.inputItem}>
                    <span className={styles.bullet} aria-hidden="true">·</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </article>
          </div>

          <svg
            className={`${styles.connector} ${styles.connectorLeft}`}
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
            aria-hidden="true"
          >
            <path d="M0 25 C 45 25, 55 42, 100 42" fill="none" stroke="#C3C4C5" strokeWidth="0.7" />
            <path d="M0 75 C 45 75, 55 52, 100 52" fill="none" stroke="#C3C4C5" strokeWidth="0.7" />
          </svg>

          <section className={styles.orchestrator} aria-label="Orchestrator progress">
            <div className={styles.orchestratorHead}>
              <h3 className={styles.orchestratorName}>Orchestrator</h3>
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

          <svg
            className={`${styles.connector} ${styles.connectorRight}`}
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
            aria-hidden="true"
          >
            <path d="M0 40 C 50 40, 50 17, 100 17" fill="none" stroke="#005EEB" strokeWidth="0.8" />
            <path d="M0 50 C 50 50, 50 50, 100 50" fill="none" stroke="#C3C4C5" strokeWidth="0.7" />
            <path
              d="M0 60 C 50 60, 50 83, 100 83"
              fill="none"
              stroke="#C3C4C5"
              strokeWidth="0.7"
              strokeDasharray="3 3"
            />
          </svg>

          <ul className={styles.recommends}>
            {error && <li className={styles.recommendError}>{error}</li>}

            {!error && recommends.length === 0 && (
              <li className={styles.recommendPending}>
                {attachment ? 'Asking SAVIA which agents fit…' : 'Nothing to analyse yet.'}
              </li>
            )}

            {recommends.map((item) => {
              const chosen = item.agent === selectedAgent;
              const isBest = item.agent === recommendation?.primary_agent;
              return (
                <li key={item.agent}>
                  <button
                    type="button"
                    aria-pressed={chosen}
                    className={`${styles.recommend} ${styles.recommendButton} ${
                      chosen ? styles.recommendChosen : ''
                    }`}
                    onClick={() => selectAgent(item.agent)}
                  >
                    <span className={styles.recommendHead}>
                      <span className={styles.recommendTitle}>{agentLabel(item)}</span>
                      {chosen && (
                        <span className={styles.chosenPill}>
                          <span className={styles.stateDot} aria-hidden="true" />
                          Chosen
                        </span>
                      )}
                    </span>
                    <span className={styles.recommendText}>
                      {agentMeta(item).blurb} ·{' '}
                      {isBest ? 'best match for this input' : 'also fits this input'}
                    </span>
                    <span className={styles.confidence}>
                      {Math.round(item.confidence * 100)}% confidence
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        </div>

        <div className={styles.statsBorder}>
          <StatGrid label="What it has found so far" stats={found} />
        </div>

        <div className={styles.footer}>
          <div>
            <h2 className={styles.footerTitle}>You can close this it carries on</h2>
            <p className={styles.footerBody}>
              It will appear in My Work the moment it needs you. Nothing is saved or published in this step.
            </p>
          </div>
          <div className={styles.footerActions}>
            <Button variant="primary" onClick={() => navigate('/plan')}>
              Show me the detail
            </Button>
            <Button>Cancel the run</Button>
          </div>
        </div>
      </Card>
    </Section>
  );
}
