import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Section } from '../components/ui/Section';
import { StatGrid } from '../components/ui/StatGrid';
import { PLATFORMS } from '../lib/platforms';
import { AGENT_META, agentMeta, downloadArtifact, documentFormat, getNextAgent, sectionText } from '../lib/savia';
import type { NextAgentDecision, UploadResult } from '../lib/savia';
import { useAttachment } from '../state/attachment';
import { resetOnce } from '../lib/once';
import { useRun, useCurrentRun } from '../state/run';
import styles from './PublishPage.module.css';

const MAX_ITERATIONS = 2;

type Destination = 'confluence' | 'next' | 'jira' | 'sharepoint' | 'word' | 'teams';

export function PublishPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { resetAll, upload, setRun, agentRuns, selectAgent, startAgentRun } = useRun();
  const { setAttachment } = useAttachment();
  const { agentId, run } = useCurrentRun();
  const meta = agentId ? AGENT_META[agentId] : undefined;
  const approvedBy = (location.state as { approvedBy?: string } | null)?.approvedBy;
  const [published, setPublished] = useState(false);
  const [choosing, setChoosing] = useState(false);
  const [on, setOn] = useState<Record<Destination, boolean>>({
    confluence: true, next: true, jira: true, sharepoint: false, word: false, teams: false,
  });
  const [decision, setDecision] = useState<NextAgentDecision | null>(null);
  const [readFor, setReadFor] = useState<string | null>(null); // the output the orchestrator has finished reading

  // Two iterations only: the second one's publish page offers no third.
  const done = new Set(
    Object.keys(agentRuns).filter((k) => k.endsWith(`:${upload?.workflow_id}`)).map((k) => k.split(':')[0]),
  );
  const iteration = Math.max(1, done.size);
  const canIterate = iteration < MAX_ITERATIONS;

  // The orchestrator reads the generated document and names the agent that takes it next.
  const docText = run ? sectionText(run.content) : '';
  const runId = run?.artifact_id;
  const workflowId = upload?.workflow_id;
  useEffect(() => {
    if (!canIterate || !runId || !workflowId) return;
    let cancelled = false;
    getNextAgent(workflowId, runId)
      .then((d) => !cancelled && setDecision(d))
      .catch(() => !cancelled && setDecision(null)) // no decision: the page just offers no next agent
      .finally(() => !cancelled && setReadFor(runId));
    return () => {
      cancelled = true;
    };
  }, [runId, workflowId, canIterate]);

  const reading = canIterate && Boolean(runId) && readFor !== runId;
  const nextRec = decision?.agent ? decision.recommendation : null;
  const next = nextRec?.recommended_agents.find((a) => a.agent === decision?.agent) ?? null;
  const nextMeta = next ? agentMeta(next) : null;

  // Screen 11 comes after the approval on screen 10, never before it.
  if (!run || !meta || !approvedBy) {
    return (
      <Section id="publish" title="Approve it before you publish" size="compact">
        <Card panel className={styles.panel}>
          <div className={styles.actions}>
            <Button variant="primary" onClick={() => navigate(run ? '/sharing' : '/work')}>
              {run ? 'Go to the approval' : 'Start a run'}
            </Button>
          </div>
        </Card>
      </Section>
    );
  }

  const mainFile = documentFormat(agentId);
  const toggle = (id: Destination) => setOn((current) => ({ ...current, [id]: !current[id] }));
  const startIteration2 = () => {
    if (!next || !nextRec || !upload) return;
    // The generated document becomes the new input file; the workflow stays so the agent can use the approved output.
    const filename = `${meta.label} output · v${run.version}`;
    const input: UploadResult = {
      ...upload,
      filename,
      input_type: 'doc',
      metadata: {
        ...upload.metadata,
        filename,
        input_type: 'doc',
        character_count: docText.length,
        word_count: docText.split(/\s+/).filter(Boolean).length,
        file_size_bytes: new Blob([docText]).size,
      },
      full_normalized_text: docText,
    };
    setRun(input, nextRec);
    selectAgent(next.agent);
    startAgentRun(next.agent, input, run.artifact_id);
    navigate('/writing');
  };
  const wordLogo = mainFile.fmt === 'pptx' ? PLATFORMS.powerpoint : PLATFORMS.word;

  const toggleButton = (id: Destination, red?: boolean) => (
    <button
      type="button"
      aria-pressed={on[id]}
      aria-label={`${on[id] ? 'Turn off' : 'Turn on'} ${id}`}
      className={`${styles.toggle} ${on[id] ? (red ? styles.toggleRed : styles.toggleBlue) : styles.toggleOff}`}
      onClick={() => toggle(id)}
    >
      {on[id] ? 'On' : 'Off'}
    </button>
  );

  const platformRows: Array<{ id: Destination; platform: { name: string; logo: string; url: string }; title: string; note: string }> = [
    {
      id: 'confluence',
      platform: PLATFORMS.confluence,
      title: `CONFLUENCE · ${meta.full}`,
      note: 'Publishes the approved version as a page, with the approval record attached and a link back to this workspace',
    },
    {
      id: 'jira',
      platform: PLATFORMS.jira,
      title: 'JIRA · linked stories',
      note: `Updates the stories linked to this run with a link to the approved ${meta.label}${nextMeta ? ` and moves them to Ready for ${nextMeta.label}` : ''}`,
    },
  ];

  const outcome = [
    { value: on.confluence ? '1' : '0', caption: published ? 'page created' : 'page will be created', hint: 'Confluence', tone: 'red' as const },
    { value: on.jira ? '1' : '0', caption: published ? 'Jira link added' : 'Jira link will be added', hint: 'on the linked stories', tone: 'red' as const },
    canIterate
      ? {
          value: on.next && next ? '1' : '0',
          caption: published ? 'agent ready' : 'agent will start',
          hint: reading ? 'reading the document…' : nextMeta ? `${nextMeta.label}, with this document as its input` : 'no other agent suggested',
          tone: 'red' as const,
        }
      : { value: `${MAX_ITERATIONS} of ${MAX_ITERATIONS}`, caption: 'iterations complete', hint: 'the run is finished', tone: 'red' as const },
    { value: `v${run.version}`, caption: 'version published', hint: approvedBy === 'You' ? 'approved by you' : `approved by the ${approvedBy}`, tone: 'red' as const },
  ];

  const open = (url: string) => (
    <a className={styles.openLink} href={url} target="_blank" rel="noopener noreferrer">
      Open ↗
    </a>
  );

  const renderRow = (item: (typeof platformRows)[number]) => (
    <li key={item.id} className={styles.destination}>
      <a className={styles.logoLink} href={item.platform.url} target="_blank" rel="noopener noreferrer" aria-label={`Open ${item.platform.name}`}>
        <img className={styles.logoImg} src={item.platform.logo} alt="" />
      </a>
      <div className={styles.destinationText}>
        <h3 className={`${styles.destinationTitle} ${styles.titleBlue}`}>{item.title}</h3>
        <p className={styles.destinationNote}>{item.note}</p>
      </div>
      <div className={styles.destinationEnd}>
        {published && on[item.id] && open(item.platform.url)}
        <span className={`${styles.recommended} ${styles.recommendedBlue}`}>
          <span className={styles.recommendedDot} aria-hidden="true" />
          Recommended
        </span>
        {toggleButton(item.id)}
      </div>
    </li>
  );

  return (
    <Section
      id="publish"
      title={
        published
          ? `Published. ${canIterate ? 'Iteration 1 is complete.' : 'Both iterations are complete.'}`
          : 'Approved. Now send it where it belongs.'
      }
      size="compact"
      subtitle={`Iteration ${iteration} of ${MAX_ITERATIONS} · ${meta.full} · version ${run.version}. Each destination says exactly what will be created.`}
      aside={
        <div className={styles.pills}>
          <p className={styles.approvedPill}>Approved by {approvedBy}</p>
          {run.readiness && (
            <p
              className={`${styles.approvedPill} ${run.readiness.ready ? '' : styles.pillWarn}`}
              title={run.readiness.issues.join('\n') || 'Every check passed'}
            >
              Readiness {Math.round(run.readiness.score * 100)}%
              {run.readiness.ready ? ' · ready' : ` · ${run.readiness.issues.length} to review`}
            </p>
          )}
        </div>
      }
    >
      <Card panel className={styles.panel}>
        <div className={styles.block}>
          <h2 className={styles.label}>Recommended · do all three</h2>
          <ul className={styles.destinations}>
            {renderRow(platformRows[0])}

            {canIterate && reading && !next && (
              <li className={`${styles.destination} ${styles.destinationNext}`}>
                <span className={styles.logoLink}>
                  <img className={styles.logoImg} src="/assets/docc.png" alt="" />
                </span>
                <div className={styles.destinationText}>
                  <h3 className={`${styles.destinationTitle} ${styles.titleRed}`}>The Next Agent</h3>
                  <p className={styles.destinationNote}>Reading the generated document to suggest the best next agent…</p>
                </div>
              </li>
            )}

            {next && nextMeta && (
              <li className={`${styles.destination} ${styles.destinationNext}`}>
                <span className={styles.logoLink}>
                  <img className={styles.logoImg} src="/assets/docc.png" alt="" />
                </span>
                <div className={styles.destinationText}>
                  <h3 className={`${styles.destinationTitle} ${styles.titleRed}`}>
                    {nextMeta.label.toUpperCase()} · The Next Agent
                  </h3>
                  <p className={styles.destinationNote}>
                    Takes the generated {meta.label} document as its input, with everything it carries (criteria, decisions,
                    personas, systems), so {nextMeta.label} can start without you retyping anything
                  </p>
                </div>
                <div className={styles.destinationEnd}>
                  <span className={`${styles.recommended} ${styles.recommendedRed}`}>
                    <span className={styles.recommendedDot} aria-hidden="true" />
                    Recommended
                  </span>
                  {toggleButton('next', true)}
                </div>
              </li>
            )}

            {renderRow(platformRows[1])}
          </ul>
          <p className={styles.footnote}>
            Confluence and Jira are not connected yet: these open the platform, and the approved {mainFile.label} file is
            the copy to share until they are.
          </p>
        </div>

        <div className={`${styles.block} ${styles.divider}`}>
          <h2 className={styles.label}>Also available</h2>
          <ul className={styles.alsoGrid}>
            <li className={styles.also}>
              <div className={styles.alsoHead}>
                <a className={styles.alsoLink} href={PLATFORMS.sharepoint.url} target="_blank" rel="noopener noreferrer">
                  <img className={styles.alsoLogoImg} src={PLATFORMS.sharepoint.logo} alt="" />
                  <h3 className={styles.alsoTitle}>SharePoint ↗</h3>
                </a>
                {choosing && toggleButton('sharepoint')}
              </div>
              <p className={styles.alsoText}>If your team keeps signed specifications there instead</p>
            </li>
            <li className={styles.also}>
              <div className={styles.alsoHead}>
                <button
                  type="button"
                  className={styles.alsoLink}
                  onClick={() => void downloadArtifact(run.artifact_id, mainFile.fmt).catch((e: Error) => window.alert(e.message))}
                >
                  <img className={styles.alsoLogoImg} src={wordLogo.logo} alt="" />
                  <h3 className={styles.alsoTitle}>{mainFile.label} download</h3>
                </button>
                {choosing && toggleButton('word')}
              </div>
              <p className={styles.alsoText}>The J&amp;J cover page and template are kept</p>
            </li>
            <li className={styles.also}>
              <div className={styles.alsoHead}>
                <a className={styles.alsoLink} href={PLATFORMS.teams.url} target="_blank" rel="noopener noreferrer">
                  <img className={styles.alsoLogoImg} src={PLATFORMS.teams.logo} alt="" />
                  <h3 className={styles.alsoTitle}>Teams message ↗</h3>
                </a>
                {choosing && toggleButton('teams')}
              </div>
              <p className={styles.alsoText}>A link and a two-line summary to a channel you choose</p>
            </li>
          </ul>
        </div>

        <div className={styles.statsBorder}>
          <StatGrid label={published ? 'What was published' : 'What will happen when you press publish'} labelTone="ink" stats={outcome} />
        </div>

        {published && canIterate && (
          <div className={`${styles.block} ${styles.iteration}`}>
            <h2 className={styles.label}>Iteration 2</h2>
            {next && nextMeta && on.next ? (
              <p className={styles.iterationText}>
                <strong>{nextMeta.label}</strong> is ready to take the generated {meta.label} document as its input
                {decision?.reason ? `. ${decision.reason}` : '.'}
              </p>
            ) : (
              <p className={styles.iterationText}>
                {next ? 'The next agent was turned off for this hand-off.' : 'SAVIA has no other agent to suggest for this input.'}
              </p>
            )}
          </div>
        )}

        <div className={styles.actions}>
          {published ? (
            <>
              {next && on.next && (
                <Button variant="primary" onClick={startIteration2}>
                  Start iteration 2 with {nextMeta?.label}
                </Button>
              )}
              <Button
                variant={next && on.next ? undefined : 'primary'}
                onClick={() => {
                  resetAll();
                  setAttachment(null);
                  resetOnce();
                  navigate('/work');
                }}
              >
                Start a new run
              </Button>
            </>
          ) : (
            <>
              <Button variant="primary" onClick={() => setPublished(true)}>
                Publish and hand off
              </Button>
              <Button onClick={() => setChoosing((c) => !c)}>{choosing ? 'Done choosing' : 'Choose destinations'}</Button>
            </>
          )}
          <Button onClick={() => navigate('/document')}>Back to the document</Button>
        </div>
      </Card>
    </Section>
  );
}
