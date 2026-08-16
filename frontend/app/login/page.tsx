'use client';

import { useState } from 'react';
import { useAuth } from '@/app/context/AuthContext';
import Link from 'next/link';
import { LogIn, Mail, Lock } from 'lucide-react';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const res = await fetch('/api/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Login failed');
      }

      const data = await res.json();
      login(data.access_token);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred during login');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <div className="w-full max-w-md rounded-3xl bg-white/60 p-8 shadow-[0_8px_32px_0_rgba(31,38,135,0.07)] backdrop-blur-xl border border-white/50 text-slate-800">
        <div className="flex justify-center mb-6">
          <div className="bg-sky-100 p-4 rounded-full text-sky-500 shadow-sm">
            <LogIn size={32} />
          </div>
        </div>
        <h2 className="mb-2 text-3xl font-extrabold text-center bg-clip-text text-transparent bg-gradient-to-r from-sky-500 to-purple-500">Welcome Back</h2>
        <p className="mb-8 text-center text-slate-500 font-medium">Sign in to your account</p>
        
        {error && (
          <div className="mb-6 rounded-2xl bg-red-50 p-4 text-sm text-red-600 border border-red-100 flex items-center shadow-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="mb-2 block text-sm font-semibold text-slate-600">Email Address</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <Mail size={18} />
              </div>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-2xl bg-white/80 py-3 pl-10 pr-4 text-slate-800 placeholder-slate-400 border border-slate-200 focus:border-sky-400 focus:outline-none focus:ring-4 focus:ring-sky-400/20 transition-all shadow-sm"
                placeholder="you@example.com"
                required
              />
            </div>
          </div>
          <div>
            <label className="mb-2 block text-sm font-semibold text-slate-600">Password</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <Lock size={18} />
              </div>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-2xl bg-white/80 py-3 pl-10 pr-4 text-slate-800 placeholder-slate-400 border border-slate-200 focus:border-sky-400 focus:outline-none focus:ring-4 focus:ring-sky-400/20 transition-all shadow-sm"
                placeholder="••••••••"
                required
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-2xl bg-gradient-to-r from-sky-500 to-purple-500 p-3.5 font-bold text-white transition-all hover:opacity-90 hover:shadow-lg disabled:opacity-50 disabled:shadow-none mt-4"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        
        <p className="mt-8 text-center text-sm font-medium text-slate-500">
          Don&apos;t have an account?{' '}
          <Link href="/register" className="text-sky-600 hover:text-sky-700 transition-colors">
            Create one
          </Link>
        </p>
      </div>
    </div>
  );
}
