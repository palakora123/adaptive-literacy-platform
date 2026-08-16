'use client';

import { Globe } from 'lucide-react';

import { AUTO_DETECT, useLanguage } from '@/app/context/LanguageContext';

interface Props {
  /** Offer "Auto-detect" - only useful where the server does the recognising. */
  allowAuto?: boolean;
  compact?: boolean;
  label?: string;
}

export default function LanguageSelector({ allowAuto = true, compact = false, label }: Props) {
  const { language, setLanguage, languages, serverVoice } = useLanguage();

  // Auto-detect is a Sarvam feature; the browser engine needs an explicit tag.
  const showAuto = allowAuto && serverVoice;

  return (
    <label
      className={`flex items-center gap-2 ${compact ? 'text-xs' : 'text-sm'} font-semibold text-slate-600`}
    >
      <Globe size={compact ? 14 : 16} className="text-sky-500 shrink-0" aria-hidden />
      {label && <span className="sr-only sm:not-sr-only">{label}</span>}
      <select
        value={language}
        onChange={(event) => setLanguage(event.target.value)}
        aria-label="Speech language"
        className={`rounded-xl border border-slate-200 bg-white font-semibold text-slate-700 shadow-sm transition-colors hover:border-sky-300 focus:border-sky-400 focus:outline-none focus:ring-4 focus:ring-sky-400/20 ${
          compact ? 'px-2 py-1 text-xs' : 'px-3 py-2 text-sm'
        }`}
      >
        {showAuto && <option value={AUTO_DETECT}>Auto-detect language</option>}
        {languages.map((lang) => (
          <option key={lang.code} value={lang.code}>
            {lang.native_name}
            {lang.native_name !== lang.name ? ` (${lang.name})` : ''}
          </option>
        ))}
      </select>
    </label>
  );
}
