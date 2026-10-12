import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { DataTable } from '../components/ui/DataTable';
import { Section } from '../components/ui/Section';
import { StatusPill } from '../components/ui/StatusPill';
import { DEFAULT_FILTER, INVENTORY_FILTERS } from '../data/inventoryFilters';
import type { InventoryFilter } from '../data/inventoryFilters';
import styles from './InventoryPage.module.css';

const FILTERS = INVENTORY_FILTERS;

type CaseState = 'Ready' | 'Edited' | 'Partial' | 'Needs you';

const CASES: Array<{
  tc: string;
  name: string;
  persona: string;
  covers: string;
  type: string;
  state: CaseState;
}> = [
  { tc: '01', name: 'Create a Trade Supplier change request via BP UI', persona: 'Requestor · Trade Supplier', covers: 'AC-001 · JGFY-2812', type: 'New', state: 'Ready' },
  { tc: '02', name: 'Duplicate check on an existing business partner', persona: 'Requestor · Trade Supplier', covers: 'AC-002 · JGFY-2812', type: 'New', state: 'Ready' },
  { tc: '03', name: 'GSDB fields are read-only, others stay editable', persona: 'Requestor · Trade Supplier', covers: 'AC-003 · JGFY-2812', type: 'New', state: 'Ready' },
  { tc: '04', name: 'Category Code accepts a value from the allowed list', persona: 'Finance Master Data Maintainer', covers: 'AC-001 · JGFY-5303', type: 'New', state: 'Edited' },
  { tc: '05', name: 'Posting is rejected when Consolidation Unit is missing', persona: 'Finance Master Data Maintainer', covers: 'AC-002 · JGFY-5303', type: 'Negative', state: 'Ready' },
  { tc: '06', name: 'Derivation runs on every ledger during posting', persona: 'GS Finance Display', covers: 'AC-001 · JGFY-8052', type: 'New', state: 'Partial' },
  { tc: '07', name: 'Expected result is undefined cannot be written', persona: 'GS Finance Display', covers: 'AC-002 · JGFY-8052', type: '—', state: 'Needs you' },
];

const STATE_CLASS: Record<CaseState, string> = {
  Ready: styles.statusReady,
  Edited: styles.statusEdited,
  Partial: styles.statusPartial,
  'Needs you': styles.statusNeeds,
};

export function InventoryPage() {
  const navigate = useNavigate();
  const location = useLocation();

  // Coverage deep-links here asking for a specific chip ("the two gaps").
  // Anything unrecognised falls back to showing everything.
  const requested = (location.state as { filter?: InventoryFilter } | null)?.filter;
  const [filter, setFilter] = useState<InventoryFilter>(
    requested && FILTERS.includes(requested) ? requested : DEFAULT_FILTER,
  );

  return (
    <Section
      id="inventory"
      title="The inventory, one row per case"
      size="compact"
      subtitle="Every case says which criterion it proves. Edit any row, add one Savia missed, or open a case to see its steps."
      aside={<StatusPill tone="draft">Draft · not pushed to Jira</StatusPill>}
    >
      <Card panel className={styles.panel}>
        <div className={styles.filters}>
          <div className={styles.filterList} role="group" aria-label="Filter test cases">
            {FILTERS.map((item) => (
              <button
                key={item}
                type="button"
                aria-pressed={filter === item}
                className={`${styles.filter} ${filter === item ? styles.filterActive : ''}`}
                onClick={() => setFilter(item)}
              >
                {item}
              </button>
            ))}
          </div>
          <button type="button" className={styles.personaSelect}>
            Persona · all 4 <span aria-hidden="true">▾</span>
          </button>
        </div>

        <DataTable
          caption="Every test case, the persona that runs it and the criterion it proves"
          minWidth={980}
          columns={[
            { key: 'tc', label: 'TC', width: '6%' },
            { key: 'name', label: 'Test case' },
            { key: 'persona', label: 'Persona', width: '20%' },
            { key: 'covers', label: 'Covers', width: '14%' },
            { key: 'type', label: 'Type', width: '9%' },
            { key: 'status', label: 'Status', width: '12%' },
          ]}
          rows={CASES.map((item) => ({
            id: item.tc,
            cells: [
              <span key="tc" className={styles.tc}>{item.tc}</span>,
              item.name,
              item.persona,
              item.covers,
              item.type,
              <span key="status" className={`${styles.statusPill} ${STATE_CLASS[item.state]}`}>
                {item.state === 'Needs you' && <span className={styles.statusDot} aria-hidden="true" />}
                {item.state}
              </span>,
            ],
          }))}
        />

        <div className={styles.footer}>
          <div>
            <h2 className={styles.footerTitle}>Approve the inventory</h2>
            <p className={styles.footerBody}>
              Approval is what lets it reach Jira. The two open rows can be accepted with a reason or sent back.
            </p>
          </div>
          <div className={styles.footerActions}>
            <Button variant="primary" onClick={() => navigate('/gaps')}>
              Approve and assign
            </Button>
            <Button>Add a case</Button>
          </div>
        </div>
      </Card>
    </Section>
  );
}
