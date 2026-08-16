'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { AlertCircle, ArrowRight, Loader2, Sparkles, Target } from 'lucide-react';

import ProtectedRoute from '@/components/ProtectedRoute';
import SpeakButton from '@/components/voice/SpeakButton';
import VoiceInput from '@/components/voice/VoiceInput';
import { useAuth } from '@/app/context/AuthContext';
import { ApiError, apiSend } from '@/lib/api';
import type { PlacementStep } from '@/lib/types';

const LETTERS = ['A', 'B', 'C', 'D'] as const;

/**
 * The adaptive placement test.
 *
 * One question at a time: the server picks each item from the running ability
 * estimate, so there is no "next" button to pre-empt and no fixed length. The
 * bar shows progress toward the maximum, not toward a known end, because the
 * test stops as soon as the estimate is precise enough.
 */
function PlacementTest() {
  const { token, refreshUser } = useAuth();
  const router = useRouter();

  const [step, setStep] = useState<PlacementStep | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [voiceOpen, setVoiceOpen] = useState(false);
  const [voiceNote, setVoiceNote] = useState<string | null>(null);

  const questionShownAt = useRef<number>(Date.now());
  const answeredViaVoice = useRef(false);

  const begin = useCallback(
    async (restart: boolean) => {
      setLoading(true);
      setError(null);
      try {
        const next = await apiSend<PlacementStep>(
          `/placement/start${restart ? '?restart=true' : ''}`,
          token,
        );
        setStep(next);
        questionShownAt.current = Date.now();
        if (next.status === 'completed') {
          await refreshUser();
          router.push('/report');
        }
      } catch (err) {
        setError(err instanceof ApiError ? err.message : 'Could not start the test.');
      } finally {
        setLoading(false);
      }
    },
    [refreshUser, router, token],
  );

  useEffect(() => {
    if (token) void begin(false);
  }, [begin, token]);

  const submitAnswer = async (choice: string) => {
    if (!step?.question || submitting) return;
    setSubmitting(true);
    setError(null);
    setSelected(choice);

    try {
      const next = await apiSend<PlacementStep>('/placement/answer', token, {
        session_id: step.session_id,
        question_id: step.question.id,
        answer: choice,
        response_ms: Date.now() - questionShownAt.current,
        via_voice: answeredViaVoice.current,
      });

      if (next.status === 'completed') {
        await refreshUser();
        router.push('/report');
        return;
      }

      setStep(next);
      setSelected(null);
      setVoiceNote(null);
      answeredViaVoice.current = false;
      questionShownAt.current = Date.now();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not submit that answer.');
      setSelected(null);
    } finally {
      setSubmitting(false);
    }
  };

  /**
   * Turn a spoken answer into a choice.
   *
   * A learner may say the letter ("B"), the option text, or something close to
   * it, so we match on the letter first and fall back to word overlap with the
   * option text. Anything ambiguous is reported rather than guessed - silently
   * picking the wrong option would corrupt their level.
   */
  const handleTranscript = (text: string) => {
    if (!step?.question) return;
    const cleaned = text.trim().toLowerCase();
    const options = [
      step.question.option_a,
      step.question.option_b,
      step.question.option_c,
      step.question.option_d,
    ];

    const spokenLetter = /^(?:option\s+)?([abcd])\b/.exec(cleaned);
    if (spokenLetter) {
      answeredViaVoice.current = true;
      void submitAnswer(spokenLetter[1].toUpperCase());
      return;
    }

    const scores = options.map((option) => {
      const optionText = option.toLowerCase();
      if (cleaned === optionText) return 100;
      if (cleaned.includes(optionText) || optionText.includes(cleaned)) return 50;
      const words = optionText.split(/\s+/).filter((w) => w.length > 2);
      if (!words.length) return 0;
      return words.filter((w) => cleaned.includes(w)).length / words.length;
    });

    const best = Math.max(...scores);
    const winners = scores.filter((s) => s === best).length;

    if (best >= 0.5 && winners === 1) {
      answeredViaVoice.current = true;
      void submitAnswer(LETTERS[scores.indexOf(best)]);
    } else {
      setVoiceNote(
        `Heard “${text}”, but that did not clearly match one option. Say the letter — A, B, C or D — or tap your answer.`,
      );
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center gap-3 font-medium text-slate-500">
        <Loader2 className="animate-spin" /> Preparing your placement test…
      </div>
    );
  }

  if (error && !step) {
    return (
      <div className="flex min-h-screen items-center justify-center p-4">
        <div className="max-w-md rounded-3xl border border-rose-200 bg-rose-50 p-8 text-center shadow-sm">
          <AlertCircle className="mx-auto mb-4 text-rose-500" size={44} />
          <h2 className="mb-2 text-2xl font-bold text-rose-600">Something went wrong</h2>
          <p className="mb-6 text-slate-600">{error}</p>
          <button
            onClick={() => void begin(false)}
            className="rounded-2xl bg-rose-600 px-6 py-3 font-semibold text-white shadow-md transition-colors hover:bg-rose-700"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  const question = step?.question;
  if (!question) return null;

  const options = [
    { key: 'A', text: question.option_a },
    { key: 'B', text: question.option_b },
    { key: 'C', text: question.option_c },
    { key: 'D', text: question.option_d },
  ];
  const answered = step.progress.answered;
  const spokenQuestion = `${question.question_text}. Option A: ${question.option_a}. Option B: ${question.option_b}. Option C: ${question.option_c}. Option D: ${question.option_d}.`;

  return (
    <div className="min-h-screen p-4 text-slate-800 md:p-8">
      <div className="mx-auto mt-4 max-w-3xl">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-4 rounded-3xl border border-white/50 bg-white/60 p-4 shadow-[0_8px_32px_0_rgba(31,38,135,0.07)] backdrop-blur-xl">
          <div className="flex items-center gap-3">
            <span className="rounded-xl bg-purple-100 p-2 text-purple-500">
              <Target size={22} />
            </span>
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Adaptive placement
              </p>
              <p className="text-lg font-extrabold text-slate-800">
                Question {answered + 1}
                <span className="ml-1 text-sm font-semibold text-slate-400">
                  of up to {step.progress.max_questions}
                </span>
              </p>
            </div>
          </div>

          <div className="flex-1 md:mx-6 md:max-w-xs">
            <div className="h-2 w-full rounded-full bg-slate-200">
              <div
                className="h-2 rounded-full bg-gradient-to-r from-sky-400 to-purple-400 transition-all duration-500"
                style={{ width: `${Math.max(4, step.progress.fraction * 100)}%` }}
              />
            </div>
            <p className="mt-1.5 text-[11px] font-medium text-slate-400">
              The test ends early once your level is clear.
            </p>
          </div>

          <Link
            href="/dashboard"
            className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-bold text-slate-500 shadow-sm transition-colors hover:text-slate-800"
          >
            Save &amp; exit
          </Link>
        </div>

        <div className="mb-6 rounded-[2.5rem] border border-white/50 bg-white/70 p-6 shadow-[0_8px_32px_0_rgba(31,38,135,0.07)] backdrop-blur-xl md:p-10">
          <div className="mb-6 flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-500">
              {question.skill_tag}
            </span>
            <span className="rounded-full bg-purple-50 px-3 py-1 text-xs font-bold text-purple-500">
              Difficulty {question.difficulty}/10
            </span>
            <span className="ml-auto">
              {/* A learner at level 1-3 may not be able to read the question. */}
              <SpeakButton text={spokenQuestion} label="Read aloud" compact />
            </span>
          </div>

          <h1 className="mb-8 text-2xl font-bold leading-relaxed text-slate-800 md:text-3xl">
            {question.question_text}
          </h1>

          <div className="space-y-3">
            {options.map((option) => (
              <button
                key={option.key}
                onClick={() => void submitAnswer(option.key)}
                disabled={submitting}
                className={`group w-full rounded-2xl border-2 p-5 text-left transition-all duration-200 disabled:cursor-wait ${
                  selected === option.key
                    ? 'scale-[1.01] border-purple-500 bg-purple-50 shadow-[0_8px_20px_rgba(168,85,247,0.15)] ring-4 ring-purple-500/20'
                    : 'border-slate-200 bg-white shadow-sm hover:border-purple-300 hover:bg-slate-50'
                }`}
              >
                <span className="flex items-center">
                  <span
                    className={`mr-5 flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-lg font-bold transition-colors ${
                      selected === option.key
                        ? 'bg-gradient-to-br from-sky-400 to-purple-500 text-white'
                        : 'bg-slate-100 text-slate-500 group-hover:bg-purple-100 group-hover:text-purple-600'
                    }`}
                  >
                    {option.key}
                  </span>
                  <span
                    className={`text-lg font-medium ${
                      selected === option.key ? 'text-purple-900' : 'text-slate-700'
                    }`}
                  >
                    {option.text}
                  </span>
                </span>
              </button>
            ))}
          </div>

          {submitting && (
            <p className="mt-6 flex items-center gap-2 text-sm font-medium text-slate-400">
              <Loader2 size={14} className="animate-spin" /> Choosing your next question…
            </p>
          )}

          {error && (
            <p className="mt-6 rounded-2xl border border-rose-100 bg-rose-50 p-3 text-sm font-medium text-rose-600">
              {error}
            </p>
          )}
        </div>

        <div className="mb-8">
          {voiceOpen ? (
            <>
              <VoiceInput
                onTranscript={handleTranscript}
                hint="Say the letter — A, B, C or D — in any supported language"
                translateToEnglish={false}
                disabled={submitting}
              />
              {voiceNote && (
                <p className="mt-3 rounded-2xl border border-amber-100 bg-amber-50 p-3 text-sm font-medium text-amber-700">
                  {voiceNote}
                </p>
              )}
              <button
                onClick={() => setVoiceOpen(false)}
                className="mt-3 text-xs font-bold text-slate-400 underline underline-offset-2 hover:text-slate-600"
              >
                Hide voice answering
              </button>
            </>
          ) : (
            <button
              onClick={() => setVoiceOpen(true)}
              className="flex w-full items-center justify-center gap-2 rounded-2xl border border-dashed border-slate-300 bg-white/50 p-4 text-sm font-bold text-slate-500 transition-colors hover:border-sky-300 hover:text-sky-600"
            >
              <Sparkles size={16} /> Prefer to answer by speaking? Turn on voice answering
            </button>
          )}
        </div>

        {answered === 0 && (
          <p className="pb-8 text-center text-sm font-medium text-slate-400">
            Answer honestly — the test adapts to you. Getting questions wrong is how it
            finds your level.
            <button
              onClick={() => void begin(true)}
              className="ml-2 inline-flex items-center gap-1 font-bold text-sky-500 underline underline-offset-2"
            >
              Start over <ArrowRight size={12} />
            </button>
          </p>
        )}
      </div>
    </div>
  );
}

export default function PlacementPage() {
  return (
    <ProtectedRoute>
      <PlacementTest />
    </ProtectedRoute>
  );
}
