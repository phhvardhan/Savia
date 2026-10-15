import { useEffect, useRef, useState } from 'react';
import { FanConnector } from '../components/ui/FanConnector';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Section } from '../components/ui/Section';
import { StatusPill } from '../components/ui/StatusPill';
import { StatGrid } from '../components/ui/StatGrid';
import { formatBytes } from '../state/attachment';
import { AGENT_META } from '../lib/savia';
import type { UploadResult } from '../lib/savia';
import { readDocStats } from '../lib/docStats';
import styles from './ReadingPage.module.css';

type StepState = 'Done' | 'Now' | 'Next';

const STEPS = [
  { title: 'Read the document', note: 'Text, tables, slides and speech, file by file' },
  { title: 'Match it to the project', note: 'Checks what this run has already produced' },
  { title: 'Work out the stage', note: 'Requirements, design, testing or release?' },
  { title: 'Choose the agents', note: `Ranks all ${Object.keys(AGENT_META).length} agents for this input` },
];

/** Steps 2–4 are one AI call; they advance on a timer so the wait reads as progress. */
const STAGGER_MS = 4000;
/** Once the answer is in, the remaining steps finish at this pace before screen 04 opens. */
const FINISH_MS = 500;
const TIPS = Object.values(AGENT_META);

interface ReadingLoaderProps {
  files: File[];
  /** Set once the files are read; the counts and word total come from it. */
  ingested: UploadResult | null;
  /** When the recommendation call started (null while still reading). */
  recommendingSince: number | null;
  startedAt: number;
  error: string | null;
  /** The recommendation is in: play the remaining steps out, then call onFinished. */
  finished: boolean;
  onFinished: () => void;
  onCancel: () => void;
  onRetry: () => void;
}

