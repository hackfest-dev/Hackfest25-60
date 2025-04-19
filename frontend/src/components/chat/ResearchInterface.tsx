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
  IconX,
  IconDatabase,
  IconFileText,
  IconNews,
  IconSchool
} from '@tabler/icons-react';
import anime from 'animejs';

interface ResearchInterfaceProps {
  searchQuery: string;
  sourceCount: number;
  progress: number;
  currentStage: string;
  onNewChat?: () => void;
  onComplete?: () => void;
  backendData?: any;
}

// Sample research sources by category for demo
const SAMPLE_SOURCES = {
  academic: [
    { title: "The Evolution of Deep Learning", source: "journal.ai-research.org", icon: <IconSchool size={16} />, relevance: 98 },
    { title: "Multimodal Learning: A Survey", source: "academic-journals.org", icon: <IconBooks size={16} />, relevance: 94 },
    { title: "Comparative Analysis of ML Algorithms", source: "ieee-explore.org", icon: <IconSchool size={16} />, relevance: 92 },
    { title: "Neural Networks in Practice", source: "research-gate.net", icon: <IconSchool size={16} />, relevance: 90 },
    { title: "Statistical Methods in AI", source: "statistics-journal.edu", icon: <IconBooks size={16} />, relevance: 87 }
  ],
  news: [
    { title: "Latest Breakthroughs in AI", source: "tech-today.com", icon: <IconNews size={16} />, relevance: 89 },
    { title: "Industry Adopts New ML Techniques", source: "ai-industry-news.com", icon: <IconNews size={16} />, relevance: 82 },
    { title: "Start-ups Leveraging AI for Growth", source: "startup-mag.com", icon: <IconNews size={16} />, relevance: 78 },
    { title: "AI Conference Highlights", source: "tech-events-daily.com", icon: <IconNews size={16} />, relevance: 76 }
  ],
  expert: [
    { title: "Expert Opinion: Future of AI", source: "expert-insights.net", icon: <IconBrain size={16} />, relevance: 93 },
    { title: "Interview with Leading Researcher", source: "ai-talks.com", icon: <IconBrain size={16} />, relevance: 89 },
    { title: "AI Ethics Perspective", source: "ethics-in-tech.org", icon: <IconBrain size={16} />, relevance: 84 }
  ],
  insights: [
    { title: "Market Analysis of AI Trends", source: "market-intelligence.com", icon: <IconDatabase size={16} />, relevance: 86 },
    { title: "Key Insights from Multiple Sources", source: "data-synthesis.com", icon: <IconFileText size={16} />, relevance: 82 },
    { title: "Practical Applications Survey", source: "implementation-review.org", icon: <IconDatabase size={16} />, relevance: 79 }
  ]
};

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

// Stages of research for better visualization of progress
const RESEARCH_STAGES = [
  { threshold: 0, name: "Initializing...", detail: "Setting up research parameters" },
  { threshold: 5, name: "Data Collection", detail: "Gathering relevant sources" },
  { threshold: 25, name: "Indexing", detail: "Cataloging research materials" },
  { threshold: 40, name: "Analysis", detail: "Processing research data" },
  { threshold: 60, name: "Contextualizing", detail: "Establishing connections between sources" },
  { threshold: 75, name: "Synthesizing", detail: "Combining insights from multiple sources" },
  { threshold: 90, name: "Finalizing", detail: "Preparing research results" },
  { threshold: 98, name: "Completion", detail: "Research complete" }
];

