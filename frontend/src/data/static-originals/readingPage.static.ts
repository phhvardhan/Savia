/** Original hard-coded content for ReadingPage, before /ingestion + /savia. */

export const STEPS = [
  { id: 'read', title: 'Read the document', state: 'Done' as const },
  { id: 'match', title: 'Match it to the project', state: 'Done' as const },
  { id: 'stage', title: 'Work out the stage', state: 'Now' as const, note: 'Design functional, then technical' },
  { id: 'agents', title: 'Choose the agents', state: 'Next' as const },
];

export const RECOMMENDS = [
  { id: 'ddl3', title: 'DDL3', text: 'Design documents · best match for this input', chosen: true },
  { id: 'test', title: 'TEST', text: 'Queued starts once the design is approved' },
  { id: 'bus', title: 'BUS / TUS', text: 'Not needed the stories already exist', muted: true },
];

export const FOUND = [
  { value: '2', caption: 'User Stories', hint: 'JGFY-2812 and JGFY-5303', tone: 'blue' as const },
  { value: '6', caption: 'Acceptance Criteria', hint: '1 has no expected result', tone: 'orange' as const },
  { value: '4', caption: 'Systems Touched', hint: 'all inside the J&J boundary', tone: 'green' as const },
  { value: '1', caption: 'Open Question', hint: 'needs you', tone: 'red' as const },
];

/** The input card, which showed a fixed file rather than the upload. */
export const INPUT_CARD = {
  title: '02a-BRD.docx',
  badge: 'Read',
  meta: '34 pages · 2 user stories · 6 acceptance criteria',
  listItem: 'Read · 11,402 words',
};

export const ORCHESTRATOR_STATE = 'Step 3 of 4';
export const WORKING_PILL = 'Working · about 40 seconds left';
