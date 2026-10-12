/**
 * Counts for the "what it has found so far" panel.
 *
 * The backend returns no such counts — /ingestion/analyze gives booleans, and
 * real figures only exist once an agent has run. So these are read off the
 * normalized text the upload returns: derived from the actual document, but
 * by pattern matching, in the same spirit as the backend's own orchestrator.
 * Each count says in its hint what it matched, so the number is never a claim
 * the document does not support.
 */

export interface DocStats {
  userStories: number;
  acceptanceCriteria: number;
  systemsTouched: number;
  openQuestions: number;
  /** What each count was matched on, for the tile hints. */
  notes: {
    userStories: string;
    acceptanceCriteria: string;
    systemsTouched: string;
    openQuestions: string;
  };
}

/** Systems this programme talks about; counted only when actually named. */
const KNOWN_SYSTEMS = [
  'SAP', 'S/4', 'S4', 'MDG', 'BTP', 'TIME', 'Jira', 'GSDB', 'Ariba',
  'Salesforce', 'ServiceNow', 'Oracle', 'Workday', 'SharePoint', 'OTC',
];

function countMatches(text: string, pattern: RegExp): number {
  return (text.match(pattern) ?? []).length;
}

export function readDocStats(text: string): DocStats {
  // "As a <role> … I want …" — the INVEST story shape.
  const storyShapes = countMatches(text, /\bas an?\b[^.!?\n]{0,80}?\bi want\b/gi);
  const storyMentions = countMatches(text, /\buser stor(?:y|ies)\b/gi);
  // Ticket keys like JGFY-2812, counted once each.
  const storyKeys = new Set(text.match(/\b[A-Z]{2,}-\d+\b/g) ?? []);

  const userStories = storyShapes || storyKeys.size || storyMentions;
  const userStoriesNote = storyShapes
    ? 'from "as a … I want" statements'
    : storyKeys.size
      ? `keys: ${[...storyKeys].slice(0, 3).join(', ')}`
      : storyMentions
        ? 'mentions of user stories'
        : 'none found in the text';

  // Given / When / Then triples, else explicit mentions.
  const gwt = countMatches(text, /\bgiven\b[^.!?\n]{0,160}?\bwhen\b[^.!?\n]{0,160}?\bthen\b/gi);
  const acMentions = countMatches(text, /\bacceptance criteri(?:on|a)\b/gi);
  const acceptanceCriteria = gwt || acMentions;
  const acceptanceCriteriaNote = gwt
    ? 'Given-When-Then statements'
    : acMentions
      ? 'mentions of acceptance criteria'
      : 'none found in the text';

  const systems = KNOWN_SYSTEMS.filter((name) =>
    new RegExp(`\\b${name.replace(/[/\\]/g, '\\$&')}\\b`, 'i').test(text),
  );
  const systemsTouched = systems.length;
  const systemsNote = systems.length ? systems.slice(0, 4).join(', ') : 'no known systems named';

  // Direct questions, plus the usual placeholders for an unanswered decision.
  const questionMarks = countMatches(text, /\?/g);
  const placeholders = countMatches(text, /\b(?:TBD|TBC|open question|to be confirmed|to be decided)\b/gi);
  const openQuestions = questionMarks + placeholders;
  const openQuestionsNote = openQuestions
    ? `${questionMarks} question${questionMarks === 1 ? '' : 's'}, ${placeholders} TBD/TBC`
    : 'nothing left open';

  return {
    userStories,
    acceptanceCriteria,
    systemsTouched,
    openQuestions,
    notes: {
      userStories: userStoriesNote,
      acceptanceCriteria: acceptanceCriteriaNote,
      systemsTouched: systemsNote,
      openQuestions: openQuestionsNote,
    },
  };
}
