import React, { useState } from 'react';
import { IconChevronDown, IconX, IconSearch } from '@tabler/icons-react';
import { ModelProvider, modelProviders } from './ChatMain';

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
  const [searchTerm, setSearchTerm] = useState('');
  
  // Filter models based on search term
  const filteredModels = modelProviders.filter(model => 
    model.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (model.description && model.description.toLowerCase().includes(searchTerm.toLowerCase()))
  );
  
  // Function to handle model selection
  const handleSelectModel = (model: ModelProvider) => {
    setSelectedModel(model);
    setIsDropdownOpen(false);
    setSearchTerm('');
  };

  return (
    <div className="relative">
      {/* Selected model button - desktop only */}
      {!isMobile && (
        <button
          onClick={() => setIsDropdownOpen(!isDropdownOpen)}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gray-800/80 border border-gray-700/50 text-white text-sm shadow-md hover:bg-gray-800 hover:border-indigo-500/30 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all duration-200"
        >
          <div className={`w-5 h-5 flex-shrink-0 rounded-full bg-gradient-to-br ${selectedModel.color} flex items-center justify-center`}>
            {selectedModel.icon}
          </div>
          <span className="text-sm font-medium">{selectedModel.name}</span>
          <IconChevronDown
            size={16}
            className={`transform transition-transform duration-200 text-gray-400 ${
              isDropdownOpen ? 'rotate-180' : 'rotate-0'
            }`}
          />
        </button>
      )}

      {/* Mobile specific button */}
      {isMobile && (
        <button
          onClick={() => setIsDropdownOpen(!isDropdownOpen)}
          className="flex items-center justify-between w-full px-4 py-3 rounded-lg bg-gray-800 border border-gray-700/50 text-white"
        >
          <div className="flex items-center gap-2">
            <div className={`w-5 h-5 rounded-full bg-gradient-to-br ${selectedModel.color} flex items-center justify-center`}>
              {selectedModel.icon}
            </div>
            <span className="font-medium">{selectedModel.name}</span>
          </div>
          <IconChevronDown 
            size={16} 
            className={`transform transition-transform duration-200 text-gray-400 ${isDropdownOpen ? 'rotate-180' : 'rotate-0'}`} 
          />
        </button>
      )}

      {/* Dropdown menu */}
      {isDropdownOpen && (
        <>
          {/* Desktop backdrop */}
          {!isMobile && (
            <div 
              className="fixed inset-0 z-[100]" 
              onClick={() => setIsDropdownOpen(false)}
            />
          )}
          
          {/* Mobile list view with scroll and search */}
          {isMobile ? (
            <div className="mt-2 transition-all duration-200">
              {/* Search input */}
              <div className="mb-2 relative">
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Search models..."
                  className="w-full py-2 pl-10 pr-4 rounded-lg bg-gray-800 border border-gray-700 text-white text-sm focus:outline-none focus:border-indigo-500 transition-colors"
                />
                <IconSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
                {searchTerm && (
                  <button 
                    onClick={() => setSearchTerm('')} 
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
                  >
                    <IconX size={14} />
                  </button>
                )}
              </div>
              
              {/* Scrollable models list */}
              <div className="max-h-[45vh] overflow-y-auto pr-1 space-y-2 rounded-lg scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
                {filteredModels.length > 0 ? (
                  filteredModels.map((model) => (
                    <button
                      key={model.id}
                      onClick={() => handleSelectModel(model)}
                      className={`
                        w-full px-4 py-3 rounded-lg text-left flex items-center justify-between
                        ${selectedModel.id === model.id 
                          ? 'bg-gray-700/50 border border-indigo-500/30' 
                          : 'bg-gray-800 border border-gray-700/50 hover:border-gray-600'
                        }
                        transition-colors duration-150
                      `}
                    >
                      <div className="flex items-center gap-2">
                        <div className={`w-5 h-5 rounded-full bg-gradient-to-br ${model.color} flex items-center justify-center`}>
                          {model.icon}
                        </div>
                        <div>
                          <div className="font-medium text-white">{model.name}</div>
                          <div className="text-xs text-gray-400 mt-0.5">{model.description}</div>
                        </div>
                      </div>
                    </button>
                  ))
                ) : (
                  <div className="text-center py-4 text-gray-400">
                    No models match your search
                  </div>
                )}
              </div>
            </div>
          ) : (
            /* Desktop dropdown */
            <div className="absolute right-0 mt-2 w-72 rounded-xl shadow-xl bg-gray-900 border border-gray-700/50 p-2 z-[60]">
              <div className="space-y-1">
                {modelProviders.map((model) => (
                  <button
                    key={model.id}
                    onClick={() => handleSelectModel(model)}
                    className={`
                      w-full px-3 py-3 rounded-lg text-left flex items-center gap-3
                      ${
                        selectedModel.id === model.id
                          ? 'bg-indigo-600/20 border-l-2 border-indigo-500 pl-2'
                          : 'hover:bg-gray-800/70 border-l-2 border-transparent pl-2'
                      }
                      transition-colors duration-150
                    `}
                  >
                    <div className={`w-7 h-7 flex-shrink-0 rounded-full bg-gradient-to-br ${model.color} flex items-center justify-center shadow-md`}>
                      {model.icon}
                    </div>
                    <div>
                      <div className="text-sm font-medium text-white">{model.name}</div>
                      {model.description && (
                        <div className="text-xs text-gray-400 mt-0.5">{model.description}</div>
                      )}
                    </div>
                    {selectedModel.id === model.id && (
                      <div className="ml-auto w-2 h-2 rounded-full bg-indigo-500"></div>
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default ModelSelector; 