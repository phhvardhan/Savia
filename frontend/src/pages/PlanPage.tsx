import { useNavigate } from 'react-router-dom';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { DataTable } from '../components/ui/DataTable';
import { Section } from '../components/ui/Section';
import { StatGrid } from '../components/ui/StatGrid';
import { StatusPill } from '../components/ui/StatusPill';
import { agentLabel, agentMeta, planCost } from '../lib/savia';
import { formatBytes, useAttachment } from '../state/attachment';
import { useRun } from '../state/run';
import styles from './PlanPage.module.css';

const FINDINGS = [
  {
    id: 'stage',
    title: 'Stage',
    pill: 'Requirements → design',
    text: 'The room agreed scope but nothing is written down',
  },
  {
    id: 'exists',
    title: 'What exists',
    pill: '12 approved stories',
    text: 'So the requirements agents are mostly not needed',
  },
  {
    id: 'missing',
    title: 'What is missing',
    pill: 'Minutes, design, DAB pack',
    text: 'And a test set once the design lands',
  },
  {
    id: 'deadline',
    title: 'Deadline pressure',
    pill: 'DAB in 9 days',
    text: 'It puts the KDD package in the plan now',
  },
];

/** Curves are decorative; the columns carry the meaning. Each one ends at the
 *  centre of its card, so they fan out evenly whatever the plan's length. */
function curveEnd(index: number, total: number): number {
  return ((index + 0.5) / total) * 100;
}
const RIGHT_COLOURS = ['#EB1700', '#005EEB', '#EB7D00', '#D82E59', '#40AF0C'];
const RANK_TONES = [styles.rec1, styles.rec2, styles.rec3, styles.rec4, styles.rec5];
const COUNT_WORDS = ['no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight'];

