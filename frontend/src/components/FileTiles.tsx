import { formatBytes } from '../state/attachment';
import styles from './FileTiles.module.css';

interface FileKind {
  label: string;
  color: string;
  tint: string;
}

const KINDS: Record<string, FileKind> = {
  pdf: { label: 'PDF', color: '#D32F2F', tint: '#FDECEC' },
  document: { label: 'Document', color: '#185ABD', tint: '#E8F0FB' },
  presentation: { label: 'Presentation', color: '#C43E1C', tint: '#FCEDE8' },
  spreadsheet: { label: 'Spreadsheet', color: '#1E7145', tint: '#E6F3EC' },
  text: { label: 'Text', color: '#595959', tint: '#EFEFEF' },
  recording: { label: 'Recording', color: '#7B3FE4', tint: '#F1EAFD' },
};

const EXTENSION_KIND: Record<string, keyof typeof KINDS> = {
  pdf: 'pdf', docx: 'document', doc: 'document', pptx: 'presentation',
  csv: 'spreadsheet', xlsx: 'spreadsheet', xls: 'spreadsheet',
  mp3: 'recording', wav: 'recording', m4a: 'recording', mp4: 'recording', mov: 'recording',
  avi: 'recording', mkv: 'recording', webm: 'recording',
};

function kindOf(file: File): FileKind {
  const ext = file.name.split('.').pop()?.toLowerCase() ?? '';
  if (/^(audio|video)\//.test(file.type)) return KINDS.recording;
  return KINDS[EXTENSION_KIND[ext] ?? 'text'];
}

/** "Employment_Timesheet.xlsx" → "Employment Timesheet" */
const displayName = (name: string) => name.replace(/\.[^.]+$/, '').replace(/[_-]+/g, ' ').trim() || name;

/** One tile per attached file: its name, a coloured type badge, and a remove button. */
export function FileTiles({ files, onRemove }: { files: File[]; onRemove: (index: number) => void }) {
  if (!files.length) return null;
  return (
    <ul className={styles.tiles} aria-label={`${files.length} attached file${files.length === 1 ? '' : 's'}`}>
      {files.map((file, i) => {
        const kind = kindOf(file);
        return (
          <li key={`${file.name}:${file.size}:${file.lastModified}`} className={styles.tile} title={`${file.name} · ${formatBytes(file.size)}`}>
            <button type="button" className={styles.remove} aria-label={`Remove ${file.name}`} onClick={() => onRemove(i)}>
              ×
            </button>
            <span className={styles.name}>{displayName(file.name)}</span>
            <span className={styles.badge} style={{ background: kind.tint, color: kind.color }}>
              <svg viewBox="0 0 16 16" width="12" height="12" aria-hidden="true" className={styles.badgeIcon}>
                <path fill="currentColor" d="M3 1.5A1.5 1.5 0 0 1 4.5 0h5L13 3.5v11a1.5 1.5 0 0 1-1.5 1.5h-7A1.5 1.5 0 0 1 3 14.5zM9 .8V4h3.2z" />
              </svg>
              {kind.label}
            </span>
          </li>
        );
      })}
    </ul>
  );
}
