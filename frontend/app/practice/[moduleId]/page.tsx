'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import {
  ArrowLeft,
  ArrowRight,
  Award,
  CheckCircle2,
  Loader2,
  RotateCcw,
  TrendingUp,
  XCircle,
} from 'lucide-react';

import AppShell from '@/components/AppShell';
import ProtectedRoute from '@/components/ProtectedRoute';
import SpeakButton from '@/components/voice/SpeakButton';
import { useAuth } from '@/app/context/AuthContext';
import { ApiError, apiSend } from '@/lib/api';
import type { PracticeResult, PracticeTest } from '@/lib/types';

function PracticeView() {
  const params = useParams();
  const moduleId = Array.isArray(params.moduleId) ? params.moduleId[0] : params.moduleId;
  const { token, refreshUser } = useAuth();

  const [test, setTest] = useState<PracticeTest | null>(null);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [index, setIndex] = useState(0);
  const [result, setResult] = useState<PracticeResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!token || !moduleId) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setAnswers({});
    setIndex(0);
    try {
      const data = await apiSend<PracticeTest>(`/practice/${moduleId}/start`, token);
      setTest(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not start this test.');
    } finally {
      setLoading(false);
    }
  }, [moduleId, token]);

  useEffect(() => {
    void load();
  }, [load]);

  const submit = async () => {
    if (!test) return;
    setSubmitting(true);
    setError(null);
    try {
      const data = await apiSend<PracticeResult>('/practice/submit', token, {
        practice_session_id: test.practice_session_id,
        answers,
      });
      setResult(data);
      // The level in the header may have moved as a result of this test.
      await refreshUser();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not submit your answers.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-3 py-24 font-medium text-slate-500">
        <Loader2 className="animate-spin" /> Building your test…
      </div>
    );
  }

  if (error && !test) {
    return (
      <div className="rounded-3xl border border-rose-200 bg-rose-50 p-8 text-center">
        <p className="mb-4 font-medium text-rose-600">{error}</p>
        <Link href="/learn" className="font-bold text-rose-700 underline underline-offset-2">
          Back to curriculum
        </Link>
      </div>
    );
  }

  if (!test) return null;

  /* --- Results ---------------------------------------------------------- */

  if (result) {
    return (
      <div className="space-y-6 pb-12">
        <section className="rounded-3xl border border-white/50 bg-white/70 p-8 text-center shadow-[0_8px_32px_0_rgba(31,38,135,0.07)] backdrop-blur-xl">
          <div
            className={`mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-full ${
              result.passed ? 'bg-emerald-100 text-emerald-600' : 'bg-amber-100 text-amber-600'
            }`}
          >
            <Award size={40} />
          </div>

          <h1 className="mb-2 text-3xl font-extrabold text-slate-800">
            {result.passed ? 'Module passed' : 'Not quite yet'}
          </h1>
          <p className="mb-6 text-xl font-bold text-slate-600">
            {result.score} of {result.total} correct · {Math.round(result.percentage)}%
            <span className="ml-2 text-sm font-medium text-slate-400">
              (pass mark {result.pass_mark}%)
            </span>
          </p>

          {result.level_changed && (
            <p className="mx-auto mb-6 flex max-w-md items-center justify-center gap-2 rounded-2xl border border-sky-100 bg-sky-50 p-4 font-bold text-sky-700">
              <TrendingUp size={18} />
              Your level moved from {result.level_before} to {result.level_after}
            </p>
          )}

          <p className="mx-auto mb-8 max-w-xl leading-relaxed text-slate-600">{result.feedback}</p>

          <div className="flex flex-wrap justify-center gap-3">
            {result.passed && result.next_module_id ? (
              <Link
                href={`/learn/${result.next_module_id}`}
                className="flex items-center gap-2 rounded-2xl bg-gradient-to-r from-sky-500 to-purple-500 px-6 py-3 font-bold text-white shadow-md transition-opacity hover:opacity-90"
              >
                Start the next module <ArrowRight size={18} />
              </Link>
            ) : (
              <button
                onClick={() => void load()}
                className="flex items-center gap-2 rounded-2xl bg-gradient-to-r from-sky-500 to-purple-500 px-6 py-3 font-bold text-white shadow-md transition-opacity hover:opacity-90"
              >
                <RotateCcw size={18} /> Retake with new questions
              </button>
            )}
            <Link
              href={`/learn/${test.module_id}`}
              className="rounded-2xl border border-slate-200 bg-white px-6 py-3 font-bold text-slate-600 shadow-sm transition-colors hover:bg-slate-50"
            >
              Back to the lessons
            </Link>
          </div>
        </section>

        <section className="space-y-4">
          <h2 className="text-xl font-bold text-slate-700">Every answer explained</h2>
          {result.review.map((item, i) => (
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
                  <p className="mb-3 font-semibold text-slate-800">
                    {i + 1}. {item.question_text}
                  </p>
                  <div className="mb-3 space-y-1.5 text-sm font-medium">
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
                    <p className="rounded-xl bg-white/80 p-3 text-sm leading-relaxed text-slate-600">
                      {item.explanation}
                    </p>
                  )}
                </div>
              </div>
            </article>
          ))}
        </section>
      </div>
    );
  }

  /* --- Taking the test -------------------------------------------------- */

  const question = test.questions[index];
  const options = [
    { key: 'A', text: question.option_a },
    { key: 'B', text: question.option_b },
    { key: 'C', text: question.option_c },
    { key: 'D', text: question.option_d },
  ];
  const answeredCount = Object.keys(answers).length;
  const isLast = index === test.questions.length - 1;

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <Link
          href={`/learn/${test.module_id}`}
          className="inline-flex items-center gap-2 text-sm font-bold text-slate-500 transition-colors hover:text-slate-800"
        >
          <ArrowLeft size={16} /> Leave test
        </Link>
        <p className="text-sm font-bold text-slate-500">
          {answeredCount} of {test.questions.length} answered
        </p>
      </div>

      <section className="rounded-3xl border border-white/50 bg-white/70 p-6 shadow-[0_8px_32px_0_rgba(31,38,135,0.07)] backdrop-blur-xl md:p-10">
        <div className="mb-6">
          <div className="mb-4 flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-purple-100 px-3 py-1 text-xs font-bold text-purple-600">
              {test.skill_tag} test
            </span>
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-500">
              Question {index + 1} of {test.questions.length}
            </span>
            <span className="rounded-full bg-sky-50 px-3 py-1 text-xs font-bold text-sky-600">
              Difficulty {question.difficulty}/10
            </span>
            <span className="ml-auto">
              <SpeakButton text={question.question_text} compact />
            </span>
          </div>

          <div className="h-2 w-full rounded-full bg-slate-200">
            <div
              className="h-2 rounded-full bg-gradient-to-r from-sky-400 to-purple-400 transition-all duration-300"
              style={{ width: `${((index + 1) / test.questions.length) * 100}%` }}
            />
          </div>
        </div>

        <h1 className="mb-8 text-2xl font-bold leading-relaxed text-slate-800">
          {question.question_text}
        </h1>

        <div className="space-y-3">
          {options.map((option) => {
            const chosen = answers[question.id] === option.key;
            return (
              <button
                key={option.key}
                onClick={() => setAnswers({ ...answers, [question.id]: option.key })}
                className={`group w-full rounded-2xl border-2 p-5 text-left transition-all duration-200 ${
                  chosen
                    ? 'scale-[1.01] border-purple-500 bg-purple-50 shadow-[0_8px_20px_rgba(168,85,247,0.15)] ring-4 ring-purple-500/20'
                    : 'border-slate-200 bg-white shadow-sm hover:border-purple-300 hover:bg-slate-50'
                }`}
              >
                <span className="flex items-center">
                  <span
                    className={`mr-5 flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-lg font-bold ${
                      chosen
                        ? 'bg-gradient-to-br from-sky-400 to-purple-500 text-white'
                        : 'bg-slate-100 text-slate-500 group-hover:bg-purple-100 group-hover:text-purple-600'
                    }`}
                  >
                    {option.key}
                  </span>
                  <span
                    className={`text-lg font-medium ${chosen ? 'text-purple-900' : 'text-slate-700'}`}
                  >
                    {option.text}
                  </span>
                </span>
              </button>
            );
          })}
        </div>
      </section>

      {error && (
        <p className="rounded-2xl border border-rose-100 bg-rose-50 p-4 text-sm font-medium text-rose-600">
          {error}
        </p>
      )}

      <nav className="flex items-center justify-between gap-3">
        <button
          onClick={() => setIndex((i) => i - 1)}
          disabled={index === 0}
          className="flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-6 py-4 font-bold text-slate-600 shadow-sm transition-all hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <ArrowLeft size={18} /> Previous
        </button>

        {isLast ? (
          <button
            onClick={() => void submit()}
            disabled={submitting || answeredCount < test.questions.length}
            title={
              answeredCount < test.questions.length
                ? `Answer all ${test.questions.length} questions first`
                : undefined
            }
            className="flex items-center gap-2 rounded-2xl bg-gradient-to-r from-sky-500 to-purple-500 px-8 py-4 font-bold text-white shadow-xl shadow-purple-200 transition-all hover:-translate-y-0.5 hover:opacity-90 disabled:transform-none disabled:opacity-50"
          >
            {submitting ? <Loader2 size={18} className="animate-spin" /> : null}
            {submitting ? 'Marking…' : 'Submit test'}
          </button>
        ) : (
          <button
            onClick={() => setIndex((i) => i + 1)}
            className="flex items-center gap-2 rounded-2xl bg-slate-800 px-8 py-4 font-bold text-white shadow-xl shadow-slate-300 transition-all hover:-translate-y-0.5 hover:bg-slate-700"
          >
            Next <ArrowRight size={18} />
          </button>
        )}
      </nav>
    </div>
  );
}

export default function PracticePage() {
  return (
    <ProtectedRoute>
      <AppShell>
        <PracticeView />
      </AppShell>
    </ProtectedRoute>
  );
}
