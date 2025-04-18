import React from 'react';
import { motion } from 'framer-motion';

interface LogoProps {
  name: string;
  imageUrl?: string;
  color: string;
  textColor: string;
  bgColor: string;
}

const LogoMarquee: React.FC = () => {
  // First row logos
  const topLogos: LogoProps[] = [
    { 
      name: "OpenAI", 
      color: "border-blue-500", 
      textColor: "text-white",
      bgColor: "bg-blue-600/20"
    },
    { 
      name: "Google", 
      color: "border-red-500", 
      textColor: "text-white",
      bgColor: "bg-red-600/20"
    },
    { 
      name: "Anthropic", 
      color: "border-purple-500", 
      textColor: "text-white",
      bgColor: "bg-purple-600/20"
    },
    { 
      name: "Meta AI", 
      color: "border-blue-500", 
      textColor: "text-white",
      bgColor: "bg-blue-600/20"
    },
    { 
      name: "Mistral", 
      color: "border-indigo-500", 
      textColor: "text-white",
      bgColor: "bg-indigo-600/20"
    },
    { 
      name: "Cohere", 
      color: "border-pink-500", 
      textColor: "text-white",
      bgColor: "bg-pink-600/20"
    },
    { 
      name: "Hugging Face", 
      color: "border-yellow-500", 
      textColor: "text-white",
      bgColor: "bg-yellow-600/20"
    },
    { 
      name: "Microsoft", 
      color: "border-cyan-500", 
      textColor: "text-white",
      bgColor: "bg-cyan-600/20"
    },
    { 
      name: "Amazon", 
      color: "border-orange-500", 
      textColor: "text-white",
      bgColor: "bg-orange-600/20"
    },
  ];

  // Second row logos
  const bottomLogos: LogoProps[] = [
    { name: "Ollama", color: "border-teal-500", textColor: "text-white", bgColor: "bg-teal-600/20" },
    { name: "ChatGPT", color: "border-green-500", textColor: "text-white", bgColor: "bg-green-600/20" },
    { name: "Claude", color: "border-violet-500", textColor: "text-white", bgColor: "bg-violet-600/20" },
    { name: "Gemini", color: "border-sky-500", textColor: "text-white", bgColor: "bg-sky-600/20" },
    { name: "Llama", color: "border-rose-500", textColor: "text-white", bgColor: "bg-rose-600/20" },
    { name: "Falcon", color: "border-blue-500", textColor: "text-white", bgColor: "bg-blue-600/20" },
    { name: "Bard", color: "border-lime-500", textColor: "text-white", bgColor: "bg-lime-600/20" },
    { name: "GPT-4", color: "border-indigo-500", textColor: "text-white", bgColor: "bg-indigo-600/20" },
    { name: "LLaMA 2", color: "border-amber-500", textColor: "text-white", bgColor: "bg-amber-600/20" },
    { name: "Mixtral", color: "border-purple-500", textColor: "text-white", bgColor: "bg-purple-600/20" },
    { name: "LangChain", color: "border-emerald-500", textColor: "text-white", bgColor: "bg-emerald-600/20" },
  ];

  // Duplicate logos for continuous scrolling
  const duplicatedTopLogos = [...topLogos, ...topLogos];
  const duplicatedBottomLogos = [...bottomLogos, ...bottomLogos];

  return (
    <div className="w-full py-10 md:py-16 relative overflow-hidden bg-gray-950/50 backdrop-blur-sm">
      {/* Subtle background pattern */}
      <div className="absolute inset-0 bg-grid-pattern opacity-5"></div>
      
      {/* Gradient fade on sides */}
      <div className="absolute inset-y-0 left-0 w-24 bg-gradient-to-r from-gray-950 to-transparent z-10"></div>
      <div className="absolute inset-y-0 right-0 w-24 bg-gradient-to-l from-gray-950 to-transparent z-10"></div>
      
      <div className="container mx-auto px-4 text-center mb-8">
        <h3 className="text-white text-lg font-medium mb-1">Powered by</h3>
        <p className="text-indigo-400 text-sm uppercase tracking-wider font-bold">CUTTING-EDGE AI MODELS</p>
      </div>
      
      {/* Top row - right to left */}
      <div className="relative overflow-hidden flex w-full mb-8">
        <motion.div
          className="flex whitespace-nowrap"
          animate={{ x: ["0%", "-50%"] }}
          transition={{
            duration: 40,
            ease: "linear",
            repeat: Infinity,
          }}
        >
          {duplicatedTopLogos.map((logo, index) => (
            <div key={`top-logo-${index}`} className="mx-3">
              <div 
                className={`w-40 h-16 flex items-center justify-center rounded-xl border-2 ${logo.color} ${logo.bgColor} px-5 shadow-lg shadow-black/20 relative overflow-hidden`}
                style={{
                  boxShadow: `0 4px 20px -2px rgba(0, 0, 0, 0.4), 0 0 12px ${logo.color.replace('border-', 'rgba(').replace('-500', ', 0.4)')}`
                }}
              >
                <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent"></div>
                <div className="z-10 relative">
                  <span className={`${logo.textColor} text-lg font-bold tracking-wide`}>
                    {logo.name}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </motion.div>
      </div>
      
      {/* Bottom row - left to right */}
      <div className="relative overflow-hidden flex w-full">
        <motion.div
          className="flex whitespace-nowrap"
          animate={{ x: ["-50%", "0%"] }}
          transition={{
            duration: 36,
            ease: "linear",
            repeat: Infinity,
          }}
        >
          {duplicatedBottomLogos.map((logo, index) => (
            <div key={`bottom-logo-${index}`} className="mx-3">
              <div 
                className={`w-40 h-16 flex items-center justify-center rounded-xl border-2 ${logo.color} ${logo.bgColor} px-5 shadow-lg shadow-black/20 relative overflow-hidden`}
                style={{
                  boxShadow: `0 4px 20px -2px rgba(0, 0, 0, 0.4), 0 0 12px ${logo.color.replace('border-', 'rgba(').replace('-500', ', 0.4)')}`
                }}
              >
                <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent"></div>
                <div className="z-10 relative">
                  <span className={`${logo.textColor} text-lg font-bold tracking-wide`}>
                    {logo.name}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </motion.div>
      </div>
    </div>
  );
};

export default LogoMarquee; 