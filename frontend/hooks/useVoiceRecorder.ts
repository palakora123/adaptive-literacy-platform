'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

export type RecorderState = 'idle' | 'requesting' | 'recording' | 'processing' | 'error';

export interface RecorderOptions {
  /** Hard stop after this long, so a forgotten mic cannot upload 20MB. */
  maxDurationMs?: number;
  /** Auto-stop after this much continuous silence once speech has started. */
  silenceTimeoutMs?: number;
  /** RMS level below which audio counts as silence (0-1). */
  silenceThreshold?: number;
  onComplete?: (blob: Blob, mimeType: string) => void | Promise<void>;
  onError?: (message: string) => void;
}

/** Pick a container the browser can actually produce. Safari only has mp4. */
function pickMimeType(): string {
  if (typeof MediaRecorder === 'undefined') return '';
  const candidates = [
    'audio/webm;codecs=opus',
    'audio/webm',
    'audio/ogg;codecs=opus',
    'audio/mp4',
  ];
  return candidates.find((t) => MediaRecorder.isTypeSupported(t)) ?? '';
}

/**
 * Microphone capture with a live level meter and silence detection.
 *
 * The level meter is not decoration: without visible feedback a learner cannot
 * tell a muted microphone from a quiet one, which is the single most common
 * reason voice input "does not work".
 */
export function useVoiceRecorder(options: RecorderOptions = {}) {
  const {
    maxDurationMs = 60_000,
    silenceTimeoutMs = 2_000,
    silenceThreshold = 0.015,
    onComplete,
    onError,
  } = options;

  const [state, setState] = useState<RecorderState>('idle');
  const [error, setError] = useState<string | null>(null);
  const [level, setLevel] = useState(0);
  const [elapsedMs, setElapsedMs] = useState(0);
  const [isSupported, setIsSupported] = useState(true);

  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const rafRef = useRef<number | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const startedAtRef = useRef(0);
  const lastSoundAtRef = useRef(0);
  const heardSpeechRef = useRef(false);
  // Read inside the animation frame loop, which must not close over stale state.
  const stopRef = useRef<() => void>(() => {});

  useEffect(() => {
    const ok =
      typeof window !== 'undefined' &&
      typeof navigator !== 'undefined' &&
      !!navigator.mediaDevices?.getUserMedia &&
      typeof MediaRecorder !== 'undefined';
    setIsSupported(ok);
  }, []);

  const cleanup = useCallback(() => {
    if (rafRef.current !== null) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    if (audioCtxRef.current && audioCtxRef.current.state !== 'closed') {
      void audioCtxRef.current.close();
    }
    audioCtxRef.current = null;
    recorderRef.current = null;
    setLevel(0);
  }, []);

  // Release the microphone if the component unmounts mid-recording.
  useEffect(() => cleanup, [cleanup]);

  const fail = useCallback(
    (message: string) => {
      cleanup();
      setState('error');
      setError(message);
      onError?.(message);
    },
    [cleanup, onError],
  );

  const stop = useCallback(() => {
    const recorder = recorderRef.current;
    if (recorder && recorder.state === 'recording') {
      recorder.stop();
    }
  }, []);

  // Keep the ref in sync outside of render, so the silence-detection loop
  // (which closes over stopRef, not stop) always calls the latest version.
  useEffect(() => {
    stopRef.current = stop;
  }, [stop]);

  const start = useCallback(async () => {
    if (!isSupported) {
      fail('This browser cannot record audio. Try Chrome, Edge or Safari.');
      return;
    }

    setError(null);
    setState('requesting');
    chunksRef.current = [];
    heardSpeechRef.current = false;

    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
    } catch (err) {
      const name = (err as DOMException)?.name;
      if (name === 'NotAllowedError' || name === 'SecurityError') {
        fail('Microphone access was blocked. Allow it in your browser settings and try again.');
      } else if (name === 'NotFoundError') {
        fail('No microphone was found. Plug one in and try again.');
      } else {
        fail('Could not start the microphone. Check that no other app is using it.');
      }
      return;
    }

    streamRef.current = stream;
    const mimeType = pickMimeType();

    let recorder: MediaRecorder;
    try {
      recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
    } catch {
      fail('This browser cannot record in a supported audio format.');
      return;
    }
    recorderRef.current = recorder;

    recorder.ondataavailable = (event) => {
      if (event.data.size > 0) chunksRef.current.push(event.data);
    };

    recorder.onstop = () => {
      const type = recorder.mimeType || mimeType || 'audio/webm';
      const blob = new Blob(chunksRef.current, { type });
      cleanup();
      // An empty blob means the mic produced nothing - a muted device.
      if (blob.size < 1024) {
        setState('idle');
        const message = 'No audio was captured. Check that your microphone is not muted.';
        setError(message);
        onError?.(message);
        return;
      }
      setState('processing');
      void Promise.resolve(onComplete?.(blob, type)).finally(() => {
        setState((current) => (current === 'processing' ? 'idle' : current));
      });
    };

    // Meter the input and drive both the visual level and silence auto-stop.
    try {
      const AudioCtx =
        window.AudioContext ??
        (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      const ctx = new AudioCtx();
      audioCtxRef.current = ctx;
      const source = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 512;
      source.connect(analyser);
      const buffer = new Float32Array(analyser.fftSize);

      const tick = () => {
        analyser.getFloatTimeDomainData(buffer);
        let sum = 0;
        for (let i = 0; i < buffer.length; i += 1) sum += buffer[i] * buffer[i];
        const rms = Math.sqrt(sum / buffer.length);
        // Scale up: speech RMS is typically 0.02-0.2, which would barely move a bar.
        setLevel(Math.min(1, rms * 8));

        const now = performance.now();
        setElapsedMs(now - startedAtRef.current);

        if (rms > silenceThreshold) {
          heardSpeechRef.current = true;
          lastSoundAtRef.current = now;
        }

        const silentFor = now - lastSoundAtRef.current;
        const tooLong = now - startedAtRef.current > maxDurationMs;
        // Only auto-stop after real speech, so a slow starter is not cut off.
        if (tooLong || (heardSpeechRef.current && silentFor > silenceTimeoutMs)) {
          stopRef.current();
          return;
        }
        rafRef.current = requestAnimationFrame(tick);
      };

      startedAtRef.current = performance.now();
      lastSoundAtRef.current = startedAtRef.current;
      rafRef.current = requestAnimationFrame(tick);
    } catch {
      // Metering is a nicety; recording still works without it.
      startedAtRef.current = performance.now();
    }

    recorder.start();
    setState('recording');
  }, [cleanup, fail, isSupported, maxDurationMs, onComplete, onError, silenceThreshold, silenceTimeoutMs]);

  const cancel = useCallback(() => {
    const recorder = recorderRef.current;
    if (recorder) {
      // Drop the handler so onstop does not upload the discarded audio.
      recorder.onstop = null;
      if (recorder.state === 'recording') recorder.stop();
    }
    cleanup();
    setState('idle');
    setError(null);
  }, [cleanup]);

  const reset = useCallback(() => {
    setError(null);
    setState('idle');
  }, []);

  return {
    state,
    error,
    level,
    elapsedMs,
    isSupported,
    isRecording: state === 'recording',
    isBusy: state === 'requesting' || state === 'processing',
    start,
    stop,
    cancel,
    reset,
  };
}
