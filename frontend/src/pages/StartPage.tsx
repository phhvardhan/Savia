import { useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Section } from '../components/ui/Section';
import { DocumentIcon, RecordingIcon } from '../components/ui/Icons';
import {
  ACCEPTED_FILES,
  attachmentFromFile,
  formatBytes,
  useAttachment,
} from '../state/attachment';
import styles from './StartPage.module.css';

interface Source {
  id: string;
  title: string;
  text: string;
  accent: string;
  chosen?: boolean;
}

const SOURCES: Source[] = [
  {
    id: 'document',
    title: 'A Document',
    text: 'BRD, functional spec, workshop output',
    accent: styles.accentInk,
  },
  {
    id: 'recording',
    title: 'A Recording',
    text: 'Workshop, walkthrough, refinement call',
    accent: styles.accentBlue,
  },
  {
    id: 'jira',
    title: 'A Jira Key',
    text: 'Savia pulls the story and its criteria',
    accent: styles.accentAmber,
  },
  {
    id: 'project',
    title: 'From the Project',
    text: 'Something already approved on this release',
    accent: styles.accentPurple,
  },
];

export function StartPage() {
  const navigate = useNavigate();
  const { attachment, setAttachment } = useAttachment();
  const fileInputRef = useRef<HTMLInputElement>(null);

  function handleFileChosen(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;

    // One attachment at a time — picking again replaces what is there.
    setAttachment(attachmentFromFile(file));

    // Reset so re-picking the same file still fires a change event.
    event.target.value = '';
  }

  // The source card that matches whatever came off the home finder.
  const chosenSource = attachment ? attachment.kind : null;

  return (
    <Section
      id="start"
      title="Start with what you have"
      size="compact"
      subtitle="Drop a document, a recording or a Jira key. Savia reads it and works out which part of the lifecycle it belongs to."
    >
      <Card panel className={styles.panel}>
        <div className={styles.block}>
          <h2 className={styles.label}>What you can give it</h2>
          <ul className={styles.sources}>
            {SOURCES.map((source) => (
              <li key={source.id} className={`${styles.source} ${source.accent}`}>
                <div className={styles.sourceHead}>
                  <h3 className={styles.sourceTitle}>{source.title}</h3>
                  {(source.chosen || source.id === chosenSource) && (
                    <span className={styles.chosen}>
                      <span className={styles.chosenDot} aria-hidden="true" />
                      Chosen
                    </span>
                  )}
                </div>
                <p className={styles.sourceText}>{source.text}</p>
              </li>
            ))}
          </ul>
        </div>

        <div className={`${styles.block} ${styles.divider}`}>
          <h2 className={styles.label}>What you attached</h2>
          {attachment ? (
            <div className={styles.attachment}>
              <span className={styles.thumbIcon} aria-hidden="true">
                {attachment.kind === 'recording' ? <RecordingIcon /> : <DocumentIcon />}
              </span>
              <div className={styles.attachmentText}>
                <p className={styles.fileName}>{attachment.name}</p>
                <p className={styles.fileMeta}>
                  {formatBytes(attachment.size)} · {attachment.kind} · added by you, just now
                </p>
              </div>
              <p className={styles.ready}>Ready to read</p>
            </div>
          ) : (
            <p className={styles.empty}>
              Nothing attached yet. Go back to <Link to="/work">Work</Link> and attach a document or
              recording with the upload button.
            </p>
          )}
        </div>

        <div className={styles.actions}>
          <Button variant="primary" disabled={!attachment} onClick={() => navigate('/reading')}>
            Let Savia read it
          </Button>
          <Button onClick={() => fileInputRef.current?.click()}>Add another file</Button>
          <input
            ref={fileInputRef}
            type="file"
            className="visually-hidden"
            accept={ACCEPTED_FILES}
            onChange={handleFileChosen}
          />
        </div>
      </Card>
    </Section>
  );
}
