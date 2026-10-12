import { createContext, useContext } from 'react';

/** What the person attached on the home finder, carried across pages. */
export interface Attachment {
  /** The real File, kept so it can be posted to /ingestion/upload later. */
  file: File;
  name: string;
  /** Bytes. */
  size: number;
  /** 'recording' for audio/video, otherwise 'document'. */
  kind: 'document' | 'recording';
}

interface AttachmentContextValue {
  attachment: Attachment | null;
  setAttachment: (next: Attachment | null) => void;
}

export const AttachmentContext = createContext<AttachmentContextValue | null>(null);

export function useAttachment(): AttachmentContextValue {
  const context = useContext(AttachmentContext);
  if (!context) throw new Error('useAttachment must be used inside an AttachmentProvider');
  return context;
}

/** 1.4 MB, 812 KB, 240 bytes — whichever unit reads best. */
export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} bytes`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/** Extensions app/services/document_parser.py can actually read. */
export const MEDIA_EXTENSIONS = ['.mp3', '.wav', '.m4a', '.mp4', '.mov', '.avi', '.mkv'];
export const DOC_EXTENSIONS = ['.pdf', '.docx', '.doc', '.txt', '.md', '.csv', '.json', '.vtt', '.srt'];
export const ACCEPTED_FILES = [...MEDIA_EXTENSIONS, ...DOC_EXTENSIONS].join(',');

/** Describe a picked File the way every page wants to show it. */
export function attachmentFromFile(file: File): Attachment {
  const isMedia = MEDIA_EXTENSIONS.some((ext) => file.name.toLowerCase().endsWith(ext));
  return {
    file,
    name: file.name,
    size: file.size,
    kind: isMedia ? 'recording' : 'document',
  };
}
