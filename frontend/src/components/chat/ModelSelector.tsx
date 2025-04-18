import React, { useRef, useEffect } from 'react';
import { IconChevronDown, IconX } from '@tabler/icons-react';
import { ModelProvider, modelProviders } from './ChatMain';
import anime from 'animejs';

interface ModelSelectorProps {
  selectedModel: ModelProvider;
  setSelectedModel: (model: ModelProvider) => void;
  isDropdownOpen: boolean;
  setIsDropdownOpen: (isOpen: boolean) => void;
  isMobile: boolean;
}

const ModelSelector: React.FC<ModelSelectorProps> = ({
  selectedModel,
  setSelectedModel,
  isDropdownOpen,
  setIsDropdownOpen,
  isMobile
}) => {
  const dropdownRef = useRef<HTMLDivElement>(null);
  const modelButtonRef = useRef<HTMLButtonElement>(null);
  
  // This ensures we don't interact with the page when dropdown is open on mobile
  useEffect(() => {
    if (isDropdownOpen && isMobile) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    
    return () => {
      document.body.style.overflow = '';
    };
  }, [isDropdownOpen, isMobile]);
  
  useEffect(() => {
    // Handle clicks outside of dropdown to close it
    const handleClickOutside = (event: MouseEvent) => {
      // Only run this if dropdown is open
      if (!isDropdownOpen) return;
      
      // Check if click is outside both the button and dropdown
      if (
        dropdownRef.current && 
        !dropdownRef.current.contains(event.target as Node) &&
        modelButtonRef.current && 
        !modelButtonRef.current.contains(event.target as Node)
      ) {
        setIsDropdownOpen(false);
      }
    };
    
    // Handle escape key to close dropdown
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isDropdownOpen) {
        setIsDropdownOpen(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscape);
    
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isDropdownOpen, setIsDropdownOpen]);
  
  const selectModel = (model: ModelProvider, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    // If it's the same model, just close the dropdown
    if (selectedModel.id === model.id) {
      setIsDropdownOpen(false);
      return;
    }
    
    // Animate model change
    anime({
      targets: '.model-button-text',
      opacity: [1, 0, 1],
      translateY: [0, -10, 0],
      duration: 400,
      easing: 'easeInOutQuad',
      complete: () => {
        setSelectedModel(model);
      }
    });
    
    // Close the dropdown after model selection
    setIsDropdownOpen(false);
  };
  
  const toggleDropdown = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation(); // Prevent event bubbling
    setIsDropdownOpen(!isDropdownOpen);
    
    if (!isDropdownOpen) {
      // If opening, animate the dropdown items
      setTimeout(() => {
        anime({
          targets: '.model-dropdown-item',
          opacity: [0, 1],
          translateY: [10, 0],
          delay: anime.stagger(50),
          easing: 'easeOutQuad'
        });
      }, 50);
    }
  };
  
  // Handle closing modal with specific function for mobile
  const closeDropdown = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDropdownOpen(false);
  };
  
  return (
    <div className="relative mt-3 md:mt-0 z-[9999]">
      <button 
        ref={modelButtonRef}
        onClick={toggleDropdown}
        className="group flex items-center justify-between w-full md:w-64 px-4 py-2.5 bg-gray-800/80 hover:bg-gray-800 text-gray-200 rounded-lg transition-all duration-200 border border-gray-700/50 hover:border-indigo-500/30 shadow-sm"
      >
        <div className="flex items-center gap-2">
          <div className={`w-6 h-6 rounded-full bg-gradient-to-r ${selectedModel.color} flex items-center justify-center`}>
            {selectedModel.icon}
          </div>
          <span className="model-button-text">{selectedModel.name}</span>
        </div>
        <IconChevronDown size={16} className={`transition-transform duration-300 ${isDropdownOpen ? 'rotate-180' : ''} text-gray-400 group-hover:text-white`} />
      </button>
      
      {/* Desktop Dropdown Menu - Only shown on desktop */}
      {isDropdownOpen && !isMobile && (
        <div 
          ref={dropdownRef}
          className="absolute right-0 mt-2 w-80 rounded-lg bg-gray-800/95 border border-gray-700/50 shadow-xl z-[9999] backdrop-blur-sm overflow-hidden"
        >
          <div className="py-2 max-h-[400px] overflow-y-auto">
            {modelProviders.map((model) => (
              <button
                key={model.id}
                onClick={(e) => selectModel(model, e)}
                className={`model-dropdown-item w-full px-4 py-3 text-left flex items-start gap-3 transition-all duration-200 ${
                  selectedModel.id === model.id 
                    ? 'bg-indigo-600/20 text-white' 
                    : 'text-gray-300 hover:bg-gray-700/70'
                }`}
              >
                <div className={`w-6 h-6 rounded-full bg-gradient-to-r ${model.color} flex items-center justify-center mt-0.5 flex-shrink-0`}>
                  {model.icon}
                </div>
                <div>
                  <span className="block font-medium text-sm">{model.name}</span>
                  {model.description && (
                    <span className="text-xs text-gray-400">{model.description}</span>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
      
      {/* Mobile Full screen modal - only shown on mobile */}
      {isDropdownOpen && isMobile && (
        <div 
          className="fixed inset-0 bg-gray-950/90 z-[99999] overflow-hidden"
          style={{ touchAction: 'none' }}
        >
          <div className="flex flex-col h-full">
            {/* Modal header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-800">
              <h2 className="text-xl font-semibold text-white">Select Model</h2>
              <button 
                onClick={closeDropdown}
                className="p-2 text-gray-400 hover:text-white rounded-full hover:bg-gray-800"
              >
                <IconX size={20} />
              </button>
            </div>
            
            {/* Modal content */}
            <div 
              className="flex-1 overflow-y-auto p-3"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="space-y-2 max-w-md mx-auto">
                {modelProviders.map((model) => (
                  <button
                    key={model.id}
                    onClick={(e) => selectModel(model, e)}
                    className={`model-dropdown-item w-full p-4 text-left flex items-start gap-3 transition-all duration-200 rounded-lg ${
                      selectedModel.id === model.id 
                        ? 'bg-indigo-600/20 border-l-2 border-indigo-500 shadow-sm' 
                        : 'hover:bg-gray-800/70'
                    }`}
                  >
                    <div className={`w-8 h-8 rounded-full bg-gradient-to-r ${model.color} flex items-center justify-center mt-0.5 flex-shrink-0`}>
                      {React.cloneElement(model.icon as React.ReactElement, { size: 20 })}
                    </div>
                    <div>
                      <span className="block font-medium text-lg text-white">{model.name}</span>
                      {model.description && (
                        <span className="text-sm text-gray-400">{model.description}</span>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Overlay for desktop dropdown to catch clicks outside */}
      {isDropdownOpen && !isMobile && (
        <div 
          className="fixed inset-0 z-[9998]"
          onClick={closeDropdown}
        />
      )}
    </div>
  );
};

export default ModelSelector; 