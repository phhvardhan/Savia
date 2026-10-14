import {
  DocumentIcon,
  KeyIcon,
  MicIcon,
  PencilIcon,
  RecordingIcon,
} from '../components/ui/Icons';

export interface InputModeMeta {
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  placeholder: string;
  kind: 'describe' | 'speak' | 'document' | 'recording' | 'jira';
  acceptFiles?: string;
  hint: string;
}

/** The finder's input modes. Shared across Home and Library pages. */
export const INPUT_MODES: InputModeMeta[] = [
  {
    label: 'Describe',
    icon: PencilIcon,
    kind: 'describe',
    placeholder: 'The stories for the coding block extension are approved and there is no design document yet…',
    hint: 'Type a detailed description of what you want Savia to take on.',
  },
  {
    label: 'Speak',
    icon: MicIcon,
    kind: 'speak',
    placeholder: 'Click the mic button or speak into your microphone to dictate your prompt in real-time…',
    hint: 'Speak into your microphone and watch speech convert into text live.',
  },
  {
    label: 'Upload a document',
    icon: DocumentIcon,
    kind: 'document',
    acceptFiles: '.pdf,.docx,.doc,.pptx,.txt,.md,.json',
    placeholder: 'Attach a document file (PDF, DOCX, TXT) or describe its context here…',
    hint: 'Upload a functional specification, design document, or architecture document.',
  },
  {
    label: 'Upload a recording',
    icon: RecordingIcon,
    kind: 'recording',
    acceptFiles: 'video/*,audio/*,.mp4,.webm,.mov,.m4a,.mp3,.wav',
    placeholder: 'Attach a video recording (MP4, WEBM, MOV) or audio clip from a design workshop…',
    hint: 'Upload a video recording or audio clip of your meeting for AI processing.',
  },
  {
    label: 'Paste a Jira key',
    icon: KeyIcon,
    kind: 'jira',
    placeholder: 'e.g. PROJ-123 or SAV-402 (paste Jira key here to fetch issue details)',
    hint: 'Paste a Jira issue or epic key to fetch user stories and requirements automatically.',
  },
];
