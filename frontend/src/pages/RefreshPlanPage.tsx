import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { DataTable } from '../components/ui/DataTable';
import { Section } from '../components/ui/Section';
import { StatGrid } from '../components/ui/StatGrid';
import styles from './RefreshPlanPage.module.css';

type RedoTone = 'rerun' | 'add';

const REDO: Array<{
  id: string;
  title: string;
  pill: string;
  tone: RedoTone;
  body: string;
  items: string[];
}> = [
  {
    id: 'ddl3',
    title: 'DDL3 · section 4 only',
    pill: 'Will re-run',
    tone: 'rerun',
    body: 'Field and table design',
    items: ['~2 min', 'Needs re-approval'],
  },
  {
    id: 'test-6',
    title: 'TEST · 6 cases',
    pill: 'Will re-run',
    tone: 'rerun',
    body: 'The ones that assert field length',
    items: ['~4 min', 'Your edits kept'],
  },
  {
    id: 'test-new',
    title: 'TEST · 2 new cases',
    pill: 'Will add',
    tone: 'add',
    body: 'AC-002 can now be covered',
    items: ['~2 min', 'Coverage goes to 20 of 20'],
  },
];

const REDO_TONE_CLASS: Record<RedoTone, string> = {
  rerun: styles.toneRerun,
  add: styles.toneAdd,
};

type KeptState = 'Kept' | 'Protected';

const KEPT: Array<{ id: string; what: string; why: string; state: KeptState }> = [
  {
    id: 'sections',
    what: 'Sections 1, 2, 3, 5, 6, 7',
    why: 'Nothing in the change touches them',
    state: 'Kept',
  },
  {
    id: 'approval',
    what: "D. Blanco's approval",
    why: 'It applies to the sections that did not change',
    state: 'Kept',
  },
  {
    id: 'cases',
    what: '56 test cases',
    why: 'Already assigned, 41 already passed in SIT',
    state: 'Kept',
  },
  {
    id: 'edits',
    what: 'Your 3 edited cases',
    why: 'Savia writes around your edits, it does not overwrite them',
    state: 'Protected',
  },
  {
    id: 'decision',
    what: 'The section 5 decision',
    why: 'Your derivation choice stands it was not affected',
    state: 'Kept',
  },
];

const KEPT_STATE_CLASS: Record<KeptState, string> = {
  Kept: styles.stateKept,
  Protected: styles.stateProtected,
};

const APPROVALS = [
  { value: '1', caption: 'section to re-approve', hint: 'section 4, by D. Blanco', tone: 'red' as const },
  { value: '1', caption: 'coverage approval', hint: 'after the 8 cases change' },
  { value: '0', caption: 'approvals lost', hint: 'the rest stand', tone: 'green' as const },
  { value: '~25 min', caption: 'end to end', hint: 'including both approvals', tone: 'red' as const },
];

export function RefreshPlanPage() {
  const navigate = useNavigate();

  return (
    <Section
      id="refresh-plan"
      title="What Savia will redo, and what it will keep"
      size="compact"
      subtitle="A refresh is not a re-run. Approvals, your edits and everything unaffected carry forward. Only the stale parts are rebuilt."
    >
      <Card panel className={styles.panel}>
        <div className={styles.block}>
          <h2 className={styles.labelDark}>What will be redone</h2>
          <ul className={styles.redoGrid}>
            {REDO.map((item) => (
              <li key={item.id} className={`${styles.redoCard} ${REDO_TONE_CLASS[item.tone]}`}>
                <div className={styles.redoHead}>
                  <h3 className={styles.redoTitle}>{item.title}</h3>
                  <span className={styles.redoPill}>
                    <span className={styles.pillDot} aria-hidden="true" />
                    {item.pill}
                  </span>
                </div>
                <p className={styles.redoBody}>{item.body}</p>
                <ul className={styles.redoList}>
                  {item.items.map((line) => (
                    <li key={line} className={styles.redoItem}>
                      <span className={styles.bullet} aria-hidden="true">·</span>
                      <span>{line}</span>
                    </li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        </div>

        <div className={`${styles.block} ${styles.divider}`}>
          <h2 className={styles.label}>What carries forward untouched</h2>
        </div>

        <DataTable
          caption="What carries forward untouched, why it is safe to keep, and its state"
          minWidth={900}
          columns={[
            { key: 'what', label: 'What', width: '26%' },
            { key: 'why', label: 'Why it is safe to keep' },
            { key: 'state', label: 'State', width: '14%' },
          ]}
          rows={KEPT.map((row) => ({
            id: row.id,
            cells: [
              row.what,
              row.why,
              <span key="state" className={`${styles.statePill} ${KEPT_STATE_CLASS[row.state]}`}>
                {row.state}
              </span>,
            ],
          }))}
        />

        <div className={styles.statsBorder}>
          <StatGrid label="What will need approving again" labelTone="blue" stats={APPROVALS} />
        </div>

        <div className={styles.footer}>
          <div>
            <h2 className={styles.footerTitle}>Refresh now</h2>
            <p className={styles.footerBody}>
              The 41 cases already executed in SIT are unaffected. Testers running the other cases will not be
              interrupted.
            </p>
          </div>
          <div className={styles.footerActions}>
            <Button variant="primary" onClick={() => navigate('/execution')}>
              Refresh now
            </Button>
            <Button>Schedule it for tonight</Button>
          </div>
        </div>
      </Card>
    </Section>
  );
}
