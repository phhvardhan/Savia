import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { DataTable } from '../components/ui/DataTable';
import { Section } from '../components/ui/Section';
import { StatusPill } from '../components/ui/StatusPill';
import styles from './HelpPage.module.css';

const TILES = [
  { key: 'from', label: 'From', value: 'DDL3 · functional design v1', tone: styles.tileFrom },
  { key: 'to', label: 'To', value: 'TEST · SIT, Release 2.1', tone: styles.tileTo },
  { key: 'by', label: 'Released by', value: 'D. Blanco, Design Lead', tone: styles.tileBy },
  { key: 'when', label: 'When', value: '21 Sept, 14:06', tone: styles.tileWhen },
];

const CROSSED = [
  ['Project and release', 'TIME · Release 2.1 · RICEFW FIN-0002', 'Set the test cycle and naming'],
  ['Approved user stories', 'JGFY-2812 · JGFY-5303 · JGFY-8052', 'Grouped the inventory by story'],
  ['Acceptance criteria', '20 criteria across the three stories', 'One or more cases per criterion'],
  ['Design decisions', '4, including the section 5 derivation rule', 'Shaped the expected results'],
  ['Personas', '4, named in the design', 'Split the 62 cases between them'],
  ['Systems in scope', 'Finance S4 · MDG · BTP · TIME', 'Wrote the preconditions'],
  ['Known weak spots', 'AC-002 has no expected result', 'Reported it as a gap, did not paper over it'],
];

export function HelpPage() {
  const navigate = useNavigate();
  return (
    <Section
      id="handoff"
      title="Exactly what crossed between them"
      titleClassName={styles.pageTitle}
      subtitle={
        <>
          This is the handoff, field by field. Not a claim that the agents talked to each other the actual contents,
          <br />
          the approval that released it, and what TEST did with each part.
        </>
      }
      aside={<StatusPill>Recorded · 21 Sept, 14:06</StatusPill>}
    >
      <Card panel className={styles.panel}>
        <div className={styles.handoff}>
          <h2 className={styles.label}>The handoff</h2>
          <dl className={styles.tiles}>
            {TILES.map((tile) => (
              <div key={tile.key} className={`${styles.tile} ${tile.tone}`}>
                <dt className={styles.tileLabel}>{tile.label}</dt>
                <dd className={styles.tileValue}>{tile.value}</dd>
              </div>
            ))}
          </dl>
        </div>

        <DataTable
          caption="Each field that crossed from DDL3 to TEST"
          columns={[
            { key: 'crossed', label: 'What crossed', width: '26%' },
            { key: 'value', label: 'Value', width: '36%' },
            { key: 'did', label: 'What TEST did with it' },
          ]}
          rows={CROSSED.map(([crossed, value, did]) => ({
            id: crossed,
            cells: [crossed, value, did],
          }))}
        />

        <div className={styles.footer}>
          <div className={styles.footerText}>
            <h2 className={styles.footerTitle}>Nothing crossed that was not approved</h2>
            <p className={styles.footerBody}>
              TEST never saw the draft. It read version 1 as the Design Lead approved it, and it can show you which
              part of that version each case came from.
            </p>
          </div>
          <div className={styles.footerActions}>
            <Button
              variant="primary"
              className={styles.approveButton}
              onClick={() => navigate('/projects')}
            >
              Open the approved version
            </Button>
            <Button>See the run history</Button>
          </div>
        </div>
      </Card>
    </Section>
  );
}
