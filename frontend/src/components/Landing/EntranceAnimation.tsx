import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search } from 'lucide-react';
import anime from 'animejs';
import { GlowingEffect } from "../ui/glowing-effect";

const EntranceAnimation: React.FC = () => {
  const particlesRef = useRef<HTMLDivElement>(null);
  const morphingCircleRef = useRef<SVGPathElement>(null);
  const [isAnimationComplete, setIsAnimationComplete] = useState(false);
  const [windowSize, setWindowSize] = useState({ width: window.innerWidth, height: window.innerHeight });

  useEffect(() => {
    document.body.style.backgroundColor = "#030712";
    
    // Handle window resize for responsiveness
    const handleResize = () => {
      setWindowSize({ width: window.innerWidth, height: window.innerHeight });
    };
    
    window.addEventListener('resize', handleResize);
    
    // Enhanced morphing circle animation with more complex paths
    if (morphingCircleRef.current) {
      const radius = 50;
      const points = 12; // Increased points for more complex morphing
      const getPath = (offset = 0, complexity = 1) => {
        const angleStep = (Math.PI * 2) / points;
        const path = [];

        for (let i = 0; i <= points; i++) {
          const theta = i * angleStep;
          const radiusOffset = offset * Math.sin(theta * complexity) * Math.cos(theta * 2);
          const x = radius * (1 + radiusOffset) * Math.cos(theta);
          const y = radius * (1 + radiusOffset) * Math.sin(theta);
          path.push(`${i === 0 ? 'M' : 'L'} ${x + 50} ${y + 50}`);
        }
        path.push('Z');
        return path.join(' ');
      };

      anime({
        targets: morphingCircleRef.current,
        d: [
          { value: getPath(0, 1) },
          { value: getPath(0.4, 3) },
          { value: getPath(0.2, 2) },
          { value: getPath(0.3, 4) },
          { value: getPath(0, 1) }
        ],
        duration: 8000,
        easing: 'easeInOutSine',
        loop: true,
        direction: 'alternate'
      });
    }

    // Enhanced particle system with more dynamic trails
    if (particlesRef.current) {
      const particlesContainer = particlesRef.current;
      // Adjust particles based on screen size
      const numberOfParticles = windowSize.width < 768 ? 10 : 20;
      
      for (let i = 0; i < numberOfParticles; i++) {
        const particle = document.createElement('div');
        const trail = document.createElement('div');
        const size = Math.random() * 4 + 1;
        
        trail.className = 'absolute w-12 h-1.5 rounded-full bg-gradient-to-r from-indigo-500/0 via-indigo-500/40 to-transparent backdrop-blur-sm';
        particle.className = 'absolute rounded-full bg-indigo-400 shadow-lg shadow-indigo-500/50';
        
        particle.style.width = `${size}px`;
        particle.style.height = `${size}px`;
        trail.style.opacity = '0';
        
        particlesContainer.appendChild(trail);
        particlesContainer.appendChild(particle);
        
        // Adjust animation range based on screen size
        const rangeX = windowSize.width < 768 ? 100 : 200;
        const rangeY = windowSize.width < 768 ? 100 : 200;
        
        const randomX = anime.random(0, windowSize.width);
        const randomY = anime.random(0, windowSize.height);
        
        // Apply animation to particle
        anime({
          targets: particle,
          translateX: [
            randomX,
            randomX + anime.random(-rangeX, rangeX)
          ],
          translateY: [
            randomY,
            randomY + anime.random(-rangeY, rangeY)
          ],
          scale: [
            1,
            { value: 2.5, duration: 1500 },
            { value: 1, duration: 1500 }
          ],
          opacity: [0, 1],
          easing: 'easeInOutQuad',
          duration: 6000,
          loop: true,
          direction: 'alternate'
        });
        
        // Apply animation to trail
        anime({
          targets: trail,
          opacity: [0, 0.6, 0],
          translateX: randomX,
          translateY: randomY,
          rotate: () => anime.random(-60, 60),
          scale: [1, 1.2, 1],
          easing: 'easeInOutSine',
          duration: 6000,
          loop: true,
          direction: 'alternate'
        });
      }
    }

    const entranceAnimation = anime.timeline({
      easing: 'easeOutExpo',
      complete: () => setIsAnimationComplete(true)
    });

    // Enhanced staggered letter animation
    const letters = document.querySelectorAll('.entrance-text .letter');
    letters.forEach((letter: Element) => {
      if (letter instanceof HTMLElement) {
        letter.style.transform = 'translateY(-100%) rotate(-15deg) scale(0.8)';
        letter.style.opacity = '0';
      }
    });

    entranceAnimation
      .add({
        targets: '.entrance-logo',
        scale: [0, 1],
        opacity: [0, 1],
        rotate: [360, 0],
        duration: 2000,
        easing: 'spring(1, 90, 12, 0)'
      })
      .add({
        targets: '.entrance-text .letter',
        translateY: ['-100%', '0%'],
        rotate: [-15, 0],
        scale: [0.8, 1],
        opacity: [0, 1],
        duration: 1200,
        delay: anime.stagger(80),
        easing: 'spring(1, 90, 8, 0)'
      }, '-=1500')
      .add({
        targets: '.entrance-subtitle',
        clipPath: ['polygon(0 0, 0 0, 0 100%, 0% 100%)', 'polygon(0 0, 100% 0, 100% 100%, 0 100%)'],
        opacity: [0, 1],
        duration: 1200,
        easing: 'easeOutExpo'
      }, '-=800');

    // Enhanced loading dots animation
    anime({
      targets: '.loading-dot',
      scale: [1, 1.8],
      opacity: [0.3, 1],
      duration: 800,
      loop: true,
      direction: 'alternate',
      delay: anime.stagger(200),
      easing: 'easeInOutQuad'
    });

    return () => {
      anime.remove('.entrance-logo');
      anime.remove('.entrance-text .letter');
      anime.remove('.entrance-subtitle');
      anime.remove('.loading-dot');
      anime.remove(morphingCircleRef.current);
      window.removeEventListener('resize', handleResize);
    };
  }, [windowSize.width, windowSize.height]);

  return (
    <AnimatePresence>
      {!isAnimationComplete ? (
        <motion.div 
          className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-gray-950 overflow-hidden"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.5, exit: { duration: 0.8 } }}
        >
          <div className="entrance-particles absolute inset-0 z-0" ref={particlesRef}></div>
          
          <div className="absolute inset-0 bg-gradient-to-b from-transparent via-gray-950/50 to-gray-950 z-[1]"></div>
          
          <div className="relative z-10 container mx-auto px-4 sm:px-6 flex flex-col items-center">
            <div className="entrance-logo text-center space-y-6 md:space-y-8">
              <div className="relative inline-block">
                <svg className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-24 h-24 md:w-32 lg:w-40 lg:h-40" viewBox="0 0 100 100">
                  <path
                    ref={morphingCircleRef}
                    className="fill-indigo-500/20"
                    d="M50,0 A50,50 0 1,1 50,100 A50,50 0 1,1 50,0"
                  />
                </svg>
                <div className="relative">
                  <GlowingEffect
                    spread={windowSize.width < 768 ? 40 : 80}
                    glow={true}
                    disabled={false}
                    proximity={windowSize.width < 768 ? 60 : 100}
                    inactiveZone={0.01}
                  />
                  <Search className="w-12 h-12 sm:w-16 sm:h-16 md:w-20 md:h-20 text-indigo-400" />
                </div>
              </div>
              
              <h1 className="entrance-text relative text-4xl sm:text-5xl md:text-6xl lg:text-7xl xl:text-8xl font-bold tracking-tight text-white overflow-hidden">
                <span className="relative inline-block">
                  {'SEARCHIFY'.split('').map((letter, index) => (
                    <span key={index} className="letter relative inline-block">{letter}</span>
                  ))}
                  <span className="text-indigo-500">
                    {'.AI'.split('').map((letter, index) => (
                      <span key={index} className="letter relative inline-block">{letter}</span>
                    ))}
                  </span>
                </span>
              </h1>
              
              <p className="entrance-subtitle text-lg sm:text-xl md:text-2xl lg:text-3xl text-gray-300 font-light max-w-xs sm:max-w-lg md:max-w-2xl lg:max-w-3xl text-center">
                The intelligent research engine
              </p>
            </div>

            <div className="mt-8 sm:mt-12 md:mt-16 flex justify-center space-x-2 sm:space-x-3 md:space-x-4">
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  className="loading-dot w-2 h-2 sm:w-3 sm:h-3 md:w-4 md:h-4 rounded-full bg-indigo-500/60 backdrop-blur-sm shadow-lg shadow-indigo-500/30"
                  style={{ animationDelay: `${i * 0.2}s` }}
                ></div>
              ))}
            </div>
          </div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
};

export default EntranceAnimation;
