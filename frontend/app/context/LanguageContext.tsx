'use client';

import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import { useAuth } from '@/app/context/AuthContext';
import { apiGet, apiSend } from '@/lib/api';
import type { VoiceCapabilities, VoiceLanguage } from '@/lib/types';

/**
 * Languages the UI can offer before the backend answers, and the set it falls
 * back to when Sarvam is not configured (the browser's own speech engine
 * supports the same tags).
 */
const FALLBACK_LANGUAGES: VoiceLanguage[] = [
  { code: 'en-IN', name: 'English', native_name: 'English', speech_code: 'en-IN' },
  { code: 'hi-IN', name: 'Hindi', native_name: 'हिन्दी', speech_code: 'hi-IN' },
  { code: 'bn-IN', name: 'Bengali', native_name: 'বাংলা', speech_code: 'bn-IN' },
  { code: 'gu-IN', name: 'Gujarati', native_name: 'ગુજરાતી', speech_code: 'gu-IN' },
  { code: 'kn-IN', name: 'Kannada', native_name: 'ಕನ್ನಡ', speech_code: 'kn-IN' },
  { code: 'ml-IN', name: 'Malayalam', native_name: 'മലയാളം', speech_code: 'ml-IN' },
  { code: 'mr-IN', name: 'Marathi', native_name: 'मराठी', speech_code: 'mr-IN' },
  { code: 'od-IN', name: 'Odia', native_name: 'ଓଡ଼ିଆ', speech_code: 'or-IN' },
  { code: 'pa-IN', name: 'Punjabi', native_name: 'ਪੰਜਾਬੀ', speech_code: 'pa-IN' },
  { code: 'ta-IN', name: 'Tamil', native_name: 'தமிழ்', speech_code: 'ta-IN' },
  { code: 'te-IN', name: 'Telugu', native_name: 'తెలుగు', speech_code: 'te-IN' },
];

export const AUTO_DETECT = 'unknown';

interface LanguageContextType {
  /** The learner's chosen language, or AUTO_DETECT to let Sarvam decide. */
  language: string;
  setLanguage: (code: string) => void;
  languages: VoiceLanguage[];
  capabilities: VoiceCapabilities | null;
  loading: boolean;
  /** True once we know Sarvam is reachable; drives the fallback banner. */
  serverVoice: boolean;
  /** BCP-47 tag for the Web Speech API fallback. */
  speechCodeFor: (code: string) => string;
  labelFor: (code: string) => string;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

const STORAGE_KEY = 'preferred_language';

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const { token, isAuthenticated } = useAuth();
  const [capabilities, setCapabilities] = useState<VoiceCapabilities | null>(null);
  const [language, setLanguageState] = useState<string>('en-IN');
  const [loading, setLoading] = useState(true);

  // Restore the last choice immediately so the picker does not flicker while
  // /voice/capabilities is in flight.
  useEffect(() => {
    const stored = typeof window !== 'undefined' ? localStorage.getItem(STORAGE_KEY) : null;
    if (stored) setLanguageState(stored);
  }, []);

  useEffect(() => {
    if (!isAuthenticated || !token) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const caps = await apiGet<VoiceCapabilities>('/voice/capabilities', token);
        if (cancelled) return;
        setCapabilities(caps);
        // The server's stored preference wins over localStorage only when the
        // device has no choice of its own yet.
        if (!localStorage.getItem(STORAGE_KEY)) {
          setLanguageState(caps.default_language);
        }
      } catch {
        // Capabilities are advisory. Losing them means the browser fallback is
        // used, which is exactly what should happen when the server is down.
        if (!cancelled) setCapabilities(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [isAuthenticated, token]);

  const setLanguage = useCallback(
    (code: string) => {
      setLanguageState(code);
      if (typeof window !== 'undefined') localStorage.setItem(STORAGE_KEY, code);
      // Persist to the account too, but never block the UI on it.
      if (token && code !== AUTO_DETECT) {
        void apiSend('/voice/language', token, { preferred_language: code }, 'PUT').catch(
          () => undefined,
        );
      }
    },
    [token],
  );

  const languages = capabilities?.languages ?? FALLBACK_LANGUAGES;

  const value = useMemo<LanguageContextType>(() => {
    const byCode = new Map(languages.map((l) => [l.code, l]));
    return {
      language,
      setLanguage,
      languages,
      capabilities,
      loading,
      serverVoice: capabilities?.server_stt ?? false,
      speechCodeFor: (code: string) => byCode.get(code)?.speech_code ?? 'en-IN',
      labelFor: (code: string) => {
        if (code === AUTO_DETECT) return 'Auto-detect';
        const lang = byCode.get(code);
        return lang ? lang.native_name : code;
      },
    };
  }, [capabilities, language, languages, loading, setLanguage]);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};
