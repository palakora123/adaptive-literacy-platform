'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { BookOpen, GraduationCap, LayoutDashboard, LogOut, ScrollText } from 'lucide-react';

import { useAuth } from '@/app/context/AuthContext';
import LanguageSelector from '@/components/voice/LanguageSelector';

const NAV = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/learn', label: 'My Curriculum', icon: BookOpen },
  { href: '/report', label: 'My Report', icon: ScrollText },
];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-slate-50 p-4 text-slate-800 md:p-8">
      <div className="mx-auto max-w-6xl">
        <header className="mb-8 flex flex-wrap items-center justify-between gap-4 rounded-3xl border border-white/50 bg-white/60 p-4 shadow-[0_8px_32px_0_rgba(31,38,135,0.07)] backdrop-blur-xl">
          <Link href="/dashboard" className="flex items-center gap-3 pl-2">
            <span className="rounded-xl bg-sky-100 p-2 text-sky-500">
              <GraduationCap size={26} />
            </span>
            <span className="bg-gradient-to-r from-sky-500 to-purple-500 bg-clip-text text-2xl font-extrabold text-transparent">
              Literacy Assistant
            </span>
          </Link>

          <nav className="order-3 flex w-full gap-1 overflow-x-auto md:order-none md:w-auto">
            {NAV.map(({ href, label, icon: Icon }) => {
              const active = pathname === href || pathname.startsWith(`${href}/`);
              return (
                <Link
                  key={href}
                  href={href}
                  aria-current={active ? 'page' : undefined}
                  className={`flex shrink-0 items-center gap-2 rounded-xl px-3 py-2 text-sm font-bold transition-colors ${
                    active
                      ? 'bg-sky-100 text-sky-700'
                      : 'text-slate-500 hover:bg-slate-100 hover:text-slate-800'
                  }`}
                >
                  <Icon size={16} />
                  {label}
                </Link>
              );
            })}
          </nav>

          <div className="flex items-center gap-3">
            {user?.level != null && (
              <span
                className="hidden rounded-xl bg-gradient-to-r from-sky-500 to-purple-500 px-3 py-2 text-xs font-bold text-white shadow-sm sm:inline-block"
                title={user.level_label ?? undefined}
              >
                Level {user.level}
              </span>
            )}
            <LanguageSelector compact allowAuto={false} />
            <button
              onClick={logout}
              className="flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-bold text-slate-600 shadow-sm transition-all hover:bg-slate-50 hover:text-rose-500"
            >
              <LogOut size={16} />
              <span className="hidden sm:inline">Sign Out</span>
            </button>
          </div>
        </header>

        {children}
      </div>
    </div>
  );
}
