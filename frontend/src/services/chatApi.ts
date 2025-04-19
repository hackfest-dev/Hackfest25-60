import api from './api';

// Types
export interface Message {
  id: number;
  chat_id: number;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export interface Chat {
  id: number;
  user_id: number;
  title: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface ChatWithMessages extends Chat {
  messages: Message[];
}

export interface ChatCreate {
  title?: string;
}

export interface ChatUpdate {
  title?: string;
  is_active?: boolean;
}

export interface MessageCreate {
  role: 'user' | 'assistant';
  content: string;
}

// Chat API service
export const chatAPI = {
  // Create a new chat
  createChat: async (data: ChatCreate = {}): Promise<Chat> => {
    const response = await api.post('/chats', data);
    return response.data;
  },

  // Get all chats for current user
  getChats: async (activeOnly: boolean = true): Promise<Chat[]> => {
    const response = await api.get('/chats', {
      params: { active_only: activeOnly }
    });
    return response.data;
  },

  // Get a specific chat with its messages
  getChat: async (chatId: number): Promise<ChatWithMessages> => {
    const response = await api.get(`/chats/${chatId}`);
    return response.data;
  },

  // Update a chat
  updateChat: async (chatId: number, data: ChatUpdate): Promise<Chat> => {
    const response = await api.put(`/chats/${chatId}`, data);
    return response.data;
  },

  // Delete a chat (soft delete by default)
  deleteChat: async (chatId: number, permanent: boolean = false): Promise<void> => {
    await api.delete(`/chats/${chatId}`, {
      params: { permanent }
    });
  },

  // Add a message to a chat - now returns array of messages (user message and AI response)
  addMessage: async (chatId: number, message: MessageCreate): Promise<Message[]> => {
    const response = await api.post(`/chats/${chatId}/messages`, message);
    return response.data;
  },

  // Get messages for a chat
  getMessages: async (chatId: number): Promise<Message[]> => {
    const response = await api.get(`/chats/${chatId}/messages`);
    return response.data;
  }
};

export default chatAPI; 