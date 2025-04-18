import React, { useEffect, useRef, useState } from 'react';
import anime from 'animejs';
import { motion } from 'framer-motion';
import { Users, Globe, Award, Shield, Star, Code, Zap, BarChart, Lock, UserCheck } from 'lucide-react';

const About: React.FC = () => {
  const aboutRef = useRef<HTMLDivElement>(null);
  const statsRef = useRef<HTMLDivElement>(null);
  const teamRef = useRef<HTMLDivElement>(null);
  const [windowSize, setWindowSize] = useState({ width: window.innerWidth, height: window.innerHeight });

  useEffect(() => {
    const handleResize = () => {
      setWindowSize({ width: window.innerWidth, height: window.innerHeight });
    };
    
    window.addEventListener('resize', handleResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  useEffect(() => {
    // Create morphing background
    const morphBackground = (el: SVGPathElement) => {
      anime({
        targets: el,
        d: [
          { value: createMorphPath(0) },
          { value: createMorphPath(0.3) },
          { value: createMorphPath(0.1) },
          { value: createMorphPath(0.4) },
          { value: createMorphPath(0) },
        ],
        easing: 'easeInOutSine',
        duration: 10000,
        loop: true
      });
    };

    // Generate path for morphing background
    function createMorphPath(intensity: number) {
      const width = windowSize.width;
      const height = 300;
      const controlPoints = Math.min(Math.floor(width / 100), 10);
      let path = `M0,${height * 0.7} `;
      
      for (let i = 0; i <= controlPoints; i++) {
        const x = (width * i) / controlPoints;
        const yOffset = Math.sin((i / controlPoints) * Math.PI * 2) * intensity;
        const y = height * (0.5 + yOffset * 0.3);
        path += `${i === 0 ? 'C' : ''} ${x},${y} `;
      }
      
      path += `${width},${height * 0.7} L${width},0 L0,0 Z`;
      return path;
    }

    const morphElements = document.querySelectorAll('.morph-path');
    morphElements.forEach(el => {
      if (el instanceof SVGPathElement) {
        morphBackground(el);
      }
    });

    // Create dynamic particles
    const particlesContainer = document.querySelector('.about-particles');
    if (particlesContainer) {
      const numberOfParticles = windowSize.width < 768 ? 15 : 30;
      
      // Clear existing particles if any
      while (particlesContainer.firstChild) {
        particlesContainer.removeChild(particlesContainer.firstChild);
      }
      
      for (let i = 0; i < numberOfParticles; i++) {
        const particle = document.createElement('div');
        const size = Math.random() * 4 + 1;
        const opacity = Math.random() * 0.5 + 0.2;
        
        // Create different types of particles
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
        
        // Create more dynamic movement
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

    // Create intersection observer for scroll animations
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            // Animate the section that came into view
            if (entry.target === aboutRef.current) {
              anime({
                targets: '.about-title',
                translateY: [30, 0],
                opacity: [0, 1],
                duration: 800,
                easing: 'easeOutExpo',
              });
              
              anime({
                targets: '.about-description',
                translateY: [20, 0],
                opacity: [0, 1],
                duration: 800,
                delay: 200,
                easing: 'easeOutExpo',
              });
              
              anime({
                targets: '.about-image',
                scale: [0.95, 1],
                opacity: [0, 1],
                duration: 1000,
                delay: 400,
                easing: 'easeOutExpo',
              });
            }
            
            if (entry.target === statsRef.current) {
              anime({
                targets: '.stat-card',
                translateY: [30, 0],
                opacity: [0, 1],
                duration: 800,
                delay: anime.stagger(150),
                easing: 'easeOutExpo',
              });
            }
            
            if (entry.target === teamRef.current) {
              anime({
                targets: '.team-title',
                translateY: [30, 0],
                opacity: [0, 1],
                duration: 800,
                easing: 'easeOutExpo',
              });
              
              anime({
                targets: '.team-member',
                scale: [0.95, 1],
                translateY: [30, 0],
                opacity: [0, 1],
                duration: 800,
                delay: anime.stagger(150),
                easing: 'easeOutExpo',
              });
            }
          }
        });
      },
      { threshold: 0.1 }
    );
    
    // Observe the sections
    if (aboutRef.current) observer.observe(aboutRef.current);
    if (statsRef.current) observer.observe(statsRef.current);
    if (teamRef.current) observer.observe(teamRef.current);
    
    return () => {
      observer.disconnect();
    };
  }, [windowSize]);

  // Stagger animation for stats counting effect
  useEffect(() => {
    anime({
      targets: '.stat-number',
      innerHTML: (el: HTMLElement) => [0, el.dataset.value],
      round: 1,
      easing: 'easeInOutExpo',
      duration: 2000,
      delay: anime.stagger(200)
    });
  }, []);

  return (
    <section id="about" className="py-20 relative overflow-hidden">
      {/* Morphing background */}
      <div className="absolute inset-0 w-full overflow-hidden pointer-events-none">
        <svg className="absolute inset-0 w-full h-[300px]" viewBox={`0 0 ${windowSize.width} 300`} preserveAspectRatio="none">
          <path
            className="morph-path fill-indigo-500/5"
            d={`M0,${300 * 0.7} C${windowSize.width * 0.3},${300 * 0.3} ${windowSize.width * 0.6},${300 * 0.4} ${windowSize.width},${300 * 0.2} L${windowSize.width},0 L0,0 Z`}
          />
        </svg>
      </div>

      <div className="about-particles absolute inset-0 z-0 pointer-events-none"></div>
      
      <div className="container mx-auto px-4 relative z-10">
        {/* About Section */}
        <div ref={aboutRef} className="mb-20">
          <div className="flex flex-col lg:flex-row items-center gap-12">
            <div className="w-full lg:w-1/2">
              <h2 className="about-title text-3xl md:text-4xl font-bold mb-6 text-white opacity-0">
                About <span className="text-indigo-400">Searchify</span><span className="text-indigo-500">.AI</span>
              </h2>
              <p className="about-description text-lg text-gray-300 mb-6 opacity-0">
                Searchify.AI is revolutionizing the research process by connecting knowledge seekers with comprehensive insights through our intelligent AI platform. Founded in 2023, we've built a comprehensive solution that addresses the challenges of modern information discovery and analysis.
              </p>
              <p className="about-description text-lg text-gray-300 mb-8 opacity-0">
                Our mission is to streamline the research process, condense vast information into actionable insights, and improve efficiency for academics, professionals, and curious minds alike. With our advanced AI technology and powerful algorithms, we're making deep research simpler, faster, and more reliable.
              </p>
              <div className="about-description flex flex-wrap gap-4 opacity-0">
                <motion.button 
                  className="bg-indigo-500 hover:bg-indigo-600 text-white font-medium px-6 py-3 rounded-xl transition-all duration-300 transform hover:-translate-y-1 hover:shadow-lg hover:shadow-indigo-500/20 relative overflow-hidden group"
                  whileHover={{ scale: 1.03 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <span className="relative z-10">Learn More</span>
                  <div className="absolute inset-0 bg-gradient-to-r from-indigo-600 to-violet-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                </motion.button>
                <motion.button 
                  className="bg-gray-800 hover:bg-gray-700 text-white font-medium px-6 py-3 rounded-xl border border-gray-700 transition-all duration-300 transform hover:-translate-y-1 relative overflow-hidden group"
                  whileHover={{ scale: 1.03 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <span className="relative z-10">Our Story</span>
                  <div className="absolute inset-0 bg-gradient-to-r from-gray-800 to-gray-700 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                </motion.button>
              </div>
            </div>
            <div className="about-image w-full lg:w-1/2 opacity-0">
              <div className="relative">
                <div className="absolute -inset-4 bg-gradient-to-r from-indigo-500/20 to-violet-500/20 rounded-3xl blur-md"></div>
                <div className="relative bg-gray-900/30 backdrop-blur-sm border border-gray-800/50 rounded-2xl p-6 overflow-hidden">
                  <div className="aspect-video bg-gray-900 rounded-xl overflow-hidden">
                    <img 
                      src="https://images.unsplash.com/photo-1581089781785-603411fa81e5?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1470&q=80" 
                      alt="AI Research Team" 
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <div className="mt-4 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-indigo-400"></div>
                      <span className="text-sm text-gray-300">AI-Powered Analysis</span>
                    </div>
                    <div className="text-sm text-gray-400">Real-time Updates</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Stats Section */}
        <div ref={statsRef} className="mb-20">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { icon: <Users className="w-8 h-8 text-indigo-400" />, value: "25000", label: "Active Users" },
              { icon: <Globe className="w-8 h-8 text-indigo-400" />, value: "120", label: "Countries Served" },
              { icon: <Award className="w-8 h-8 text-indigo-400" />, value: "99", label: "Customer Satisfaction" },
              { icon: <Lock className="w-8 h-8 text-indigo-400" />, value: "100", label: "Secure Searches" }
            ].map((stat, index) => (
              <motion.div 
                key={index} 
                className="stat-card bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-xl p-6 opacity-0"
                whileHover={{ 
                  scale: 1.03, 
                  boxShadow: "0 0 20px rgba(99, 102, 241, 0.2)"
                }}
              >
                <div className="mb-4 bg-indigo-500/10 rounded-lg p-3 w-fit">
                  {stat.icon}
                </div>
                <h3 className="text-3xl font-bold text-white mb-1">
                  <span className="stat-number" data-value={stat.value}>0</span>
                  {stat.label === "Customer Satisfaction" || stat.label === "Secure Searches" ? "%" : "+"}
                </h3>
                <p className="text-gray-400">{stat.label}</p>
              </motion.div>
            ))}
          </div>
        </div>
        
        {/* Team Section */}
        <div ref={teamRef}>
          <h2 className="team-title text-3xl md:text-4xl font-bold mb-12 text-center text-white opacity-0">
            Meet Our <span className="text-indigo-400">Expert</span> Team
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {[
              { 
                name: "Dr. Alex Chen", 
                role: "Chief AI Scientist", 
                image: "https://images.unsplash.com/photo-1560250097-0b93528c311a?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=687&q=80",
                specialty: <Code className="w-4 h-4 text-indigo-400" />
              },
              { 
                name: "Dr. Sarah Lin", 
                role: "Data Science Director", 
                image: "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=688&q=80",
                specialty: <BarChart className="w-4 h-4 text-indigo-400" />
              },
              { 
                name: "Michael Rodriguez", 
                role: "UX Research Lead", 
                image: "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=687&q=80",
                specialty: <UserCheck className="w-4 h-4 text-indigo-400" />
              },
              { 
                name: "Priya Sharma", 
                role: "ML Engineering Lead", 
                image: "https://images.unsplash.com/photo-1580489944761-15a19d654956?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=761&q=80",
                specialty: <Zap className="w-4 h-4 text-indigo-400" /> 
              }
            ].map((member, index) => (
              <motion.div 
                key={index} 
                className="team-member bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 rounded-xl overflow-hidden opacity-0"
                whileHover={{ 
                  scale: 1.03, 
                  boxShadow: "0 0 20px rgba(99, 102, 241, 0.2)"
                }}
              >
                <div className="relative aspect-square overflow-hidden bg-gradient-to-br from-indigo-900/20 to-violet-900/20">
                  <img 
                    src={member.image} 
                    alt={member.name} 
                    className="w-full h-full object-cover transition-transform duration-500 hover:scale-105"
                  />
                  <div className="absolute bottom-0 right-0 bg-indigo-500/90 text-white p-2 rounded-tl-lg">
                    {member.specialty}
                  </div>
                </div>
                <div className="p-6">
                  <h3 className="text-xl font-bold text-white mb-1">{member.name}</h3>
                  <p className="text-gray-400">{member.role}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

export default About;