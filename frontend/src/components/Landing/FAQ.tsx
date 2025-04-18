import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { FiChevronDown, FiChevronUp } from 'react-icons/fi';

interface FAQItemProps {
  question: string;
  answer: string;
}

const FAQItem: React.FC<FAQItemProps> = ({ question, answer }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="border-b border-gray-700/50">
      <button
        className="flex w-full items-center justify-between py-5 text-left focus:outline-none"
        onClick={() => setIsOpen(!isOpen)}
      >
        <span className="text-lg font-medium text-white">{question}</span>
        <span className="ml-6 flex-shrink-0 text-indigo-400">
          {isOpen ? <FiChevronUp className="h-6 w-6" /> : <FiChevronDown className="h-6 w-6" />}
        </span>
      </button>
      {isOpen && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: "auto", opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          transition={{ duration: 0.3 }}
          className="pb-5"
        >
          <p className="text-gray-300">{answer}</p>
        </motion.div>
      )}
    </div>
  );
};

const FAQ: React.FC = () => {
  const faqItems = [
    {
      question: "What is DeepResearcher?",
      answer: "DeepResearcher is an AI-powered research assistant that helps you find, analyze, and synthesize information from various sources using advanced machine learning algorithms."
    },
    {
      question: "How does DeepResearcher work?",
      answer: "DeepResearcher uses natural language processing and machine learning to understand your research queries, search through relevant sources, extract key information, and present findings in an organized format."
    },
    {
      question: "Is my research data secure?",
      answer: "Yes. We take data security seriously. All your research data is encrypted and stored securely. We never share your data with third parties without your explicit permission."
    },
    {
      question: "Can I try DeepResearcher before subscribing?",
      answer: "Absolutely! We offer a free tier that allows you to explore the basic features of DeepResearcher. You can upgrade to a premium plan anytime to access advanced features."
    },
    {
      question: "What types of research can I do with DeepResearcher?",
      answer: "DeepResearcher supports a wide range of research areas including academic research, market research, literature reviews, competitive analysis, and more."
    },
    {
      question: "How do I get started with DeepResearcher?",
      answer: "Simply create an account, choose your research area, and start with your first query. Our intuitive interface will guide you through the process."
    }
  ];

  return (
    <div className="container mx-auto px-4 py-20">
      <div className="mx-auto max-w-3xl">
        <h2 className="text-4xl md:text-5xl font-bold text-center mb-2 text-white">
          Frequently Asked <span className="text-indigo-400">Questions</span>
        </h2>
        <p className="text-gray-300 text-center mb-12">
          Have questions? We've got you covered.
        </p>
        <div className="mt-8 space-y-0 rounded-2xl bg-gray-800/30 backdrop-blur-lg p-6 border border-gray-700/50">
          {faqItems.map((item, index) => (
            <FAQItem key={index} question={item.question} answer={item.answer} />
          ))}
        </div>
      </div>
    </div>
  );
};

export default FAQ; 