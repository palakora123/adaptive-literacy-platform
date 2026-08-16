'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { AlertCircle, Check, Loader2, Mic, RotateCcw, Square } from 'lucide-react';

import { useAuth } from '@/app/context/AuthContext';
import { AUTO_DETECT, useLanguage } from '@/app/context/LanguageContext';
import { useVoiceRecorder } from '@/hooks/useVoiceRecorder';
import { ApiError, apiUpload } from '@/lib/api';
import type { TranscriptionResult } from '@/lib/types';
import LanguageSelector from './LanguageSelector';

interface Props {
  onTranscript: (text: string, meta: { language: string | null; source: 'sarvam' | 'browser' }) => void;
  /** Ask Sarvam to return English regardless of the language spoken. */
  translateToEnglish?: boolean;
  showLanguageSelector?: boolean;
  hint?: string;
  compact?: boolean;
  disabled?: boolean;
}

/* --- Web Speech API fallback -------------------------------------------- */

interface SpeechRecognitionLike extends EventTarget {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  start(): void;
  stop(): void;
  abort(): void;
  onresult: ((event: any) => void) | null; // eslint-disable-line @typescript-eslint/no-explicit-any
  onerror: ((event: any) => void) | null; // eslint-disable-line @typescript-eslint/no-explicit-any
  onend: (() => void) | null;
}

