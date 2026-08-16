'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import {
  ArrowLeft,
  CheckCircle2,
  Circle,
  ClipboardCheck,
  Clock,
  History,
  Loader2,
} from 'lucide-react';

import AppShell from '@/components/AppShell';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useAuth } from '@/app/context/AuthContext';
import { ApiError, apiGet } from '@/lib/api';
import type { ModuleDetail } from '@/lib/types';

function ModuleView() {
  const params = useParams();
  const moduleId = Array.isArray(params.moduleId) ? params.moduleId[0] : params.moduleId;
  const { token } = useAuth();

  const [module, setModule] = useState<ModuleDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token || !moduleId) return;
    let cancelled = false;
    (async () => {
      try {
        const data = await apiGet<ModuleDetail>(`/curriculum/modules/${moduleId}`, token);
        if (!cancelled) setModule(data);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'Could not load this module.');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [moduleId, token]);

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-3 py-24 font-medium text-slate-500">
        <Loader2 className="animate-spin" /> Loading module…
      </div>
    );
  }

  if (error || !module) {
    return (
      <div className="rounded-3xl border border-rose-200 bg-rose-50 p-8 text-center">
        <p className="mb-4 font-medium text-rose-600">{error ?? 'Module unavailable.'}</p>
        <Link href="/learn" className="font-bold text-rose-700 underline underline-offset-2">
          Back to curriculum
        </Link>
      </div>
    );
  }

  const allLessonsDone = module.lessons_completed === module.lessons_total;
  const passed = module.status === 'passed';

  return (
    <div className="space-y-6 pb-12">
      <Link
        href="/learn"
        className="inline-flex items-center gap-2 text-sm font-bold text-slate-500 transition-colors hover:text-slate-800"
      >
        <ArrowLeft size={16} /> Back to curriculum
      </Link>

      <section className="rounded-3xl border border-white/50 bg-white/70 p-8 shadow-[0_8px_32px_0_rgba(31,38,135,0.07)] backdrop-blur-xl">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-500">
            {module.skill_tag}
          </span>
          <span className="rounded-full bg-purple-50 px-3 py-1 text-xs font-bold text-purple-600">
            Level {module.start_level} → {module.target_level}
          </span>
          {passed && (
            <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-emerald-700">
              Passed
            </span>
          )}
        </div>

        <h1 className="mb-3 text-3xl font-extrabold text-slate-800">{module.title}</h1>
        <p className="max-w-3xl leading-relaxed text-slate-600">{module.objective}</p>
      </section>

      <section className="rounded-3xl border border-white/50 bg-white/70 p-8 shadow-sm backdrop-blur-xl">
        <h2 className="mb-6 text-xl font-bold text-slate-700">
          Lessons
          <span className="ml-2 text-sm font-semibold text-slate-400">
            {module.lessons_completed} of {module.lessons_total} done
          </span>
        </h2>

        <ol className="space-y-3">
          {module.lessons.map((lesson) => (
            <li key={lesson.id}>
              <Link
                href={`/learn/lesson/${lesson.id}`}
                className={`flex items-center gap-4 rounded-2xl border-2 p-5 transition-all hover:-translate-y-0.5 hover:shadow-md ${
                  lesson.completed
                    ? 'border-emerald-100 bg-emerald-50/40 hover:border-emerald-300'
                    : 'border-slate-200 bg-white hover:border-sky-300'
                }`}
              >
                {lesson.completed ? (
                  <CheckCircle2 className="shrink-0 text-emerald-500" size={24} />
                ) : (
                  <Circle className="shrink-0 text-slate-300" size={24} />
                )}
                <div className="min-w-0 flex-1">
                  <p className="font-bold text-slate-800">{lesson.title}</p>
                  <p className="mt-0.5 text-sm text-slate-500">{lesson.objective}</p>
                </div>
                <span className="flex shrink-0 items-center gap-1 text-xs font-bold text-slate-400">
                  <Clock size={13} /> {lesson.estimated_minutes} min
                </span>
              </Link>
            </li>
          ))}
        </ol>
      </section>

      <section className="rounded-3xl border border-purple-100 bg-gradient-to-br from-indigo-50 to-purple-50 p-8 shadow-sm">
        <h2 className="mb-3 flex items-center gap-2 text-xl font-bold text-indigo-700">
          <ClipboardCheck /> Module test
        </h2>
        <p className="mb-6 max-w-2xl leading-relaxed text-slate-600">
          Score 70% or more to pass this module, unlock the next one, and update your
          overall level. Each attempt draws fresh questions, so retaking it is not a
          memory exercise.
        </p>

        {!allLessonsDone && !passed && (
          <p className="mb-4 text-sm font-medium text-indigo-600">
            You can take the test now, but finishing the {module.lessons_total - module.lessons_completed}{' '}
            remaining lesson{module.lessons_total - module.lessons_completed === 1 ? '' : 's'} first
            will help.
          </p>
        )}

        <Link
          href={`/practice/${module.id}`}
          className="inline-block rounded-2xl bg-gradient-to-r from-sky-500 to-purple-500 px-6 py-3 font-bold text-white shadow-md transition-opacity hover:opacity-90"
        >
          {passed ? 'Retake the test' : 'Start the test'} →
        </Link>
      </section>

      {module.attempts.length > 0 && (
        <section className="rounded-3xl border border-white/50 bg-white/70 p-8 shadow-sm backdrop-blur-xl">
          <h2 className="mb-5 flex items-center gap-2 text-lg font-bold text-slate-700">
            <History size={18} className="text-slate-400" /> Past attempts
          </h2>
          <ul className="space-y-2">
            {module.attempts.map((attempt) => (
              <li
                key={attempt.id}
                className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-100 bg-white p-4"
              >
                <span className="text-sm font-medium text-slate-500">
                  {new Date(attempt.taken_at).toLocaleString()}
                </span>
                <span className="flex items-center gap-3">
                  {attempt.level_before != null &&
                    attempt.level_after != null &&
                    attempt.level_before !== attempt.level_after && (
                      <span className="rounded-lg bg-sky-50 px-2 py-1 text-xs font-bold text-sky-600">
                        Level {attempt.level_before} → {attempt.level_after}
                      </span>
                    )}
                  <span
                    className={`rounded-lg px-3 py-1 text-sm font-bold ${
                      attempt.passed
                        ? 'bg-emerald-100 text-emerald-700'
                        : 'bg-slate-100 text-slate-600'
                    }`}
                  >
                    {attempt.score}/{attempt.total} · {Math.round(attempt.percentage)}%
                  </span>
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

export default function ModulePage() {
  return (
    <ProtectedRoute>
      <AppShell>
        <ModuleView />
      </AppShell>
    </ProtectedRoute>
  );
}
