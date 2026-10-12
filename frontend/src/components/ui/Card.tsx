import type { ElementType, HTMLAttributes, ReactNode } from 'react';
import styles from './Card.module.css';

interface CardProps extends HTMLAttributes<HTMLElement> {
  /** Larger corner radius used by the big page panels. */
  panel?: boolean;
  padded?: boolean;
  as?: ElementType;
  children: ReactNode;
}

export function Card({
  panel = false,
  padded = false,
  as: Tag = 'div',
  className,
  children,
  ...rest
}: CardProps) {
  const classes = [styles.card];
  if (panel) classes.push(styles.flush);
  if (padded) classes.push(styles.padded);
  if (className) classes.push(className);

  return (
    <Tag className={classes.join(' ')} {...rest}>
      {children}
    </Tag>
  );
}
