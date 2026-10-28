import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { DataTable } from '../components/ui/DataTable';
import { Section } from '../components/ui/Section';
import { StatusPill } from '../components/ui/StatusPill';
import { ApiError } from '../lib/api';
import { AGENT_META, approveWorkflow } from '../lib/savia';
import { useRun, useCurrentRun } from '../state/run';
import styles from './SharingPage.module.css';

const initials = (name: string) =>
  name
    .split(/\s+/)
    .map((w) => w[0])
    .join('')
    .slice(0, 3)
    .toUpperCase();

export function SharingPage() {
  const navigate = useNavigate();
  const { upload } = useRun();
  const { agentId, run } = useCurrentRun();
  const meta = agentId ? AGENT_META[agentId] : undefined;
  const approver = meta?.approver ?? 'You';
  const selfApproved = approver === 'You';
  const [approved, setApproved] = useState(false);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!run || !meta) {
    return (
      <Section id="sharing" title="Nothing to send for approval yet" size="compact">
        <Card panel className={styles.panel}>
          <div className={styles.actions}>
            <Button variant="primary" onClick={() => navigate('/work')}>
              Start a run
            </Button>
          </div>
        </Card>
      </Section>
    );
  }

  // Only the people this run actually has: whoever approves this agent's output, and you.
  const people = [
    ...(selfApproved
      ? []
      : [
          {
            id: 'approver',
            name: approver,
            role: 'Approver',
            can: 'Decides. Nothing is published without this approval',
            status: approved ? 'Approved' : 'Asked just now',
          },
        ]),
    {
      id: 'you',
      name: 'You',
      role: selfApproved ? 'Owner and approver' : 'Owner',
      can: selfApproved ? 'Approves your own output for this agent' : 'Everything, including who else is on it',
      status: selfApproved ? (approved ? 'Approved' : 'Your turn') : '—',
    },
  ];

  const approve = async () => {
    if (!upload) return;
    setWorking(true);
    setError(null);
    try {
      await approveWorkflow(upload.workflow_id, approver, run.artifact_id);
      setApproved(true);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'The approval could not be recorded.');
    } finally {
      setWorking(false);
    }
  };

  return (
    <Section
      id="sharing"
      title="Who sees it, who comments, who decides"
      size="compact"
      subtitle={`${meta.full} · version ${run.version}. Sharing gives someone access. Approving is a decision on the record.`}
      aside={
        approved ? (
          <StatusPill tone="done">Approved</StatusPill>
        ) : (
          <StatusPill tone="alert" dot>
            1 approval outstanding
          </StatusPill>
        )
      }
    >
      <Card panel className={styles.panel}>
        <DataTable
          caption="Who has access to this output and what they can do"
          columns={[
            { key: 'person', label: 'Person', width: '30%' },
            { key: 'role', label: 'Role on this output', width: '20%' },
            { key: 'can', label: 'What they can do' },
            { key: 'status', label: 'Status', width: '17%' },
          ]}
          rows={people.map((person) => ({
            id: person.id,
            cells: [
              <span key="person" className={styles.person}>
                <span className={styles.avatar} aria-hidden="true">
                  {initials(person.name)}
                </span>
                <span className={styles.personName}>{person.name}</span>
              </span>,
              person.role,
              person.can,
              person.status === '—' ? (
                person.status
              ) : (
                <span key="status" className={`${styles.statusPill} ${approved ? styles.statusCommented : styles.statusAsked}`}>
                  {!approved && <span className={styles.statusDot} aria-hidden="true" />}
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
              {initials(approver)}
            </span>
            <div className={styles.approvalText}>
              <p className={styles.approvalTitle}>
                {approved
                  ? `Approved by ${approver}`
                  : selfApproved
                    ? 'This one is yours to approve'
                    : `Waiting on the ${approver}`}
              </p>
              <p className={styles.approvalNote}>
                {error ??
                  (approved
                    ? 'Recorded on the run. You can publish it now.'
                    : `Version ${run.version} of the ${meta.label} output. If changes are needed, go back to the document and ask Savia.`)}
              </p>
            </div>
            <div className={styles.approvalActions}>
              {!approved && (
                <Button onClick={approve} disabled={working}>
                  {working ? 'Recording…' : selfApproved ? 'Approve it' : `Record the ${approver}'s approval`}
                </Button>
              )}
              <Button onClick={() => navigate('/document')}>Back to the document</Button>
            </div>
          </div>
        </div>

        <div className={styles.actions}>
          <Button variant="primary" disabled={!approved} onClick={() => navigate('/publish', { state: { approvedBy: approver } })}>
            Continue to publish
          </Button>
        </div>
      </Card>
    </Section>
  );
}
