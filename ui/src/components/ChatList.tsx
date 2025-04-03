'use client';

import React, { useEffect, useState } from 'react';
import { useChatStore } from '@/store/chatStore';
import ChatItem from './ChatItem';
import { useUserStore, UserState } from '@/store/userStore';

// Define props interface
interface ChatListProps {
  searchQuery: string;
}

export default function ChatList({ searchQuery }: ChatListProps) {
  const ownerName = useUserStore((state: UserState) => state.ownerName);
  const chats = useChatStore((state) => state.chats);
  const setChats = useChatStore((state) => state.setChats);
  const currentChatId = useChatStore((state) => state.currentChatId);
  const setCurrentChatId = useChatStore((state) => state.setCurrentChatId);

  // Local state for initial loading and errors
  const [isFetching, setIsFetching] = useState<boolean>(true);
  const [fetchError, setFetchError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true; // Flag to prevent state update on unmounted component
    const fetchChats = async () => {
      if (!ownerName) {
        setIsFetching(false); // Stop loading if no owner
        return;
      }
      setIsFetching(true); // Start loading
      setFetchError(null);
      try {
        // Construct API URL
        const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
        let apiUrl = `${baseUrl}/chat/list/${encodeURIComponent(ownerName)}`;
        if (searchQuery) {
          apiUrl += `?searchQuery=${encodeURIComponent(searchQuery)}`;
        }

        const response = await fetch(apiUrl);

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`Failed to fetch chats: ${response.status} ${errorText}`);
        }

        const data = await response.json();

        if (!data || !Array.isArray(data.items)) {
          throw new Error('Invalid chat data received from API');
        }

        if (isMounted) {
          setChats(data.items);
        }

      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred';
        console.error("Failed to fetch chats:", err);
        if (isMounted) {
          setFetchError(errorMessage);
          setChats([]); // Clear chats on error?
        }
      } finally {
        if (isMounted) {
          setIsFetching(false);
        }
      }
    };

    fetchChats();

    return () => { isMounted = false; }; // Cleanup function
  }, [ownerName, searchQuery, setChats]); // Removed store setters from dependencies

  const handleSelectChat = (chatId: string) => {
    setCurrentChatId(chatId);
  };

  // Use local state for initial loading/error display
  if (isFetching) {
    return <div className="p-4 text-center text-gray-500">Loading chats...</div>;
  }

  if (fetchError) {
    return <div className="p-4 text-center text-red-500">Error loading chats: {fetchError}</div>;
  }

  if (!chats || chats.length === 0) {
    return <div className="p-4 text-center text-gray-500">No chats found.</div>;
  }

  return (
    <div className="space-y-1 pt-2">
      {chats.map((chat) => (
        <ChatItem
          key={chat.id}
          chat={chat}
          isSelected={currentChatId === chat.id}
          onSelect={() => handleSelectChat(chat.id)}
        />
      ))}
    </div>
  );
} 