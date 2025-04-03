import { create, StateCreator } from "zustand";

// Define interfaces for Chat and Message (adjust based on actual API response)
export interface Message {
  id: string;
  chat_id: string;
  agent_id?: string | null; // Optional agent ID
  content: string;
  role: "user" | "assistant" | "system";
  type: string; // e.g., 'text', 'image'
  created_at: string; // ISO string
  metadata?: Record<string, unknown>;
  agent_name?: string | null; // Add agent name
  agent_avatar?: string | null; // Add agent avatar URL
}

export interface Chat {
  id: string;
  title: string;
  description?: string | null;
  status: string;
  message_count?: number; // Assuming this comes from the list endpoint
  created_at: string;
  updated_at: string;
}

// --- Stream Event Interfaces ---

interface StreamProgressData {
  step: string; // e.g., status, chat_created, history_retrieved, user_message_saved, intention_recognized, plan_generated, action_started, action_result, action_error, fatal_error
  message?: string | Message | null; // Can be a status string or a full Message object for user_message_saved
  error?: string;
  // Specific known optional fields for certain steps:
  chat_id?: string; // For chat_created (can be derived from chat object now)
  title?: string; // For chat_created (can be derived from chat object now)
  chat?: Chat; // For chat_created (contains full chat details)
  count?: number; // For history_retrieved
  index?: number; // For action_started, action_result, action_error
  result?: Message | null; // For action_result (the assistant message object)
  agent_name?: string; // For action_started, action_result, action_error
  action_type?: string; // For action_started, action_error
  content?: string; // Add content field for message_chunk step
  // Fields with currently unknown structure - use unknown
  intention?: unknown; // For intention_recognized
  actions?: unknown[]; // For plan_generated
}

interface StreamEvent {
  type: "progress" | "done";
  // For 'done', data might contain { last_assistant_message?: Message }
  // For 'progress', data contains StreamProgressData
  data:
    | StreamProgressData
    | { last_assistant_message?: Message }
    | Record<string, never>;
}

// Export ChatState
export interface ChatState {
  chats: Chat[];
  currentChatId: string | null;
  messages: { [chatId: string]: Message[] }; // Store messages per chat ID
  isLoading: boolean;
  error: string | null;
  progressMessage: string | null; // Added for progress updates
  streamingMessageId: string | null; // ID of the message being streamed

  setChats: (chats: Chat[]) => void;
  addChat: (chat: Chat) => void;
  setCurrentChatId: (chatId: string | null) => void;
  startNewChat: () => void;
  setMessages: (chatId: string, messages: Message[]) => void;
  addMessage: (chatId: string, message: Message) => void;
  updateMessageContent: (
    chatId: string,
    messageId: string,
    contentChunk: string
  ) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setProgressMessage: (message: string | null) => void; // Added setter
  setStreamingMessageId: (id: string | null) => void; // Add new setter
  sendMessageStream: (
    messageContent: string,
    owner: string,
    chatId?: string | null
  ) => Promise<void>; // Action defined directly
}

