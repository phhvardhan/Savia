import type { ComponentType } from 'react';
import { AGENTS, STATE_TONE } from '../data/agents';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import {
  BlueprintIcon,
  BranchIcon,
  DossierIcon,
  FlagIcon,
  FlaskIcon,
  LayersIcon,
  MatrixIcon,
  NotesIcon,
  StackIcon,
  TargetIcon,
} from '../components/ui/Icons';
import { Section } from '../components/ui/Section';
import { StatusPill } from '../components/ui/StatusPill';
import styles from './WorkPage.module.css';

/** Same marks as the Library table, keyed by the ids in data/agents.ts. */
const AGENT_ICONS: Record<string, ComponentType> = {
  mom: NotesIcon,
  'agile-stories': StackIcon,
  'gap-analysis': MatrixIcon,
  ddl3: BlueprintIcon,
  'solution-analyzer': LayersIcon,
  'kdd-dab': DossierIcon,
  'change-impact': BranchIcon,
  test: FlaskIcon,
  'readiness-audit': TargetIcon,
  cutover: FlagIcon,
};

export function WorkPage() {
  const availableCount = AGENTS.filter((agent) => agent.state === 'Available').length;

  return (
    <Section
      id="work"
      title="Every agent, and what it can actually do"
      subtitle="The full capability list for each of the ten agents the same detail the capability sheets carry, in the place where people choose."
      aside={<StatusPill tone="neutral">{`${AGENTS.length} agents · ${availableCount} available`}</StatusPill>}
    >
      <Card panel className={styles.panel}>
        <ul className={styles.grid}>
          {AGENTS.map((agent) => {
            const isComingSoon = agent.state === 'Coming soon';
            return (
              <li key={agent.id} className={styles.agent}>
                <div className={styles.head}>
                  <span className={styles.icon}>
                    {(() => {
                      const Icon = AGENT_ICONS[agent.id];
                      return Icon ? <Icon /> : null;
                    })()}
                  </span>
                  <div className={styles.headText}>
                    <h3 className={`${styles.name} ${isComingSoon ? styles.nameMuted : ''}`}>{agent.name}</h3>
                    <p className={styles.stage}>{agent.stage}</p>
                  </div>
                  <span className={styles.state}>
                    <Badge tone={STATE_TONE[agent.state]}>{agent.state}</Badge>
                  </span>
                </div>

                <ul className={styles.capabilities}>
                  {agent.capabilities.map((capability) => (
                    <li key={capability} className={styles.capability}>
                      <span className={styles.bullet} aria-hidden="true">
                        •
                      </span>
                      <span>{capability}</span>
                    </li>
                  ))}
                </ul>

                <div className={styles.actions}>
                  <Button small>What it needs</Button>
                  {isComingSoon ? (
                    <Button small>Notify me</Button>
                  ) : (
                    <Button variant="primary" small>
                      Run it
                    </Button>
                  )}
                </div>
              </li>
            );
          })}
        </ul>

        <div className={styles.footer}>
          <div className={styles.footerText}>
            <h2 className={styles.footerTitle}>Seven you can run today, three on the way</h2>
            <p className={styles.footerBody}>
              Every one takes its input from something already approved, and every one stops for a person before its
              output leaves Savia.
            </p>
          </div>
          <div className={styles.footerActions}>
            <Button variant="primary">Run one on this release</Button>
            <Button>See how they chain together</Button>
          </div>
        </div>
      </Card>
    </Section>
  );
}
