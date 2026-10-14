import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Section } from '../components/ui/Section';
import { Spinner } from '../components/ui/Spinner';
import { StatusPill } from '../components/ui/StatusPill';
import { ApiError } from '../lib/api';
import { claim, release } from '../lib/once';
import {
  agentLabel,
  findOpenDecisions,
  recordDecision,
  type OpenDecision,
} from '../lib/savia';
import { useCurrentRun } from '../state/run';
import styles from './DecidePage.module.css';

export function DecidePage() {
  const navigate = useNavigate();
  const { run, agent, save } = useCurrentRun();
  const label = agent ? agentLabel(agent) : 'Savia';

  // Found once per document (not per version), so deciding one doesn't re-scan.
  const [decisions, setDecisions] = useState<OpenDecision[] | null>(null);
  const [index, setIndex] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [working, setWorking] = useState(false);
  const [decidedCount, setDecidedCount] = useState(0);

  const workflowAgent = run ? `${run.workflow_id}:${run.agent_name}` : null;
  const artifactId = run?.artifact_id;

  useEffect(() => {
    if (!workflowAgent || !artifactId) return;
    const key = `decisions:${workflowAgent}`;
    if (!claim(key)) return;
    findOpenDecisions(artifactId)
      .then((result) => setDecisions(result.decisions))
      .catch((caught: unknown) => setError(caught instanceof ApiError ? caught.message : 'Savia could not review the document.'))
      .finally(() => release(key));
    // Re-scan only for a different document, not for each new version we save.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workflowAgent]);

  const decision = decisions?.[index] ?? null;
  const choice = selected ?? decision?.leaning ?? null;
  const isLast = decisions !== null && index >= decisions.length - 1;

  const next = () => {
    setSelected(null);
    setError(null);
    if (isLast) navigate('/sharing');
    else setIndex((i) => i + 1);
  };

  const handleChoose = async () => {
    if (!run || !decision || choice === null) return;
    const option = decision.options[choice];
    setWorking(true);
    setError(null);
    try {
      save(await recordDecision(run.artifact_id, decision.question, option.title, option.text));
      setDecidedCount((n) => n + 1);
      next();
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'The decision could not be saved.');
    } finally {
      setWorking(false);
    }
  };

  if (!run) {
    return (
      <Section id="decide" title="Open decisions" size="compact">
        <Card panel className={styles.panel}>
          <div className={styles.block}>
            <p>There is no agent output to review yet. Run an agent from the recommendations first.</p>
          </div>
          <div className={styles.footer}>
            <div className={styles.footerActions}>
              <Button variant="primary" onClick={() => navigate('/reading')}>
                Back to recommendations
              </Button>
            </div>
          </div>
        </Card>
      </Section>
    );
  }

  return (
    <Section
      id="decide"
      title={decisions?.length === 0 ? 'Nothing is left open' : `${label} will not decide this one for you`}
      size="compact"
      subtitle="Savia looks for decisions your input leaves open. Pick an option and it records it in the document as a new version."
      aside={
        decisions && decisions.length > 0 ? (
          <StatusPill tone="alert" dot>
            Your turn · decision {index + 1} of {decisions.length}
          </StatusPill>
        ) : undefined
      }
    >
      <Card panel className={styles.panel}>
        {decisions === null && !error && (
          <div className={styles.block}>
            <p className={styles.openNote}>
              <Spinner label="Reviewing" /> Savia is reading the document for decisions that are still open…
            </p>
          </div>
        )}

        {decisions?.length === 0 && (
          <div className={styles.block}>
            <p className={styles.openNote}>
              Savia found no open decisions in this output{decidedCount ? ' after the ones you just made' : ''}. You can move
              on to sharing it.
            </p>
          </div>
        )}

        {decision && (
          <>
            <div className={styles.block}>
              <h2 className={styles.label}>The open question</h2>
              <div className={styles.section}>
                <div className={styles.sectionHead}>
                  <span className={styles.sectionNum}>{index + 1}</span>
                  <h3 className={styles.sectionTitle}>{decision.question}</h3>
                </div>
                <p className={styles.openNote}>
                  {decision.evidence && <>From your input: &ldquo;{decision.evidence}&rdquo;. </>}
                  Choosing records it with the document&rsquo;s decisions and resolves the question.
                </p>
              </div>
            </div>

            <div className={`${styles.block} ${styles.divider}`}>
              <h2 className={`${styles.label} ${styles.labelRed}`}>The two options Savia found</h2>
              <ul className={styles.options}>
                {decision.options.map((option, i) => {
                  const isSelected = choice === i;
                  const leans = decision.leaning === i;
                  return (
                    <li key={option.title}>
                      <button
                        type="button"
                        aria-pressed={isSelected}
                        className={`${styles.option} ${leans ? styles.optionLeaning : ''} ${
                          isSelected ? styles.optionSelected : ''
                        } ${styles.optionClickable} ${styles.optionButton}`}
                        onClick={() => setSelected(i)}
                      >
                        <span className={styles.optionHead}>
                          <span className={styles.optionTitle}>{option.title}</span>
                          {isSelected ? (
                            <span className={styles.selectedBadge}>&#10003; Selected{leans ? ' · your input leans here' : ''}</span>
                          ) : leans ? (
                            <span className={styles.leans}>
                              <span className={styles.leansDot} aria-hidden="true" />
                              Your input leans here
                            </span>
                          ) : null}
                        </span>
                        <span className={styles.optionText}>
                          {option.text}
                        </span>
                        {option.cost && (
                          <span className={`${styles.cost} ${leans || isSelected ? styles.costLeaning : ''}`}>
                            Trade-off: {option.cost}
                          </span>
                        )}
                      </button>
                    </li>
                  );
                })}
              </ul>
              {decision.leaning !== null && decision.leaning_reason && (
                <p className={styles.openNote}>Why it leans: {decision.leaning_reason}</p>
              )}
            </div>
          </>
        )}

        {error && (
          <div className={styles.block}>
            <p className={styles.openNote} role="alert">
              {error}
            </p>
          </div>
        )}

        <div className={styles.footer}>
          <div>
            <h2 className={styles.footerTitle}>
              {decision && choice !== null
                ? `Choose ${decision.options[choice].title}`
                : decision
                  ? 'Pick an option'
                  : decisions === null && !error
                    ? 'Reviewing the document…'
                    : 'Ready to share'}
            </h2>
            <p className={styles.footerBody}>
              {decision
                ? 'Or leave it open: the question stays in the document for someone else to decide.'
                : decisions === null && !error
                  ? 'Savia is checking for decisions that are still open.'
                  : `${decidedCount} decision${decidedCount === 1 ? '' : 's'} recorded in this session.`}
            </p>
          </div>
          <div className={styles.footerActions}>
            {decision ? (
              <>
                <Button variant="primary" onClick={handleChoose} disabled={choice === null || working}>
                  {working ? 'Recording…' : 'Choose this and update the document'}
                </Button>
                <Button onClick={next} disabled={working}>
                  Leave it open
                </Button>
              </>
            ) : (
              <Button variant="primary" onClick={() => navigate('/sharing')} disabled={decisions === null && !error}>
                Continue to sharing
              </Button>
            )}
            <Button onClick={() => navigate('/document')}>Back to document</Button>
          </div>
        </div>
      </Card>
    </Section>
  );
}
