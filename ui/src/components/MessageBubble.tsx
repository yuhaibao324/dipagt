'use client';

import React from 'react';
import { Message } from '@/store/chatStore';
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";
import { format } from 'date-fns';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MessageBubbleProps {
  message: Message;
  isOwnMessage: boolean;
  ownerName: string; // To display 'You' or agent name
}

// Helper to get initials or role identifier
const getSenderIdentifier = (message: Message, isOwnMessage: boolean, ownerName: string): string => {
  if (isOwnMessage) return ownerName.charAt(0).toUpperCase() || 'U';
  // Use agent name if available, otherwise role
  const name = message.agent_name || message.role;
  // Basic initial generation
  const words = name.split(' ');
  if (words.length > 1) {
    return (words[0][0] + words[1][0]).toUpperCase();
  }
  return name.substring(0, 1).toUpperCase();
};

// Use agent name if available
const getSenderName = (message: Message, isOwnMessage: boolean): string => {
  if (isOwnMessage) return 'You';
  return message.agent_name || (message.role.charAt(0).toUpperCase() + message.role.slice(1));
};

// Use actual agent avatar if available
const getAvatarUrl = (message: Message, isOwnMessage: boolean, ownerName: string): string => {
  if (isOwnMessage) return `https://avatar.vercel.sh/${ownerName}.png`;
  // Prioritize actual agent avatar URL
  if (message.agent_avatar) return message.agent_avatar;
  // Fallback to placeholder
  const fallbackSeed = message.agent_id || message.agent_name || message.role;
  return `https://avatar.vercel.sh/${fallbackSeed}.png`;
};

// Format timestamp
const formatTimestamp = (dateString: string): string => {
  try {
    return format(new Date(dateString), 'p'); // e.g., 10:30 AM
  } catch {
    return 'Invalid time';
  }
};

export default function MessageBubble({ message, isOwnMessage, ownerName }: MessageBubbleProps) {
  const senderIdentifier = getSenderIdentifier(message, isOwnMessage, ownerName);
  const senderName = getSenderName(message, isOwnMessage);
  const avatarUrl = getAvatarUrl(message, isOwnMessage, ownerName);
  const timestamp = formatTimestamp(message.created_at);

  const renderContent = () => {
    if (message.type === 'image' && message.content.startsWith('http')) {
      return (
        <img
          src={message.content}
          alt="Chat image"
          className="rounded-lg max-w-xs md:max-w-sm lg:max-w-md shadow-md mt-2 cursor-pointer"
          onClick={() => window.open(message.content, '_blank')}
        />
      );
    }
    // Add more types handling here (e.g., file)

    // Render text content (default) using ReactMarkdown
    // Wrap in a div and apply prose styles for Tailwind CSS Typography plugin
    return (
      <div className="prose prose-sm dark:prose-invert max-w-none">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            a: ({ ...props }) => <a {...props} target="_blank" rel="noopener noreferrer" />
          }}
        >
          {message.content}
        </ReactMarkdown>
      </div>
    );
  };

  return (
    <div className={cn("flex items-start gap-3", isOwnMessage && "justify-end")}>
      {!isOwnMessage && (
        <Avatar className="w-8 h-8 flex-shrink-0 mt-1">
          <AvatarImage src={avatarUrl} alt={senderName} />
          <AvatarFallback>{senderIdentifier}</AvatarFallback>
        </Avatar>
      )}
      <div className={cn("max-w-lg lg:max-w-xl", isOwnMessage && "text-right")}>
        <div
          className={cn(
            "p-3 rounded-lg shadow-sm inline-block",
            isOwnMessage
              ? "bg-blue-500 text-white rounded-br-none"
              : "bg-white dark:bg-gray-700 rounded-tl-none"
          )}
        >
          {renderContent()}
        </div>
        <span className="text-xs text-gray-500 dark:text-gray-400 mt-1 block px-1">
          {!isOwnMessage ? `${senderName} - ${timestamp}` : timestamp}
        </span>
      </div>
      {/* We don't typically show avatar for own messages in standard chat UIs */}
      {/* {isOwnMessage && (
        <Avatar className="w-8 h-8 flex-shrink-0 mt-1">
          <AvatarImage src={avatarUrl} alt={senderName} />
          <AvatarFallback>{senderIdentifier}</AvatarFallback>
        </Avatar>
      )} */}
    </div>
  );
} 