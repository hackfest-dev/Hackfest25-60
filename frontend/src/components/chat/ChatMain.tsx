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
  IconMessage,
  IconDownload
} from '@tabler/icons-react';
import SearchBar from './SearchBar';
import anime from 'animejs';
import ModelSelector from './ModelSelector';
import WelcomeScreen from './WelcomeScreen';
import ActionButtonGroup from './ActionButtonGroup';
import chatAPI, { Message as ApiMessage, ChatWithMessages } from '../../services/chatApi';
import ReactMarkdown from 'react-markdown';
import { jsPDF } from 'jspdf';
import 'jspdf-autotable';
import ResearchInterface from './ResearchInterface';
import * as Showdown from 'showdown';
import html2canvas from 'html2canvas';

interface ChatMainProps {
  username: string;
  chatId?: number | null;
}

// Convert API Message to local Message interface
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

export type ResearchMode = 'idle' | 'processing' | 'results' | 'chat';

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

const ChatMain: React.FC<ChatMainProps> = ({ 
  username,
  chatId
}) => {
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
  const [currentChatId, setCurrentChatId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  
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

  // Add these states and refs for caching and optimization
  const [cachedChats, setCachedChats] = useState<Record<number, Message[]>>({});
  const [isFirstLoad, setIsFirstLoad] = useState(true);
  const isInitialLoadComplete = useRef(false);
  const [assistantResponse, setAssistantResponse] = useState<Message | null>(null);

  // Modify the loadChat function to use cached data when available
  const loadChat = async (chatId: number) => {
    try {
      setIsLoading(true);
      
      // Check if we already have the chat messages cached
      if (cachedChats[chatId]) {
        setCurrentChatId(chatId);
        setMessages(cachedChats[chatId]);
        setResearchMode(cachedChats[chatId].length > 0 ? 'chat' : 'idle');
        setIsLoading(false);
        return;
      }
      
      const chat = await chatAPI.getChat(chatId);
      
      // Convert API messages to local format
      const formattedMessages = chat.messages.map(convertApiMessage);
      
      // Cache the messages
      setCachedChats(prev => ({
        ...prev,
        [chatId]: formattedMessages
      }));
      
      setCurrentChatId(chat.id);
      setMessages(formattedMessages);
      
      // If chat has a title, update UI
      if (chat.title) {
        // Update title in UI if needed
      }
      
      // Set the research mode to 'chat' if there are messages
      if (formattedMessages.length > 0) {
        setResearchMode('chat');
      } else {
        setResearchMode('idle');
      }
    } catch (error) {
      console.error('Failed to load chat:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Add a useEffect to keep the chatId in sync
  useEffect(() => {
    if (chatId && chatId !== currentChatId) {
      console.log('chatId prop changed, loading new chat:', chatId);
      setCurrentChatId(chatId);
      loadChat(chatId);
    }
  }, [chatId]);

  // Watch for changes in currentChatId (when we create a new chat internally)
  useEffect(() => {
    if (currentChatId && (!chatId || currentChatId !== chatId)) {
      console.log('currentChatId changed internally:', currentChatId);
      // If this is not the initial load, reload the chat to make sure we have fresh data
      if (isInitialLoadComplete.current) {
        loadChat(currentChatId);
      }
    }
  }, [currentChatId]);

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
  
  // Create a new chat
  const createNewChat = async () => {
    try {
      // Show loading state
      setIsLoading(true);
      
      // Create a new chat in the backend
      const newChat = await chatAPI.createChat({ title: "New Chat" });
      
      // Clear existing messages and reset states
      setMessages([]);
      setInputValue('');
      setResearchMode('idle');
      setResearchActive(false);
      setSourceCount(0);
      setProgress(0);
      setCurrentStage('');
      setAssistantResponse(null);
      
      // Update cached chats
      setCachedChats(prev => ({
        ...prev,
        [newChat.id]: []
      }));
      
      // Set the new chat ID
      setCurrentChatId(newChat.id);
      
      // Reset features
      setActiveFeatures({
        queryRefiner: false,
        deepResearch: false,
        podcastCreation: false,
        extendedResearch: false
      });
      
      // Animate the transition
      if (mainRef.current) {
        anime({
          targets: mainRef.current,
          opacity: [0.7, 1],
          translateY: [5, 0],
          duration: 300,
          easing: 'easeOutQuad'
        });
      }
      
      // Animate welcome screen if transitioning to idle mode
      setTimeout(() => {
        if (welcomeRef.current && researchMode === 'idle') {
          anime({
            targets: welcomeRef.current,
            opacity: [0, 1],
            translateY: [20, 0],
            duration: 500,
            easing: 'easeOutQuad'
          });
        }
      }, 100);
      
      // Force re-render by updating a state
      setIsFirstLoad(false);
      
      console.log('New chat created successfully:', newChat);
    } catch (error) {
      console.error('Failed to create new chat:', error);
      // Show error notification or toast here if you have a notification system
    } finally {
      // Hide loading after a slight delay for better UX
      setTimeout(() => {
        setIsLoading(false);
      }, 300);
    }
  };
  
  // Convert API message to local message format
  const convertApiMessage = (apiMessage: ApiMessage): Message => {
    return {
      id: apiMessage.id.toString(),
      role: apiMessage.role as 'user' | 'assistant',
      content: apiMessage.content,
      createdAt: new Date(apiMessage.created_at),
      updatedAt: new Date(apiMessage.created_at)
    };
  };
  
  // Add a message to the current chat
  const addMessage = async (role: 'user' | 'assistant', content: string) => {
    if (!content.trim()) return null;
    
    // Set loading state
    setIsLoading(true);
    
    try {
      // If no current chat, create one
      if (!currentChatId) {
        console.log('No current chat, creating a new one');
        const newChat = await chatAPI.createChat();
        console.log('New chat created:', newChat.id);
        setCurrentChatId(newChat.id);
        
        // Now we can proceed with adding the message
        const result = await addMessageToChat(newChat.id, role, content);
        setIsLoading(false);
        return result;
      } else {
        // Add to existing chat
        console.log('Adding message to existing chat:', currentChatId);
        const result = await addMessageToChat(currentChatId, role, content);
        setIsLoading(false);
        return result;
      }
    } catch (error) {
      console.error('Failed in addMessage:', error);
      setIsLoading(false);
      return null;
    }
  };
  
  // Helper function to add a message to a specific chat
  const addMessageToChat = async (chatId: number, role: 'user' | 'assistant', content: string) => {
    try {
      // Create temporary local message for immediate UI feedback
      const tempMessage: Message = {
        id: `temp-${Date.now()}`,
        role,
        content,
        createdAt: new Date(),
        updatedAt: new Date()
      };
      
      // Update UI immediately with the user message
      setMessages(prev => [...prev, tempMessage]);
      
      // Update cached messages
      setCachedChats(prev => {
        const prevMessages = prev[chatId] || [];
        return {
          ...prev,
          [chatId]: [...prevMessages, tempMessage]
        };
      });
      
      // Switch to chat mode if not already in chat or results mode
      if (researchMode !== 'chat' && researchMode !== 'results') {
        setResearchMode('chat');
      }
      
      // Scroll to bottom
      scrollToBottom();
      
      // Send to API
      const response = await chatAPI.addMessage(chatId, {
        role,
        content
      });
      
      // Remove the temporary message
      setMessages(prev => prev.filter(msg => msg.id !== tempMessage.id));
      
      // Add all returned messages (both user message and AI response)
      const apiMessages = response.map(convertApiMessage);
      setMessages(prev => [...prev, ...apiMessages]);
      
      // Store the assistant response for displaying in research interface
      const assistantMsg = apiMessages.find(msg => msg.role === 'assistant');
      if (assistantMsg) {
        setAssistantResponse(assistantMsg);
      }
      
      // Update cached messages
      setCachedChats(prev => {
        const filteredMessages = (prev[chatId] || []).filter(msg => msg.id !== tempMessage.id);
        return {
          ...prev,
          [chatId]: [...filteredMessages, ...apiMessages]
        };
      });
      
      // Scroll to bottom again after adding AI response
      setTimeout(scrollToBottom, 100);
      
      // Return the first message (user message) for compatibility
      return apiMessages[0];
    } catch (error) {
      console.error('Failed to add message:', error);
      // Remove temp message on error
      setMessages(prev => prev.filter(msg => !msg.id.startsWith('temp-')));
      setCachedChats(prev => {
        const filteredMessages = (prev[chatId] || []).filter(msg => !msg.id.startsWith('temp-'));
        return {
          ...prev,
          [chatId]: filteredMessages
        };
      });
      return null;
    }
  };
  
  // Handle chat submission
  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!inputValue.trim()) return;
    
    // Save the input value and clear the input field
    const message = inputValue;
    setInputValue('');
    
    // Add user message
    await addMessage('user', message);
    
    // No need to generate response here - the backend now handles this
  };
  
  // Handle research completion
  const handleResearchComplete = () => {
    // Change to results mode
    setResearchMode('results');
    
    // Add the user's query as a message if not already present
    if (messages.length === 0) {
      // Delay slightly for better UX
      setTimeout(() => {
        addMessage('user', searchQuery).then(() => {
          // The backend will automatically add an assistant response
          // We'll display this in the research interface
        });
      }, 500);
    } else {
      // Find the most recent assistant message to display
      const assistantMsg = messages.find(msg => msg.role === 'assistant');
      if (assistantMsg) {
        setAssistantResponse(assistantMsg);
      }
    }
  };
  
  // Add function to start chat mode
  const startChatMode = () => {
    setResearchMode('chat');
    
    // Add a transitional message
    setTimeout(() => {
      const message = addMessage(
        'assistant',
        'What would you like to know more about? You can ask specific questions about the research findings.'
      );
      
      // Focus the input field
      if (inputRef.current) {
        inputRef.current.focus();
      }
    }, 300);
  };
  
  // Scroll to bottom of chat container
  const scrollToBottom = () => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  };

  // Initialize component - check for existing chats
  useEffect(() => {
    const initializeChat = async () => {
      // If we already loaded messages, don't load again
      if (isInitialLoadComplete.current) {
        return;
      }
      
      try {
        setIsLoading(true);
        
        // Get list of chats
        const chats = await chatAPI.getChats();
        
        // If there are chats, load the most recent one
        if (chats.length > 0) {
          console.log('Loading existing chat:', chats[0].id);
          await loadChat(chats[0].id);
          isInitialLoadComplete.current = true;
        } else {
          // Otherwise prepare for a new chat
          console.log('No existing chats, starting in idle mode');
          setResearchMode('idle');
          // Optionally create a new chat automatically
          // await createNewChat();
        }
      } catch (error) {
        console.error('Failed to initialize chat:', error);
        setResearchMode('idle');
      } finally {
        setIsLoading(false);
        setIsFirstLoad(false);
      }
    };
    
    // Only run initialization if no chatId is provided from props
    if (!chatId) {
      initializeChat();
    } else if (!isInitialLoadComplete.current) {
      console.log('Loading chat from props:', chatId);
      loadChat(chatId);
      isInitialLoadComplete.current = true;
    }
  }, []);

  // Function to download only the markdown response as PDF
  const downloadMarkdownAsPDF = (markdownContent: string) => {
    // Create a temporary div to render the HTML
    const tempDiv = document.createElement('div');
    tempDiv.style.padding = '20px';
    tempDiv.style.position = 'absolute';
    tempDiv.style.top = '-9999px';
    tempDiv.style.left = '-9999px';
    tempDiv.style.width = '800px'; // Fixed width for better layout control
    
    // Apply some basic styles for the PDF
    tempDiv.style.fontFamily = 'Arial, Helvetica, sans-serif';
    tempDiv.style.fontSize = '12px';
    tempDiv.style.lineHeight = '1.6';
    tempDiv.style.color = '#333';
    
    // Add styling for markdown elements
    const styleElement = document.createElement('style');
    styleElement.textContent = `
      h1 { font-size: 24px; margin-top: 20px; margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 5px; }
      h2 { font-size: 20px; margin-top: 18px; margin-bottom: 8px; }
      h3 { font-size: 16px; margin-top: 16px; margin-bottom: 8px; }
      p { margin-bottom: 10px; }
      code { background-color: #f5f5f5; padding: 2px 4px; border-radius: 3px; font-family: monospace; }
      pre { background-color: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; margin-bottom: 15px; }
      blockquote { border-left: 4px solid #ddd; padding-left: 15px; margin-left: 0; color: #666; }
      ul, ol { margin-bottom: 15px; margin-left: 20px; }
      li { margin-bottom: 5px; }
      table { border-collapse: collapse; width: 100%; margin-bottom: 15px; }
      th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
      th { background-color: #f5f5f5; }
      hr { border: 0; height: 1px; background-color: #ddd; margin: 20px 0; }
      img { max-width: 100%; height: auto; }
    `;
    document.head.appendChild(styleElement);
    
    // Convert markdown to HTML
    const converter = new Showdown.Converter({
      tables: true, 
      simplifiedAutoLink: true,
      strikethrough: true,
      tasklists: true,
      smartIndentationFix: true,
      openLinksInNewWindow: true,
      emoji: true
    });
    
    // Add a title
    const htmlContent = `
      <h1 style="color: #4338ca; margin-bottom: 20px;">Research Results</h1>
      ${converter.makeHtml(markdownContent)}
    `;
    
    tempDiv.innerHTML = htmlContent;
    document.body.appendChild(tempDiv);
    
    // Use html2canvas to convert the HTML to an image
    html2canvas(tempDiv, {
      scale: 2, // Higher scale for better quality
      useCORS: true,
      logging: false,
      allowTaint: true
    }).then(canvas => {
      // Clean up
      document.body.removeChild(tempDiv);
      document.head.removeChild(styleElement);
      
      // Create PDF with proper dimensions
      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF({
        orientation: 'portrait',
        unit: 'mm',
      });
      
      // Calculate dimensions
      const imgWidth = 210; // A4 width in mm (portrait)
      const pageHeight = 297; // A4 height in mm
      const imgHeight = (canvas.height * imgWidth) / canvas.width;
      
      let heightLeft = imgHeight;
      let position = 0;
      
      // Add image to first page
      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
      heightLeft -= pageHeight;
      
      // Add additional pages if needed
      while (heightLeft > 0) {
        position = heightLeft - imgHeight;
        pdf.addPage();
        pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
        heightLeft -= pageHeight;
      }
      
      // Save the PDF
      pdf.save('research-response.pdf');
    });
  };

  return (
    <div className="flex flex-col h-full bg-gradient-to-br from-gray-900 to-gray-950" ref={mainRef}>
      {/* Loading Overlay */}
      {isLoading && (
        <div className="absolute inset-0 bg-gray-900/70 backdrop-blur-sm z-[10000] flex items-center justify-center">
          <div className="flex flex-col items-center">
            <div className="w-12 h-12 rounded-full border-4 border-indigo-500 border-t-transparent animate-spin mb-4"></div>
            <p className="text-white font-medium">Creating new chat...</p>
          </div>
        </div>
      )}
      
      {/* Header with model selection */}
      <header className="flex flex-col md:flex-row justify-between md:items-center p-4 border-b border-gray-800/40 backdrop-blur-md bg-gray-900/70 z-[9999]">
        <div className="flex items-center">
          <div className="w-2 h-6 bg-gradient-to-b from-indigo-500 to-purple-600 rounded-full mr-3"></div>
          <h1 className="text-xl font-semibold text-white">
            {researchMode === 'processing' ? 'Research Query' : 
             researchMode === 'results' ? 'Research Results' : 
             researchMode === 'chat' ? 'Chat Results' : 'AI Assistant'}
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
        {(researchMode === 'processing' || researchMode === 'results' || researchMode === 'chat') && (
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              {researchMode === 'processing' && (
                <>
                  <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></div>
                  <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" style={{ animationDelay: '0.5s' }}></div>
                </>
              )}
              {(researchMode === 'results' || researchMode === 'chat') && (
                <div className="w-2 h-2 rounded-full bg-green-500"></div>
              )}
            </div>
            <button 
              onClick={createNewChat}
              disabled={isLoading}
              className="px-3 py-2 rounded-md bg-indigo-600 hover:bg-indigo-700 text-white text-sm flex items-center gap-1.5 transition-all duration-200 shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <IconX size={14} className="text-gray-100" />
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
      
      {/* Research results - Only shown in results mode with response below research interface */}
      {researchMode === 'results' && (
        <div className="flex-1 flex flex-col p-4 overflow-hidden">
          <ResearchInterface
            searchQuery={searchQuery}
            sourceCount={sourceCount}
            progress={100}  
            currentStage="Research Complete"
            onNewChat={createNewChat}
            onComplete={handleResearchComplete}
          />

          {/* Markdown Response Section */}
          {assistantResponse && (
            <div className="mt-6">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold text-white">Research Results</h3>
                <button 
                  onClick={() => downloadMarkdownAsPDF(assistantResponse.content)}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors flex items-center gap-2"
                >
                  <IconDownload size={16} />
                  <span>Download PDF</span>
                </button>
              </div>
              <div className="p-4 rounded-lg bg-gray-800/30 border border-gray-700/50">
                <ReactMarkdown>
                  {assistantResponse.content}
                </ReactMarkdown>
              </div>
            </div>
          )}
        </div>
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
                    {message.role === 'assistant' ? (
                      <ReactMarkdown>
                        {message.content}
                      </ReactMarkdown>
                    ) : (
                      message.content
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
          
          {/* Add download button in chat mode too */}
          {messages.length > 0 && (
            <div className="mt-2 mb-4 flex justify-end">
              <button 
                onClick={() => {
                  // Find the latest assistant message
                  const latestAssistantMessage = [...messages]
                    .reverse()
                    .find(msg => msg.role === 'assistant');
                  
                  if (latestAssistantMessage) {
                    downloadMarkdownAsPDF(latestAssistantMessage.content);
                  }
                }}
                className="px-3 py-1.5 bg-gray-800 text-gray-300 rounded-lg hover:bg-gray-700 transition-colors text-sm flex items-center gap-1.5 border border-gray-700/30"
              >
                <IconDownload size={14} />
                <span>Download Response</span>
              </button>
            </div>
          )}
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