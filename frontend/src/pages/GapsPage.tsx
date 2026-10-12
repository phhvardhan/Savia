import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Section } from '../components/ui/Section';
import { StatGrid } from '../components/ui/StatGrid';
import { StatusPill } from '../components/ui/StatusPill';
import styles from './GapsPage.module.css';

const COSTS = [
  { value: '~2 days', caption: 'to send both back', hint: 'and re-run those two criteria', tone: 'red' as const },
  { value: '20 of 20', caption: 'coverage if you do', hint: 'nothing left open', tone: 'green' as const },
  { value: '18 of 20', caption: 'if you accept them', hint: 'both gaps on the record', tone: 'orange' as const },
  { value: '0', caption: 'cases wasted either way', hint: 'the other 62 stand' },
];

export function GapsPage() {
  const navigate = useNavigate();
  return (
    <Section
      id="gaps"
      title="Two criteria have no test"
      size="compact"
      subtitle="Savia will not invent an expected result to make the number look better. Decide what happens to each one."
      aside={
        <StatusPill tone="alert" dot>
          Your turn · Test Lead
        </StatusPill>
      }
    >
      <Card panel className={styles.panel}>
        <div className={styles.block}>
          <h2 className={styles.label}>Gap 1 of 2</h2>
          <article className={`${styles.gap} ${styles.gapOpen}`}>
            <div className={styles.gapHead}>
              <h3 className={styles.gapTitle}>AC-002 · &ldquo;Consolidation Unit derives correctly&rdquo;</h3>
              <span className={styles.gapState}>
                <span className={styles.gapDot} aria-hidden="true" />
                No expected result
              </span>
            </div>
            <p className={styles.gapText}>
              The criterion says what should happen but not what the tester should see. There is nothing to assert
              against, so a case written here would pass whatever the system did.
            </p>
            <div className={styles.gapActions}>
              <Button variant="primary">Send it back to the BA</Button>
              <Button>Accept the gap with a reason</Button>
              <Button>Write the expected result myself</Button>
            </div>
          </article>
        </div>

        <div className={`${styles.block} ${styles.divider}`}>
          <h2 className={styles.label}>Gap 2 of 2</h2>
          <article className={styles.gap}>
            <div className={styles.gapHead}>
              <h3 className={styles.gapTitle}>AC-001 · &ldquo;Derivation runs on every ledger&rdquo;</h3>
              <span className={styles.partial}>Partly covered</span>
            </div>
            <p className={styles.gapText}>
              Twelve cases cover the main ledger. The rest depends on the derivation rule left open in section 5 of
              the design until that is settled, the remaining ledgers cannot be written.
            </p>
            <div className={styles.gapActions}>
              <Button variant="primary">Close the design decision first</Button>
              <Button>Accept partial coverage</Button>
            </div>
          </article>
        </div>

        <div className={styles.statsBorder}>
          <StatGrid label="What each route costs" labelTone="ink" stats={COSTS} />
        </div>

        <div className={styles.footer}>
          <div>
            <h2 className={styles.footerTitle}>Send both back to the Business Analyst</h2>
            <p className={styles.footerBody}>
              Savia will re-run only these two criteria when they come back. The other 62 cases are untouched.
            </p>
          </div>
          <div className={styles.footerActions}>
            <Button variant="primary" onClick={() => navigate('/approve')}>
              Send both back
            </Button>
            <Button onClick={() => navigate('/approve')}>Accept and move on</Button>
          </div>
        </div>
      </Card>
    </Section>
  );
}
