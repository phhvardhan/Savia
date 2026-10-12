import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Section } from '../components/ui/Section';
import { StatGrid } from '../components/ui/StatGrid';
import { StatusPill } from '../components/ui/StatusPill';
import { GAPS_FILTER } from '../data/inventoryFilters';
import styles from './CoveragePage.module.css';

const STORIES = [
  {
    id: 'jgfy-2812',
    name: 'JGFY-2812 · Add Category Code to the coding block',
    state: 'Complete',
    percent: 100,
    meta: '8 of 8 criteria · 24 cases',
  },
  {
    id: 'jgfy-5303',
    name: 'JGFY-5303 · Consolidation Unit',
    state: 'Complete',
    percent: 100,
    meta: '8 of 8 criteria · 26 cases',
  },
  {
    id: 'jgfy-8052',
    name: 'JGFY-8052 · Consolidation Unit derivation',
    state: '2 gaps',
    percent: 50,
    meta: '2 of 4 criteria · 12 cases',
  },
];

const NUMBERS = [
  { value: '62', caption: 'test cases', hint: 'ready for SIT' },
  { value: '18 of 20', caption: 'criteria covered', hint: 'the two gaps are named', tone: 'red' as const },
  { value: '4', caption: 'personas covered', hint: 'all from the design' },
  { value: '~11 hrs', caption: 'of writing replaced', hint: '62 cases at ~11 min each', tone: 'red' as const },
];

export function CoveragePage() {
  const navigate = useNavigate();

  return (
    <Section
      id="coverage"
      size="compact"
      title={
        <>
          <span className={styles.titleRed}>62 cases.</span> 18 of 20 criteria covered.
        </>
      }
      subtitle="This is the number that matters, and Savia leads with it. Two criteria are not covered and it will not pretend otherwise."
      aside={
        <StatusPill tone="alert" dot>
          Your turn · Test Lead
        </StatusPill>
      }
    >
      <Card panel className={styles.panel}>
        <div className={styles.block}>
          <h2 className={styles.label}>Coverage by story</h2>
          {STORIES.map((story) => {
            const complete = story.state === 'Complete';
            return (
              <section key={story.id} className={styles.story}>
                <div className={styles.storyHead}>
                  <h3 className={styles.storyName}>{story.name}</h3>
                  <span
                    className={`${styles.storyPill} ${complete ? styles.pillComplete : styles.pillGaps}`}
                  >
                    {!complete && <span className={styles.pillDot} aria-hidden="true" />}
                    {story.state}
                  </span>
                </div>
                <div
                  className={styles.track}
                  role="img"
                  aria-label={`${story.meta} covered`}
                >
                  <div
                    className={`${styles.fill} ${complete ? styles.fillComplete : styles.fillGaps}`}
                    style={{ width: `${story.percent}%` }}
                  />
                </div>
                <p className={styles.storyMeta}>{story.meta}</p>
              </section>
            );
          })}
        </div>

        <div className={styles.statsBorder}>
          <StatGrid label="The run in numbers" labelTone="ink" stats={NUMBERS} />
        </div>

        <div className={styles.actions}>
          <Button
            variant="primary"
            // Lands on the inventory already narrowed to the two open rows,
            // so it doesn't just repeat the button beside it.
            onClick={() => navigate('/inventory', { state: { filter: GAPS_FILTER } })}
          >
            Look at the two gaps
          </Button>
          <Button onClick={() => navigate('/inventory')}>Open the full inventory</Button>
        </div>
      </Card>
    </Section>
  );
}
