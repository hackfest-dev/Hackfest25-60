import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { 
  IconHistory, 
  IconUser, 
  IconLogout, 
  IconPlus, 
  IconTrash,
  IconMessageCircle,
  IconChevronRight,
  IconStar,
  IconMessagePlus
} from '@tabler/icons-react';
import anime from 'animejs';

interface SidebarProps {
  className?: string;
}

interface ChatHistory {
  id: string;
  title: string;
  date: Date;
  starred?: boolean;
}

const Sidebar: React.FC<SidebarProps> = ({ className }) => {
  const { user, logout } = useAuth();
  const [chatHistory, setChatHistory] = useState<ChatHistory[]>([
    { id: '1', title: 'AI Research Discussion', date: new Date(2023, 6, 15), starred: true },
    { id: '2', title: 'Code Generation Help', date: new Date(2023, 6, 16) },
    { id: '3', title: 'Data Analysis Results', date: new Date(2023, 6, 17) }
  ]);
  const [activeChatId, setActiveChatId] = useState<string | null>('1');
  const [expanded, setExpanded] = useState(true);
  
  useEffect(() => {
    // Animate sidebar elements on load
    anime({
      targets: '.sidebar-item',
      translateX: [-30, 0],
      opacity: [0, 1],
      delay: anime.stagger(80),
      easing: 'easeOutQuad'
    });
  }, []);
  
  const createNewChat = () => {
    const newChat = {
      id: Date.now().toString(),
      title: `New Chat ${chatHistory.length + 1}`,
      date: new Date()
    };
    
    setChatHistory([newChat, ...chatHistory]);
    setActiveChatId(newChat.id);
    
    // Animation for new chat
    setTimeout(() => {
      anime({
        targets: '.sidebar-item:first-child',
        backgroundColor: ['rgba(79, 70, 229, 0.2)', 'rgba(0, 0, 0, 0)'],
        duration: 1000,
        easing: 'easeOutQuad'
      });
    }, 0);
  };
  
  const deleteChat = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    
    // Find the element and animate it before removal
    const target = document.querySelector(`#chat-${id}`);
    
    anime({
      targets: target,
      translateX: [0, -50],
      opacity: [1, 0],
      easing: 'easeOutQuad',
      duration: 300,
      complete: () => {
        setChatHistory(chatHistory.filter(chat => chat.id !== id));
        if (activeChatId === id) {
          setActiveChatId(chatHistory[0]?.id || null);
        }
      }
    });
  };
  
  const toggleStarred = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setChatHistory(
      chatHistory.map(chat => chat.id === id ? { ...chat, starred: !chat.starred } : chat)
    );
  };
  
  const selectChat = (id: string) => {
    setActiveChatId(id);
  };

  return (
    <div className={`flex flex-col h-full border-r border-gray-800/40 bg-gray-900/80 backdrop-blur-md ${className}`}>
      {/* Chat actions */}
      <div className="p-4 border-b border-gray-800/40">
        <button 
          onClick={createNewChat}
          className="w-full py-2 px-4 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white rounded-lg flex items-center justify-center gap-2 transition-all duration-200 shadow-md hover:shadow-indigo-600/20"
        >
          <IconMessagePlus size={18} />
          <span>New Chat</span>
        </button>
      </div>
      
      {/* Chat history section */}
      <div className="flex-1 overflow-y-auto py-4 px-3 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
        <div className="mb-3">
          <div className="flex items-center justify-between px-2 mb-2">
            <button 
              onClick={() => setExpanded(!expanded)}
              className="flex items-center gap-2 text-sm font-medium text-gray-400 hover:text-white transition-colors"
            >
              <IconHistory size={18} />
              <span>Recent Chats</span>
              <IconChevronRight 
                size={16} 
                className={`transition-transform duration-200 ${expanded ? 'rotate-90' : ''}`} 
              />
            </button>
          </div>
          
          {expanded && (
            <>
              {chatHistory.length === 0 ? (
                <div className="py-6 text-center text-gray-500">
                  <p>No chat history yet</p>
                </div>
              ) : (
                <div className="space-y-1.5 px-1">
                  {chatHistory.map(chat => (
                    <div 
                      id={`chat-${chat.id}`}
                      key={chat.id}
                      onClick={() => selectChat(chat.id)}
                      className={`sidebar-item flex items-center justify-between p-3 rounded-lg cursor-pointer transition-all duration-200 group ${
                        activeChatId === chat.id
                          ? 'bg-indigo-600/20 text-white border-l-2 border-indigo-500 pl-[10px] shadow-sm'
                          : 'hover:bg-gray-800/50 text-gray-300 hover:text-white'
                      }`}
                    >
                      <div className="flex items-center gap-3 overflow-hidden">
                        <div className={`w-7 h-7 rounded-md flex items-center justify-center flex-shrink-0 ${
                          activeChatId === chat.id ? 'bg-indigo-500/30' : 'bg-gray-800'
                        }`}>
                          <IconMessageCircle size={16} className={activeChatId === chat.id ? 'text-indigo-400' : 'text-gray-400'} />
                        </div>
                        <div className="overflow-hidden">
                          <h3 className="text-sm font-medium truncate">{chat.title}</h3>
                          <p className="text-xs text-gray-400 truncate">
                            {chat.date.toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                        <button
                          onClick={(e) => toggleStarred(chat.id, e)}
                          className={`p-1 rounded hover:bg-gray-700/50 ${chat.starred ? 'text-yellow-400' : 'text-gray-500 hover:text-gray-300'}`}
                          aria-label={chat.starred ? "Unstar chat" : "Star chat"}
                        >
                          <IconStar size={14} />
                        </button>
                        <button
                          onClick={(e) => deleteChat(chat.id, e)}
                          className="p-1 rounded text-gray-500 hover:text-red-400 hover:bg-gray-700/50"
                          aria-label="Delete chat"
                        >
                          <IconTrash size={14} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      </div>
      
      {/* User section at bottom */}
      <div className="border-t border-gray-800/40 p-3">
        <div className="flex items-center justify-between bg-gray-800/50 rounded-lg p-2">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-md">
              <IconUser size={18} className="text-white" />
            </div>
            <div>
              <p className="font-medium text-white">{user?.name || 'User'}</p>
              <p className="text-xs text-gray-400">{user?.email || 'user@example.com'}</p>
            </div>
          </div>
          <button 
            onClick={logout}
            className="text-gray-400 hover:text-white p-1.5 rounded-full hover:bg-gray-700/50 transition-colors"
            aria-label="Logout"
          >
            <IconLogout size={18} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default Sidebar; 