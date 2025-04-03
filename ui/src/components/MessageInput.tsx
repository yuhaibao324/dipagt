'use client';

import React, { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SendHorizontal, Loader2 } from 'lucide-react';
import { useChatStore } from '@/store/chatStore';
import { useUserStore, UserState } from '@/store/userStore';
import { cn } from "@/lib/utils";

interface MessageInputProps {
  chatId: string | null;
  isNewChatView?: boolean;
}

export default function MessageInput({ chatId, isNewChatView = false }: MessageInputProps) {
  const [messageText, setMessageText] = useState('');
  const ownerName = useUserStore((state: UserState) => state.ownerName);

  // Zustand store selectors
  const currentStoreChatId = useChatStore((state) => state.currentChatId);
  const sendMessageStream = useChatStore((state) => state.sendMessageStream);
  const isLoading = useChatStore((state) => state.isLoading);
  const progressMessage = useChatStore((state) => state.progressMessage);
  const error = useChatStore((state) => state.error);
  const setError = useChatStore((state) => state.setError);

  // Use the store's chatId if the prop isn't explicitly overriding it
  const effectiveChatId = isNewChatView ? null : (chatId ?? currentStoreChatId);

  // Clear error when user starts typing
  useEffect(() => {
    if (error && messageText) {
      setError(null);
    }
  }, [messageText, error, setError]);

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const trimmedMessage = messageText.trim();
    if (!trimmedMessage || !ownerName || isLoading) return;

    setMessageText(''); // Clear input immediately
    try {
      await sendMessageStream(trimmedMessage, ownerName, effectiveChatId);
      // Store updates via stream processing
    } catch (err) {
      // Basic catch just in case the stream function itself throws synchronously
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
      console.error("Error calling sendMessageStream:", err);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault(); // Prevent newline on Enter
      handleSendMessage();
    }
  };

  return (
    <footer
      className={cn(
        "p-4 flex-shrink-0",
        !isNewChatView && "bg-white border-t border-gray-200 shadow-inner"
      )}
    >
      {/* Progress/Error Display Area */}
      {(isLoading || error) && (
        <div className="text-xs text-center mb-2 px-4 truncate">
          {isLoading && !error && (
            <span className="text-gray-500 flex items-center justify-center">
              <Loader2 className="mr-2 h-3 w-3 animate-spin" />
              {progressMessage || "Processing..."}
            </span>
          )}
          {error && (
            <span className="text-red-500">Error: {error}</span>
          )}
        </div>
      )}

      {/* Input Form */}
      <form onSubmit={handleSendMessage} className="flex items-center space-x-3">
        <Input
          type="text"
          placeholder="Type your message..."
          className="flex-grow rounded-full bg-gray-50"
          value={messageText}
          onChange={(e) => setMessageText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
        />
        <Button
          type="submit"
          size="icon"
          className="bg-blue-600 text-white rounded-full w-10 h-10 flex-shrink-0 hover:bg-blue-700 disabled:opacity-50"
          disabled={!messageText.trim() || isLoading}
        >
          {isLoading ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : (
            <SendHorizontal className="h-5 w-5" />
          )}
          <span className="sr-only">Send message</span>
        </Button>
      </form>
    </footer>
  );
} 