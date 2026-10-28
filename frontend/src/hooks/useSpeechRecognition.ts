import { useState, useRef, useCallback, useEffect } from 'react';
import { uploadFile } from '../lib/api';

// Dictation without the browser's cloud speech service (blocked on the J&J network):
// record the mic with MediaRecorder, then have the backend transcribe it with local Whisper.
// The text arrives after you stop, not word by word.

export interface UseSpeechRecognitionReturn {
  isListening: boolean;
  isTranscribing: boolean;
  transcript: string;
  hasSupport: boolean;
  error: string | null;
  startListening: () => void;
  stopListening: () => void;
  resetTranscript: () => void;
}

export function useSpeechRecognition(): UseSpeechRecognitionReturn {
  const [isListening, setIsListening] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState<string | null>(null);

  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  // getUserMedia only exists on https:// or localhost
  const hasSupport =
    typeof window !== 'undefined' && Boolean(navigator.mediaDevices?.getUserMedia) && typeof MediaRecorder !== 'undefined';

  const startListening = useCallback(async () => {
    if (recorderRef.current) return;
    setTranscript('');
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (e) => e.data.size && chunksRef.current.push(e.data);
      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        recorderRef.current = null;
        setIsTranscribing(true);
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType });
        try {
          const { text } = await uploadFile<{ text: string }>('/ingestion/dictate', [
            new File([blob], 'dictation.webm', { type: blob.type }),
          ]);
          if (text) setTranscript(text);
          else setError('Speech error: no-speech');
        } catch (err) {
          setError(err instanceof Error ? err.message : 'Could not transcribe the recording.');
        } finally {
          setIsTranscribing(false);
        }
      };
      recorderRef.current = recorder;
      recorder.start();
      setIsListening(true);
    } catch (err) {
      const name = err instanceof DOMException ? err.name : '';
      setError(name === 'NotAllowedError' ? 'Speech error: not-allowed' : 'Could not start the microphone.');
    }
  }, []);

  const stopListening = useCallback(() => {
    if (recorderRef.current?.state === 'recording') recorderRef.current.stop();
    setIsListening(false);
  }, []);

  const resetTranscript = useCallback(() => setTranscript(''), []);

  // Release the mic if the page unmounts mid-recording
  useEffect(
    () => () => {
      if (recorderRef.current?.state === 'recording') recorderRef.current.stop();
    },
    [],
  );

  return { isListening, isTranscribing, transcript, hasSupport, error, startListening, stopListening, resetTranscript };
}
