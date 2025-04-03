'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useUserStore, UserState } from '@/store/userStore';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function LoginPage() {
  const [name, setName] = useState('');
  const setOwnerName = useUserStore((state: UserState) => state.setOwnerName);
  const ownerName = useUserStore((state: UserState) => state.ownerName);
  const router = useRouter();

  // Redirect if already logged in (has ownerName)
  useEffect(() => {
    if (ownerName) {
      router.push('/chat');
    }
  }, [ownerName, router]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (name.trim()) {
      setOwnerName(name.trim());
      // Redirect is handled by the useEffect hook
    } else {
      // Optional: Add error handling for empty name
      console.error("Name cannot be empty");
    }
  };

  // Render null or loading state while checking ownerName
  if (ownerName) {
    return null; // Or a loading spinner
  }

  return (
    <div
      className="flex items-center justify-center min-h-screen bg-cover bg-center p-4"
      style={{ backgroundImage: "url('https://images.unsplash.com/photo-1554189097-0457f06b3c89?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3wzOTAzMzl8MHwxfGFsbHx8fHx8fHx8fDE3MDg2MTQwMjZ8&ixlib=rb-4.0.3&q=80&w=1080')" }}
    >
      <Card className="w-full max-w-md bg-white/90 backdrop-blur-sm shadow-2xl">
        <CardHeader className="text-center">
          {/* Using Lucide icon as FontAwesome isn't directly integrated with shadcn */}
          {/* You can install `lucide-react` if not already added by shadcn */}
          <div className="flex justify-center mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-blue-600"><path d="M15.14 10.08c-.13.42-.06.9.21 1.26.42.56.63 1.28.63 2.03 0 1.1-.42 2.1-1.18 2.82-.8.74-1.89 1.14-3.07 1.14-.75 0-1.47-.2-2.1-.56-.35-.18-.76-.18-1.1.02-.28.15-.47.47-.51.82a1.11 1.11 0 0 0 .84 1.21c.9.33 1.9.5 2.94.5a4.91 4.91 0 0 0 3.81-1.65c1.1-1.2 1.7-2.78 1.7-4.48 0-1.13-.38-2.18-1.03-3.01-.27-.34-.58-.61-.94-.79-.34-.18-.74-.24-1.12-.21zm-3.07 4.04c.28-.28.49-.63.61-.98.14-.4.16-.83.07-1.24-.1-.41-.3-.79-.56-1.1-.42-.56-.63-1.28-.63-2.03 0-1.1.42-2.1 1.18-2.82.8-.74 1.89-1.14 3.07-1.14.75 0 1.47.2 2.1.56.35.18.76.18 1.1 0 .28-.15.47-.47.51-.82a1.11 1.11 0 0 0-.84-1.21c-.9-.33-1.9-.5-2.94-.5a4.91 4.91 0 0 0-3.81 1.65c-1.1 1.2-1.7 2.78-1.7 4.48 0 1.13.38 2.18 1.03 3.01.27.34.58.61.94.79.34.18.74.24 1.12.21z" /><path d="M8.86 13.92c.13-.42.06-.9-.21-1.26-.42-.56-.63-1.28-.63-2.03 0-1.1.42-2.1 1.18-2.82.8-.74 1.89-1.14 3.07-1.14.75 0 1.47.2 2.1.56.35.18.76-.18 1.1.02.28.15.47.47-.51.82a1.11 1.11 0 0 0 .84 1.21c.9.33 1.9.5 2.94.5a4.91 4.91 0 0 0 3.81-1.65c1.1-1.2 1.7-2.78 1.7-4.48 0-1.13-.38-2.18-1.03-3.01-.27-.34-.58-.61-.94-.79-.34-.18-.74-.24-1.12-.21z" /></svg>
          </div>
          <CardTitle className="text-3xl font-bold">Multi-Agent Chat</CardTitle>
          <CardDescription>Enter your name to begin</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <Label htmlFor="owner_name" className="sr-only">Your Name</Label>
              <Input
                id="owner_name"
                name="owner_name"
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Enter your name (e.g., Alex)"
                className="transition duration-150 ease-in-out"
              />
            </div>
            <div>
              <Button
                type="submit"
                className="w-full transition duration-150 ease-in-out shadow-md hover:shadow-lg">
                {/* Icon can be added here if needed using lucide-react */}
                Start Chatting
              </Button>
            </div>
          </form>
          <p className="mt-6 text-center text-sm text-muted-foreground">
            No account needed, just enter your name.
          </p>
        </CardContent>
      </Card>
    </div>
  );
} 