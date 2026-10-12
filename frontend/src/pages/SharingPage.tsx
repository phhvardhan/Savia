import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { DataTable } from '../components/ui/DataTable';
import { Section } from '../components/ui/Section';
import { StatusPill } from '../components/ui/StatusPill';
import styles from './SharingPage.module.css';

type Status = 'asked' | 'commented' | 'idle' | 'none';

const PEOPLE: Array<{
  id: string;
  initials: string;
  name: string;
  title: string;
  role: string;
  can: string;
  status: string;
  statusKind: Status;
}> = [
  {
    id: 'blanco',
    initials: 'DB',
    name: 'D. Blanco',
    title: 'Design Lead',
    role: 'Approver',
    can: 'Decides. Nothing moves downstream without them',
    status: 'Asked 4 min ago',
    statusKind: 'asked',
  },
  {
    id: 'kumar',
    initials: 'RK',
    name: 'R. Kumar',
    title: 'Business Analyst',
    role: 'Editor',
    can: 'Edit and comment. Asked about AC-002',
    status: 'Commented',
    statusKind: 'commented',
  },
  {
    id: 'pieretti',
    initials: 'MP',
    name: 'M. Pieretti',
    title: 'Test Lead',
    role: 'Viewer',
    can: 'Read only she needs the context, not the pen',
    status: 'Has not opened it',
    statusKind: 'idle',
  },
  {
    id: 'you',
    initials: 'YOU',
    name: 'You',
    title: 'Business Analyst',
    role: 'Owner',
    can: 'Everything, including who else is on it',
    status: '—',
    statusKind: 'none',
  },
];

const STATUS_CLASS: Record<Status, string> = {
  asked: styles.statusAsked,
  commented: styles.statusCommented,
  idle: styles.statusIdle,
  none: '',
};

export function SharingPage() {
  const navigate = useNavigate();

  return (
    <Section
      id="sharing"
      title="Who sees it, who comments, who decides"
      size="compact"
      subtitle="Sharing gives someone access. Approving is a decision on the record."
      aside={
        <StatusPill tone="alert" dot>
          1 approval outstanding
        </StatusPill>
      }
    >
      <Card panel className={styles.panel}>
        <div className={styles.block}>
          <h2 className={styles.label}>Add someone</h2>
          <div className={styles.addRow}>
            <div className={styles.field}>
              <span className={styles.fieldIcon} aria-hidden="true">
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.6">
                  <circle cx="7" cy="6" r="3" />
                  <path d="M2.5 15c0-2.5 2-4.2 4.5-4.2S11.5 12.5 11.5 15" strokeLinecap="round" />
                  <path d="M13 6.5h3.5M14.75 4.75v3.5" strokeLinecap="round" />
                </svg>
              </span>
              <label className="visually-hidden" htmlFor="share-person">
                Name or email
              </label>
              <input id="share-person" className={styles.fieldInput} placeholder="Name or email" />
            </div>
            <Button>Add as viewer</Button>
            <Button>Add as editor</Button>
            <Button variant="primary">Add as approver</Button>
          </div>
        </div>

        <DataTable
          caption="Who has access to this document and what they can do"
          columns={[
            { key: 'person', label: 'Person', width: '26%' },
            { key: 'role', label: 'Role on this document', width: '18%' },
            { key: 'can', label: 'What they can do' },
            { key: 'status', label: 'Status', width: '17%' },
          ]}
          rows={PEOPLE.map((person) => ({
            id: person.id,
            cells: [
              <span key="person" className={styles.person}>
                <span className={styles.avatar} aria-hidden="true">
                  {person.initials}
                </span>
                <span>
                  <span className={styles.personName}>{person.name}</span>{' '}
                  <span className={styles.personRole}>· {person.title}</span>
                </span>
              </span>,
              <button key="role" type="button" className={styles.roleSelect}>
                {person.role}
                <span className={styles.caret} aria-hidden="true">
                  ▾
                </span>
              </button>,
              person.can,
              person.statusKind === 'none' ? (
                person.status
              ) : (
                <span key="status" className={`${styles.statusPill} ${STATUS_CLASS[person.statusKind]}`}>
                  {person.statusKind === 'asked' && <span className={styles.statusDot} aria-hidden="true" />}
                  {person.status}
                </span>
              ),
            ],
          }))}
        />

        <div className={styles.block}>
          <h2 className={styles.label}>The approval</h2>
          <div className={styles.approval}>
            <span className={styles.approvalAvatar} aria-hidden="true">
              DB
            </span>
            <div className={styles.approvalText}>
              <p className={styles.approvalTitle}>
                Waiting on D. Blanco <span className={styles.approvalAge}>· asked 4 minutes ago</span>
              </p>
              <p className={styles.approvalNote}>
                Version 2, with your note about the open question attached. If they request changes it comes back to
                you with their comments on the exact sections.
              </p>
            </div>
            <div className={styles.approvalActions}>
              <Button>Send a reminder</Button>
              <Button>Change the approver</Button>
            </div>
          </div>
        </div>

        <div className={styles.actions}>
          <Button variant="primary" onClick={() => navigate('/publish')}>
            Open the document
          </Button>
          <Button>See what they will see</Button>
        </div>
      </Card>
    </Section>
  );
}
