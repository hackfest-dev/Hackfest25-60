import React from "react";
import { InfiniteMovingCards } from "../ui/infinite-moving-cards";
import { motion } from "framer-motion";

const Testimonials: React.FC = () => {
  const testimonials = [
    {
      quote: "DeepResearcher has transformed my academic workflow. I've been able to complete literature reviews in half the time with more comprehensive results. The AI understands context and connections between papers that I might have missed.",
      name: "Dr. Sarah Johnson",
      title: "Professor of Computer Science"
    },
    {
      quote: "As a market analyst, I need to stay ahead of trends. DeepResearcher helps me synthesize information from thousands of sources to spot patterns and opportunities that give our clients a competitive edge.",
      name: "Michael Chen",
      title: "Senior Market Analyst"
    },
    {
      quote: "The depth and accuracy of research I can conduct with DeepResearcher is remarkable. My dissertation research has progressed much faster, and the AI helps me organize my findings in a way that makes writing so much easier.",
      name: "Emily Rodriguez",
      title: "Doctoral Candidate"
    },
    {
      quote: "Our startup used DeepResearcher to analyze market trends and competitor strategies. The insights we gained were instrumental in refining our product and securing our next round of funding.",
      name: "David Kim",
      title: "Tech Entrepreneur"
    },
    {
      quote: "DeepResearcher has accelerated our lab's research timeline significantly. What used to take weeks of literature review and data analysis now takes days, allowing us to focus more on experimental design and results.",
      name: "Dr. Priya Patel",
      title: "Research Scientist"
    },
    {
      quote: "I was skeptical about AI research tools, but DeepResearcher has proven invaluable. It doesn't just find sources but helps connect ideas across disciplines in ways I wouldn't have considered.",
      name: "Thomas Wright",
      title: "Policy Researcher"
    },
    {
      quote: "As a journalist covering complex topics, DeepResearcher helps me quickly get up to speed on new subjects with comprehensive background research that I can trust for accuracy.",
      name: "Sophia Martinez",
      title: "Investigative Journalist"
    }
  ];

  return (
    <div className="container mx-auto px-4 py-20">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        viewport={{ once: true }}
        className="text-center mb-12"
      >
        <h2 className="text-4xl md:text-5xl font-bold text-center mb-4 text-white">
          What Our <span className="text-indigo-400">Researchers Say</span>
        </h2>
        <p className="text-gray-300 text-center max-w-2xl mx-auto">
          Join thousands of professionals who have transformed their research workflow with our AI-powered assistant.
        </p>
      </motion.div>

      <div className="relative h-[400px] md:h-[350px] w-full overflow-hidden rounded-lg">
        <div className="absolute inset-0 bg-gradient-to-r from-gray-950 via-transparent to-gray-950 z-10"></div>
        
        <InfiniteMovingCards
          items={testimonials}
          direction="right"
          speed="slow"
          className="py-8"
        />
      </div>

      <div className="mt-12 flex flex-col items-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          viewport={{ once: true }}
          className="relative"
        >
          <div className="flex flex-wrap justify-center gap-4">
            <div className="p-1 rounded-full bg-gradient-to-r from-indigo-500 to-purple-500">
              <div className="bg-gray-900 rounded-full px-6 py-2">
                <p className="text-white font-medium">Join 10,000+ researchers</p>
              </div>
            </div>
            <div className="p-1 rounded-full bg-gradient-to-r from-indigo-500 to-purple-500">
              <div className="bg-gray-900 rounded-full px-6 py-2">
                <p className="text-white font-medium">Used in 500+ universities</p>
              </div>
            </div>
            <div className="p-1 rounded-full bg-gradient-to-r from-indigo-500 to-purple-500">
              <div className="bg-gray-900 rounded-full px-6 py-2">
                <p className="text-white font-medium">4.9/5 average rating</p>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default Testimonials;
