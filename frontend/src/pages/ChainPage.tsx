import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Section } from '../components/ui/Section';
import { StatGrid } from '../components/ui/StatGrid';
import { StatusPill } from '../components/ui/StatusPill';
import styles from './ChainPage.module.css';

type StageState = 'available' | 'comingSoon' | 'running' | 'inReview' | 'queued';

interface StageCard {
  id: string;
  label: string;
  title: string;
  state: StageState;
  stateText: string;
}

const STAGE_STATE_CLASS: Record<StageState, string> = {
  available: styles.stateAvailable,
  comingSoon: styles.stateComingSoon,
  running: styles.stateRunning,
  inReview: styles.stateInReview,
  queued: styles.stateComingSoon,
};

const COL_1: StageCard[] = [
  { id: 'mom', label: 'Requirements', title: 'MoM & Action Items', state: 'available', stateText: 'Available' },
  {
    id: 'stories',
    label: 'Requirements',
    title: 'Agile User Stories & Epics',
    state: 'comingSoon',
    stateText: 'Coming soon',
  },
  { id: 'rtm', label: 'Requirements', title: 'Requirement Gap & RTM', state: 'available', stateText: 'Available' },
];

const COL_2: StageCard[] = [
  { id: 'ddl3', label: 'Design', title: 'DDL3 — design documents', state: 'running', stateText: 'Running' },
  {
    id: 'architecture',
    label: 'Design',
    title: 'Enterprise Architecture',
    state: 'inReview',
    stateText: 'In review',
  },
  {
    id: 'kdd',
    label: 'Design governance',
    title: 'KDD Package for DAB',
    state: 'available',
    stateText: 'Available',
  },
  {
    id: 'change',
    label: 'Change',
    title: 'Change Impact & Interdependency',
    state: 'available',
    stateText: 'Available',
  },
];

const COL_3: StageCard[] = [
  { id: 'test', label: 'Testing', title: 'TEST — inventories and cases', state: 'queued', stateText: 'Queued' },
  {
    id: 'readiness',
    label: 'Release',
    title: 'Delivery Readiness & SDLC Audit',
    state: 'comingSoon',
    stateText: 'Coming soon',
  },
  { id: 'cutover', label: 'Cutover', title: 'Cutover — deployment docs', state: 'available', stateText: 'Available' },
];

const BEHAVIOUR = [
  { value: '10', caption: 'agents in the chain', hint: '7 you can run today' },
  { value: '3', caption: 'approval gates', hint: 'one per stage that matters' },
  { value: '2', caption: 'can run in parallel', hint: 'TEST and Change Impact' },
  { value: '1', caption: 'packet', hint: 'it grows, it is never retyped' },
];

function StageCardItem({ card }: { card: StageCard }) {
  return (
    <div className={styles.stageCard}>
      <p className={styles.stageLabel}>{card.label}</p>
      <h3 className={styles.stageTitle}>{card.title}</h3>
      <span className={`${styles.statePill} ${STAGE_STATE_CLASS[card.state]}`}>
        {card.state === 'running' && <span className={styles.stateDot} aria-hidden="true" />}
        {card.stateText}
      </span>
    </div>
  );
}

function GateNode({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className={styles.gate}>
      <p className={styles.gateLabel}>{title}</p>
      <p className={styles.gateText}>{subtitle}</p>
    </div>
  );
}

export function ChainPage() {
  const navigate = useNavigate();

  return (
    <Section
      id="chain"
      title="How the agents chain across the lifecycle"
      size="compact"
      subtitle="This is the whole chain, where the approvals sit, and which two can run at the same time."
      aside={<StatusPill tone="neutral">8 stages · 3 approval gates</StatusPill>}
    >
      <Card panel className={styles.panel}>
        <div className={styles.block}>
          <div className={styles.columns}>
            <div className={styles.column}>
              <p className={styles.columnLabel}>From a meeting or a document</p>
              <div className={styles.stack}>
                {COL_1.map((card) => (
                  <StageCardItem key={card.id} card={card} />
                ))}
              </div>
            </div>

            <div className={styles.gateColumn}>
              <GateNode title="Human approval" subtitle="Stories approved" />
              <GateNode title="Human approval" subtitle="Design approved" />
            </div>

            <div className={styles.column}>
              <p className={`${styles.columnLabel} ${styles.columnLabelRed}`}>Through the lifecycle</p>
              <div className={styles.stack}>
                {COL_2.map((card) => (
                  <StageCardItem key={card.id} card={card} />
                ))}
              </div>
            </div>

            <div className={styles.gateColumn}>
              <GateNode title="Human approval" subtitle="Coverage approved" />
            </div>

            <div className={styles.column}>
              <p className={styles.columnLabel}>To a signed release</p>
              <div className={styles.stack}>
                {COL_3.map((card) => (
                  <StageCardItem key={card.id} card={card} />
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className={styles.statsBorder}>
          <StatGrid label="How the chain behaves" stats={BEHAVIOUR} />
        </div>

        <div className={styles.footer}>
          <div>
            <h2 className={styles.footerTitle}>You never run the whole chain</h2>
            <p className={styles.footerBody}>
              Savia reads your input, works out where in this picture you are standing, and proposes only the agents
              from there onwards.
            </p>
          </div>
          <div className={styles.footerActions}>
            <Button variant="primary" onClick={() => navigate('/start')}>
              Show me for my requirement
            </Button>
            <Button onClick={() => navigate('/agents')}>Open an agent</Button>
          </div>
        </div>
      </Card>
    </Section>
  );
}
