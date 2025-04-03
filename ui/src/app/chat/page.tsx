'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useUserStore, UserState } from '@/store/userStore';
import Sidebar from '@/components/Sidebar';
import ChatHeader from '@/components/ChatHeader';
import MessageArea from '@/components/MessageArea';
import MessageInput from '@/components/MessageInput';
import { useChatStore, ChatState, Chat } from '@/store/chatStore';
import { MessageSquarePlus } from 'lucide-react';

export default function ChatPage() {
  const ownerName = useUserStore((state: UserState) => state.ownerName);
  const currentChatId = useChatStore((state: ChatState) => state.currentChatId);
  const chats = useChatStore((state: ChatState) => state.chats);
  const startNewChat = useChatStore((state: ChatState) => state.startNewChat);
  const router = useRouter();

  // Redirect to login if ownerName is not set
  useEffect(() => {
    if (typeof window !== 'undefined' && !ownerName) {
      router.push('/login');
    }
  }, [ownerName, router]);

  // Start in new chat state on initial load if no chat is selected
  useEffect(() => {
    if (ownerName && currentChatId === undefined) { // Check for undefined initial state
      startNewChat();
    }
  }, [ownerName, currentChatId, startNewChat]);

  // Find the current chat details if an ID is selected
  const currentChat: Chat | undefined = currentChatId ? chats.find(chat => chat.id === currentChatId) : undefined;

  if (!ownerName) {
    return null; // Render loading or null state until ownerName is confirmed
  }

  return (
    <div className="flex h-screen overflow-hidden bg-gray-100">
      <Sidebar />
      <main className="flex-1 flex flex-col h-screen overflow-hidden bg-gradient-to-br from-blue-50 via-white to-indigo-50">
        {currentChatId && currentChat ? (
          // Existing Chat View
          <>
            {/* Header wrapper */}
            <div className="flex-shrink-0">
              <ChatHeader chat={currentChat} />
            </div>
            {/* MessageArea takes up remaining space and handles internal scroll */}
            <div className="flex-1 overflow-y-auto">
              <MessageArea chatId={currentChatId} />
            </div>
            {/* Input wrapper */}
            <div className="flex-shrink-0">
              <MessageInput chatId={currentChatId} />
            </div>
          </>
        ) : (
          // New Chat View - Adjust layout for vertical centering
          <div className="flex flex-col flex-grow items-center justify-center p-10 space-y-8">
            {/* Prompt Area */}
            <div className="flex flex-col items-center text-center">
              <MessageSquarePlus className="w-16 h-16 text-gray-400 mb-4" />
              <h2 className="text-2xl font-semibold text-gray-700">Start a new chat</h2>
              <p className="text-gray-500 mt-2 max-w-lg">Ask anything or start a task with the multi-agent system.</p>
            </div>

            {/* Input Area - Removed mt-auto, adjusted width and padding */}
            <div className="w-full max-w-2xl px-4">
              <MessageInput chatId={null} isNewChatView={true} />
            </div>
          </div>
        )}
      </main>
    </div>
  );
} 