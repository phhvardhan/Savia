import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Section } from '../components/ui/Section';
import { StatGrid } from '../components/ui/StatGrid';
import { StatusPill } from '../components/ui/StatusPill';
import { agentMeta, type AgentRun } from '../lib/savia';
import { useRun } from '../state/run';
import styles from './DecidePage.module.css';

interface DecisionOption {
  id: string;
  title: string;
  text: string;
  cost: string;
  leaning?: boolean;
}

export function DecidePage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { recommendation, selectedAgent, upload, agentRuns, saveAgentRun, activeRun } = useRun();

  const locationState = (location.state as {
    passage?: string;
    originalPassage?: string;
    instruction?: string;
    sectionTitle?: string;
    agentId?: string;
  }) || {};

  const targetAgent = locationState.agentId || selectedAgent || recommendation?.primary_agent || 'test';
  const workflowId = upload?.workflow_id ?? 'default';
  const runKey = `${targetAgent}:${workflowId}`;
  const cachedRun = agentRuns[runKey];
  const runContent = activeRun?.run?.content || cachedRun?.content || {};

  const agent = recommendation?.recommended_agents?.find((a) => a.agent === targetAgent) ?? null;
  const label = agent
    ? agentMeta(agent).label
    : targetAgent === 'test'
    ? 'TEST'
    : targetAgent === 'ddl3'
    ? 'DDL3'
    : targetAgent === 'readiness-scoring'
    ? 'Readiness'
    : 'MOM';

  // Section number & title dynamic per agent
  const sectionNum = targetAgent === 'test' ? '4' : targetAgent === 'ddl3' ? '5' : targetAgent === 'readiness-scoring' ? '2' : '3';
  const sectionTitle =
    locationState.sectionTitle ||
    (targetAgent === 'test'
      ? 'Test Execution Strategy & Pipeline Orchestration'
      : targetAgent === 'ddl3'
      ? 'Validation, Derivation & Architecture Stack'
      : targetAgent === 'readiness-scoring'
      ? 'Quality Gate Enforcement & Compliance Policy'
      : 'Action Items & Delivery Governance Cadence');

  // Dynamic open trade-off note
  const getDynamicOpenNote = (): string => {
    if (targetAgent === 'test') {
      return 'Test execution orchestration model is open between high-speed isolated contract mocks versus live end-to-end sandbox execution. Review and pick the optimal execution model below.';
    }
    if (targetAgent === 'readiness-scoring') {
      return 'Production release gate enforcement policy has two compliance options. Choose how strict to configure automated deployment blockers.';
    }
    if (targetAgent === 'mom') {
      return 'Action item sprint tracking workflow is open between automated Jira story linkage versus weekly digest review. Choose the preferred team tracking model.';
    }
    return 'Consolidation Unit and derivation source is open between stack substitution versus master data derivation. See the two implementation options below.';
  };

  // Dynamic options list based on active agent
  const getDynamicOptions = (): DecisionOption[] => {
    if (targetAgent === 'test') {
      return [
        {
          id: 'mock-contract',
          title: 'Mock-Based Contract Testing (WireMock & MSW)',
          text: 'Fastest pipeline execution (< 45s) with 100% deterministic test runs. Validates request/response contracts, boundary limits, and 3DS authorization tokens without live network dependencies.',
          cost: 'Cost: Mock fixtures must be maintained when external API contracts change.',
          leaning: true,
        },
        {
          id: 'live-sandbox',
          title: 'Live Sandbox Integration Testing',
          text: 'Executes real end-to-end network requests against the staging payment gateway. Validates live tokenization, bank authorization webhooks, and real TLS handshake latency.',
          cost: 'Cost: Slower pipeline execution (~4 mins) and dependent on gateway staging uptime.',
          leaning: false,
        },
      ];
    }

    if (targetAgent === 'readiness-scoring') {
      return [
        {
          id: 'strict-blocker',
          title: 'Strict Automated Blocker Gate (GxP / Compliance)',
          text: 'Automated CI/CD gate immediately blocks deployment if any P1 readiness finding is open or test coverage is below 85%. Enforces zero-defect policy for healthcare compliance.',
          cost: 'Cost: May delay emergency hotfixes pending formal exception approvals.',
          leaning: true,
        },
        {
          id: 'soft-gate',
          title: 'Soft Gate with Documented Technical Sign-off',
          text: 'Allows staging deployment with non-critical open items if Product Owner and QA Lead provide signed waiver with scheduled sprint remediation ticket.',
          cost: 'Cost: Introduces technical debt tracking overhead.',
          leaning: false,
        },
      ];
    }

    if (targetAgent === 'mom') {
      return [
        {
          id: 'auto-jira',
          title: 'Automated Jira Story & Sprint Backlog Sync',
          text: 'Automatically provisions Jira subtasks, assigns story points directly to named attendees, and links acceptance criteria to the current sprint backlog.',
          cost: 'Cost: Requires strict Jira board field permissions.',
          leaning: true,
        },
        {
          id: 'manual-digest',
          title: 'Digest Review & Lead Allocation',
          text: 'Publishes summary notes to Confluence space and holds action items in pending queue for delivery lead to review and assign during standup.',
          cost: 'Cost: Manual coordination step required before development begins.',
          leaning: false,
        },
      ];
    }

    // Default: DDL3
    return [
      {
        id: 'substitution',
        title: 'Substitution on the stack',
        text: 'Follows the SAP recommendation and matches what Finance S4 already does. No custom ABAP. Architecture criteria are written assuming this pattern.',
        cost: 'Cost: derivation runs on every posting transaction.',
        leaning: true,
      },
      {
        id: 'master-data',
        title: 'Derive in the master data object',
        text: 'Simpler to maintain and easier to correct after the fact, but it diverges from Finance S4 and needs a periodic reconciliation job.',
        cost: 'Cost: a new reconciliation job to own and monitor.',
        leaning: false,
      },
    ];
  };

  const options = getDynamicOptions();
  const [selectedId, setSelectedId] = useState<string>(options[0]?.id || '');
  const selectedOption = options.find((o) => o.id === selectedId) || options[0];

  // Dynamic impact stats
  const getDynamicImpact = () => {
    if (targetAgent === 'test') {
      return [
        { value: '1', caption: 'test suite updated', hint: `${sectionTitle}, in place` },
        { value: '1', caption: 'execution plan updated', hint: 'CI/CD pipeline test strategy' },
        { value: '4', caption: 'test cases aligned', hint: 'TC-001 through TC-004' },
        { value: '0', caption: 'things you retype', hint: 'the decision carries forward', tone: 'red' as const },
      ];
    }
    if (targetAgent === 'readiness-scoring') {
      return [
        { value: '1', caption: 'policy updated', hint: 'Deployment gate strategy' },
        { value: '1', caption: 'scorecard updated', hint: 'Compliance model weight' },
        { value: '3', caption: 'audit checks aligned', hint: 'P1 blocker criteria' },
        { value: '0', caption: 'things you retype', hint: 'the decision carries forward', tone: 'red' as const },
      ];
    }
    if (targetAgent === 'mom') {
      return [
        { value: '1', caption: 'matrix updated', hint: 'Action items & governance' },
        { value: '1', caption: 'workflow synced', hint: 'Jira sprint alignment' },
        { value: '5', caption: 'owners assigned', hint: 'Attendees & leads' },
        { value: '0', caption: 'things you retype', hint: 'the decision carries forward', tone: 'red' as const },
      ];
    }
    return [
      { value: '1', caption: 'section rewritten', hint: 'Section 5, in place' },
      { value: '1', caption: 'table updated', hint: 'Impact and dependencies' },
      { value: '2', caption: 'criteria affected', hint: 'AC-001 and AC-002 on JGFY-8052' },
      { value: '0', caption: 'things you retype', hint: 'the change carries forward', tone: 'red' as const },
    ];
  };

  const impactStats = getDynamicImpact();

  const handleChooseAndRewrite = () => {
    const updatedContent = {
      ...runContent,
      decision: {
        option_id: selectedOption?.id,
        option_title: selectedOption?.title,
        status: 'decided',
        decided_by: 'Business Analyst',
        timestamp: new Date().toISOString(),
      },
      architecture_notes: `${label} Decision Applied: "${selectedOption?.title}" - ${selectedOption?.text}`,
    };

    const updatedRun: AgentRun = {
      workflow_id: upload?.workflow_id || null,
      artifact_id: cachedRun?.artifact_id || 'art-decision-applied',
      agent_name: targetAgent,
      stage: targetAgent,
      version: (cachedRun?.version || 1) + 1,
      content: updatedContent,
    };
    saveAgentRun(runKey, updatedRun);
    navigate('/sharing');
  };

  const handleLeaveForLead = () => {
    navigate('/document');
  };

  return (
    <Section
      id="decide"
      title={`${label} will not decide this one for you`}
      size="compact"
      subtitle="Pick one and it rewrites the section, the impact table and the criteria that depend on it."
      aside={
        <StatusPill tone="alert" dot>
          Your turn · Business Analyst
        </StatusPill>
      }
    >
      <Card panel className={styles.panel}>
        <div className={styles.block}>
          <h2 className={styles.label}>The section as it stands</h2>
          <div className={styles.section}>
            <div className={styles.sectionHead}>
              <span className={styles.sectionNum}>{sectionNum}</span>
              <h3 className={styles.sectionTitle}>{sectionTitle}</h3>
            </div>
            <p className={styles.openNote}>
              {getDynamicOpenNote()}
            </p>
          </div>
        </div>

        <div className={`${styles.block} ${styles.divider}`}>
          <h2 className={`${styles.label} ${styles.labelRed}`}>The two options {label} found</h2>
          <ul className={styles.options}>
            {options.map((option) => {
              const isSelected = selectedId === option.id;
              return (
                <li
                  key={option.id}
                  className={`${styles.option} ${option.leaning ? styles.optionLeaning : ''} ${
                    isSelected ? styles.optionSelected : ''
                  } ${styles.optionClickable}`}
                  onClick={() => setSelectedId(option.id)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      setSelectedId(option.id);
                    }
                  }}
                >
                  <div className={styles.optionHead}>
                    <h3 className={styles.optionTitle}>{option.title}</h3>
                    {isSelected ? (
                      <span className={styles.selectedBadge}>
                        &#10003; Selected
                      </span>
                    ) : option.leaning ? (
                      <span className={styles.leans}>
                        <span className={styles.leansDot} aria-hidden="true" />
                        {label} leans here
                      </span>
                    ) : null}
                  </div>
                  <p className={styles.optionText}>{option.text}</p>
                  <p className={`${styles.cost} ${option.leaning || isSelected ? styles.costLeaning : ''}`}>
                    {option.cost}
                  </p>
                </li>
              );
            })}
          </ul>
        </div>

        <div className={styles.statsBorder}>
          <StatGrid label="What changes when you choose" labelTone="ink" stats={impactStats} />
        </div>

        <div className={styles.footer}>
          <div>
            <h2 className={styles.footerTitle}>Choose {selectedOption?.title}</h2>
            <p className={styles.footerBody}>
              You can also leave it open and flag it for the Design Lead — the document will be marked pending until someone decides.
            </p>
          </div>
          <div className={styles.footerActions}>
            <Button variant="primary" onClick={handleChooseAndRewrite}>
              Choose this and rewrite
            </Button>
            <Button onClick={handleLeaveForLead}>
              Leave it for the Design Lead
            </Button>
            <Button onClick={() => navigate('/document')}>
              Back to Document
            </Button>
          </div>
        </div>
      </Card>
    </Section>
  );
}