export function PlanPage() {
  const navigate = useNavigate();
  const { attachment } = useAttachment();
  const { upload, recommendation, selectedAgent, startAgentRun } = useRun();

  // The plan is the top five SAVIA returned: every agent the document
  // triggered first, then the next best available ones to round it out.
  const plan = (recommendation?.recommended_agents ?? []).slice(0, 5);
  const cost = planCost(plan);
  const countWord = COUNT_WORDS[cost.count] ?? String(cost.count);

  return (
    <Section
      id="plan"
      title={`Savia read it and recommends ${countWord} agent${cost.count === 1 ? '' : 's'}`}
      size="compact"
      subtitle="You gave it one workshop recording. It worked out the stage, found what already exists on this release, and proposed the agents that cover the rest in the order they have to run."
      aside={
        <StatusPill tone="alert" dot>
          Your turn · approve the plan
        </StatusPill>
      }
    >
      <Card panel className={styles.panel}>
        <div className={styles.board}>
          <p className={`${styles.columnLabel} ${styles.labelGave}`}>What you gave it</p>
          <p className={`${styles.columnLabel} ${styles.labelWorking}`}>Savia is working it out</p>
          <p className={`${styles.columnLabel} ${styles.labelRecommends}`}>What it recommends</p>

          <div className={styles.gave}>
            <article className={styles.inputCard}>
              <div className={styles.inputHead}>
                <h3 className={styles.inputTitle}>
                  {attachment ? attachment.name : 'Nothing attached'}
                </h3>
                <Badge tone={attachment ? 'solidGreen' : 'waiting'}>
                  {attachment ? 'Read' : 'Waiting'}
                </Badge>
              </div>
              <p className={styles.inputMeta}>
                {attachment
                  ? `${formatBytes(attachment.size)} · ${attachment.kind}`
                  : 'Attach a document to build a plan'}
              </p>
              {upload && (
                <ul className={styles.inputList}>
                  <li className={styles.inputItem}>
                    <span className={styles.bullet} aria-hidden="true">·</span>
                    <span>Read · {upload.metadata.word_count.toLocaleString()} words</span>
                  </li>
                </ul>
              )}
            </article>

            <article className={styles.inputCard}>
              <div className={styles.inputHead}>
                <h3 className={styles.inputTitle}>Project context</h3>
                <Badge tone="waiting">Loaded</Badge>
              </div>
              <p className={styles.inputMeta}>TIME · Release 2.1 · Finance</p>
              <ul className={styles.inputList}>
                {['12 approved BUS', 'No design document yet', 'DAB meets in 9 days'].map((item) => (
                  <li key={item} className={styles.inputItem}>
                    <span className={styles.bullet} aria-hidden="true">·</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </article>
          </div>

          <svg
            className={`${styles.connector} ${styles.connectorLeft}`}
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
            aria-hidden="true"
          >
            <path d="M0 25 C 45 25, 55 46, 100 46" fill="none" stroke="#C3C4C5" strokeWidth="0.7" />
            <path d="M0 75 C 45 75, 55 54, 100 54" fill="none" stroke="#C3C4C5" strokeWidth="0.7" />
          </svg>

          <section className={styles.orchestrator} aria-label="Orchestrator analysis">
            <div className={styles.orchestratorHead}>
              <h3 className={styles.orchestratorName}>Orchestrator</h3>
              <p className={styles.orchestratorState}>Analysis complete</p>
            </div>
            {FINDINGS.map((finding) => (
              <div key={finding.id} className={styles.finding}>
                <div className={styles.findingHead}>
                  <h4 className={styles.findingTitle}>{finding.title}</h4>
                  <span className={styles.findingPill}>
                    {finding.id === 'stage' && recommendation?.current_stage
                      ? recommendation.current_stage
                      : finding.pill}
                  </span>
                </div>
                <p className={styles.findingText}>{finding.text}</p>
              </div>
            ))}
          </section>

          <svg
            className={`${styles.connector} ${styles.connectorRight}`}
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
            aria-hidden="true"
          >
            {plan.map((agent, index) => (
              <path
                key={agent.agent}
                d={`M0 50 C 50 50, 50 ${curveEnd(index, plan.length)}, 100 ${curveEnd(index, plan.length)}`}
                fill="none"
                stroke={RIGHT_COLOURS[index]}
                strokeWidth="0.8"
              />
            ))}
          </svg>

          <ul className={styles.recommends}>
            {plan.length === 0 && (
              <li className={styles.recommendPending}>
                No plan yet — let Savia read a document first.
              </li>
            )}
            {plan.map((agent, index) => (
              <li key={agent.agent} className={`${styles.recommend} ${RANK_TONES[index]}`}>
                {index + 1} · {agentLabel(agent)}
              </li>
            ))}
          </ul>
        </div>

        <DataTable
          caption="The recommended agents, why each was chosen and who approves it"
          columns={[
            { key: 'rank', label: '', width: '5%' },
            { key: 'agent', label: 'Agent', width: '24%' },
            { key: 'why', label: 'Why Savia chose it' },
            { key: 'get', label: 'What you get', width: '22%' },
            { key: 'approval', label: 'Approval', width: '13%' },
          ]}
          rows={plan.map((agent, index) => {
            const meta = agentMeta(agent);
            return {
              id: agent.agent,
              cells: [
                <span key="rank" className={styles.rank}>{index + 1}</span>,
                meta.full,
                agent.reason,
                meta.output,
                <span key="approval" className={styles.approvalPill}>
                  <span className={styles.approvalDot} aria-hidden="true" />
                  {meta.approver}
                </span>,
              ],
            };
          })}
        />

        <div className={styles.costsBorder}>
          <StatGrid
            label="What this plan costs you"
            labelTone="ink"
            stats={[
              { value: String(cost.count), caption: 'agents, in order', hint: 'as SAVIA ranked them' },
              {
                value: String(cost.count),
                caption: 'times it needs you',
                hint: 'one approval each',
                tone: 'red' as const,
              },
              {
                value: `~${cost.agentMinutes} min`,
                caption: 'of agent time',
                hint: 'you are not waiting on it',
              },
              {
                value: `~${cost.manualDays} days`,
                caption: 'of manual work replaced',
                hint: 'estimated per agent',
                tone: 'red' as const,
              },
            ]}
          />
        </div>

        <div className={styles.actions}>
          <Button
            variant="primary"
            disabled={!upload || plan.length === 0}
            onClick={() => {
              // Fire the agent, then move on — the writing page shows progress
              // rather than waiting here on a call that takes up to a minute.
              const agentId = selectedAgent ?? plan[0]?.agent;
              if (agentId) startAgentRun(agentId);
              navigate('/writing');
            }}
          >
            Approve and start
          </Button>
          <Button onClick={() => navigate('/reading')}>Change the plan</Button>
        </div>
      </Card>
    </Section>
  );
}
