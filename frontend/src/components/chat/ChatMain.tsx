import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { 
  IconBrandOpenai,
  IconCircleFilled,
  IconRobot,
  IconBrandGoogle,
  IconFlame,
  IconSparkles,
  IconX,
  IconMoodHappy,
  IconSend,
  IconMessage,
  IconDownload
} from '@tabler/icons-react';
import SearchBar from './SearchBar';
import ModelSelector from './ModelSelector';
import WelcomeScreen from './WelcomeScreen';
import ActionButtonGroup from './ActionButtonGroup';
import chatAPI, { Message as ApiMessage } from '../../services/chatApi';
import ReactMarkdown from 'react-markdown';
import { jsPDF } from 'jspdf';
import 'jspdf-autotable';
import ResearchInterface from './ResearchInterface';
import * as Showdown from 'showdown';
import html2canvas from 'html2canvas';
import { useTransition } from 'react';
// @ts-ignore
import remarkGfm from 'remark-gfm';
// @ts-ignore
import html2pdf from 'html2pdf.js';

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

export type FeatureType = 'queryRefiner' | 'deepResearch';

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
  }>({
    queryRefiner: false,
    deepResearch: false,
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
  
  // Replace the isFeatureSelected check with a simpler version - just always enable search
  const isFeatureSelected = true;
  
  const [isPending, startTransition] = useTransition();
  const requestCache = useRef<Record<string, any>>({});
  
  // Memoize expensive data structures
  const modelProvidersMap = useMemo(() => 
    Object.fromEntries(modelProviders.map(m => [m.id, m])), 
    []
  );
  
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
      if (welcomeRef.current) {
        welcomeRef.current.style.opacity = '0';
        welcomeRef.current.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
          if (welcomeRef.current) {
            welcomeRef.current.style.opacity = '1';
            welcomeRef.current.style.transform = 'translateY(0)';
            welcomeRef.current.style.transition = 'opacity 800ms ease, transform 800ms ease';
          }
        }, 300);
      }
      
      document.querySelectorAll('.feature-button').forEach((el, i) => {
        const element = el as HTMLElement;
        element.style.opacity = '0';
        element.style.transform = 'translateY(10px)';
        
        setTimeout(() => {
          element.style.opacity = '1';
          element.style.transform = 'translateY(0)';
          element.style.transition = 'opacity 500ms ease, transform 500ms ease';
        }, 600 + (i * 100));
      });
    } else if (researchMode === 'chat') {
      // Animate chat interface entrance
      const chatContainer = document.querySelector('.chat-container') as HTMLElement;
      if (chatContainer) {
        chatContainer.style.opacity = '0';
        chatContainer.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
          chatContainer.style.opacity = '1';
          chatContainer.style.transform = 'translateY(0)';
          chatContainer.style.transition = 'opacity 500ms ease, transform 500ms ease';
        }, 10);
      }
      
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

  // Add a ref to store active polling intervals
  const activePollingIntervals = useRef<number[]>([]);

  // Memoized scroll function for better performance
  const scrollToBottom = useCallback(() => {
    if (chatContainerRef.current) {
      const { scrollHeight, clientHeight } = chatContainerRef.current;
      chatContainerRef.current.scrollTop = scrollHeight - clientHeight;
    }
  }, []);

  // Optimize loadChat function with caching and batched updates
  const loadChat = useCallback(async (chatId: number) => {
    try {
      setIsLoading(true);
      
      // Use cached data if available
      if (cachedChats[chatId]) {
        startTransition(() => {
          setCurrentChatId(chatId);
          setMessages(cachedChats[chatId]);
          setResearchMode(cachedChats[chatId].length > 0 ? 'chat' : 'idle');
        });
        setIsLoading(false);
        return;
      }
      
      // Check request cache to avoid duplicate requests
      const cacheKey = `chat-${chatId}`;
      if (requestCache.current[cacheKey]) {
        return requestCache.current[cacheKey];
      }
      
      // Create a promise for this request
      const requestPromise = chatAPI.getChat(chatId).then(chat => {
        // Convert API messages to local format
        const formattedMessages = chat.messages.map(convertApiMessage);
        
        // Update state in a single batched update
        startTransition(() => {
          setCachedChats(prev => ({
            ...prev,
            [chatId]: formattedMessages
          }));
          
          setCurrentChatId(chat.id);
          setMessages(formattedMessages);
          
          // Set the research mode based on messages
          setResearchMode(formattedMessages.length > 0 ? 'chat' : 'idle');
        });
        
        // Clear from request cache
        delete requestCache.current[cacheKey];
        return formattedMessages;
      });
      
      // Store the promise in cache
      requestCache.current[cacheKey] = requestPromise;
      
      await requestPromise;
    } catch (error) {
      console.error('Failed to load chat:', error);
    } finally {
      setIsLoading(false);
    }
  }, [cachedChats, setCurrentChatId, setMessages, setResearchMode]);

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
    // Special handling for all feature types - each can be toggled on/off individually
    if (feature === 'queryRefiner') {
      setActiveFeatures(prev => ({
        ...prev,
        queryRefiner: !prev.queryRefiner
      }));
    } else if (feature === 'deepResearch') {
      setActiveFeatures(prev => ({
        ...prev,
        deepResearch: !prev.deepResearch
      }));
    }
    
    // Animation for feature toggle button using CSS
    const featureButton = document.querySelector(`.${feature}-button`) as HTMLElement;
    if (featureButton) {
      featureButton.style.transform = 'scale(1.05)';
      setTimeout(() => {
        featureButton.style.transform = 'scale(1)';
        featureButton.style.transition = 'transform 400ms ease';
      }, 200);
    }
  };
  
  // Optimize createNewChat to be more efficient
  const createNewChat = useCallback(async () => {
    try {
      setIsLoading(true);
      
      // Create a new chat in the backend
      const newChat = await chatAPI.createChat({ title: "New Chat" });
      
      // Batch state updates
      startTransition(() => {
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
        });
      });
      
      // Animate the transition with CSS instead of anime.js
      if (mainRef.current) {
        mainRef.current.style.opacity = '0.7';
        
        setTimeout(() => {
          if (mainRef.current) {
            mainRef.current.style.opacity = '1';
            mainRef.current.style.transform = 'translateY(0)';
            mainRef.current.style.transition = 'opacity 300ms ease, transform 300ms ease';
          }
        }, 10);
      }
      
      // Force re-render by updating a state
      setIsFirstLoad(false);
      
      console.log('New chat created successfully:', newChat);
    } catch (error) {
      console.error('Failed to create new chat:', error);
    } finally {
      setTimeout(() => {
        setIsLoading(false);
      }, 300);
    }
  }, []);
  
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
  
  // Optimize addMessage function with better handling
  const addMessage = useCallback(async (role: 'user' | 'assistant', content: string) => {
    if (!content.trim()) return null;
    
    // Set loading state
    setIsLoading(true);
    
    try {
      // If no current chat, create one
      if (!currentChatId) {
        console.log('No current chat, creating a new one');
        
        // Check if we have a pending request for chat creation
        const cacheKey = 'create-chat';
        if (!requestCache.current[cacheKey]) {
          requestCache.current[cacheKey] = chatAPI.createChat();
        }
        
        const newChat = await requestCache.current[cacheKey];
        delete requestCache.current[cacheKey];
        
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
  }, [currentChatId]);
  
  // Optimize addMessageToChat with better state updates
  const addMessageToChat = useCallback(async (chatId: number, role: 'user' | 'assistant', content: string) => {
    try {
      // Create temporary local message for immediate UI feedback
      const tempMessage: Message = {
        id: `temp-${Date.now()}`,
        role,
        content,
        createdAt: new Date(),
        updatedAt: new Date()
      };
      
      // Update UI immediately with the user message (optimistic update)
      startTransition(() => {
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
      });
      
      // Scroll to bottom
      scrollToBottom();
      
      // Check request cache to avoid duplicate requests
      const cacheKey = `add-message-${chatId}-${Date.now()}`;
      if (!requestCache.current[cacheKey]) {
        requestCache.current[cacheKey] = chatAPI.addMessage(chatId, {
          role,
          content
        });
      }
      
      // Send to API
      const response = await requestCache.current[cacheKey];
      delete requestCache.current[cacheKey];
      
      // Convert API messages to local format
      const apiMessages = response.map(convertApiMessage);
      
      // Process response in a single batch update
      startTransition(() => {
        // Remove the temporary message
        setMessages(prev => prev.filter(msg => msg.id !== tempMessage.id));
        
        // Add all returned messages (both user message and AI response)
        setMessages(prev => [...prev, ...apiMessages]);
        
        // Store the assistant response for displaying in research interface
        const assistantMsg = apiMessages.find((msg: Message) => msg.role === 'assistant');
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
      });
      
      // Start polling for any placeholder messages
      const placeholderMessages = response.filter(
        (msg: ApiMessage) => msg.role === 'assistant' && isPlaceholderMessage(msg.content)
      );
      
      placeholderMessages.forEach((msg: ApiMessage) => {
        console.log('Found placeholder message, starting polling:', msg.id);
        pollForMessageUpdates(chatId, msg.id.toString());
      });
      
      // Scroll to bottom again after adding AI response
      setTimeout(scrollToBottom, 100);
      
      // Return the first message (user message) for compatibility
      return apiMessages[0];
    } catch (error) {
      console.error('Failed to add message:', error);
      // Remove temp message on error
      startTransition(() => {
        setMessages(prev => prev.filter(msg => !msg.id.startsWith('temp-')));
        setCachedChats(prev => {
          const filteredMessages = (prev[chatId] || []).filter(msg => !msg.id.startsWith('temp-'));
          return {
            ...prev,
            [chatId]: filteredMessages
          };
        });
      });
      return null;
    }
  }, [researchMode, scrollToBottom]);
  
  // Handle chat submission
  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!inputValue.trim()) return;
    
    // Save the input value and clear the input field
    const message = inputValue;
    setInputValue('');
    
    // Add user message
    await addMessage('user', message);

  };
  
  // Handle research completion optimization
  const handleResearchComplete = useCallback(() => {
    // Change to results mode
    setResearchMode('results');
    
    // Add the user's query as a message if not already present
    if (messages.length === 0) {
      // Delay slightly for better UX
      setTimeout(() => {
        addMessage('user', searchQuery).then(() => {
          // The backend will automatically add an assistant response
        });
      }, 300);
    } else {
      // Find the most recent assistant message to display
      const assistantMsg = messages.find(msg => msg.role === 'assistant');
      if (assistantMsg) {
        setAssistantResponse(assistantMsg);
      }
    }
  }, [messages, searchQuery, addMessage]);
  
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
  
  // Optimized initialization
  useEffect(() => {
    const initializeChat = async () => {
      // If we already loaded messages, don't load again
      if (isInitialLoadComplete.current) {
        return;
      }
      
      try {
        setIsLoading(true);
        
        // Get list of chats with fast timeouts
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);
        
        try {
          const chats = await chatAPI.getChats();
          clearTimeout(timeoutId);
          
          // If there are chats, load the most recent one
          if (chats.length > 0) {
            console.log('Loading existing chat:', chats[0].id);
            await loadChat(chats[0].id);
            isInitialLoadComplete.current = true;
          } else {
            // Otherwise prepare for a new chat
            console.log('No existing chats, starting in idle mode');
            setResearchMode('idle');
          }
        } catch (error: unknown) {
          if (error instanceof Error && error.name === 'AbortError') {
            console.log('Chat loading timed out, starting in idle mode');
            setResearchMode('idle');
          } else {
            throw error;
          }
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
  }, [chatId, loadChat]);

  // Function to download only the markdown response as PDF
  const downloadMarkdownAsPDF = (markdownContent: string) => {
    try {
      console.log("Starting PDF generation using html2pdf.js");
      
      // Create a temporary container for the PDF content
      const tempDiv = document.createElement('div');
      tempDiv.id = 'preview';
      
      // Apply base styles for single-column layout
      tempDiv.style.fontFamily = 'Times, "Times New Roman", serif';
      tempDiv.style.fontSize = '10pt';
      tempDiv.style.lineHeight = '1.2';
      tempDiv.style.width = 'auto';
      tempDiv.style.boxSizing = 'border-box';
      
      // Create markdown renderer
      const converter = new Showdown.Converter({
        tables: true,
        simplifiedAutoLink: true,
        strikethrough: true,
        tasklists: true
      });
      
      // Convert markdown to HTML
      tempDiv.innerHTML = converter.makeHtml(markdownContent);
      
      // Process title section
      const titleSection = document.createElement('div');
      titleSection.className = 'title-section';
      
      // Extract title (h1) if present
      const h1 = tempDiv.querySelector('h1');
      if (h1) {
        titleSection.appendChild(h1);
        
        // Check for author paragraph (first p after h1)
        let sibling = h1.nextSibling;
        if (sibling && (sibling as HTMLElement).tagName === 'P') {
          const authorsP = document.createElement('p');
          authorsP.className = 'authors';
          authorsP.innerHTML = (sibling as HTMLElement).innerHTML;
          titleSection.appendChild(authorsP);
          tempDiv.removeChild(sibling);
          sibling = h1.nextSibling;
        }
        
        // Check for affiliation paragraph (second p after h1)
        if (sibling && (sibling as HTMLElement).tagName === 'P') {
          const affP = document.createElement('p');
          affP.className = 'affiliations';
          affP.innerHTML = (sibling as HTMLElement).innerHTML;
          titleSection.appendChild(affP);
          tempDiv.removeChild(sibling);
        }
        
        // Insert title section at the beginning
        tempDiv.insertBefore(titleSection, tempDiv.firstChild);
      } else {
        // If no h1 is found, create a default title using current date
        const defaultTitle = document.createElement('h1');
        defaultTitle.textContent = "Research Results";
        
        const today = new Date();
        const formattedDate = today.toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'long',
          day: 'numeric'
        });
        
        const dateP = document.createElement('p');
        dateP.className = 'authors';
        dateP.textContent = formattedDate;
        
        titleSection.appendChild(defaultTitle);
        titleSection.appendChild(dateP);
        
        tempDiv.insertBefore(titleSection, tempDiv.firstChild);
      }
      
      // Process sections: abstract, keywords, references
      wrapSection(tempDiv, 'abstract', 'abstract-section', 'abstract-text');
      wrapSection(tempDiv, 'keywords', 'keywords-section', 'keywords-text');
      wrapSection(tempDiv, 'references', 'references-section', null, true);
      
      // Add section-title class to other H2 headings
      tempDiv.querySelectorAll('h2').forEach(h2 => {
        if (!h2.parentElement?.classList.contains('abstract-section') &&
            !h2.parentElement?.classList.contains('keywords-section') &&
            !h2.parentElement?.classList.contains('references-section')) {
          h2.classList.add('section-title');
        }
      });
      
      // Add styles for document formatting
      const styleElement = document.createElement('style');
      styleElement.textContent = `
        /* A4 page settings */
        @page { size: A4; margin: 2cm 1.5cm; }
        
        /* Main container: single-column layout */
        #preview {
          font-family: Times, "Times New Roman", serif;
          font-size: 10pt;
          line-height: 1.2;
          width: auto;
          box-sizing: border-box;
          color: #000000;
        }
        
        /* Title, authors and affiliations */
        .title-section,
        .abstract-section,
        .keywords-section,
        .references-section {
          margin-bottom: 1em;
          color: #000000;
        }
        
        .title-section h1 {
          font-size: 14pt;
          font-weight: bold;
          text-align: center;
          margin-bottom: 0.2em;
          color: #000000;
        }
        .title-section .authors {
          font-size: 10pt;
          text-align: center;
          margin: 0;
          color: #000000;
        }
        .title-section .affiliations {
          font-size: 9pt;
          text-align: center;
          margin: 0.2em 0;
          color: #000000;
        }
        
        /* Section headings */
        .section-title {
          font-size: 12pt;
          font-weight: bold;
          margin-top: 1em;
          margin-bottom: 0.3em;
          color: #000000;
        }
        
        /* Abstract formatting */
        .abstract-section h2 { margin: 0; font-size: 12pt; font-weight: bold; color: #000000; }
        .abstract-section .abstract-text { font-style: italic; margin-top: 0.5em; color: #000000; }
        
        /* Keywords formatting */
        .keywords-section h2 { margin: 0; font-size: 12pt; font-weight: bold; color: #000000; }
        .keywords-section .keywords-text { margin-top: 0.3em; color: #000000; }
        
        /* References formatting */
        .references-section h2 { margin: 0; font-size: 12pt; font-weight: bold; color: #000000; }
        .references-section ol { padding-left: 1.2em; margin-top: 0.5em; color: #000000; }
        .references-section li { margin-bottom: 0.3em; color: #000000; }
        
        /* General text formatting */
        p { margin-bottom: 0.6em; color: #000000; }
        
        /* Lists */
        ul, ol { padding-left: 1.2em; margin-top: 0.5em; margin-bottom: 0.5em; color: #000000; }
        li { margin-bottom: 0.3em; color: #000000; }
        
        /* Tables */
        table {
          width: 100%;
          border-collapse: collapse;
          margin: 1em 0;
          break-inside: avoid;
          page-break-inside: avoid;
          color: #000000;
        }
        
        th, td {
          border: 1px solid #000000;
          padding: 0.4em;
          text-align: left;
          color: #000000;
        }
        
        th {
          background-color: #f5f5f5;
          font-weight: bold;
          color: #000000;
        }
        
        /* Code blocks */
        pre {
          background-color: #f8f8f8;
          border: 1px solid #eeeeee;
          border-radius: 3px;
          padding: 0.5em;
          margin: 0.7em 0;
          font-family: "Courier New", monospace;
          font-size: 9pt;
          white-space: pre-wrap;
          break-inside: avoid;
          page-break-inside: avoid;
          color: #000000;
        }
        
        code {
          font-family: "Courier New", monospace;
          font-size: 9pt;
          background-color: #f5f5f5;
          padding: 0.1em 0.3em;
          border-radius: 3px;
          color: #000000;
        }
        
        /* Prevent breaks inside figures/images */
        img {
          max-width: 100%;
          break-inside: avoid;
          page-break-inside: avoid;
        }
        
        /* Blockquotes */
        blockquote {
          margin: 0.7em 0;
          padding-left: 1em;
          border-left: 3px solid #000000;
          color: #000000;
          font-style: italic;
        }
        
        /* Force all text to be black */
        * {
          color: #000000 !important;
        }
      `;
      
      // Add the style element to the tempDiv
      tempDiv.appendChild(styleElement);
      
      // Add the temporary container to the document body
      document.body.appendChild(tempDiv);
      
      // Configure html2pdf options for A4 paper
      const opt = {
        margin: [20, 15, 20, 15], // [top, right, bottom, left] in mm
        filename: `research-report-${new Date().toISOString().slice(0, 10)}.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
        pagebreak: { mode: ['avoid-all', 'css', 'legacy'] }
      };
      
      // Generate and save the PDF
      html2pdf()
        .set(opt)
        .from(tempDiv)
        .save()
        .then(() => {
          // Clean up
          document.body.removeChild(tempDiv);
          console.log("PDF successfully generated");
        })
        .catch((error: unknown) => {
          console.error("Error generating PDF:", error);
          if (document.body.contains(tempDiv)) {
            document.body.removeChild(tempDiv);
          }
          alert("There was an error generating the PDF. Please try again.");
        });
    } catch (error) {
      console.error("Error initializing PDF generation:", error);
      alert("There was an error generating the PDF. Please try again.");
    }
  };

  // Helper function to wrap sections (abstract, keywords, references)
  const wrapSection = (
    root: HTMLElement, 
    name: string, 
    containerClass: string, 
    textClass: string | null, 
    isList: boolean = false
  ) => {
    Array.from(root.children).forEach(node => {
      if (node.tagName === 'H2' && node.textContent?.trim().toLowerCase() === name) {
        const div = document.createElement('div');
        div.className = containerClass;
        root.insertBefore(div, node);
        div.appendChild(node);
        
        let sib = div.nextSibling;
        while (sib && (sib as HTMLElement).tagName !== 'H2') {
          if (isList || textClass) {
            if (textClass && (sib as HTMLElement).tagName === 'P') {
              (sib as HTMLElement).classList.add(textClass);
            }
          }
          div.appendChild(sib);
          sib = div.nextSibling;
        }
      }
    });
  };

  // Add a function to check if a message is a placeholder
  const isPlaceholderMessage = (content: string): boolean => {
    return content.includes("I'm researching your query") || 
           content.includes("This may take a few moments");
  };

  // Optimize pollForMessageUpdates with better performance
  const pollForMessageUpdates = useCallback((chatId: number, messageId: string): void => {
    console.log(`Starting polling for updates to message: ${messageId}`);
    
    let retryCount = 0;
    const MAX_RETRIES = 5;
    
    // Set up an interval to check for updates
    const pollingInterval = setInterval(async () => {
      try {
        // Check if the component is still mounted
        if (!isInitialLoadComplete.current) {
          clearInterval(pollingInterval);
          return;
        }
        
        // Check request cache to avoid duplicate requests
        const cacheKey = `poll-${chatId}-${Date.now()}`;
        if (!requestCache.current[cacheKey]) {
          requestCache.current[cacheKey] = chatAPI.getChat(chatId);
        }
        
        // Fetch the latest chat to check for message updates
        const updatedChat = await requestCache.current[cacheKey];
        delete requestCache.current[cacheKey];
        
        // Find the message that matches our ID
        const updatedMessage = updatedChat.messages.find(
          (msg: { id: number | string }) => msg.id.toString() === messageId
        );
        
        if (updatedMessage) {
          // Check if the content has changed and is no longer a placeholder
          if (!isPlaceholderMessage(updatedMessage.content)) {
            console.log("Message has been updated with final content");
            
            // Update the messages state with the new content
            startTransition(() => {
              setMessages(prevMessages => 
                prevMessages.map(msg => 
                  msg.id === messageId 
                    ? { ...msg, content: updatedMessage.content } 
                    : msg
                )
              );
              
              // Update the cached messages
              setCachedChats(prev => {
                if (!prev[chatId]) return prev;
                
                return {
                  ...prev,
                  [chatId]: prev[chatId].map(msg => 
                    msg.id === messageId 
                      ? { ...msg, content: updatedMessage.content } 
                      : msg
                  )
                };
              });
              
              // Set the new content as the assistant response for the research UI
              setAssistantResponse({
                id: messageId,
                role: 'assistant',
                content: updatedMessage.content,
                createdAt: new Date(updatedMessage.created_at),
                updatedAt: new Date(updatedMessage.created_at)
              });
            });
            
            // Stop polling
            clearInterval(pollingInterval);
            // Remove from active intervals
            activePollingIntervals.current = activePollingIntervals.current.filter(
              id => id !== pollingInterval
            );
            
            // Animate the updated message with CSS transitions instead of anime.js
            const messageElement = document.querySelector(`.message-${messageId}`) as HTMLElement;
            if (messageElement) {
              messageElement.style.transform = 'translateY(5px)';
              messageElement.style.opacity = '0.8';
              messageElement.style.backgroundColor = 'rgba(79, 70, 229, 0.2)';
              
              setTimeout(() => {
                messageElement.style.transform = 'translateY(0)';
                messageElement.style.opacity = '1';
                messageElement.style.backgroundColor = 'transparent';
                messageElement.style.transition = 'transform 800ms ease, opacity 800ms ease, background-color 800ms ease';
              }, 10);
            }
          } else {
            retryCount++;
            
            if (retryCount > MAX_RETRIES) {
              // Increase polling interval after several retries
              clearInterval(pollingInterval);
              const newInterval = setInterval(pollingFunction, 5000); // 5 seconds
              activePollingIntervals.current = activePollingIntervals.current.filter(
                id => id !== pollingInterval
              );
              activePollingIntervals.current.push(newInterval);
            }
          }
        }
      } catch (error) {
        console.error("Error polling for message updates:", error);
        retryCount++;
        
        // Stop polling on too many errors
        if (retryCount > MAX_RETRIES) {
          clearInterval(pollingInterval);
          // Remove from active intervals
          activePollingIntervals.current = activePollingIntervals.current.filter(
            id => id !== pollingInterval
          );
        }
      }
    }, 2000); // Poll every 2 seconds initially
    
    const pollingFunction = () => {
      // Using the same function reference for both intervals
    };
    
    // Store the interval ID
    activePollingIntervals.current.push(pollingInterval);
    
    // Clean up the interval after 5 minutes to prevent indefinite polling
    setTimeout(() => {
      clearInterval(pollingInterval);
      // Remove from active intervals
      activePollingIntervals.current = activePollingIntervals.current.filter(
        id => id !== pollingInterval
      );
      console.log("Polling timeout reached, stopping polling.");
    }, 300000); // 5 minutes
  }, []);

  // Add cleanup for polling when component unmounts
  useEffect(() => {
    return () => {
      // Clear all active polling intervals when component unmounts
      activePollingIntervals.current.forEach(interval => {
        clearInterval(interval);
      });
      activePollingIntervals.current = [];
    };
  }, []);

  return (
    <div className="flex flex-col h-full bg-gradient-to-br from-gray-900 to-gray-950" ref={mainRef}>
      {/* Loading Overlay - Optimized to be less resource intensive */}
      {isLoading && (
        <div className="absolute inset-0 bg-gray-900/50 z-[10000] flex items-center justify-center" style={{backdropFilter: 'blur(2px)'}}>
          <div className="flex flex-col items-center">
            <div className="w-12 h-12 rounded-full border-t-2 border-l-2 border-indigo-500 animate-spin mb-4"></div>
            <p className="text-white font-medium">Loading...</p>
          </div>
        </div>
      )}
      
      {/* Header with model selection - Improved for mobile */}
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center p-4 border-b border-gray-800/40 backdrop-blur-md bg-gray-900/70 z-[39] sticky top-0">
        <div className="flex items-center mb-3 md:mb-0">
          <div className="w-2 h-6 bg-gradient-to-b from-indigo-500 to-purple-600 rounded-full mr-3"></div>
          <h1 className="text-xl font-semibold text-white">
            {researchMode === 'processing' ? 'Research Query' : 
             researchMode === 'results' ? 'Research Results' : 
             researchMode === 'chat' ? 'Chat Results' : 'AI Assistant'}
          </h1>
        </div>
        
        <div className="flex flex-col md:flex-row items-start md:items-center gap-3 w-full md:w-auto">
          {/* Model dropdown - only show in idle mode */}
          {researchMode === 'idle' && (
            <div className="w-full md:w-auto relative">
              <ModelSelector 
                selectedModel={selectedModel}
                setSelectedModel={setSelectedModel}
                isDropdownOpen={isDropdownOpen}
                setIsDropdownOpen={setIsDropdownOpen}
                isMobile={isMobile}
              />
            </div>
          )}
          
          {/* Status indicators for research mode */}
          {(researchMode === 'processing' || researchMode === 'results' || researchMode === 'chat') && (
            <div className="flex items-center gap-3 self-end md:self-auto">
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
        </div>
      </header>

      {/* Main chat area - Only show in idle mode */}
      {researchMode === 'idle' && (
        <div className="flex-1 overflow-auto">
          <WelcomeScreen 
            username={username} 
            welcomeRef={welcomeRef} 
          />
        </div>
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

          {/* Markdown Response Section - Improved styling */}
          {assistantResponse && (
            <div className="mt-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-3 gap-2">
                <h3 className="text-lg font-semibold text-white flex items-center">
                  Research Results
                  {isPlaceholderMessage(assistantResponse.content) && (
                    <span className="ml-2 text-xs text-indigo-400 bg-indigo-500/20 px-2 py-1 rounded-full">
                      Processing...
                    </span>
                  )}
                </h3>
                <button 
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    if (!isPlaceholderMessage(assistantResponse.content)) {
                      downloadMarkdownAsPDF(assistantResponse.content);
                    }
                  }}
                  className={`px-4 py-2 text-white rounded-lg flex items-center gap-2 transition-colors ${
                    isPlaceholderMessage(assistantResponse.content) 
                      ? 'bg-gray-600 cursor-not-allowed' 
                      : 'bg-indigo-600 hover:bg-indigo-700'
                  }`}
                  disabled={isPlaceholderMessage(assistantResponse.content)}
                >
                  <IconDownload size={16} />
                  <span>Download PDF</span>
                </button>
              </div>
              <div className="p-4 rounded-lg bg-gray-800/30 border border-gray-700/50">
                {isPlaceholderMessage(assistantResponse.content) ? (
                  <div>
                    <p>{assistantResponse.content}</p>
                    <div className="flex items-center gap-2 mt-4 p-3 bg-indigo-500/10 rounded-lg border border-indigo-500/20">
                      <div className="w-6 h-6 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin"></div>
                      <span className="text-indigo-400">Your research is being processed...</span>
                    </div>
                  </div>
                ) : (
                  <div className="prose prose-invert max-w-none">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        code({node, inline, className, children, ...props}: any) {
                          const match = /language-(\w+)/.exec(className || '');
                          return !inline && match ? (
                            <pre className="rounded-md">
                              <code className={className} {...props}>
                                {children}
                              </code>
                            </pre>
                          ) : (
                            <code className={className} {...props}>
                              {children}
                            </code>
                          );
                        },
                        table({children, ...props}: any) {
                          return (
                            <div className="overflow-x-auto my-4">
                              <table className="border-collapse border border-gray-700/50 w-full" {...props}>
                                {children}
                              </table>
                            </div>
                          );
                        },
                        th({children, ...props}: any) {
                          return (
                            <th className="border border-gray-700/50 bg-gray-800/50 px-4 py-2 text-left" {...props}>
                              {children}
                            </th>
                          );
                        },
                        td({children, ...props}: any) {
                          return (
                            <td className="border border-gray-700/50 px-4 py-2" {...props}>
                              {children}
                            </td>
                          );
                        }
                      }}
                    >
                      {assistantResponse.content}
                    </ReactMarkdown>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
      
      {/* Chat interface - Only shown in chat mode - Improved for mobile */}
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
                    className={`max-w-[95%] sm:max-w-[80%] rounded-lg px-4 py-3 ${
                      message.role === 'user'
                        ? 'bg-indigo-600 text-white rounded-tr-none shadow-lg shadow-indigo-600/10'
                        : 'bg-gray-800/80 text-gray-200 rounded-tl-none border border-gray-700/30'
                    }`}
                  >
                    {message.role === 'assistant' && isPlaceholderMessage(message.content) ? (
                      <div>
                        <p>{message.content}</p>
                        <div className="flex items-center mt-2">
                          <div className="animate-pulse flex space-x-1">
                            <div className="w-2 h-2 rounded-full bg-indigo-400"></div>
                            <div className="w-2 h-2 rounded-full bg-indigo-400" style={{ animationDelay: '0.3s' }}></div>
                            <div className="w-2 h-2 rounded-full bg-indigo-400" style={{ animationDelay: '0.6s' }}></div>
                          </div>
                          <span className="ml-2 text-xs text-indigo-400">Processing...</span>
                        </div>
                      </div>
                    ) : message.role === 'assistant' ? (
                      <div className="prose prose-invert max-w-none">
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          components={{
                            code({node, inline, className, children, ...props}: any) {
                              const match = /language-(\w+)/.exec(className || '');
                              return !inline && match ? (
                                <pre className="rounded-md">
                                  <code className={className} {...props}>
                                    {children}
                                  </code>
                                </pre>
                              ) : (
                                <code className={className} {...props}>
                                  {children}
                                </code>
                              );
                            },
                            table({children, ...props}: any) {
                              return (
                                <div className="overflow-x-auto my-4">
                                  <table className="border-collapse border border-gray-700/50 w-full" {...props}>
                                    {children}
                                  </table>
                                </div>
                              );
                            },
                            th({children, ...props}: any) {
                              return (
                                <th className="border border-gray-700/50 bg-gray-800/50 px-4 py-2 text-left" {...props}>
                                  {children}
                                </th>
                              );
                            },
                            td({children, ...props}: any) {
                              return (
                                <td className="border border-gray-700/50 px-4 py-2" {...props}>
                                  {children}
                                </td>
                              );
                            }
                          }}
                        >
                          {message.content}
                        </ReactMarkdown>
                      </div>
                    ) : (
                      message.content
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
          
          {/* Add download button in chat mode too - Improved for mobile */}
          {messages.length > 0 && (
            <div className="mt-2 mb-4 flex justify-end">
              <button 
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  // Find the latest assistant message
                  const latestAssistantMessage = [...messages]
                    .reverse()
                    .find(msg => msg.role === 'assistant');
                
                  if (latestAssistantMessage && !isPlaceholderMessage(latestAssistantMessage.content)) {
                    downloadMarkdownAsPDF(latestAssistantMessage.content);
                  }
                }}
                disabled={!messages.some(msg => msg.role === 'assistant' && !isPlaceholderMessage(msg.content))}
                className={`px-3 py-1.5 rounded-lg text-sm flex items-center gap-1.5 border transition-colors ${
                  messages.some(msg => msg.role === 'assistant' && !isPlaceholderMessage(msg.content))
                    ? 'bg-gray-800 text-gray-300 hover:bg-gray-700 border-gray-700/30'
                    : 'bg-gray-800/50 text-gray-500 border-gray-800/30 cursor-not-allowed'
                }`}
              >
                <IconDownload size={14} />
                <span>Download Response</span>
              </button>
            </div>
          )}
          
          {/* Chat input form - Improved for mobile */}
          <form onSubmit={handleChatSubmit} className="relative">
            <input
              type="text"
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Type your message..."
              className="w-full p-4 pl-4 pr-12 rounded-lg border border-gray-700/50 bg-gray-800/50 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/40"
            />
            <button
              type="submit"
              disabled={!inputValue.trim()}
              className="absolute right-2 top-1/2 transform -translate-y-1/2 p-2 rounded-full bg-indigo-600 hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:bg-gray-700"
            >
              <IconSend size={18} className="text-white" />
            </button>
          </form>
        </div>
      )}

      {/* Search bar and controls - Only show in idle mode */}
      {researchMode === 'idle' && (
        <div className="p-4 border-t border-gray-800/40 backdrop-blur-md bg-gray-900/70 sticky bottom-0 z-[40]">
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

export default React.memo(ChatMain); 