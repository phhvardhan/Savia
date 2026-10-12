import { useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { AttachmentContext } from './attachment';
import type { Attachment } from './attachment';

/**
 * Holds the attachment in memory only. It is deliberately not persisted — a
 * File cannot be revived from storage, and a stale filename with no bytes
 * behind it would be worse than showing nothing.
 */
export function AttachmentProvider({ children }: { children: ReactNode }) {
  const [attachment, setAttachment] = useState<Attachment | null>(null);
  const value = useMemo(() => ({ attachment, setAttachment }), [attachment]);
  return <AttachmentContext.Provider value={value}>{children}</AttachmentContext.Provider>;
}
