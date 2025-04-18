import React, { useEffect, useRef } from 'react';
import { Facebook, Twitter, Instagram, Linkedin, Mail, Phone, MapPin, Github, Youtube, ArrowRight, Heart, Shield, Gift } from 'lucide-react';
import { motion } from 'framer-motion';
import anime from 'animejs';

export default function Footer() {
  const footerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            // Footer entrance animation
            anime({
              targets: '.footer-col',
              translateY: [30, 0],
              opacity: [0, 1],
              duration: 800,
              delay: anime.stagger(100),
              easing: 'easeOutExpo',
            });
            
            anime({
              targets: '.footer-bottom',
              translateY: [20, 0],
              opacity: [0, 1],
              duration: 800,
              delay: 500,
              easing: 'easeOutExpo',
            });
          }
        });
      },
      { threshold: 0.1 }
    );
    
    if (footerRef.current) observer.observe(footerRef.current);
    
    return () => {
      observer.disconnect();
    };
  }, []);

  return (
    <footer ref={footerRef} className="w-full border-t border-gray-800 relative overflow-hidden">
      {/* Decorative elements */}
      <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-indigo-500/50 to-transparent"></div>
      <motion.div 
        className="absolute -top-32 -left-32 w-64 h-64 rounded-full bg-indigo-500/5 blur-3xl"
        animate={{
          opacity: [0.3, 0.5, 0.3],
          scale: [1, 1.2, 1],
        }}
        transition={{
          duration: 15,
          repeat: Infinity,
          repeatType: "reverse",
          ease: "easeInOut"
        }}
      />
      <motion.div 
        className="absolute -bottom-32 -right-32 w-64 h-64 rounded-full bg-indigo-500/5 blur-3xl"
        animate={{
          opacity: [0.2, 0.4, 0.2],
          scale: [1, 1.3, 1],
        }}
        transition={{
          duration: 18,
          repeat: Infinity,
          repeatType: "reverse",
          ease: "easeInOut"
        }}
      />
      
      <div className="container mx-auto px-4 py-12 relative z-10">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12 mb-16">
          <div className="footer-col">
            <div className="flex items-center mb-6">
              <h3 className="text-2xl font-bold">
                <span className="text-white">Searchify</span>
                <span className="text-indigo-500">.AI</span>
              </h3>
            </div>
            <p className="text-gray-400 mb-6">
              Empowering researchers with AI-driven insights and comprehensive knowledge discovery.
            </p>
            <div className="flex space-x-4">
              {[
                { icon: <Facebook className="w-5 h-5" />, color: 'hover:text-indigo-400' },
                { icon: <Twitter className="w-5 h-5" />, color: 'hover:text-indigo-400' },
                { icon: <Instagram className="w-5 h-5" />, color: 'hover:text-indigo-400' },
                { icon: <Linkedin className="w-5 h-5" />, color: 'hover:text-indigo-400' },
                { icon: <Github className="w-5 h-5" />, color: 'hover:text-indigo-400' },
              ].map((social, index) => (
                <motion.a 
                  key={index} 
                  href="#" 
                  className={`${social.color} transition-all p-2 bg-gray-900/50 rounded-full border border-gray-800/50`}
                  whileHover={{ y: -3, scale: 1.1 }}
                  whileTap={{ scale: 0.95 }}
                >
                  {social.icon}
                </motion.a>
              ))}
            </div>
          </div>
          
          <div className="footer-col">
            <h4 className="text-lg font-semibold mb-6 text-white">Quick Links</h4>
            <ul className="space-y-3">
              {[
                'Home', 'About Us', 'Features', 'Pricing', 'Blog', 'Contact'
              ].map((link, index) => (
                <li key={index}>
                  <motion.a 
                    href="#" 
                    className="text-gray-400 hover:text-indigo-400 transition-colors flex items-center group"
                    whileHover={{ x: 5 }}
                  >
                    <span className="transform transition-transform group-hover:translate-x-1">{link}</span>
                    <ArrowRight className="w-3 h-3 ml-1 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </motion.a>
                </li>
              ))}
            </ul>
          </div>
          
          <div className="footer-col">
            <h4 className="text-lg font-semibold mb-6 text-white">Services</h4>
            <ul className="space-y-3">
              {[
                'Deep Research', 'Academic Analysis', 'Scientific Literature', 'Market Reports', 'Custom Insights', 'Data Visualization'
              ].map((service, index) => (
                <li key={index}>
                  <motion.a 
                    href="#" 
                    className="text-gray-400 hover:text-indigo-400 transition-colors flex items-center group"
                    whileHover={{ x: 5 }}
                  >
                    <span className="transform transition-transform group-hover:translate-x-1">{service}</span>
                    <ArrowRight className="w-3 h-3 ml-1 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </motion.a>
                </li>
              ))}
            </ul>
          </div>
          
          <div className="footer-col">
            <h4 className="text-lg font-semibold mb-6 text-white">Contact Us</h4>
            <ul className="space-y-4">
              <li className="flex items-start">
                <Mail className="w-5 h-5 mr-3 text-indigo-400 flex-shrink-0 mt-0.5" />
                <span className="text-gray-400">contact@searchify.ai</span>
              </li>
              <li className="flex items-start">
                <Phone className="w-5 h-5 mr-3 text-indigo-400 flex-shrink-0 mt-0.5" />
                <span className="text-gray-400">+91 (999) 888-7777</span>
              </li>
              <li className="flex items-start">
                <MapPin className="w-5 h-5 mr-3 text-indigo-400 flex-shrink-0 mt-0.5" />
                <span className="text-gray-400">123 AI Avenue, Bangalore, India 560001</span>
              </li>
            </ul>
            
            <div className="mt-6">
              <h5 className="text-white font-medium mb-3">Subscribe to Newsletter</h5>
              <div className="flex">
                <input 
                  type="email" 
                  placeholder="Your email" 
                  className="bg-gray-900/70 border border-gray-800 rounded-l-lg px-4 py-2 focus:outline-none focus:border-indigo-500 text-gray-300 w-full"
                />
                <motion.button 
                  className="bg-indigo-500 hover:bg-indigo-600 text-white px-4 rounded-r-lg transition-colors flex items-center justify-center"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <ArrowRight className="w-5 h-5" />
                </motion.button>
              </div>
            </div>
          </div>
        </div>
        
        <div className="footer-bottom border-t border-gray-900 pt-8 opacity-0">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <p className="text-gray-400 text-sm mb-4 md:mb-0">
              © {new Date().getFullYear()} Searchify.AI. All rights reserved.
            </p>
            <div className="flex flex-wrap justify-center gap-x-6 gap-y-2">
              <motion.a 
                href="#" 
                className="text-gray-400 hover:text-indigo-400 text-sm transition-colors"
                whileHover={{ x: 2 }}
              >
                Privacy Policy
              </motion.a>
              <motion.a 
                href="#" 
                className="text-gray-400 hover:text-indigo-400 text-sm transition-colors"
                whileHover={{ x: 2 }}
              >
                Terms of Service
              </motion.a>
              <motion.a 
                href="#" 
                className="text-gray-400 hover:text-indigo-400 text-sm transition-colors"
                whileHover={{ x: 2 }}
              >
                Cookie Policy
              </motion.a>
              <motion.a 
                href="#" 
                className="text-gray-400 hover:text-indigo-400 text-sm transition-colors"
                whileHover={{ x: 2 }}
              >
                Sitemap
              </motion.a>
            </div>
          </div>
          
          <div className="mt-6 flex flex-col md:flex-row items-center justify-center md:justify-between text-xs text-gray-500">
            <div className="flex items-center mb-3 md:mb-0">
              <Shield className="w-4 h-4 mr-1 text-indigo-400/70" />
              <span>Secure Payment</span>
              <span className="mx-2">•</span>
              <Gift className="w-4 h-4 mr-1 text-indigo-400/70" />
              <span>Free Trial Available</span>
            </div>
            <div className="flex items-center">
              <span>Made with</span>
              <motion.div
                animate={{
                  scale: [1, 1.2, 1],
                }}
                transition={{
                  duration: 1.5,
                  repeat: Infinity,
                  repeatType: "reverse",
                  ease: "easeInOut"
                }}
              >
                <Heart className="w-3 h-3 mx-1 text-pink-500" />
              </motion.div>
              <span>by Searchify Team</span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}