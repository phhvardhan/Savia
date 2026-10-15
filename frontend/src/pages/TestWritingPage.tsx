import { useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { FanConnector } from '../components/ui/FanConnector';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Section } from '../components/ui/Section';
import { StatusPill } from '../components/ui/StatusPill';
import { StatGrid } from '../components/ui/StatGrid';
import styles from './TestWritingPage.module.css';

type StepState = 'Done' | 'Writing' | 'Next';

const STEPS: Array<{ id: string; title: string; state: StepState; note?: string }> = [
  { id: 'read', title: 'Read the design and criteria', state: 'Done' },
  { id: 'inventory', title: 'Build the inventory', state: 'Done', note: '62 cases across 4 personas' },
  { id: 'steps', title: 'Write the steps', state: 'Writing', note: 'AC-001 on JGFY-8052' },
  { id: 'coverage', title: 'Check coverage', state: 'Next' },
  { id: 'automation', title: 'Suggest automation', state: 'Next' },
];

const OUTPUTS = [
  {
    id: 'inventory',
    title: 'Test case inventory',
    state: 'Built',
    text: '62 rows, mapped to criteria',
  },
  {
    id: 'coverage',
    title: 'Coverage statement',
    text: 'Where the gaps are',
    muted: true,
  },
];

const PROGRESS = [
  { value: '62', caption: 'test cases written', hint: 'across 4 personas', hintTone: 'red' as const },
  { value: '4 of 6', caption: 'criteria fully covered', hint: 'steps and expected results', tone: 'blue' as const, hintTone: 'red' as const },
  { value: '1', caption: 'criterion partly covered', hint: 'AC-001 on JGFY-8052', tone: 'orange' as const, hintTone: 'red' as const },
  { value: '1', caption: 'criterion it cannot cover', hint: 'AC-002 — no expected result', tone: 'red' as const, hintTone: 'red' as const },
];

export function TestWritingPage() {
  const navigate = useNavigate();
  const gaveRef = useRef<HTMLDivElement>(null);
  const hubRef = useRef<HTMLElement>(null);
  const recommendsRef = useRef<HTMLUListElement>(null);

  return (
    <Section
      id="test-writing"
      title="TEST is writing the cases"
      size="compact"
      subtitle="It works criterion by criterion. You can see which ones it has covered and which it is struggling with, while it runs."
      aside={
        <StatusPill tone="running" dot pulse>
          Working · about 3 minutes left
        </StatusPill>
      }
    >
      <Card panel className={styles.panel}>
        <div className={styles.board}>
          <p className={`${styles.columnLabel} ${styles.labelGave}`}>What it received</p>
          <p className={`${styles.columnLabel} ${styles.labelWorking}`}>TEST</p>
          <p className={`${styles.columnLabel} ${styles.labelRecommends}`}>What it will produce</p>

          <div ref={gaveRef} className={styles.gave}>
            <article className={styles.inputCard}>
              <div className={styles.inputHead}>
                <h3 className={styles.inputTitle}>Approved design v1</h3>
                <Badge tone="solidGreen">Received</Badge>
              </div>
              <p className={styles.inputMeta}>Approved by D. Blanco, 21 Sept</p>
              <ul className={styles.inputList}>
                {['4 design decisions', '6 acceptance criteria'].map((item) => (
                  <li key={item} className={styles.inputItem}>
                    <span className={styles.bullet} aria-hidden="true">·</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </article>

            <article className={styles.inputCard}>
              <div className={styles.inputHead}>
                <h3 className={styles.inputTitle}>4 personas</h3>
                <Badge tone="waiting">Loaded</Badge>
              </div>
              <p className={styles.inputMeta}>Finance Master Data Maintainer and 3 others</p>
            </article>
          </div>

          <FanConnector
            className={`${styles.connector} ${styles.connectorLeft}`}
            cards={gaveRef}
            cardSelector=":scope > article"
            hub={hubRef}
            hubSide="right"
            deps={[]}
          />

          <section ref={hubRef} className={styles.orchestrator} aria-label="TEST progress">
            <div className={styles.orchestratorHead}>
              <h3 className={styles.orchestratorName}>TEST</h3>
              <p className={styles.orchestratorState}>Criterion 5 of 6</p>
            </div>
            {STEPS.map((step) => (
              <div key={step.id} className={styles.step}>
                <div className={styles.stepHead}>
                  <h4
                    className={`${styles.stepTitle} ${step.state === 'Next' ? styles.stepTitleNext : ''}`}
                  >
                    {step.title}
                  </h4>
                  <span
                    className={`${styles.statePill} ${
                      step.state === 'Writing'
                        ? styles.stateWriting
                        : step.state === 'Next'
                          ? styles.stateNext
                          : styles.stateDone
                    }`}
                  >
                    {step.state === 'Writing' && <span className={styles.stateDot} aria-hidden="true" />}
                    {step.state}
                  </span>
                </div>
                {step.note && <p className={styles.stepNote}>{step.note}</p>}
              </div>
            ))}
          </section>

          <FanConnector
            className={`${styles.connector} ${styles.connectorRight}`}
            cards={recommendsRef}
            cardSelector=":scope > li"
            hub={hubRef}
            hubSide="left"
            deps={[]}
            line={(i) => (i === 0 ? { stroke: '#EB7D00', strokeWidth: 1.6 } : { strokeDasharray: '3 3' })}
          />

          <ul ref={recommendsRef} className={styles.recommends}>
            {OUTPUTS.map((item) => (
              <li key={item.id} className={styles.recommend}>
                <div className={styles.outputHead}>
                  <h3 className={`${styles.outputTitle} ${item.muted ? styles.outputTitleMuted : ''}`}>
                    {item.title}
                  </h3>
                  {item.state && <span className={styles.outputState}>{item.state}</span>}
                </div>
                <p className={styles.recommendText}>{item.text}</p>
              </li>
            ))}
          </ul>
        </div>

        <div className={styles.statsBorder}>
          <StatGrid label="Where it has got to" labelTone="ink" stats={PROGRESS} />
        </div>

        <div className={styles.footer}>
          <div>
            <h2 className={styles.footerTitle}>Two criteria are going to need you</h2>
            <p className={styles.footerBody}>
              It will finish everything it can first, then show you exactly which two and why.
            </p>
          </div>
          <div className={styles.footerActions}>
            <Button variant="primary" onClick={() => navigate('/coverage')}>
              Show the detailed log
            </Button>
            <Button>Stop the run</Button>
          </div>
        </div>
      </Card>
    </Section>
  );
}
