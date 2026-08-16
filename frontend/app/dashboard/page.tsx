'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  ArrowRight,
  BookOpen,
  ClipboardCheck,
  Loader2,
  Sparkles,
  Target,
  TrendingUp,
} from 'lucide-react';

import AppShell from '@/components/AppShell';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useAuth } from '@/app/context/AuthContext';
import { apiGet } from '@/lib/api';
import type { Curriculum, LiteracyReport } from '@/lib/types';

function PlacementPrompt() {
  return (
    <section className="overflow-hidden rounded-3xl border border-white/50 bg-gradient-to-br from-sky-500 to-purple-500 p-10 text-center text-white shadow-[0_8px_32px_0_rgba(31,38,135,0.15)]">
      <Sparkles className="mx-auto mb-4" size={40} />
      <h1 className="mb-3 text-3xl font-extrabold">Let&apos;s find your starting point</h1>
      <p className="mx-auto mb-8 max-w-lg text-sky-50">
        A short adaptive test (about ten minutes) places you on a 1-10 literacy scale,
        writes you a personal AI report, and builds a curriculum around what you need
        most. You can answer by typing or by speaking, in your own language.
      </p>
      <Link
        href="/placement"
        className="inline-flex items-center gap-2 rounded-2xl bg-white px-8 py-4 font-bold text-sky-600 shadow-xl transition-transform hover:-translate-y-0.5"
      >
        Start the placement test <ArrowRight size={18} />
      </Link>
    </section>
  );
}

function DashboardContent() {
  const { user, token } = useAuth();
  const [report, setReport] = useState<LiteracyReport | null>(null);
  const [curriculum, setCurriculum] = useState<Curriculum | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token || !user?.placement_completed) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const [reportData, curriculumData] = await Promise.allSettled([
          apiGet<LiteracyReport>('/placement/report', token),
          apiGet<Curriculum>('/curriculum', token),
        ]);
        if (cancelled) return;
        if (reportData.status === 'fulfilled') setReport(reportData.value);
        if (curriculumData.status === 'fulfilled') setCurriculum(curriculumData.value);
      } catch {
        // Non-fatal - the dashboard cards simply hide themselves.
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token, user?.placement_completed]);

  if (!user?.placement_completed) {
    return <PlacementPrompt />;
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-3 py-24 font-medium text-slate-500">
        <Loader2 className="animate-spin" /> Loading your dashboard…
      </div>
    );
  }

  const nextModule = curriculum?.modules.find(
    (m) => m.status === 'available' || m.status === 'in_progress',
  );
  const progressPercent = Math.round((curriculum?.overall_progress ?? 0) * 100);

  return (
    <div className="space-y-6 pb-12">
      <section className="rounded-3xl border border-white/50 bg-white/70 p-8 shadow-[0_8px_32px_0_rgba(31,38,135,0.07)] backdrop-blur-xl">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="mb-1 text-sm font-semibold text-slate-400">Welcome back</p>
            <h1 className="text-3xl font-extrabold text-slate-800">
              {user.username ?? user.email.split('@')[0]}
            </h1>
          </div>
          <div className="flex items-center gap-4 rounded-2xl bg-gradient-to-r from-sky-500 to-purple-500 px-6 py-4 text-white shadow-lg">
            <Target size={28} />
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-sky-100">
                Current level
              </p>
              <p className="text-2xl font-extrabold">
                {user.level} <span className="text-sm font-semibold">/ 10</span>
              </p>
              <p className="text-xs font-medium text-sky-100">{user.level_label}</p>
            </div>
          </div>
        </div>
      </section>

      <div className="grid gap-6 md:grid-cols-3">
        <Link
          href="/report"
          className="group flex flex-col rounded-3xl border border-white/50 bg-white/70 p-6 shadow-sm transition-all hover:-translate-y-1 hover:shadow-md"
        >
          <span className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-sky-100 text-sky-500">
            <Sparkles size={22} />
          </span>
          <h2 className="mb-1 font-bold text-slate-800">Your AI report</h2>
          <p className="mb-4 flex-1 text-sm text-slate-500">
            {report ? report.summary.slice(0, 90) + '…' : 'See your strengths and focus areas.'}
          </p>
          <span className="flex items-center gap-1 text-sm font-bold text-sky-600 transition-transform group-hover:translate-x-1">
            Read report <ArrowRight size={14} />
          </span>
        </Link>

        <Link
          href="/learn"
          className="group flex flex-col rounded-3xl border border-white/50 bg-white/70 p-6 shadow-sm transition-all hover:-translate-y-1 hover:shadow-md"
        >
          <span className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-purple-100 text-purple-500">
            <BookOpen size={22} />
          </span>
          <h2 className="mb-1 font-bold text-slate-800">Your curriculum</h2>
          <p className="mb-3 text-sm text-slate-500">
            {curriculum ? curriculum.title : 'A learning path built for you.'}
          </p>
          {curriculum && (
            <div className="mb-3 h-2 w-full rounded-full bg-slate-100">
              <div
                className="h-2 rounded-full bg-gradient-to-r from-sky-400 to-purple-400"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          )}
          <span className="mt-auto flex items-center gap-1 text-sm font-bold text-purple-600 transition-transform group-hover:translate-x-1">
            {progressPercent}% complete <ArrowRight size={14} />
          </span>
        </Link>

        {nextModule ? (
          <Link
            href={`/learn/${nextModule.id}`}
            className="group flex flex-col rounded-3xl border border-white/50 bg-white/70 p-6 shadow-sm transition-all hover:-translate-y-1 hover:shadow-md"
          >
            <span className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-100 text-emerald-500">
              <ClipboardCheck size={22} />
            </span>
            <h2 className="mb-1 font-bold text-slate-800">Continue learning</h2>
            <p className="mb-4 flex-1 text-sm text-slate-500">{nextModule.title}</p>
            <span className="flex items-center gap-1 text-sm font-bold text-emerald-600 transition-transform group-hover:translate-x-1">
              Resume <ArrowRight size={14} />
            </span>
          </Link>
        ) : (
          <Link
            href="/placement"
            className="group flex flex-col rounded-3xl border border-white/50 bg-white/70 p-6 shadow-sm transition-all hover:-translate-y-1 hover:shadow-md"
          >
            <span className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-100 text-amber-500">
              <TrendingUp size={22} />
            </span>
            <h2 className="mb-1 font-bold text-slate-800">Retake placement</h2>
            <p className="mb-4 flex-1 text-sm text-slate-500">
              Think your level has changed? Take the adaptive test again.
            </p>
            <span className="flex items-center gap-1 text-sm font-bold text-amber-600 transition-transform group-hover:translate-x-1">
              Start <ArrowRight size={14} />
            </span>
          </Link>
        )}
      </div>

      {report && report.focus_areas.length > 0 && (
        <section className="rounded-3xl border border-indigo-100 bg-gradient-to-br from-indigo-50 to-purple-50 p-6 shadow-sm">
          <h2 className="mb-4 font-bold text-indigo-700">Focus on these next</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {report.focus_areas.slice(0, 2).map((area) => (
              <div key={area.skill} className="rounded-2xl border border-white bg-white/70 p-4">
                <p className="mb-1 font-bold text-indigo-700">{area.skill}</p>
                <p className="text-sm text-slate-600">{area.what_to_do}</p>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <AppShell>
        <DashboardContent />
      </AppShell>
    </ProtectedRoute>
  );
}
