'use client';

import { useEffect, useState } from 'react';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useAuth } from '@/app/context/AuthContext';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { CheckCircle2, XCircle, ChevronLeft, ChevronRight, Award, TrendingUp, TrendingDown, ClipboardList } from 'lucide-react';

interface Question {
  id: number;
  subject_id: number;
  question_text: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
}

interface DetailedResult {
  question_id: number;
  question_text: string;
  user_answer: string;
  correct_answer: string;
  is_correct: boolean;
  skill_tag: string;
}

interface AssessmentResult {
  score: number;
  total_questions: number;
  percentage: number;
  category_breakdown: Record<string, number>;
  strengths: string[];
  weaknesses: string[];
  detailed_results: DetailedResult[];
  remarks: string;
  actionable_feedback: string[];
}

export default function AssessmentPage() {
  const params = useParams();
  const subjectId = params.subjectId;
  
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<AssessmentResult | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  
  const { token } = useAuth();

  useEffect(() => {
    const fetchQuestions = async () => {
      try {
        const res = await fetch(`/api/assessments/${subjectId}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        if (!res.ok) {
          throw new Error('Failed to fetch questions');
        }
        const data = await res.json();
        setQuestions(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred while fetching questions');
      } finally {
        setLoading(false);
      }
    };

    if (token) {
      fetchQuestions();
    }
  }, [token, subjectId]);

  const handleSelectOption = (questionId: number, option: string) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: option
    }));
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    setError('');
    
    try {
      const res = await fetch(`/api/assessments/${subjectId}/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ answers })
      });
      
      if (!res.ok) {
        throw new Error('Failed to submit assessment');
      }
      
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred during submission');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen bg-slate-50 flex justify-center items-center text-slate-500 font-medium">
          Loading assessment...
        </div>
      </ProtectedRoute>
    );
  }

  if (error && !result) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen bg-slate-50 flex flex-col justify-center items-center text-slate-800 p-4">
          <div className="bg-red-50 border border-red-200 p-8 rounded-3xl text-center max-w-md shadow-sm">
            <div className="flex justify-center mb-4">
              <XCircle className="text-red-500" size={48} />
            </div>
            <h2 className="text-2xl font-bold text-red-600 mb-2">Oops! Something went wrong</h2>
            <p className="text-slate-600 mb-8">{error}</p>
            <Link href="/dashboard" className="px-6 py-3 bg-red-600 text-white rounded-2xl hover:bg-red-700 transition-colors font-semibold shadow-md">
              Return to Dashboard
            </Link>
          </div>
        </div>
      </ProtectedRoute>
    );
  }
  
  if (questions.length === 0) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen bg-slate-50 flex flex-col justify-center items-center p-4">
          <div className="bg-white/60 backdrop-blur-xl border border-white/50 p-8 rounded-3xl text-center max-w-md shadow-lg">
            <h2 className="text-2xl font-bold mb-4 text-slate-800">No questions available</h2>
            <p className="text-slate-500 mb-8">This assessment hasn&apos;t been set up yet.</p>
            <Link href="/dashboard" className="px-6 py-3 bg-gradient-to-r from-sky-500 to-purple-500 text-white font-bold rounded-2xl hover:opacity-90 transition-opacity shadow-md">
              Return to Dashboard
            </Link>
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  if (result) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen bg-slate-50 flex flex-col items-center p-4 py-12 text-slate-800">
          <div className="w-full max-w-3xl rounded-3xl bg-white/70 p-8 shadow-[0_8px_32px_0_rgba(31,38,135,0.07)] backdrop-blur-xl border border-white/50 mb-8">
            <div className="flex flex-col items-center text-center">
              <div className="bg-gradient-to-tr from-sky-100 to-purple-100 p-4 rounded-full mb-4 shadow-sm text-purple-600">
                <Award size={48} />
              </div>
              <h2 className="text-4xl font-extrabold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-sky-500 to-purple-500">Assessment Complete!</h2>
              <p className="text-xl text-slate-700 font-bold mb-2">
                You scored {result.score} out of {result.total_questions} questions correct.
              </p>
              <div className="mt-4 mb-8 bg-sky-50 border-l-4 border-sky-400 p-4 rounded-r-2xl max-w-xl shadow-sm text-left">
                <p className="text-sky-800 font-semibold italic text-lg">&quot;{result.remarks}&quot;</p>
              </div>
            </div>

            <div className="my-8 flex justify-center">
              <div className="relative w-40 h-40 flex items-center justify-center">
                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="45" fill="none" stroke="#f1f5f9" strokeWidth="10" />
                  <circle 
                    cx="50" cy="50" r="45" fill="none" 
                    stroke="url(#gradient)" 
                    strokeWidth="10" 
                    strokeDasharray={`${(result.percentage / 100) * 283} 283`} 
                    strokeLinecap="round" 
                    className="transition-all duration-1000 ease-out"
                  />
                  <defs>
                    <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#0ea5e9" />
                      <stop offset="100%" stopColor="#a855f7" />
                    </linearGradient>
                  </defs>
                </svg>
                <div className="absolute flex flex-col items-center justify-center">
                  <span className="text-4xl font-extrabold text-slate-700">{Math.round(result.percentage)}%</span>
                </div>
              </div>
            </div>
            
            <div className="mb-8 p-6 bg-white rounded-3xl shadow-sm border border-slate-100">
              <h3 className="text-xl font-bold mb-6 text-slate-700 flex items-center gap-2">
                <TrendingUp className="text-sky-500" /> Skill Breakdown
              </h3>
              <div className="space-y-5">
                {Object.entries(result.category_breakdown).map(([category, percentage]) => (
                  <div key={category}>
                    <div className="flex justify-between text-sm mb-2 font-semibold">
                      <span className="text-slate-600">{category}</span>
                      <span className="text-sky-600">{Math.round(percentage)}%</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-3 shadow-inner">
                      <div 
                        className="bg-gradient-to-r from-sky-400 to-purple-400 h-3 rounded-full transition-all duration-1000 ease-out" 
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8 text-left">
              <div className="bg-emerald-50 border border-emerald-100 rounded-3xl p-6 shadow-sm">
                <h4 className="text-emerald-600 font-bold mb-4 flex items-center gap-2 text-lg">
                  <TrendingUp /> Strengths
                </h4>
                {result.strengths.length > 0 ? (
                  <ul className="space-y-3">
                    {result.strengths.map(s => (
                      <li key={s} className="text-emerald-700 font-medium text-sm flex items-start gap-2">
                        <CheckCircle2 size={18} className="shrink-0 text-emerald-500 mt-0.5" />
                        {s}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-emerald-600/70 text-sm font-medium">Keep practicing to build your strengths!</p>
                )}
              </div>

              <div className="bg-rose-50 border border-rose-100 rounded-3xl p-6 shadow-sm">
                <h4 className="text-rose-600 font-bold mb-4 flex items-center gap-2 text-lg">
                  <TrendingDown /> Needs Work
                </h4>
                {result.weaknesses.length > 0 ? (
                  <ul className="space-y-3">
                    {result.weaknesses.map(w => (
                      <li key={w} className="text-rose-700 font-medium text-sm flex items-start gap-2">
                        <XCircle size={18} className="shrink-0 text-rose-500 mt-0.5" />
                        {w}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-rose-600/70 text-sm font-medium">Great job! No major weaknesses identified.</p>
                )}
              </div>
            </div>

            {/* Actionable Feedback Section */}
            {result.actionable_feedback && result.actionable_feedback.length > 0 && (
              <div className="mb-8 p-6 bg-gradient-to-br from-indigo-50 to-purple-50 rounded-3xl shadow-sm border border-indigo-100">
                <h3 className="text-xl font-bold mb-4 text-indigo-700 flex items-center gap-2">
                  <span className="bg-indigo-100 p-2 rounded-xl">💡</span> Areas to Improve
                </h3>
                <ul className="space-y-4">
                  {result.actionable_feedback.map((feedback, idx) => (
                    <li key={idx} className="flex items-start gap-3 bg-white/60 p-4 rounded-2xl border border-white">
                      <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold shrink-0 mt-0.5">
                        {idx + 1}
                      </div>
                      <p className="text-slate-700 font-medium leading-relaxed">{feedback}</p>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <button 
              onClick={() => setShowDetails(!showDetails)}
              className="w-full mb-4 px-6 py-4 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-2xl font-bold flex items-center justify-center gap-2 transition-colors border border-slate-200"
            >
              <ClipboardList />
              {showDetails ? 'Hide Detailed Answers' : 'Review Your Answers'}
            </button>

            <Link href="/dashboard" className="block text-center w-full rounded-2xl bg-gradient-to-r from-sky-500 to-purple-500 p-4 font-bold text-white transition-all hover:opacity-90 hover:shadow-lg">
              Return to Dashboard
            </Link>
          </div>

          {/* Detailed Results Section */}
          {showDetails && (
            <div className="w-full max-w-3xl rounded-3xl bg-white/70 p-8 shadow-[0_8px_32px_0_rgba(31,38,135,0.07)] backdrop-blur-xl border border-white/50 mb-8 space-y-6">
              <h3 className="text-2xl font-bold text-slate-800 mb-6">Detailed Review</h3>
              {result.detailed_results.map((detail, index) => (
                <div key={detail.question_id} className={`p-6 rounded-2xl border-2 ${detail.is_correct ? 'bg-emerald-50/50 border-emerald-100' : 'bg-rose-50/50 border-rose-100'}`}>
                  <div className="flex items-start gap-4">
                    <div className="mt-1">
                      {detail.is_correct ? (
                        <CheckCircle2 className="text-emerald-500" size={24} />
                      ) : (
                        <XCircle className="text-rose-500" size={24} />
                      )}
                    </div>
                    <div className="flex-1">
                      <p className="font-semibold text-slate-800 mb-2">
                        {index + 1}. {detail.question_text}
                      </p>
                      <div className="inline-block px-3 py-1 bg-slate-200 text-slate-600 rounded-full text-xs font-bold mb-4">
                        {detail.skill_tag}
                      </div>
                      <div className="space-y-2 text-sm font-medium">
                        <div className="flex items-center gap-2">
                          <span className="text-slate-500 w-24">Your Answer:</span>
                          <span className={`px-3 py-1 rounded-lg ${detail.is_correct ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}`}>
                            {detail.user_answer}
                          </span>
                        </div>
                        {!detail.is_correct && (
                          <div className="flex items-center gap-2">
                            <span className="text-slate-500 w-24">Correct:</span>
                            <span className="px-3 py-1 rounded-lg bg-emerald-100 text-emerald-700">
                              {detail.correct_answer}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </ProtectedRoute>
    );
  }

  const currentQuestion = questions[currentIdx];
  const selectedOption = answers[currentQuestion.id];

  const optionLabels = [
    { key: 'A', text: currentQuestion.option_a },
    { key: 'B', text: currentQuestion.option_b },
    { key: 'C', text: currentQuestion.option_c },
    { key: 'D', text: currentQuestion.option_d },
  ];

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-slate-50 text-slate-800 p-4 md:p-8">
        <div className="max-w-3xl mx-auto mt-8">
          {/* Header */}
          <div className="flex justify-between items-center mb-8 bg-white/60 p-4 rounded-3xl shadow-[0_8px_32px_0_rgba(31,38,135,0.07)] backdrop-blur-xl border border-white/50">
            <div className="px-4 py-2 bg-slate-100 rounded-xl">
              <span className="text-sm font-bold text-slate-500 uppercase tracking-wider">Question</span>
              <div className="text-lg font-extrabold text-slate-800 flex items-baseline gap-1">
                {currentIdx + 1} <span className="text-sm text-slate-400">/ {questions.length}</span>
              </div>
            </div>
            
            {/* Progress bar inside header */}
            <div className="flex-1 max-w-xs mx-6">
              <div className="w-full bg-slate-200 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-sky-400 to-purple-400 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${((currentIdx + 1) / questions.length) * 100}%` }}
                ></div>
              </div>
            </div>

            <Link href="/dashboard" className="px-4 py-2 text-sm font-bold text-slate-500 hover:text-slate-800 transition-colors bg-white hover:bg-slate-100 rounded-xl border border-slate-200 shadow-sm">
              Exit
            </Link>
          </div>
          
          <div className="bg-white/70 p-8 md:p-12 rounded-[2.5rem] shadow-[0_8px_32px_0_rgba(31,38,135,0.07)] backdrop-blur-xl border border-white/50 mb-8">
            {/* Question */}
            <div className="mb-12">
              <h2 className="text-2xl md:text-3xl font-bold leading-relaxed text-slate-800">{currentQuestion.question_text}</h2>
            </div>
            
            {/* Options */}
            <div className="space-y-4">
              {optionLabels.map((opt) => (
                <button
                  key={opt.key}
                  onClick={() => handleSelectOption(currentQuestion.id, opt.key)}
                  className={`w-full text-left p-6 rounded-2xl border-2 transition-all duration-200 group ${
                    selectedOption === opt.key
                      ? 'border-purple-500 bg-purple-50 shadow-[0_8px_20px_rgba(168,85,247,0.15)] ring-4 ring-purple-500/20 transform scale-[1.01]'
                      : 'border-slate-200 bg-white hover:border-purple-300 hover:bg-slate-50 shadow-sm'
                  }`}
                >
                  <div className="flex items-center">
                    <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center mr-5 font-bold text-lg transition-colors ${
                      selectedOption === opt.key 
                        ? 'bg-gradient-to-br from-sky-400 to-purple-500 text-white shadow-inner' 
                        : 'bg-slate-100 text-slate-500 group-hover:bg-purple-100 group-hover:text-purple-600'
                    }`}>
                      {opt.key}
                    </div>
                    <span className={`text-lg font-medium ${selectedOption === opt.key ? 'text-purple-900' : 'text-slate-700'}`}>
                      {opt.text}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </div>
          
          {/* Navigation */}
          <div className="flex justify-between items-center px-4">
            <button
              onClick={() => setCurrentIdx(prev => prev - 1)}
              disabled={currentIdx === 0}
              className="flex items-center gap-2 px-6 py-4 rounded-2xl font-bold text-slate-600 bg-white hover:bg-slate-100 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm border border-slate-200"
            >
              <ChevronLeft size={20} /> Previous
            </button>
            
            {currentIdx < questions.length - 1 ? (
              <button
                onClick={() => setCurrentIdx(prev => prev + 1)}
                className="flex items-center gap-2 px-8 py-4 rounded-2xl font-bold text-white bg-slate-800 hover:bg-slate-700 shadow-xl shadow-slate-300 transition-all transform hover:-translate-y-1"
              >
                Next <ChevronRight size={20} />
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={submitting || Object.keys(answers).length < questions.length}
                className="px-8 py-4 rounded-2xl font-bold text-white bg-gradient-to-r from-sky-500 to-purple-500 hover:opacity-90 shadow-xl shadow-purple-200 disabled:opacity-50 disabled:transform-none disabled:cursor-not-allowed transition-all transform hover:-translate-y-1"
              >
                {submitting ? 'Submitting...' : 'Complete Assessment'}
              </button>
            )}
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}
