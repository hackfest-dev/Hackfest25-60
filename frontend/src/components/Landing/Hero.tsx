import React, { useEffect, useRef, useState } from 'react';
import anime from 'animejs';
import { motion } from 'framer-motion';
import { Search, Database, Globe, Brain, ChevronDown, ArrowRight, LogIn, UserPlus, Sparkles, Zap, Code, Share2, Star, BarChart } from 'lucide-react';
import { Link } from 'react-router-dom';
import { GlowingEffect } from "../ui/glowing-effect";

const Hero: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const particlesRef = useRef<HTMLDivElement>(null);
  const morphRef = useRef<SVGPathElement>(null);
  const progressRef = useRef<HTMLDivElement>(null);
  const [windowSize, setWindowSize] = useState({ width: window.innerWidth, height: window.innerHeight });
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    document.body.style.backgroundColor = "#030712";
    
    const handleResize = () => {
      setWindowSize({ width: window.innerWidth, height: window.innerHeight });
    };
    
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };
    
    window.addEventListener('resize', handleResize);
    window.addEventListener('scroll', handleScroll);
    
    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  useEffect(() => {
    // Create advanced morphing background paths
    if (morphRef.current) {
      const width = window.innerWidth;
      const height = window.innerHeight * 0.5;
      
      const generateCurve = (complexity: number, amplitude: number) => {
        const midX = width / 2;
        const pointsCount = Math.min(Math.floor(width / 100), 12); // Adaptive point count
        let path = `M0,${height} `;
        
        for (let i = 0; i <= pointsCount; i++) {
          const x = (width * i) / pointsCount;
          const yOffset = Math.sin((i / pointsCount) * Math.PI * complexity) * amplitude;
          const y = Math.max(0, height - yOffset * (height * 0.7)); // Prevent negative values
          path += `${i === 0 ? 'C' : ''} ${x},${y} `;
        }
        
        path += `${width},${height} L${width},0 L0,0 Z`;
        return path;
      };
      
      anime({
        targets: morphRef.current,
        d: [
          { value: generateCurve(2, 0.6) },
          { value: generateCurve(3, 0.3) },
          { value: generateCurve(2.5, 0.7) },
          { value: generateCurve(1.5, 0.5) },
          { value: generateCurve(2, 0.6) }
        ],
        easing: 'easeInOutSine',
        duration: 12000,
        loop: true
      });
    }

    // Enhanced particles with interactive behavior
    if (particlesRef.current) {
      const particlesContainer = particlesRef.current;
      const numberOfParticles = windowSize.width < 768 ? 20 : 40;
      
      // Clear previous particles if needed
      while (particlesContainer.firstChild) {
        particlesContainer.removeChild(particlesContainer.firstChild);
      }
      
      for (let i = 0; i < numberOfParticles; i++) {
        const particle = document.createElement('div');
        const size = Math.random() * 5 + 1;
        const opacity = Math.random() * 0.5 + 0.2;
        
        // Create different types of particles for visual variety
        const particleType = Math.floor(Math.random() * 4);
        let className = 'absolute rounded-full backdrop-blur-sm ';
        
        switch (particleType) {
          case 0:
            className += 'bg-indigo-400/30';
            break;
          case 1:
            className += 'bg-violet-400/30';
            break;
          case 2:
            className += 'bg-blue-400/30';
            break;
          default:
            className += 'bg-sky-400/30';
        }
        
        particle.className = className;
        particle.style.width = `${size}px`;
        particle.style.height = `${size}px`;
        particle.style.left = `${Math.random() * 100}%`;
        particle.style.top = `${Math.random() * 100}%`;
        particle.style.opacity = opacity.toString();
        
        particlesContainer.appendChild(particle);
        
        // Create more dynamic movement with variable speeds and directions
        const duration = anime.random(3000, 8000);
        const delay = anime.random(0, 2000);
        
        anime({
          targets: particle,
          translateX: () => {
            const range = windowSize.width < 768 ? 150 : 250;
            return anime.random(-range, range);
          },
          translateY: () => {
            const range = windowSize.width < 768 ? 150 : 250;
            return anime.random(-range, range);
          },
          scale: [
            { value: 1 },
            { value: anime.random(1.5, 3), duration: duration / 2 },
            { value: 1, duration: duration / 2 }
          ],
          opacity: [
            { value: opacity, duration: 0 },
            { value: anime.random(0.5, 0.9), duration: duration / 2 },
            { value: opacity, duration: duration / 2 }
          ],
          rotate: () => anime.random(-360, 360),
          easing: 'easeInOutQuad',
          duration: duration,
          loop: true,
          delay: delay
        });
      }
    }

    // Advanced hero animation sequence
    const heroAnimation = anime.timeline({
      easing: 'easeOutExpo',
    });

    // Create staggered title animation with layered effects
    const title = document.querySelector('.hero-title');
    if (title instanceof HTMLElement) {
      // Split letters into individual spans
      const titleText = title.textContent || '';
      title.innerHTML = '';
      
      titleText.split('').forEach((char, index) => {
        const span = document.createElement('span');
        span.className = 'letter inline-block relative';
        span.textContent = char;
        span.style.opacity = '0';
        span.style.transform = 'translateY(-20px) rotate(-5deg) scale(0.8)';
        title.appendChild(span);
      });
    }

    heroAnimation
      .add({
        targets: '.hero-morphing-bg',
        opacity: [0, 1],
        duration: 1000,
        easing: 'easeOutQuad'
      })
      .add({
        targets: '.hero-title .letter',
        translateY: ['-20px', '0px'],
        rotate: [-5, 0],
        scale: [0.8, 1],
        opacity: [0, 1],
        duration: 1200,
        delay: anime.stagger(60),
        easing: 'spring(1, 90, 10, 0)'
      }, '-=800')
      .add({
        targets: '.hero-subtitle',
        clipPath: ['polygon(0 0, 0 0, 0 100%, 0% 100%)', 'polygon(0 0, 100% 0, 100% 100%, 0 100%)'],
        opacity: [0, 1],
        duration: 800,
        easing: 'easeOutQuint'
      }, '-=800')
      .add({
        targets: '.hero-cta',
        translateY: [40, 0],
        opacity: [0, 1],
        duration: 600,
        delay: anime.stagger(150)
      }, '-=600')
      .add({
        targets: '.hero-feature',
        scale: [0.9, 1],
        translateY: [20, 0],
        opacity: [0, 1],
        duration: 800,
        delay: anime.stagger(80),
        easing: 'spring(1, 80, 10, 0)'
      }, '-=400')
      .add({
        targets: '.hero-graphic',
        translateX: [50, 0],
        translateY: [20, 0],
        opacity: [0, 1],
        duration: 1000,
        easing: 'easeOutElastic(1, .6)'
      }, '-=800');

    // Interactive floating animation for features
    anime({
      targets: '.hero-feature',
      translateY: (el: HTMLElement, i: number) => [-4 - i, 4 + i],
      translateX: (el: HTMLElement, i: number) => [i - 2, 2 - i],
      rotate: (el: HTMLElement, i: number) => [i * 0.5, -i * 0.5],
      duration: 4000,
      direction: 'alternate',
      loop: true,
      delay: anime.stagger(200),
      easing: 'easeInOutSine'
    });

    // Animated progress bar
    if (progressRef.current) {
      anime({
        targets: progressRef.current,
        width: ['0%', '67%'],
        duration: 2000,
        delay: 1500,
        easing: 'easeInOutQuart',
        loop: false
      });
    }

    // Enhanced glowing dots animation with pulse effect
    anime({
      targets: '.glow-dot',
      scale: [1, 1.5],
      opacity: [0.3, 0.8],
      boxShadow: [
        '0 0 0 rgba(129, 140, 248, 0)',
        '0 0 15px rgba(129, 140, 248, 0.5)'
      ],
      duration: 1000,
      direction: 'alternate',
      loop: true,
      delay: anime.stagger(200),
      easing: 'easeInOutSine'
    });
    
    // Continuous micro-animations for subtle ongoing movement
    anime({
      targets: '.micro-animation',
      translateY: (el: HTMLElement, i: number) => [i % 2 === 0 ? -3 : 3, i % 2 === 0 ? 3 : -3],
      rotate: (el: HTMLElement, i: number) => [i % 2 === 0 ? -1 : 1, i % 2 === 0 ? 1 : -1],
      duration: 3000,
      direction: 'alternate',
      loop: true,
      easing: 'easeInOutQuad',
      delay: anime.stagger(400)
    });
    
    // Scrolling hint animation to encourage exploration
    anime({
      targets: '.scroll-hint',
      translateY: [0, 10],
      opacity: [0.7, 0.3],
      duration: 1500,
      direction: 'alternate',
      loop: true,
      easing: 'easeInOutQuad'
    });
  }, [windowSize.width]);

  return (
    <div className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden">
      {/* Responsive Morphing background */}
      <div className="hero-morphing-bg absolute inset-0 w-full overflow-hidden pointer-events-none">
        <svg className="absolute inset-0 w-full h-full" viewBox={`0 0 ${windowSize.width} ${windowSize.height * 0.5}`} preserveAspectRatio="none">
          <path
            ref={morphRef}
            className="fill-indigo-500/5"
            d={`M0,${windowSize.height * 0.5} C${windowSize.width * 0.3},${windowSize.height * 0.3} ${windowSize.width * 0.6},${windowSize.height * 0.4} ${windowSize.width},${windowSize.height * 0.2} L${windowSize.width},0 L0,0 Z`}
          />
        </svg>
      </div>

      <div ref={particlesRef} className="absolute inset-0 z-0 pointer-events-none"></div>
      
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-gray-950/50 to-gray-950 z-[1] pointer-events-none"></div>
      
      <div className="relative z-10 container mx-auto px-4 sm:px-6 py-16 flex flex-col items-center lg:items-start">
        <div className="w-full grid grid-cols-1 lg:grid-cols-2 gap-8 md:gap-12 lg:gap-16 items-center">
          <div className="space-y-6 md:space-y-8 text-center lg:text-left order-2 lg:order-1">
            <div className="space-y-4">
              <h1 className="hero-title relative text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight text-white">
                SEARCHIFY<span className="text-indigo-500">.AI</span>
              </h1>
              <p className="hero-subtitle text-xl sm:text-2xl text-gray-300 font-light max-w-2xl">
                Deep research made simple. One prompt, one comprehensive report.
              </p>
            </div>

            <div className="hero-cta flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-4">
              <Link to="/signup" className="w-full sm:w-auto">
                <motion.button 
                  className="group w-full bg-indigo-500 hover:bg-indigo-600 text-white px-6 py-3 sm:px-8 sm:py-4 rounded-xl font-medium transition-all duration-300 transform hover:-translate-y-1 hover:shadow-lg hover:shadow-indigo-500/25 relative overflow-hidden"
                  whileHover={{ scale: 1.03 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <span className="flex items-center justify-center gap-2 relative z-10">
                    <UserPlus className="w-5 h-5 transition-transform group-hover:scale-110" />
                    <span>Get Started</span>
                  </span>
                  <div className="absolute inset-0 bg-gradient-to-r from-indigo-600 to-violet-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                </motion.button>
              </Link>
              <Link to="/login" className="w-full sm:w-auto">
                <motion.button 
                  className="group w-full px-6 py-3 sm:px-8 sm:py-4 rounded-xl font-medium border border-gray-700 hover:border-indigo-500/50 text-white transition-all duration-300 relative overflow-hidden"
                  whileHover={{ scale: 1.03 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <span className="flex items-center justify-center gap-2 relative z-10">
                    <LogIn className="w-5 h-5 transition-transform group-hover:rotate-12" />
                    <span>Login</span>
                  </span>
                  <div className="absolute inset-0 bg-gradient-to-r from-gray-900 to-gray-800 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                </motion.button>
              </Link>
            </div>

            <div className="grid grid-cols-2 gap-3 sm:gap-4 md:gap-6">
              {[
                {icon: <Database className="w-5 h-5 sm:w-6 sm:h-6 text-indigo-400" />, text: "Knowledge Base"},
                {icon: <Brain className="w-5 h-5 sm:w-6 sm:h-6 text-indigo-400" />, text: "AI Analysis"},
                {icon: <Globe className="w-5 h-5 sm:w-6 sm:h-6 text-indigo-400" />, text: "Web Crawling"},
                {icon: <Search className="w-5 h-5 sm:w-6 sm:h-6 text-indigo-400" />, text: "Smart Reports"}
              ].map((feature, index) => (
                <motion.div 
                  key={index} 
                  className="hero-feature flex items-center gap-3 p-3 sm:p-4 rounded-xl bg-gray-900/30 backdrop-blur-sm border border-gray-800/50 hover:border-indigo-500/50 transition-all duration-300"
                  whileHover={{ 
                    scale: 1.03, 
                    boxShadow: "0 0 20px rgba(99, 102, 241, 0.15)"
                  }}
                >
                  <div className="flex-shrink-0 micro-animation">
                    {feature.icon}
                  </div>
                  <span className="text-gray-300 text-sm sm:text-base">{feature.text}</span>
                </motion.div>
              ))}
            </div>
            
            <div className="hidden md:flex items-center justify-center lg:justify-start text-gray-500 text-sm scroll-hint">
              <span className="mr-2">Explore more</span>
              <ChevronDown className="w-4 h-4 animate-bounce" />
            </div>
          </div>

          <div className="w-full relative hero-graphic order-1 lg:order-2">
            <motion.div 
              className="relative rounded-2xl overflow-hidden shadow-2xl shadow-indigo-500/10"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5, duration: 0.8 }}
            >
              <GlowingEffect
                spread={windowSize.width < 768 ? 40 : 80}
                glow={true}
                disabled={false}
                proximity={windowSize.width < 768 ? 60 : 100}
                inactiveZone={0.01}
              />
              <div className="relative bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-2xl p-4 sm:p-6 md:p-8">
                <div className="space-y-6 sm:space-y-8">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="glow-dot w-6 h-6 sm:w-8 sm:h-8 rounded-full bg-indigo-500/20 flex items-center justify-center">
                        <Search className="w-3 h-3 sm:w-4 sm:h-4 text-indigo-400" />
                      </div>
                      <span className="text-white font-medium text-sm sm:text-base">Research Query</span>
                    </div>
                    <div className="flex gap-2">
                      <div className="w-2 h-2 sm:w-2.5 sm:h-2.5 rounded-full bg-red-500/80 backdrop-blur-sm"></div>
                      <div className="w-2 h-2 sm:w-2.5 sm:h-2.5 rounded-full bg-amber-500/80 backdrop-blur-sm"></div>
                      <div className="w-2 h-2 sm:w-2.5 sm:h-2.5 rounded-full bg-green-500/80 backdrop-blur-sm"></div>
                    </div>
                  </div>
                  
                  <div className="space-y-5 sm:space-y-6">
                    <div className="bg-gray-800/30 backdrop-blur-sm rounded-xl p-3 sm:p-4 md:p-6">
                      <p className="text-gray-400 text-xs sm:text-sm mb-2 sm:mb-3">Query:</p>
                      <p className="text-white font-medium text-sm sm:text-base">Analyze quantum computing's impact on cryptography and future security.</p>
                    </div>
                    
                    <div className="flex items-center justify-between p-3 sm:p-4 bg-gray-800/20 backdrop-blur-sm rounded-xl">
                      <div className="flex items-center gap-2 sm:gap-3">
                        <div className="glow-dot w-5 h-5 sm:w-6 sm:h-6 rounded-full bg-indigo-500/20 flex items-center justify-center">
                          <Database className="w-2.5 h-2.5 sm:w-3 sm:h-3 text-indigo-400" />
                        </div>
                        <span className="text-gray-300 text-xs sm:text-sm">Processing <span className="text-white font-medium">42</span> sources</span>
                      </div>
                      <div className="text-indigo-400 text-xs font-medium">In Progress</div>
                    </div>
                    
                    <div className="space-y-2">
                      <div className="h-1.5 bg-gray-800/30 rounded-full overflow-hidden">
                        <div ref={progressRef} className="h-full w-0 bg-gradient-to-r from-indigo-600 to-violet-500 rounded-full"></div>
                      </div>
                      <div className="flex justify-between text-xs text-gray-500">
                        <span>Analyzing data</span>
                        <span>67%</span>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-2 sm:gap-3">
                      {[
                        {icon: <Star className="w-3 h-3 sm:w-4 sm:h-4" />, text: "Academic Sources"},
                        {icon: <BarChart className="w-3 h-3 sm:w-4 sm:h-4" />, text: "Trend Analysis"},
                        {icon: <Share2 className="w-3 h-3 sm:w-4 sm:h-4" />, text: "Expert Opinions"},
                        {icon: <Sparkles className="w-3 h-3 sm:w-4 sm:h-4" />, text: "Key Insights"}
                      ].map((feature, index) => (
                        <motion.div 
                          key={index} 
                          className="micro-animation flex items-center gap-2 p-2 sm:p-3 rounded-lg bg-gray-800/20 backdrop-blur-sm border border-gray-800/50"
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: 0.8 + (index * 0.1), duration: 0.5 }}
                        >
                          <div className="flex-shrink-0 text-indigo-400">
                            {feature.icon}
                          </div>
                          <span className="text-gray-300 text-xs sm:text-sm">{feature.text}</span>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Added floating elements for visual interest */}
            <div className="absolute -top-8 -right-8 w-24 h-24 rounded-full bg-indigo-500/5 backdrop-blur-md border border-indigo-500/10 hidden md:block"></div>
            <div className="absolute -bottom-4 -left-4 w-16 h-16 rounded-full bg-violet-500/5 backdrop-blur-md border border-violet-500/10 hidden md:block"></div>
          </div>
        </div>
      </div>
      
      {/* Additional decorative elements */}
      <div className="absolute top-1/4 right-[10%] w-1 h-20 bg-gradient-to-b from-indigo-500/0 via-indigo-500/20 to-indigo-500/0 hidden lg:block"></div>
      <div className="absolute bottom-1/4 left-[10%] w-1 h-20 bg-gradient-to-b from-indigo-500/0 via-indigo-500/20 to-indigo-500/0 hidden lg:block"></div>
    </div>
  );
};

export default Hero;