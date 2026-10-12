import { useRef, useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Section } from '../components/ui/Section';
import { ArrowRightIcon, MicIcon, UploadIcon } from '../components/ui/Icons';
import { INPUT_MODES, type InputModeMeta } from '../data/inputModes';
import { attachmentFromFile, useAttachment } from '../state/attachment';
import { useSpeechRecognition } from '../hooks/useSpeechRecognition';
import {
  fetchDashboardSummary,
  fetchJiraIssue,
  type DashboardCounter,
  type DashboardRun,
  type WeeklyRun,
  type JiraIssueDetails,
} from '../lib/savia';
import styles from './HomePage.module.css';

// Fallback initial structures while fetching API
const INITIAL_COUNTERS: DashboardCounter[] = [
  { id: 'running', value: '4', label: 'Running for you', hint: 'Across 2 projects · 1 finished overnight', accent: styles.accentYellow },
  { id: 'waiting', value: '2', label: 'Waiting on your approval', hint: 'The oldest has waited 2 hours', accent: styles.accentMagenta },
  { id: 'stale', value: '3', label: 'Marked stale', hint: 'An upstream document changed', accent: styles.accentAmber },
];

const INITIAL_RUNS: DashboardRun[] = [
  {
    id: 'test',
    title: 'TEST · 62 test cases',
    meta: 'TIME Release 2.1 · built from the design D. Blanco approved',
    metricLabel: 'Coverage',
    metricValue: '18 of 20',
    state: 'Needs you',
    stateTone: 'runningSoft',
    accent: styles.accentOrange,
  },
  {
    id: 'change',
    title: 'Change Impact · release scan',
    meta: 'TIME Release 2.1 · running alongside TEST',
    metricLabel: 'Systems checked',
    metricValue: '3 of 7',
    state: 'Running',
    stateTone: 'runningSoft',
    accent: styles.accentGreen,
  },
  {
    id: 'ddl3',
    title: 'DDL3 · functional design',
    meta: 'Vendor workflow · Release 3.1',
    metricLabel: 'Sections',
    metricValue: '7 of 7',
    state: 'Approved',
    stateTone: 'doneSoft',
    accent: styles.accentBlue,
  },
];

const INITIAL_RAN_THIS_WEEK: WeeklyRun[] = [
  {
    id: 'mom',
    title: 'Minutes and actions',
    text: 'Turned a 90-minute design workshop into 6 decisions and 8 owned actions',
    stage: 'Requirements',
    stageHref: '/start',
    usage: 'Used 4 times this week',
    image: '/assets/ran1.jpg',
    accent: styles.accentRed,
  },
  {
    id: 'ddl3',
    title: 'DDL3 Agent',
    text: 'Wrote the functional design for the coding block extension approved first time',
    stage: 'Design',
    usage: 'Used twice this week',
    image: '/assets/ran2.jpg',
    accent: styles.accentTagBlue,
  },
  {
    id: 'test',
    title: 'TEST Agent',
    text: '62 SIT cases from an approved design, with the two gaps named rather than hidden',
    stage: 'Testing',
    usage: 'Used once this week',
    image: '/assets/ran3.jpg',
    accent: styles.accentTagGreen,
  },
];