// Define the store creator with the full state including actions
const chatStoreCreator: StateCreator<ChatState> = (set, get) => ({
  chats: [],
  currentChatId: null,
  messages: {},
  isLoading: false,
  error: null,
  progressMessage: null,
  streamingMessageId: null, // Initialize new state

  // --- Sync Setters ---
  setChats: (chats) => set({ chats }),
  addChat: (chat) => set((state) => ({ chats: [chat, ...state.chats] })),
  setCurrentChatId: (chatId) =>
    set({ currentChatId: chatId, error: null, progressMessage: null }),
  startNewChat: () =>
    set({ currentChatId: null, error: null, progressMessage: null }),
  setMessages: (chatId, messages) =>
    set((state) => ({
      messages: { ...state.messages, [chatId]: messages },
    })),
  addMessage: (chatId, message) =>
    set((state) => {
      const chatMessages = state.messages[chatId] || [];
      // Prevent adding duplicate final message IDs
      if (
        message.id &&
        !message.id.startsWith("temp-") &&
        chatMessages.some((m) => m.id === message.id)
      ) {
        console.warn(`Attempted to add duplicate message ID: ${message.id}`);
        return {}; // No change
      }
      // Add message and sort
      const updatedMessages = [...chatMessages, message].sort(
        (a, b) =>
          new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
      );
      return {
        messages: {
          ...state.messages,
          [chatId]: updatedMessages,
        },
      };
    }),
  updateMessageContent: (chatId, messageId, contentChunk) =>
    set((state) => {
      const chatMessages = state.messages[chatId] || [];
      const messageIndex = chatMessages.findIndex((m) => m.id === messageId);
      if (messageIndex === -1) {
        console.warn(
          `Message ID ${messageId} not found in chat ${chatId} for update.`
        );
        return {}; // Message not found
      }
      // Create a new message object with appended content
      const updatedMessage = {
        ...chatMessages[messageIndex],
        content: chatMessages[messageIndex].content + contentChunk,
      };
      // Create a new array with the updated message
      const updatedMessages = [
        ...chatMessages.slice(0, messageIndex),
        updatedMessage,
        ...chatMessages.slice(messageIndex + 1),
      ];
      return {
        messages: {
          ...state.messages,
          [chatId]: updatedMessages,
        },
      };
    }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error: error }),
  setProgressMessage: (message) => set({ progressMessage: message }),
  setStreamingMessageId: (id) => set({ streamingMessageId: id }), // Implement setter

  // --- Async Action: sendMessageStream ---
  sendMessageStream: async (messageContent, owner, chatId) => {
    set({
      isLoading: true,
      error: null,
      progressMessage: "Sending message...",
      streamingMessageId: null, // Reset streaming ID at start
    });
    const currentChatId = chatId || get().currentChatId;
    let tempChatId = currentChatId; // Use let for potential update

    try {
      const baseUrl =
        process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
      const apiUrl = `${baseUrl}/chat/`;
      const response = await fetch(apiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: messageContent,
          chat_id: currentChatId,
          owner: owner,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
          `HTTP error! status: ${response.status}, message: ${errorText}`
        );
      }

      if (!response.body) {
        throw new Error("Response body is null");
      }

      const reader = response.body!.getReader(); // Add non-null assertion
      const decoder = new TextDecoder();
      let buffer = "";
      let currentStreamingMessageId: string | null = null; // Local var for this stream

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          set({ streamingMessageId: null }); // Clear on normal completion
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        let boundary = buffer.indexOf("\n\n");
        while (boundary >= 0) {
          const chunk = buffer.substring(0, boundary);
          buffer = buffer.substring(boundary + 2);
          if (chunk.startsWith("data: ")) {
            const jsonString = chunk.substring(6);
            try {
              const event: StreamEvent = JSON.parse(jsonString);
              if (event.type === "progress") {
                const data = event.data as StreamProgressData;
                let progressText = get().progressMessage;

                switch (data.step) {
                  case "status":
                    progressText = data.message as string;
                    break;
                  case "chat_created":
                    // Assert the type of the received chat data
                    const newChat = data.chat as Chat;
                    tempChatId = newChat.id; // Update tempChatId from the received object
                    // Add the new chat to the store
                    get().addChat(newChat);
                    // Set it as the current chat
                    set({ currentChatId: tempChatId });
                    progressText = `Chat created: ${newChat.title}`;
                    break;
                  case "user_message_saved":
                    if (
                      tempChatId &&
                      data.message &&
                      typeof data.message === "object" &&
                      "id" in data.message
                    ) {
                      get().addMessage(tempChatId, data.message as Message);
                    }
                    progressText = "User message saved.";
                    break;
                  case "action_started":
                    progressText = `Agent ${data.agent_name} starting action...`;
                    // Create placeholder message for streaming content
                    if (tempChatId) {
                      const tempId = `temp-stream-${Date.now()}-${data.index}`;
                      const placeholder: Message = {
                        id: tempId,
                        chat_id: tempChatId,
                        role: "assistant",
                        content: "", // Start with empty content
                        type: "text", // Assuming text
                        created_at: new Date().toISOString(),
                        agent_name: data.agent_name,
                        agent_id: undefined, // Or get from somewhere if available
                        agent_avatar: undefined, // Or get from somewhere
                        metadata: { action_type: data.action_type },
                      };
                      get().addMessage(tempChatId, placeholder);
                      currentStreamingMessageId = tempId; // Track the ID locally for this stream
                      set({ streamingMessageId: tempId }); // Update global state
                    }
                    break;
                  case "message_chunk":
                    if (
                      tempChatId &&
                      currentStreamingMessageId &&
                      data.content
                    ) {
                      get().updateMessageContent(
                        tempChatId,
                        currentStreamingMessageId,
                        data.content
                      );
                      // No progress text update needed for every chunk usually
                      progressText = get().progressMessage; // Keep existing progress text
                    }
                    break;
                  case "action_result":
                    if (tempChatId && data.result) {
                      // Remove placeholder if it exists
                      if (currentStreamingMessageId) {
                        set((state) => {
                          const msgs = (
                            state.messages[tempChatId!] || []
                          ).filter((m) => m.id !== currentStreamingMessageId);
                          return {
                            messages: {
                              ...state.messages,
                              [tempChatId!]: msgs,
                            },
                            streamingMessageId:
                              state.streamingMessageId ===
                              currentStreamingMessageId
                                ? null
                                : state.streamingMessageId, // Clear global ID only if it matches
                          };
                        });
                        // Add the final message (will replace placeholder visually if ID matches)
                        get().addMessage(tempChatId, data.result as Message);
                        currentStreamingMessageId = null; // Clear local tracking for this action
                      } else {
                        // Should not happen often, but add if no placeholder was tracked
                        get().addMessage(tempChatId, data.result as Message);
                      }
                    } else {
                      set({ streamingMessageId: null }); // Clear if action finished without result
                    }
                    progressText = `Action completed: ${data.result?.agent_name}`;
                    currentStreamingMessageId = null; // Clear local tracker after action result/error
                    set({ streamingMessageId: null }); // Clear global tracker
                    break;
                  case "action_error":
                  case "fatal_error":
                    console.error("Stream Error:", data.error);
                    set({
                      error: `Error: ${data.error}`,
                      streamingMessageId: null,
                    }); // Clear streaming ID on error
                    progressText = `Error: ${data.error}`;
                    currentStreamingMessageId = null;
                    break;
                  default:
                    progressText = `Progress: ${data.step}`;
                    if (data.message && typeof data.message === "string") {
                      progressText += `: ${data.message}`;
                    }
                    console.log("Progress step:", data);
                    break;
                }
                if (progressText !== get().progressMessage) {
                  // Only update if changed
                  set({ progressMessage: progressText });
                }
              } else if (event.type === "done") {
                console.log("Stream finished.");
                set({
                  isLoading: false,
                  progressMessage: null,
                  streamingMessageId: null,
                });
                reader.cancel();
                return;
              }
            } catch (e) {
              console.error(
                "Failed to parse stream data:",
                e,
                "Data:",
                jsonString
              );
              set({
                error: "Failed to parse stream data",
                isLoading: false,
                progressMessage: null,
                streamingMessageId: null,
              });
              reader.cancel();
              return;
            }
          }
          boundary = buffer.indexOf("\n\n");
        }
      }
      // Fallback cleanup if loop exits unexpectedly
      set({
        isLoading: false,
        progressMessage: null,
        streamingMessageId: null,
      });
    } catch (error) {
      console.error("Failed to send message:", error);
      set({
        isLoading: false,
        error:
          error instanceof Error ? error.message : "An unknown error occurred",
        progressMessage: null,
        streamingMessageId: null,
      });
    }
  },
});

