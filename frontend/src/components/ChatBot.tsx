import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageCircle, X, Send, Search, Database, Brain, ArrowRight, ChevronDown } from 'lucide-react';
import anime from 'animejs';

interface Message {
  id: number;
  text: string;
  isBot: boolean;
  timestamp: Date;
}

const ChatBot: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      text: "👋 Hi there! I'm your Searchify.AI assistant. How can I help with your research needs today?",
      isBot: true,
      timestamp: new Date()
    }
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const chatButtonRef = useRef<HTMLButtonElement>(null);
  const particlesRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input when chat opens
  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus();
      
      // Animated opening sequence
      anime.timeline({
        easing: 'easeOutExpo',
      })
      .add({
        targets: '.chat-header',
        translateY: [-20, 0],
        opacity: [0, 1],
        duration: 600,
      })
      .add({
        targets: '.chat-message',
        translateY: [10, 0],
        opacity: [0, 1],
        duration: 800,
        delay: anime.stagger(100)
      }, '-=400')
      .add({
        targets: '.chat-input-container',
        translateY: [20, 0],
        opacity: [0, 1],
        duration: 600
      }, '-=600');
    }
  }, [isOpen]);

  // Initialize particle effects
  useEffect(() => {
    if (particlesRef.current && chatButtonRef.current) {
      const particlesContainer = particlesRef.current;
      const numberOfParticles = 12;
      
      // Clear previous particles if any
      while (particlesContainer.firstChild) {
        particlesContainer.removeChild(particlesContainer.firstChild);
      }
      
      for (let i = 0; i < numberOfParticles; i++) {
        const particle = document.createElement('div');
        const size = Math.random() * 3 + 1;
        const opacity = Math.random() * 0.3 + 0.1;
        
        particle.className = 'absolute rounded-full bg-indigo-400/30 backdrop-blur-sm';
        particle.style.width = `${size}px`;
        particle.style.height = `${size}px`;
        particle.style.position = 'absolute';
        particle.style.opacity = opacity.toString();
        
        particlesContainer.appendChild(particle);
        
        const duration = anime.random(2000, 5000);
        const delay = anime.random(0, 1000);
        
        // Calculate positions relative to the button
        const angle = (i / numberOfParticles) * Math.PI * 2;
        const radius = 40;
        
        anime({
          targets: particle,
          translateX: [
            { 
              value: Math.cos(angle) * radius, 
              duration: 0 
            },
            { 
              value: Math.cos(angle) * (radius + anime.random(5, 15)), 
              duration: duration 
            }
          ],
          translateY: [
            { 
              value: Math.sin(angle) * radius, 
              duration: 0 
            },
            { 
              value: Math.sin(angle) * (radius + anime.random(5, 15)), 
              duration: duration 
            }
          ],
          scale: [
            { value: 1 },
            { value: anime.random(1.5, 2.5), duration: duration / 2 },
            { value: 0, duration: duration / 2 }
          ],
          opacity: [
            { value: opacity, duration: 0 },
            { value: anime.random(0.5, 0.8), duration: duration / 2 },
            { value: 0, duration: duration / 2 }
          ],
          easing: 'easeInOutQuad',
          duration: duration,
          loop: true,
          delay: delay
        });
      }
    }
    
    // Button hover animation
    if (chatButtonRef.current) {
      chatButtonRef.current.addEventListener('mouseenter', () => {
        anime({
          targets: chatButtonRef.current,
          scale: 1.05,
          boxShadow: '0 0 15px rgba(99, 102, 241, 0.5)',
          duration: 300,
          easing: 'easeOutQuad'
        });
      });
      
      chatButtonRef.current.addEventListener('mouseleave', () => {
        anime({
          targets: chatButtonRef.current,
          scale: 1,
          boxShadow: '0 0 0 rgba(99, 102, 241, 0)',
          duration: 300,
          easing: 'easeOutQuad'
        });
      });
    }
    
    return () => {
      if (chatButtonRef.current) {
        chatButtonRef.current.removeEventListener('mouseenter', () => {});
        chatButtonRef.current.removeEventListener('mouseleave', () => {});
      }
    };
  }, []);

  // Sample bot responses
  const botResponses = [
    "What type of research are you looking to conduct today?",
    "I can help with finding academic sources, news articles, and data analysis. What are you looking for?",
    "Our platform can generate comprehensive reports on various topics. What subject interests you?",
    "Would you like me to analyze recent trends on this topic for your research?",
    "I can connect to multiple databases to find the most relevant information for your query. What specific aspects are you interested in?"
  ];

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!message.trim()) return;
    
    // Add user message
    const newUserMessage: Message = {
      id: messages.length + 1,
      text: message,
      isBot: false,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, newUserMessage]);
    setMessage('');
    
    // Animate the new message with a slide-in effect
    setTimeout(() => {
      anime({
        targets: '.chat-message:last-child',
        translateX: [10, 0],
        opacity: [0, 1],
        duration: 400,
        easing: 'easeOutQuad'
      });
    }, 10);
    
    // Show bot typing indicator
    setIsTyping(true);
    
    // Simulate bot response after delay
    setTimeout(() => {
      const randomResponse = botResponses[Math.floor(Math.random() * botResponses.length)];
      const newBotMessage: Message = {
        id: messages.length + 2,
        text: randomResponse,
        isBot: true,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, newBotMessage]);
      setIsTyping(false);
      
      // Animate the bot response
      setTimeout(() => {
        anime({
          targets: '.chat-message:last-child',
          translateX: [-10, 0],
          opacity: [0, 1],
          duration: 400,
          easing: 'easeOutQuad'
        });
      }, 10);
    }, 1000 + Math.random() * 1000);
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      <AnimatePresence>
        {isOpen && (
          <motion.div
            ref={chatContainerRef}
            initial={{ opacity: 0, y: 20, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.9 }}
            transition={{ duration: 0.2 }}
            className="mb-4 bg-gray-900 border border-gray-800 rounded-2xl shadow-2xl w-80 sm:w-96 max-h-[500px] flex flex-col overflow-hidden"
          >
            {/* Chat header */}
            <div className="chat-header bg-gray-800/80 backdrop-blur-sm px-4 py-3 border-b border-gray-700 flex items-center justify-between">
              <div className="flex items-center">
                <div className="relative mr-2">
                  <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500 to-violet-500 rounded-full blur-sm opacity-60"></div>
                  <div className="relative bg-gray-900 rounded-full p-1.5">
                    <Search className="w-5 h-5 text-indigo-400" />
                  </div>
                </div>
                <div>
                  <h3 className="text-white font-medium text-pretty">Searchify<span className='text-indigo-400'>.AI</span> Assistant</h3>
                  <div className="flex items-center text-xs text-green-400">
                    <span className="w-2 h-2 bg-green-400 rounded-full inline-block mr-1"></span>
                    <span>Online</span>
                  </div>
                </div>
              </div>
              <button 
                onClick={() => setIsOpen(false)}
                className="text-gray-400 hover:text-white p-1 rounded-full hover:bg-gray-700 transition-colors"
              >
                <X size={18} />
              </button>
            </div>
            
            {/* Chat messages */}
            <div className="flex-1 p-4 overflow-y-auto bg-gray-950/50 backdrop-blur-sm">
              <div className="space-y-4">
                {messages.map((msg) => (
                  <div 
                    key={msg.id} 
                    className={`chat-message flex ${msg.isBot ? 'justify-start' : 'justify-end'}`}
                  >
                    <div 
                      className={`max-w-[80%] px-4 py-2 rounded-2xl ${
                        msg.isBot 
                          ? 'bg-gray-800 text-white rounded-bl-none' 
                          : 'bg-indigo-500 text-white rounded-br-none'
                      }`}
                    >
                      <p className="text-sm">{msg.text}</p>
                      <p className="text-xs mt-1 opacity-70 text-right">
                        {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>
                  </div>
                ))}
                
                {/* Bot typing indicator */}
                {isTyping && (
                  <div className="flex justify-start">
                    <div className="bg-gray-800 text-white px-4 py-3 rounded-2xl rounded-bl-none max-w-[80%]">
                      <div className="flex space-x-1">
                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></span>
                      </div>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>
            </div>
            
            {/* Chat input */}
            <form onSubmit={handleSendMessage} className="chat-input-container p-3 border-t border-gray-800 bg-gray-900/80 backdrop-blur-sm">
              <div className="flex items-center">
                <input
                  ref={inputRef}
                  type="text"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Type your research query..."
                  className="flex-1 bg-gray-800 border border-gray-700 rounded-full py-2 px-4 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm"
                />
                <button 
                  type="submit"
                  className="ml-2 p-2 bg-indigo-500 text-white rounded-full hover:bg-indigo-600 transition-colors"
                  disabled={!message.trim()}
                >
                  <Send size={18} />
                </button>
              </div>
            </form>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Chat button with particles */}
      <div className="relative">
        <div className="absolute inset-0 rounded-full" ref={particlesRef}></div>
        <motion.button
          ref={chatButtonRef}
          onClick={() => {
            setIsOpen(!isOpen);
            
            // Button click animation
            anime({
              targets: chatButtonRef.current,
              scale: [1, 1.2, 1],
              duration: 400,
              easing: 'easeOutBack'
            });
          }}
          className="bg-indigo-500 hover:bg-indigo-600 text-white p-4 rounded-full shadow-lg flex items-center justify-center relative group"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <AnimatePresence mode="wait">
            {isOpen ? (
              <motion.div
                key="close"
                initial={{ rotate: -90, opacity: 0 }}
                animate={{ rotate: 0, opacity: 1 }}
                exit={{ rotate: 90, opacity: 0 }}
                transition={{ duration: 0.2 }}
              >
                <X size={24} />
              </motion.div>
            ) : (
              <motion.div
                key="open"
                initial={{ rotate: 90, opacity: 0 }}
                animate={{ rotate: 0, opacity: 1 }}
                exit={{ rotate: -90, opacity: 0 }}
                transition={{ duration: 0.2 }}
              >
                <MessageCircle size={24} />
              </motion.div>
            )}
          </AnimatePresence>
          
          {/* Notification dot with pulsing animation */}
          {!isOpen && (
            <span className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full border-2 border-indigo-500 animate-pulse"></span>
          )}
        </motion.button>
      </div>
    </div>
  );
};

export default ChatBot; 