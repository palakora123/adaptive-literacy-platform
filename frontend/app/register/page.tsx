'use client';

import { useState } from 'react';
import Link from 'next/link';
import { UserPlus, Mail, Lock, User } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function RegisterPage() {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
  });
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [message, setMessage] = useState('');
  const router = useRouter();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus("loading");
    setMessage("");

    try {
      const response = await fetch("/api/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Registration failed");
      }

      setStatus("success");
      setMessage("Account created successfully! Redirecting...");
      setTimeout(() => {
        router.push('/login');
      }, 2000);
    } catch (error) {
      setStatus("error");
      setMessage(error instanceof Error ? error.message : "An unexpected error occurred.");
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <div className="w-full max-w-md rounded-3xl bg-white/60 p-8 shadow-[0_8px_32px_0_rgba(31,38,135,0.07)] backdrop-blur-xl border border-white/50 text-slate-800">
        <div className="flex justify-center mb-6">
          <div className="bg-purple-100 p-4 rounded-full text-purple-500 shadow-sm">
            <UserPlus size={32} />
          </div>
        </div>
        <h2 className="mb-2 text-3xl font-extrabold text-center bg-clip-text text-transparent bg-gradient-to-r from-purple-500 to-pink-500">Create Account</h2>
        <p className="mb-8 text-center text-slate-500 font-medium">Join Literacy Assistant today</p>
        
        {status === "success" && (
          <div className="mb-6 rounded-2xl bg-emerald-50 p-4 text-sm text-emerald-600 border border-emerald-100 flex items-center shadow-sm">
            {message}
          </div>
        )}

        {status === "error" && (
          <div className="mb-6 rounded-2xl bg-red-50 p-4 text-sm text-red-600 border border-red-100 flex items-center shadow-sm">
            {message}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="mb-2 block text-sm font-semibold text-slate-600">Username</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <User size={18} />
              </div>
              <input
                type="text"
                name="username"
                value={formData.username}
                onChange={handleChange}
                className="w-full rounded-2xl bg-white/80 py-3 pl-10 pr-4 text-slate-800 placeholder-slate-400 border border-slate-200 focus:border-purple-400 focus:outline-none focus:ring-4 focus:ring-purple-400/20 transition-all shadow-sm"
                placeholder="johndoe"
                required
              />
            </div>
          </div>
          <div>
            <label className="mb-2 block text-sm font-semibold text-slate-600">Email Address</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <Mail size={18} />
              </div>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className="w-full rounded-2xl bg-white/80 py-3 pl-10 pr-4 text-slate-800 placeholder-slate-400 border border-slate-200 focus:border-purple-400 focus:outline-none focus:ring-4 focus:ring-purple-400/20 transition-all shadow-sm"
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
                name="password"
                value={formData.password}
                onChange={handleChange}
                className="w-full rounded-2xl bg-white/80 py-3 pl-10 pr-4 text-slate-800 placeholder-slate-400 border border-slate-200 focus:border-purple-400 focus:outline-none focus:ring-4 focus:ring-purple-400/20 transition-all shadow-sm"
                placeholder="••••••••"
                required
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={status === "loading"}
            className="w-full rounded-2xl bg-gradient-to-r from-purple-500 to-pink-500 p-3.5 font-bold text-white transition-all hover:opacity-90 hover:shadow-lg disabled:opacity-50 disabled:shadow-none mt-4"
          >
            {status === "loading" ? 'Creating Account...' : 'Create Account'}
          </button>
        </form>
        
        <p className="mt-8 text-center text-sm font-medium text-slate-500">
          Already have an account?{' '}
          <Link href="/login" className="text-purple-600 hover:text-purple-700 transition-colors">
            Log in
          </Link>
        </p>
      </div>
    </div>
  );
}
