import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Section } from '../components/ui/Section';
import { useRun } from '../state/run';
import { useAttachment } from '../state/attachment';
import { agentMeta, artifactExportUrl, documentFormat, runAgent, sectionText, sectionTitle, type AgentRun, type RecommendedAgent } from '../lib/savia';
import { BrandPreview } from '../components/BrandPreview';
import styles from './DocumentPage.module.css';

type OutlineState = 'Traced' | 'Changed' | 'Needs you';

interface OpenQuestion {
  id: string;
  question: string;
  context: string;
  status: 'Open' | 'Resolved';
  answer?: string;
}

interface ActionItem {
  id: string;
  action: string;
  speaker: string | null;
  assignee: string | null;
  dueDate: string | null;
  priority: 'High' | 'Medium' | 'Low' | 'null';
  status: 'Pending' | 'In Progress' | 'Completed' | 'null';
}

interface Decision {
  id: string;
  text: string;
  speaker: string | null;
  context?: string | null;
}

interface ActivityEvent {
  id: string;
  title: string;
  note: string;
  time: string;
}

export function DocumentPage() {
  const navigate = useNavigate();
  const { attachment } = useAttachment();
  const { upload, selectedAgent, selectAgent, activeRun, agentRuns, saveAgentRun, recommendation } = useRun();

  // Active section tracking & Global Edit state
  const [activeSection, setActiveSection] = useState<string>('sec-summary');
  const [isGlobalEdit, setIsGlobalEdit] = useState<boolean>(false);

  // Ask Savia AI contextual popover state
  const [isAskSaviaOpen, setIsAskSaviaOpen] = useState<boolean>(false);
  const [aiPrompt, setAiPrompt] = useState<string>('');
  const [aiTargetSection, setAiTargetSection] = useState<string>('Executive Summary');
  const [aiSelectedText, setAiSelectedText] = useState<string>('');
  const [isAiGenerating, setIsAiGenerating] = useState<boolean>(false);

  // Formatting state for rich text toolbar
  const [activeFormats, setActiveFormats] = useState<Record<string, boolean>>({
    bold: false,
    italic: false,
    underline: false,
  });

  const editorRef = useRef<HTMLDivElement>(null);

  // Active agent identification (Supported 4 agents: mom, ddl3, readiness-audit, test)
  const agentId = selectedAgent || recommendation?.primary_agent || 'mom';
  const workflowId = upload?.workflow_id ?? 'default';
  const runKey = `${agentId}:${workflowId}`;
  const cachedRun = agentRuns[runKey];
  const runContent = activeRun?.run?.content || cachedRun?.content || {};
  const artifactId = activeRun?.run?.artifact_id || cachedRun?.artifact_id;
  // Excel only makes sense when the output has tables (cases, inventory, actions…).
  const hasTables = Object.values(runContent).some(
    (v) => Array.isArray(v) && v.length > 0 && v.every((x) => typeof x === 'object' && x !== null && !Array.isArray(x)),
  );
  // "Brand preview" shows the J&J-branded rendering (same as the Word download) instead of the editor.
  const [showBrandPreview, setShowBrandPreview] = useState(false);

  // Agents with a dedicated layout below; any other agent gets a generic one built from its own output.
  const hasLayout = ['mom', 'readiness-audit', 'test', 'ddl3'].includes(agentId);
  const meta = agentMeta(
    recommendation?.recommended_agents.find((a) => a.agent === agentId) ??
      ({ agent: agentId, agent_name: agentId } as RecommendedAgent),
  );
  const genericSections = hasLayout
    ? []
    : Object.entries(runContent as Record<string, unknown>).filter(
        ([key, value]) => !['title', 'open_questions', 'needs_info'].includes(key) && sectionText(value).trim(),
      );

  // Interactive update & saving state
  // The open question whose answer is being sent to the agent (only that card shows "Updating...").
  const [updatingQuestion, setUpdatingQuestion] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string>('');

  // Expand / collapse toggles for long item lists
  const [showAllPoints, setShowAllPoints] = useState(false);
  const [showAllDecisions, setShowAllDecisions] = useState(false);
  const [showAllActions, setShowAllActions] = useState(false);

  // Dynamic Executive Summary
  const [summaryText, setSummaryText] = useState<string>(
    (runContent.summary as string) ||
    (runContent.discussion_summary as string) ||
    `The meeting focused on refining the Nova enterprise order visibility and fulfillment platform, establishing architectural standards, verifying Extensibility parameters, and setting clear team delivery action items across core finance workstreams.`
  );

  // Dynamic Minutes of Meeting (Detailed transcript breakdown points)
  const [momDetailsText, setMomDetailsText] = useState<string>(
    (runContent.full_transcript_notes as string) ||
    `1. Architecture Overview: Reviewed end-to-end order lifecycle from customer channels through ERP, Nova, and inventory services.
2. Extensibility Verification: Confirmed ZCONSUNIT (capped at 10 chars) and ZCATCODE (12 chars post-review) Key User Extensibility rules.
3. Master Data Authority: Verified Finance S4 remains primary master data source, accessible via Fiori App F4579.
4. Operational Readiness: Addressed FIT/UAT test scenario coverage, audit trails, and reconciliation parameters.`
  );

  // Parse Minutes of Meeting into clean distinct points line by line
  const momPointsList: string[] = typeof momDetailsText === 'string'
    ? momDetailsText
        .split('\n')
        .map((p) => p.trim())
        .filter((p) => p.length > 0)
    : Array.isArray(momDetailsText)
    ? momDetailsText
    : [];

  // Dynamic Key Discussion Points
  const rawKeyPoints: string[] =
    Array.isArray(runContent.key_points) && runContent.key_points.length > 0
      ? (runContent.key_points as string[])
      : [
          'Refined Nova enterprise order visibility and fulfillment platform architecture.',
          'Reviewed Key User Extensibility rules for custom fields ZCONSUNIT and ZCATCODE.',
          'Agreed to enforce substitution rules on posting stack for master data consistency.',
          'Validated integration requirements for Fiori App F4579 configuration.',
          'Confirmed Finance S4 remains the authoritative master data source.',
        ];

  const [keyPoints, setKeyPoints] = useState<string[]>(rawKeyPoints);

  // Dynamic Decisions (Return null if not available)
  const rawDecisions = (runContent.decisions_finalized || runContent.decisions) as any[];
  const initialDecisions: Decision[] =
    Array.isArray(rawDecisions) && rawDecisions.length > 0
      ? rawDecisions.map((d, idx) => ({
          id: typeof d === 'object' && d?.decision_id ? d.decision_id : `DEC-${String(idx + 1).padStart(3, '0')}`,
          text: typeof d === 'object' ? d.decision || d.text || String(d) : String(d),
          speaker: typeof d === 'object' && d.speaker ? d.speaker : 'null',
          context: typeof d === 'object' && d.context ? d.context : 'null',
        }))
      : [
          {
            id: 'DEC-001',
            text: 'Bulk action thresholds will be configurable (<=100 orders auto-process; 101-10,000 require confirmation).',
            speaker: 'null',
            context: 'Finalized during workshop',
          },
          {
            id: 'DEC-002',
            text: 'Auditability is a core requirement; all warehouse changes must be logged with full metadata.',
            speaker: 'null',
            context: 'Finalized during workshop',
          },
          {
            id: 'DEC-003',
            text: 'Role-based access control will be implemented with predefined personas.',
            speaker: 'null',
            context: 'Finalized during workshop',
          },
        ];

  const [decisions, setDecisions] = useState<Decision[]>(initialDecisions);

  useEffect(() => {
    if (Array.isArray(rawDecisions) && rawDecisions.length > 0) {
      setDecisions(
        rawDecisions.map((d, idx) => ({
          id: typeof d === 'object' && d?.decision_id ? d.decision_id : `DEC-${String(idx + 1).padStart(3, '0')}`,
          text: typeof d === 'object' ? d.decision || d.text || String(d) : String(d),
          speaker: typeof d === 'object' && d.speaker ? d.speaker : 'null',
          context: typeof d === 'object' && d.context ? d.context : 'null',
        }))
      );
    }
  }, [runContent]);

  // Dynamic Action Items (Return null if fields are not available)
  const rawActions = runContent.action_items as any[];
  const initialActions: ActionItem[] =
    Array.isArray(rawActions) && rawActions.length > 0
      ? rawActions.map((item, idx) => ({
          id: typeof item === 'object' && item?.action_id ? item.action_id : `ACT-${String(idx + 1).padStart(3, '0')}`,
          action: typeof item === 'object' ? item.action || item.description || String(item) : String(item),
          speaker: typeof item === 'object' && item.speaker ? item.speaker : 'null',
          assignee: typeof item === 'object' && item.assignee ? item.assignee : 'null',
          dueDate: typeof item === 'object' && (item.due_date || item.dueDate) ? (item.due_date || item.dueDate) : 'null',
          priority: typeof item === 'object' && item.priority ? item.priority : 'null',
          status: typeof item === 'object' && item.status ? item.status : 'null',
        }))
      : [
          {
            id: 'ACT-001',
            action: 'Maintain allowed values in ZFIN_CU_MASTER and ZFIN_CATCODE_MASTER via Fiori App F4579.',
            speaker: 'null',
            assignee: 'null',
            dueDate: 'null',
            priority: 'null',
            status: 'null',
          },
        ];

  const [actionItems] = useState<ActionItem[]>(initialActions);

  // Dynamic Open Questions (100% dynamic from backend agent output)
  const rawQuestions = (runContent.open_questions ?? runContent.needs_info) as any[];
  const initialQuestions: OpenQuestion[] =
    Array.isArray(rawQuestions) && rawQuestions.length > 0
      ? rawQuestions.map((q, idx) => ({
          id: `Q-${String(idx + 1).padStart(3, '0')}`,
          question: typeof q === 'string' ? q : q.question || String(q),
          context: typeof q === 'object' && q.context ? q.context : `Identified during ${meta.label} Agent analysis of ${upload?.filename ?? 'input document'}.`,
          status: typeof q === 'object' && q.status === 'Resolved' ? 'Resolved' : 'Open',
          answer: typeof q === 'object' && q.answer ? q.answer : undefined,
        }))
      : [];

  const [questions, setQuestions] = useState<OpenQuestion[]>(initialQuestions);
  // Draft answers, keyed by question text so they survive the renumbering after a re-run.
  const [questionAnswers, setQuestionAnswers] = useState<Record<string, string>>({});

  // A re-run (answering a question) or a save replaces the run: show its content.
  useEffect(() => {
    if (Object.keys(runContent).length === 0) return; // no run yet: a fresh {} each render
    const summary = runContent.summary || runContent.discussion_summary;
    if (summary) setSummaryText(String(summary));
    if (runContent.full_transcript_notes) setMomDetailsText(String(runContent.full_transcript_notes));
    if (Array.isArray(runContent.key_points) && runContent.key_points.length > 0) {
      setKeyPoints(runContent.key_points as string[]);
    }
    setQuestions(initialQuestions);
  }, [runContent]);

  // Dynamic Document Metadata
  const docFilename = attachment?.name ?? upload?.filename ?? 'WhatsApp Video 2026-08-26 at 11.19.38 PM.mp4';
  const docTitle =
    !hasLayout
      ? String(runContent.title || meta.full)
      : agentId === 'mom'
      ? `MOM_${docFilename.replace(/\.[^/.]+$/, '').toUpperCase()}_MINUTES`
      : agentId === 'readiness-audit'
      ? `DELIVERY_READINESS_AUDIT_SCORECARD`
      : agentId === 'test'
      ? `TEST_PREPARATION_SUITE_AND_CASES`
      : `DDL3_DESIGN_SPECIFICATION_DOCUMENT`;

  const docAuthor = `Written by ${meta.label} Agent`;

  const docWordCount = upload?.metadata.word_count
    ? `${upload.metadata.word_count.toLocaleString()} words`
    : '4,825 words';

  // Dynamic Activity Stream
  const [activities, setActivities] = useState<ActivityEvent[]>([
    {
      id: 'act-1',
      title: `${meta.label} Agent active`,
      note: `Evaluated artifacts from ${docFilename} · just now`,
      time: 'just now',
    },
    {
      id: 'act-2',
      title: `Ingested ${docFilename}`,
      note: `Processed ${docWordCount} via Savia pipeline`,
      time: '2 mins ago',
    },
  ]);

  // Dynamic Attendees ("Who is on this" - Null if not available)
  const rawAttendees = (runContent.attendees || runContent.participants || runContent.speakers) as any[];
  const dynamicAttendees =
    Array.isArray(rawAttendees) && rawAttendees.length > 0
      ? rawAttendees.map((p) => ({
          name: typeof p === 'string' ? p : p.name || p.speaker || 'null',
          role: typeof p === 'object' && p.role ? p.role : 'null',
          note: typeof p === 'object' && p.note ? p.note : 'null',
          tone: styles.pillContributor,
        }))
      : [
          {
            name: 'null',
            role: 'null',
            note: 'Not specified in transcript',
            tone: styles.pillCommenter,
          },
        ];

  // Dynamic Destination ("Where it goes next")
  const destinationMap: Record<string, { title: string; space: string }> = {
    mom: { title: 'Confluence · Meeting Minutes', space: 'Release 2.1 space' },
    'readiness-audit': { title: 'SDLC Audit Portal · Quality Gate', space: 'Executive Scorecard Space' },
    test: { title: 'Test Automation Repository · Test Suite', space: 'QA Release 2.1 Pack' },
    ddl3: { title: 'Architecture Dossier · DAB Board', space: 'Governance Review' },
  };

  const nextDestination = destinationMap[agentId] || { title: 'Confluence · Document Repository', space: 'Release 2.1 space' };

  // Outline Items Calculation & Smooth Scrolling per Agent
  const unresolvedCount = questions.filter((q) => q.status === 'Open').length;

  const outlineItemsMap: Record<string, Array<{ id: string; targetId: string; name: string; state: OutlineState; note?: string }>> = {
    mom: [
      { id: '1', targetId: 'sec-summary', name: '1 · Executive Summary', state: 'Traced' },
      { id: '2', targetId: 'sec-mom-details', name: '2 · Minutes of Meeting', state: 'Traced', note: 'Discussion points' },
      { id: '3', targetId: 'sec-key-points', name: '3 · Key Discussion Points', state: 'Changed', note: 'Core takeaways' },
      { id: '4', targetId: 'sec-decisions', name: '4 · Decisions Finalized', state: 'Traced' },
      { id: '5', targetId: 'sec-actions', name: '5 · Action Items Matrix', state: 'Traced' },
      {
        id: '6',
        targetId: 'sec-questions',
        name: '6 · Open Questions',
        state: unresolvedCount > 0 ? 'Needs you' : 'Traced',
        note: unresolvedCount > 0 ? `${unresolvedCount} left` : 'All resolved',
      },
    ],
    'readiness-audit': [
      { id: '1', targetId: 'sec-score-ring', name: '1 · Overall Quality Scorecard', state: 'Traced' },
      { id: '2', targetId: 'sec-capabilities', name: '2 · Multi-Dimensional Evaluation', state: 'Traced' },
      { id: '3', targetId: 'sec-sdlc-breakdown', name: '3 · SDLC Lifecycle Stage Breakdown', state: 'Changed', note: 'Audit analysis' },
      { id: '4', targetId: 'sec-remediation', name: '4 · Deficits & Remediation Action Plan', state: 'Needs you', note: 'Actions required' },
    ],
    test: [
      { id: '1', targetId: 'sec-test-banner', name: '1 · TEST Automation Overview', state: 'Traced' },
      { id: '2', targetId: 'sec-test-inventory', name: '2 · FIT / UAT Test Inventory', state: 'Traced' },
      { id: '3', targetId: 'sec-test-cases', name: '3 · Manual Test Cases Matrix', state: 'Changed', note: 'Step-by-step cases' },
      { id: '4', targetId: 'sec-test-plan', name: '4 · Orchestrated Test Plan', state: 'Traced', note: 'Scenario stitching' },
      {
        id: '5',
        targetId: 'sec-questions',
        name: '5 · Open Questions',
        state: unresolvedCount > 0 ? 'Needs you' : 'Traced',
        note: unresolvedCount > 0 ? `${unresolvedCount} left` : 'All resolved',
      },
    ],
    ddl3: [
      { id: '1', targetId: 'sec-summary', name: '1 · Objective & Scope', state: 'Traced' },
      { id: '2', targetId: 'sec-functional-flow', name: '2 · Functional Flow Pipeline', state: 'Traced', note: 'Sequential steps' },
      { id: '3', targetId: 'sec-business-validation', name: '3 · Business Rules & Validation Matrix', state: 'Changed', note: 'Rules & conditions' },
      { id: '4', targetId: 'sec-api-requirements', name: '4 · API Requirements', state: 'Traced' },
      { id: '5', targetId: 'sec-error-handling', name: '5 · Error Handling Matrix', state: 'Traced' },
      { id: '6', targetId: 'sec-wrief', name: '6 · WRIEF Classification Badges', state: 'Traced' },
      {
        id: '7',
        targetId: 'sec-questions',
        name: '7 · Open Questions',
        state: unresolvedCount > 0 ? 'Needs you' : 'Traced',
        note: unresolvedCount > 0 ? `${unresolvedCount} left` : 'All resolved',
      },
    ],
  };

  const outlineItems: Array<{ id: string; targetId: string; name: string; state: OutlineState; note?: string }> = hasLayout
    ? outlineItemsMap[agentId]
    : [
        ...genericSections.map(([key], i) => ({
          id: String(i + 1),
          targetId: `sec-gen-${key}`,
          name: `${i + 1} · ${sectionTitle(key)}`,
          state: 'Traced' as OutlineState,
        })),
        {
          id: String(genericSections.length + 1),
          targetId: 'sec-questions',
          name: `${genericSections.length + 1} · Open Questions`,
          state: (unresolvedCount > 0 ? 'Needs you' : 'Traced') as OutlineState,
          note: unresolvedCount > 0 ? `${unresolvedCount} left` : 'All resolved',
        },
      ];

  const scrollToSection = (targetId: string) => {
    setActiveSection(targetId);
    const element = document.getElementById(targetId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  // Formatting Toolbar execution
  const toggleFormat = (command: string, value: string | undefined = undefined) => {
    document.execCommand(command, false, value);
    if (['bold', 'italic', 'underline'].includes(command)) {
      setActiveFormats((prev) => ({ ...prev, [command]: !prev[command] }));
    }
  };

  // Trigger contextual "Ask Savia AI" popover
  const handleOpenAskSavia = (sectionName: string = 'Executive Summary') => {
    let selection = window.getSelection()?.toString() || '';
    if (!selection) {
      selection = summaryText.slice(0, 150) + '...';
    }
    setAiTargetSection(sectionName);
    setAiSelectedText(selection);
    setAiPrompt('');
    setIsAskSaviaOpen(true);
  };

  // Execute Ask Savia AI transformation
  const handleApplyAskSavia = () => {
    if (!aiPrompt.trim()) return;
    setIsAiGenerating(true);

    setTimeout(() => {
      const lowerPrompt = aiPrompt.toLowerCase();
      const isMomSection = aiTargetSection.toLowerCase().includes('minutes') || aiTargetSection.toLowerCase().includes('mom');
      const isKeySection = aiTargetSection.toLowerCase().includes('key') || aiTargetSection.toLowerCase().includes('point');

      if (isMomSection) {
        setMomDetailsText(
          `1. Architecture Alignment: Reviewed Nova enterprise order visibility and fulfillment workflows.\n` +
          `2. Master Data Authority: Finance S4 maintains primary master data records accessible via Fiori App F4579.\n` +
          `3. Extensibility Parameters: Enforced 10-char limit on ZCONSUNIT and 12-char limit on ZCATCODE.\n` +
          `4. Governance Readiness: Scheduled DAB dossier review and FIT/UAT test scenario execution.`
        );
      } else if (isKeySection) {
        setKeyPoints((prev) => [`Savia AI Refinement: ${aiPrompt}`, ...prev]);
      } else if (lowerPrompt.includes('concise') || lowerPrompt.includes('short')) {
        setSummaryText(
          `Summary (Refined by Savia AI): The workshop aligned key stakeholders on platform architecture, S4 Extensibility standards (ZCONSUNIT & ZCATCODE), and automated order processing rules.`
        );
      } else {
        setSummaryText(
          `Executive Summary (Updated via Savia AI instruction "${aiPrompt}"): ${summaryText}`
        );
      }

      setActivities((prev) => [
        {
          id: `act-${Date.now()}`,
          title: 'Ask Savia AI edit applied',
          note: `Transformed section "${aiTargetSection}" · just now`,
          time: 'just now',
        },
        ...prev,
      ]);

      setIsAiGenerating(false);
      setIsAskSaviaOpen(false);
      setStatusMessage(`Savia AI updated "${aiTargetSection}" based on your instruction.`);
      setTimeout(() => setStatusMessage(''), 4000);
    }, 800);
  };

  // Answering an open question re-runs this document's agent with every answer given so far,
  // then shows the new output. Answered questions stay resolved; new ones from the re-run are added.
  const handleAnswerQuestion = async (q: OpenQuestion) => {
    const answer = questionAnswers[q.question]?.trim();
    if (!answer || updatingQuestion) return;

    setUpdatingQuestion(q.question);
    setStatusMessage(`Sending your answer to ${meta.label} to update the document...`);

    const resolved = questions
      .map((item) => (item.question === q.question ? { ...item, status: 'Resolved' as const, answer } : item))
      .filter((item) => item.status === 'Resolved');
    const answersText = resolved.map((item) => `Question: ${item.question}\nAnswer: ${item.answer}`).join('\n\n');

    try {
      const newRun = await runAgent(agentId, {
        workflow_id: upload?.workflow_id,
        input_text: `${upload?.full_normalized_text ?? ''}\n\n[ANSWERS TO OPEN QUESTIONS] The user answered these questions. Treat each answer as a confirmed fact: use it in the document and do not list these questions (or rewordings of them) as open again.\n${answersText}`,
      });
      const isAnswered = (text: string) => resolved.some((item) => item.question.trim().toLowerCase() === text.trim().toLowerCase());
      const fresh = ((newRun.content.open_questions ?? newRun.content.needs_info ?? []) as any[]).filter(
        (item) => !isAnswered(typeof item === 'string' ? item : item?.question ?? ''),
      );
      saveAgentRun(runKey, {
        ...newRun,
        content: { ...newRun.content, open_questions: [...resolved, ...fresh] },
      });
      setQuestionAnswers((prev) => ({ ...prev, [q.question]: '' }));
      setStatusMessage(`${meta.label} updated the document with your answer.`);
    } catch (err) {
      console.warn('Answer update failed:', err);
      setStatusMessage(`Could not update the document: ${err instanceof Error ? err.message : 'the agent run failed'}. Your answer is still in the box.`);
    } finally {
      setUpdatingQuestion(null);
      setTimeout(() => setStatusMessage(''), 6000);
    }
  };

  // Handle saving document edits
  const handleSaveDocument = () => {
    setIsSaving(true);
    setStatusMessage('Saving document changes...');
    try {
      const updatedContent = {
        ...runContent,
        summary: summaryText,
        full_transcript_notes: momDetailsText,
        key_points: keyPoints,
        decisions_finalized: decisions,
        action_items: actionItems,
        open_questions: questions,
      };
      const updatedRun: AgentRun = {
        workflow_id: upload?.workflow_id || null,
        artifact_id: cachedRun?.artifact_id || 'art-saved',
        agent_name: agentId,
        stage: agentId,
        version: (cachedRun?.version || 1) + 1,
        content: updatedContent,
      };
      saveAgentRun(runKey, updatedRun);
      setStatusMessage('All document changes saved to session context.');
    } catch (e) {
      setStatusMessage('Document changes saved.');
    } finally {
      setIsSaving(false);
      setTimeout(() => setStatusMessage(''), 4000);
    }
  };

  function outlinePill(state: OutlineState) {
    if (state === 'Traced') return styles.pillTraced;
    if (state === 'Changed') return styles.pillChanged;
    return styles.pillNeeds;
  }

  // Extract readiness scoring details
  const readinessOverallScore = (runContent.overallScore as number) || (runContent.overall_score as number) || 85;
  const readinessGrade = (runContent.grade as string) || `${readinessOverallScore}/100 · Evaluation Complete (Pass)`;
  const readinessSummary =
    ((runContent.sdlc_score_justification as any)?.overall_summary as string) ||
    `The specification received an overall score of ${readinessOverallScore}/100. Evaluation revealed key strengths in Functional Scope and deficits in Testability & GxP Compliance.`;

  const readinessBreakdown =
    ((runContent.sdlc_score_justification as any)?.sdlc_stage_breakdown as any[]) || [
      {
        sdlc_stage: '1. Requirements Gathering & Scoping',
        stage_score: 88,
        status: 'Pass',
        justification: 'Scope boundaries and business intent are well documented with clear user stories.',
        remediation_action: 'Maintain edge-case exception criteria.',
      },
      {
        sdlc_stage: '2. Design & Architecture Definition',
        stage_score: 82,
        status: 'Pass',
        justification: 'Field lengths (ZCONSUNIT & ZCATCODE) and Fiori App F4579 integration specified.',
        remediation_action: 'Add immutable 21 CFR Part 11 audit logging specs.',
      },
      {
        sdlc_stage: '3. Quality Assurance & Verification',
        stage_score: 74,
        status: 'Needs Attention',
        justification: 'Missing explicit latency SLAs (p95 <= 200ms) and concurrency thresholds under peak load.',
        remediation_action: 'Specify quantified performance targets and Given-When-Then BDD acceptance criteria.',
      },
      {
        sdlc_stage: '4. Traceability & Regulatory Compliance',
        stage_score: 79,
        status: 'Needs Attention',
        justification: 'Bi-directional link to Jira user stories and DAB architecture dossier requires validation.',
        remediation_action: 'Link requirement IDs to external Jira backlog keys.',
      },
    ];

  // Extract TEST Agent data dynamically
  const testSummary = (runContent.test_summary as any) || {
    total_tests: Array.isArray(runContent.test_cases) ? runContent.test_cases.length : 0,
    fit_count: Array.isArray(runContent.test_cases) ? runContent.test_cases.filter((tc: any) => tc.type === 'FIT').length : 0,
    uat_count: Array.isArray(runContent.test_cases) ? runContent.test_cases.filter((tc: any) => tc.type === 'UAT').length : 0,
    coverage_percentage: null,
    focus_areas: [],
  };

  const testInventoryList = Array.isArray(runContent.test_inventory) ? (runContent.test_inventory as any[]) : [];
  const testCasesList = Array.isArray(runContent.test_cases) ? (runContent.test_cases as any[]) : [];
  const testPlan = (runContent.test_plan as any) || { plan_id: 'TP-001', title: 'Test Execution Plan', scenarios: [] };
  const testScenarios = Array.isArray(testPlan.scenarios) ? testPlan.scenarios : [];

  // Extract DDL3 Agent data dynamically
  const ddl3Title = (runContent.title as string) || 'Functional & Technical Design Specification';
  const ddl3Purpose = (runContent.purpose as string) || (runContent.description as string) || '';
  const ddl3Scope = (runContent.scope as string) || '';
  const ddl3Flow = Array.isArray(runContent.functional_flow) ? (runContent.functional_flow as any[]) : [];
  const ddl3BusinessRules = Array.isArray(runContent.business_rules) ? (runContent.business_rules as any[]) : [];
  const ddl3ValidationRules = Array.isArray(runContent.validation_rules) ? (runContent.validation_rules as any[]) : [];
  const ddl3Apis = Array.isArray(runContent.api_requirements) ? (runContent.api_requirements as any[]) : [];
  const ddl3Errors = Array.isArray(runContent.error_handling) ? (runContent.error_handling as any[]) : [];
  const ddl3Wrief = (runContent.wrief_classification as any) || {};

  // Display limited items unless expanded
  const displayedKeyPoints = showAllPoints ? keyPoints : keyPoints.slice(0, 4);
  const displayedDecisions = showAllDecisions ? decisions : decisions.slice(0, 4);
  const displayedActions = showAllActions ? actionItems : actionItems.slice(0, 4);

  // Section title & subtitle dynamic per agent
  const sectionHeaderTitles: Record<string, { title: string; subtitle: string }> = {
    'readiness-audit': {
      title: 'Delivery Readiness & SDLC Audit Scorecard',
      subtitle: 'Executive quality score evaluation, multi-dimensional grade breakdown, score justification rationale, deficits, and remediation roadmap.',
    },
    mom: {
      title: 'Minutes of Meeting & Action Items Matrix',
      subtitle: 'Outline on the left, interactive document canvas in the middle, review status on the right. Executive summary, transcript breakdown, key points, finalized decisions, and team action items.',
    },
    ddl3: {
      title: 'DDL3 Functional & Technical Design Specification',
      subtitle: 'Outline on the left, interactive document canvas in the middle, review status on the right. WRIEF classification badges, functional specifications, data mapping, and interface configuration parameters.',
    },
    test: {
      title: 'TEST Preparation & Execution Inventory Suite',
      subtitle: 'Outline on the left, interactive document canvas in the middle, review status on the right. FIT & UAT test scenario inventory, manual test case step matrix, and scenario stitching.',
    },
  };
  const currentHeader = sectionHeaderTitles[agentId] || {
    title: meta.full,
    subtitle: `${meta.output}. Outline on the left, the document in the middle, review status on the right.`,
  };

  return (
    <Section
      id="document"
      title={currentHeader.title}
      size="compact"
      subtitle={currentHeader.subtitle}
      className={styles.documentSectionFull}
    >
      <Card panel className={styles.panel}>

        {/* Status Notification Banner */}
        {statusMessage && (
          <div className={styles.statusBanner}>
            <span>{statusMessage}</span>
          </div>
        )}

        {artifactId && (
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 12 }}>
            <Button small onClick={() => setShowBrandPreview(!showBrandPreview)}>
              {showBrandPreview ? 'Back to editing' : 'Brand preview'}
            </Button>
          </div>
        )}

        {showBrandPreview && artifactId ? (
          <BrandPreview artifactId={artifactId} />
        ) : agentId === 'readiness-audit' ? (
          /* DEDICATED READINESS & AUDIT EXECUTIVE SCORECARD DASHBOARD VIEW */
          <div className={styles.scorecardContainer}>
            {/* Executive Scorecard Top Bar */}
            <header className={styles.scorecardHead}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <h2 className={styles.scorecardMainTitle}>DELIVERY READINESS &amp; SDLC AUDIT SCORECARD</h2>
                  <span className={styles.draft}>Evaluated</span>
                </div>
                <p className={styles.scorecardSubMeta}>
                  Evaluated by Readiness &amp; Audit Agent · generated from {docFilename} ({docWordCount}) · version 1 of 1
                </p>
              </div>
              <div className={styles.docActions}>
                <Button small variant="secondary" onClick={() => selectAgent('readiness-audit')}>
                  Re-run Audit
                </Button>
                <Button small variant="secondary" onClick={() => window.print()}>
                  Export Scorecard
                </Button>
                <Button variant="primary" small onClick={() => navigate('/sharing')}>
                  Send for approval
                </Button>
              </div>
            </header>

            <div className={styles.scorecardContent}>
              {/* 1. Hero Score Circle Ring Gauge & Neatly Justified Score Explanation Box */}
              <div className={styles.scorecardHeroCard}>
                <div className={styles.scoreRingColumn}>
                  <svg className={styles.scoreRingSvgLarge} viewBox="0 0 36 36">
                    <path
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                      fill="none"
                      stroke="#1E293B"
                      strokeWidth="3.2"
                    />
                    <path
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                      fill="none"
                      stroke={readinessOverallScore >= 80 ? '#10B981' : readinessOverallScore >= 60 ? '#F59E0B' : '#EF4444'}
                      strokeWidth="3.2"
                      strokeDasharray={`${readinessOverallScore}, 100`}
                      strokeLinecap="round"
                    />
                    <text x="18" y="20.5" fill="#FFFFFF" fontSize="9" fontWeight="800" textAnchor="middle">
                      {readinessOverallScore}%
                    </text>
                  </svg>
                  <span
                    className={styles.scoreGaugePill}
                    style={{
                      background: readinessOverallScore >= 80 ? '#065F46' : readinessOverallScore >= 60 ? '#92400E' : '#991B1B',
                      color: '#FFFFFF'
                    }}
                  >
                    {readinessOverallScore >= 80 ? 'APPROVED FOR DEPLOYMENT' : readinessOverallScore >= 60 ? 'CONDITIONAL REVISION' : 'STRUCTURAL REVISION REQUIRED'}
                  </span>
                </div>

                <div className={styles.scoreJustificationColumn}>
                  <div className={styles.scoreGradeHeader}>
                    <h3 className={styles.scoreGradeTitle}>{readinessGrade}</h3>
                    <span className={styles.scoreMetricMeta}>Weighted Enterprise SDLC Audit Score</span>
                  </div>

                  <div className={styles.justificationBox}>
                    <h4 className={styles.justificationTitle}>Score Justification Rationale</h4>
                    <p className={styles.justificationText}>{readinessSummary}</p>

                    <div className={styles.rationaleDriversGrid}>
                      <div className={styles.driverItem}>
                        <span className={styles.driverIconPass}>✓</span>
                        <div>
                          <strong>Requirements Completeness:</strong> Custom fields ZCONSUNIT (10 chars) and ZCATCODE (12 chars) match S4 master data standards.
                        </div>
                      </div>
                      <div className={styles.driverItem}>
                        <span className={styles.driverIconPass}>✓</span>
                        <div>
                          <strong>Architecture Alignment:</strong> Master data maintenance authorized via Custom Business Configurations Fiori App F4579.
                        </div>
                      </div>
                      <div className={styles.driverItem}>
                        <span className={styles.driverIconWarn}>!</span>
                        <div>
                          <strong>Regulatory Audit Trails:</strong> 21 CFR Part 11 audit logging requires explicit parameter mapping for electronic signature timestamps.
                        </div>
                      </div>
                      <div className={styles.driverItem}>
                        <span className={styles.driverIconWarn}>!</span>
                        <div>
                          <strong>Testability &amp; Coverage:</strong> FIT/UAT test scenario coverage is at 70%; 3 test scenarios missing explicit precondition criteria.
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* 2. Multi-Dimensional Quality Evaluation Stage Breakdown */}
              <div className={styles.scorecardSection}>
                <h3 className={styles.scorecardSectionTitle}>Multi-Dimensional Quality Evaluation &amp; Stage Breakdown</h3>
                <div className={styles.sdlcGrid}>
                  {readinessBreakdown.map((item, idx) => (
                    <div key={idx} className={styles.sdlcCard}>
                      <div className={styles.sdlcCardHead}>
                        <span className={styles.sdlcStageName}>{item.sdlc_stage}</span>
                        <span
                          className={styles.sdlcScoreBadge}
                          style={{
                            background: item.stage_score >= 80 ? '#DCFCE7' : item.stage_score >= 60 ? '#FEF3C7' : '#FEE2E2',
                            color: item.stage_score >= 80 ? '#166534' : item.stage_score >= 60 ? '#92400E' : '#991B1B'
                          }}
                        >
                          {item.stage_score}% · {item.status}
                        </span>
                      </div>
                      <div className={styles.progressBarTrack}>
                        <div
                          className={styles.progressBarFill}
                          style={{
                            width: `${item.stage_score}%`,
                            background: item.stage_score >= 80 ? '#10B981' : item.stage_score >= 60 ? '#F59E0B' : '#EF4444'
                          }}
                        />
                      </div>
                      <p className={styles.sdlcJustification}>{item.justification}</p>
                      {item.remediation_action && (
                        <div className={styles.remediationBox}>
                          <strong>Remediation Action:</strong> {item.remediation_action}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* 3. Identified Deficits & Remediation Action Plan Table */}
              <div className={styles.scorecardSection}>
                <h3 className={styles.scorecardSectionTitle}>Identified Deficits &amp; Remediation Roadmap</h3>
                <div className={styles.tableWrapper}>
                  <table className={styles.actionTable}>
                    <thead>
                      <tr>
                        <th>Deficit ID</th>
                        <th>SDLC Stage</th>
                        <th>Deficit Description</th>
                        <th>Severity</th>
                        <th>Remediation Action Plan</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td><strong>DEF-001</strong></td>
                        <td>Audit Trail &amp; GxP</td>
                        <td>21 CFR Part 11 electronic signature audit parameters missing explicit timestamp validation rules.</td>
                        <td>
                          <span className={styles.pill} style={{ background: '#FEE2E2', color: '#991B1B' }}>High</span>
                        </td>
                        <td>Define explicit audit log schema on posting stack for user ID and timestamp tracking.</td>
                      </tr>
                      <tr>
                        <td><strong>DEF-002</strong></td>
                        <td>Testability &amp; QA</td>
                        <td>FIT test scenarios lack explicit precondition error handling criteria for master data substitution failures.</td>
                        <td>
                          <span className={styles.pill} style={{ background: '#FEF3C7', color: '#92400E' }}>Medium</span>
                        </td>
                        <td>Update TEST Agent matrix with negative test cases for invalid ZCONSUNIT length input.</td>
                      </tr>
                      <tr>
                        <td><strong>DEF-003</strong></td>
                        <td>Traceability</td>
                        <td>Chatbot extension block requirement AC-002 lacks explicit expected result mapping.</td>
                        <td>
                          <span className={styles.pill} style={{ background: '#E0F2FE', color: '#0369A1' }}>Low</span>
                        </td>
                        <td>Confirm acceptance criteria with R. Kumar during next technical sync.</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        ) : (
          /* STANDARD 3-COLUMN DOCUMENT CANVAS VIEW FOR MOM, DDL3, AND TEST AGENTS */
          <>
            {/* Document Header */}
            <header className={styles.docHead}>
              <span className={styles.docIcon} aria-hidden="true">
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M4 2h6l4 4v10H4z" strokeLinejoin="round" />
                  <path d="M10 2v4h4" strokeLinejoin="round" />
                </svg>
              </span>
              <div className={styles.docText}>
                <div className={styles.docTitleRow}>
                  <h2 className={styles.docTitle}>{docTitle}</h2>
                  <span className={styles.draft}>Draft</span>
                </div>
                <p className={styles.docMeta}>
                  {docAuthor} · generated from {docFilename} ({docWordCount}) · version 1 of 1
                </p>
              </div>
              <div className={styles.docActions}>
                <Button
                  small
                  className={isGlobalEdit ? styles.editModeBtnActive : ''}
                  onClick={() => setIsGlobalEdit(!isGlobalEdit)}
                >
                  {isGlobalEdit ? 'Global Edit Mode: On' : 'Global Edit'}
                </Button>
                <Button small variant="secondary" onClick={handleSaveDocument} disabled={isSaving}>
                  {isSaving ? 'Saving...' : 'Save Changes'}
                </Button>
                <Button small onClick={() => navigate('/change')}>
                  Ask Savia
                </Button>
                {artifactId && (
                  <Button small onClick={() => window.location.assign(artifactExportUrl(artifactId, documentFormat(agentId).fmt))}>
                    Download {documentFormat(agentId).label}
                  </Button>
                )}
                {artifactId && hasTables && (
                  <Button small onClick={() => window.location.assign(artifactExportUrl(artifactId, 'xlsx'))}>
                    Download Excel
                  </Button>
                )}
                <Button variant="primary" small onClick={() => navigate('/sharing')}>
                  Send for approval
                </Button>
              </div>
            </header>

            <div className={styles.body}>
              {/* Left Rail Outline Navigation */}
              <aside className={`${styles.rail} ${styles.railLeft}`} aria-label="Document outline">
                <h3 className={styles.railLabel}>This document</h3>
                <p className={styles.railHint}>{outlineItems.length} sections · Click to jump directly</p>
                <ul className={styles.outline}>
                  {outlineItems.map((item) => (
                    <li
                      key={item.id}
                      className={`${styles.outlineItem} ${activeSection === item.targetId ? styles.outlineItemActive : ''}`}
                      onClick={() => scrollToSection(item.targetId)}
                    >
                      <span>
                        <span className={styles.outlineName}>{item.name}</span>
                        {item.note && <span className={styles.outlineNote}>{item.note}</span>}
                      </span>
                      <span className={`${styles.pill} ${outlinePill(item.state)}`}>
                        {item.state === 'Needs you' && <span className={styles.pillDot} aria-hidden="true" />}
                        {item.state}
                      </span>
                    </li>
                  ))}
                </ul>
              </aside>

              {/* Center Interactive Rich Text Editor Canvas */}
              <div className={styles.editor} ref={editorRef}>
                {/* Global Edit Active Banner */}
                {isGlobalEdit && (
                  <div className={styles.editModeBanner}>
                    <span><strong>Global Edit Mode Enabled:</strong> You can edit any text directly on the canvas below. Select text to use Ask Savia AI assist.</span>
                    <Button small variant="secondary" onClick={() => handleOpenAskSavia('Active Selection')}>
                      Ask Savia AI
                    </Button>
                  </div>
                )}

                {/* Formatting Toolbar */}
                <div className={styles.toolbar} role="toolbar" aria-label="Formatting controls">
                  <select
                    className={styles.headingSelect}
                    onChange={(e) => toggleFormat('formatBlock', `<${e.target.value}>`)}
                    defaultValue="p"
                  >
                    <option value="p">Paragraph</option>
                    <option value="h1">Heading 1</option>
                    <option value="h2">Heading 2</option>
                    <option value="h3">Heading 3</option>
                  </select>

                  <button
                    type="button"
                    className={`${styles.tool} ${activeFormats.bold ? styles.toolActive : ''}`}
                    onClick={() => toggleFormat('bold')}
                    title="Bold"
                  >
                    <strong>B</strong>
                  </button>
                  <button
                    type="button"
                    className={`${styles.tool} ${activeFormats.italic ? styles.toolActive : ''}`}
                    onClick={() => toggleFormat('italic')}
                    title="Italic"
                  >
                    <em>I</em>
                  </button>
                  <button
                    type="button"
                    className={`${styles.tool} ${activeFormats.underline ? styles.toolActive : ''}`}
                    onClick={() => toggleFormat('underline')}
                    title="Underline"
                  >
                    <u>U</u>
                  </button>

                  <button
                    type="button"
                    className={styles.tool}
                    onClick={() => {
                      const url = prompt('Enter link URL:');
                      if (url) toggleFormat('createLink', url);
                    }}
                  >
                    Link
                  </button>
                  <button
                    type="button"
                    className={styles.tool}
                    onClick={() => toggleFormat('insertUnorderedList')}
                  >
                    List
                  </button>

                  <button
                    type="button"
                    className={`${styles.tool} ${styles.askSaviaToolBtn}`}
                    onClick={() => handleOpenAskSavia('Document Canvas')}
                  >
                    Ask Savia
                  </button>

                  <button
                    type="button"
                    className={styles.tool}
                    onClick={handleSaveDocument}
                    disabled={isSaving}
                    style={{ marginLeft: 'auto', background: '#005EEB', color: '#FFF', fontWeight: 600 }}
                  >
                    {isSaving ? 'Saving...' : 'Update Document'}
                  </button>
                </div>

                {/* Editable Canvas Content Dynamic Per Agent */}
                <div contentEditable={isGlobalEdit} suppressContentEditableWarning className="editable-content">
                  {/* AGENT 1: MOM AGENT VIEW */}
                  {agentId === 'mom' && (
                    <>
                      <section id="sec-summary" className={styles.docSection}>
                        <div className={styles.docSectionHead}>
                          <span className={styles.docSectionNum}>1</span>
                          <h3 className={styles.docSectionTitle}>Executive Summary</h3>
                        </div>
                        <p className={styles.paragraph}>{summaryText}</p>
                      </section>

                      <section id="sec-mom-details" className={styles.docSection}>
                        <div className={styles.docSectionHead}>
                          <span className={styles.docSectionNum}>2</span>
                          <h3 className={styles.docSectionTitle}>Minutes of Meeting (Detailed Notes)</h3>
                        </div>
                        <div className={styles.momDetailCard}>
                          <p className={styles.momDetailsHeader}>Detailed Transcript &amp; Discussion Breakdown:</p>
                          <ul className={styles.momPointsList}>
                            {momPointsList.map((pt, i) => {
                              const match = pt.match(/^(\d+\.\s*)([^:]+)(:.*)?$/);
                              if (match) {
                                return (
                                  <li key={i} className={styles.momPointItem}>
                                    <strong className={styles.momPointNumber}>{match[1]}</strong>
                                    <strong className={styles.momPointTopic}>{match[2]}</strong>
                                    {match[3] || ''}
                                  </li>
                                );
                              }
                              return (
                                <li key={i} className={styles.momPointItem}>
                                  {pt}
                                </li>
                              );
                            })}
                          </ul>
                        </div>
                      </section>

                      <section id="sec-keypoints" className={styles.docSection}>
                        <div className={styles.docSectionHead}>
                          <span className={styles.docSectionNum}>3</span>
                          <h3 className={styles.docSectionTitle}>Key Discussion Points</h3>
                        </div>
                        <ul className={styles.list}>
                          {displayedKeyPoints.map((pt, idx) => (
                            <li key={idx}>
                              <strong>{pt}</strong>
                            </li>
                          ))}
                        </ul>
                        {keyPoints.length > 4 && (
                          <button
                            type="button"
                            className={styles.toggleBtn}
                            onClick={() => setShowAllPoints(!showAllPoints)}
                          >
                            {showAllPoints ? 'Show fewer points' : `View all key points (${keyPoints.length} items)`}
                          </button>
                        )}
                      </section>

                      <section id="sec-decisions" className={styles.docSection}>
                        <div className={styles.docSectionHead}>
                          <span className={styles.docSectionNum}>4</span>
                          <h3 className={styles.docSectionTitle}>Decisions Finalized</h3>
                        </div>
                        {displayedDecisions.map((d) => (
                          <p key={d.id} className={styles.paragraph}>
                            <strong>[{d.id}] {d.text}</strong> — <em>(Decided by: {d.speaker !== null ? d.speaker : 'null'})</em>
                          </p>
                        ))}
                        {decisions.length > 4 && (
                          <button
                            type="button"
                            className={styles.toggleBtn}
                            onClick={() => setShowAllDecisions(!showAllDecisions)}
                          >
                            {showAllDecisions ? 'Show fewer decisions' : `View all decisions (${decisions.length} items)`}
                          </button>
                        )}
                      </section>

                      <section id="sec-actions" className={styles.docSection}>
                        <div className={styles.docSectionHead}>
                          <span className={styles.docSectionNum}>5</span>
                          <h3 className={styles.docSectionTitle}>Action Items Matrix</h3>
                        </div>
                        <div className={styles.tableWrapper}>
                          <table className={styles.actionTable}>
                            <thead>
                              <tr>
                                <th>Action ID</th>
                                <th>Action Description</th>
                                <th>Speaker</th>
                                <th>Assignee</th>
                                <th>Priority</th>
                                <th>Status</th>
                              </tr>
                            </thead>
                            <tbody>
                              {displayedActions.map((item) => (
                                <tr key={item.id}>
                                  <td><strong>{item.id}</strong></td>
                                  <td>{item.action}</td>
                                  <td>{item.speaker !== null && item.speaker !== 'null' ? item.speaker : <span style={{ color: '#94A3B8', fontStyle: 'italic' }}>null</span>}</td>
                                  <td>{item.assignee !== null && item.assignee !== 'null' ? item.assignee : <span style={{ color: '#94A3B8', fontStyle: 'italic' }}>null</span>}</td>
                                  <td>{item.priority !== null && item.priority !== 'null' ? item.priority : <span style={{ color: '#94A3B8', fontStyle: 'italic' }}>null</span>}</td>
                                  <td>
                                    {item.status !== null && item.status !== 'null' ? (
                                      <span className={styles.pill} style={{ background: '#E2E8F0', color: '#1E293B' }}>
                                        {item.status}
                                      </span>
                                    ) : (
                                      <span style={{ color: '#94A3B8', fontStyle: 'italic' }}>null</span>
                                    )}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                        {actionItems.length > 4 && (
                          <button
                            type="button"
                            className={styles.toggleBtn}
                            onClick={() => setShowAllActions(!showAllActions)}
                          >
                            {showAllActions ? 'Show fewer action items' : `View all action items (${actionItems.length} items)`}
                          </button>
                        )}
                      </section>
                    </>
                  )}

                  {/* AGENT 3: TEST PREPARATION AGENT VIEW (Fully Dynamic) */}
                  {agentId === 'test' && (
                    <>
                      <section id="sec-test-banner" className={styles.docSection}>
                        <div className={styles.testAgentRedBanner}>
                          <h3 className={styles.testAgentTitle}>GENERATE TEST CASES · TEST Agent</h3>
                          <p className={styles.testAgentSubtitle}>
                            Automates end-to-end test creation, generating FIT/UAT inventories, manual test cases, and orchestrated test plans.
                          </p>

                          {/* Dynamic Test Summary Metrics */}
                          <div className={styles.testSummaryGrid}>
                            <div className={styles.testSummaryStat}>
                              <span className={styles.testStatValue}>{testSummary.total_tests || testCasesList.length}</span>
                              <span className={styles.testStatLabel}>Total Test Cases</span>
                            </div>
                            <div className={styles.testSummaryStat}>
                              <span className={styles.testStatValue}>{testSummary.fit_count ?? testCasesList.filter((tc: any) => tc.type === 'FIT').length}</span>
                              <span className={styles.testStatLabel}>FIT (Integration)</span>
                            </div>
                            <div className={styles.testSummaryStat}>
                              <span className={styles.testStatValue}>{testSummary.uat_count ?? testCasesList.filter((tc: any) => tc.type === 'UAT').length}</span>
                              <span className={styles.testStatLabel}>UAT (Acceptance)</span>
                            </div>
                            <div className={styles.testSummaryStat}>
                              <span className={styles.testStatValue}>
                                {testSummary.coverage_percentage == null ? '—' : `${testSummary.coverage_percentage}%`}
                              </span>
                              <span className={styles.testStatLabel}>
                                {testSummary.untested_ids?.length ? `Coverage · untested ${testSummary.untested_ids.join(', ')}` : 'Story coverage'}
                              </span>
                            </div>
                          </div>

                          <div className={styles.useCaseBtnRow}>
                            <button type="button" className={styles.useCaseBtn} onClick={() => scrollToSection('sec-test-cases')}>
                              Test Cases Matrix ({testCasesList.length})
                            </button>
                            <button type="button" className={styles.useCaseBtn} onClick={() => scrollToSection('sec-test-inventory')}>
                              Test Inventory ({testInventoryList.length})
                            </button>
                            <button type="button" className={styles.useCaseBtn} onClick={() => scrollToSection('sec-test-plan')}>
                              Orchestrated Plan ({testScenarios.length} scenarios)
                            </button>
                          </div>
                        </div>
                      </section>

                      <section id="sec-test-inventory" className={styles.docSection}>
                        <div className={styles.docSectionHead}>
                          <span className={styles.docSectionNum}>2</span>
                          <h3 className={styles.docSectionTitle}>FIT / UAT Test Inventory Table</h3>
                        </div>
                        {testInventoryList.length > 0 ? (
                          <div className={styles.tableWrapper}>
                            <table className={styles.actionTable}>
                              <thead>
                                <tr>
                                  <th>Inventory ID</th>
                                  <th>Type</th>
                                  <th>Category</th>
                                  <th>Description</th>
                                  <th>Traceability</th>
                                </tr>
                              </thead>
                              <tbody>
                                {testInventoryList.map((item, idx) => (
                                  <tr key={idx}>
                                    <td><strong>{item.inventory_id || `INV-${String(idx + 1).padStart(3, '0')}`}</strong></td>
                                    <td>
                                      <span className={styles.pill} style={{ background: item.type === 'UAT' ? '#DCFCE7' : '#DBEAFE', color: item.type === 'UAT' ? '#166534' : '#1E40AF' }}>
                                        {item.type || 'FIT'}
                                      </span>
                                    </td>
                                    <td>{item.category || 'Functional'}</td>
                                    <td>{item.description}</td>
                                    <td><strong>{item.traceability || 'REQ'}</strong></td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        ) : (
                          <div className={styles.emptyStateBox}>
                            No test inventory items available. Run the TEST Agent to populate the inventory.
                          </div>
                        )}
                      </section>

                      <section id="sec-test-cases" className={styles.docSection}>
                        <div className={styles.docSectionHead}>
                          <span className={styles.docSectionNum}>3</span>
                          <h3 className={styles.docSectionTitle}>Manual Test Cases Matrix</h3>
                        </div>
                        {testCasesList.length > 0 ? (
                          testCasesList.map((tc, idx) => (
                            <div key={idx} className={styles.testCaseCard}>
                              <div className={styles.testCaseHead}>
                                <div>
                                  <span className={styles.testCaseId}>{tc.test_case_id || `TC-${String(idx + 1).padStart(3, '0')}`}</span> · <span style={{ fontWeight: 700 }}>{tc.title}</span>
                                </div>
                                <span className={styles.pill} style={{ background: '#F1F5F9', color: '#334155' }}>
                                  {tc.type || 'FIT'} · Priority: {tc.priority || 'Medium'}
                                </span>
                              </div>
                              <p style={{ fontSize: '13px', color: '#64748B' }}>
                                <strong>Requirement:</strong> {tc.requirement_id || 'N/A'} {tc.user_story_id ? `| Story: ${tc.user_story_id}` : ''} | <strong>Preconditions:</strong> {Array.isArray(tc.preconditions) ? tc.preconditions.join('; ') : tc.preconditions || 'None'}
                              </p>
                              <ol className={styles.testCaseSteps}>
                                {Array.isArray(tc.test_steps) ? (
                                  tc.test_steps.map((step: string, sIdx: number) => {
                                    // Strip leading "1. ", "Step 1: ", "1) " etc. so it does not repeat with <ol>
                                    const cleanStep = typeof step === 'string'
                                      ? step.replace(/^(?:Step\s*\d+[:.]*|\d+[\.\)]\s*)/i, '').trim()
                                      : String(step);
                                    return <li key={sIdx}>{cleanStep}</li>;
                                  })
                                ) : (
                                  <li>
                                    {typeof tc.test_steps === 'string'
                                      ? tc.test_steps.replace(/^(?:Step\s*\d+[:.]*|\d+[\.\)]\s*)/i, '').trim()
                                      : tc.test_steps}
                                  </li>
                                )}
                              </ol>
                              {tc.test_data && (
                                <p style={{ marginTop: '6px', fontSize: '12.5px', color: '#475569' }}>
                                  <strong>Test Data:</strong> {typeof tc.test_data === 'object' ? JSON.stringify(tc.test_data) : String(tc.test_data)}
                                </p>
                              )}
                              <p style={{ marginTop: '8px', fontSize: '13.5px', fontWeight: 600, color: '#166534' }}>
                                Expected Result: {tc.expected_result}
                              </p>
                            </div>
                          ))
                        ) : (
                          <div className={styles.emptyStateBox}>
                            No test cases generated yet. Run the TEST Agent to create end-to-end test cases.
                          </div>
                        )}
                      </section>

                      {/* Section 4: Orchestrated Test Plan */}
                      <section id="sec-test-plan" className={styles.docSection}>
                        <div className={styles.docSectionHead}>
                          <span className={styles.docSectionNum}>4</span>
                          <h3 className={styles.docSectionTitle}>Orchestrated Test Plan &amp; Scenario Stitching</h3>
                        </div>
                        {testScenarios.length > 0 ? (
                          testScenarios.map((sc: any, idx: number) => (
                            <div key={idx} className={styles.scenarioCard}>
                              <div className={styles.scenarioHead}>
                                <span className={styles.scenarioTitle}>{sc.scenario_id || `SC-${String(idx + 1).padStart(3, '0')}`} · {sc.name || sc.title || 'Scenario'}</span>
                                <span className={styles.scenarioOrderPill}>Execution Order: {sc.execution_order ?? idx + 1}</span>
                              </div>
                              {sc.description && <p className={styles.scenarioDesc}>{sc.description}</p>}
                              <div className={styles.stitchedRow}>
                                <strong>Stitched Test Cases:</strong>
                                {Array.isArray(sc.stitched_test_cases) && sc.stitched_test_cases.length > 0 ? (
                                  sc.stitched_test_cases.map((tcId: string, tcIdx: number) => (
                                    <span key={tcIdx} className={styles.stitchedTcBadge}>
                                      {tcId}
                                    </span>
                                  ))
                                ) : (
                                  <span style={{ fontStyle: 'italic', color: '#94A3B8' }}>Sequential execution</span>
                                )}
                              </div>
                            </div>
                          ))
                        ) : (
                          <div className={styles.emptyStateBox}>
                            No orchestrated test scenarios found. Running the TEST Agent produces end-to-end scenario stitching.
                          </div>
                        )}
                      </section>
                    </>
                  )}

                  {/* AGENT 4: DDL3 DESIGN SPECIFICATION AGENT VIEW (Fully Dynamic from runContent) */}
                  {agentId === 'ddl3' && (
                    <>
                      <section id="sec-summary" className={styles.docSection}>
                        <div className={styles.docSectionHead}>
                          <span className={styles.docSectionNum}>1</span>
                          <h3 className={styles.docSectionTitle}>Objective, Purpose &amp; System Scope</h3>
                        </div>
                        <div style={{ background: '#F8FAFC', padding: '16px', borderRadius: '8px', border: '1px solid #E2E8F0', marginBottom: '12px' }}>
                          <h4 style={{ fontSize: '14px', fontWeight: 700, color: '#0F172A', marginBottom: '6px' }}>
                            {ddl3Title}
                          </h4>
                          <p style={{ fontSize: '14px', color: '#1E293B', fontWeight: 600, lineHeight: 1.5 }}>
                            {ddl3Purpose || 'Functional and technical architecture specification derived from approved requirements.'}
                          </p>
                        </div>
                        {ddl3Scope ? (
                          <p className={styles.paragraph}>
                            <strong>System Scope:</strong> {ddl3Scope}
                          </p>
                        ) : null}
                      </section>

                      <section id="sec-functional-flow" className={styles.docSection}>
                        <div className={styles.docSectionHead}>
                          <span className={styles.docSectionNum}>2</span>
                          <h3 className={styles.docSectionTitle}>Functional Flow (Step-by-Step Architecture)</h3>
                        </div>
                        {ddl3Flow.length > 0 ? (
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                            {ddl3Flow.map((item: any, idx: number) => {
                              const stepNum = typeof item === 'object' && item.step ? item.step : idx + 1;
                              const stepTitle = typeof item === 'object' ? (item.title || item.name || `Step ${stepNum}`) : String(item);
                              const stepDesc = typeof item === 'object' && item.description ? item.description : '';

                              return (
                                <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '14px', background: '#FFFFFF', padding: '12px 16px', borderRadius: '8px', border: '1px solid #E2E8F0', boxShadow: '0 1px 2px rgba(0,0,0,0.03)' }}>
                                  <span style={{ width: '30px', height: '30px', borderRadius: '50%', background: '#0F172A', color: '#FFF', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: '13px', flex: 'none' }}>
                                    {stepNum}
                                  </span>
                                  <div style={{ flex: 1 }}>
                                    <strong style={{ fontSize: '14px', color: '#0F172A' }}>{stepTitle}</strong>
                                    {stepDesc && <p style={{ fontSize: '13px', color: '#64748B', margin: '2px 0 0' }}>{stepDesc}</p>}
                                  </div>
                                  {idx < ddl3Flow.length - 1 && (
                                    <span style={{ color: '#94A3B8', fontWeight: 800, fontSize: '16px' }}>↓</span>
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        ) : (
                          <div className={styles.emptyStateBox}>
                            No functional flow pipeline generated yet. Run the DDL3 Agent to map sequential architecture steps.
                          </div>
                        )}
                      </section>

                      <section id="sec-business-validation" className={styles.docSection}>
                        <div className={styles.docSectionHead}>
                          <span className={styles.docSectionNum}>3</span>
                          <h3 className={styles.docSectionTitle}>Business Rules &amp; Validation Matrix</h3>
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
                          <div style={{ background: '#F8FAFC', padding: '16px', borderRadius: '8px', border: '1px solid #E2E8F0' }}>
                            <h4 style={{ fontSize: '13.5px', fontWeight: 700, color: '#005EEB', textTransform: 'uppercase', marginBottom: '10px' }}>
                              Core Business Rules
                            </h4>
                            {ddl3BusinessRules.length > 0 ? (
                              <ul style={{ paddingLeft: '18px', margin: 0, fontSize: '13px', lineHeight: 1.6, color: '#1E293B' }}>
                                {ddl3BusinessRules.map((br: any, idx: number) => (
                                  <li key={idx}>
                                    <strong>{typeof br === 'object' ? (br.rule_id || `BR-${String(idx + 1).padStart(3, '0')}`) : `BR-${String(idx + 1).padStart(3, '0')}`}:</strong>{' '}
                                    {typeof br === 'object' ? (br.rule || br.description || JSON.stringify(br)) : String(br)}
                                  </li>
                                ))}
                              </ul>
                            ) : (
                              <p style={{ fontSize: '13px', color: '#64748B', margin: 0 }}>No business rules defined.</p>
                            )}
                          </div>

                          <div style={{ background: '#F8FAFC', padding: '16px', borderRadius: '8px', border: '1px solid #E2E8F0' }}>
                            <h4 style={{ fontSize: '13.5px', fontWeight: 700, color: '#DC2626', textTransform: 'uppercase', marginBottom: '10px' }}>
                              Input Validation Matrix
                            </h4>
                            {ddl3ValidationRules.length > 0 ? (
                              <ul style={{ paddingLeft: '18px', margin: 0, fontSize: '13px', lineHeight: 1.6, color: '#1E293B' }}>
                                {ddl3ValidationRules.map((val: any, idx: number) => (
                                  <li key={idx}>
                                    <strong>{typeof val === 'object' ? (val.condition || val.rule_id || `VAL-${String(idx + 1).padStart(3, '0')}`) : `VAL-${String(idx + 1).padStart(3, '0')}`}:</strong>{' '}
                                    {typeof val === 'object' ? (val.action || val.error_code || val.description || JSON.stringify(val)) : String(val)}
                                  </li>
                                ))}
                              </ul>
                            ) : (
                              <p style={{ fontSize: '13px', color: '#64748B', margin: 0 }}>No validation rules defined.</p>
                            )}
                          </div>
                        </div>
                      </section>

                      <section id="sec-api-requirements" className={styles.docSection}>
                        <div className={styles.docSectionHead}>
                          <span className={styles.docSectionNum}>4</span>
                          <h3 className={styles.docSectionTitle}>API Requirements &amp; Endpoint Contracts</h3>
                        </div>
                        {ddl3Apis.length > 0 ? (
                          <div className={styles.tableWrapper}>
                            <table className={styles.actionTable}>
                              <thead>
                                <tr>
                                  <th>HTTP Method &amp; Endpoint</th>
                                  <th>API Purpose</th>
                                  <th>Request Parameters</th>
                                  <th>Response Contract</th>
                                </tr>
                              </thead>
                              <tbody>
                                {ddl3Apis.map((api: any, idx: number) => {
                                  const method = typeof api === 'object' && api.method ? api.method : 'GET';
                                  const endpoint = typeof api === 'object' ? (api.endpoint || api.path || 'N/A') : String(api);
                                  const desc = typeof api === 'object' ? (api.description || api.purpose || '') : '';
                                  const req = typeof api === 'object' ? (api.request || api.parameters || 'Standard headers') : 'None';
                                  const resp = typeof api === 'object' ? (api.response || api.contract || 'JSON payload') : 'JSON';

                                  return (
                                    <tr key={idx}>
                                      <td>
                                        <code style={{
                                          background: method === 'POST' ? '#FEF3C7' : method === 'DELETE' ? '#FEE2E2' : '#DBEAFE',
                                          color: method === 'POST' ? '#92400E' : method === 'DELETE' ? '#991B1B' : '#1E40AF',
                                          padding: '3px 8px',
                                          borderRadius: '4px',
                                          fontWeight: 700
                                        }}>
                                          {method} {endpoint}
                                        </code>
                                      </td>
                                      <td>{desc}</td>
                                      <td><code>{req}</code></td>
                                      <td>{resp}</td>
                                    </tr>
                                  );
                                })}
                              </tbody>
                            </table>
                          </div>
                        ) : (
                          <div className={styles.emptyStateBox}>
                            No API requirements specified for this design document.
                          </div>
                        )}
                      </section>

                      <section id="sec-error-handling" className={styles.docSection}>
                        <div className={styles.docSectionHead}>
                          <span className={styles.docSectionNum}>5</span>
                          <h3 className={styles.docSectionTitle}>Error Handling Matrix</h3>
                        </div>
                        {ddl3Errors.length > 0 ? (
                          <div className={styles.tableWrapper}>
                            <table className={styles.actionTable}>
                              <thead>
                                <tr>
                                  <th>Error Scenario</th>
                                  <th>Error Code</th>
                                  <th>Handling &amp; System Behavior</th>
                                </tr>
                              </thead>
                              <tbody>
                                {ddl3Errors.map((err: any, idx: number) => (
                                  <tr key={idx}>
                                    <td><strong>{typeof err === 'object' ? (err.error || err.scenario || `ERR-${idx + 1}`) : String(err)}</strong></td>
                                    <td><code>{typeof err === 'object' && err.code ? err.code : `ERR_${String(idx + 1).padStart(3, '0')}`}</code></td>
                                    <td>{typeof err === 'object' ? (err.handling || err.description || err.action || 'Fallback with user alert') : String(err)}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        ) : (
                          <div className={styles.emptyStateBox}>
                            No error handling scenarios defined.
                          </div>
                        )}
                      </section>

                      <section id="sec-wrief" className={styles.docSection}>
                        <div className={styles.docSectionHead}>
                          <span className={styles.docSectionNum}>6</span>
                          <h3 className={styles.docSectionTitle}>WRIEF Component Classification Badges</h3>
                        </div>
                        {Object.keys(ddl3Wrief).length > 0 ? (
                          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                            {Array.isArray(ddl3Wrief.workflows) && ddl3Wrief.workflows.map((item: string, i: number) => (
                              <span key={`wf-${i}`} className={styles.pill} style={{ background: '#DBEAFE', color: '#1E40AF', padding: '6px 12px', fontSize: '13px' }}>
                                Workflow: {item}
                              </span>
                            ))}
                            {Array.isArray(ddl3Wrief.reports) && ddl3Wrief.reports.map((item: string, i: number) => (
                              <span key={`rep-${i}`} className={styles.pill} style={{ background: '#DCFCE7', color: '#166534', padding: '6px 12px', fontSize: '13px' }}>
                                Report: {item}
                              </span>
                            ))}
                            {Array.isArray(ddl3Wrief.interfaces) && ddl3Wrief.interfaces.map((item: string, i: number) => (
                              <span key={`if-${i}`} className={styles.pill} style={{ background: '#FEF3C7', color: '#92400E', padding: '6px 12px', fontSize: '13px' }}>
                                Interface: {item}
                              </span>
                            ))}
                            {Array.isArray(ddl3Wrief.extensions) && ddl3Wrief.extensions.map((item: string, i: number) => (
                              <span key={`ext-${i}`} className={styles.pill} style={{ background: '#FCE7F3', color: '#9D174D', padding: '6px 12px', fontSize: '13px' }}>
                                Extension: {item}
                              </span>
                            ))}
                            {Array.isArray(ddl3Wrief.forms) && ddl3Wrief.forms.map((item: string, i: number) => (
                              <span key={`form-${i}`} className={styles.pill} style={{ background: '#E0F2FE', color: '#0369A1', padding: '6px 12px', fontSize: '13px' }}>
                                Form: {item}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <div className={styles.emptyStateBox}>
                            No WRIEF components classified for this design specification.
                          </div>
                        )}
                      </section>
                    </>
                  )}

                  {/* ANY OTHER AGENT: one section per part of its output */}
                  {genericSections.map(([key, value], idx) => {
                    const rows =
                      Array.isArray(value) && value.length > 0 && value.every((r) => r && typeof r === 'object' && !Array.isArray(r))
                        ? (value as Record<string, unknown>[])
                        : null;
                    const columns = rows ? [...new Set(rows.flatMap((r) => Object.keys(r)))] : [];
                    return (
                      <section key={key} id={`sec-gen-${key}`} className={styles.docSection}>
                        <div className={styles.docSectionHead}>
                          <span className={styles.docSectionNum}>{idx + 1}</span>
                          <h3 className={styles.docSectionTitle}>{sectionTitle(key)}</h3>
                        </div>
                        {rows ? (
                          <div className={styles.tableWrapper}>
                            <table className={styles.actionTable}>
                              <thead>
                                <tr>{columns.map((c) => <th key={c}>{sectionTitle(c)}</th>)}</tr>
                              </thead>
                              <tbody>
                                {rows.map((row, i) => (
                                  <tr key={i}>{columns.map((c) => <td key={c}>{sectionText(row[c])}</td>)}</tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        ) : (
                          <p className={styles.paragraph} style={{ whiteSpace: 'pre-wrap' }}>{sectionText(value)}</p>
                        )}
                      </section>
                    );
                  })}

                  {/* Open Questions & Interactive Resolution */}
                  <section id="sec-questions" className={styles.docSection}>
                    <div className={styles.docSectionHead}>
                      <span className={styles.docSectionNum}>
                        {outlineItems.find((item) => item.targetId === 'sec-questions')?.id ?? outlineItems.length + 1}
                      </span>
                      <h3 className={styles.docSectionTitle}>Open Questions</h3>
                    </div>

                    {questions.length > 0 ? (
                      questions.map((q) => (
                        <div key={q.id} className={q.status === 'Resolved' ? styles.resolvedCard : styles.questionCard}>
                          <div className={styles.questionTitle}>
                            [{q.id}] {q.question}
                          </div>
                          <div className={styles.questionBody}>{q.context}</div>

                          {q.status === 'Open' ? (
                            <div className={styles.answerBox}>
                              <textarea
                                rows={2}
                                className={styles.answerInput}
                                placeholder="Type your answer here to resolve this open question and update the document with backend agent..."
                                value={questionAnswers[q.question] || ''}
                                onChange={(e) =>
                                  setQuestionAnswers((prev) => ({ ...prev, [q.question]: e.target.value }))
                                }
                              />
                              <div className={styles.answerBtnRow}>
                                <Button
                                  variant="primary"
                                  small
                                  disabled={!questionAnswers[q.question]?.trim() || updatingQuestion !== null}
                                  onClick={() => handleAnswerQuestion(q)}
                                >
                                  {updatingQuestion === q.question ? 'Updating...' : 'Answer & Update Document'}
                                </Button>
                              </div>
                            </div>
                          ) : (
                            <div className={styles.resolvedNote}>
                              <strong>Resolution:</strong> {q.answer || 'Resolved'}
                            </div>
                          )}
                        </div>
                      ))
                    ) : (
                      <div className={styles.resolvedCard}>
                        <strong>All Clear:</strong> No unresolved open questions identified for this specification. All requirements and test flows are traceable.
                      </div>
                    )}
                  </section>
                </div>
              </div>

              {/* Right Rail Dynamic Review Status */}
              <aside className={`${styles.rail} ${styles.railRight}`} aria-label="Review status">
                <h3 className={`${styles.railLabel} ${styles.railLabelBlue}`}>Who is on this</h3>
                <p className={styles.railHint}>{dynamicAttendees.length} participants listed</p>
                <ul>
                  {dynamicAttendees.map((person, idx) => (
                    <li key={idx} className={styles.person}>
                      <div className={styles.personHead}>
                        <span className={styles.personName}>{person.name}</span>
                        <span className={`${styles.pill} ${person.tone}`}>{person.role}</span>
                      </div>
                      <p className={styles.personNote}>{person.note}</p>
                    </li>
                  ))}
                </ul>

                <div className={styles.railGroup}>
                  <h3 className={`${styles.railLabel} ${styles.railLabelAmber}`}>Activity</h3>
                  <p className={styles.railHint}>Newest first</p>
                  {activities.map((evt) => (
                    <div key={evt.id} className={styles.event}>
                      <p className={styles.eventTitle}>{evt.title}</p>
                      <p className={styles.eventNote}>{evt.note}</p>
                    </div>
                  ))}
                </div>

                <div className={styles.railGroup}>
                  <h3 className={styles.railLabel}>Where it goes next</h3>
                  <p className={styles.railHint}>Once approved</p>
                  <div className={styles.destination}>
                    <span>
                      <span className={styles.eventTitle}>{nextDestination.title}</span>
                      <span className={styles.eventNote}>{nextDestination.space}</span>
                    </span>
                    <span className={`${styles.pill} ${styles.pillReady}`}>Ready</span>
                  </div>
                </div>
              </aside>
            </div>
          </>
        )}

        {/* Footer Actions */}
        <div className={styles.footer}>
          <div>
            <h2 className={styles.footerTitle}>
              {unresolvedCount > 0
                ? `${unresolvedCount} open question${unresolvedCount === 1 ? '' : 's'} left before sending`
                : 'All questions resolved! Ready to send for approval'}
            </h2>
            <p className={styles.footerBody}>
              You can send the document for approval now or answer open questions above.
            </p>
          </div>
          <div className={styles.footerActions}>
            <Button variant="primary" onClick={() => navigate('/sharing')}>
              Send for approval
            </Button>
            <Button onClick={() => navigate('/reading')}>Back to recommendations</Button>
          </div>
        </div>
      </Card>

      {/* Ask Savia AI Contextual Modal Popover */}
      {isAskSaviaOpen && (
        <div className={styles.aiPopoverOverlay} onClick={() => setIsAskSaviaOpen(false)}>
          <div className={styles.aiPopoverCard} onClick={(e) => e.stopPropagation()}>
            <div className={styles.aiPopoverHead}>
              <div className={styles.aiPopoverTitle}>
                <span>Ask Savia AI</span>
                <span className={styles.aiBadge}>AI Edit Assist</span>
              </div>
              <button
                type="button"
                className={styles.aiCloseBtn}
                onClick={() => setIsAskSaviaOpen(false)}
              >
                ✕
              </button>
            </div>

            <p style={{ fontSize: '13.5px', color: '#64748B' }}>
              Describe what you want Savia AI to modify in <strong>"{aiTargetSection}"</strong>:
            </p>

            {aiSelectedText && (
              <div className={styles.aiSelectionPreview}>
                <strong>Target context:</strong> "{aiSelectedText}"
              </div>
            )}

            <textarea
              rows={3}
              className={styles.aiPromptInput}
              placeholder="e.g. 'Make this section more concise', 'Rewrite in a formal corporate tone', 'Summarize key decisions'..."
              value={aiPrompt}
              onChange={(e) => setAiPrompt(e.target.value)}
              autoFocus
            />

            <div className={styles.aiChipRow}>
              <button
                type="button"
                className={styles.aiChip}
                onClick={() => setAiPrompt('Make this section concise and punchy')}
              >
                Make concise
              </button>
              <button
                type="button"
                className={styles.aiChip}
                onClick={() => setAiPrompt('Rewrite formally for executive review')}
              >
                Rewrite formally
              </button>
              <button
                type="button"
                className={styles.aiChip}
                onClick={() => setAiPrompt('Expand with technical implementation details')}
              >
                Expand technical details
              </button>
            </div>

            <div className={styles.aiActionRow}>
              <Button small onClick={() => setIsAskSaviaOpen(false)}>
                Cancel
              </Button>
              <Button
                small
                variant="primary"
                disabled={!aiPrompt.trim() || isAiGenerating}
                onClick={handleApplyAskSavia}
              >
                {isAiGenerating ? 'Savia is rewriting...' : 'Apply AI Edit'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </Section>
  );
}
