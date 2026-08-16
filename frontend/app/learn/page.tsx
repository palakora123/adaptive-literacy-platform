'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { BookOpen, CheckCircle2, ChevronRight, Loader2, Lock, PlayCircle } from 'lucide-react';

import AppShell from '@/components/AppShell';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useAuth } from '@/app/context/AuthContext';
import { ApiError, apiGet } from '@/lib/api';
import type { Curriculum, ModuleSummary } from '@/lib/types';

const STATUS_STYLES: Record<ModuleSummary['status'], { label: string; chip: string; card: string }> = {
  passed: {
    label: 'Passed',
    chip: 'bg-emerald-100 text-emerald-700',
    card: 'border-emerald-200 bg-emerald-50/40 hover:border-emerald-300',
  },
  in_progress: {
    label: 'In progress',
    chip: 'bg-sky-100 text-sky-700',
    card: 'border-sky-200 bg-white hover:border-sky-300',
  },
  available: {
    label: 'Ready to start',
    chip: 'bg-purple-100 text-purple-700',
    card: 'border-purple-200 bg-white hover:border-purple-300',
  },
  locked: {
    label: 'Locked',
    chip: 'bg-slate-200 text-slate-500',
    card: 'border-slate-200 bg-slate-50/60',
  },
};

function CurriculumView() {
  const { token } = useAuth();
  const [curriculum, setCurriculum] = useState<Curriculum | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [needsPlacement, setNeedsPlacement] = useState(false);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    (async () => {
      try {
        const data = await apiGet<Curriculum>('/curriculum', token);
        if (!cancelled) setCurriculum(data);
      } catch (err) {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 404) setNeedsPlacement(true);
        else setError(err instanceof ApiError ? err.message : 'Could not load your curriculum.');
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
        <Loader2 className="animate-spin" /> Loading your curriculum…
      </div>
    );
  }

  if (needsPlacement) {
    return (
      <div className="rounded-3xl border-2 border-dashed border-slate-200 bg-white/50 p-12 text-center">
        <BookOpen className="mx-auto mb-4 text-purple-400" size={44} />
        <h2 className="mb-2 text-2xl font-bold text-slate-800">Your curriculum is not built yet</h2>
        <p className="mx-auto mb-8 max-w-md text-slate-500">
          The placement test decides which modules you need and in what order. It takes
          about ten minutes.
        </p>
        <Link
          href="/placement"
          className="inline-block rounded-2xl bg-gradient-to-r from-sky-500 to-purple-500 px-6 py-3 font-bold text-white shadow-md transition-opacity hover:opacity-90"
        >
          Take the placement test
        </Link>
      </div>
    );
  }

  if (error || !curriculum) {
    return (
      <div className="rounded-3xl border border-rose-200 bg-rose-50 p-8 text-center">
        <p className="font-medium text-rose-600">{error ?? 'Curriculum unavailable.'}</p>
      </div>
    );
  }

  const progressPercent = Math.round(curriculum.overall_progress * 100);

  return (
    <div className="space-y-6 pb-12">
      <section className="rounded-3xl border border-white/50 bg-white/70 p-8 shadow-[0_8px_32px_0_rgba(31,38,135,0.07)] backdrop-blur-xl">
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <span className="rounded-full bg-gradient-to-r from-sky-500 to-purple-500 px-4 py-1.5 text-sm font-bold text-white">
            Level {curriculum.level} · {curriculum.level_label}
          </span>
          <Link
            href="/report"
            className="text-sm font-bold text-sky-600 underline underline-offset-2 hover:text-sky-700"
          >
            See the report this came from
          </Link>
        </div>

        <h1 className="mb-3 text-3xl font-extrabold text-slate-800">{curriculum.title}</h1>
        <p className="mb-6 max-w-3xl leading-relaxed text-slate-600">{curriculum.rationale}</p>

        <div className="flex items-center gap-4">
          <div className="h-3 flex-1 rounded-full bg-slate-100 shadow-inner">
            <div
              className="h-3 rounded-full bg-gradient-to-r from-sky-400 to-purple-400 transition-all duration-1000"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
          <span className="text-sm font-bold text-slate-600">{progressPercent}% complete</span>
        </div>
        <p className="mt-2 text-xs font-medium text-slate-400">
          Progress counts lessons read and module tests passed equally.
        </p>
      </section>

      <ol className="space-y-4">
        {curriculum.modules.map((module) => {
          const style = STATUS_STYLES[module.status];
          const locked = module.status === 'locked';
          const lessonPercent = module.lessons_total
            ? Math.round((module.lessons_completed / module.lessons_total) * 100)
            : 0;

          const content = (
            <>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="flex min-w-0 items-start gap-4">
                  <span
                    className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl text-sm font-extrabold ${
                      module.status === 'passed'
                        ? 'bg-emerald-100 text-emerald-600'
                        : locked
                          ? 'bg-slate-200 text-slate-400'
                          : 'bg-gradient-to-br from-sky-400 to-purple-500 text-white'
                    }`}
                  >
                    {module.status === 'passed' ? (
                      <CheckCircle2 size={20} />
                    ) : locked ? (
                      <Lock size={18} />
                    ) : (
                      module.order_index + 1
                    )}
                  </span>
                  <div className="min-w-0">
                    <h2
                      className={`text-lg font-bold ${locked ? 'text-slate-400' : 'text-slate-800'}`}
                    >
                      {module.title}
                    </h2>
                    <p className={`mt-1 text-sm ${locked ? 'text-slate-400' : 'text-slate-500'}`}>
                      {module.objective}
                    </p>
                  </div>
                </div>

                <span className={`rounded-full px-3 py-1 text-xs font-bold ${style.chip}`}>
                  {style.label}
                </span>
              </div>

              <div className="mt-4 flex flex-wrap items-center gap-4 pl-0 md:pl-15">
                <span className="rounded-lg bg-slate-100 px-2.5 py-1 text-xs font-bold text-slate-500">
                  Level {module.start_level} → {module.target_level}
                </span>
                <span className="text-xs font-medium text-slate-500">
                  {module.lessons_completed}/{module.lessons_total} lessons
                </span>
                {module.best_score != null && (
                  <span className="text-xs font-medium text-slate-500">
                    Best test score {Math.round(module.best_score)}%
                  </span>
                )}
                {!locked && (
                  <span className="ml-auto flex items-center gap-1 text-sm font-bold text-sky-600">
                    {module.status === 'passed' ? 'Review' : 'Open'} <ChevronRight size={16} />
                  </span>
                )}
              </div>

              {!locked && module.lessons_total > 0 && (
                <div className="mt-3 h-1.5 w-full rounded-full bg-slate-100">
                  <div
                    className="h-1.5 rounded-full bg-sky-400 transition-all duration-700"
                    style={{ width: `${lessonPercent}%` }}
                  />
                </div>
              )}
            </>
          );

          return (
            <li key={module.id}>
              {locked ? (
                <div
                  className={`rounded-3xl border-2 p-6 ${style.card}`}
                  title="Pass the previous module's test to unlock this"
                >
                  {content}
                </div>
              ) : (
                <Link
                  href={`/learn/${module.id}`}
                  className={`block rounded-3xl border-2 p-6 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md ${style.card}`}
                >
                  {content}
                </Link>
              )}
            </li>
          );
        })}
      </ol>

      <p className="flex items-center justify-center gap-2 rounded-2xl bg-white/60 p-4 text-sm font-medium text-slate-500">
        <PlayCircle size={16} className="text-purple-400" />
        Each module ends with a test. Score 70% or more to unlock the next one and update
        your level.
      </p>
    </div>
  );
}

export default function LearnPage() {
  return (
    <ProtectedRoute>
      <AppShell>
        <CurriculumView />
      </AppShell>
    </ProtectedRoute>
  );
}
