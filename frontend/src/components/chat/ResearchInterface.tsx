import React, { useEffect, useState, useRef } from 'react';
import {
  IconBooks,
  IconSearch,
  IconBrain,
  IconBolt,
  IconArrowRight,
  IconLink,
  IconWorld,
  IconClock,
  IconLoader2,
  IconRocket,
  IconPencil,
  IconCheck,
  IconX
} from '@tabler/icons-react';
import anime from 'animejs';

interface ResearchInterfaceProps {
  searchQuery: string;
  sourceCount: number;
  progress: number;
  currentStage: string;
  onNewChat?: () => void;
  onComplete?: () => void;
}

// Animated progress bar with 3D effect
const ProgressBar: React.FC<{ progress: number }> = ({ progress }) => {
  return (
    <div className="w-full bg-gray-800/70 rounded-full h-4 overflow-hidden backdrop-blur-sm shadow-inner relative">
      {/* Gradient background */}
      <div 
        className="h-full relative bg-gradient-to-r from-indigo-600 via-purple-500 to-indigo-600 transition-all duration-300 ease-out"
        style={{ 
          width: `${progress}%`,
          backgroundSize: '200% 100%',
          animation: 'shimmer 2s infinite linear'
        }}
      >
        {/* Animated shine effect */}
        <div className="absolute inset-0 overflow-hidden">
          <span className="absolute inset-0 opacity-40 blur-sm" 
                style={{
                  background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent)',
                  transform: 'translateX(-100%)',
                  animation: 'shine 1.5s infinite'
                }}>
          </span>
        </div>
        
        {/* Progress pill */}
        {progress > 5 && (
          <div className="absolute right-1 top-1/2 -translate-y-1/2 bg-white text-indigo-800 text-[8px] font-bold px-1.5 rounded-full shadow-lg">
            {Math.floor(progress)}%
          </div>
        )}
      </div>
      
      {/* Progress indicator dots */}
      <div className="absolute top-1/2 left-0 w-full -translate-y-1/2 flex justify-between px-2 pointer-events-none">
        {[25, 50, 75].map(milestone => (
          <div 
            key={milestone} 
            className={`w-1.5 h-1.5 rounded-full transition-all duration-500 ${
              progress >= milestone 
                ? 'bg-white shadow-glow' 
                : 'bg-gray-600'
            }`}
            style={{
              left: `${milestone}%`,
              boxShadow: progress >= milestone ? '0 0 5px rgba(255,255,255,0.7)' : 'none'
            }}
          />
        ))}
      </div>
    </div>
  );
};

// Modern research category card with 3D hover effect
const ResearchCategory: React.FC<{ 
  icon: React.ReactNode, 
  title: string,
  count: number,
  isActive?: boolean,
  isComplete?: boolean,
  onClick?: () => void
}> = ({ icon, title, count, isActive = false, isComplete = false, onClick }) => {
  return (
    <button 
      onClick={onClick}
      className={`research-category flex flex-col items-center justify-center p-4 rounded-xl transition-all duration-300 transform hover:-translate-y-1 hover:shadow-lg group relative ${
        isActive 
          ? 'bg-gradient-to-br from-indigo-600/30 to-purple-600/30 border border-indigo-500/50 shadow-md' 
          : 'bg-gray-800/60 backdrop-blur-sm border border-gray-700/50 hover:border-indigo-500/30 hover:bg-gray-800/80'
      }`}
    >
      {/* 3D rotational wrapper */}
      <div className="transition-transform duration-300 group-hover:scale-105 flex flex-col items-center">
        <div className={`w-12 h-12 rounded-xl ${isActive ? 'bg-gradient-to-br from-indigo-600 to-purple-600' : 'bg-gray-700/70'} flex items-center justify-center mb-3 transition-all duration-300 group-hover:shadow-lg ${!isActive && 'group-hover:bg-gray-700'}`}>
          {icon}
        </div>
        
        <span className="text-sm font-medium text-white mb-1">{title}</span>
        
        <div className="flex items-center justify-center bg-gray-900/70 px-2.5 py-1 rounded-full text-xs mt-1">
          <span className={`${isActive ? 'text-indigo-400' : 'text-gray-400'}`}>{count}</span>
        </div>
      </div>
      
      {/* Completion indicator */}
      {isComplete && (
        <div className="absolute top-2 right-2 w-5 h-5 rounded-full bg-green-500 flex items-center justify-center">
          <IconCheck size={12} className="text-white" />
        </div>
      )}
    </button>
  );
};