/** Screen 03: what the person watches while Savia reads the input and picks the agents. */
export function ReadingLoader({ files, ingested, recommendingSince, startedAt, error, finished, onFinished, onCancel, onRetry }: ReadingLoaderProps) {
  const [now, setNow] = useState(() => Date.now());
  const gaveRef = useRef<HTMLDivElement>(null);
  const hubRef = useRef<HTMLElement>(null);
  const recommendsRef = useRef<HTMLUListElement>(null);
  const [finishedAt, setFinishedAt] = useState<number | null>(null);
  if (finished && finishedAt === null) setFinishedAt(Date.now());
  useEffect(() => {
    if (error) return;
    const timer = setInterval(() => setNow(Date.now()), finishedAt ? 100 : 1000);
    return () => clearInterval(timer);
  }, [error, finishedAt]);

  const seconds = Math.max(0, Math.floor((now - startedAt) / 1000));
  const elapsed = `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;

  // Index of the step that is "Now"; everything before it is Done. STEPS.length = all Done.
  const timed = (at: number) =>
    recommendingSince === null ? 0 : Math.min(1 + Math.floor(Math.max(0, at - recommendingSince) / STAGGER_MS), STEPS.length - 1);
  const current = finishedAt
    ? Math.min(timed(finishedAt) + 1 + Math.floor((now - finishedAt) / FINISH_MS), STEPS.length)
    : timed(now);
  const allDone = current === STEPS.length;
  useEffect(() => {
    if (!allDone) return;
    const timer = setTimeout(onFinished, FINISH_MS);
    return () => clearTimeout(timer);
  }, [allDone, onFinished]);
  const lineDeps = [current, Boolean(ingested), Boolean(error)];
  const state = (i: number): StepState => (i < current ? 'Done' : i === current ? 'Now' : 'Next');

  const tip = TIPS[Math.floor(seconds / 5) % TIPS.length];
  const stats = ingested ? readDocStats(ingested.full_normalized_text) : null;
  const found = [
    { value: stats ? String(stats.userStories) : '—', caption: 'User Stories', hint: stats?.notes.userStories ?? 'reading…', tone: 'blue' as const },
    { value: stats ? String(stats.acceptanceCriteria) : '—', caption: 'Acceptance Criteria', hint: stats?.notes.acceptanceCriteria ?? 'reading…', tone: 'orange' as const },
    { value: stats ? String(stats.systemsTouched) : '—', caption: 'Systems Touched', hint: stats?.notes.systemsTouched ?? 'reading…', tone: 'green' as const },
    { value: stats ? String(stats.openQuestions) : '—', caption: 'Open Questions', hint: stats?.notes.openQuestions ?? 'reading…', tone: 'red' as const },
  ];

  return (
    <Section
      id="reading"
      title="SAVIA is reading it"
      size="compact"
      titleClassName={styles.titleRed}
      subtitle="It reads the document first, then works out where you are in the lifecycle and which agents fit."
      aside={
        error ? (
          <StatusPill tone="alert" dot>Run failed</StatusPill>
        ) : (
          <StatusPill tone="info" dot pulse>{`Working · ${elapsed}`}</StatusPill>
        )
      }
    >
      <Card panel className={styles.panel}>
        <div className={styles.board}>
          <p className={`${styles.columnLabel} ${styles.labelGave}`}>What you gave it</p>
          <p className={`${styles.columnLabel} ${styles.labelWorking}`}>Savia is working it out</p>
          <p className={`${styles.columnLabel} ${styles.labelRecommends}`}>What it recommends</p>

          <div ref={gaveRef} className={styles.gave}>
            <article className={styles.inputCard}>
              <div className={styles.inputHead}>
                <h3 className={styles.inputTitle}>{files.length === 1 ? files[0].name : `${files.length} files`}</h3>
                <Badge tone={ingested ? 'solidGreen' : 'waiting'}>{ingested ? 'Read' : 'Reading'}</Badge>
              </div>
              <p className={styles.inputMeta}>
                {[
                  formatBytes(files.reduce((total, f) => total + f.size, 0)),
                  ingested ? `${ingested.metadata.word_count.toLocaleString()} words` : null,
                ]
                  .filter(Boolean)
                  .join(' · ')}
              </p>
              {files.length > 1 && (
                <ul className={styles.inputList}>
                  {files.map((f) => (
                    <li key={`${f.name}:${f.lastModified}`} className={styles.inputItem}>
                      <span className={styles.bullet} aria-hidden="true">·</span>
                      <span>{f.name}</span>
                    </li>
                  ))}
                </ul>
              )}
            </article>
          </div>

          <FanConnector
            className={`${styles.connector} ${styles.connectorLeft}`}
            cards={gaveRef}
            cardSelector=":scope > article"
            hub={hubRef}
            hubSide="right"
            deps={lineDeps}
          />

          <section ref={hubRef} className={styles.orchestrator} aria-label="Savia agent recommender progress" aria-live="polite">
            <div className={styles.orchestratorHead}>
              <h3 className={styles.orchestratorName}>Savia · Agent Recommender</h3>
              <p className={styles.orchestratorState}>
                Step {Math.min(current + 1, STEPS.length)} of {STEPS.length}
              </p>
            </div>
            {STEPS.map((step, i) => (
              <div key={step.title} className={styles.step}>
                <div className={styles.stepHead}>
                  <h4 className={`${styles.stepTitle} ${state(i) === 'Next' ? styles.stepTitleNext : ''}`}>{step.title}</h4>
                  <span
                    className={`${styles.statePill} ${
                      state(i) === 'Now' ? styles.stateNow : state(i) === 'Next' ? styles.stateNext : styles.stateDone
                    }`}
                  >
                    {state(i) === 'Now' && <span className={styles.stateDot} aria-hidden="true" />}
                    {state(i)}
                  </span>
                </div>
                {state(i) !== 'Next' && (
                  <p className={styles.stepNote}>
                    {i === 0 && ingested
                      ? `Read ${files.length} file${files.length === 1 ? '' : 's'} · ${ingested.metadata.word_count.toLocaleString()} words`
                      : step.note}
                  </p>
                )}
              </div>
            ))}
          </section>

          <FanConnector
            className={`${styles.connector} ${styles.connectorRight}`}
            cards={recommendsRef}
            cardSelector=":scope > li"
            hub={hubRef}
            hubSide="left"
            deps={lineDeps}
            line={() => ({ strokeDasharray: '3 3' })}
          />

          <ul ref={recommendsRef} className={styles.recommends} aria-label="Recommendations, still being worked out">
            {error ? (
              <li className={styles.recommendError}>{error}</li>
            ) : (
              [1, 2, 3, 4, 5].map((n) => (
                <li key={n} className={styles.skeleton}>
                  <span className={styles.skeletonRank}>{n}</span>
                  <span className={styles.skeletonBar} />
                </li>
              ))
            )}
          </ul>
        </div>

        <div className={styles.statsBorder}>
          <StatGrid label="What it has found so far" stats={found} />
        </div>

        {!error && (
          <div className={styles.tip} aria-live="polite">
            <p className={styles.tipLabel}>While you wait · one of the agents Savia can pick</p>
            <p key={tip.label} className={styles.tipBody}>
              <strong>{tip.full}</strong> · {tip.blurb}. You get: {tip.output}.
            </p>
          </div>
        )}

        <div className={styles.footer}>
          <div>
            <h2 className={styles.footerTitle}>{error ? 'Savia could not finish reading it' : 'You can leave this page, it carries on'}</h2>
            <p className={styles.footerBody}>
              {error
                ? 'Check the files on the previous screen and try again.'
                : 'The recommendation appears here when it is ready. Nothing is saved or published in this step.'}
            </p>
          </div>
          <div className={styles.footerActions}>
            {error && (
              <Button variant="primary" onClick={onRetry}>
                Back to my files
              </Button>
            )}
            <Button onClick={onCancel}>Cancel the run</Button>
          </div>
        </div>
      </Card>
    </Section>
  );
}
