import { AGENT_META } from '../lib/savia';
import type { BadgeTone } from '../components/ui/Badge';

export type AgentState = 'Available' | 'In review' | 'Coming soon';

export const STATE_TONE: Record<AgentState, BadgeTone> = {
  Available: 'available',
  'In review': 'inReview',
  'Coming soon': 'comingSoon',
};

export interface Agent {
  id: string;
  name: string;
  stage: string;
  state: AgentState;
  capabilities: string[];
}

/** The full capability sheet for each agent — used by the Work page. */
export const AGENTS: Agent[] = [
  {
    id: 'mom',
    name: AGENT_META['mom'].full,
    stage: 'Requirements',
    state: 'Available',
    capabilities: [
      'Multi-speaker transcription analysis for meetings, workshops and discussions',
      'Executive summaries, key decision logs and follow-up actions',
      'Action items tracked with assignee, due date and status',
      'Exports to Excel, Word or SharePoint',
    ],
  },
  {
    id: 'agile-stories',
    name: AGENT_META['agile-stories'].full,
    stage: 'Requirements',
    state: 'Coming soon',
    capabilities: [
      'INVEST-compliant user stories — independent, negotiable, valuable, estimable, small, testable',
      'BDD acceptance criteria in Given / When / Then form',
      'Story point estimation for sprint planning',
      'Exports stories and epics to Excel, Jira or Azure DevOps',
    ],
  },
  {
    id: 'gap-analysis',
    name: AGENT_META['gap-analysis'].full,
    stage: 'Requirements',
    state: 'Available',
    capabilities: [
      'End-to-end traceability from business objective to technical component and test case',
      'Identifies standard versus custom gaps in the requirements',
      'Highlights unmet requirements and their impact on timeline and budget',
      'Produces the RTM the auditors ask for',
    ],
  },
  {
    id: 'ddl3',
    name: AGENT_META['ddl3'].full,
    stage: 'Design',
    state: 'Available',
    capabilities: [
      'Functional design documents for WRICEF objects',
      'Technical design documents',
      'Configuration design documents',
      'Updates an existing functional or technical design in place',
    ],
  },
  {
    id: 'solution-analyzer',
    name: AGENT_META['solution-analyzer'].full,
    stage: 'Design',
    state: 'In review',
    capabilities: [
      'End-to-end solution design for enterprise systems ERP (SAP S/4HANA), WMS, TMS and IoT hubs',
      'Integration and interface landscape blueprints',
      'Target architecture set against the current platform',
      'Diagrams and the rationale behind them in one package',
    ],
  },
  {
    id: 'kdd-dab',
    name: AGENT_META['kdd-dab'].full,
    stage: 'Design governance',
    state: 'Available',
    capabilities: [
      'Architecture dossiers written for Design Authority Board review',
      'Architectural governance, decision frameworks and solution rationale',
      'Structured documentation that meets enterprise compliance and audit requirements',
      'Assembled from the design and architecture you already approved',
    ],
  },
  {
    id: 'change-impact',
    name: AGENT_META['change-impact'].full,
    stage: 'Change',
    state: 'Available',
    capabilities: [
      'Cross-platform impact analysis current platform against target architecture',
      'Cross-workstream dependencies and the risks they carry',
      'Operational readiness evaluation for a clean transition',
      'Interdependencies visualised as a matrix for stakeholder alignment',
    ],
  },
  {
    id: 'test',
    name: AGENT_META['test'].full,
    stage: 'Testing',
    state: 'Available',
    capabilities: [
      'Test case inventories for FIT and UAT',
      'Manual test cases with preconditions, steps and expected results',
      'Coverage stated against every acceptance criterion',
      'Test plans by scenario stitching · in development',
    ],
  },
  {
    id: 'readiness-audit',
    name: AGENT_META['readiness-audit'].full,
    stage: 'Release',
    state: 'Coming soon',
    capabilities: [
      'Multi-dimensional quality scorecard completeness, feasibility, security and compliance',
      'GxP and regulated-industry compliance checks',
      'Production readiness and hypercare preparedness',
      'Identifies gaps in the SDLC process itself',
    ],
  },
  {
    id: 'cutover',
    name: 'Cutover Deployment Documentation',
    stage: 'Cutover',
    state: 'Available',
    capabilities: [
      'Cutover run sheets built from the approved release scope',
      'Go / no-go readiness checks across every workstream',
      'Rollback plans and the evidence that they were tested',
      'Sign-off records for the release',
    ],
  },
];

export interface LibraryRow {
  id: string;
  name: string;
  stage: string;
  needs: string;
  produces: string;
  systems: string[];
  state: AgentState;
}

/** The one-line contract for every agent — used by the Library table. */
export const LIBRARY_ROWS: LibraryRow[] = [
  {
    id: 'mom',
    name: AGENT_META['mom'].full,
    stage: 'Requirements',
    needs: 'A recording, transcript or notes',
    produces: 'Minutes, decisions & owned actions',
    systems: ['Teams', 'SharePoint'],
    state: 'Available',
  },
  {
    id: 'agile-stories',
    name: AGENT_META['agile-stories'].full,
    stage: 'Requirements',
    needs: 'Minutes or a BRD',
    produces: 'INVEST stories, BDD criteria, points',
    systems: ['Jira', 'Excel'],
    state: 'Coming soon',
  },
  {
    id: 'gap-analysis',
    name: AGENT_META['gap-analysis'].full,
    stage: 'Requirements',
    needs: 'A BRD and the stories',
    produces: 'Gap list and traceability matrix',
    systems: ['Excel', 'Confluence'],
    state: 'Available',
  },
  {
    id: 'ddl3',
    name: AGENT_META['ddl3'].full,
    stage: 'Design',
    needs: 'Approved stories or a BRD',
    produces: 'Functional, technical & config designs',
    systems: ['Confluence', 'SharePoint'],
    state: 'Available',
  },
  {
    id: 'solution-analyzer',
    name: AGENT_META['solution-analyzer'].full,
    stage: 'Design',
    needs: 'Design documents',
    produces: 'Enterprise solution blueprint',
    systems: ['Confluence'],
    state: 'In review',
  },
  {
    id: 'kdd-dab',
    name: AGENT_META['kdd-dab'].full,
    stage: 'Design governance',
    needs: 'Design plus architecture',
    produces: 'A DAB-ready dossier',
    systems: ['SharePoint'],
    state: 'Available',
  },
  {
    id: 'change-impact',
    name: AGENT_META['change-impact'].full,
    stage: 'Change',
    needs: 'A design and the landscape',
    produces: 'Impact and interdependency matrix',
    systems: ['Excel', 'ServiceNow'],
    state: 'Available',
  },
  {
    id: 'test',
    name: AGENT_META['test'].full,
    stage: 'Testing',
    needs: 'An approved design and its criteria',
    produces: 'Inventory, cases, coverage, plans',
    systems: ['Jira', 'Excel'],
    state: 'Available',
  },
  {
    id: 'readiness-audit',
    name: AGENT_META['readiness-audit'].full,
    stage: 'Release',
    needs: 'Everything upstream',
    produces: 'Readiness scorecard and SDLC audit',
    systems: ['Excel'],
    state: 'Coming soon',
  },
  {
    id: 'cutover',
    name: 'Cutover Deployment Docs',
    stage: 'Cutover',
    needs: 'Readiness and the run sheet',
    produces: 'Cutover plan and sign-off record',
    systems: ['ServiceNow'],
    state: 'Available',
  },
];
