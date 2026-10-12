import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { DataTable } from '../components/ui/DataTable';
import { Section } from '../components/ui/Section';
import { StatGrid } from '../components/ui/StatGrid';
import styles from './ExecutionPage.module.css';

const PROGRESS = [
  { value: '41', caption: 'passed', hint: 'of 62 executed', tone: 'green' as const },
  { value: '1', caption: 'failed', hint: 'TC-14 · Category Code validation', tone: 'red' as const },
  { value: '20', caption: 'not started', hint: 'assigned, due 27 Sept' },
  { value: '0', caption: 'blocked', hint: 'nothing waiting on the platform' },
];

type Verdict = 'Correct' | 'Gap here' | 'Consequence';

const TRACE: Array<{ id: string; step: string; says: string; verdict: Verdict }> = [
  {
    id: 'case',
    step: 'The test case',
    says: 'Steps and expected result match the criterion',
    verdict: 'Correct',
  },
  {
    id: 'criterion',
    step: 'AC-002 on JGFY-2812',
    says: '“Values outside the list must be rejected” — unambiguous',
    verdict: 'Correct',
  },
  {
    id: 'design',
    step: 'Section 4 of the design',
    says: 'Names the allowed values table but not where validation runs',
    verdict: 'Gap here',
  },
  {
    id: 'build',
    step: 'The build',
    says: 'Validation was implemented on the UI only, not on posting',
    verdict: 'Consequence',
  },
];

const VERDICT_CLASS: Record<Verdict, string> = {
  Correct: styles.verdictCorrect,
  'Gap here': styles.verdictGap,
  Consequence: styles.verdictConsequence,
};

export function ExecutionPage() {
  const navigate = useNavigate();
  return (
    <Section
      id="execution"
      title="62 cases in Jira. One has failed."
      size="compact"
      subtitle="Execution is tracked here as well as in Jira. The failure has been traced back to the thing that caused it, so it goes to the right person first time."
    >
      <Card panel className={styles.panel}>
        <StatGrid label="Where SIT has got to" labelTone="ink" stats={PROGRESS} />

        <div className={`${styles.block} ${styles.divider}`}>
          <h2 className={styles.label}>The failure</h2>
          <article className={styles.failure}>
            <div className={styles.failureHead}>
              <h3 className={styles.failureTitle}>
                TC-14 · Category Code is accepted outside the allowed list
              </h3>
              <span className={styles.failedPill}>
                <span className={styles.failedDot} aria-hidden="true" />
                Failed
              </span>
            </div>
            <p className={styles.failureText}>
              Expected: the posting is rejected with a validation message. Actual: the posting completed. Raised by
              R. Kumar, 25 Sept, with a screenshot attached.
            </p>
          </article>
        </div>

        <div className={`${styles.block} ${styles.divider}`}>
          <h2 className={styles.label}>What Savia traced it back to</h2>
        </div>
        <DataTable
          caption="Each step back from the failure and what it shows"
          columns={[
            { key: 'step', label: 'Step back', width: '30%' },
            { key: 'says', label: 'What it says' },
            { key: 'verdict', label: 'Verdict', width: '18%' },
          ]}
          rows={TRACE.map((row) => ({
            id: row.id,
            cells: [
              row.step,
              row.says,
              <span key="verdict" className={`${styles.verdict} ${VERDICT_CLASS[row.verdict]}`}>
                {row.verdict === 'Gap here' && <span className={styles.failedDot} aria-hidden="true" />}
                {row.verdict}
              </span>,
            ],
          }))}
        />

        <div className={styles.actions}>
          <Button variant="primary" onClick={() => navigate('/projects')}>
            Raise it against the design
          </Button>
          <Button>Raise it as a build defect</Button>
        </div>
      </Card>
    </Section>
  );
}
