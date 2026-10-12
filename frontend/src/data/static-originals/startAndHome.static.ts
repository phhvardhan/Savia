/** Original hard-coded content for StartPage and HomePage. */

/** StartPage showed a fixed attachment instead of the real upload. */
export const START_ATTACHMENT = {
  thumb: '/assets/attachment-thumb.png',
  fileName: '02a-BRD, Code Block Extension.docx',
  fileMeta: '1.4 MB · 34 pages · added by you, just now',
  ready: 'Ready to read',
};

/** The "A Document" source card carried a fixed Chosen marker. */
export const START_DOCUMENT_CHOSEN = true;

/**
 * HomePage's finder held this as a real value in the textarea, so it had to be
 * deleted before typing. It is now the placeholder instead.
 */
export const PREFILLED_PROMPT =
  'The stories for the coding block extension are approved and there is no design document yet…';

/** The two squares beside the finder were empty placeholder boxes. */
export const FINDER_GLYPHS_WERE_PLACEHOLDERS = true;

/** Input mode tabs were plain strings with no icons. */
export const INPUT_MODES = [
  'Describe',
  'Speak',
  'Upload a document',
  'Upload a recording',
  'Paste a Jira key',
];
