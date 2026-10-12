import { useNavigate } from 'react-router-dom';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { DataTable } from '../components/ui/DataTable';
import { Section } from '../components/ui/Section';
import { StatGrid } from '../components/ui/StatGrid';
import { StatusPill } from '../components/ui/StatusPill';
import styles from './ProjectsPage.module.css';

const RUN_ROWS = [
  {
    id: 'mom',
    agent: 'MoM',
    did: 'Read the workshop recording, wrote the minutes',
    passed: '6 decisions, 8 actions',
    state: <Badge tone="solidGreen">Done</Badge>,
  },
  {
    id: 'bus',
    agent: 'BUS / TUS',
    did: 'Wrote 12 user stories with acceptance criteria',
    passed: '12 stories, 38 criteria',
    state: <Badge tone="solidGreen">Done</Badge>,
  },
  {
    id: 'ddl3',
    agent: 'DDL3',
    did: 'Wrote the functional design on the J&J template',
    passed: 'Design v1, 4 decisions',
    state: <Badge tone="solidGreen">Approved</Badge>,
  },
  {
    id: 'test',
    agent: 'TEST',
    did: 'Writing SIT cases from the approved design',
    passed: '62 cases, coverage 18 of 20',
    state: (
      <Badge tone="needsYou" dot>
        Needs you
      </Badge>
    ),
  },
  {
    id: 'change',
    agent: 'Change Impact',
    did: 'Checking what else this release touches in parallel',
    passed: '3 downstream systems so far',
    state: (
      <Badge tone="running" dot>
        Running
      </Badge>
    ),
  },
  {
    id: 'cutover',
    agent: 'Cutover',
    did: 'Has not started it needs test results first',
    passed: '—',
    state: <Badge tone="waiting">Waiting</Badge>,
  },
];

const RUN_STATS = [
  { value: '6', caption: 'agents involved', hint: '4 done, 2 running' },
  { value: '3', caption: 'approvals given', hint: 'all named and dated' },
  { value: '1', caption: 'approval waiting', hint: 'TEST coverage, with you', tone: 'red' as const },
  { value: '~31 hrs', caption: 'of manual work replaced', hint: 'across the whole run' },
];

function HumanNode({ label, name }: { label: string; name: string }) {
  return (
    <div className={styles.human}>
      <span className={styles.humanLabel}>{label}</span>
      <span className={styles.humanName}>{name}</span>
    </div>
  );
}

export function ProjectsPage() {
  const navigate = useNavigate();
  return (
    <Section
      id="run"
      title="The whole run on one screen"
      titleClassName={styles.pageTitle}
      subtitle={
        <>
          Which agent is active, what each one did, where a person had to decide, and what is waiting.
          <br />
          Nothing about this run is hidden behind a log.
        </>
      }
      aside={
        <StatusPill tone="alert" dot>
          1 agent running · 1 waiting on you
        </StatusPill>
      }
    >
      <Card panel className={styles.panel}>
        <div className={styles.flow}>
          <div className={styles.board}>
            <p className={`${styles.zone} ${styles.zoneDone}`}>Done</p>
            <p className={`${styles.zone} ${styles.zoneRunning}`}>Running now</p>
            <p className={`${styles.zone} ${styles.zoneWaiting}`}>Waiting</p>

            {/* Row of human decisions sitting above the agents */}
            <div className={styles.above} />
            <div className={styles.above} />
            <div className={styles.above} />
            <div className={styles.above}>
              <HumanNode label="Human" name="Approval due" />
              <span className={styles.stem} aria-hidden="true" />
            </div>
            <div className={styles.above} />

            {/* The agents themselves */}
            <div className={styles.node}>
              <article className={`${styles.card} ${styles.cardDone}`}>
                <h3 className={`${styles.cardTitle} ${styles.inkTitle}`}>MoM</h3>
                <p className={styles.cardBadge}>
                  <span className={styles.doneChip}>Done</span>
                </p>
                <p className={styles.cardMeta}>Minutes and actions</p>
                <span className={styles.link} aria-hidden="true" />
              </article>
            </div>
            <div className={styles.node}>
              <article className={`${styles.card} ${styles.cardDone}`}>
                <h3 className={`${styles.cardTitle} ${styles.inkTitle}`}>BUS / TUS</h3>
                <p className={styles.cardBadge}>
                  <span className={styles.doneChip}>Done</span>
                </p>
                <p className={styles.cardMeta}>12 user stories</p>
                <span className={styles.link} aria-hidden="true" />
              </article>
            </div>
            <div className={styles.node}>
              <article className={`${styles.card} ${styles.cardDone}`}>
                <h3 className={`${styles.cardTitle} ${styles.inkTitle}`}>DDL3</h3>
                <p className={styles.cardBadge}>
                  <span className={styles.doneChip}>Done</span>
                </p>
                <p className={styles.cardMeta}>Functional design v1</p>
                <span className={styles.link} aria-hidden="true" />
              </article>
            </div>
            <div className={styles.node}>
              <article className={`${styles.card} ${styles.cardRunning}`}>
                <h3 className={styles.cardTitle}>TEST</h3>
                <p className={styles.cardBadge}>
                  <span className={styles.pillWhite}>
                    <span className={styles.pillDot} aria-hidden="true" />
                    Running
                  </span>
                </p>
                <p className={styles.cardMeta}>62 cases, 18 of 20</p>
                <span className={`${styles.link} ${styles.linkDashed}`} aria-hidden="true" />
              </article>
            </div>
            <div className={styles.node}>
              <article className={`${styles.card} ${styles.cardIdle}`}>
                <h3 className={`${styles.cardTitle} ${styles.inkTitle}`}>Cutover</h3>
                <p className={styles.cardMeta}>Needs test results</p>
              </article>
            </div>

            {/* Human decisions and the parallel branch below the agents */}
            <div className={styles.below} />
            <div className={styles.below}>
              <span className={styles.stem} aria-hidden="true" />
              <HumanNode label="Human" name="You approved" />
            </div>
            <div className={styles.below}>
              <span className={styles.stem} aria-hidden="true" />
              <HumanNode label="Human" name="D. Blanco approved" />
            </div>
            <div className={styles.below}>
              <span className={styles.stem} aria-hidden="true" />
              <article className={styles.branch}>
                <h3 className={styles.branchTitle}>Change Impact</h3>
                <p className={styles.branchBadge}>
                  <Badge tone="runningSoft" dot>
                    Running
                  </Badge>
                </p>
                <p className={styles.branchMeta}>Running alongside TEST</p>
              </article>
            </div>
            <div className={styles.below} />
          </div>
        </div>

        <DataTable
          caption="Every agent in this run, what it did and its current state"
          columns={[
            { key: 'agent', label: 'Agent', width: '17%' },
            { key: 'did', label: 'What it did' },
            { key: 'passed', label: 'What it passed on', width: '22%' },
            { key: 'state', label: 'State', width: '14%' },
          ]}
          rows={RUN_ROWS.map((row) => ({
            id: row.id,
            cells: [row.agent, row.did, row.passed, row.state],
          }))}
        />

        <StatGrid label="This run so far" stats={RUN_STATS} />

        <div className={styles.actions}>
          <Button variant="primary" onClick={() => navigate('/help')}>
            Go to the approval
          </Button>
          <Button onClick={() => navigate('/stale')}>See the full history</Button>
        </div>
      </Card>
    </Section>
  );
}
