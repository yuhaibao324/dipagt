'use client';

import React from 'react';
import { Chat } from '@/store/chatStore';
import { cn } from "@/lib/utils"; // Utility for conditional classes
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { formatDistanceToNow } from 'date-fns'; // For relative time

interface ChatItemProps {
  chat: Chat;
  isSelected: boolean;
  onSelect: () => void;
}

// Function to get initials from a name/title
const getInitials = (name: string): string => {
  const words = name.split(' ');
  if (words.length > 1) {
    return (words[0][0] + words[1][0]).toUpperCase();
  }
  return name.substring(0, 2).toUpperCase();
};

// Helper to safely format date
const formatUpdateTime = (dateString: string): string => {
  try {
    return formatDistanceToNow(new Date(dateString), { addSuffix: true });
  } catch (e) {
    console.error("Error formatting date:", e);
    return "Invalid date";
  }
};

export default function ChatItem({ chat, isSelected, onSelect }: ChatItemProps) {
  // Assuming title contains the name, e.g., "Alice (Designer)"
  const name = chat.title.split(' (')[0];
  const initials = getInitials(name);
  const lastUpdateTime = formatUpdateTime(chat.updated_at);

  // Use a placeholder avatar API or generate based on name
  const avatarUrl = `https://avatar.vercel.sh/${name.replace(/\s+/g, '')}.png?text=${initials}`;

  return (
    <div
      onClick={onSelect}
      className={cn(
        "flex items-center p-3 mx-2 rounded-lg cursor-pointer hover:bg-gray-100 transition-colors duration-150",
        isSelected ? "bg-blue-100 hover:bg-blue-200" : "bg-white"
      )}
    >
      <Avatar className="w-11 h-11 mr-3 flex-shrink-0">
        <AvatarImage src={avatarUrl} alt={name} />
        <AvatarFallback>{initials}</AvatarFallback>
      </Avatar>
      <div className="flex-grow overflow-hidden min-w-0">
        <div className="flex justify-between items-center mb-0.5">
          <h3
            className={cn(
              "font-semibold truncate",
              isSelected ? "text-blue-800" : "text-gray-800"
            )}
            title={chat.title}
          >
            {chat.title}
          </h3>
        </div>
        <span className="text-xs text-gray-500 block truncate">
          {lastUpdateTime}
        </span>
      </div>
    </div>
  );
} 