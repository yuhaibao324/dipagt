'use client';

import React, { useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import ChatList from './ChatList'; // Assuming ChatList is in the same directory
import { useUserStore, UserState } from '@/store/userStore';
import { useChatStore } from '@/store/chatStore'; // Import chat store
import { PlusCircle, Search } from 'lucide-react'; // Using lucide icons
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import debounce from 'lodash.debounce'; // Import debounce

export default function Sidebar() {
  const ownerName = useUserStore((state: UserState) => state.ownerName);
  const startNewChat = useChatStore((state) => state.startNewChat); // Get action
  const userInitial = ownerName ? ownerName.charAt(0).toUpperCase() : '?';
  const [searchQuery, setSearchQuery] = useState(''); // State for search input

  const handleNewChatClick = () => {
    startNewChat();
  };

  // Debounced search handler - we will pass this down to ChatList
  // ChatList will call this when the actual API call needs to be triggered
  const debouncedSearch = useCallback(
    debounce((query: string) => {
      // The actual fetching logic is in ChatList's useEffect
      // We just need to trigger a state update there if necessary,
      // but ChatList already re-fetches when searchQuery prop changes.
      console.log("Debounced search triggered for:", query); // For debugging
    }, 500), // 500ms debounce delay
    [] // Empty dependency array for useCallback
  );

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const query = event.target.value;
    setSearchQuery(query); // Update input field immediately
    debouncedSearch(query); // Trigger debounced search logic
  };

  // TODO: Implement search functionality
  // TODO: Implement create new chat functionality

  return (
    <aside className="w-80 bg-white border-r border-gray-200 flex flex-col h-screen flex-shrink-0">
      {/* Sidebar Header */}
      <div className="p-4 border-b border-gray-200 flex justify-between items-center flex-shrink-0">
        <div className="flex items-center">
          <Avatar className="w-10 h-10 mr-3">
            {/* Placeholder for actual user avatar logic */}
            <AvatarImage src={`https://avatar.vercel.sh/${ownerName || 'user'}.png`} alt={ownerName || 'User'} />
            <AvatarFallback>{userInitial}</AvatarFallback>
          </Avatar>
          <h2 className="font-semibold text-lg text-gray-800 truncate">{`${ownerName}'s`} Chats</h2>
        </div>
        <Button variant="ghost" size="icon" onClick={handleNewChatClick}>
          <PlusCircle className="h-5 w-5" />
          <span className="sr-only">New Chat</span>
        </Button>
      </div>

      {/* Search Bar */}
      <div className="p-4 flex-shrink-0">
        <div className="relative">
          <Input
            type="text"
            placeholder="Search chats..."
            className="pl-10 pr-4 py-2 text-sm"
            value={searchQuery} // Bind value to state
            onChange={handleSearchChange} // Handle changes
          />
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        </div>
      </div>

      {/* Chat List Container - Pass search query down */}
      <ScrollArea className="flex-grow">
        <ChatList searchQuery={searchQuery} />
      </ScrollArea>
    </aside>
  );
} 