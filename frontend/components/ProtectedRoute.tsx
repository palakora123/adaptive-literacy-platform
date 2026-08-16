'use client';

import { useAuth } from '@/app/context/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, loadingUser } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated && !loadingUser) {
      router.push('/login');
    }
  }, [isAuthenticated, loadingUser, router]);

  if (!isAuthenticated) {
    return null; // Will redirect in useEffect
  }

  return <>{children}</>;
}
