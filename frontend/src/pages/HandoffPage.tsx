import { useNavigate } from 'react-router-dom';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Section } from '../components/ui/Section';
import { StatusPill } from '../components/ui/StatusPill';
import { StatGrid } from '../components/ui/StatGrid';
import styles from './HandoffPage.module.css';

const CROSSED = [
  'RICEFW FIN-0002 · Release 2.1',
  '2 approved user stories',
  '6 acceptance criteria',
  '4 design decisions, including section 5',
  '4 systems in scope',
  'Approved by D. Blanco, 21 Sept',
];

const SAVED = [
  { value: '0', caption: 'fields retyped', hint: 'TEST asked you for nothing' },
  { value: '6', caption: 'criteria carried through', hint: 'the same ones TEST will cover' },
  { value: '1', caption: 'approval recorded', hint: 'named, dated, on version 1' },
  { value: '~3 hrs', caption: 'saved on this handoff', hint: 'against the manual route', tone: 'red' as const },
];

export function HandoffPage() {
  const navigate = useNavigate();

  return (
    <Section
      id="handoff"
      title="Approved and TEST already has it"
      size="compact"
      subtitle="D. Blanco approved version 1. The approved design and everything it carries were handed to TEST automatically."
      aside={<StatusPill tone="done">Handed off</StatusPill>}
    >
      <Card panel className={styles.panel}>
        <div className={styles.board}>
          <p className={`${styles.columnLabel} ${styles.labelGave}`}>What was approved</p>
          <p className={`${styles.columnLabel} ${styles.labelWorking}`}>What crossed over</p>
          <p className={`${styles.columnLabel} ${styles.labelRecommends}`}>Who picked it up</p>

          <div className={styles.gave}>
            <article className={styles.inputCard}>
              <div className={styles.inputHead}>
                <h3 className={styles.inputTitle}>Functional design v1</h3>
                <Badge tone="solidGreen">Approved</Badge>
              </div>
              <p className={styles.inputMeta}>TIME_L3_FIN_FI_E_CODE_BLOCK_EXTENSION</p>
              <ul className={styles.inputList}>
                {['Approved by D. Blanco', '21 Sept, 14:06'].map((item) => (
                  <li key={item} className={styles.inputItem}>
                    <span className={styles.bullet} aria-hidden="true">·</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </article>

            <article className={styles.inputCard}>
              <div className={styles.inputHead}>
                <h3 className={styles.inputTitle}>Published to Confluence</h3>
                <Badge tone="solidGreen">Done</Badge>
              </div>
              <p className={styles.inputMeta}>Design Specifications · Release 2.1</p>
            </article>
          </div>

          <svg
            className={`${styles.connector} ${styles.connectorLeft}`}
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
            aria-hidden="true"
          >
            <path d="M0 25 C 45 25, 55 42, 100 42" fill="none" stroke="#C3C4C5" strokeWidth="0.7" />
            <path d="M0 75 C 45 75, 55 55, 100 55" fill="none" stroke="#C3C4C5" strokeWidth="0.7" />
          </svg>

          <section className={styles.orchestrator} aria-label="What crossed over">
            <div className={styles.orchestratorHead}>
              <h3 className={styles.orchestratorName}>Context packet</h3>
              <p className={styles.orchestratorState}>DDL3 → TEST</p>
            </div>
            {CROSSED.map((item) => (
              <p key={item} className={styles.crossed}>
                <span className={styles.crossedDot} aria-hidden="true">·</span>
                <span>{item}</span>
              </p>
            ))}
          </section>

          <svg
            className={`${styles.connector} ${styles.connectorRight}`}
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
            aria-hidden="true"
          >
            <path d="M0 45 C 50 45, 50 25, 100 25" fill="none" stroke="#49A032" strokeWidth="0.9" />
            <path
              d="M0 55 C 50 55, 50 72, 100 72"
              fill="none"
              stroke="#C3C4C5"
              strokeWidth="0.7"
              strokeDasharray="3 3"
            />
          </svg>

          <ul className={styles.recommends}>
            <li className={`${styles.recommend} ${styles.recommendChosen}`}>
              <div className={styles.outputHead}>
                <h3 className={styles.outputTitle}>TEST</h3>
                <span className={styles.runningPill}>
                  <span className={styles.stateDot} aria-hidden="true" />
                  Running
                </span>
              </div>
              <p className={styles.recommendText}>Started on its own, 4 min ago</p>
            </li>
            <li className={styles.recommend}>
              <div className={styles.outputHead}>
                <h3 className={styles.outputTitle}>Cutover</h3>
              </div>
              <p className={styles.recommendText}>Waits for test results</p>
            </li>
          </ul>
        </div>

        <div className={styles.statsBorder}>
          <StatGrid label="What this saved you" stats={SAVED} />
        </div>

        <div className={styles.footer}>
          <div>
            <h2 className={styles.footerTitle}>TEST is already building the inventory</h2>
            <p className={styles.footerBody}>
              You will be asked once more to approve the coverage before anything is pushed to Jira.
            </p>
          </div>
          <div className={styles.footerActions}>
            <Button variant="primary" onClick={() => navigate('/test-ready')}>
              Watch TEST run
            </Button>
            <Button>See exactly what was passed</Button>
          </div>
        </div>
      </Card>
    </Section>
  );
}
