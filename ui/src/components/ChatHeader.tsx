'use client';

import React from 'react';
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Search, Cog, MoreVertical } from 'lucide-react';
import { Chat } from '@/store/chatStore';

interface ChatHeaderProps {
  chat: Chat;
}

export default function ChatHeader({ chat }: ChatHeaderProps) {
  const displayName = chat.title || 'Chat';
  const initials = displayName.split(' ').map(n => n[0]).slice(0, 2).join('').toUpperCase();
  const avatarUrl = `https://avatar.vercel.sh/${chat.id}.png?text=${initials}`;

  return (
    <header className="bg-white border-b border-gray-200 p-4 flex justify-between items-center flex-shrink-0 shadow-sm">
      <div className="flex items-center">
        <Avatar className="w-10 h-10 mr-3">
          <AvatarImage src={avatarUrl} alt={displayName} />
          <AvatarFallback>{initials}</AvatarFallback>
        </Avatar>
        <div>
          <h2 className="font-semibold text-lg text-gray-800 truncate">{displayName}</h2>
          <p className="text-xs text-gray-500">ID: {chat.id.substring(0, 8)}...</p>
        </div>
      </div>
      <div className="flex items-center space-x-1">
        <Button variant="ghost" size="icon">
          <Search className="h-5 w-5" />
          <span className="sr-only">Search</span>
        </Button>
        <Button variant="ghost" size="icon">
          <Cog className="h-5 w-5" />
          <span className="sr-only">Settings</span>
        </Button>
        <Button variant="ghost" size="icon">
          <MoreVertical className="h-5 w-5" />
          <span className="sr-only">More options</span>
        </Button>
      </div>
    </header>
  );
} 