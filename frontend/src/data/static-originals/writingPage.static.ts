/** Original hard-coded content for WritingPage, before POST /agents/{id}. */

type SectionState = 'Done' | 'Writing' | 'Next';

export const SECTIONS: Array<{ id: string; title: string; state: SectionState; note?: string }> = [
  { id: 'purpose', title: 'Purpose and scope', state: 'Done' },
  { id: 'definitions', title: 'Definitions', state: 'Done' },
  { id: 'considerations', title: 'Design considerations', state: 'Done' },
  { id: 'field', title: 'Field and table design', state: 'Writing', note: 'Consolidation Unit, Category Code' },
  { id: 'validation', title: 'Validation and derivation', state: 'Next' },
  { id: 'impact', title: 'Impact and dependencies', state: 'Next' },
];

export const OUTPUTS = [
  { id: 'design', title: 'Functional design', state: 'Building', text: '7 sections · opens in Studio' },
  { id: 'packet', title: 'Updated context packet', text: 'Design decisions, ready for TEST', muted: true },
];

export const WRITTEN = [
  { value: '3 of 7', caption: 'sections complete', hint: 'on the J&J template' },
  { value: '2', caption: 'custom fields designed', hint: 'ZCONSUNIT and ZCATCODE' },
  { value: '6', caption: 'criteria traced', hint: 'each one lands in a section' },
  { value: '1', caption: 'section flagged', hint: 'AC-002 is thin', tone: 'orange' as const },
];

export const TITLE = 'DDL3 is writing the design';
export const COLUMN_LABEL = 'DDDL3 agent';
export const ORCHESTRATOR = { name: 'DDL3', state: 'Section 4 of 7' };
export const WORKING_PILL = 'Working · about 2 minutes left';

export const CONTEXT_CARD = {
  title: 'Context packet',
  meta: 'From the orchestrator, 4 min ago',
  items: ['2 approved stories', '6 acceptance criteria', 'RICEFW FIN-0002'],
};