// Enhanced source item with interactive elements
const SourceItem: React.FC<{
  title: string;
  source: string;
  icon: React.ReactNode;
  index: number;
  relevance?: number; // 0-100 relevance score
}> = ({ title, source, icon, index, relevance = 70 }) => {
  return (
    <div 
      className="source-item flex items-start gap-3 p-4 rounded-lg bg-gray-800/40 backdrop-blur-sm border border-gray-700/40 hover:border-indigo-500/30 hover:bg-gray-800/60 transition-all duration-200 group relative overflow-hidden"
      style={{ 
        animationDelay: `${index * 100}ms`,
        opacity: 0,
        transform: 'translateY(20px)'
      }}
    >
      {/* Relevance indicator bar */}
      <div 
        className="absolute left-0 top-0 h-full bg-gradient-to-r from-indigo-600/20 to-transparent" 
        style={{ width: `${relevance}%` }}
      />
      
      {/* Content */}
      <div className="w-8 h-8 rounded-md bg-gray-700/70 flex-shrink-0 flex items-center justify-center text-indigo-400 z-10">
        {icon}
      </div>
      
      <div className="flex-1 min-w-0 z-10">
        <h4 className="text-sm font-medium text-white truncate">{title}</h4>
        <p className="text-xs text-gray-400 truncate flex items-center gap-1">
          <IconLink size={10} className="inline" />
          <span>{source}</span>
        </p>
      </div>
      
      {/* Action buttons that appear on hover */}
      <div className="absolute right-2 top-1/2 -translate-y-1/2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-10">
        <button className="w-6 h-6 rounded-full bg-gray-700 hover:bg-indigo-600 transition-colors flex items-center justify-center">
          <IconPencil size={12} className="text-gray-300" />
        </button>
        <button className="w-6 h-6 rounded-full bg-gray-700 hover:bg-red-600 transition-colors flex items-center justify-center">
          <IconX size={12} className="text-gray-300" />
        </button>
      </div>
    </div>
  );
};

