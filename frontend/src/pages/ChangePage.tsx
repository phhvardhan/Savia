import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Section } from '../components/ui/Section';
import { useCurrentRun } from '../state/run';
import { agentLabel, sectionText, sectionTitle } from '../lib/savia';
import styles from './ChangePage.module.css';

const PRESETS = ['Shorten', 'Expand', 'Make it clearer', 'Restructure'];

const GUARDRAILS = [
  {
    id: 'scope',
    title: 'It only touches the section you pick',
    text: 'Every other section of the output stays exactly as it is.',
  },
  {
    id: 'preview',
    title: 'It shows you the change first',
    text: 'Nothing is saved until you accept it, and the previous version is kept.',
  },
  {
    id: 'facts',
    title: 'It will not invent facts',
    text: 'If your instruction needs something that is not in your input, it asks instead of guessing.',
  },
];

export function ChangePage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { run, agent } = useCurrentRun();

  // Every non-empty section, skipping alias keys that repeat an earlier one
  // (MOM stores decisions under both "decisions" and "decisions_finalized").
  const sections = Object.entries(run?.content ?? {}).filter(
    ([, value], i, all) =>
      value !== null &&
      value !== '' &&
      !(Array.isArray(value) && value.length === 0) &&
      all.findIndex(([, other]) => JSON.stringify(other) === JSON.stringify(value)) === i,
  );
  const requested = (location.state as { section?: string } | null)?.section;
  const [section, setSection] = useState<string>(
    () => sections.find(([key]) => key === requested)?.[0] ?? sections.find(([, v]) => typeof v === 'string' && v.length > 80)?.[0] ?? sections[0]?.[0] ?? '',
  );
  const [instruction, setInstruction] = useState('');
  const current = sections.find(([key]) => key === section);
  const sectionIndex = sections.findIndex(([key]) => key === section) + 1;

  const handleAskSavia = () => {
    if (!section || !instruction.trim()) return;
    navigate('/suggestions', { state: { section, instruction: instruction.trim() } });
  };

  if (!run) {
    return (
      <Section id="change" title="Tell SAVIA what to change, in your words" size="compact">
        <Card panel className={styles.panel}>
          <div className={styles.block}>
            <p>There is no agent output to change yet. Run an agent from the recommendations first.</p>
          </div>
          <div className={styles.actions}>
            <Button variant="primary" onClick={() => navigate('/reading')}>
              Back to recommendations
            </Button>
          </div>
        </Card>
      </Section>
    );
  }

  return (
    <Section
      id="change"
      title="Tell SAVIA what to change, in your words"
      size="compact"
      subtitle={`Pick a section of the ${agent ? agentLabel(agent) : 'agent'} output and say what to change. Savia drafts it and shows you before anything is saved.`}
    >
      <Card panel className={styles.panel}>
        <div className={styles.block}>
          <h2 className={styles.label}>Pick the section</h2>
          <div className={styles.presets} role="radiogroup" aria-label="Section to change">
            {sections.map(([key]) => (
              <button
                key={key}
                type="button"
                role="radio"
                aria-checked={key === section}
                className={`${styles.preset} ${key === section ? styles.presetActive : ''}`}
                onClick={() => setSection(key)}
              >
                {sectionTitle(key)}
              </button>
            ))}
          </div>

          <div className={styles.passage}>
            <div className={styles.passageHead}>
              <span className={styles.passageNum}>{sectionIndex}</span>
              <h3 className={styles.passageTitle}>{sectionTitle(section)}</h3>
            </div>
            <p className={styles.quote} style={{ whiteSpace: 'pre-wrap' }}>
              {current ? sectionText(current[1]) : ''}
            </p>
          </div>

          <div className={styles.ask}>
            <div className={styles.askRow}>
              <span className={styles.askIcon} aria-hidden="true">
                <svg width="22" height="22" viewBox="0 0 22 22" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <rect x="0.5" y="0.5" width="21" height="21" rx="3.5" fill="#F1EFED" />
                  <rect x="0.5" y="0.5" width="21" height="21" rx="3.5" stroke="#DAD6D2" strokeDasharray="3 3" />
                  <path
                    fillRule="evenodd"
                    clipRule="evenodd"
                    d="M12.4467 3.17511C12.3197 3.06582 12.148 3.00421 11.9678 3.00382C10.7909 3.00128 6.32302 3 6.32302 3C4.7089 3 3.40039 4.11901 3.40039 5.49938V16.5006C3.40039 17.881 4.7089 19 6.32302 19H15.6778C17.2919 19 18.6004 17.881 18.6004 16.5006V8.92405C18.6004 8.63236 18.4654 8.35251 18.2249 8.14565L12.4467 3.17511ZM11.2919 16.0004H7.49285C7.16988 16.0004 6.90793 15.7764 6.90793 15.5002C6.90793 15.224 7.16988 15 7.49285 15H11.2919C11.6148 15 11.8768 15.224 11.8768 15.5002C11.8768 15.7764 11.6148 16.0004 11.2919 16.0004ZM14.5079 13.4994H7.49285C7.16988 13.4994 6.90793 13.2754 6.90793 13.0008C6.90793 12.7246 7.16988 12.5006 7.49285 12.5006H14.5079C14.8309 12.5006 15.0928 12.7246 15.0928 13.0008C15.0928 13.2754 14.8309 13.4994 14.5079 13.4994ZM14.5079 11H7.49285C7.16988 11 6.90793 10.776 6.90793 10.4998C6.90793 10.2236 7.16988 9.99959 7.49285 9.99959H14.5079C14.8309 9.99959 15.0928 10.2236 15.0928 10.4998C15.0928 10.776 14.8309 11 14.5079 11ZM14.5079 8.00041C13.539 8.00041 12.7551 7.32841 12.7551 6.49978V4.70779L16.6053 8.00041H14.5079Z"
                    fill="black"
                  />
                </svg>
              </span>
              <label className="visually-hidden" htmlFor="change-instruction">
                Tell Savia what to change
              </label>
              <input
                id="change-instruction"
                className={styles.askInput}
                value={instruction}
                onChange={(e) => setInstruction(e.target.value)}
                placeholder="e.g. Shorten this and lead with the decisions"
                onKeyDown={(e) => e.key === 'Enter' && handleAskSavia()}
              />
              <Button variant="primary" small onClick={handleAskSavia} disabled={!instruction.trim()}>
                Ask Savia
              </Button>
            </div>
            <div className={styles.presets}>
              <span className={styles.presetLabel}>Or pick one</span>
              {PRESETS.map((preset) => (
                <button
                  key={preset}
                  type="button"
                  className={styles.preset}
                  onClick={() => setInstruction(`${preset} this section`)}
                >
                  {preset}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className={`${styles.block} ${styles.divider}`}>
          <h2 className={styles.label}>What Savia will and will not do here</h2>
          <ul className={styles.guardrails}>
            {GUARDRAILS.map((item) => (
              <li key={item.id} className={styles.guardrail}>
                <h3 className={styles.guardrailTitle}>{item.title}</h3>
                <p className={styles.guardrailText}>{item.text}</p>
              </li>
            ))}
          </ul>
        </div>

        <div className={styles.actions}>
          <Button variant="primary" onClick={handleAskSavia} disabled={!instruction.trim()}>
            Ask Savia
          </Button>
          <Button onClick={() => navigate('/document')}>Edit it myself instead</Button>
        </div>
      </Card>
    </Section>
  );
}
