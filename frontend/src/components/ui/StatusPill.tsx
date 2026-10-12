import type { ReactNode } from 'react';
import styles from './StatusPill.module.css';

export type StatusTone = 'alert' | 'info' | 'running' | 'done' | 'draft' | 'neutral' | 'plain';

interface StatusPillProps {
  tone?: StatusTone;
  dot?: boolean;
  /** Makes the dot breathe — for a run that is still going. */
  pulse?: boolean;
  children: ReactNode;
}

export function StatusPill({ tone = 'plain', dot = false, pulse = false, children }: StatusPillProps) {
  return (
    <p className={`${styles.pill} ${styles[tone]}`}>
      {dot && (
        <span className={`${styles.dot} ${pulse ? styles.dotPulse : ''}`} aria-hidden="true" />
      )}
      {children}
    </p>
  );
}
