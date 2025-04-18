import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { Search, Mail, Lock, Eye, EyeOff, ArrowRight, Home, AlertCircle } from 'lucide-react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import anime from 'animejs';

const Login: React.FC = () => {
  const { login, isAuthenticated, isLoading } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const particlesRef = useRef<HTMLDivElement>(null);
  const formRef = useRef<HTMLFormElement>(null);
  const logoRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  useEffect(() => {
    document.body.style.backgroundColor = "#030712";
  }, []);

  // Setup background animations
  useEffect(() => {
    // Create particle animations
    if (particlesRef.current) {
      const particlesContainer = particlesRef.current;
      const numberOfParticles = window.innerWidth < 768 ? 20 : 40;
      
      // Clear any existing particles
      while (particlesContainer.firstChild) {
        particlesContainer.removeChild(particlesContainer.firstChild);
      }
      
      for (let i = 0; i < numberOfParticles; i++) {
        const particle = document.createElement('div');
        const size = Math.random() * 4 + 1;
        const opacity = Math.random() * 0.5 + 0.1;
        
        const particleType = Math.floor(Math.random() * 3);
        let className = 'absolute rounded-full backdrop-blur-sm ';
        
        switch (particleType) {
          case 0:
            className += 'bg-indigo-400/20';
            break;
          case 1:
            className += 'bg-indigo-500/20';
            break;
          default:
            className += 'bg-violet-400/20';
        }
        
        particle.className = className;
        particle.style.width = `${size}px`;
        particle.style.height = `${size}px`;
        particle.style.left = `${Math.random() * 100}%`;
        particle.style.top = `${Math.random() * 100}%`;
        particle.style.opacity = opacity.toString();
        
        particlesContainer.appendChild(particle);
        
        const duration = anime.random(5000, 10000);
        const delay = anime.random(0, 2000);
        
        anime({
          targets: particle,
          translateX: () => {
            const range = window.innerWidth < 768 ? 150 : 250;
            return anime.random(-range, range);
          },
          translateY: () => {
            const range = 150;
            return anime.random(-range, range);
          },
          scale: [
            { value: 1 },
            { value: anime.random(1.2, 2.5), duration: duration / 2 },
            { value: 1, duration: duration / 2 }
          ],
          opacity: [
            { value: opacity, duration: 0 },
            { value: anime.random(0.3, 0.7), duration: duration / 2 },
            { value: opacity, duration: duration / 2 }
          ],
          easing: 'easeInOutQuad',
          duration: duration,
          loop: true,
          delay: delay
        });
      }
    }
    
    // Logo animation
    if (logoRef.current) {
      anime({
        targets: logoRef.current,
        scale: [0.95, 1.05],
        boxShadow: [
          '0 0 0 rgba(99, 102, 241, 0)',
          '0 0 20px rgba(99, 102, 241, 0.5)'
        ],
        duration: 2000,
        direction: 'alternate',
        loop: true,
        easing: 'easeInOutQuad'
      });
    }
    
    // Form entrance animation
    if (formRef.current) {
      anime.timeline({
        easing: 'easeOutExpo',
      })
      .add({
        targets: '.login-logo',
        translateY: [-30, 0],
        opacity: [0, 1],
        duration: 1000,
        delay: 300
      })
      .add({
        targets: '.login-title',
        translateY: [-20, 0],
        opacity: [0, 1],
        duration: 800
      }, '-=700')
      .add({
        targets: '.login-subtitle',
        translateY: [-20, 0],
        opacity: [0, 1],
        duration: 800
      }, '-=600')
      .add({
        targets: '.form-field',
        translateY: [20, 0],
        opacity: [0, 1],
        duration: 800,
        delay: anime.stagger(100)
      }, '-=500')
      .add({
        targets: '.login-btn',
        translateY: [20, 0],
        opacity: [0, 1],
        duration: 600
      }, '-=400');
    }
    
    return () => {
      anime.remove('.login-logo');
      anime.remove('.login-title');
      anime.remove('.login-subtitle');
      anime.remove('.form-field');
      anime.remove('.login-btn');
      
      if (particlesRef.current) {
        const particlesContainer = particlesRef.current;
        while (particlesContainer.firstChild) {
          particlesContainer.removeChild(particlesContainer.firstChild);
        }
      }
    };
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);
    
    try {
      // Animate button press
      anime({
        targets: '.login-btn',
        scale: [1, 0.95, 1],
        duration: 400,
        easing: 'easeInOutQuad'
      });
      
      // The login from AuthContext handles navigation
      await login(email, password);
    } catch (err) {
      setError('Login failed. Please try again.');
      // Shake animation for error
      if (formRef.current) {
        anime({
          targets: formRef.current,
          translateX: [0, -10, 10, -10, 10, -5, 5, -2, 2, 0],
          duration: 600,
          easing: 'easeInOutQuad'
        });
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // If already authenticated, redirect to chat
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/chat');
    }
  }, [isAuthenticated, navigate]);

  // Redirect if already authenticated
  if (isAuthenticated) {
    return <Navigate to="/chat" replace />;
  }

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col justify-center items-center relative overflow-hidden py-8">
      {/* Animated background particles */}
      <div ref={particlesRef} className="fixed inset-0 z-0 pointer-events-none"></div>
      
      {/* Home navigation */}
      <Link to="/" className="absolute top-6 left-6 p-2 rounded-full bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 z-50 hover:bg-indigo-500/20 transition-all duration-300 group">
        <Home className="w-5 h-5 text-gray-300 group-hover:text-indigo-400 transition-colors" />
        <span className="sr-only">Back to Home</span>
      </Link>

      {/* Background patterns */}
      <div className="absolute inset-0 opacity-5 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCI+PHBhdGggZD0iTTAgMGg2MHY2MEgweiIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjZmZmIiBzdHJva2Utd2lkdGg9Ii41Ii8+PC9zdmc+')] bg-[length:60px_60px] z-0"></div>
      
      {/* Gradient effects */}
      <div className="absolute top-20 right-0 w-1/3 aspect-square bg-indigo-500/10 rounded-full blur-[150px] -z-10"></div>
      <div className="absolute bottom-20 left-0 w-1/3 aspect-square bg-violet-500/10 rounded-full blur-[150px] -z-10"></div>
      
      <div className="relative max-w-md w-full mx-auto px-4">
        {/* Logo centered at the top */}
        <div className="flex justify-center mb-10">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="login-logo flex items-center justify-center"
            ref={logoRef}
          >
            <div className="relative">
              <div className="absolute -inset-3 bg-gradient-to-r from-indigo-500 to-violet-500 rounded-full blur-md opacity-60"></div>
              <div className="relative bg-gray-900/90 rounded-full p-4">
                <Search className="w-10 h-10 text-indigo-400" />
              </div>
            </div>
          </motion.div>
        </div>
        
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center mb-6"
        >
          <h1 className="text-4xl font-bold tracking-tight text-white mb-1">
            <span>SEARCHIFY</span><span className="text-indigo-500">.AI</span>
          </h1>
          <h2 className="login-title text-2xl font-semibold text-white mb-2">Welcome Back</h2>
          <p className="login-subtitle text-gray-400 text-center">Sign in to continue to your research dashboard</p>
        </motion.div>
        
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="bg-gray-900/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-800 shadow-xl"
        >
          {error && (
            <motion.div 
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg flex items-start gap-3"
            >
              <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
              <p className="text-sm text-red-200">{error}</p>
            </motion.div>
          )}
          
          <form ref={formRef} onSubmit={handleSubmit} className="space-y-5">
            <div className="form-field">
              <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-1.5">Email or Username</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-gray-500" />
                </div>
                <input
                  id="email"
                  name="email"
                  type="text"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="block w-full pl-10 pr-3 py-2.5 border border-gray-700 rounded-lg bg-gray-800/50 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all duration-200"
                  placeholder="Email or username"
                />
              </div>
            </div>
            
            <div className="form-field">
              <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-1.5">Password</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-500" />
                </div>
                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full pl-10 pr-10 py-2.5 border border-gray-700 rounded-lg bg-gray-800/50 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all duration-200"
                  placeholder="••••••••"
                />
                <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
                  <button
                    type="button"
                    onClick={togglePasswordVisibility}
                    className="text-gray-400 hover:text-white focus:outline-none"
                  >
                    {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                  </button>
                </div>
              </div>
            </div>
            
            <div className="form-field flex items-center justify-between">
              <div className="flex items-center">
                <input
                  id="remember-me"
                  name="remember-me"
                  type="checkbox"
                  className="h-4 w-4 rounded border-gray-700 bg-gray-800 text-indigo-500 focus:ring-indigo-500"
                />
                <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-300">
                  Remember me
                </label>
              </div>
              <div className="text-sm">
                <a href="#" className="font-medium text-indigo-400 hover:text-indigo-300 transition-colors">
                  Forgot password?
                </a>
              </div>
            </div>
            
            <div>
              <motion.button
                type="submit"
                disabled={isSubmitting}
                whileHover={{ y: -3, boxShadow: "0 10px 25px -5px rgba(99, 102, 241, 0.4)" }}
                whileTap={{ y: 0 }}
                className={`login-btn w-full flex justify-center items-center px-4 py-3 border border-transparent rounded-lg shadow-sm text-white bg-gradient-to-r from-indigo-600 to-violet-600 font-medium hover:from-indigo-500 hover:to-violet-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-all duration-200 ${isSubmitting ? 'opacity-70 cursor-not-allowed' : ''}`}
              >
                {isSubmitting ? (
                  <span className="flex items-center">
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Signing in...
                  </span>
                ) : (
                  <>
                    <span>Sign in</span>
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </>
                )}
              </motion.button>
            </div>
          </form>
          
          <div className="mt-6 text-center form-field">
            <p className="text-sm text-gray-400">
              Don't have an account?{' '}
              <Link to="/signup" className="font-medium text-indigo-400 hover:text-indigo-300 transition-colors">
                Sign up
              </Link>
            </p>
          </div>
        </motion.div>
        
        <div className="mt-6 text-center">
          <p className="text-xs text-gray-500">
            &copy; {new Date().getFullYear()} Searchify.AI. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login; 