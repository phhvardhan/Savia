import { useState } from 'react';
import type { FormEvent } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { Logo } from '../components/layout/Logo';
import { Button } from '../components/ui/Button';
import { ArrowRightIcon } from '../components/ui/Icons';
import { useAuth } from '../auth/context';
import { ApiError } from '../lib/api';
import styles from './LoginPage.module.css';

export function LoginPage() {
  const { user, loading, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const from = (location.state as { from?: string } | null)?.from ?? '/work';

  if (loading) return null;
  if (user) return <Navigate to={from} replace />;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (submitting) return;

    setError(null);
    setSubmitting(true);
    try {
      await login(username.trim(), password);
      navigate(from, { replace: true });
    } catch (caught) {
      setError(
        caught instanceof ApiError ? caught.message : 'Something went wrong. Please try again.',
      );
      setSubmitting(false);
    }
  }

  return (
    <main className={styles.page}>
      <section className={styles.panel} aria-labelledby="login-title">
        <div className={styles.brand}>
          <Logo />
          <span className={styles.brandText}>
            <span className={styles.brandEyebrow}>J&amp;J</span>
            <span className={styles.brandName}>SAVIA</span>
          </span>
        </div>

        <h1 id="login-title" className={styles.title}>
          Sign in to SAVIA
        </h1>
        <p className={styles.body}>
          Use your J&amp;J network account. SAVIA checks it against Active Directory and keeps you
          signed in on this device.
        </p>

        <form className={styles.form} onSubmit={handleSubmit} noValidate>
          <div className={styles.field}>
            <label className={styles.label} htmlFor="login-username">
              Username or email
            </label>
            <input
              id="login-username"
              className={styles.input}
              type="text"
              autoComplete="username"
              autoFocus
              required
              value={username}
              onChange={(event) => setUsername(event.target.value)}
            />
          </div>

          <div className={styles.field}>
            <label className={styles.label} htmlFor="login-password">
              Password
            </label>
            <input
              id="login-password"
              className={styles.input}
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </div>

          {error ? (
            <p className={styles.error} role="alert">
              {error}
            </p>
          ) : null}

          <Button
            variant="primary"
            pill
            type="submit"
            className={styles.submit}
            disabled={submitting || !username.trim() || !password}
          >
            {submitting ? 'Signing in…' : 'Sign in'}
            {submitting ? null : <ArrowRightIcon />}
          </Button>
        </form>

        <p className={styles.foot}>
          Trouble signing in? Contact the SAVIA delivery team.
        </p>
      </section>
    </main>
  );
}
