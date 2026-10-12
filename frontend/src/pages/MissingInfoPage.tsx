import { useNavigate } from 'react-router-dom';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Section } from '../components/ui/Section';
import { FolderErrorIcon } from '../components/ui/Icons';
import styles from './MissingInfoPage.module.css';

const HAS: Array<{ id: string; title: string; badge: string; text: string }> = [
  { id: 'stories', title: '2 of 3 stories', badge: 'Approved', text: 'JGFY-2812 · JGFY-5303' },
  { id: 'brd', title: 'The source BRD', badge: 'Read', text: '34 pages, read in full' },
  { id: 'context', title: 'Project context', badge: 'Loaded', text: 'Release, RICEFW ID, template' },
  { id: 'systems', title: 'Systems in scope', badge: 'Found', text: '4, from the Interface Hub' },
];

export function MissingInfoPage() {
  const navigate = useNavigate();

  return (
    <Section
      id="missing-info"
      title="One thing is missing, and it is a small one"
      size="compact"
      subtitle="Savia will not start DDL3 with a guess in place of an approval. It has everything else this is the only thing it needs from you."
    >
      <Card panel className={styles.panel}>
        <div className={styles.block}>
          <h2 className={styles.label}>What is missing</h2>
          <div className={styles.banner}>
            <span className={styles.bannerIcon}>
              <FolderErrorIcon />
            </span>
            <div>
              <h3 className={styles.bannerTitle}>JGFY-8052 has not been approved</h3>
              <p className={styles.bannerText}>
                The other two stories are approved and ready. DDL3 writes designs from approved requirements only
                starting on a draft story produces a design that has to be rewritten the moment the story changes.
              </p>
            </div>
          </div>
        </div>

        <div className={`${styles.block} ${styles.divider}`}>
          <h2 className={styles.label}>What it already has</h2>
          <ul className={styles.hasGrid}>
            {HAS.map((item) => (
              <li key={item.id} className={styles.hasCard}>
                <div className={styles.hasHead}>
                  <h3 className={styles.hasTitle}>{item.title}</h3>
                  <Badge tone="solidGreen">{item.badge}</Badge>
                </div>
                <p className={styles.hasText}>{item.text}</p>
              </li>
            ))}
          </ul>
        </div>

        <div className={styles.footer}>
          <Button variant="primary" onClick={() => navigate('/writing')}>
            Run on the two approved stories
          </Button>
          <Button>Ask R. Kumar to approve it</Button>
        </div>
      </Card>
    </Section>
  );
}