// --- Store Creation and Export ---

// Dummy store for SSR (now matches ChatState directly)
const dummyStore: ChatState = {
  chats: [],
  currentChatId: null,
  messages: {},
  isLoading: false,
  error: null,
  progressMessage: null,
  streamingMessageId: null,
  setChats: () => console.warn("Attempted to set chats on server"),
  addChat: () => console.warn("Attempted to add chat on server"),
  setCurrentChatId: () =>
    console.warn("Attempted to set current chat ID on server"),
  startNewChat: () => console.warn("Attempted to start new chat on server"),
  setMessages: () => console.warn("Attempted to set messages on server"),
  addMessage: () => console.warn("Attempted to add message on server"),
  updateMessageContent: () =>
    console.warn("Attempted to update message content on server"),
  setLoading: () => console.warn("Attempted to set loading state on server"),
  setError: () => console.warn("Attempted to set error on server"),
  setProgressMessage: () =>
    console.warn("Attempted to set progress message on server"),
  setStreamingMessageId: () =>
    console.warn("Attempted to set streaming message ID on server"),
  sendMessageStream: async () => {
    console.warn("Attempted to send message stream on server");
    return Promise.resolve();
  },
};

// Export the store, handling SSR
export const useChatStore =
  typeof window === "undefined"
    ? create<ChatState>(() => dummyStore)
    : create<ChatState>(chatStoreCreator); // Use the creator directly
