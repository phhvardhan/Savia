import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { DataTable } from '../components/ui/DataTable';
import { Section } from '../components/ui/Section';
import { StatGrid } from '../components/ui/StatGrid';
import { StatusPill } from '../components/ui/StatusPill';
import styles from './ApprovePage.module.css';

const APPROVING = [
  { value: '62', caption: 'test cases', hint: 'SIT · Release 2.1', tone: 'blue' as const, tintCaption: true },
  { value: '18 of 20', caption: 'criteria covered', hint: '2 accepted with a reason', tone: 'green' as const, tintCaption: true },
  { value: '4', caption: 'personas', hint: 'all from the approved design', tone: 'orange' as const, tintCaption: true },
  { value: '3', caption: 'cases you edited', hint: 'kept as yours', tone: 'red' as const, tintCaption: true },
];

const TARGETS = [
  {
    id: 'jira',
    logo: '/assets/jira.png',
    title: 'Jira · OTC board',
    text: 'Created as test issues under each story',
    state: 'Chosen',
    chosen: true,
  },
  {
    id: 'tms',
    logo: '/assets/docc.png',
    title: 'Test management tool',
    text: 'As a SIT cycle with all 62 cases',
    state: 'Also available',
  },
  {
    id: 'excel',
    logo: '/assets/excel.png',
    title: 'Excel workbook',
    text: 'The same format your team downloads today',
    state: 'Also available',
  },
];

const RUNNERS = [
  { id: 'requestor', persona: 'Requestor · Trade Supplier', cases: '18', assigned: 'M. Pieretti', due: '26 Sept' },
  { id: 'finance', persona: 'Finance Master Data Maintainer', cases: '22', assigned: 'R. Kumar', due: '26 Sept' },
  { id: 'display', persona: 'GS Finance Display', cases: '12', assigned: 'Unassigned', due: '—' },
  { id: 'warehouse', persona: 'Warehouse Operator · Inbound', cases: '10', assigned: 'D. Tomar', due: '27 Sept' },
];

export function ApprovePage() {
  const navigate = useNavigate();

  return (
    <Section
      id="approve"
      title="Approve it and send it where it belongs"
      size="compact"
      titleClassName={styles.titleRed}
      subtitle="Your approval is what lets these cases leave Savia. Choose where they go and who runs them."
      aside={
        <StatusPill tone="alert" dot>
          Your turn · Test Lead
        </StatusPill>
      }
    >
      <Card panel className={styles.panel}>
        <StatGrid label="What you are approving" labelTone="ink" stats={APPROVING} />

        <div className={`${styles.block} ${styles.divider}`}>
          <h2 className={styles.label}>Where they go</h2>
          <ul className={styles.targets}>
            {TARGETS.map((target) => (
              <li
                key={target.id}
                className={`${styles.target} ${target.chosen ? styles.targetChosen : ''}`}
              >
                <div className={styles.targetHead}>
                  <img className={styles.logo} src={target.logo} alt="" />
                  <h3 className={styles.targetTitle}>{target.title}</h3>
                </div>
                <p className={styles.targetText}>{target.text}</p>
                <p
                  className={`${styles.targetState} ${target.chosen ? styles.stateChosen : styles.stateAlso}`}
                >
                  {target.chosen && <span className={styles.stateDot} aria-hidden="true" />}
                  {target.state}
                </p>
              </li>
            ))}
          </ul>
        </div>

        <div className={`${styles.block} ${styles.divider}`}>
          <h2 className={styles.label}>Who runs them</h2>
        </div>
        <DataTable
          caption="How the cases are split between personas and who runs each set"
          columns={[
            { key: 'persona', label: 'Persona' },
            { key: 'cases', label: 'Cases', width: '12%' },
            { key: 'assigned', label: 'Assigned to', width: '22%' },
            { key: 'due', label: 'Due', width: '16%' },
          ]}
          rows={RUNNERS.map((row) => ({
            id: row.id,
            cells: [
              row.persona,
              <span key="cases" className={styles.cases}>{row.cases}</span>,
              row.assigned,
              row.due,
            ],
          }))}
        />

        <div className={styles.footer}>
          <div>
            <h2 className={styles.footerTitle}>Approve and push 62 cases to Jira</h2>
            <p className={styles.footerBody}>
              One persona is still unassigned you can approve now and assign later, or assign first.
            </p>
          </div>
          <div className={styles.footerActions}>
            <Button variant="primary" onClick={() => navigate('/execution')}>
              Approve and push
            </Button>
            <Button>Assign the last 12 first</Button>
          </div>
        </div>
      </Card>
    </Section>
  );
}
