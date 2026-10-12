import type { ButtonHTMLAttributes, ReactNode } from 'react';
import styles from './Button.module.css';

export type ButtonVariant = 'primary' | 'secondary' | 'onRed' | 'ghostOnRed';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  /** Fully rounded — used by the recommendation cards in the Library. */
  pill?: boolean;
  small?: boolean;
  children: ReactNode;
}

export function Button({
  variant = 'secondary',
  pill = false,
  small = false,
  className,
  children,
  type = 'button',
  ...rest
}: ButtonProps) {
  const classes = [styles.base, styles[variant]];
  if (pill) classes.push(styles.pill);
  if (small) classes.push(styles.small);
  if (className) classes.push(className);

  return (
    <button type={type} className={classes.join(' ')} {...rest}>
      {children}
    </button>
  );
}
