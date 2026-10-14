import { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Section } from '../components/ui/Section';
import { StatGrid } from '../components/ui/StatGrid';
import { Spinner } from '../components/ui/Spinner';
import { useCurrentRun } from '../state/run';
import { ApiError } from '../lib/api';
import { claim, release } from '../lib/once';
import { applyEdit, sectionText, sectionTitle, suggestEdit, type EditSuggestion } from '../lib/savia';
import styles from './SuggestionsPage.module.css';

export function SuggestionsPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { run, save } = useCurrentRun();
  const { section = '', instruction = '' } = (location.state as { section?: string; instruction?: string } | null) ?? {};

  const [suggestion, setSuggestion] = useState<EditSuggestion | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [applying, setApplying] = useState(false);

  // The version you asked about. Fixed at mount: accepting saves a newer
  // version, and that must not trigger a second draft for it.
  const [artifactId] = useState(() => run?.artifact_id);

  // One AI draft per (version, section, instruction). Released once it lands so
  // a later visit can ask again; StrictMode's immediate remount is skipped.
  useEffect(() => {
    if (!artifactId || !section || !instruction) return;
    const key = `suggest:${artifactId}:${section}:${instruction}`;
    if (!claim(key)) return;
    suggestEdit(artifactId, section, instruction)
      .then(setSuggestion)
      .catch((caught: unknown) => setError(caught instanceof ApiError ? caught.message : 'Savia could not draft the change.'))
      .finally(() => release(key));
  }, [artifactId, section, instruction]);

  const handleAccept = async () => {
    if (!artifactId || !suggestion) return;
    setApplying(true);
    try {
      save(await applyEdit(artifactId, section, suggestion.revised));
      navigate('/decide');
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'The change could not be saved.');
      setApplying(false);
    }
  };

  if (!run || !section || !instruction) {
    return (
      <Section id="suggestions" title="SAVIA suggests changes for review" size="compact">
        <Card panel className={styles.panel}>
          <div className={styles.block}>
            <p>Nothing to review yet. Pick a section and tell Savia what to change first.</p>
          </div>
          <div className={styles.footer}>
            <div className={styles.footerActions}>
              <Button variant="primary" onClick={() => navigate('/change')}>
                Choose what to change
              </Button>
            </div>
          </div>
        </Card>
      </Section>
    );
  }

  const unchanged = suggestion !== null && JSON.stringify(suggestion.revised) === JSON.stringify(suggestion.original);
  const needsInfo = suggestion?.needs_info ?? [];
  const unsupported = suggestion?.unsupported_claims ?? [];

  return (
    <Section
      id="suggestions"
      title="SAVIA suggests changes for review"
      size="compact"
      subtitle="Accept the change and it is saved as a new version, or discard it and the section stays exactly as it was."
    >
      <Card panel className={styles.panel}>
        <header className={styles.head}>
          <p className={styles.instruction}>&ldquo;{instruction}&rdquo;</p>
          <div className={styles.headActions}>
            <span className={styles.countBadge}>{sectionTitle(section)}</span>
          </div>
        </header>

        <div className={styles.block}>
          <h2 className={styles.label}>What it wants to change</h2>

          {error && <p className={`${styles.body} ${styles.bodyRemoved}`}>{error}</p>}

          {!error && !suggestion && (
            <p className={styles.body}>
              <Spinner label="Drafting" /> Savia is drafting the change, grounded in your input…
            </p>
          )}

          {suggestion && needsInfo.length > 0 && (
            <section className={styles.change}>
              <div className={styles.changeHead}>
                <div className={styles.changeLabel}>
                  <span className={styles.changeNum}>?</span>
                  <h3 className={styles.changeTitle}>Savia needs this before it can make the change</h3>
                </div>
              </div>
              <p className={`${styles.body} ${styles.bodyKept}`} style={{ whiteSpace: 'pre-wrap' }}>
                {needsInfo.map((q) => `• ${q}`).join('\n')}
                {'\n\n'}It is not in your input, so Savia left the section unchanged rather than guess.
              </p>
            </section>
          )}

          {suggestion && needsInfo.length === 0 && (
            <>
              {suggestion.summary && <p className={styles.body}>{suggestion.summary}</p>}
              <section className={styles.change}>
                <div className={styles.changeHead}>
                  <div className={styles.changeLabel}>
                    <span className={styles.changeNum}>1</span>
                    <h3 className={styles.changeTitle}>Now</h3>
                  </div>
                </div>
                <p className={`${styles.body} ${styles.bodyRemoved}`} style={{ whiteSpace: 'pre-wrap' }}>
                  {sectionText(suggestion.original)}
                </p>
              </section>
              <section className={styles.change}>
                <div className={styles.changeHead}>
                  <div className={styles.changeLabel}>
                    <span className={styles.changeNum}>2</span>
                    <h3 className={styles.changeTitle}>{unchanged ? 'No change needed' : 'Savia’s revision'}</h3>
                  </div>
                </div>
                <p className={`${styles.body} ${styles.bodyAdded}`} style={{ whiteSpace: 'pre-wrap' }}>
                  {sectionText(suggestion.revised)}
                </p>
              </section>
              {unsupported.length > 0 && (
                <section className={styles.change}>
                  <div className={styles.changeHead}>
                    <div className={styles.changeLabel}>
                      <span className={styles.changeNum}>!</span>
                      <h3 className={styles.changeTitle}>Check these: not found in your input</h3>
                    </div>
                  </div>
                  <p className={`${styles.body} ${styles.bodyKept}`} style={{ whiteSpace: 'pre-wrap' }}>
                    {unsupported.map((c) => `• ${c}`).join('\n')}
                  </p>
                </section>
              )}
            </>
          )}
        </div>

        {suggestion && needsInfo.length === 0 && (
          <div className={styles.statsBorder}>
            <StatGrid
              label="What this changes"
              labelTone="ink"
              stats={[
                { value: '1', caption: 'section changed', hint: sectionTitle(section), tone: 'red' as const },
                { value: '0', caption: 'other sections touched', hint: 'only this section is sent back', tone: 'green' as const },
                {
                  value: String(unsupported.length),
                  caption: 'statements to check',
                  hint: unsupported.length ? 'not found in your input' : 'all found in your input',
                  tone: unsupported.length ? ('red' as const) : ('green' as const),
                },
                { value: `v${run.version + 1}`, caption: 'saved as', hint: `v${run.version} stays in history`, tone: 'blue' as const },
              ]}
            />
          </div>
        )}

        <div className={styles.footer}>
          <div>
            <h2 className={styles.footerTitle}>
              {needsInfo.length ? 'Answer these, then ask again' : 'Accept and move on to open decisions'}
            </h2>
            <p className={styles.footerBody}>
              You can still edit the result by hand on the document, and every earlier version is kept.
            </p>
          </div>
          <div className={styles.footerActions}>
            {needsInfo.length === 0 && (
              <Button variant="primary" onClick={handleAccept} disabled={!suggestion || unchanged || applying}>
                {applying ? 'Saving…' : 'Accept and continue →'}
              </Button>
            )}
            <Button onClick={() => navigate('/change', { state: { section } })}>Change the instruction</Button>
            <Button onClick={() => navigate('/document')}>Discard</Button>
          </div>
        </div>
      </Card>
    </Section>
  );
}
