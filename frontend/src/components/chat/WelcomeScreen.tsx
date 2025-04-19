import React, { RefObject } from 'react';
import { IconBolt, IconMessage, IconRocket } from '@tabler/icons-react';

interface WelcomeScreenProps {
  username: string;
  welcomeRef: RefObject<HTMLDivElement>;
}

const WelcomeScreen: React.FC<WelcomeScreenProps> = ({ username, welcomeRef }) => {
  return (
    <div className="flex-1 overflow-y-auto py-6 px-4 md:px-6">
      <div className="flex items-center justify-center h-full" ref={welcomeRef}>
        <div className="text-center max-w-xl mx-auto">
          <div className="w-20 h-20 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center mx-auto mb-8 shadow-lg shadow-indigo-600/20 p-1.5 ring-4 ring-gray-800/40">
            <div className="bg-gray-900 w-full h-full rounded-full flex items-center justify-center">
              <IconMessage size={32} className="text-white" />
            </div>
          </div>
          
          <h2 className="text-4xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
            Hello {username}
          </h2>
          
          <p className="text-gray-400 text-lg leading-relaxed mb-8 max-w-md mx-auto">
            Start a new conversation or continue a previous chat. Your chat history is saved automatically.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-lg mx-auto">
            <div className="p-4 rounded-xl bg-gradient-to-br from-gray-800/50 to-gray-900/50 border border-gray-700/50 hover:border-indigo-500/30 shadow-sm hover:shadow-md transition-all duration-200 hover:bg-gray-800/70 transform hover:-translate-y-1">
              <div className="flex items-center mb-2">
                <div className="w-8 h-8 rounded-md bg-indigo-600/30 flex items-center justify-center mr-3">
                  <IconMessage size={18} className="text-indigo-400" />
                </div>
                <h3 className="font-semibold text-white">Ask a Question</h3>
              </div>
              <p className="text-sm text-gray-400">Get instant answers to your questions with our AI assistant</p>
            </div>
            
            <div className="p-4 rounded-xl bg-gradient-to-br from-gray-800/50 to-gray-900/50 border border-gray-700/50 hover:border-indigo-500/30 shadow-sm hover:shadow-md transition-all duration-200 hover:bg-gray-800/70 transform hover:-translate-y-1">
              <div className="flex items-center mb-2">
                <div className="w-8 h-8 rounded-md bg-purple-600/30 flex items-center justify-center mr-3">
                  <IconRocket size={18} className="text-purple-400" />
                </div>
                <h3 className="font-semibold text-white">Export Conversations</h3>
              </div>
              <p className="text-sm text-gray-400">Download your chat history as a PDF document anytime</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WelcomeScreen; 