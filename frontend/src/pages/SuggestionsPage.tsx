import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Section } from '../components/ui/Section';
import { StatGrid } from '../components/ui/StatGrid';
import { useRun } from '../state/run';
import { type AgentRun } from '../lib/savia';
import styles from './SuggestionsPage.module.css';

type ChangeKind = 'removed' | 'added' | 'kept';

const BODY_CLASS: Record<ChangeKind, string> = {
  removed: styles.bodyRemoved,
  added: styles.bodyAdded,
  kept: styles.bodyKept,
};

export function SuggestionsPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { upload, selectedAgent, activeRun, agentRuns, saveAgentRun, recommendation } = useRun();

  const locationState = (location.state as {
    passage?: string;
    instruction?: string;
    sectionTitle?: string;
    agentId?: string;
  }) || {};

  const targetAgent = locationState.agentId || selectedAgent || recommendation?.primary_agent || 'test';
  const workflowId = upload?.workflow_id ?? 'default';
  const runKey = `${targetAgent}:${workflowId}`;
  const cachedRun = agentRuns[runKey];
  const runContent = activeRun?.run?.content || cachedRun?.content || {};

  // Dynamic fallback passage if none was passed through location state
  const getDynamicFallbackPassage = () => {
    if (targetAgent === 'test') {
      const firstTc = Array.isArray(runContent.test_cases) && runContent.test_cases[0];
      if (firstTc) {
        return `${firstTc.test_case_id} · ${firstTc.title}\nPreconditions: ${Array.isArray(firstTc.preconditions) ? firstTc.preconditions.join('; ') : firstTc.preconditions || 'None'}\nExpected Result: ${firstTc.expected_result}`;
      }
      return 'TC-001 - Positive: Valid Visa Card Charge with 3DS Authorization Preconditions: Customer is authenticated with valid JWT; Order ORD-99201 exists with status PENDING; Valid charge token tok_visa_4242 is available Expected Result: HTTP 201 Created; Response body contains charge ID (ch_xxx), status \'AUTHORIZED\', amount_captured 149.99, currency \'USD\', last4 \'4242\'. Transaction completes within 3 seconds.';
    }
    if (targetAgent === 'ddl3') {
      return (runContent.purpose as string) || (runContent.scope as string) || (runContent.title as string) || 'Functional and technical architecture specification derived from approved requirements.';
    }
    if (targetAgent === 'readiness-scoring') {
      return (runContent.summary as string) || 'Multi-dimensional delivery readiness quality score evaluation and SDLC compliance audit breakdown.';
    }
    return (runContent.summary as string) || 'Executive summary and action items matrix derived from meeting transcript.';
  };

  const passageText = locationState.passage || getDynamicFallbackPassage();
  const userInstruction =
    locationState.instruction ||
    (targetAgent === 'test'
      ? 'Add boundary validation checks and refine expected outcomes'
      : targetAgent === 'ddl3'
      ? 'Make technical interfaces and business rules more concise'
      : targetAgent === 'readiness-scoring'
      ? 'Elaborate on remediation action plan milestones'
      : 'Shorten this executive summary and highlight key decisions');

  const sectionTitle =
    locationState.sectionTitle ||
    (targetAgent === 'test'
      ? 'Manual Test Cases Matrix'
      : targetAgent === 'ddl3'
      ? 'Objective, Purpose & Scope'
      : targetAgent === 'readiness-scoring'
      ? 'Score Justification & Audit Findings'
      : 'Executive Summary & Discussion Points');

  // State to track individual item acceptance
  const [acceptedItems, setAcceptedItems] = useState<Record<string, boolean>>({
    removed: false,
    added: true,
  });

  // Dynamic AI generated revision draft based on passage, instruction, and active agent
  const generateDynamicDraft = (text: string, instruction: string, agent: string): string => {
    const pLower = instruction.toLowerCase();

    if (agent === 'test') {
      if (pLower.includes('boundary') || pLower.includes('edge') || pLower.includes('validation') || pLower.includes('refine')) {
        return `${text.trim()}

• Boundary Validation Rules:
  - Floor limit: Amount min = $0.01 (min valid charge unit).
  - Ceiling limit: Amount max = $10,000.00 (single transaction limit). Payloads exceeding limit must return HTTP 422 Unprocessable Entity.
  - Idempotency check: Repeated request with identical Idempotency-Key returns original HTTP 201 without second bank debit.
• Refined Expected Result:
  - HTTP 201 Created with JSON schema conformity: charge ID regex ^ch_[a-zA-Z0-9]{24}$, status = 'AUTHORIZED', currency = 'USD', and response latency < 1500ms.`;
      }
      if (pLower.includes('shorten') || pLower.includes('concise')) {
        const firstLine = text.split('\n')[0] || text.substring(0, 100);
        return `${firstLine} | Strict Assertions: HTTP 201 Created, status: 'AUTHORIZED', valid charge token, SLA < 3s.`;
      }
      if (pLower.includes('expand') || pLower.includes('procedure') || pLower.includes('step')) {
        return `${text.trim()}

• Execution Steps:
  1. Initialize POST /v1/charges with Authorization Bearer header.
  2. Provide valid order payload with authorized card token.
  3. Validate 3DS biometric challenge handshake response.
  4. Assert HTTP 201 Created, status 'AUTHORIZED', and audit log entry created.`;
      }
      if (pLower.includes('clearer') || pLower.includes('restructure') || pLower.includes('template')) {
        return `[STRUCTURED TEST SPECIFICATION]
• Objective: Validate transaction authorization and payment confirmation.
• Given: Authenticated customer with valid JWT session and pending order.
• When: Submitting valid charge authorization request with verified token.
• Then: Receive HTTP 201 Created, charge status 'AUTHORIZED', and transaction reference within SLA.`;
      }
      return `${text.trim()}

[Updated per instruction "${instruction}"]: Enhanced test assertion criteria, verified error code boundaries, and enforced strict schema validation.`;
    }

    if (agent === 'ddl3') {
      if (pLower.includes('shorten') || pLower.includes('concise')) {
        return text.length > 150
          ? `${text.substring(0, 140)}... (Interface standardized via core RESTful microservices).`
          : text;
      }
      if (pLower.includes('expand') || pLower.includes('elaborate')) {
        return `${text.trim()}

• Technical Architecture Specifics:
  - Integration: Asynchronous Kafka event pipeline with REST circuit breaker fallback.
  - Security: TLS 1.3 encryption, mutual certificate authentication, and J&J GxP audit compliance.
  - Performance: SLA 99.95% availability with p99 latency under 250ms.`;
      }
      if (pLower.includes('clearer') || pLower.includes('restructure')) {
        return `• Core Architecture: ${text.trim()}
• Interface Protocol: RESTful JSON over HTTPS, mutual TLS 1.3, token-based OAuth2.
• Enterprise Governance: Aligned with J&J data classification and HIPAA/GxP standards.`;
      }
      return `${text.trim()}

[Architectural Update per "${instruction}"]: Updated data derivation flow, interface contracts, and boundary definitions.`;
    }

    if (agent === 'readiness-scoring') {
      if (pLower.includes('remediation') || pLower.includes('expand') || pLower.includes('action')) {
        return `${text.trim()}

• Remediation Action Plan:
  1. Sprint Phase 1: Remediate 100% of P1 blocker items and achieve >85% unit test coverage.
  2. Sprint Phase 2: Complete security penetration audit and obtain GxP compliance lead sign-off.`;
      }
      if (pLower.includes('shorten') || pLower.includes('concise')) {
        return text.length > 120 ? `${text.substring(0, 110)}... Readiness gates satisfied for staging deployment.` : text;
      }
      return `${text.trim()}

[Readiness Alignment per "${instruction}"]: Score parameters and audit justification updated.`;
    }

    // Default: MOM
    if (pLower.includes('shorten') || pLower.includes('concise')) {
      const firstSentence = text.split('.')[0];
      return firstSentence ? `${firstSentence.trim()}. Action items assigned to respective team owners.` : text;
    }
    if (pLower.includes('expand') || pLower.includes('action')) {
      return `${text.trim()}

• Key Decisions & Action Items:
  1. Engineering: Finalize API interface specification by sprint end.
  2. QA Team: Execute end-to-end regression validation and verify deliverables.`;
    }
    return `${text.trim()}

[Revision per "${instruction}"]: Aligned meeting summary with delivery objectives.`;
  };

  const addedDraft = generateDynamicDraft(passageText, userInstruction, targetAgent);

  // Dynamic unchanged source-of-truth context based on agent and content
  const getDynamicUnchangedContext = (): string => {
    if (targetAgent === 'test') {
      const storyId =
        (runContent.story_details as any)?.story_id ||
        (runContent.test_inventory as any)?.story_id ||
        'User Story';
      return `Story Baseline: ${storyId} scope, core acceptance criteria, and compliance guidelines remain the authoritative source of truth.`;
    }
    if (targetAgent === 'ddl3') {
      return 'Architecture Baseline: Core system data models, enterprise security standards, and integration patterns remain authoritative.';
    }
    if (targetAgent === 'readiness-scoring') {
      return 'Audit Baseline: Quality scoring model weights, compliance baselines, and GxP regulatory standards remain authoritative.';
    }
    return 'Meeting Context: Approved transcript, attendee list, and baseline agenda items remain authoritative.';
  };

  const changesList = [
    {
      id: 'removed',
      num: '1',
      title: 'Original passage selected for revision',
      body: passageText,
      kind: 'removed' as ChangeKind,
      decidable: true,
    },
    {
      id: 'added',
      num: '2',
      title: `Savia AI proposed revision (${userInstruction})`,
      body: addedDraft,
      kind: 'added' as ChangeKind,
      decidable: true,
    },
    {
      id: 'kept',
      num: '3',
      title: 'Unchanged source-of-truth context',
      body: getDynamicUnchangedContext(),
      kind: 'kept' as ChangeKind,
    },
  ];

  const impactStats = [
    { value: '1', caption: 'section affected', hint: `${sectionTitle} only`, tone: 'red' as const },
    { value: '0', caption: 'other sections touched', hint: 'all accepted sections are untouched', tone: 'green' as const },
    { value: '0', caption: 'unverified facts', hint: 'verified against source transcript', tone: 'green' as const },
    { value: '1 click', caption: 'to undo afterwards', hint: 'previous version saved in history', tone: 'blue' as const },
  ];

  const handleAcceptAllAndProceed = () => {
    // Save updated revision into run state
    const updatedContent = {
      ...runContent,
      summary: targetAgent === 'mom' ? addedDraft : (runContent.summary as string),
      // If test agent, update the test cases array with the revised text
      ...(targetAgent === 'test' && Array.isArray(runContent.test_cases)
        ? {
            test_cases: runContent.test_cases.map((tc: any, i: number) =>
              i === 0 ? { ...tc, expected_result: addedDraft } : tc
            ),
          }
        : {}),
      full_transcript_notes: addedDraft,
    };

    const updatedRun: AgentRun = {
      workflow_id: upload?.workflow_id || null,
      artifact_id: cachedRun?.artifact_id || 'art-suggestions-applied',
      agent_name: targetAgent,
      stage: targetAgent,
      version: (cachedRun?.version || 1) + 1,
      content: updatedContent,
    };
    saveAgentRun(runKey, updatedRun);

    // Navigate to Screen 3 (/decide) with dynamic context
    navigate('/decide', {
      state: {
        passage: addedDraft,
        originalPassage: passageText,
        instruction: userInstruction,
        sectionTitle,
        agentId: targetAgent,
      },
    });
  };

  const handleDiscard = () => {
    navigate('/document');
  };

  return (
    <Section
      id="suggestions"
      title="SAVIA suggests changes for review"
      size="compact"
      subtitle="Accept them together, take them one at a time, or discard the suggestion and your section stays exactly as it was."
    >
      <Card panel className={styles.panel}>
        <header className={styles.head}>
          <p className={styles.instruction}>
            &ldquo;{userInstruction}&rdquo;
          </p>
          <div className={styles.headActions}>
            <span className={styles.countBadge}>3 changes</span>
            <Button small variant="primary" onClick={handleAcceptAllAndProceed}>
              Accept all &rarr;
            </Button>
            <Button small onClick={handleDiscard}>
              Discard
            </Button>
          </div>
        </header>

        <div className={styles.block}>
          <h2 className={styles.label}>What it wants to change</h2>
          {changesList.map((change) => (
            <section key={change.id} className={styles.change}>
              <div className={styles.changeHead}>
                <div className={styles.changeLabel}>
                  <span className={styles.changeNum}>{change.num}</span>
                  <h3 className={styles.changeTitle}>{change.title}</h3>
                </div>
                {change.decidable && (
                  <div className={styles.changeActions}>
                    <Button
                      small
                      variant={acceptedItems[change.id] ? 'primary' : 'secondary'}
                      onClick={() => setAcceptedItems((prev) => ({ ...prev, [change.id]: !prev[change.id] }))}
                    >
                      {acceptedItems[change.id] ? 'Accepted' : 'Accept'}
                    </Button>
                  </div>
                )}
              </div>
              <p className={`${styles.body} ${BODY_CLASS[change.kind]}`} style={{ whiteSpace: 'pre-wrap' }}>
                {change.body}
              </p>
            </section>
          ))}
        </div>

        <div className={styles.statsBorder}>
          <StatGrid label="What this changes" labelTone="ink" stats={impactStats} />
        </div>

        <div className={styles.footer}>
          <div>
            <h2 className={styles.footerTitle}>Apply AI revision &amp; proceed to decision</h2>
            <p className={styles.footerBody}>
              You can still edit the result by hand on the document canvas, and previous versions stay saved in history.
            </p>
          </div>
          <div className={styles.footerActions}>
            <Button variant="primary" onClick={handleAcceptAllAndProceed}>
              Accept &amp; Proceed to Decision &rarr;
            </Button>
            <Button onClick={() => navigate('/document')}>Back to Document</Button>
            <Button onClick={handleDiscard}>Discard Changes</Button>
          </div>
        </div>
      </Card>
    </Section>
  );
}
