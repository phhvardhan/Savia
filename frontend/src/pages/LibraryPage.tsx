import { useRef, useState } from 'react';
import type { ComponentType } from 'react';
import { LIBRARY_ROWS, STATE_TONE, type AgentState } from '../data/agents';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { DataTable } from '../components/ui/DataTable';
import { Section } from '../components/ui/Section';
import {
  ArrowRightIcon,
  BlueprintIcon,
  BranchIcon,
  DossierIcon,
  FlagIcon,
  FlaskIcon,
  LayersIcon,
  MatrixIcon,
  MicIcon,
  NotesIcon,
  StackIcon,
  TargetIcon,
  UploadIcon,
} from '../components/ui/Icons';
import { INPUT_MODES } from '../data/inputModes';
import { ACCEPTED_FILES, attachmentFromFile, useAttachment } from '../state/attachment';
import styles from './LibraryPage.module.css';


const PROMPT_PLACEHOLDER = 'I need test cases for a change we have already designed and approved…';

/** One mark per agent, keyed by the ids in data/agents.ts. */
const AGENT_ICONS: Record<string, ComponentType> = {
  mom: NotesIcon,
  stories: StackIcon,
  rtm: MatrixIcon,
  ddl3: BlueprintIcon,
  architecture: LayersIcon,
  kdd: DossierIcon,
  change: BranchIcon,
  test: FlaskIcon,
  readiness: TargetIcon,
  cutover: FlagIcon,
};

const STAGES = [
  { id: 'requirements', name: 'Requirements', agents: 3, inUse: '2 in use on your release', image: '/assets/stage-1.jpg' },
  { id: 'design', name: 'Design', agents: 3, inUse: '1 in use on your release', image: '/assets/stage-2.jpg' },
  { id: 'change-testing', name: 'Change & testing', agents: 2, inUse: '1 in use on your release', image: '/assets/stage-3.jpg' },
  { id: 'release-cutover', name: 'Release & cutover', agents: 2, inUse: 'none yet', image: '/assets/stage-4.jpg' },
];

const FILTERS: Array<{ id: string; label: string; state?: AgentState }> = [
  { id: 'all', label: `All ${LIBRARY_ROWS.length}` },
  { id: 'available', label: 'Available', state: 'Available' },
  { id: 'in-review', label: 'In review', state: 'In review' },
  { id: 'coming-soon', label: 'Coming soon', state: 'Coming soon' },
];

const PICKS = [
  {
    id: 'kdd',
    stage: 'Design',
    title: 'KDD for DAB',
    body: 'Your design is approved and the DAB meets in nine days. This builds the dossier from the design and the architecture you already have.',
    meta: '~12 min · Works after DDL3',
  },
  {
    id: 'change',
    stage: 'Change',
    title: 'Change impact',
    body: 'The field length change this morning touches one downstream report. This finds the rest before SIT does.',
    meta: '~20 min · Works alongside TEST',
  },
  {
    id: 'rtm',
    stage: 'Requirements',
    title: 'Requirement gap & RTM',
    body: 'Two of your acceptance criteria were thin enough to cost you coverage. This catches that at the requirements stage instead.',
    meta: '~8 min · Works before DDL3',
  },
];

const NOTES = [
  {
    label: 'Every agent is governed',
    body: 'Internally built or internally reviewed, version pinned, and hosted inside the J&J boundary. A version change re-opens governance automatically.',
  },
  {
    label: 'Nothing generic is shown',
    body: 'You see the agents that can run on your project, your release and your data classification. The rest are hidden, not buried.',
  },
  {
    label: 'Every recommendation is explained',
    body: 'SAVIA names the reason the stage you are in, what you have approved, what your team already runs. Never one opaque score.',
  },
];