const ResearchInterface: React.FC<ResearchInterfaceProps> = ({ 
  searchQuery, 
  sourceCount, 
  progress, 
  currentStage,
  onNewChat,
  onComplete
}) => {
  const [sourcesDiscovered, setSourcesDiscovered] = useState({
    academic: 0,
    news: 0,
    expert: 0,
    insights: 0
  });
  
  const containerRef = useRef<HTMLDivElement>(null);
  const [showNewChatButton, setShowNewChatButton] = useState(false);
  
  // Generate random source counts based on progress
  useEffect(() => {
    const interval = setInterval(() => {
      if (progress < 100) {
        setSourcesDiscovered({
          academic: Math.min(Math.floor(Math.random() * 5) + Math.floor(progress / 5), 28),
          news: Math.min(Math.floor(Math.random() * 3) + Math.floor(progress / 7), 12),
          expert: Math.min(Math.floor(Math.random() * 2) + Math.floor(progress / 10), 8),
          insights: Math.min(Math.floor(Math.random() * 2) + Math.floor(progress / 15), 6)
        });
      }
    }, 2000);
    
    // Show new chat button when research is complete
    if (progress >= 99) {
      setShowNewChatButton(true);
      if (onComplete) {
        setTimeout(onComplete, 1500);
      }
    }
    
    return () => clearInterval(interval);
  }, [progress, onComplete]);
  
  // Sample sources for demonstration
  const sampleSources = [
    { title: "Advanced Research Methods", source: "academic-journals.org", icon: <IconBooks size={16} />, relevance: 95 },
    { title: "Recent Developments in AI", source: "tech-insights.com", icon: <IconWorld size={16} />, relevance: 88 },
    { title: "Expert Analysis on Subject", source: "expert-opinions.net", icon: <IconBrain size={16} />, relevance: 76 },
    { title: "Latest Industry Trends", source: "industry-today.com", icon: <IconClock size={16} />, relevance: 65 }
  ];

  // Animations
  useEffect(() => {
    if (!containerRef.current) return;
    
    // Add perspective to container for 3D effects
    containerRef.current.style.perspective = '1000px';
    
    // Animate research interface
    anime({
      targets: '.research-header',
      opacity: [0, 1],
      translateY: [-20, 0],
      duration: 700,
      easing: 'easeOutQuad'
    });
    
    anime({
      targets: '.research-progress',
      opacity: [0, 1],
      translateY: [20, 0],
      rotateX: ['-5deg', '0deg'],
      duration: 700,
      delay: 200,
      easing: 'easeOutQuad'
    });
    
    anime({
      targets: '.research-category',
      opacity: [0, 1],
      scale: [0.95, 1],
      rotateX: ['-10deg', '0deg'],
      duration: 700,
      delay: anime.stagger(100, {start: 400}),
      easing: 'easeOutQuad'
    });
    
    anime({
      targets: '.sources-header',
      opacity: [0, 1],
      translateX: [-20, 0],
      duration: 700, 
      delay: 600,
      easing: 'easeOutQuad'
    });
    
    anime({
      targets: '.source-item',
      translateY: [20, 0],
      opacity: [0, 1],
      rotateX: ['-5deg', '0deg'],
      duration: 700,
      delay: anime.stagger(100, {start: 800}),
      easing: 'easeOutElastic(1, .8)'
    });
    
    // Shimmer animation for gradient background
    const shimmerStyle = document.createElement('style');
    shimmerStyle.innerHTML = `
      @keyframes shimmer {
        0% { background-position: 0% 50%; }
        100% { background-position: 100% 50%; }
      }
      @keyframes shine {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
      }
      .shadow-glow {
        box-shadow: 0 0 8px rgba(139, 92, 246, 0.7);
      }
      .rotate-y {
        transform: rotateY(180deg);
      }
    `;
    document.head.appendChild(shimmerStyle);
    
    // Background particle effects
    if (containerRef.current) {
      createParticles(containerRef.current);
    }
    
    return () => {
      document.head.removeChild(shimmerStyle);
    };
  }, []);

  // Create background particle effects
  const createParticles = (container: HTMLDivElement) => {
    const particleCount = 30;
    const colors = ['rgba(139, 92, 246, 0.1)', 'rgba(79, 70, 229, 0.1)', 'rgba(124, 58, 237, 0.1)'];
    
    for (let i = 0; i < particleCount; i++) {
      const size = Math.random() * 6 + 2;
      const particle = document.createElement('div');
      particle.className = 'absolute rounded-full pointer-events-none';
      particle.style.width = `${size}px`;
      particle.style.height = `${size}px`;
      particle.style.background = colors[Math.floor(Math.random() * colors.length)];
      particle.style.left = `${Math.random() * 100}%`;
      particle.style.top = `${Math.random() * 100}%`;
      particle.style.opacity = '0';
      particle.style.transform = 'scale(0)';
      
      container.appendChild(particle);
      
      // Animate particles
      anime({
        targets: particle,
        opacity: [0, 0.8, 0],
        scale: [0, 1, 0],
        left: `+=${(Math.random() * 100) - 50}px`,
        top: `+=${(Math.random() * 100) - 50}px`,
        duration: Math.random() * 5000 + 3000,
        delay: Math.random() * 2000,
        easing: 'easeInOutQuad',
        complete: () => {
          container.removeChild(particle);
        }
      });
    }
  };

  // Handle new chat button click
  const handleNewChat = () => {
    if (onNewChat) {
      anime({
        targets: containerRef.current,
        translateY: [0, 20],
        opacity: [1, 0],
        duration: 500,
        easing: 'easeOutQuad',
        complete: onNewChat
      });
    }
  };

  return (
    <div className="flex-1 overflow-y-auto py-6 px-4 md:px-6 flex flex-col relative" ref={containerRef}>
      {/* Query section with enhanced design */}
      <div className="research-header mb-6">
        <div className="flex items-center text-sm text-indigo-400 mb-2">
          <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 mr-2 animate-pulse"></div>
          <span>Research Query</span>
        </div>
        <h2 className="text-xl md:text-2xl font-semibold bg-clip-text text-transparent bg-gradient-to-r from-white via-indigo-200 to-white">{searchQuery}</h2>
      </div>
      
      {/* Progress section with enhanced visuals */}
      <div className="research-progress mb-8 p-5 rounded-xl border border-gray-700/30 bg-gray-800/20 backdrop-blur-sm transform transition-all">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-4 gap-2">
          <div>
            <div className="text-sm text-gray-300 font-medium mb-1">Processing {sourceCount} sources</div>
            <div className="text-xs text-gray-400 flex items-center">
              <IconLoader2 size={12} className="text-indigo-400 mr-1.5 animate-spin" />
              <span>{currentStage}</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex -space-x-2">
              <div className="w-6 h-6 rounded-full border-2 border-gray-800 bg-indigo-600 flex items-center justify-center text-[10px] text-white font-bold">AI</div>
              <div className="w-6 h-6 rounded-full border-2 border-gray-800 bg-purple-600 flex items-center justify-center text-[10px] text-white font-bold">ML</div>
              <div className="w-6 h-6 rounded-full border-2 border-gray-800 bg-blue-600 flex items-center justify-center text-[10px] text-white font-bold">DB</div>
            </div>
            <div className="px-2 py-1 rounded-full bg-indigo-600/20 border border-indigo-500/30 text-xs text-indigo-300 font-medium">
              {Math.floor(progress)}%
            </div>
          </div>
        </div>
        
        <ProgressBar progress={progress} />
        
        {/* Stage indicators */}
        <div className="flex justify-between mt-4 text-xs text-gray-500">
          <div className={progress >= 25 ? 'text-indigo-400' : ''}>Collection</div>
          <div className={progress >= 50 ? 'text-indigo-400' : ''}>Processing</div>
          <div className={progress >= 75 ? 'text-indigo-400' : ''}>Analysis</div>
          <div className={progress >= 95 ? 'text-indigo-400' : ''}>Completion</div>
        </div>
      </div>
      
      {/* Categories grid - responsive for all devices */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4 mb-8">
        <ResearchCategory 
          icon={<IconBooks size={20} className="text-white" />} 
          title="Academic"
          count={sourcesDiscovered.academic}
          isActive={true}
          isComplete={progress >= 60}
        />
        
        <ResearchCategory 
          icon={<IconWorld size={20} className="text-white" />} 
          title="News"
          count={sourcesDiscovered.news}
          isComplete={progress >= 75}
        />
        
        <ResearchCategory 
          icon={<IconBrain size={20} className="text-white" />} 
          title="Experts"
          count={sourcesDiscovered.expert}
          isComplete={progress >= 90}
        />
        
        <ResearchCategory 
          icon={<IconBolt size={20} className="text-white" />} 
          title="Insights"
          count={sourcesDiscovered.insights}
          isComplete={progress >= 95}
        />
      </div>
      
      {/* Top sources - Enhanced section */}
      <div className="sources-header flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-300 flex items-center">
          <span className="relative">
            Top Sources
            <span className="absolute -top-1 -right-2 w-2 h-2 rounded-full bg-indigo-500 animate-ping"></span>
          </span>
        </h3>
        <div className="text-xs text-indigo-400 flex items-center gap-1 hover:text-white transition-colors cursor-pointer">
          <span>View all</span>
          <IconArrowRight size={12} />
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-8">
        {sampleSources.map((source, index) => (
          <SourceItem 
            key={index}
            title={source.title}
            source={source.source}
            icon={source.icon}
            index={index}
            relevance={source.relevance}
          />
        ))}
      </div>
      
      {/* New Chat button - appears when research is complete */}
      {showNewChatButton && (
        <div className="flex justify-center mt-auto">
          <button 
            onClick={handleNewChat}
            className="px-4 py-2.5 rounded-lg bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-medium flex items-center gap-2 hover:from-indigo-500 hover:to-purple-500 shadow-lg shadow-indigo-600/20 transition-all duration-300 hover:shadow-xl hover:shadow-indigo-600/30 hover:-translate-y-1"
          >
            <IconRocket size={16} />
            <span>Start New Chat</span>
          </button>
        </div>
      )}
    </div>
  );
};

export default ResearchInterface; 