'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useUserStore, UserState } from '@/store/userStore';

export default function HomePage() {
  const router = useRouter();
  const ownerName = useUserStore((state: UserState) => state.ownerName);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  useEffect(() => {
    // The Zustand state needs a moment to hydrate from localStorage on the client.
    // We check the ownerName *after* initial hydration.
    if (ownerName === undefined) {
      // Still initializing, wait...
      return;
    }

    setIsCheckingAuth(false); // Auth status determined (or hydration finished)

    if (ownerName) {
      // User is logged in (has ownerName), redirect to chat
      router.replace('/chat');
    } else {
      // User is not logged in, redirect to login
      router.replace('/login');
    }
  }, [ownerName, router]);

  // Show a loading indicator while checking auth status/hydrating store
  // Or return null for a blank screen during redirect
  if (isCheckingAuth) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-100">
        <p className="text-gray-500">Loading...</p>
        {/* Or a proper spinner component */}
      </div>
    );
  }

  // Should ideally never be seen as redirect happens in useEffect
  return null;
}
