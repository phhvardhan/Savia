import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Section } from '../components/ui/Section';
import { StatGrid } from '../components/ui/StatGrid';
import { AGENT_META, artifactExportUrl, documentFormat } from '../lib/savia';
import { useAttachment } from '../state/attachment';
import { resetOnce } from '../lib/once';
import { useRun, useCurrentRun } from '../state/run';
import styles from './PublishPage.module.css';

const ALSO = [
  {
    id: 'sharepoint',
    logo: 'S',
    logoClass: styles.logoGreen,
    title: 'SharePoint',
    text: 'If your team keeps signed specifications there instead',
  },
  {
    id: 'word',
    logo: 'W',
    logoClass: styles.logoWordBlue,
    title: 'Word download',
    text: 'The J&J cover page and template are kept',
  },
  {
    id: 'teams',
    logo: 'T',
    logoClass: styles.logoPurple,
    title: 'Teams message',
    text: 'A link and a two-line summary to a channel you choose',
  },
];

export function PublishPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { resetAll } = useRun();
  const { setAttachment } = useAttachment();
  const { agentId, run } = useCurrentRun();
  const meta = agentId ? AGENT_META[agentId] : undefined;
  const approvedBy = (location.state as { approvedBy?: string } | null)?.approvedBy;
  const [published, setPublished] = useState(false);

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
  const destinations = [
    {
      id: 'confluence',
      logo: 'C',
      title: `CONFLUENCE · ${meta.full}`,
      note: `Not connected yet: publishing marks the run as published here. Share the ${mainFile.label} file below until it is`,
    },
    {
      id: 'word',
      logo: mainFile.fmt === 'pptx' ? 'P' : 'W',
      title: `${mainFile.label.toUpperCase()} · download the approved version`,
      note:
        mainFile.fmt === 'pptx'
          ? 'A presentation-ready deck of the blueprint, one idea per slide. This one works today'
          : 'The J&J template is kept. This one works today: the file downloads straight away',
    },
  ];
  const outcome = [
    { value: `v${run.version}`, caption: 'version published', hint: 'the one that was approved', tone: 'red' as const },
    { value: '1', caption: 'approval on the record', hint: approvedBy === 'You' ? 'yours' : `by the ${approvedBy}`, tone: 'red' as const },
    { value: '0', caption: 'retyping', hint: 'the output goes as it is', tone: 'red' as const },
  ];

  return (
    <Section
      id="publish"
      title={published ? 'Published. This run is complete.' : 'Approved. Now send it where it belongs.'}
      size="compact"
      subtitle={`${meta.full} · version ${run.version}. Each destination says exactly what will be created.`}
      aside={<p className={styles.approvedPill}>Approved by {approvedBy}</p>}
    >
      <Card panel className={styles.panel}>
        <div className={styles.block}>
          <h2 className={styles.label}>Recommended</h2>
          <ul className={styles.destinations}>
            {destinations.map((item) => (
              <li key={item.id} className={styles.destination}>
                <span className={`${styles.logo} ${styles.logoRed}`} aria-hidden="true">
                  {item.logo}
                </span>
                <div className={styles.destinationText}>
                  <h3 className={`${styles.destinationTitle} ${styles.titleRed}`}>{item.title}</h3>
                  <p className={styles.destinationNote}>{item.note}</p>
                </div>
                <div className={styles.destinationEnd}>
                  {item.id === 'word' ? (
                    <Button small onClick={() => window.location.assign(artifactExportUrl(run.artifact_id, mainFile.fmt))}>
                      Download
                    </Button>
                  ) : (
                    <span className={`${styles.recommended} ${styles.recommendedRed}`}>
                      <span className={styles.recommendedDot} aria-hidden="true" />
                      {published ? 'Published' : 'Recommended'}
                    </span>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>

        <div className={`${styles.block} ${styles.divider}`}>
          <h2 className={styles.label}>Also available</h2>
          <ul className={styles.alsoGrid}>
            {ALSO.filter((item) => item.id !== 'word').map((item) => (
              <li key={item.id} className={styles.also}>
                <div className={styles.alsoHead}>
                  <span className={`${styles.alsoLogo} ${item.logoClass}`} aria-hidden="true">
                    {item.logo}
                  </span>
                  <h3 className={styles.alsoTitle}>{item.title}</h3>
                </div>
                <p className={styles.alsoText}>{item.text}</p>
              </li>
            ))}
          </ul>
        </div>

        <div className={styles.statsBorder}>
          <StatGrid label={published ? 'What was published' : 'What will happen when you press publish'} labelTone="ink" stats={outcome} />
        </div>

        <div className={styles.actions}>
          {published ? (
            <Button
              variant="primary"
              onClick={() => {
                resetAll();
                setAttachment(null);
                resetOnce();
                navigate('/work');
              }}
            >
              Start a new run
            </Button>
          ) : (
            <Button variant="primary" onClick={() => setPublished(true)}>
              Publish and hand off
            </Button>
          )}
          <Button onClick={() => navigate('/document')}>Back to the document</Button>
        </div>
      </Card>
    </Section>
  );
}
