import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { IconX } from '@tabler/icons-react';
import Sidebar from './Sidebar';
import anime from 'animejs';

interface MobileSidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

const MobileSidebar: React.FC<MobileSidebarProps> = ({ isOpen, onClose }) => {
  useEffect(() => {
    if (isOpen) {
      // Animate sidebar content when opened
      anime({
        targets: '.mobile-sidebar-content',
        opacity: [0, 1],
        translateX: [-20, 0],
        easing: 'easeOutQuad',
        duration: 400,
        delay: anime.stagger(50),
      });
    }
  }, [isOpen]);
  
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop with blur effect */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 bg-gray-950/60 backdrop-blur-sm z-40 md:hidden"
            onClick={onClose}
          />
          
          {/* Drawer */}
          <motion.div
            initial={{ x: '-100%' }}
            animate={{ x: 0 }}
            exit={{ x: '-100%' }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            className="fixed inset-y-0 left-0 z-50 w-[280px] md:hidden"
          >
            <div className="relative h-full mobile-sidebar-content overflow-hidden shadow-xl">
              <Sidebar />
              
              {/* Close button - floating */}
              <button
                onClick={onClose}
                className="absolute top-4 -right-4 w-8 h-8 flex items-center justify-center rounded-full bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700 transition-colors shadow-lg transform translate-x-1/2"
                aria-label="Close sidebar"
              >
                <IconX size={16} />
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default MobileSidebar; 