const ResearchInterface: React.FC<ResearchInterfaceProps> = ({ 
  searchQuery, 
  sourceCount, 
  progress, 
  currentStage,
  onComplete,
  backendData
}) => {
  const [activeCategory, setActiveCategory] = useState('academic');
  const [sourcesDiscovered, setSourcesDiscovered] = useState({
    academic: 0,
    news: 0,
    expert: 0,
    insights: 0
  });
  const [visibleSources, setVisibleSources] = useState(SAMPLE_SOURCES.academic.slice(0, 4));
  const [currentResearchStage, setCurrentResearchStage] = useState(RESEARCH_STAGES[0]);
  
  const containerRef = useRef<HTMLDivElement>(null);
  
  // Get current stage based on progress
  useEffect(() => {
    for (let i = RESEARCH_STAGES.length - 1; i >= 0; i--) {
      if (progress >= RESEARCH_STAGES[i].threshold) {
        setCurrentResearchStage(RESEARCH_STAGES[i]);
        break;
      }
    }
  }, [progress]);

  // Generate realistic source counts based on progress
  useEffect(() => {
    const interval = setInterval(() => {
      if (progress < 100) {
        // More realistic progression of sources being discovered
        const academicMax = 28;
        const newsMax = 12;
        const expertMax = 8;
        const insightsMax = 6;
        
        // Calculate progressive increase based on current progress percentage
        const progressFactor = progress / 100;
        const randomVariance = () => (Math.random() * 0.1) - 0.05; // Small random variance
        
        setSourcesDiscovered({
          academic: Math.min(Math.floor((progressFactor * academicMax) * (1 + randomVariance())), academicMax),
          news: Math.min(Math.floor((progressFactor * newsMax) * (1 + randomVariance())), newsMax),
          expert: Math.min(Math.floor((progressFactor * expertMax) * (1 + randomVariance())), expertMax),
          insights: Math.min(Math.floor((progressFactor * insightsMax) * (1 + randomVariance())), insightsMax)
        });
        
        // Update visible sources based on active category and progress
        // Show more relevant sources as research progresses
        if (progress > 30) {
          setVisibleSources(
            SAMPLE_SOURCES[activeCategory as keyof typeof SAMPLE_SOURCES]
              .slice(0, Math.min(4, Math.floor(progress / 25) + 1))
          );
        }
      }
    }, 2000);
    
    return () => clearInterval(interval);
  }, [progress, activeCategory, onComplete]);
  
  // Handle category change
  const handleCategoryChange = (category: string) => {
    setActiveCategory(category);
    setVisibleSources(
      SAMPLE_SOURCES[category as keyof typeof SAMPLE_SOURCES].slice(0, 4)
    );
  };

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
              <span>{currentResearchStage.name}: {currentResearchStage.detail}</span>
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
          isActive={activeCategory === 'academic'}
          isComplete={progress >= 60}
          onClick={() => handleCategoryChange('academic')}
        />
        
        <ResearchCategory 
          icon={<IconWorld size={20} className="text-white" />} 
          title="News"
          count={sourcesDiscovered.news}
          isActive={activeCategory === 'news'}
          isComplete={progress >= 75}
          onClick={() => handleCategoryChange('news')}
        />
        
        <ResearchCategory 
          icon={<IconBrain size={20} className="text-white" />} 
          title="Experts"
          count={sourcesDiscovered.expert}
          isActive={activeCategory === 'expert'}
          isComplete={progress >= 90}
          onClick={() => handleCategoryChange('expert')}
        />
        
        <ResearchCategory 
          icon={<IconBolt size={20} className="text-white" />} 
          title="Insights"
          count={sourcesDiscovered.insights}
          isActive={activeCategory === 'insights'}
          isComplete={progress >= 95}
          onClick={() => handleCategoryChange('insights')}
        />
      </div>
      
      {/* Top sources - Enhanced section */}
      <div className="sources-header flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-300 flex items-center">
          <span className="relative">
            {activeCategory === 'academic' ? 'Academic Sources' : 
             activeCategory === 'news' ? 'News Sources' :
             activeCategory === 'expert' ? 'Expert Sources' : 'Key Insights'}
            <span className="absolute -top-1 -right-2 w-2 h-2 rounded-full bg-indigo-500 animate-ping"></span>
          </span>
        </h3>
        <div className="text-xs text-indigo-400 flex items-center gap-1 hover:text-white transition-colors cursor-pointer">
          <span>View all {sourcesDiscovered[activeCategory as keyof typeof sourcesDiscovered]}</span>
          <IconArrowRight size={12} />
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-8">
        {visibleSources.map((source, index) => (
          <SourceItem 
            key={`${activeCategory}-${index}`}
            title={source.title}
            source={source.source}
            icon={source.icon}
            index={index}
            relevance={source.relevance}
          />
        ))}
      </div>
    </div>
  );
};

export default ResearchInterface; 