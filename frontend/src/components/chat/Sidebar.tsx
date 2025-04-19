import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  IconPlus, 
  IconTrash, 
  IconMessage, 
  IconLogout,
  IconSettings,
  IconAdjustments,
  IconClockHour4,
  IconArrowsSort
} from '@tabler/icons-react';
import { useAuth } from '../../context/AuthContext';
import chatAPI, { Chat } from '../../services/chatApi';

interface SidebarProps {
  className?: string;
  onNewChat?: () => void;
  onChatSelect?: (chatId: number) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ 
  className = "", 
  onNewChat,
  onChatSelect
}) => {
  const { logout, user } = useAuth();
  const [chats, setChats] = useState<Chat[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sortNewest, setSortNewest] = useState(true);
  const [activeChat, setActiveChat] = useState<number | null>(null);

  // Load chat history
  useEffect(() => {
    const loadChats = async () => {
      try {
        setIsLoading(true);
        const chatList = await chatAPI.getChats();
        setChats(chatList);
        
        // Set active chat to the first one if available
        if (chatList.length > 0 && !activeChat) {
          setActiveChat(chatList[0].id);
          if (onChatSelect) {
            onChatSelect(chatList[0].id);
          }
        }
      } catch (error) {
        console.error('Failed to load chats:', error);
      } finally {
        setIsLoading(false);
      }
    };
    
    loadChats();
  }, []);

  // Create a new chat
  const createNewChat = async () => {
    try {
      // Call the API to create a new chat
      const newChat = await chatAPI.createChat({ title: "New Chat" });
      
      // Add it to our list
      setChats(prev => [newChat, ...prev]);
      
      // Set it as active
      setActiveChat(newChat.id);
      
      // Notify parent component
      if (onNewChat) {
        onNewChat();
      }
      
      // Select this chat
      if (onChatSelect) {
        onChatSelect(newChat.id);
      }
    } catch (error) {
      console.error('Failed to create new chat:', error);
    }
  };

  // Delete a chat
  const deleteChat = async (chatId: number, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent selecting the chat when deleting
    
    try {
      // Call the API to delete the chat
      await chatAPI.deleteChat(chatId);
      
      // Remove from our list
      setChats(prev => prev.filter(chat => chat.id !== chatId));
      
      // If this was the active chat, select another one
      if (activeChat === chatId) {
        const remainingChats = chats.filter(chat => chat.id !== chatId);
        if (remainingChats.length > 0) {
          setActiveChat(remainingChats[0].id);
          if (onChatSelect) {
            onChatSelect(remainingChats[0].id);
          }
        } else {
          setActiveChat(null);
          // Create a new chat if there are none left
          createNewChat();
        }
      }
    } catch (error) {
      console.error('Failed to delete chat:', error);
    }
  };

  // Handle chat selection
  const handleChatSelect = (chatId: number) => {
    setActiveChat(chatId);
    if (onChatSelect) {
      onChatSelect(chatId);
    }
  };

  // Toggle sort order
  const toggleSortOrder = () => {
    setSortNewest(!sortNewest);
    // Re-sort the chats
    setChats(prev => [...prev].sort((a, b) => {
      const dateA = new Date(a.updated_at || a.created_at).getTime();
      const dateB = new Date(b.updated_at || b.created_at).getTime();
      return sortNewest ? dateB - dateA : dateA - dateB;
    }));
  };

  // Format chat title
  const formatChatTitle = (chat: Chat) => {
    if (chat.title) return chat.title;
    
    // If no title, create one from created_at date
    const date = new Date(chat.created_at);
    return `Chat ${date.toLocaleDateString()}`;
  };

  return (
    <div className={`flex flex-col h-full bg-gray-900 border-r border-gray-800 ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-800">
        <div className="flex items-center justify-between">
          <div className="text-xl font-bold text-white">
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-indigo-500">
              Chat History
            </span>
          </div>
          <div className="flex space-x-1">
            <button 
              onClick={toggleSortOrder}
              className="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800 transition"
              title={sortNewest ? "Showing newest first" : "Showing oldest first"}
            >
              <IconArrowsSort size={18} />
            </button>
            <button
              onClick={createNewChat}
              className="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800 transition"
              title="New chat"
            >
              <IconPlus size={18} />
            </button>
          </div>
        </div>
      </div>
      
      {/* Chat list */}
      <div className="flex-1 overflow-y-auto py-2">
        {isLoading ? (
          <div className="text-center py-4 text-gray-500">Loading chats...</div>
        ) : chats.length === 0 ? (
          <div className="text-center py-4 text-gray-500">No chats yet</div>
        ) : (
          chats.map(chat => (
            <div
              key={chat.id}
              onClick={() => handleChatSelect(chat.id)}
              className={`group flex items-center justify-between px-4 py-2 my-1 mx-2 rounded-lg cursor-pointer transition-all duration-200 ${
                activeChat === chat.id
                  ? 'bg-indigo-600/20 text-indigo-300'
                  : 'hover:bg-gray-800/70 text-gray-300'
              }`}
            >
              <div className="flex items-center overflow-hidden">
                <IconMessage size={18} className="mr-2 flex-shrink-0" />
                <span className="truncate">
                  {formatChatTitle(chat)}
                </span>
              </div>
              <button
                onClick={(e) => deleteChat(chat.id, e)}
                className={`p-1 rounded-lg transition-opacity duration-200 ${
                  activeChat === chat.id 
                    ? 'text-indigo-300 hover:bg-indigo-700/50' 
                    : 'text-gray-500 hover:text-gray-300 hover:bg-gray-700/50'
                } opacity-0 group-hover:opacity-100`}
                title="Delete chat"
              >
                <IconTrash size={16} />
              </button>
            </div>
          ))
        )}
      </div>
      
      {/* Footer */}
      <div className="p-4 border-t border-gray-800">
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-400 truncate">
            {user?.name || 'User'}
          </div>
          <div className="flex space-x-1">
            <button 
              className="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800 transition"
              title="Settings"
            >
              <IconSettings size={18} />
            </button>
            <button 
              onClick={logout}
              className="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800 transition"
              title="Logout"
            >
              <IconLogout size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar; 