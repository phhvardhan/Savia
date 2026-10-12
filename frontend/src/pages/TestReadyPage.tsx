import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Section } from '../components/ui/Section';
import styles from './TestReadyPage.module.css';

const NEEDS = [
  {
    id: 'bus',
    label: 'BUS Jira IDs',
    value: 'JGFY-2812 · JGFY-5303 · JGFY-8052',
    source: 'From the approved design',
  },
  { id: 'release', label: 'Release', value: 'TIME · Release 2.1', source: 'From the project' },
  { id: 'cycle', label: 'Test cycle', value: 'SIT', source: 'The cycle this release is in' },
  {
    id: 'personas',
    label: 'Personas',
    value: '4 incl. Finance Master Data Maintainer',
    source: 'From the design and the stories',
  },
];

const PRODUCES = [
  {
    id: 'inventory',
    title: 'Test case inventory',
    text: 'One row per case, mapped to the criterion it covers',
    note: 'Type, persona, release, AC reference',
  },
  {
    id: 'cases',
    title: 'Manual test cases',
    text: 'Preconditions, steps, expected results',
    note: 'Ready for SIT execution',
  },
  {
    id: 'coverage',
    title: 'A coverage statement',
    text: 'Which criteria are covered and which are not',
    note: 'The part people skip today',
    point: true,
  },
];

export function TestReadyPage() {
  const navigate = useNavigate();

  return (
    <Section
      id="test-ready"
      title="TEST already has what it needs"
      size="compact"
      subtitle="It asks for four things before it will run. All four came from the approved design. Nothing was typed and nothing was asked of you."
      aside={<p className={styles.readyPill}>Ready to run</p>}
    >
      <Card panel className={styles.panel}>
        <div className={styles.block}>
          <h2 className={styles.label}>The four things TEST insists on</h2>
          <ul className={styles.needs}>
            {NEEDS.map((need) => (
              <li key={need.id} className={styles.need}>
                <div className={styles.needHead}>
                  <span className={styles.needLabel}>{need.label}</span>
                  <span className={styles.haveIt}>Have it</span>
                </div>
                <p className={styles.needValue}>{need.value}</p>
                <p className={styles.needSource}>{need.source}</p>
              </li>
            ))}
          </ul>
        </div>

        <div className={`${styles.block} ${styles.divider}`}>
          <h2 className={styles.label}>What it will produce</h2>
          <ul className={styles.produces}>
            {PRODUCES.map((item) => (
              <li key={item.id} className={styles.produce}>
                <div className={styles.produceHead}>
                  <h3 className={styles.produceTitle}>{item.title}</h3>
                  {item.point && (
                    <span className={styles.thePoint}>
                      <span className={styles.pointDot} aria-hidden="true" />
                      The point
                    </span>
                  )}
                </div>
                <p className={styles.produceText}>{item.text}</p>
                <p className={styles.produceNote}>
                  <span aria-hidden="true">·</span>
                  <span>{item.note}</span>
                </p>
              </li>
            ))}
          </ul>
        </div>

        <div className={styles.actions}>
          <Button variant="primary" onClick={() => navigate('/test-writing')}>
            Let it run
          </Button>
          <Button>Change the cycle or personas</Button>
        </div>
      </Card>
    </Section>
  );
}
