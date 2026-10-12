import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { DataTable } from '../components/ui/DataTable';
import { Section } from '../components/ui/Section';
import { StatGrid } from '../components/ui/StatGrid';
import { StatusPill } from '../components/ui/StatusPill';
import styles from './ReviewsPage.module.css';

const WAITING_ROWS = [
  {
    id: 'you',
    on: 'You · Test Lead',
    what: 'Approve the coverage 18 of 20 criteria',
    blocking: '62 cases cannot reach Jira',
    since: <span className={styles.overdue}>2 hours</span>,
  },
  {
    id: 'kumar',
    on: 'R. Kumar · Business Analyst',
    what: 'An expected result for AC-002 on JGFY-8052',
    blocking: '2 criteria stay uncovered',
    since: <span className={styles.overdue}>3 days · overdue</span>,
  },
  {
    id: 'nobody',
    on: 'Nobody',
    what: 'Change Impact is still running',
    blocking: 'Nothing, Cutover has slack',
    since: '—',
  },
];

const UNBLOCKED = [
  {
    title: '60 of 62 test cases',
    meta: 'Complete, assigned and ready to run',
    badge: <Badge tone="doneSoft">Unaffected</Badge>,
  },
  {
    title: 'The approved design',
    meta: 'Published to Confluence',
    badge: <Badge tone="doneSoft">Unaffected</Badge>,
  },
  {
    title: 'Change Impact',
    meta: 'Running alongside, 3 systems found so far',
    badge: (
      <Badge tone="running" dot>
        Running
      </Badge>
    ),
  },
];

const COST_STATS = [
  { value: '2', caption: 'decisions outstanding', hint: 'one is yours', tone: 'red' as const },
  { value: '3 days', caption: 'the oldest has waited', hint: 'a reminder went out twice', tone: 'red' as const },
  { value: '2', caption: 'criteria uncovered', hint: 'until it is answered', tone: 'orange' as const },
  { value: '0', caption: 'agents stuck', hint: 'the platform is not the bottleneck' },
];

export function ReviewsPage() {
  return (
    <Section
      id="reviews"
      title="Two things are waiting on people"
      subtitle="Savia has done everything it can without a decision. Here is what is stuck, who it is with, and what it is blocking."
      aside={
        <StatusPill tone="alert" dot>
          2 waiting · 1 overdue
        </StatusPill>
      }
    >
      <Card panel className={styles.panel}>
        <DataTable
          caption="Decisions that are currently waiting on a person"
          columns={[
            { key: 'on', label: 'Waiting on', width: '24%' },
            { key: 'what', label: 'What for' },
            { key: 'blocking', label: 'Blocking', width: '22%' },
            { key: 'since', label: 'Since', width: '15%' },
          ]}
          rows={WAITING_ROWS.map((row) => ({
            id: row.id,
            cells: [row.on, row.what, row.blocking, row.since],
          }))}
        />

        <div className={styles.unblocked}>
          <h2 className={styles.label}>What is not blocked</h2>
          <ul className={styles.cards}>
            {UNBLOCKED.map((item) => (
              <Card as="li" key={item.title} className={styles.card}>
                <div className={styles.cardHead}>
                  <h3 className={styles.cardTitle}>{item.title}</h3>
                  {item.badge}
                </div>
                <p className={styles.cardMeta}>{item.meta}</p>
              </Card>
            ))}
          </ul>
        </div>

        <div className={styles.statsBorder}>
          <StatGrid label="What the delay is costing" labelTone="ink" stats={COST_STATS} />
        </div>

        <div className={styles.actions}>
          <Button variant="primary">Send a reminder</Button>
          <Button>Accept the gap and continue</Button>
        </div>
      </Card>
    </Section>
  );
}
