import type { ReactNode } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useRun } from '../../state/run';
import { useAttachment } from '../../state/attachment';
import { resetOnce } from '../../lib/once';
// AUTH DISABLED — restore with: import { useAuth } from '../../auth/context';
import {
  BellIcon,
  ChevronDownIcon,
  ExternalIcon,
  HelpIcon,
  SearchIcon,
} from '../ui/Icons';
import styles from './AppShell.module.css';

const NAV_ITEMS = [
  { label: 'Work', to: '/work' },
  { label: 'Library', to: '/library' },
  { label: 'Studio', to: '/studio' },
  { label: 'Reviews', to: '/reviews' },
  { label: 'Projects', to: '/projects' },
];

/**
 * Stand-in for the signed-in user while auth is switched off.
 * Restoring auth: delete this and bring back `const { user, logout } = useAuth()`
 * along with the account menu (see the git-free copy in App.tsx's restore note).
 */
const DEMO_USER = {
  greeting: 'Mrunal',
  role: 'SAP Delivery',
  avatar: '/assets/avatar.png',
};

export function AppShell({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const { resetAll } = useRun();
  const { setAttachment } = useAttachment();

  const handleStartNewRun = () => {
    resetAll();
    setAttachment(null);
    resetOnce();
    navigate('/work');
  };
  return (
    <>
      <div className={styles.topbar}>
        <div className={styles.topbarInner}>
          <a className={styles.topbarLink} href="https://www.jnj.com" target="_blank" rel="noreferrer">
            J&amp;J Technology
            <ExternalIcon />
          </a>
          <button type="button" className={styles.locale}>
            Global · English
            <ChevronDownIcon />
          </button>
        </div>
      </div>

      <header className={styles.masthead}>
        <div className={styles.mastheadInner}>
          <NavLink to="/work" className={styles.brand}>
            <img
              className={styles.brandMark}
              src="/assets/savia-logo-black 1.png"
              alt="SAVIA — Volume. Velocity. Value."
              width={500}
              height={209}
            />
          </NavLink>

          <nav className={styles.nav} aria-label="Primary">
            <ul className={styles.navList}>
              {NAV_ITEMS.map((item) => (
                <li key={item.to}>
                  <NavLink
                    to={item.to}
                    className={({ isActive }) =>
                      isActive ? `${styles.navLink} ${styles.navLinkActive}` : styles.navLink
                    }
                  >
                    {item.label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>

          <div className={styles.search}>
            <label className="visually-hidden" htmlFor="global-search">
              Search projects, agents, user stories, or a Jira key
            </label>
            <span className={styles.searchIcon}>
              <SearchIcon />
            </span>
            <input
              id="global-search"
              type="search"
              className={styles.searchInput}
              placeholder="Search projects, agents, user stories, or a Jira key"
            />
          </div>

          <div className={styles.mastheadEnd}>
            <button
              type="button"
              className={styles.newRunButton}
              onClick={handleStartNewRun}
              title="Erase all current run data and start completely fresh from document upload"
            >
              <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
                <path d="M8 2v12M2 8h12" />
              </svg>
              Start New Run
            </button>

            <NavLink
              to="/help"
              className={({ isActive }) =>
                isActive ? `${styles.iconButton} ${styles.iconButtonActive}` : styles.iconButton
              }
              aria-label="Help & guidance"
              title="Help & guidance"
            >
              <HelpIcon />
            </NavLink>
            <button type="button" className={styles.iconButton} aria-label="Notifications">
              <BellIcon />
            </button>
            <button type="button" className={styles.user}>
              <img className={styles.avatar} src={DEMO_USER.avatar} alt="" />
              <span className={styles.who}>
                <span className={styles.userGreeting}>Hello, {DEMO_USER.greeting}</span>
                <span className={styles.userRole}>
                  {DEMO_USER.role}
                  <ChevronDownIcon />
                </span>
              </span>
            </button>
          </div>
        </div>
      </header>

      <main className={styles.main}>{children}</main>
    </>
  );
}
