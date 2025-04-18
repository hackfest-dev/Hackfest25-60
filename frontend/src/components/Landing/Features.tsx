import { Book, Brain, FileSearch, Globe, Sparkles } from "lucide-react";
import { GlowingEffect } from "../ui/glowing-effect";
import { motion } from "framer-motion";
import React, { useState } from "react";

export default function Features() {
  return (
    <div className="w-full">
      <motion.ul 
        className="grid grid-cols-1 gap-6 md:grid-cols-12 md:grid-rows-3 lg:gap-8 xl:min-h-[50rem] xl:grid-rows-2"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ staggerChildren: 0.2, delayChildren: 0.3 }}
      >
        <GridItem
          area="md:[grid-area:1/1/2/7] xl:[grid-area:1/1/2/5]"
          icon={<FileSearch className="h-5 w-5 text-black dark:text-neutral-200" />}
          title="One-Prompt Research"
          description="Input a single prompt and get a complete research paper with detailed findings and analysis."
          index={0}
        />

        <GridItem
          area="md:[grid-area:1/7/2/13] xl:[grid-area:2/1/3/5]"
          icon={<Brain className="h-5 w-5 text-black dark:text-neutral-200" />}
          title="AI-Generated Papers"
          description="Our AI autonomously crafts comprehensive research papers with proper structure and citations."
          index={1}
        />

        <GridItem
          area="md:[grid-area:2/1/3/7] xl:[grid-area:1/5/3/8]"
          icon={<Book className="h-5 w-5 text-black dark:text-neutral-200" />}
          title="Deep Literature Review"
          description="Automatically analyzes academic papers, extracting relevant information for your research topic."
          index={2}
        />

        <GridItem
          area="md:[grid-area:2/7/3/13] xl:[grid-area:1/8/2/13]"
          icon={<Globe className="h-5 w-5 text-black dark:text-neutral-200" />}
          title="Comprehensive Internet Research"
          description="Scours the web for cutting-edge information and incorporates it into your custom research paper."
          index={3}
        />

        <GridItem
          area="md:[grid-area:3/1/4/13] xl:[grid-area:2/8/3/13]"
          icon={<Sparkles className="h-5 w-5 text-black dark:text-neutral-200" />}
          title="Complete Research Reports"
          description="Delivers polished, publication-ready research papers with minimal human intervention."
          index={4}
        />
      </motion.ul>
    </div>
  );
}

interface GridItemProps {
  area: string;
  icon: React.ReactNode;
  title: string;
  description: React.ReactNode;
  index: number;
}

const GridItem = ({ area, icon, title, description, index }: GridItemProps) => {
  const [isHovered, setIsHovered] = useState(false);
  
  // Animation variants for staggered entry effects
  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: { 
        duration: 0.6,
        ease: [0.22, 1, 0.36, 1],
        delay: index * 0.1
      }
    }
  };
  
  return (
    <motion.li 
      className={`min-h-[16rem] list-none ${area}`}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.2 }}
      variants={itemVariants}
    >
      <motion.div 
        className="relative h-full rounded-2xl border border-gray-200 p-2 shadow-lg transition-all duration-300 hover:shadow-xl md:rounded-3xl md:p-3 dark:border-gray-800"
        whileHover={{ 
          y: -10, 
          boxShadow: "0 20px 30px -10px rgba(99, 102, 241, 0.3)"
        }}
        onHoverStart={() => setIsHovered(true)}
        onHoverEnd={() => setIsHovered(false)}
      >
        <GlowingEffect
          spread={60}
          glow={true}
          disabled={false}
          proximity={80}
          inactiveZone={0.01}
        />
        <div className="relative flex h-full flex-col justify-between gap-6 overflow-hidden rounded-xl bg-white/5 p-6 backdrop-blur-sm md:p-8 dark:shadow-[0px_0px_30px_0px_#2D2D2D]">
          {/* Background animated gradient */}
          <motion.div 
            className="absolute inset-0 bg-gradient-to-br from-indigo-500/10 via-purple-500/5 to-transparent z-0 opacity-0"
            animate={{
              opacity: isHovered ? 0.5 : 0,
              background: isHovered 
                ? "radial-gradient(circle at center, rgba(99, 102, 241, 0.15), rgba(0, 0, 0, 0) 70%)"
                : "radial-gradient(circle at center, rgba(99, 102, 241, 0), rgba(0, 0, 0, 0) 70%)",
            }}
            transition={{ duration: 0.5 }}
          />
          
          {/* Animated particles for hover effect */}
          {isHovered && (
            <Particles />
          )}
          
          <div className="relative flex flex-1 flex-col justify-between gap-4 z-10">
            <motion.div 
              className="w-fit rounded-lg border border-gray-300 bg-white/10 p-3 dark:border-gray-700"
              whileHover={{ 
                rotate: [0, -5, 5, 0],
                scale: 1.1,
                transition: { duration: 0.5 }
              }}
            >
              {icon}
            </motion.div>
            <div className="space-y-4">
              <motion.h3 
                className="font-sans text-xl font-bold tracking-tight text-balance text-black md:text-2xl dark:text-white"
                animate={{ 
                  color: isHovered ? "#6366f1" : "#ffffff",
                }}
                transition={{ duration: 0.3 }}
              >
                {title}
              </motion.h3>
              <p className="font-sans text-base text-gray-700 md:text-lg dark:text-gray-300">
                {description}
              </p>
              
              {/* Learn more button that appears on hover */}
              <motion.div
                initial={{ opacity: 0, y: 10, height: 0 }}
                animate={{ 
                  opacity: isHovered ? 1 : 0,
                  y: isHovered ? 0 : 10,
                  height: isHovered ? 'auto' : 0
                }}
                transition={{ duration: 0.3 }}
                className="overflow-hidden"
              >
                <button className="flex items-center text-indigo-400 hover:text-indigo-300 transition-colors mt-2 group">
                  <span>Learn more</span>
                  <svg
                    className="w-4 h-4 ml-1 transform transition-transform group-hover:translate-x-1"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                </button>
              </motion.div>
            </div>
          </div>
        </div>
      </motion.div>
    </motion.li>
  );
};

// Animated particles component for hover effects
const Particles = () => {
  const particles = Array.from({ length: 10 }).map((_, i) => ({
    id: i,
    size: Math.random() * 4 + 2,
    x: Math.random() * 100,
    y: Math.random() * 100,
    duration: Math.random() * 10 + 10
  }));
  
  return (
    <>
      {particles.map((particle) => (
        <motion.div
          key={particle.id}
          className="absolute rounded-full bg-indigo-500/30 pointer-events-none"
          style={{
            width: particle.size,
            height: particle.size,
            left: `${particle.x}%`,
            top: `${particle.y}%`,
          }}
          animate={{
            y: [0, -20, 0],
            x: [0, Math.random() * 20 - 10, 0],
            opacity: [0, 0.7, 0],
          }}
          transition={{
            duration: particle.duration,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      ))}
    </>
  );
};
