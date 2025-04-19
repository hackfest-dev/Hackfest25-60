import React from 'react';
import { IconX } from '@tabler/icons-react';
import Sidebar from './Sidebar';

interface MobileSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  onChatSelect?: (chatId: number) => void;
  onNewChat?: () => void;
}

const MobileSidebar: React.FC<MobileSidebarProps> = ({ 
  isOpen, 
  onClose,
  onChatSelect,
  onNewChat
}) => {
  // Handler for chat selection that also closes the sidebar
  const handleChatSelect = (chatId: number) => {
    if (onChatSelect) {
      onChatSelect(chatId);
    }
    onClose();
  };
  
  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={onClose}
        />
      )}
      
      {/* Sidebar */}
      <div 
        className={`fixed top-0 left-0 bottom-0 w-80 bg-gray-900 z-50 transform transition-transform duration-300 ease-in-out md:hidden ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex justify-end p-4 border-b border-gray-800">
          <button 
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800/70 transition"
          >
            <IconX size={20} />
          </button>
        </div>
        
        <Sidebar 
          className="h-[calc(100%-64px)]" 
          onChatSelect={handleChatSelect}
          onNewChat={onNewChat}
        />
      </div>
    </>
  );
};

export default MobileSidebar; 