export function LibraryPage() {
  const [mode, setMode] = useState(INPUT_MODES[0].label);
  const { setAttachment } = useAttachment();
  const fileInputRef = useRef<HTMLInputElement>(null);

  function handleFileChosen(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;

    const next = attachmentFromFile(file);
    setAttachment(next);
    setMode(next.kind === 'recording' ? 'Upload a recording' : 'Upload a document');
    event.target.value = '';
  }
  const [prompt, setPrompt] = useState('');
  const [filter, setFilter] = useState('all');

  const activeFilter = FILTERS.find((item) => item.id === filter);
  const rows = activeFilter?.state
    ? LIBRARY_ROWS.filter((row) => row.state === activeFilter.state)
    : LIBRARY_ROWS;

  return (
    <>
      <section className={styles.hero} aria-labelledby="library-hero-title">
        <div className="shell">
          <p className={styles.eyebrow}>
            The Savia agent library · 10 agents across 8 lifecycle stages · All internal to J&amp;J
          </p>
          <h1 id="library-hero-title" className={styles.heroTitle}>
            Tell us what you are trying to get done.
          </h1>
          <p className={styles.heroBody}>
            You do not need to know which agent you want. Describe the work and Savia will name the agents that fit,
            what they need from you, and who has to approve the result.
          </p>

          <div className={styles.finder}>
            <div className={styles.tabs} role="tablist" aria-label="How to describe your work">
              {INPUT_MODES.map(({ label, icon: Icon }) => (
                <button
                  key={label}
                  type="button"
                  role="tab"
                  aria-selected={mode === label}
                  className={`${styles.tab} ${mode === label ? styles.tabActive : ''}`}
                  onClick={() => setMode(label)}
                >
                  <span className={styles.tabIcon}>
                    <Icon />
                  </span>
                  {label}
                </button>
              ))}
            </div>

            <div className={styles.finderRow}>
              <label className="visually-hidden" htmlFor="agent-finder">
                Describe the work you are trying to get done
              </label>
              <input
                id="agent-finder"
                className={styles.finderInput}
                placeholder={PROMPT_PLACEHOLDER}
                value={prompt}
                onChange={(event) => setPrompt(event.target.value)}
              />
              <div className={styles.finderGlyphs}>
                <button
                  type="button"
                  className={styles.finderAction}
                  aria-label="Speak instead of typing"
                  title="Speak"
                  onClick={() => setMode('Speak')}
                >
                  <MicIcon />
                </button>
                <button
                  type="button"
                  className={styles.finderAction}
                  aria-label="Upload a document or recording"
                  title="Upload a file"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <UploadIcon />
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  className="visually-hidden"
                  accept={ACCEPTED_FILES}
                  onChange={handleFileChosen}
                />
              </div>
              <Button variant="primary" pill>
                Find my agents
                <ArrowRightIcon />
              </Button>
            </div>
          </div>

          <p className={styles.heroHint}>Or browse the library below ↓</p>
        </div>
      </section>

      <Section
        id="stages"
        eyebrow="Start from where you are"
        title="Browse by lifecycle stage"
        size="compact"
        subtitle="Stages are filtered to your project and your data classification before you see them. An agent that cannot run on TIME Release 2.1 is not shown."
      >
        <ul className={styles.stages}>
          {STAGES.map((stage) => (
            <Card as="li" key={stage.id} className={styles.stageCard}>
              <img className={styles.stageImage} src={stage.image} alt="" />
              <div className={styles.stageBody}>
                <h3 className={styles.stageName}>{stage.name}</h3>
                <p className={styles.stageCount}>
                  <strong>{stage.agents} agents</strong> · {stage.inUse}
                </p>
              </div>
            </Card>
          ))}
        </ul>
      </Section>

      <Section
        id="contract"
        eyebrow="The whole library, on one contract"
        title="What each agent needs, and what it gives back"
        size="compact"
        subtitle="Every agent answers the same four questions. That is what keeps the library readable as it grows."
        className={styles.altSection}
        aside={
          <div className={styles.filters} role="group" aria-label="Filter agents by state">
            {FILTERS.map((item) => (
              <button
                key={item.id}
                type="button"
                aria-pressed={filter === item.id}
                className={`${styles.filter} ${filter === item.id ? styles.filterActive : ''}`}
                onClick={() => setFilter(item.id)}
              >
                {item.label}
              </button>
            ))}
          </div>
        }
      >
        <Card panel>
          <DataTable
            caption="What each agent needs, what it produces, the systems it touches and its state"
            minWidth={900}
            columns={[
              { key: 'agent', label: 'Agent', width: '19%' },
              { key: 'stage', label: 'Stage', width: '13%' },
              { key: 'needs', label: 'What it needs', width: '20%' },
              { key: 'produces', label: 'What it produces', width: '21%' },
              { key: 'systems', label: 'Systems', width: '14%' },
              { key: 'state', label: 'State', width: '13%' },
            ]}
            rows={rows.map((row) => ({
              id: row.id,
              cells: [
                <span key="name">
                  <span className={styles.rowIcon}>
                    {(() => {
                      const Icon = AGENT_ICONS[row.id];
                      return Icon ? <Icon /> : null;
                    })()}
                  </span>
                  <span className={row.state === 'Coming soon' ? styles.mutedName : undefined}>{row.name}</span>
                </span>,
                row.stage,
                row.needs,
                row.produces,
                <span key="systems" className={styles.systems}>{row.systems.join(' · ')}</span>,
                <Badge key="state" tone={STATE_TONE[row.state]}>{row.state}</Badge>,
              ],
            }))}
          />
        </Card>
      </Section>

      <Section
        id="picks"
        eyebrow="Picked for TIME Release 2.1"
        title="Because of what your team already runs"
        size="compact"
        subtitle="Savia looked at your four running agents, the stage this release is in, and what it has already approved. These are the gaps it can close this week."
        className={styles.altSection}
      >
        <ul className={styles.picks}>
          {PICKS.map((pick) => (
            <li key={pick.id} className={styles.pick}>
              <div className={styles.pickHead}>
                <p className={styles.pickStage}>{pick.stage}</p>
                <Badge tone="doneSoft">Available</Badge>
              </div>
              <h3 className={styles.pickTitle}>{pick.title}</h3>
              <p className={styles.pickBody}>{pick.body}</p>
              <p className={styles.pickMeta}>{pick.meta}</p>
              <div className={styles.pickActions}>
                <Button variant="primary" pill small>
                  Run it
                </Button>
                <Button pill small>
                  What it needs
                </Button>
                <Button pill small>
                  Add to Studio
                </Button>
              </div>
            </li>
          ))}
        </ul>
      </Section>

      <section className={styles.notes} aria-label="How the library is governed">
        <div className="shell">
          <div className={styles.notesGrid}>
            {NOTES.map((note) => (
              <div key={note.label}>
                <h2 className={styles.noteLabel}>{note.label}</h2>
                <p className={styles.noteBody}>{note.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
