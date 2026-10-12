/**
 * Small interface glyphs. The Figma export supplied no icon assets, so these
 * are minimal inline SVGs matching the stroke weight in the reference.
 */
const base = {
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.6,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
};

/**
 * Supplied glyphs. Stroke is `currentColor` rather than the #767E85 in the
 * source files, so the icons follow their label on hover and when active.
 */
const stroke = {
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.7,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
};

export function SearchIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true" {...stroke}>
      <path d="M8.25 13.5C11.1495 13.5 13.5 11.1495 13.5 8.25C13.5 5.35051 11.1495 3 8.25 3C5.35051 3 3 5.35051 3 8.25C3 11.1495 5.35051 13.5 8.25 13.5Z" />
      <path d="M15 15L12.3 12.3" />
    </svg>
  );
}

export function BellIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true" {...stroke}>
      <path d="M15 7C15 5.67392 14.4733 4.40215 13.5356 3.46447C12.5979 2.52678 11.3261 2 10 2C8.67396 2 7.40219 2.52678 6.46451 3.46447C5.52682 4.40215 5.00004 5.67392 5.00004 7C5.00004 12.5 2.83337 13.3333 2.83337 13.3333H17.1667C17.1667 13.3333 15 12.5 15 7Z" />
      <path d="M11.5 16.3333C11.3635 16.6151 11.1504 16.8527 10.8851 17.019C10.6199 17.1853 10.3131 17.2735 10 17.2735C9.68691 17.2735 9.38014 17.1853 9.11485 17.019C8.84956 16.8527 8.63647 16.6151 8.5 16.3333" />
    </svg>
  );
}

export function HelpIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true" {...stroke}>
      <path d="M8 14C11.3137 14 14 11.3137 14 8C14 4.68629 11.3137 2 8 2C4.68629 2 2 4.68629 2 8C2 11.3137 4.68629 14 8 14Z" />
      <path d="M6.40004 6.40002C6.39162 6.09168 6.46893 5.78705 6.62337 5.52004C6.77782 5.25304 7.00332 5.03413 7.2748 4.88768C7.54628 4.74124 7.85306 4.673 8.16102 4.69057C8.46897 4.70814 8.76601 4.81083 9.01907 4.9872C9.27212 5.16358 9.47127 5.40671 9.59434 5.68956C9.71741 5.9724 9.75958 6.28384 9.71614 6.58922C9.67271 6.89461 9.54538 7.18194 9.34832 7.41925C9.15127 7.65656 8.89223 7.83453 8.60003 7.93335C8.20003 8.13335 8.00003 8.46669 8.00003 8.86669V9.20002" />
      <path d="M8 11.5333V11.54" />
    </svg>
  );
}

export function ChevronDownIcon() {
  return (
    <svg width="10" height="10" viewBox="0 0 10 10" aria-hidden="true" {...base}>
      <path d="m2 3.8 3 3 3-3" />
    </svg>
  );
}

export function ExternalIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 11 11" aria-hidden="true" {...base}>
      <path d="M3 8 8 3" />
      <path d="M4 3h4v4" />
    </svg>
  );
}

export function ArrowRightIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true" {...base}>
      <path d="M2.5 7h9" />
      <path d="M8 3.5 11.5 7 8 10.5" />
    </svg>
  );
}

/* Finder input modes on the home hero ------------------------------------- */

/** Describe — a pencil writing a line. */
export function PencilIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true" {...stroke}>
      <path d="M11.3 2.7a1.7 1.7 0 0 1 2.4 2.4L5.4 13.4 2 14l.6-3.4 8.7-7.9Z" />
      <path d="M10.3 3.7l2 2" />
    </svg>
  );
}

/** Speak — a microphone on its stand. */
export function MicIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true" {...stroke}>
      <path d="M8 1.8a1.9 1.9 0 0 1 1.9 1.9v4a1.9 1.9 0 0 1-3.8 0v-4A1.9 1.9 0 0 1 8 1.8Z" />
      <path d="M12 7a4 4 0 0 1-8 0" />
      <path d="M8 11v3.2M6.2 14.2h3.6" />
    </svg>
  );
}

/** Upload a document — a page with a turned corner and an up arrow. */
export function DocumentIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true" {...stroke}>
      <path d="M9 1.7H4.4a1.4 1.4 0 0 0-1.4 1.4v9.8a1.4 1.4 0 0 0 1.4 1.4h7.2a1.4 1.4 0 0 0 1.4-1.4V5.7L9 1.7Z" />
      <path d="M9 1.7v4h4" />
      <path d="M8 11.8V8.2M6.5 9.5 8 8l1.5 1.5" />
    </svg>
  );
}

/** Upload a recording — a play frame, for audio or video files. */
export function RecordingIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true" {...stroke}>
      <path d="M2.4 4.2a1.5 1.5 0 0 1 1.5-1.5h8.2a1.5 1.5 0 0 1 1.5 1.5v7.6a1.5 1.5 0 0 1-1.5 1.5H3.9a1.5 1.5 0 0 1-1.5-1.5V4.2Z" />
      <path d="M6.7 6.2l3.4 1.8-3.4 1.8V6.2Z" />
    </svg>
  );
}

