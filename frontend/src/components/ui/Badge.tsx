import type { ReactNode } from 'react';
import styles from './Badge.module.css';

export type BadgeTone =
  | 'available'
  | 'solidGreen'
  | 'inReview'
  | 'comingSoon'
  | 'waiting'
  | 'running'
  | 'needsYou'
  | 'doneSoft'
  | 'runningSoft';

interface BadgeProps {
  tone: BadgeTone;
  /** Leading status dot, as used by the "Running" and "Needs you" states. */
  dot?: boolean;
  children: ReactNode;
}

export function Badge({ tone, dot = false, children }: BadgeProps) {
  return (
    <span className={`${styles.badge} ${styles[tone]}`}>
      {dot && <span className={styles.dot} aria-hidden="true" />}
      {children}
    </span>
  );
}
