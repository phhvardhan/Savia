import { Fragment } from 'react';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { DataTable } from '../components/ui/DataTable';
import { Section } from '../components/ui/Section';
import styles from './StudioPage.module.css';

interface Pattern {
  id: string;
  title: string;
  steps: string[];
  meta: string;
  usage: string;
  featured?: boolean;
}

const PATTERNS: Pattern[] = [
  {
    id: 'stories-design-tests',
    title: 'Approved stories → design → tests',
    steps: ['DDL3', 'TEST'],
    meta: '2 approvals · ~25 min',
    usage: 'Run 14 times · used by 3 teams',
    featured: true,
  },
  {
    id: 'workshop-minutes-stories',
    title: 'Workshop → minutes → stories',
    steps: ['MoM', 'BUS/TUS'],
    meta: '1 approval · ~12 min',
    usage: 'Run 31 times · the most used pattern here',
  },
  {
    id: 'design-dab',
    title: 'Design → DAB dossier',
    steps: ['DDL3', 'KDD'],
    meta: '1 approval · ~18 min',
    usage: 'Run 4 times · built by you',
  },
];

const REMEMBERS = [
  ['The agents and their order', 'DDL3 writes the design, then TEST builds the cases', 'Yes — drop or add one'],
  ['Who approves each step', 'Design Lead, then Test Lead', 'Yes — pick someone else'],
  ['The template', 'J&J RICEFW design specification', 'Rarely — it is the approved one'],
  ['Where the output goes', 'Confluence, then Jira', 'Yes — choose destinations'],
  ['What it needs from you', 'One input, and two approvals', 'No — that is the pattern'],
];

export function StudioPage() {
  return (
    <Section
      id="studio"
      title="The sequences your team runs again and again"
      subtitle="A pattern is a run you have already proved the agents, the order, the approvers and the destinations. Start one and SAVIA only asks for the input."
    >
      <Card panel className={styles.panel}>
        <div className={styles.block}>
          <h2 className={styles.label}>Start from a pattern</h2>
          <ul className={styles.patterns}>
            {PATTERNS.map((pattern) => (
              <li
                key={pattern.id}
                className={`${styles.pattern} ${pattern.featured ? styles.patternFeatured : ''}`}
              >
                <h3 className={styles.patternTitle}>{pattern.title}</h3>
                <p className={styles.chips}>
                  {pattern.steps.map((step, index) => (
                    <Fragment key={step}>
                      {index > 0 && (
                        <span className={styles.arrow} aria-hidden="true">
                          →
                        </span>
                      )}
                      <span className={styles.chip}>{step}</span>
                    </Fragment>
                  ))}
                </p>
                <p className={styles.patternMeta}>{pattern.meta}</p>
                <p className={styles.patternUsage}>{pattern.usage}</p>
                <div className={styles.patternActions}>
                  <Button variant={pattern.featured ? 'onRed' : 'secondary'} small>
                    Start this
                  </Button>
                  <Button variant={pattern.featured ? 'ghostOnRed' : 'secondary'} small>
                    What it does
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        </div>

        <div className={styles.tableBlock}>
          <h2 className={styles.label}>What a pattern remembers for you</h2>
        </div>
        <DataTable
          caption="The parts of a pattern that are fixed, and the parts you can change per run"
          columns={[
            { key: 'fixes', label: 'What it fixes', width: '28%' },
            { key: 'pattern', label: 'For this pattern' },
            { key: 'change', label: 'Change it per run?', width: '26%' },
          ]}
          rows={REMEMBERS.map(([fixes, forPattern, change]) => ({
            id: fixes,
            cells: [fixes, forPattern, change],
          }))}
        />

        <div className={styles.footer}>
          <div className={styles.footerText}>
            <h2 className={styles.footerTitle}>Start “approved stories → design → tests”</h2>
            <p className={styles.footerBody}>
              It will ask you for the stories and nothing else. Two approvals, both yours to give or to route
              elsewhere.
            </p>
          </div>
          <div className={styles.footerActions}>
            <Button variant="primary">Start this pattern</Button>
            <Button>Build a new pattern</Button>
          </div>
        </div>
      </Card>
    </Section>
  );
}
