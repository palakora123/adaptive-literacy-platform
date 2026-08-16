'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  BookOpen,
  CalendarDays,
  CheckCircle2,
  ClipboardList,
  Loader2,
  Sparkles,
  Target,
  TrendingUp,
  XCircle,
} from 'lucide-react';

import AppShell from '@/components/AppShell';
import ProtectedRoute from '@/components/ProtectedRoute';
import SpeakButton from '@/components/voice/SpeakButton';
import { useAuth } from '@/app/context/AuthContext';
import { ApiError, apiGet } from '@/lib/api';
import type { LiteracyReport } from '@/lib/types';

function LevelDial({ level }: { level: number }) {
  const fraction = level / 10;
  return (
    <div className="relative flex h-44 w-44 items-center justify-center">
      <svg className="h-full w-full -rotate-90" viewBox="0 0 100 100" aria-hidden>
        <circle cx="50" cy="50" r="45" fill="none" stroke="#f1f5f9" strokeWidth="10" />
        <circle
          cx="50"
          cy="50"
          r="45"
          fill="none"
          stroke="url(#levelGradient)"
          strokeWidth="10"
          strokeDasharray={`${fraction * 283} 283`}
          strokeLinecap="round"
          className="transition-all duration-1000 ease-out"
        />
        <defs>
          <linearGradient id="levelGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#0ea5e9" />
            <stop offset="100%" stopColor="#a855f7" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Level</span>
        <span className="text-5xl font-extrabold text-slate-700">{level}</span>
        <span className="text-xs font-semibold text-slate-400">of 10</span>
      </div>
    </div>
  );
}

