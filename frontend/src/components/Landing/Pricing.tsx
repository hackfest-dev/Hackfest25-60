import React, { useEffect, useRef, useState } from 'react';
import anime from 'animejs';
import { motion } from 'framer-motion';
import { Check, X, Sparkles, ArrowRight, ShieldCheck, Zap, Clock, Star, Users, BookOpen, GraduationCap, Building } from 'lucide-react';
import FAQ from './FAQ';
// Define plan type with optional properties
interface PlanType {
  title: string;
  price: string;
  oldPrice?: string;
  description: string;
  features: string[];
  icon: React.ReactNode;
  popular: boolean;
  buttonText: string;
  userType: React.ReactNode;
  savings?: string;
}

const Pricing: React.FC = () => {
  const pricingRef = useRef<HTMLDivElement>(null);
  const cardsRef = useRef<HTMLDivElement>(null);
  const [windowSize, setWindowSize] = useState({ width: window.innerWidth, height: window.innerHeight });
  const [activeTab, setActiveTab] = useState<'monthly' | 'annual'>('monthly');

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
    // Generate morphing background
    const morphBackground = (el: SVGPathElement) => {
      anime({
        targets: el,
        d: [
          { value: createMorphPath(0) },
          { value: createMorphPath(0.2) },
          { value: createMorphPath(0.1) },
          { value: createMorphPath(0.3) },
          { value: createMorphPath(0) },
        ],
        easing: 'easeInOutSine',
        duration: 12000,
        loop: true
      });
    };

    // Create path function for morphing background
    function createMorphPath(intensity: number) {
      const width = windowSize.width;
      const height = 300;
      const controlPoints = Math.min(Math.floor(width / 100), 10);
      let path = `M0,${height * 0.3} `;
      
      for (let i = 0; i <= controlPoints; i++) {
        const x = (width * i) / controlPoints;
        const yOffset = Math.sin((i / controlPoints) * Math.PI * 3) * intensity;
        const y = height * (0.5 + yOffset * 0.3);
        path += `${i === 0 ? 'C' : ''} ${x},${y} `;
      }
      
      path += `${width},${height * 0.3} L${width},${height} L0,${height} Z`;
      return path;
    }

    const morphElements = document.querySelectorAll('.pricing-morph-path');
    morphElements.forEach(el => {
      if (el instanceof SVGPathElement) {
        morphBackground(el);
      }
    });

    // Create intersection observer for scroll animations
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            // Animate title
            if (entry.target === pricingRef.current) {
              anime({
                targets: '.pricing-title',
                translateY: [30, 0],
                opacity: [0, 1],
                duration: 800,
                easing: 'easeOutExpo',
              });
              
              anime({
                targets: '.pricing-description',
                translateY: [20, 0],
                opacity: [0, 1],
                duration: 800,
                delay: 200,
                easing: 'easeOutExpo',
              });
              
              anime({
                targets: '.pricing-tabs',
                scale: [0.95, 1],
                opacity: [0, 1],
                duration: 800,
                delay: 400,
                easing: 'easeOutExpo',
              });
            }
            
            // Animate cards
            if (entry.target === cardsRef.current) {
              anime({
                targets: '.pricing-card',
                translateY: [30, 0],
                opacity: [0, 1],
                duration: 800,
                delay: anime.stagger(150),
                easing: 'easeOutExpo',
              });
              
              anime({
                targets: '.pricing-table',
                opacity: [0, 1],
                translateY: [30, 0],
                duration: 1000,
                delay: 600,
                easing: 'easeOutExpo'
              });
            }
          }
        });
      },
      { threshold: 0.1 }
    );
    
    // Observe the sections
    if (pricingRef.current) observer.observe(pricingRef.current);
    if (cardsRef.current) observer.observe(cardsRef.current);
    
    return () => {
      observer.disconnect();
    };
  }, [windowSize]);

  // Price data
  const prices: {monthly: PlanType[], annual: PlanType[]} = {
    monthly: [
      {
        title: "Free",
        price: "₹0",
        description: "Perfect for trying out the platform",
        features: [
          "5 searches per month",
          "Basic research access",
          "24-hour result retention",
          "Standard response time"
        ],
        icon: <BookOpen className="w-6 h-6 text-indigo-400" />,
        popular: false,
        buttonText: "Get Started",
        userType: <Users className="w-4 h-4 mr-1" />
      },
      {
        title: "Pro",
        price: "₹999",
        description: "For individual researchers and students",
        features: [
          "50 searches per month",
          "Advanced search capabilities",
          "30-day result history",
          "Priority support",
          "Custom search parameters"
        ],
        icon: <GraduationCap className="w-6 h-6 text-indigo-300" />,
        popular: true,
        buttonText: "Get Pro",
        userType: <Star className="w-4 h-4 mr-1" />
      },
      {
        title: "Business",
        price: "₹2,499",
        description: "For teams and organizations",
        features: [
          "Unlimited searches",
          "Team collaboration tools",
          "API access",
          "Custom integrations",
          "Advanced analytics",
          "Dedicated support"
        ],
        icon: <Building className="w-6 h-6 text-indigo-500" />,
        popular: false,
        buttonText: "Contact Sales",
        userType: <Building className="w-4 h-4 mr-1" />
      }
    ],
    annual: [
      {
        title: "Free",
        price: "₹0",
        description: "Perfect for trying out the platform",
        features: [
          "5 searches per month",
          "Basic research access",
          "24-hour result retention",
          "Standard response time"
        ],
        icon: <BookOpen className="w-6 h-6 text-indigo-400" />,
        popular: false,
        buttonText: "Get Started",
        userType: <Users className="w-4 h-4 mr-1" />
      },
      {
        title: "Pro",
        price: "₹9,990",
        oldPrice: "₹11,988",
        description: "For individual researchers and students",
        features: [
          "50 searches per month",
          "Advanced search capabilities",
          "30-day result history",
          "Priority support",
          "Custom search parameters"
        ],
        icon: <GraduationCap className="w-6 h-6 text-indigo-300" />,
        popular: true,
        buttonText: "Get Pro",
        savings: "Save ₹1,998",
        userType: <Star className="w-4 h-4 mr-1" />
      },
      {
        title: "Business",
        price: "₹24,990",
        oldPrice: "₹29,988",
        description: "For teams and organizations",
        features: [
          "Unlimited searches",
          "Team collaboration tools",
          "API access",
          "Custom integrations",
          "Advanced analytics",
          "Dedicated support"
        ],
        icon: <Building className="w-6 h-6 text-indigo-500" />,
        popular: false,
        buttonText: "Contact Sales",
        savings: "Save ₹4,998",
        userType: <Building className="w-4 h-4 mr-1" />
      }
    ]
  };

  const featuresCompare = [
    { name: "Searches per month", free: "5", pro: "50", business: "Unlimited" },
    { name: "Result history", free: "24 hours", pro: "30 days", business: "Unlimited" },
    { name: "Research sources", free: "Limited", pro: "Extensive", business: "All available" },
    { name: "Response time", free: "Standard", pro: "Priority", business: "Premium" },
    { name: "Search depth", free: "Basic", pro: "Advanced", business: "Maximum" },
    { name: "API access", free: <X className="text-red-400 w-5 h-5" />, pro: <X className="text-red-400 w-5 h-5" />, business: <Check className="text-green-400 w-5 h-5" /> },
    { name: "Team collaboration", free: <X className="text-red-400 w-5 h-5" />, pro: <X className="text-red-400 w-5 h-5" />, business: <Check className="text-green-400 w-5 h-5" /> },
    { name: "Custom integrations", free: <X className="text-red-400 w-5 h-5" />, pro: <X className="text-red-400 w-5 h-5" />, business: <Check className="text-green-400 w-5 h-5" /> },
    { name: "Analytics dashboard", free: <X className="text-red-400 w-5 h-5" />, pro: <Check className="text-green-400 w-5 h-5" />, business: <Check className="text-green-400 w-5 h-5" /> },
    { name: "Custom search parameters", free: <X className="text-red-400 w-5 h-5" />, pro: <Check className="text-green-400 w-5 h-5" />, business: <Check className="text-green-400 w-5 h-5" /> }
  ];

  const currentPrices = activeTab === 'monthly' ? prices.monthly : prices.annual;

  return (
    <section id="pricing" className="py-20 relative overflow-hidden">
      {/* Morphing background */}
      <div className="absolute bottom-0 inset-x-0 h-[300px] overflow-hidden pointer-events-none">
        <svg className="absolute bottom-0 w-full h-full" viewBox={`0 0 ${windowSize.width} 300`} preserveAspectRatio="none">
          <path
            className="pricing-morph-path fill-indigo-500/5"
            d={`M0,${300 * 0.3} C${windowSize.width * 0.3},${300 * 0.6} ${windowSize.width * 0.6},${300 * 0.4} ${windowSize.width},${300 * 0.5} L${windowSize.width},${300} L0,${300} Z`}
          />
        </svg>
      </div>

      <div className="container mx-auto px-4 relative z-10">
        <div ref={pricingRef} className="text-center mb-16">
          <h2 className="pricing-title opacity-0 text-4xl md:text-5xl font-bold text-white mb-4">
            <span className="inline-block relative">
              Simple <span className="text-indigo-400">Pricing</span>
              <div className="absolute -top-6 -right-6 text-indigo-500/30">
                <Sparkles className="w-10 h-10 animate-pulse" />
              </div>
            </span>
          </h2>
          <p className="pricing-description opacity-0 text-xl text-gray-300 max-w-3xl mx-auto">
            Choose the perfect plan for your research needs. All plans include access to our AI-powered research engine.
          </p>
          
          {/* Pricing tabs */}
          <div className="pricing-tabs opacity-0 inline-flex bg-gray-900/50 backdrop-blur-sm p-1.5 rounded-xl mt-10 border border-gray-800">
            <button 
              className={`px-6 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${activeTab === 'monthly' ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/20' : 'text-gray-400 hover:text-white'}`}
              onClick={() => setActiveTab('monthly')}
            >
              Monthly
            </button>
            <button 
              className={`px-6 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${activeTab === 'annual' ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/20' : 'text-gray-400 hover:text-white'} relative group`}
              onClick={() => setActiveTab('annual')}
            >
              <span className="relative z-10">Annual</span>
              {activeTab !== 'annual' && (
                <span className="absolute -top-3 -right-3 bg-indigo-500 text-white text-[10px] px-2 py-0.5 rounded-full">
                  Save 17%
                </span>
              )}
            </button>
          </div>
        </div>
        
        <div ref={cardsRef}>
          {/* Pricing cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-16">
            {currentPrices.map((plan, index) => (
              <motion.div 
                key={index} 
                className={`pricing-card relative bg-gray-900/50 backdrop-blur-sm rounded-2xl overflow-hidden border ${plan.popular ? 'border-indigo-500/50' : 'border-gray-800/50'}`}
                whileHover={{ 
                  scale: 1.02, 
                  boxShadow: plan.popular ? "0 0 30px rgba(99, 102, 241, 0.3)" : "0 0 20px rgba(99, 102, 241, 0.15)"
                }}
              >
                {plan.popular && (
                  <div className="absolute top-0 right-0">
                    <div className="bg-indigo-500 text-white text-xs font-medium px-3 py-1 rounded-bl-lg">
                      Most Popular
                    </div>
                  </div>
                )}
                
                <div className="p-8">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <div className={`p-2 rounded-lg ${plan.popular ? 'bg-indigo-500/20' : 'bg-gray-800/50'}`}>
                        {plan.icon}
                      </div>
                      <h3 className="text-xl font-bold text-white">{plan.title}</h3>
                    </div>
                    <div className="flex items-center text-xs font-medium text-gray-400">
                      {plan.userType}
                      <span>For {plan.title === "Free" ? "Starters" : plan.title === "Pro" ? "Individuals" : "Teams"}</span>
                    </div>
                  </div>
                  
                  <div className="mb-6">
                    <div className="flex items-end">
                      <span className="text-4xl font-bold text-white">{plan.price}</span>
                      {activeTab === 'monthly' && plan.title !== "Free" && <span className="text-gray-400 ml-2">/month</span>}
                      {activeTab === 'annual' && plan.title !== "Free" && <span className="text-gray-400 ml-2">/year</span>}
                    </div>
                    {plan.oldPrice && (
                      <div className="flex items-center mt-1">
                        <span className="text-gray-500 line-through text-sm">{plan.oldPrice}</span>
                        <span className="ml-2 text-xs text-indigo-400">{plan.savings}</span>
                      </div>
                    )}
                    <p className="text-gray-400 mt-3">{plan.description}</p>
                  </div>
                  
                  <ul className="space-y-3 mb-8">
                    {plan.features.map((feature, fIndex) => (
                      <li key={fIndex} className="flex items-start">
                        <Check className="w-5 h-5 text-indigo-400 mt-0.5 mr-3 flex-shrink-0" />
                        <span className="text-gray-300">{feature}</span>
                      </li>
                    ))}
                  </ul>
                  
                  <motion.button 
                    className={`w-full py-3 rounded-xl font-medium flex items-center justify-center ${
                      plan.popular 
                        ? 'bg-indigo-500 hover:bg-indigo-600 text-white' 
                        : 'bg-gray-800 hover:bg-gray-700 text-white border border-gray-700'
                    } transition-all relative overflow-hidden group`}
                    whileHover={{ scale: 1.03 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <span className="relative z-10">{plan.buttonText}</span>
                    <ArrowRight className="w-4 h-4 ml-2 transition-transform group-hover:translate-x-1 relative z-10" />
                    {plan.popular && (
                      <div className="absolute inset-0 bg-gradient-to-r from-indigo-600 to-violet-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                    )}
                  </motion.button>
                </div>
              </motion.div>
            ))}
          </div>
          
          {/* Features comparison table */}
          <div className="pricing-table opacity-0 mt-16">
            <div className="bg-gray-900/30 backdrop-blur-sm rounded-xl p-6 border border-gray-800/50">
              <h3 className="text-2xl font-bold text-white mb-8">Features Comparison</h3>
              
              {/* Mobile view - stacked cards for small screens */}
              <div className="block md:hidden space-y-6">
                {featuresCompare.map((feature, index) => (
                  <div key={index} className="bg-gray-800/30 rounded-lg p-4">
                    <h4 className="font-medium text-white mb-3">{feature.name}</h4>
                    <div className="grid grid-cols-3 gap-2">
                      <div className="flex flex-col items-center bg-gray-900/50 rounded-lg p-2">
                        <span className="text-xs text-gray-400 mb-1">Free</span>
                        <div className="text-center">{feature.free}</div>
                      </div>
                      <div className="flex flex-col items-center bg-indigo-900/20 rounded-lg p-2">
                        <span className="text-xs text-gray-400 mb-1">Pro</span>
                        <div className="text-center">{feature.pro}</div>
                      </div>
                      <div className="flex flex-col items-center bg-gray-900/50 rounded-lg p-2">
                        <span className="text-xs text-gray-400 mb-1">Business</span>
                        <div className="text-center">{feature.business}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              {/* Desktop view - table for larger screens */}
              <div className="hidden md:block overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-800 text-left">
                      <th className="py-4 px-4 text-gray-400 font-medium">Feature</th>
                      <th className="py-4 px-4 text-gray-400 font-medium">Free</th>
                      <th className="py-4 px-4 text-gray-400 font-medium">Pro</th>
                      <th className="py-4 px-4 text-gray-400 font-medium">Business</th>
                    </tr>
                  </thead>
                  <tbody>
                    {featuresCompare.map((feature, index) => (
                      <tr key={index} className={`border-b border-gray-800/50 ${index % 2 === 0 ? 'bg-gray-900/20' : ''}`}>
                        <td className="py-4 px-4 text-white">{feature.name}</td>
                        <td className="py-4 px-4 text-gray-300">{feature.free}</td>
                        <td className="py-4 px-4 text-gray-300">{feature.pro}</td>
                        <td className="py-4 px-4 text-gray-300">{feature.business}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
        
        {/* Additional info */}
        <div className="mt-20">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                icon: <ShieldCheck className="w-8 h-8 text-indigo-400" />,
                title: "Secure Payments",
                description: "All transactions are secure and encrypted with the latest standards."
              },
              {
                icon: <Zap className="w-8 h-8 text-indigo-400" />,
                title: "Instant Access",
                description: "Get immediate access to our platform after successful payment."
              },
              {
                icon: <Clock className="w-8 h-8 text-indigo-400" />,
                title: "30-Day Guarantee",
                description: "Not satisfied? Get a full refund within 30 days of purchase."
              }
            ].map((item, index) => (
              <div key={index} className="flex flex-col items-center text-center p-6 bg-gray-900/30 backdrop-blur-sm rounded-xl border border-gray-800/50">
                <div className="p-3 bg-indigo-500/10 rounded-lg mb-4">
                  {item.icon}
                </div>
                <h4 className="text-xl font-bold text-white mb-2">{item.title}</h4>
                <p className="text-gray-400">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
      <motion.section 
                  id="faq"
                  className="relative z-10"
                  initial={{ opacity: 0, y: 50 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: "-100px" }}
                  transition={{ duration: 0.5 }}
                >
                  <FAQ />
                </motion.section>
    </section>
  );
};

export default Pricing; 