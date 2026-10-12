/** Original hard-coded content for PlanPage, before the run context. */

export const RECOMMENDATIONS = [
  { id: 'mom', label: '1 · MoM & Action Items', tone: 'rec1' },
  { id: 'rtm', label: '2 · Requirement Gap & RTM', tone: 'rec2' },
  { id: 'ddl3', label: '3 · DDL3', tone: 'rec3' },
  { id: 'kdd', label: '4 · KDD for DAB', tone: 'rec4' },
  { id: 'test', label: '5 · TEST', tone: 'rec5' },
];

export const PLAN_ROWS = [
  {
    id: 'mom',
    rank: '1',
    agent: 'Minutes of Meeting (MoM) & Action Items Matrix',
    why: 'Five speakers, six decisions and eight actions in the room, none of them written down',
    get: 'Minutes, decision log, action matrix',
    approval: 'You',
  },
  {
    id: 'rtm',
    rank: '2',
    agent: 'Requirement Gap Analysis & RTM',
    why: 'Two of the twelve approved stories have acceptance criteria with no expected result',
    get: 'Gap list and the traceability matrix',
    approval: 'You',
  },
  {
    id: 'ddl3',
    rank: '3',
    agent: 'DDL3  (Design Document Lifecycle)',
    why: 'Requirements are approved and there is no design document on this release',
    get: 'Functional design, then technical',
    approval: 'Design Lead',
  },
  {
    id: 'kdd',
    rank: '4',
    agent: 'KDD Package for DAB',
    why: 'The Design Authority Board meets in nine days and expects a dossier',
    get: 'DAB-ready architecture dossier',
    approval: 'Solution Architect',
  },
  {
    id: 'test',
    rank: '5',
    agent: 'TEST — End-to-end Test Preparation',
    why: 'SIT starts in three weeks and cases cannot be written before the design is approved',
    get: 'Inventory, cases, coverage',
    approval: 'Test Lead',
  },
];

export const COST_STATS = [
  { value: '5', caption: 'agents, in order', hint: 'two can overlap' },
  { value: '5', caption: 'times it needs you', hint: 'one approval each', tone: 'red' as const },
  { value: '~48 min', caption: 'of agent time', hint: 'you are not waiting on it' },
  { value: '~4 days', caption: 'of manual work replaced', hint: 'against the last twelve runs', tone: 'red' as const },
];

/** Fixed curve endpoints, before they were spread across the real plan length. */
export const RIGHT_ENDS = [10, 30, 50, 70, 90];

export const TITLE = 'Savia read it and recommends five agents';

export const INPUT_CARD = {
  title: 'Finance Design Workshop.mp4',
  badge: 'Read',
  meta: '1 h 12 min · 5 speakers',
  listItem: 'Transcribed · 9,860 words',
};
