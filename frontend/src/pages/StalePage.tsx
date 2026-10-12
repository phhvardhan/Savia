import { useNavigate } from 'react-router-dom';
import { Card } from '../components/ui/Card';
import { DataTable } from '../components/ui/DataTable';
import { Button } from '../components/ui/Button';
import { Section } from '../components/ui/Section';
import { StatGrid } from '../components/ui/StatGrid';
import { StatusPill } from '../components/ui/StatusPill';
import styles from './StalePage.module.css';

type ChangeTone = 'Added' | 'Changed' | 'No impact';

const CHANGES: Array<{ id: string; title: string; text: string; tone: ChangeTone }> = [
  {
    id: 'ac-002',
    title: 'AC-002 on JGFY-8052 now has an expected result',
    text: 'Added “the posting is rejected with message ZFI023”',
    tone: 'Added',
  },
  {
    id: 'category-code',
    title: 'Category Code is now 12 characters, not 10',
    text: 'Changed affects the field design and 6 test cases',
    tone: 'Changed',
  },
  {
    id: 'reporting',
    title: 'The reporting section was reworded',
    text: 'Wording only nothing downstream depends on it',
    tone: 'No impact',
  },
];

const CHANGE_TONE_CLASS: Record<ChangeTone, string> = {
  Added: styles.toneAdded,
  Changed: styles.toneChanged,
  'No impact': styles.toneNone,
};

type AffectedState = 'Stale' | 'Improves' | 'Unaffected' | 'Stale soft';

const AFFECTED: Array<{
  id: string;
  what: string;
  why: string;
  needs: string;
  state: AffectedState;
}> = [
  {
    id: 'design',
    what: 'Functional design v1',
    why: 'Section 4 states a 10-character field',
    needs: 'DDL3 re-runs section 4 only',
    state: 'Stale',
  },
  {
    id: 'six-cases',
    what: '6 test cases',
    why: 'They assert the old field length',
    needs: 'TEST rewrites those 6',
    state: 'Stale',
  },
  {
    id: 'coverage',
    what: 'Coverage · AC-002',
    why: 'It can now be tested it was a gap',
    needs: 'TEST writes 2 new cases',
    state: 'Improves',
  },
  {
    id: 'unaffected',
    what: '56 test cases',
    why: 'Nothing they assert has changed',
    needs: 'Nothing',
    state: 'Unaffected',
  },
  {
    id: 'change-impact',
    what: 'Change Impact result',
    why: 'Field length affects one downstream report',
    needs: 'Re-check one system',
    state: 'Stale soft',
  },
];

const STATE_CLASS: Record<AffectedState, string> = {
  Stale: styles.stateStale,
  Improves: styles.stateImproves,
  Unaffected: styles.stateUnaffected,
  'Stale soft': styles.stateStaleSoft,
};

const SCALE = [
  { value: '3', caption: 'things stale', hint: 'out of 9 downstream items', tone: 'red' as const },
  { value: '56 of 62', caption: 'cases unaffected', hint: 'they stay approved', tone: 'green' as const },
  { value: '2', caption: 'new cases possible', hint: 'AC-002 can now be covered', tone: 'green' as const },
  { value: '~25 min', caption: 'to bring it all up to date', hint: 'if you refresh now', tone: 'red' as const },
];

export function StalePage() {
  const navigate = useNavigate();

  return (
    <Section
      id="stale"
      title="The BRD changed. Here is what that breaks."
      size="compact"
      subtitle="R. Kumar updated the source document an hour ago. SAVIA compared it to what was approved and worked out exactly which downstream work is now out of date."
      aside={
        <StatusPill tone="alert" dot>
          3 things are now stale
        </StatusPill>
      }
    >
      <Card panel className={styles.panel}>
        <div className={styles.block}>
          <h2 className={styles.label}>What actually changed</h2>
          <ul className={styles.changes}>
            {CHANGES.map((change) => (
              <li key={change.id} className={styles.change}>
                <div>
                  <h3 className={styles.changeTitle}>{change.title}</h3>
                  <p className={styles.changeText}>{change.text}</p>
                </div>
                <span className={`${styles.changePill} ${CHANGE_TONE_CLASS[change.tone]}`}>
                  {change.tone === 'Changed' && <span className={styles.pillDot} aria-hidden="true" />}
                  {change.tone}
                </span>
              </li>
            ))}
          </ul>
        </div>

        <DataTable
          caption="Each downstream item, why the change touches it and what it needs"
          minWidth={900}
          columns={[
            { key: 'what', label: 'What is affected', width: '22%' },
            { key: 'why', label: 'Why', width: '26%' },
            { key: 'needs', label: 'What it needs', width: '24%' },
            { key: 'state', label: 'State', width: '14%' },
          ]}
          rows={AFFECTED.map((row) => ({
            id: row.id,
            cells: [
              row.what,
              row.why,
              row.needs,
              <span key="state" className={`${styles.statePill} ${STATE_CLASS[row.state]}`}>
                {row.state === 'Stale' && <span className={styles.pillDot} aria-hidden="true" />}
                {row.state === 'Stale soft' ? 'Stale' : row.state}
              </span>,
            ],
          }))}
        />

        <div className={styles.statsBorder}>
          <StatGrid label="The scale of it" stats={SCALE} />
        </div>

        <div className={styles.footer}>
          <Button variant="primary" onClick={() => navigate('/refresh-plan')}>
            Refresh what is stale
          </Button>
          <Button>Ignore for now</Button>
        </div>
      </Card>
    </Section>
  );
}