function ReportView() {
  const { token } = useAuth();
  const [report, setReport] = useState<LiteracyReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [showReview, setShowReview] = useState(false);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    (async () => {
      try {
        const data = await apiGet<LiteracyReport>('/placement/report', token);
        if (!cancelled) setReport(data);
      } catch (err) {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 404) setNotFound(true);
        else setError(err instanceof ApiError ? err.message : 'Could not load your report.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token]);

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-3 py-24 font-medium text-slate-500">
        <Loader2 className="animate-spin" /> Writing your report…
      </div>
    );
  }

  if (notFound) {
    return (
      <div className="rounded-3xl border-2 border-dashed border-slate-200 bg-white/50 p-12 text-center">
        <Target className="mx-auto mb-4 text-purple-400" size={44} />
        <h2 className="mb-2 text-2xl font-bold text-slate-800">No report yet</h2>
        <p className="mx-auto mb-8 max-w-md text-slate-500">
          Take the adaptive placement test and we will work out your literacy level and
          write you a personalised report.
        </p>
        <Link
          href="/placement"
          className="inline-block rounded-2xl bg-gradient-to-r from-sky-500 to-purple-500 px-6 py-3 font-bold text-white shadow-md transition-opacity hover:opacity-90"
        >
          Start the placement test
        </Link>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="rounded-3xl border border-rose-200 bg-rose-50 p-8 text-center">
        <p className="font-medium text-rose-600">{error ?? 'Report unavailable.'}</p>
      </div>
    );
  }

  const accuracy = report.questions_answered
    ? Math.round((report.questions_correct / report.questions_answered) * 100)
    : 0;

  return (
    <div className="space-y-6 pb-12">
      {/* Headline */}
      <section className="rounded-3xl border border-white/50 bg-white/70 p-8 shadow-[0_8px_32px_0_rgba(31,38,135,0.07)] backdrop-blur-xl">
        <div className="flex flex-col items-center gap-8 md:flex-row md:items-start">
          <LevelDial level={report.level} />

          <div className="flex-1 text-center md:text-left">
            <div className="mb-3 flex flex-wrap items-center justify-center gap-2 md:justify-start">
              <span className="rounded-full bg-gradient-to-r from-sky-500 to-purple-500 px-4 py-1.5 text-sm font-bold text-white">
                {report.level_label}
              </span>
              <span
                className="rounded-full bg-slate-100 px-3 py-1.5 text-xs font-bold text-slate-500"
                title={
                  report.generated_by === 'anthropic'
                    ? 'Written by Claude from your individual answers'
                    : 'Generated from your results without an AI service configured'
                }
              >
                {report.generated_by === 'anthropic' ? (
                  <span className="flex items-center gap-1">
                    <Sparkles size={12} /> AI-written analysis
                  </span>
                ) : (
                  'Rule-based analysis'
                )}
              </span>
              <SpeakButton text={report.summary} label="Read aloud" compact />
            </div>

            <h1 className="mb-4 text-3xl font-extrabold text-slate-800">Your literacy report</h1>
            <p className="mb-6 leading-relaxed text-slate-600">{report.summary}</p>

            <dl className="grid grid-cols-3 gap-3 text-center md:text-left">
              {[
                { label: 'Questions', value: report.questions_answered },
                { label: 'Correct', value: `${accuracy}%` },
                { label: 'Precision', value: `±${report.standard_error.toFixed(2)}` },
              ].map((stat) => (
                <div key={stat.label} className="rounded-2xl bg-slate-50 p-3">
                  <dt className="text-[11px] font-bold uppercase tracking-wide text-slate-400">
                    {stat.label}
                  </dt>
                  <dd className="text-xl font-extrabold text-slate-700">{stat.value}</dd>
                </div>
              ))}
            </dl>
          </div>
        </div>
      </section>

      {/* Skill levels */}
      <section className="rounded-3xl border border-white/50 bg-white/70 p-8 shadow-sm backdrop-blur-xl">
        <h2 className="mb-6 flex items-center gap-2 text-xl font-bold text-slate-700">
          <TrendingUp className="text-sky-500" /> Level by skill
        </h2>
        <div className="space-y-5">
          {report.skill_levels.map((skill) => (
            <div key={skill.skill}>
              <div className="mb-2 flex items-baseline justify-between gap-2 text-sm">
                <span className="font-semibold text-slate-600">{skill.skill}</span>
                <span className="text-xs font-medium text-slate-400">
                  {skill.correct}/{skill.questions_answered} correct
                  <span className="ml-2 font-bold text-sky-600">Level {skill.level}</span>
                </span>
              </div>
              <div className="h-3 w-full rounded-full bg-slate-100 shadow-inner">
                <div
                  className="h-3 rounded-full bg-gradient-to-r from-sky-400 to-purple-400 transition-all duration-1000"
                  style={{ width: `${(skill.level / 10) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
        {report.skill_levels.some((s) => s.questions_answered < 3) && (
          <p className="mt-5 text-xs font-medium text-slate-400">
            Skills with fewer than three questions are provisional — practice tests will
            sharpen them.
          </p>
        )}
      </section>

      {/* Strengths + focus areas */}
      <div className="grid gap-6 md:grid-cols-2">
        <section className="rounded-3xl border border-emerald-100 bg-emerald-50 p-6 shadow-sm">
          <h2 className="mb-4 flex items-center gap-2 text-lg font-bold text-emerald-600">
            <CheckCircle2 /> What you are doing well
          </h2>
          <ul className="space-y-3">
            {report.strengths.map((strength, index) => (
              <li key={index} className="flex items-start gap-2 text-sm font-medium text-emerald-800">
                <CheckCircle2 size={16} className="mt-0.5 shrink-0 text-emerald-500" />
                {strength}
              </li>
            ))}
          </ul>
        </section>

        <section className="rounded-3xl border border-indigo-100 bg-gradient-to-br from-indigo-50 to-purple-50 p-6 shadow-sm">
          <h2 className="mb-4 flex items-center gap-2 text-lg font-bold text-indigo-700">
            <Target /> Areas to improve
          </h2>
          <ul className="space-y-3">
            {report.focus_areas.map((area, index) => (
              <li key={index} className="rounded-2xl border border-white bg-white/70 p-4">
                <p className="mb-1 flex items-center gap-2 font-bold text-indigo-700">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-indigo-100 text-xs">
                    {index + 1}
                  </span>
                  {area.skill}
                </p>
                <p className="mb-2 text-sm leading-relaxed text-slate-600">{area.why_it_matters}</p>
                <p className="text-sm font-semibold text-indigo-600">→ {area.what_to_do}</p>
              </li>
            ))}
          </ul>
        </section>
      </div>

      {/* Curriculum recommendation */}
      <section className="rounded-3xl border border-white/50 bg-white/70 p-8 shadow-sm backdrop-blur-xl">
        <h2 className="mb-4 flex items-center gap-2 text-xl font-bold text-slate-700">
          <BookOpen className="text-purple-500" /> Your recommended curriculum
        </h2>
        <p className="mb-6 leading-relaxed text-slate-600">{report.curriculum_rationale}</p>
        <Link
          href="/learn"
          className="inline-block rounded-2xl bg-gradient-to-r from-sky-500 to-purple-500 px-6 py-3 font-bold text-white shadow-md transition-opacity hover:opacity-90"
        >
          Open my curriculum →
        </Link>
      </section>

      {/* Study plan */}
      <section className="rounded-3xl border border-white/50 bg-white/70 p-8 shadow-sm backdrop-blur-xl">
        <h2 className="mb-6 flex items-center gap-2 text-xl font-bold text-slate-700">
          <CalendarDays className="text-sky-500" /> Your first four weeks
        </h2>
        <ol className="grid gap-4 md:grid-cols-2">
          {report.study_plan.map((week) => (
            <li key={week.week} className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
              <p className="mb-1 text-xs font-bold uppercase tracking-wide text-sky-500">
                Week {week.week}
              </p>
              <p className="mb-3 font-bold text-slate-800">{week.focus}</p>
              <ul className="space-y-1.5">
                {week.activities.map((activity, index) => (
                  <li key={index} className="flex gap-2 text-sm text-slate-600">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-purple-400" />
                    {activity}
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ol>
      </section>

      {/* Encouragement */}
      <section className="rounded-3xl border-l-4 border-sky-400 bg-sky-50 p-6">
        <p className="text-lg font-semibold italic leading-relaxed text-sky-900">
          {report.encouragement}
        </p>
      </section>

      {/* Answer review */}
      <section>
        <button
          onClick={() => setShowReview(!showReview)}
          className="flex w-full items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-slate-100 p-4 font-bold text-slate-700 transition-colors hover:bg-slate-200"
        >
          <ClipboardList size={18} />
          {showReview ? 'Hide your answers' : `Review all ${report.review.length} answers`}
        </button>

        {showReview && (
          <div className="mt-4 space-y-4">
            {report.review.map((item, index) => (
              <article
                key={item.question_id}
                className={`rounded-2xl border-2 p-5 ${
                  item.is_correct
                    ? 'border-emerald-100 bg-emerald-50/50'
                    : 'border-rose-100 bg-rose-50/50'
                }`}
              >
                <div className="flex items-start gap-4">
                  {item.is_correct ? (
                    <CheckCircle2 className="mt-1 shrink-0 text-emerald-500" size={22} />
                  ) : (
                    <XCircle className="mt-1 shrink-0 text-rose-500" size={22} />
                  )}
                  <div className="min-w-0 flex-1">
                    <p className="mb-2 font-semibold text-slate-800">
                      {index + 1}. {item.question_text}
                    </p>
                    <span className="mb-3 inline-block rounded-full bg-slate-200 px-3 py-1 text-xs font-bold text-slate-600">
                      {item.skill_tag}
                    </span>
                    <div className="space-y-1.5 text-sm font-medium">
                      <p className="flex items-center gap-2">
                        <span className="w-24 text-slate-500">Your answer:</span>
                        <span
                          className={`rounded-lg px-3 py-1 ${
                            item.is_correct
                              ? 'bg-emerald-100 text-emerald-700'
                              : 'bg-rose-100 text-rose-700'
                          }`}
                        >
                          {item.user_answer}
                        </span>
                      </p>
                      {!item.is_correct && (
                        <p className="flex items-center gap-2">
                          <span className="w-24 text-slate-500">Correct:</span>
                          <span className="rounded-lg bg-emerald-100 px-3 py-1 text-emerald-700">
                            {item.correct_answer}
                          </span>
                        </p>
                      )}
                    </div>
                    {item.explanation && (
                      <p className="mt-3 rounded-xl bg-white/80 p-3 text-sm leading-relaxed text-slate-600">
                        {item.explanation}
                      </p>
                    )}
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

export default function ReportPage() {
  return (
    <ProtectedRoute>
      <AppShell>
        <ReportView />
      </AppShell>
    </ProtectedRoute>
  );
}
