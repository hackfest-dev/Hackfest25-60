import React, { useState, useEffect, useRef } from 'react';
import { 
  IconChevronDown, 
  IconAdjustmentsHorizontal, 
  IconBooks,
  IconBrandOpenai,
  IconCircleFilled,
  IconRobot,
  IconBrandGoogle,
  IconBolt,
  IconFlame,
  IconBrandCodesandbox,
  IconBrain,
  IconAbc,
  IconSparkles,
  IconX,
  IconMicrophone,
  IconHeadphones,
  IconSearch,
  IconExternalLink,
  IconMoodHappy,
  IconSend,
  IconMessage
} from '@tabler/icons-react';
import SearchBar from './SearchBar';
import anime from 'animejs';
import ModelSelector from './ModelSelector';
import ResearchInterface from './ResearchInterface';
import WelcomeScreen from './WelcomeScreen';
import ActionButtonGroup from './ActionButtonGroup';

interface ChatMainProps {
  username: string;
}

// Add Message interface definition
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  createdAt: Date;
  updatedAt: Date;
}

export type ModelProvider = {
  id: string;
  name: string;
  icon: React.ReactNode;
  color: string;
  description?: string;
};

export type ResearchMode = 'idle' | 'processing' | 'chat';

export type FeatureType = 'queryRefiner' | 'deepResearch' | 'podcastCreation' | 'extendedResearch';

export const modelProviders: ModelProvider[] = [
  { 
    id: 'gpt4', 
    name: 'GPT-4o', 
    icon: <IconBrandOpenai size={16} />,
    color: 'from-teal-500 to-emerald-600',
    description: 'OpenAI\'s most advanced model'
  },
  { 
    id: 'claude', 
    name: 'Claude 3 Opus', 
    icon: <IconCircleFilled size={16} />, 
    color: 'from-violet-500 to-purple-600',
    description: 'Anthropic\'s most powerful model'
  },
  { 
    id: 'gemini', 
    name: 'Gemini Pro', 
    icon: <IconBrandGoogle size={16} />,
    color: 'from-blue-500 to-indigo-600',
    description: 'Google\'s most capable model'
  },
  { 
    id: 'mistral', 
    name: 'Mistral Large', 
    icon: <IconRobot size={16} />,
    color: 'from-rose-500 to-red-600',
    description: 'Advanced reasoning and instructions'
  },
  { 
    id: 'llama3', 
    name: 'Llama 3 70B', 
    icon: <IconFlame size={16} />,
    color: 'from-orange-500 to-amber-600',
    description: 'Meta\'s open-source large model'
  },
  { 
    id: 'command-r', 
    name: 'Command R+', 
    icon: <IconSparkles size={16} />,
    color: 'from-pink-500 to-rose-600',
    description: 'Cohere\'s enterprise-grade model'
  },
  { 
    id: 'gpt3-5', 
    name: 'GPT-3.5 Turbo', 
    icon: <IconBrandOpenai size={16} />,
    color: 'from-teal-400 to-emerald-500',
    description: 'Fast responses, good balance'
  },
  { 
    id: 'claude-instant', 
    name: 'Claude Instant', 
    icon: <IconCircleFilled size={16} />, 
    color: 'from-violet-400 to-purple-500',
    description: 'Quick responses, lower cost'
  }
];

