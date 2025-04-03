'use client';

import React, { useEffect, useRef, useMemo, useState } from 'react';
import { useChatStore } from '@/store/chatStore';
import MessageBubble from './MessageBubble';
import { ScrollArea } from "@/components/ui/scroll-area";
import { useUserStore, UserState } from '@/store/userStore';

interface MessageAreaProps {
  chatId: string;
}

export default function MessageArea({ chatId }: MessageAreaProps) {
  const ownerName = useUserStore((state: UserState) => state.ownerName);
  const allMessages = useChatStore((state) => state.messages);
  const setMessages = useChatStore((state) => state.setMessages);

  // Memoize the derived messages array
  const messages = useMemo(() => allMessages[chatId] || [], [allMessages, chatId]);

  // Local state for initial loading and errors
  const [isFetching, setIsFetching] = useState<boolean>(true);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  // Effect for fetching initial messages
  useEffect(() => {
    let isMounted = true; // Flag to prevent state update on unmounted component
    const fetchMessages = async () => {
      setIsFetching(true); // Start loading
      setFetchError(null);
      // Clear previous messages for this chat when fetching new ones
      setMessages(chatId, []);
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
        // TODO: Add pagination query parameters (page, page_size) if needed
        const apiUrl = `${baseUrl}/chat/${chatId}/messages`;
        console.log(`Fetching messages from: ${apiUrl}`); // Debug log
        const response = await fetch(apiUrl);

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`Failed to fetch messages: ${response.status} ${errorText}`);
        }

        const data = await response.json();

        if (!data || !Array.isArray(data.items)) {
          throw new Error('Invalid message data received from API');
        }

        if (isMounted) {
          setMessages(chatId, data.items); // Update store with fetched messages
        }

      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred';
        console.error(`Failed to fetch messages for chat ${chatId}:`, err);
        if (isMounted) {
          setFetchError(errorMessage);
        }
      } finally {
        if (isMounted) {
          setIsFetching(false);
        }
      }
    };

    if (chatId) {
      fetchMessages();
    }

    return () => { isMounted = false; }; // Cleanup function
  }, [chatId, setMessages]); // Removed store setters from dependencies

  // Scroll to bottom when messages array changes
  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollViewport = scrollAreaRef.current.querySelector('div[data-radix-scroll-area-viewport]');
      if (scrollViewport) {
        // Consider adding a small delay or checking if user scrolled up
        // to prevent disrupting user reading older messages.
        // For now, always scroll to bottom.
        requestAnimationFrame(() => {
          scrollViewport.scrollTop = scrollViewport.scrollHeight;
        });
      }
    }
  }, [messages]); // Trigger only when messages for the current chat change

  // Use local state for initial loading/error display
  if (isFetching) {
    return <div className="flex-grow p-6 text-center text-gray-500">Loading messages...</div>;
  }

  if (fetchError) {
    return <div className="flex-grow p-6 text-center text-red-500">Error loading messages: {fetchError}</div>;
  }

  return (
    <ScrollArea className="flex-grow p-6" ref={scrollAreaRef}>
      <div className="space-y-4">
        {[...messages] // Create a shallow copy before sorting to avoid mutating memoized state
          .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
          .map((message) => (
            <MessageBubble
              key={message.id}
              message={message}
              isOwnMessage={message.role === 'user'} // Assuming 'user' role is the owner
              ownerName={ownerName || 'User'} // Pass owner name for display
            />
          ))}
      </div>
    </ScrollArea>
  );
} 