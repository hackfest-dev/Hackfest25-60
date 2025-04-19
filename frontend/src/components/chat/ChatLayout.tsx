import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../context/AuthContext';
import { IconMenu2, IconChevronLeft } from '@tabler/icons-react';
import Sidebar from './Sidebar';
import ChatMain from './ChatMain';
import MobileSidebar from './MobileSidebar';
import anime from 'animejs';

const ChatLayout: React.FC = () => {
  const { user } = useAuth();
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const [isDesktopSidebarOpen, setIsDesktopSidebarOpen] = useState(true);
  const [selectedChatId, setSelectedChatId] = useState<number | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    // Initial load animation
    anime({
      targets: containerRef.current,
      opacity: [0, 1],
      translateY: [20, 0],
      duration: 600,
      easing: 'easeOutQuad'
    });
  }, []);
  
  const toggleDesktopSidebar = () => {
    const newState = !isDesktopSidebarOpen;
    setIsDesktopSidebarOpen(newState);
    
    // Animate sidebar toggle
    anime({
      targets: '.sidebar-toggle-icon',
      rotate: newState ? 0 : 180,
      duration: 300,
      easing: 'easeInOutQuad'
    });
  };

  // Handler for when a new chat is created
  const handleNewChat = () => {
    // We can perform additional actions here if needed
    // The actual creation happens in Sidebar
  };

  // Handler for when a chat is selected in the sidebar
  const handleChatSelect = (chatId: number) => {
    setSelectedChatId(chatId);
    // On mobile, close the sidebar
    if (isMobileSidebarOpen) {
      setIsMobileSidebarOpen(false);
    }
  };
  
  return (
    <div 
      ref={containerRef} 
      className="flex h-screen bg-gradient-to-br from-gray-950 to-gray-900 text-slate-300 overflow-hidden"
    >
      {/* Desktop Sidebar - toggleable */}
      <div 
        className={`hidden md:block transition-all duration-300 ease-in-out ${isDesktopSidebarOpen ? 'md:w-80' : 'md:w-0'} flex-shrink-0 overflow-hidden`}
      >
        <Sidebar 
          className="h-full" 
          onNewChat={handleNewChat}
          onChatSelect={handleChatSelect}
        />
      </div>
      
      {/* Mobile Sidebar */}
      <MobileSidebar 
        isOpen={isMobileSidebarOpen} 
        onClose={() => setIsMobileSidebarOpen(false)} 
        onChatSelect={handleChatSelect}
        onNewChat={handleNewChat}
      />
      
      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden relative">
        {/* Mobile header with menu button */}
        <div className="md:hidden flex items-center p-4 backdrop-blur-md bg-gray-900/70 border-b border-gray-800/50">
          <button
            onClick={() => setIsMobileSidebarOpen(true)}
            className="p-2 mr-3 text-gray-400 hover:text-white transition-colors bg-gray-800/50 rounded-lg hover:bg-gray-700/50"
            aria-label="Open menu"
          >
            <IconMenu2 size={22} />
          </button>
          <h1 className="text-xl font-bold text-white">
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-purple-500">
              AI Chat
            </span>
          </h1>
        </div>
        
        {/* Desktop sidebar toggle button */}
        <button
          onClick={toggleDesktopSidebar}
          className="hidden md:flex absolute left-0 top-1/2 -translate-y-1/2 z-10 group"
          aria-label={isDesktopSidebarOpen ? "Close sidebar" : "Open sidebar"}
        >
          <div className="flex items-center justify-center h-10 w-5 bg-gray-800/80 hover:bg-indigo-600/90 backdrop-blur-sm rounded-r-lg transition-all duration-200 shadow-lg">
            <IconChevronLeft 
              size={18} 
              className="sidebar-toggle-icon text-gray-400 group-hover:text-white transition-colors"
            />
          </div>
        </button>
        
        <ChatMain 
          username={user?.name || 'User'} 
          key={selectedChatId || 'new-chat'}
          chatId={selectedChatId}
        />
      </div>
    </div>
  );
};

export default ChatLayout; 