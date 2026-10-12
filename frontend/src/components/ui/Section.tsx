import type { ReactNode } from 'react';
import styles from './Section.module.css';

interface SectionProps {
  id?: string;
  eyebrow?: string;
  title: ReactNode;
  subtitle?: ReactNode;
  /** Status pill or filter row shown opposite the heading. */
  aside?: ReactNode;
  /** `compact` is used by sections stacked inside a longer page. */
  size?: 'page' | 'compact';
  /** Extra class on the heading, e.g. the red title on the reading page. */
  titleClassName?: string;
  children: ReactNode;
  className?: string;
}

export function Section({
  id,
  eyebrow,
  title,
  subtitle,
  aside,
  size = 'page',
  titleClassName,
  children,
  className,
}: SectionProps) {
  const headingId = id ? `${id}-title` : undefined;
  const classes = [styles.section];
  if (size === 'compact') classes.push(styles.compact);
  if (className) classes.push(className);

  return (
    <section id={id} aria-labelledby={headingId} className={classes.join(' ')}>
      <div className="shell">
        <div className={styles.head}>
          <div className={styles.headText}>
            {eyebrow && <p className={styles.eyebrow}>{eyebrow}</p>}
            <h1 id={headingId} className={titleClassName ? `${styles.title} ${titleClassName}` : styles.title}>
              {title}
            </h1>
            {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
          </div>
          {aside && <div className={styles.aside}>{aside}</div>}
        </div>
        {children}
      </div>
    </section>
  );
}