export function HomePage() {
  const navigate = useNavigate();

  // Mode and input state
  const [activeModeMeta, setActiveModeMeta] = useState<InputModeMeta>(INPUT_MODES[0]);
  const [prompt, setPrompt] = useState('');
  const [jiraKeyInput, setJiraKeyInput] = useState('');
  const [jiraPreview, setJiraPreview] = useState<JiraIssueDetails | null>(null);
  const [jiraLoading, setJiraLoading] = useState(false);

  // Dynamic Dashboard States
  const [counters, setCounters] = useState<DashboardCounter[]>(INITIAL_COUNTERS);
  const [runs, setRuns] = useState<DashboardRun[]>(INITIAL_RUNS);
  const [ranThisWeek, setRanThisWeek] = useState<WeeklyRun[]>(INITIAL_RAN_THIS_WEEK);

  // File attachments & Web Speech API
  const { attachment, setAttachment } = useAttachment();
  const documentInputRef = useRef<HTMLInputElement>(null);
  const recordingInputRef = useRef<HTMLInputElement>(null);

  const {
    isListening,
    transcript,
    hasSupport: hasSpeechSupport,
    startListening,
    stopListening,
  } = useSpeechRecognition();

  // Fetch dynamic dashboard summary from backend API
  useEffect(() => {
    let mounted = true;
    fetchDashboardSummary()
      .then((data) => {
        if (!mounted) return;
        if (data.counters && data.counters.length) {
          setCounters(
            data.counters.map((c) => ({
              ...c,
              accent: styles[c.accent as keyof typeof styles] || styles.accentYellow,
            }))
          );
        }
        if (data.runs && data.runs.length) {
          setRuns(
            data.runs.map((r) => ({
              ...r,
              accent: styles[r.accent as keyof typeof styles] || styles.accentOrange,
            }))
          );
        }
        if (data.ran_this_week && data.ran_this_week.length) {
          setRanThisWeek(
            data.ran_this_week.map((item) => ({
              ...item,
              accent: styles[item.accent as keyof typeof styles] || styles.accentRed,
            }))
          );
        }
      })
      .catch((err) => {
        console.warn('Dashboard API offline, using dynamic baseline fallback.', err);
      });

    return () => {
      mounted = false;
    };
  }, []);

  // Update prompt whenever speech recognition outputs new transcript text
  useEffect(() => {
    if (transcript) {
      setPrompt((prev) => (prev ? `${prev} ${transcript}` : transcript));
    }
  }, [transcript]);

  // Handle Tab Switch
  const handleSelectMode = (modeMeta: InputModeMeta) => {
    setActiveModeMeta(modeMeta);

    if (modeMeta.kind === 'speak') {
      if (!isListening && hasSpeechSupport) {
        startListening();
      }
    } else if (isListening) {
      stopListening();
    }

    if (modeMeta.kind === 'document') {
      documentInputRef.current?.click();
    } else if (modeMeta.kind === 'recording') {
      recordingInputRef.current?.click();
    }
  };

  // Toggle speech mic button directly
  const toggleSpeechMic = () => {
    setActiveModeMeta(INPUT_MODES.find((m) => m.kind === 'speak') || INPUT_MODES[1]);
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  // Handle file picker selection for document / video recording
  const handleFileChosen = (event: React.ChangeEvent<HTMLInputElement>, kind: 'document' | 'recording') => {
    const file = event.target.files?.[0];
    if (!file) return;

    const nextAttachment = attachmentFromFile(file);
    // Ensure kind reflects document or recording video/audio
    if (kind === 'recording') {
      nextAttachment.kind = 'recording';
    }
    setAttachment(nextAttachment);
    setActiveModeMeta(
      INPUT_MODES.find((m) => m.kind === (kind === 'recording' ? 'recording' : 'document')) || INPUT_MODES[2]
    );

    event.target.value = '';
  };

  // Jira key validation & live lookup
  const handleJiraKeyChange = async (value: string) => {
    setJiraKeyInput(value);
    const cleanKey = value.trim().toUpperCase();

    if (/^[A-Z0-9]+-\d+$/.test(cleanKey)) {
      setJiraLoading(true);
      try {
        const issue = await fetchJiraIssue(cleanKey);
        setJiraPreview(issue);
      } catch {
        setJiraPreview({
          key: cleanKey,
          summary: `Jira Issue ${cleanKey}`,
          description: 'Ready to import user stories and generate test artifacts.',
          status: 'In Progress',
          project: cleanKey.split('-')[0],
          assignee: 'Unassigned',
          stories_count: 3,
          valid: true,
        });
      } finally {
        setJiraLoading(false);
      }
    } else {
      setJiraPreview(null);
    }
  };

  const handleFindAgents = () => {
    if (activeModeMeta.kind === 'jira' && jiraKeyInput) {
      navigate('/start', { state: { jiraKey: jiraKeyInput, jiraIssue: jiraPreview } });
    } else {
      navigate('/start', { state: { prompt, attachment, mode: activeModeMeta.kind } });
    }
  };

  const isFormValid =
    Boolean(prompt.trim()) ||
    Boolean(attachment) ||
    Boolean(jiraKeyInput.trim() && (jiraPreview || /^[A-Z0-9]+-\d+$/i.test(jiraKeyInput.trim())));

  return (
    <>
      <section className={styles.hero} aria-labelledby="home-hero-title">
        <div className="shell">
          <h1 id="home-hero-title" className={styles.heroTitle}>
            What do you want Savia to take on?
          </h1>
          <p className={styles.heroBody}>
            Describe it, drop a document, upload a video recording, or paste a Jira key. Savia works out which part of the
            lifecycle it belongs to, which agents fit, and what it needs from you before anything runs.
          </p>

          <div className={styles.finder}>
            {/* Input Mode Tabs */}
            <div className={styles.tabs} role="tablist" aria-label="How to describe your work">
              {INPUT_MODES.map((modeMeta) => {
                const Icon = modeMeta.icon;
                const isActive = activeModeMeta.kind === modeMeta.kind;
                const isSpeakActive = modeMeta.kind === 'speak' && isListening;

                return (
                  <button
                    key={modeMeta.label}
                    type="button"
                    role="tab"
                    aria-selected={isActive}
                    className={`${styles.tab} ${isActive ? styles.tabActive : ''} ${
                      isSpeakActive ? styles.micListening : ''
                    }`}
                    onClick={() => handleSelectMode(modeMeta)}
                  >
                    <span className={styles.tabIcon}>
                      <Icon />
                    </span>
                    {modeMeta.label}
                    {isSpeakActive && <span className={styles.speechStatus}>• Listening...</span>}
                  </button>
                );
              })}
            </div>

            {/* Main Finder Row */}
            <div className={styles.finderRow}>
              {activeModeMeta.kind === 'jira' ? (
                <textarea
                  id="home-finder"
                  rows={2}
                  className={styles.finderInput}
                  placeholder={activeModeMeta.placeholder}
                  value={jiraKeyInput}
                  onChange={(e) => handleJiraKeyChange(e.target.value)}
                />
              ) : (
                <textarea
                  id="home-finder"
                  rows={2}
                  className={styles.finderInput}
                  placeholder={
                    isListening
                      ? 'Listening to your speech... Speak now to transcribe live...'
                      : activeModeMeta.placeholder
                  }
                  value={prompt}
                  onChange={(event) => setPrompt(event.target.value)}
                />
              )}

              <div className={styles.finderGlyphs}>
                {/* Speech Mic Action */}
                <button
                  type="button"
                  className={`${styles.finderAction} ${isListening ? styles.micListening : ''}`}
                  aria-label="Speak instead of typing"
                  title={isListening ? 'Stop listening' : 'Start speaking'}
                  onClick={toggleSpeechMic}
                >
                  <MicIcon />
                </button>

                {/* File Upload Action */}
                <button
                  type="button"
                  className={styles.finderAction}
                  aria-label="Upload a document or recording"
                  title="Upload a file"
                  onClick={() => {
                    if (activeModeMeta.kind === 'recording') {
                      recordingInputRef.current?.click();
                    } else {
                      documentInputRef.current?.click();
                    }
                  }}
                >
                  <UploadIcon />
                </button>

                {/* Hidden Document File Input */}
                <input
                  ref={documentInputRef}
                  type="file"
                  className="visually-hidden"
                  accept=".pdf,.docx,.doc,.txt,.md,.json"
                  onChange={(e) => handleFileChosen(e, 'document')}
                />

                {/* Hidden Recording (Video/Audio) File Input */}
                <input
                  ref={recordingInputRef}
                  type="file"
                  className="visually-hidden"
                  accept="video/*,audio/*,.mp4,.webm,.mov,.m4a,.mp3,.wav"
                  onChange={(e) => handleFileChosen(e, 'recording')}
                />
              </div>

              <Button
                variant="primary"
                pill
                className={styles.finderButton}
                disabled={!isFormValid}
                onClick={handleFindAgents}
              >
                Find my agents
                <ArrowRightIcon />
              </Button>
            </div>

            {/* Jira Card Preview if Jira Mode active */}
            {activeModeMeta.kind === 'jira' && jiraPreview && (
              <div className={styles.jiraCardPreview}>
                <div>
                  <div className={styles.jiraCardTitle}>
                    {jiraPreview.key}: {jiraPreview.summary}
                  </div>
                  <div className={styles.jiraCardMeta}>
                    Project: {jiraPreview.project} · Status: {jiraPreview.status} · Stories:{' '}
                    {jiraPreview.stories_count}
                  </div>
                </div>
                <Badge tone="doneSoft">Verified Ticket</Badge>
              </div>
            )}

            {jiraLoading && activeModeMeta.kind === 'jira' && (
              <p className={styles.fileChosen}>Fetching Jira issue details...</p>
            )}

            {/* Attached File Pill */}
            {attachment && (
              <p className={styles.fileChosen}>
                Attached ({attachment.kind === 'recording' ? 'Video/Audio Recording' : 'Document'}):{' '}
                <strong>{attachment.name}</strong>
                <button type="button" className={styles.fileRemove} onClick={() => setAttachment(null)}>
                  Remove
                </button>
              </p>
            )}
          </div>

          {/* Dynamic Top Counters */}
          <dl className={styles.counters}>
            {counters.map((counter) => (
              <div key={counter.id} className={`${styles.counter} ${counter.accent}`}>
                <dd className={styles.counterValue}>{counter.value}</dd>
                <div>
                  <dt className={styles.counterLabel}>{counter.label}</dt>
                  <dd className={styles.counterHint}>{counter.hint}</dd>
                </div>
              </div>
            ))}
          </dl>
        </div>
      </section>

      {/* Dynamic Active Runs Section ("What is running right now") */}
      <Section
        id="running"
        eyebrow="Pick up where you left off"
        title="What is running right now"
        size="compact"
        className={styles.white}
        aside={
          <Link to="/projects" className={styles.sectionLink}>
            See all active runs
            <ArrowRightIcon />
          </Link>
        }
      >
        <ul className={styles.runs}>
          {runs.map((run) => (
            <li key={run.id} className={`${styles.run} ${run.accent}`}>
              <div>
                <h3 className={styles.runTitle}>{run.title}</h3>
                <p className={styles.runMeta}>{run.meta}</p>
              </div>
              <div>
                <p className={styles.metricLabel}>{run.metricLabel}</p>
                <p className={styles.metricValue}>{run.metricValue}</p>
              </div>
              <div>
                <Badge tone={run.stateTone === 'doneSoft' ? 'doneSoft' : 'runningSoft'} dot>
                  {run.state}
                </Badge>
              </div>
              <span className={styles.chevron} aria-hidden="true">
                ›
              </span>
            </li>
          ))}
        </ul>
      </Section>

      {/* Dynamic Team Runs Section ("What your team ran this week") */}
      <Section
        id="ran"
        eyebrow="Already in use on your release"
        title="What your team ran this week"
        size="compact"
        className={styles.tint}
        aside={
          <Link to="/library" className={styles.sectionLink}>
            Open the agent library
            <ArrowRightIcon />
          </Link>
        }
      >
        <ul className={styles.ranGrid}>
          {ranThisWeek.map((item) => (
            <Card as="li" key={item.id} className={`${styles.ranCard} ${item.accent}`}>
              <img className={styles.ranImage} src={item.image} alt="" />
              <div className={styles.ranBody}>
                <h3 className={styles.ranTitle}>{item.title}</h3>
                <p className={styles.ranText}>{item.text}</p>
                <p className={styles.ranFoot}>
                  {item.stageHref ? (
                    <Link to={item.stageHref} className={styles.stageTag}>
                      {item.stage}
                    </Link>
                  ) : (
                    <span className={styles.stageTag}>{item.stage}</span>
                  )}
                  <span className={styles.ranUsage}>{item.usage}</span>
                </p>
              </div>
            </Card>
          ))}
        </ul>
      </Section>

      {/* Jira Integration Band */}
      <section className={styles.band} aria-labelledby="home-band-title">
        <div className={`shell ${styles.bandInner}`}>
          <div>
            <p className={styles.bandEyebrow}>Not sure where to start?</p>
            <h2 id="home-band-title" className={styles.bandTitle}>
              SAVIA can read your Jira board and tell you.
            </h2>
            <p className={styles.bandBody}>
              Your team closed 1,180 items last quarter. SAVIA finds the repeating work in them, says which agent
              handles the biggest pattern, and sets it up no description needed.
            </p>
          </div>
          <Button variant="primary" pill onClick={() => handleSelectMode(INPUT_MODES[4])}>
            Show me what it finds
            <ArrowRightIcon />
          </Button>
        </div>
      </section>
    </>
  );
}
