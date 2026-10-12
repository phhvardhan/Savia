import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Section } from '../components/ui/Section';
import { StatGrid } from '../components/ui/StatGrid';
import styles from './PublishPage.module.css';

const DESTINATIONS = [
  {
    id: 'confluence',
    logo: 'C',
    logoClass: styles.logoBlue,
    title: 'CONFLUENCE · Design Specifications, Release 2.1',
    titleClass: styles.titleBlue,
    note: 'Publishes the approved version as a page, with the approval record attached and a link back to this workspace',
    tone: 'blue' as const,
  },
  {
    id: 'test',
    logo: 'T',
    logoClass: styles.logoRed,
    title: 'TEST · The Next Agent',
    titleClass: styles.titleRed,
    note: 'Hands over the approved design and everything it carries criteria, decisions, personas, systems, so TEST can start without you retyping anything',
    tone: 'red' as const,
  },
  {
    id: 'jira',
    logo: 'J',
    logoClass: styles.logoBlue,
    title: 'JIRA · JGFY-2812, JGFY-5303, JGFY-8052',
    titleClass: styles.titleBlue,
    note: 'Updates the three stories with a link to the approved design and moves them to Ready for Test',
    tone: 'blue' as const,
  },
];

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

const OUTCOME = [
  { value: '1', caption: 'page created', hint: 'Confluence · Release 2.1', tone: 'red' as const },
  { value: '3', caption: 'Jira stories updated', hint: 'linked and moved to Ready for Test', tone: 'red' as const },
  { value: '1', caption: 'agent started', hint: 'TEST, with the approved packet', tone: 'red' as const },
  { value: '1 hour', caption: 'to roll any of it back', hint: 'one action, everything undone', tone: 'red' as const },
];

export function PublishPage() {
  const navigate = useNavigate();

  return (
    <Section
      id="publish"
      title="Approved. Now send it where it belongs."
      size="compact"
      subtitle="Savia proposes the destinations that fit this artefact. Each one says exactly what will be created, and each one can be rolled back."
      aside={<p className={styles.approvedPill}>Approved by D. Blanco</p>}
    >
      <Card panel className={styles.panel}>
        <div className={styles.block}>
          <h2 className={styles.label}>Recommended do all three</h2>
          <ul className={styles.destinations}>
            {DESTINATIONS.map((item) => (
              <li key={item.id} className={styles.destination}>
                <span className={`${styles.logo} ${item.logoClass}`} aria-hidden="true">
                  {item.logo}
                </span>
                <div className={styles.destinationText}>
                  <h3 className={`${styles.destinationTitle} ${item.titleClass}`}>{item.title}</h3>
                  <p className={styles.destinationNote}>{item.note}</p>
                </div>
                <div className={styles.destinationEnd}>
                  <span
                    className={`${styles.recommended} ${
                      item.tone === 'red' ? styles.recommendedRed : styles.recommendedBlue
                    }`}
                  >
                    <span className={styles.recommendedDot} aria-hidden="true" />
                    Recommended
                  </span>
                  <button
                    type="button"
                    aria-pressed="true"
                    className={`${styles.toggle} ${item.tone === 'red' ? styles.toggleRed : styles.toggleBlue}`}
                  >
                    On
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </div>

        <div className={`${styles.block} ${styles.divider}`}>
          <h2 className={styles.label}>Also available</h2>
          <ul className={styles.alsoGrid}>
            {ALSO.map((item) => (
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
          <StatGrid label="What will happen when you press publish" labelTone="ink" stats={OUTCOME} />
        </div>

        <div className={styles.actions}>
          <Button variant="primary" onClick={() => navigate('/handoff')}>
            Publish and hand off
          </Button>
          <Button>Choose destinations</Button>
        </div>
      </Card>
    </Section>
  );
}