function getSpeechRecognition(): (new () => SpeechRecognitionLike) | null {
  if (typeof window === 'undefined') return null;
  const w = window as unknown as {
    SpeechRecognition?: new () => SpeechRecognitionLike;
    webkitSpeechRecognition?: new () => SpeechRecognitionLike;
  };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

/**
 * Microphone input with a live level meter, language selection and transcript
 * confirmation.
 *
 * Recognition runs server-side through Sarvam AI when it is configured, which
 * is what gives real accuracy across Indic languages. When it is not, or when
 * a call fails, the component falls back to the browser's own Web Speech API
 * rather than leaving the learner with a dead button - and says which engine
 * produced the text, because their accuracy differs enough to matter.
 */
export default function VoiceInput({
  onTranscript,
  translateToEnglish = false,
  showLanguageSelector = true,
  hint,
  compact = false,
  disabled = false,
}: Props) {
  const { token } = useAuth();
  const { language, serverVoice, speechCodeFor, labelFor } = useLanguage();

  const [transcript, setTranscript] = useState('');
  const [source, setSource] = useState<'sarvam' | 'browser' | null>(null);
  const [detected, setDetected] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
  const [browserListening, setBrowserListening] = useState(false);

  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
  const hasBrowserSpeech = getSpeechRecognition() !== null;

  useEffect(() => () => recognitionRef.current?.abort(), []);

  /* --- Browser engine --------------------------------------------------- */

  const startBrowserRecognition = useCallback(() => {
    const Recognition = getSpeechRecognition();
    if (!Recognition) {
      setFailure(
        'Voice input is unavailable: the server has no speech service configured and this browser has no built-in recogniser.',
      );
      return;
    }

    const recognition = new Recognition();
    recognitionRef.current = recognition;
    // The browser engine cannot auto-detect, so an "auto" choice becomes English.
    recognition.lang = speechCodeFor(language === AUTO_DETECT ? 'en-IN' : language);
    recognition.continuous = false;
    recognition.interimResults = true;

    let finalText = '';
    recognition.onresult = (event) => {
      let interim = '';
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const chunk = event.results[i][0].transcript;
        if (event.results[i].isFinal) finalText += chunk;
        else interim += chunk;
      }
      setTranscript((finalText + interim).trim());
    };
    recognition.onerror = (event) => {
      setBrowserListening(false);
      const code = event?.error;
      if (code === 'not-allowed' || code === 'service-not-allowed') {
        setFailure('Microphone access was blocked. Allow it in your browser settings.');
      } else if (code === 'no-speech') {
        setFailure('No speech was detected. Try again and speak a little louder.');
      } else if (code === 'language-not-supported') {
        setFailure(
          `This browser cannot recognise ${labelFor(language)}. Choose another language, or ask an administrator to enable Sarvam AI on the server.`,
        );
      } else {
        setFailure('Speech recognition failed. Please try again.');
      }
    };
    recognition.onend = () => {
      setBrowserListening(false);
      if (finalText.trim()) setSource('browser');
    };

    setFailure(null);
    setTranscript('');
    setSource(null);
    setDetected(null);
    setBrowserListening(true);
    recognition.start();
  }, [labelFor, language, speechCodeFor]);

  /* --- Sarvam engine ---------------------------------------------------- */

  const upload = useCallback(
    async (blob: Blob, mimeType: string) => {
      const extension = mimeType.includes('mp4') ? 'm4a' : mimeType.includes('ogg') ? 'ogg' : 'webm';
      const form = new FormData();
      form.append('audio', blob, `recording.${extension}`);
      form.append('language_code', language);
      form.append('translate_to_english', String(translateToEnglish));

      try {
        const result = await apiUpload<TranscriptionResult>('/voice/transcribe', token, form);
        if (!result.transcript) {
          setFailure('Nothing could be transcribed from that recording. Try speaking a little longer.');
          return;
        }
        setTranscript(result.transcript);
        setDetected(result.detected_language);
        setSource('sarvam');
        setFailure(null);
      } catch (err) {
        const apiError = err instanceof ApiError ? err : null;
        // A configuration or outage problem is exactly when the browser engine
        // earns its place; a bad request is not, and should be shown as-is.
        const shouldFallBack =
          !apiError ||
          ['not_configured', 'timeout', 'network', 'upstream_error', 'unauthorized'].includes(
            apiError.code ?? '',
          );

        if (shouldFallBack && hasBrowserSpeech) {
          setNotice(
            'The server speech service is unavailable, so this is using your browser’s recogniser instead. Accuracy may be lower for Indic languages.',
          );
          startBrowserRecognition();
        } else {
          setFailure(apiError?.message ?? 'Transcription failed. Please try again.');
        }
      }
    },
    [hasBrowserSpeech, language, startBrowserRecognition, token, translateToEnglish],
  );

  const recorder = useVoiceRecorder({
    onComplete: upload,
    onError: (message) => setFailure(message),
  });

  /* --- Controls --------------------------------------------------------- */

  const listening = recorder.isRecording || browserListening;

  const handleToggle = () => {
    if (disabled) return;

    if (listening) {
      if (browserListening) recognitionRef.current?.stop();
      else recorder.stop();
      return;
    }

    setFailure(null);
    setNotice(null);
    setTranscript('');
    setSource(null);
    setDetected(null);

    if (serverVoice && recorder.isSupported) {
      void recorder.start();
    } else {
      if (serverVoice === false) {
        setNotice(
          'Server speech recognition is not configured, so your browser’s built-in recogniser is being used.',
        );
      }
      startBrowserRecognition();
    }
  };

  const accept = () => {
    const text = transcript.trim();
    if (!text) return;
    onTranscript(text, { language: detected ?? language, source: source ?? 'browser' });
    setTranscript('');
    setSource(null);
    setDetected(null);
  };

  const retry = () => {
    setTranscript('');
    setSource(null);
    setDetected(null);
    setFailure(null);
    recorder.reset();
    handleToggle();
  };

  const busy = recorder.isBusy;
  const seconds = Math.floor(recorder.elapsedMs / 1000);

  return (
    <div
      className={`rounded-3xl border border-slate-200 bg-white/70 backdrop-blur-md shadow-sm ${
        compact ? 'p-4' : 'p-6'
      }`}
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-4">
          <button
            type="button"
            onClick={handleToggle}
            disabled={disabled || busy}
            aria-pressed={listening}
            aria-label={listening ? 'Stop recording' : 'Start recording'}
            className={`relative flex h-14 w-14 shrink-0 items-center justify-center rounded-full font-bold text-white shadow-lg transition-all disabled:cursor-not-allowed disabled:opacity-50 ${
              listening
                ? 'bg-rose-500 hover:bg-rose-600 shadow-rose-200'
                : 'bg-gradient-to-br from-sky-500 to-purple-500 hover:opacity-90 shadow-purple-200'
            }`}
          >
            {busy ? (
              <Loader2 className="animate-spin" size={22} />
            ) : listening ? (
              <Square size={20} fill="currentColor" />
            ) : (
              <Mic size={22} />
            )}
            {listening && (
              <span className="absolute inset-0 animate-ping rounded-full bg-rose-400/40" aria-hidden />
            )}
          </button>

          <div className="min-w-0">
            <p className="text-sm font-bold text-slate-700">
              {busy
                ? recorder.state === 'requesting'
                  ? 'Waiting for microphone…'
                  : 'Transcribing…'
                : listening
                  ? `Listening… ${seconds}s`
                  : 'Tap to speak'}
            </p>
            <p className="truncate text-xs font-medium text-slate-500">
              {hint ?? `Answer aloud in ${labelFor(language)}`}
            </p>
          </div>
        </div>

        {showLanguageSelector && <LanguageSelector compact={compact} label="Language" />}
      </div>

      {/* Level meter. Without it a muted mic is indistinguishable from silence. */}
      {recorder.isRecording && (
        <div
          className="mt-4 flex h-10 items-end gap-1"
          role="img"
          aria-label={`Microphone input level ${Math.round(recorder.level * 100)} percent`}
        >
          {Array.from({ length: 28 }).map((_, index) => {
            // Bars nearer the centre react more, which reads as a waveform.
            const centrality = 1 - Math.abs(index - 13.5) / 13.5;
            const height = 8 + recorder.level * 100 * (0.35 + 0.65 * centrality);
            return (
              <span
                key={index}
                className="flex-1 rounded-full bg-gradient-to-t from-sky-400 to-purple-400 transition-[height] duration-75"
                style={{ height: `${Math.min(40, height)}px` }}
              />
            );
          })}
        </div>
      )}

      {notice && (
        <p className="mt-4 rounded-2xl border border-amber-100 bg-amber-50 p-3 text-xs font-medium text-amber-700">
          {notice}
        </p>
      )}

      {failure && (
        <div className="mt-4 flex items-start gap-2 rounded-2xl border border-rose-100 bg-rose-50 p-3">
          <AlertCircle size={16} className="mt-0.5 shrink-0 text-rose-500" aria-hidden />
          <div className="min-w-0">
            <p className="text-xs font-medium text-rose-700">{failure}</p>
            <button
              type="button"
              onClick={retry}
              className="mt-2 inline-flex items-center gap-1 text-xs font-bold text-rose-600 underline underline-offset-2"
            >
              <RotateCcw size={12} /> Try again
            </button>
          </div>
        </div>
      )}

      {transcript && (
        <div className="mt-4 rounded-2xl border border-sky-100 bg-sky-50/70 p-4">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wide text-sky-600">
              What we heard
            </span>
            {source && (
              <span className="rounded-full bg-white px-2 py-0.5 text-[10px] font-bold text-slate-500">
                {source === 'sarvam' ? 'Sarvam AI' : 'Browser recogniser'}
              </span>
            )}
            {detected && detected !== language && (
              <span className="rounded-full bg-purple-100 px-2 py-0.5 text-[10px] font-bold text-purple-600">
                detected {labelFor(detected)}
              </span>
            )}
          </div>

          {/* Editable, because no recogniser is perfect and the learner should
              never be forced to re-record over one wrong word. */}
          <textarea
            value={transcript}
            onChange={(event) => setTranscript(event.target.value)}
            rows={2}
            aria-label="Transcribed text, editable"
            className="w-full resize-none rounded-xl border border-sky-200 bg-white p-3 text-sm font-medium text-slate-800 focus:border-sky-400 focus:outline-none focus:ring-4 focus:ring-sky-400/20"
          />

          <div className="mt-3 flex gap-2">
            <button
              type="button"
              onClick={accept}
              disabled={!transcript.trim()}
              className="inline-flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-sky-500 to-purple-500 px-4 py-2 text-xs font-bold text-white shadow-sm transition-opacity hover:opacity-90 disabled:opacity-50"
            >
              <Check size={14} /> Use this
            </button>
            <button
              type="button"
              onClick={retry}
              className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-bold text-slate-600 transition-colors hover:bg-slate-50"
            >
              <RotateCcw size={14} /> Record again
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
