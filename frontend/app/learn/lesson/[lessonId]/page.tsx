'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Clock,
  Loader2,
  Mic,
} from 'lucide-react';

import AppShell from '@/components/AppShell';
import Markdown from '@/components/Markdown';
import ProtectedRoute from '@/components/ProtectedRoute';
import SpeakButton from '@/components/voice/SpeakButton';
import VoiceInput from '@/components/voice/VoiceInput';
import { useAuth } from '@/app/context/AuthContext';
import { ApiError, apiGet, apiSend } from '@/lib/api';
import type { LessonDetail } from '@/lib/types';

/** Word-overlap score between what the learner said and the target sentence. */
function scoreReading(target: string, spoken: string): number {
  const normalise = (s: string) =>
    s
      .toLowerCase()
      .replace(/[^\p{L}\p{N}\s]/gu, '')
      .split(/\s+/)
      .filter(Boolean);

  const targetWords = normalise(target);
  const spokenWords = new Set(normalise(spoken));
  if (!targetWords.length) return 0;
  const hits = targetWords.filter((word) => spokenWords.has(word)).length;
  return Math.round((hits / targetWords.length) * 100);
}

function LessonView() {
  const params = useParams();
  const lessonId = Array.isArray(params.lessonId) ? params.lessonId[0] : params.lessonId;
  const { token } = useAuth();
  const router = useRouter();

  const [lesson, setLesson] = useState<LessonDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [marking, setMarking] = useState(false);
  const [readingScore, setReadingScore] = useState<number | null>(null);
  const [heard, setHeard] = useState<string | null>(null);

  useEffect(() => {
    if (!token || !lessonId) return;
    let cancelled = false;
    setLoading(true);
    setReadingScore(null);
    setHeard(null);
    (async () => {
      try {
        const data = await apiGet<LessonDetail>(`/lessons/${lessonId}`, token);
        if (!cancelled) setLesson(data);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'Could not load this lesson.');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [lessonId, token]);

  const markComplete = async (thenGoNext: boolean) => {
    if (!lesson) return;
    setMarking(true);
    try {
      if (!lesson.completed) {
        await apiSend(`/lessons/${lesson.id}/complete`, token);
        setLesson({ ...lesson, completed: true });
      }
      if (thenGoNext) {
        router.push(
          lesson.next_lesson_id
            ? `/learn/lesson/${lesson.next_lesson_id}`
            : `/learn/${lesson.module_id}`,
        );
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not save your progress.');
    } finally {
      setMarking(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-3 py-24 font-medium text-slate-500">
        <Loader2 className="animate-spin" /> Loading lesson…
      </div>
    );
  }

  if (error || !lesson) {
    return (
      <div className="rounded-3xl border border-rose-200 bg-rose-50 p-8 text-center">
        <p className="mb-4 font-medium text-rose-600">{error ?? 'Lesson unavailable.'}</p>
        <Link href="/learn" className="font-bold text-rose-700 underline underline-offset-2">
          Back to curriculum
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-12">
      <Link
        href={`/learn/${lesson.module_id}`}
        className="inline-flex items-center gap-2 text-sm font-bold text-slate-500 transition-colors hover:text-slate-800"
      >
        <ArrowLeft size={16} /> {lesson.module_title}
      </Link>

      <article className="rounded-3xl border border-white/50 bg-white/70 p-6 shadow-[0_8px_32px_0_rgba(31,38,135,0.07)] backdrop-blur-xl md:p-10">
        <header className="mb-6 border-b border-slate-100 pb-6">
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-500">
              {lesson.skill_tag}
            </span>
            <span className="flex items-center gap-1 rounded-full bg-sky-50 px-3 py-1 text-xs font-bold text-sky-600">
              <Clock size={12} /> {lesson.estimated_minutes} min
            </span>
            {lesson.completed && (
              <span className="flex items-center gap-1 rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-emerald-700">
                <CheckCircle2 size={12} /> Completed
              </span>
            )}
            <span className="ml-auto">
              <SpeakButton text={lesson.body_markdown} label="Read lesson aloud" compact />
            </span>
          </div>

          <h1 className="mb-2 text-3xl font-extrabold text-slate-800">{lesson.title}</h1>
          <p className="text-slate-500">{lesson.objective}</p>
        </header>

        <Markdown source={lesson.body_markdown} />
      </article>

      {/* Pronunciation practice. Reading aloud and being scored on it is the
          part of literacy a text-only platform cannot teach. */}
      {lesson.read_aloud_text && (
        <section className="rounded-3xl border border-purple-100 bg-gradient-to-br from-indigo-50 to-purple-50 p-6 shadow-sm md:p-8">
          <h2 className="mb-2 flex items-center gap-2 text-xl font-bold text-indigo-700">
            <Mic size={20} /> Read this aloud
          </h2>
          <p className="mb-5 text-sm text-slate-600">
            Listen to it first if you would like, then read it back. We will check how
            much of it we could hear.
          </p>

          <blockquote className="mb-5 rounded-2xl border border-white bg-white/80 p-5">
            <p className="text-lg font-semibold leading-relaxed text-slate-800">
              “{lesson.read_aloud_text}”
            </p>
            <div className="mt-3">
              <SpeakButton text={lesson.read_aloud_text} label="Hear it" compact />
            </div>
          </blockquote>

          <VoiceInput
            hint="Read the sentence above out loud"
            showLanguageSelector={false}
            onTranscript={(text) => {
              setHeard(text);
              setReadingScore(scoreReading(lesson.read_aloud_text!, text));
            }}
          />

          {readingScore !== null && (
            <div
              className={`mt-4 rounded-2xl border p-4 ${
                readingScore >= 80
                  ? 'border-emerald-200 bg-emerald-50'
                  : readingScore >= 50
                    ? 'border-amber-200 bg-amber-50'
                    : 'border-rose-200 bg-rose-50'
              }`}
            >
              <p
                className={`font-bold ${
                  readingScore >= 80
                    ? 'text-emerald-700'
                    : readingScore >= 50
                      ? 'text-amber-700'
                      : 'text-rose-700'
                }`}
              >
                {readingScore >= 80
                  ? `Clear reading — we matched ${readingScore}% of the words.`
                  : readingScore >= 50
                    ? `We matched ${readingScore}% of the words. Try again a little more slowly.`
                    : `We only matched ${readingScore}% of the words. Try again in a quieter place, or check your language is set correctly.`}
              </p>
              {heard && (
                <p className="mt-2 text-sm text-slate-600">
                  We heard: <span className="italic">“{heard}”</span>
                </p>
              )}
            </div>
          )}
        </section>
      )}

      <nav className="flex flex-wrap items-center justify-between gap-3">
        {lesson.prev_lesson_id ? (
          <Link
            href={`/learn/lesson/${lesson.prev_lesson_id}`}
            className="flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-6 py-4 font-bold text-slate-600 shadow-sm transition-colors hover:bg-slate-50"
          >
            <ArrowLeft size={18} /> Previous
          </Link>
        ) : (
          <span />
        )}

        <div className="flex flex-wrap items-center gap-3">
          {!lesson.completed && (
            <button
              onClick={() => void markComplete(false)}
              disabled={marking}
              className="rounded-2xl border border-slate-200 bg-white px-6 py-4 font-bold text-slate-600 shadow-sm transition-colors hover:bg-slate-50 disabled:opacity-50"
            >
              Mark as done
            </button>
          )}
          <button
            onClick={() => void markComplete(true)}
            disabled={marking}
            className="flex items-center gap-2 rounded-2xl bg-gradient-to-r from-sky-500 to-purple-500 px-8 py-4 font-bold text-white shadow-xl shadow-purple-200 transition-all hover:-translate-y-0.5 hover:opacity-90 disabled:opacity-50"
          >
            {marking ? (
              <Loader2 size={18} className="animate-spin" />
            ) : lesson.next_lesson_id ? (
              <>
                Next lesson <ArrowRight size={18} />
              </>
            ) : (
              <>
                Finish &amp; take the test <ArrowRight size={18} />
              </>
            )}
          </button>
        </div>
      </nav>
    </div>
  );
}

export default function LessonPage() {
  return (
    <ProtectedRoute>
      <AppShell>
        <LessonView />
      </AppShell>
    </ProtectedRoute>
  );
}
