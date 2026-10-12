import type { ReactNode } from 'react';
import styles from './StatGrid.module.css';

export interface Stat {
  /** A node, so a page can show a spinner while the figure is pending. */
  value: ReactNode;
  caption: string;
  hint: string;
  tone?: 'red' | 'orange' | 'blue' | 'green';
  /** Some panels print the hint in red rather than grey. */
  hintTone?: 'red';
  /** Colour the caption with the value's tone too. */
  tintCaption?: boolean;
}

interface StatGridProps {
  label: string;
  /** The Reviews panel prints its label in ink rather than red. */
  labelTone?: 'red' | 'ink' | 'blue';
  stats: Stat[];
}

export function StatGrid({ label, labelTone = 'red', stats }: StatGridProps) {
  return (
    <div className={styles.wrap}>
      <h3
        className={`${styles.label} ${
          labelTone === 'ink' ? styles.labelInk : labelTone === 'blue' ? styles.labelBlue : ''
        }`}
      >
        {label}
      </h3>
      <dl className={styles.grid}>
        {stats.map((stat) => (
          <div key={stat.caption} className={styles.item}>
            <dd className={`${styles.value} ${stat.tone ? styles[stat.tone] : ''}`}>{stat.value}</dd>
            <dt className={`${styles.caption} ${stat.tintCaption && stat.tone ? styles[stat.tone] : ''}`}>
              {stat.caption}
            </dt>
            <dd className={`${styles.hint} ${stat.hintTone === 'red' ? styles.hintRed : ''}`}>{stat.hint}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