const ChatMain: React.FC<ChatMainProps> = ({ username }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [selectedModel, setSelectedModel] = useState<ModelProvider>(modelProviders[0]);
  const [activeFeatures, setActiveFeatures] = useState<{
    queryRefiner: boolean;
    deepResearch: boolean;
    podcastCreation: boolean;
    extendedResearch: boolean;
  }>({
    queryRefiner: false,
    deepResearch: false,
    podcastCreation: false,
    extendedResearch: false
  });
  const [isMobile, setIsMobile] = useState(false);
  const [researchMode, setResearchMode] = useState<ResearchMode>('idle');
  const [progress, setProgress] = useState(0);
  const [sourceCount, setSourceCount] = useState(0);
  const [currentStage, setCurrentStage] = useState('');
  const [researchActive, setResearchActive] = useState(false);
  const [researchStep, setResearchStep] = useState(0);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  
  const mainRef = useRef<HTMLDivElement>(null);
  const welcomeRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  
  // Check if at least one non-queryRefiner feature is selected
  const isFeatureSelected = 
    activeFeatures.deepResearch || 
    activeFeatures.podcastCreation || 
    activeFeatures.extendedResearch;
  
  // Simulate research progress
  useEffect(() => {
    if (researchMode === 'processing') {
      // Set initial source count
      setSourceCount(Math.floor(Math.random() * 30) + 25); // Random between 25-55
      
      // Simulate increasing progress
      const interval = setInterval(() => {
        setProgress(prev => {
          const newProgress = prev + (Math.random() * 2);
          
          // Update stage based on progress
          if (newProgress < 25) {
            setCurrentStage('Collecting sources');
          } else if (newProgress < 50) {
            setCurrentStage('Processing information');
          } else if (newProgress < 75) {
            setCurrentStage('Analyzing data');
          } else {
            setCurrentStage('Finalizing results');
          }
          
          if (newProgress >= 100) {
            clearInterval(interval);
            // Transition to chat mode when research is complete
            setTimeout(() => {
              handleResearchComplete();
            }, 500);
            return 100;
          }
          return newProgress;
        });
      }, 300);
      
      return () => clearInterval(interval);
    }
  }, [researchMode]);
  
  // Check if device is mobile based on screen width
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    
    // Initial check
    checkMobile();
    
    // Set up event listener for window resize
    window.addEventListener('resize', checkMobile);
    
    return () => {
      window.removeEventListener('resize', checkMobile);
    };
  }, []);
  
  useEffect(() => {
    // Entrance animations
    if (researchMode === 'idle') {
      anime({
        targets: welcomeRef.current,
        opacity: [0, 1],
        translateY: [20, 0],
        delay: 300,
        duration: 800,
        easing: 'easeOutQuad'
      });
      
      anime({
        targets: '.feature-button',
        opacity: [0, 1],
        translateY: [10, 0],
        delay: anime.stagger(100, {start: 600}),
        easing: 'easeOutQuad'
      });
    } else if (researchMode === 'chat') {
      // Animate chat interface entrance
      anime({
        targets: '.chat-container',
        opacity: [0, 1],
        translateY: [20, 0],
        duration: 500,
        easing: 'easeOutQuad'
      });
      
      // Focus input field
      if (inputRef.current) {
        inputRef.current.focus();
      }
    }
  }, [researchMode]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Only proceed if there's actually a query and a feature is selected
    if (!searchQuery.trim() || !isFeatureSelected) return;
    
    // Add user message
    addMessage('user', searchQuery);
    
    // Switch to research mode when a search is submitted
    setResearchMode('processing');
    setProgress(0); // Reset progress
    
    // Reset messages when starting new research
    if (messages.length > 0) {
      setMessages([{
        id: Date.now().toString(),
        role: 'user',
        content: searchQuery,
        createdAt: new Date(),
        updatedAt: new Date()
      }]);
    }
  };

  const handleVoiceInput = (transcript: string) => {
    // Handle voice input with transcript
    setSearchQuery(transcript);
  };

  const toggleFeature = (feature: FeatureType) => {
    // Special handling for queryRefiner - it can be combined with other features
    if (feature === 'queryRefiner') {
      setActiveFeatures({
        ...activeFeatures,
        queryRefiner: !activeFeatures.queryRefiner
      });
    } else {
      // For other features, deselect all other non-queryRefiner features first
      setActiveFeatures({
        ...activeFeatures,
        deepResearch: feature === 'deepResearch' ? !activeFeatures.deepResearch : false,
        podcastCreation: feature === 'podcastCreation' ? !activeFeatures.podcastCreation : false,
        extendedResearch: feature === 'extendedResearch' ? !activeFeatures.extendedResearch : false,
      });
    }
    
    // Animation for feature toggle
    anime({
      targets: `.${feature}-button`,
      scale: [1, 1.05, 1],
      duration: 400,
      easing: 'easeOutElastic(1, .6)'
    });
  };
  
  const createNewChat = () => {
    // Reset all states
    setSearchQuery('');
    setResearchMode('idle');
    setProgress(0);
    setActiveFeatures({
      queryRefiner: false,
      deepResearch: false,
      podcastCreation: false,
      extendedResearch: false
    });
    setMessages([]); // Clear messages
    
    // Animation for resetting
    anime({
      targets: mainRef.current,
      opacity: [0.5, 1],
      duration: 500,
      easing: 'easeOutQuad'
    });
  };

  // Add a message to the chat
  const addMessage = (role: 'user' | 'assistant', content: string) => {
    const newMessage: Message = {
      id: Date.now().toString(),
      role,
      content,
      createdAt: new Date(),
      updatedAt: new Date()
    };
    
    setMessages(prev => [...prev, newMessage]);
    
    // Scroll to the newest message
    setTimeout(scrollToBottom, 100);
    
    return newMessage;
  };
  
  // Handle chat input submission
  const handleChatSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!inputValue.trim()) return;
    
    // Add user message
    addMessage('user', inputValue);
    
    // Clear input field
    setInputValue('');
    
    // Simulate AI response
    setTimeout(() => {
      const assistantMessage = addMessage('assistant', generateResponse(inputValue));
      
      // Animate the new message
      anime({
        targets: `.message-${assistantMessage.id}`,
        opacity: [0, 1],
        translateY: [10, 0],
        duration: 500,
        easing: 'easeOutQuad'
      });
    }, 1000);
  };
  
  // Generate a simple response based on the input
  const generateResponse = (input: string): string => {
    const lowercaseInput = input.toLowerCase();
    
    if (lowercaseInput.includes('hello') || lowercaseInput.includes('hi')) {
      return `Hello! How can I assist you with your research on "${searchQuery}"?`;
    } else if (lowercaseInput.includes('thank')) {
      return 'You\'re welcome! Is there anything else you\'d like to know about this topic?';
    } else if (lowercaseInput.includes('help')) {
      return 'I\'m here to help with your research. You can ask specific questions about the sources I found, request summaries, or ask for connections between different pieces of information.';
    } else if (lowercaseInput.includes('?')) {
      return `Based on my research about "${searchQuery}", I found that the most relevant information suggests: [detailed explanation would appear here based on actual research implementation]`;
    } else {
      return `I've analyzed your query about "${searchQuery}" and found several interesting perspectives. Would you like me to elaborate on any particular aspect?`;
    }
  };
  
  // Handle research completion
  const handleResearchComplete = () => {
    setResearchMode('chat');
    
    // Delay slightly for better UX
    setTimeout(() => {
      // Create a summary of active features
      const activeFeaturesList: string[] = [];
      if (activeFeatures.queryRefiner) activeFeaturesList.push('query refinement');
      if (activeFeatures.deepResearch) activeFeaturesList.push('deep research');
      if (activeFeatures.podcastCreation) activeFeaturesList.push('podcast creation');
      if (activeFeatures.extendedResearch) activeFeaturesList.push('extended sources');
      
      const featuresUsed = activeFeaturesList.length > 0 
        ? activeFeaturesList.join(', ') 
        : 'standard research';
        
      // Add completion message to chat
      const completionMessage = addMessage(
        'assistant',
        `I've completed my research on "${searchQuery}" using ${featuresUsed}. I found ${sourceCount} relevant sources. What specific aspects would you like to know more about?`
      );
      
      // Animate the message
      anime({
        targets: `.message-${completionMessage.id}`,
        opacity: [0, 1],
        translateY: [10, 0],
        duration: 500,
        easing: 'easeOutQuad'
      });
      
      // Focus the input field
      if (inputRef.current) {
        inputRef.current.focus();
      }
    }, 800);
  };
  
  // Scroll to bottom of chat container
  const scrollToBottom = () => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  };

  return (
    <div className="flex flex-col h-full bg-gradient-to-br from-gray-900 to-gray-950" ref={mainRef}>
      {/* Header with model selection */}
      <header className="flex flex-col md:flex-row justify-between md:items-center p-4 border-b border-gray-800/40 backdrop-blur-md bg-gray-900/70 z-[9999]">
        <div className="flex items-center">
          <div className="w-2 h-6 bg-gradient-to-b from-indigo-500 to-purple-600 rounded-full mr-3"></div>
          <h1 className="text-xl font-semibold text-white">
            {researchMode === 'processing' ? 'Research Query' : researchMode === 'chat' ? 'Chat Results' : 'AI Assistant'}
          </h1>
        </div>
        
        {/* Model dropdown - only show in idle mode */}
        {researchMode === 'idle' && (
          <ModelSelector 
            selectedModel={selectedModel}
            setSelectedModel={setSelectedModel}
            isDropdownOpen={isDropdownOpen}
            setIsDropdownOpen={setIsDropdownOpen}
            isMobile={isMobile}
          />
        )}
        
        {/* Status indicators for research mode */}
        {(researchMode === 'processing' || researchMode === 'chat') && (
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              {researchMode === 'processing' && (
                <>
                  <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></div>
                  <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" style={{ animationDelay: '0.5s' }}></div>
                </>
              )}
              {researchMode === 'chat' && (
                <div className="w-2 h-2 rounded-full bg-green-500"></div>
              )}
            </div>
            <button 
              onClick={createNewChat}
              className="px-3 py-1.5 rounded-md bg-gray-800 hover:bg-gray-700 text-gray-300 hover:text-white text-sm flex items-center gap-1.5 transition-all duration-200 border border-gray-700/30"
            >
              <IconX size={14} />
              <span>New Chat</span>
            </button>
          </div>
        )}
      </header>

      {/* Main chat area - Only show in idle mode */}
      {researchMode === 'idle' && (
        <WelcomeScreen 
          username={username} 
          welcomeRef={welcomeRef} 
        />
      )}
      
      {/* Research processing interface - Only shown in processing mode */}
      {researchMode === 'processing' && (
        <ResearchInterface
          searchQuery={searchQuery}
          sourceCount={sourceCount}
          progress={progress}
          currentStage={currentStage}
          onNewChat={createNewChat}
          onComplete={handleResearchComplete}
        />
      )}
      
      {/* Chat interface - Only shown in chat mode */}
      {researchMode === 'chat' && (
        <div className="flex-1 flex flex-col p-4 overflow-hidden chat-container">
          {/* Messages container */}
          <div 
            className="flex-1 overflow-y-auto mb-4 rounded-lg p-4 bg-gray-800/20 border border-gray-700/30"
            ref={chatContainerRef}
          >
            {messages.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-gray-500 flex items-center gap-2">
                  <IconMessage size={20} />
                  <span>Start chatting about your research</span>
                </div>
              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={`message-${message.id} flex ${
                    message.role === 'user' ? 'justify-end' : 'justify-start'
                  } mb-4`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg px-4 py-3 ${
                      message.role === 'user'
                        ? 'bg-indigo-600 text-white rounded-tr-none shadow-lg shadow-indigo-600/10'
                        : 'bg-gray-800/80 text-gray-200 rounded-tl-none border border-gray-700/30'
                    }`}
                  >
                    {message.content}
                  </div>
                </div>
              ))
            )}
          </div>
          
          {/* Chat input */}
          <form onSubmit={handleChatSubmit} className="relative">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ask about your research..."
              className="w-full py-3 px-4 pr-12 rounded-lg bg-gray-800/50 border border-gray-700/50 focus:border-indigo-500/30 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 text-white"
            />
            <button
              type="submit"
              disabled={!inputValue.trim()}
              className={`absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-lg transition-all duration-200 ${
                inputValue.trim()
                  ? 'bg-indigo-600 hover:bg-indigo-700 text-white'
                  : 'bg-gray-700 text-gray-400 cursor-not-allowed'
              }`}
            >
              <IconSend size={18} />
            </button>
          </form>
        </div>
      )}

      {/* Search bar and controls - Only show in idle mode */}
      {researchMode === 'idle' && (
        <div className="p-4 border-t border-gray-800/40 backdrop-blur-md bg-gray-900/70">
          <div className="relative max-w-4xl mx-auto">
            <SearchBar 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onSubmit={handleSearch}
              onVoiceInput={handleVoiceInput}
              isDisabled={!isFeatureSelected}
              isPulsing={searchQuery.trim().length > 0 && !isFeatureSelected}
            />
            
            {/* Instructions if text is entered but no feature selected */}
            {searchQuery.trim().length > 0 && !isFeatureSelected && (
              <div className="mt-2 text-amber-400 text-sm flex items-center gap-1.5 animate-pulse px-2">
                <IconMoodHappy size={16} />
                <span>Select at least one research type below to enable search</span>
              </div>
            )}
            
            {/* Action buttons beneath search bar */}
            <ActionButtonGroup 
              activeFeatures={activeFeatures}
              toggleFeature={toggleFeature}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatMain; 