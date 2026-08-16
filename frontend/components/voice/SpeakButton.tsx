'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { Loader2, Volume2, VolumeX } from 'lucide-react';

import { useAuth } from '@/app/context/AuthContext';
import { useLanguage } from '@/app/context/LanguageContext';
import { apiSend } from '@/lib/api';

interface SpeakResponse {
  audios: string[];
  language_code: string;
  speaker: string;
  mime_type: string;
}

interface Props {
  text: string;
  /** Defaults to the learner's selected language. */
  languageCode?: string;
  label?: string;
  compact?: boolean;
}

/**
 * Read text aloud.
 *
 * For a literacy platform this is not an accessibility extra - a learner at
 * level 1-3 may not be able to read the question they are being asked. Sarvam
 * TTS is used when configured; otherwise the browser's speechSynthesis, which
 * is available almost everywhere but has thinner Indic voice coverage.
 */
export default function SpeakButton({ text, languageCode, label, compact = false }: Props) {
  const { token } = useAuth();
  const { language, serverVoice, speechCodeFor } = useLanguage();
  const target = languageCode ?? language;

  const [status, setStatus] = useState<'idle' | 'loading' | 'playing'>('idle');
  const [error, setError] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  // Object URLs must be revoked or every playback leaks a blob.
  const urlsRef = useRef<string[]>([]);

  const cleanup = useCallback(() => {
    audioRef.current?.pause();
    audioRef.current = null;
    urlsRef.current.forEach((url) => URL.revokeObjectURL(url));
    urlsRef.current = [];
  }, []);

  useEffect(() => {
    return () => {
      cleanup();
      if (typeof window !== 'undefined') window.speechSynthesis?.cancel();
    };
  }, [cleanup]);

  const speakInBrowser = useCallback(() => {
    if (typeof window === 'undefined' || !window.speechSynthesis) {
      setError('This browser cannot read text aloud.');
      setStatus('idle');
      return;
    }
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = speechCodeFor(target);
    // Slightly slower than default: this is being read by someone learning.
    utterance.rate = 0.92;
    utterance.onend = () => setStatus('idle');
    utterance.onerror = () => {
      setStatus('idle');
      setError('Playback failed.');
    };
    setStatus('playing');
    window.speechSynthesis.speak(utterance);
  }, [speechCodeFor, target, text]);

  const stop = useCallback(() => {
    cleanup();
    if (typeof window !== 'undefined') window.speechSynthesis?.cancel();
    setStatus('idle');
  }, [cleanup]);

  const play = useCallback(async () => {
    if (status === 'playing') {
      stop();
      return;
    }
    setError(null);

    if (!serverVoice) {
      speakInBrowser();
      return;
    }

    setStatus('loading');
    try {
      const result = await apiSend<SpeakResponse>('/voice/speak', token, {
        text,
        language_code: target,
      });

      // Sarvam splits long text into several clips; play them back to back.
      const urls = result.audios.map((base64) => {
        const binary = atob(base64);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
        return URL.createObjectURL(new Blob([bytes], { type: result.mime_type || 'audio/wav' }));
      });
      urlsRef.current = urls;

      let index = 0;
      const audio = new Audio(urls[0]);
      audioRef.current = audio;
      audio.onended = () => {
        index += 1;
        if (index < urls.length) {
          audio.src = urls[index];
          void audio.play();
        } else {
          cleanup();
          setStatus('idle');
        }
      };
      audio.onerror = () => {
        cleanup();
        setStatus('idle');
        setError('Playback failed.');
      };
      setStatus('playing');
      await audio.play();
    } catch {
      // Sarvam unavailable - the browser voice is better than no voice.
      cleanup();
      speakInBrowser();
    }
  }, [cleanup, serverVoice, speakInBrowser, status, stop, target, text, token]);

  const disabled = !text?.trim();

  return (
    <span className="inline-flex flex-col items-start gap-1">
      <button
        type="button"
        onClick={() => void play()}
        disabled={disabled || status === 'loading'}
        aria-label={status === 'playing' ? 'Stop reading aloud' : label ?? 'Read aloud'}
        title={status === 'playing' ? 'Stop' : 'Read aloud'}
        className={`inline-flex items-center gap-1.5 rounded-xl border font-bold transition-colors disabled:cursor-not-allowed disabled:opacity-40 ${
          status === 'playing'
            ? 'border-purple-200 bg-purple-50 text-purple-600'
            : 'border-slate-200 bg-white text-slate-600 hover:border-sky-300 hover:text-sky-600'
        } ${compact ? 'px-2.5 py-1.5 text-xs' : 'px-3 py-2 text-sm'}`}
      >
        {status === 'loading' ? (
          <Loader2 size={compact ? 14 : 16} className="animate-spin" />
        ) : status === 'playing' ? (
          <VolumeX size={compact ? 14 : 16} />
        ) : (
          <Volume2 size={compact ? 14 : 16} />
        )}
        {label && <span>{status === 'playing' ? 'Stop' : label}</span>}
      </button>
      {error && <span className="text-[10px] font-medium text-rose-500">{error}</span>}
    </span>
  );
}
