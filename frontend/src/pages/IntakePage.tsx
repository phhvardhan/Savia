import { useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Section } from '../components/ui/Section';
import { DocumentIcon, RecordingIcon } from '../components/ui/Icons';
import {
  ACCEPTED_FILES,
  MEDIA_EXTENSIONS,
  addFiles,
  attachmentFromFiles,
  formatBytes,
  useAttachment,
} from '../state/attachment';
import styles from './IntakePage.module.css';

/** The backend reads at most this many files in one upload. */
const MAX_FILES = 10;

const SOURCES = [
  { id: 'document', title: 'A Document', text: 'BRD, functional spec, workshop output', accent: styles.accentInk },
  { id: 'recording', title: 'A Recording', text: 'Workshop, walkthrough, refinement call', accent: styles.accentBlue },
  { id: 'jira', title: 'A Jira Key', text: 'Savia pulls the story and its criteria', accent: styles.accentAmber },
  { id: 'project', title: 'From the Project', text: 'Something already approved on this release', accent: styles.accentPurple },
];

const isMedia = (file: File) =>
  /^(audio|video)\//.test(file.type) || MEDIA_EXTENSIONS.some((ext) => file.name.toLowerCase().endsWith(ext));

const fileType = (file: File) => file.name.split('.').pop()?.toUpperCase() ?? 'File';

/** Screen 02: check what you attached, add or remove files, then let Savia read it. */
export function IntakePage() {
  const navigate = useNavigate();
  const { attachment, setAttachment } = useAttachment();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dropped, setDropped] = useState(0);

  const files = attachment?.files ?? [];
  // Mixed uploads light up both cards.
  const chosen = new Set<string>(files.map((f) => (isMedia(f) ? 'recording' : 'document')));

  function handleFilesChosen(event: React.ChangeEvent<HTMLInputElement>) {
    const picked = Array.from(event.target.files ?? []);
    event.target.value = ''; // re-picking the same file still fires a change event
    if (!picked.length) return;
    const next = addFiles(attachment, picked);
    setDropped(Math.max(0, next.files.length - MAX_FILES));
    setAttachment(next.files.length > MAX_FILES ? attachmentFromFiles(next.files.slice(0, MAX_FILES)) : next);
  }

  function remove(index: number) {
    const rest = files.filter((_, i) => i !== index);
    setDropped(0);
    setAttachment(rest.length ? attachmentFromFiles(rest) : null);
  }

  return (
    <Section
      id="intake"
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
                  {chosen.has(source.id) && (
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
          {files.length ? (
            <>
              <ul className={styles.files}>
                {files.map((file, index) => (
                  <li key={`${file.name}:${file.size}:${file.lastModified}`} className={styles.attachment}>
                    <span className={styles.thumbIcon} aria-hidden="true">
                      {isMedia(file) ? <RecordingIcon /> : <DocumentIcon />}
                    </span>
                    <div className={styles.attachmentText}>
                      <p className={styles.fileName}>{file.name}</p>
                      <p className={styles.fileMeta}>
                        {formatBytes(file.size)} · {fileType(file)} · added by you, just now
                      </p>
                    </div>
                    <p className={styles.ready}>Ready to read</p>
                    <button type="button" className={styles.remove} aria-label={`Remove ${file.name}`} onClick={() => remove(index)}>
                      Remove
                    </button>
                  </li>
                ))}
              </ul>
              <p className={styles.count}>
                {files.length} of {MAX_FILES} files · Savia reads them together as one input.
                {dropped > 0 && (
                  <span className={styles.limit}> {dropped} file{dropped === 1 ? ' was' : 's were'} not added: the limit is {MAX_FILES}.</span>
                )}
              </p>
            </>
          ) : (
            <p className={styles.empty}>
              Nothing attached yet. Use <strong>Add another file</strong> below, or go back to{' '}
              <Link to="/work">Work</Link> to describe what you need.
            </p>
          )}
        </div>

        <div className={styles.actions}>
          <Button variant="primary" disabled={!files.length} onClick={() => navigate('/reading')}>
            Let Savia read it
          </Button>
          <Button disabled={files.length >= MAX_FILES} onClick={() => fileInputRef.current?.click()}>
            Add another file
          </Button>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="visually-hidden"
            accept={ACCEPTED_FILES}
            onChange={handleFilesChosen}
          />
        </div>
      </Card>
    </Section>
  );
}
