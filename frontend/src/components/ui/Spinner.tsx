import styles from './Spinner.module.css';

/**
 * Indeterminate spinner. Sized in `em` so it matches whatever text it sits in
 * — it stands in for a stat value while the number is still being worked out.
 */
export function Spinner({ label = 'Loading' }: { label?: string }) {
  return (
    <>
      <span className={styles.spinner} aria-hidden="true" />
      <span className="visually-hidden">{label}</span>
    </>
  );
}
