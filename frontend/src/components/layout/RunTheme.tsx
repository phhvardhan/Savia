import type { CSSProperties, ReactNode } from 'react';
import { useLocation } from 'react-router-dom';
import { AGENT_META } from '../../lib/savia';
import { useCurrentRun } from '../../state/run';

/** Screens 05–11 (and TEST's 13–19): one agent's run, so they take that agent's colour. */
const RUN_SCREENS = [
  '/writing', '/document', '/change', '/suggestions', '/decide', '/sharing', '/publish',
  '/test-ready', '/test-writing', '/coverage', '/inventory', '/gaps', '/approve', '/execution',
];

/** The accent tokens the pages already use (--red, --brand-red…), set to one colour. */
export function accentVars(color: string): CSSProperties {
  return {
    '--tone': color,
    '--red': color,
    '--brand-red': color,
    '--red-dark': `color-mix(in srgb, ${color} 82%, black)`,
    '--red-tint': `color-mix(in srgb, ${color} 9%, white)`,
  } as CSSProperties;
}

/** Recolours the run screens in the chosen agent's accent; every other page keeps the brand red. */
export function RunTheme({ children }: { children: ReactNode }) {
  const { pathname } = useLocation();
  const { agentId } = useCurrentRun();
  const color = agentId ? AGENT_META[agentId]?.color : undefined;
  if (!color || !RUN_SCREENS.includes(pathname)) return children;
  // display: contents adds no box, so layout is untouched; the variables still inherit.
  return <div style={{ display: 'contents', ...accentVars(color) }}>{children}</div>;
}
