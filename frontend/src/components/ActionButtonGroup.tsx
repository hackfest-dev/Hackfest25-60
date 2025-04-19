import React from 'react';
import { IconAdjustmentsHorizontal, IconBrain, IconSearch } from '@tabler/icons-react';
import { FeatureType } from './chat/ChatMain';

interface ActionButtonGroupProps {
  activeFeatures: {
    queryRefiner: boolean;
    deepResearch: boolean;
  };
  toggleFeature: (feature: FeatureType) => void;
}

const ActionButtonGroup: React.FC<ActionButtonGroupProps> = ({ 
  activeFeatures, 
  toggleFeature 
}) => {
  return (
    <div className="grid grid-cols-2 gap-2 mt-3">
      <button
        onClick={() => toggleFeature('queryRefiner')}
        className={`feature-button queryRefiner-button flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg border ${
          activeFeatures.queryRefiner 
            ? 'bg-indigo-500/10 border-indigo-500/30 text-indigo-300' 
            : 'bg-gray-800/40 border-gray-700/30 text-gray-300 hover:bg-gray-800/60 hover:border-gray-600/50'
        } transition-all duration-200 text-sm`}
      >
        <IconAdjustmentsHorizontal size={16} />
        <span>Query Refiner</span>
      </button>
      
      <button
        onClick={() => toggleFeature('deepResearch')}
        className={`feature-button deepResearch-button flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg border ${
          activeFeatures.deepResearch 
            ? 'bg-indigo-500/10 border-indigo-500/30 text-indigo-300' 
            : 'bg-gray-800/40 border-gray-700/30 text-gray-300 hover:bg-gray-800/60 hover:border-gray-600/50'
        } transition-all duration-200 text-sm`}
      >
        <IconBrain size={16} />
        <span>Deep Research</span>
      </button>
    </div>
  );
};

export default ActionButtonGroup; 