/** Paste a Jira key — a key. */
export function KeyIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true" {...stroke}>
      <path d="M10.4 2.6a3.4 3.4 0 1 1-2.6 5.6L3 13l-1.2-.2L1.6 11l.9-.9 1.1.2.2-1.1 1-1 1.1.2.2-1.1.7-.7a3.4 3.4 0 0 1 3.6-4Z" />
      <path d="M11.2 5.2h.01" />
    </svg>
  );
}

/** Upload — an arrow rising out of a tray. */
export function UploadIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true" {...stroke}>
      <path d="M2.6 10.6v2a1.4 1.4 0 0 0 1.4 1.4h8a1.4 1.4 0 0 0 1.4-1.4v-2" />
      <path d="M8 2.2v8" />
      <path d="M5.2 5l2.8-2.8L10.8 5" />
    </svg>
  );
}

/* Agent marks for the library table ---------------------------------------- */

/** MoM — a page of notes with ruled lines. */
export function NotesIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true" {...stroke}>
      <path d="M4 2.4h10a1.4 1.4 0 0 1 1.4 1.4v10.4A1.4 1.4 0 0 1 14 15.6H4a1.4 1.4 0 0 1-1.4-1.4V3.8A1.4 1.4 0 0 1 4 2.4Z" />
      <path d="M5.6 6.2h6.8M5.6 9h6.8M5.6 11.8h4" />
    </svg>
  );
}

/** User stories — stacked cards. */
export function StackIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true" {...stroke}>
      <path d="M2.6 5.6 9 2.4l6.4 3.2L9 8.8 2.6 5.6Z" />
      <path d="m2.6 9 6.4 3.2L15.4 9" />
      <path d="m2.6 12.4 6.4 3.2 6.4-3.2" />
    </svg>
  );
}

/** Gap analysis & RTM — a traceability grid. */
export function MatrixIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true" {...stroke}>
      <path d="M3 3h12v12H3z" />
      <path d="M3 7h12M3 11h12M7 3v12M11 3v12" />
    </svg>
  );
}

/** DDL3 — a design blueprint with a drawn shape. */
export function BlueprintIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true" {...stroke}>
      <path d="M2.6 3.8h12.8v10.4H2.6z" />
      <path d="M5.6 11.2V7.4h3.2v3.8M8.8 8.6h3.6" />
    </svg>
  );
}

/** Enterprise architecture — layered blocks. */
export function LayersIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true" {...stroke}>
      <path d="M3 3.4h4.4v4.4H3zM10.6 3.4H15v4.4h-4.4zM3 10.2h4.4v4.4H3zM10.6 10.2H15v4.4h-4.4z" />
    </svg>
  );
}

/** KDD for DAB — a governance dossier. */
export function DossierIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true" {...stroke}>
      <path d="M2.6 5a1.4 1.4 0 0 1 1.4-1.4h2.8l1.4 1.8H14A1.4 1.4 0 0 1 15.4 6.8v6.4A1.4 1.4 0 0 1 14 14.6H4a1.4 1.4 0 0 1-1.4-1.4V5Z" />
      <path d="M6.6 10.4h4.8" />
    </svg>
  );
}

/** Change impact — a branching route. */
export function BranchIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true" {...stroke}>
      <path d="M5.4 4.2v5.2a2.4 2.4 0 0 0 2.4 2.4h4.8" />
      <path d="M5.4 4.2a1.6 1.6 0 1 0 0-.1M12.6 11.8a1.6 1.6 0 1 0 0-.1M5.4 14.4a1.6 1.6 0 1 0 0-.1" />
    </svg>
  );
}

/** TEST — a sample vial. */
export function FlaskIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true" {...stroke}>
      <path d="M7.2 2.6h3.6M7.8 2.6v4.2L4.2 13a1.4 1.4 0 0 0 1.2 2.1h7.2A1.4 1.4 0 0 0 13.8 13l-3.6-6.2V2.6" />
      <path d="M6 10.6h6" />
    </svg>
  );
}

/** Readiness scoring — a target. */
export function TargetIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true" {...stroke}>
      <path d="M9 15.4A6.4 6.4 0 1 0 9 2.6a6.4 6.4 0 0 0 0 12.8Z" />
      <path d="M9 12.2a3.2 3.2 0 1 0 0-6.4 3.2 3.2 0 0 0 0 6.4Z" />
      <path d="M9 9.8a.8.8 0 1 0 0-1.6.8.8 0 0 0 0 1.6Z" />
    </svg>
  );
}

/** Cutover — a flag planted at the go-live point. */
export function FlagIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true" {...stroke}>
      <path d="M4.4 15.4V2.8" />
      <path d="M4.4 3.4h8.2l-1.8 3 1.8 3H4.4" />
    </svg>
  );
}

/** A folder that failed a check — used where something required is absent. */
export function FolderErrorIcon() {
  return (
    <svg width="26" height="26" viewBox="0 0 26 26" aria-hidden="true" {...stroke}>
      <path d="M2.6 6.6a1.6 1.6 0 0 1 1.6-1.6h5.2l2 2.4h10.4a1.6 1.6 0 0 1 1.6 1.6v10.8a1.6 1.6 0 0 1-1.6 1.6H4.2a1.6 1.6 0 0 1-1.6-1.6V6.6Z" />
      <path d="M9.4 15.4l4 4M13.4 15.4l-4 4" />
    </svg>
  );
}
