/**
 * Module-scoped guard for expensive one-off calls.
 *
 * A `useRef` is not enough: React StrictMode unmounts and remounts every
 * component in development, which creates a fresh ref and lets the call fire a
 * second time. Two concurrent LLM runs cost twice as much and contend with
 * each other. This registry lives outside React, so a remount sees the key is
 * already in flight and stands down. It resets on a real page reload.
 */
const inFlight = new Set<string>();

/** True if this key was free and is now claimed by the caller. */
export function claim(key: string): boolean {
  if (inFlight.has(key)) return false;
  inFlight.add(key);
  return true;
}

/** Let a key run again, e.g. after a failure the person may retry. */
export function release(key: string): void {
  inFlight.delete(key);
}

/** Clear all in-flight keys to allow starting a completely fresh run. */
export function resetOnce(): void {
  inFlight.clear();
}

