import React, { ChangeEvent, FormEvent, useState, useEffect, useRef } from 'react';
import { IconSearch, IconMicrophone, IconArrowRight, IconMicrophoneOff, IconSend } from '@tabler/icons-react';
import anime from 'animejs';

interface SearchBarProps {
  value: string;
  onChange: (e: ChangeEvent<HTMLInputElement>) => void;
  onSubmit: (e: FormEvent) => void;
  onVoiceInput: (transcript: string) => void;
  isDisabled?: boolean; // Optional prop to disable search submission
  isPulsing?: boolean; // Optional prop to add pulsing effect to the search bar
}

const SearchBar: React.FC<SearchBarProps> = ({
  value,
  onChange,
  onSubmit,
  onVoiceInput,
  isDisabled = false,
  isPulsing = false
}) => {
  const [isListening, setIsListening] = useState(false);
  const [voiceLevel, setVoiceLevel] = useState(0);
  const [focused, setFocused] = useState(false);
  const searchBarRef = useRef<HTMLFormElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const micPulseRef = useRef<any>(null);
  const rainbowBorderRef = useRef<any>(null);
  const recognitionRef = useRef<any>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const microphoneRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const micButtonRef = useRef<HTMLButtonElement>(null);
  const pulseAnimationRef = useRef<any>(null);
  
  useEffect(() => {
    // Animate search bar on mount
    anime({
      targets: searchBarRef.current,
      translateY: [10, 0],
      opacity: [0, 1],
      easing: 'easeOutQuad',
      duration: 500,
      delay: 300
    });
    
    // Cleanup function to ensure all resources are released
    return () => {
      stopListening();
      if (pulseAnimationRef.current) {
        pulseAnimationRef.current.pause();
        pulseAnimationRef.current = null;
      }
    };
  }, []);
  
  // This effect ensures the UI state stays in sync with isListening
  useEffect(() => {
    if (micButtonRef.current) {
      if (isListening) {
        micButtonRef.current.classList.add('bg-red-500', 'text-white');
      } else {
        micButtonRef.current.classList.remove('bg-red-500', 'text-white');
      }
    }
  }, [isListening]);
  
  // Handle pulsing animation
  useEffect(() => {
    if (isPulsing) {
      pulseAnimationRef.current = anime({
        targets: searchBarRef.current,
        boxShadow: [
          '0 0 0 0 rgba(139, 92, 246, 0)',
          '0 0 0 4px rgba(139, 92, 246, 0.3)',
          '0 0 0 0 rgba(139, 92, 246, 0)'
        ],
        duration: 1500,
        easing: 'easeInOutSine',
        loop: true
      });
    } else if (pulseAnimationRef.current) {
      pulseAnimationRef.current.pause();
      pulseAnimationRef.current = null;
      if (searchBarRef.current) {
        searchBarRef.current.style.boxShadow = '';
      }
    }
    
    return () => {
      if (pulseAnimationRef.current) {
        pulseAnimationRef.current.pause();
        pulseAnimationRef.current = null;
      }
    };
  }, [isPulsing]);
  
  const startListening = () => {
    // If already listening, stop first to avoid multiple instances
    if (isListening) {
      stopListening();
      return;
    }
    
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      alert('Speech recognition is not supported in your browser.');
      return;
    }
    
    setIsListening(true);
    
    // Pulsing animation for mic button
    micPulseRef.current = anime({
      targets: '.mic-button',
      scale: [1, 1.1, 1],
      backgroundColor: ['#ef4444', '#dc2626'],
      duration: 1000,
      easing: 'easeInOutQuad',
      direction: 'alternate',
      loop: true
    });
    
    // Rainbow border animation
    rainbowBorderRef.current = anime({
      targets: '.rainbow-border',
      backgroundPosition: ['0% 50%', '100% 50%'],
      easing: 'linear',
      duration: 3000,
      loop: true
    });
    
    // @ts-ignore - TypeScript doesn't have types for the Web Speech API by default
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    
    recognition.lang = 'en-US';
    recognition.interimResults = true;
    recognition.continuous = true;
    recognition.maxAlternatives = 1;
    
    // Store recognition instance for later cleanup
    recognitionRef.current = recognition;
    
    // Try to simulate voice levels (not all browsers support audioLevel)
    try {
      navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
          // Store stream for cleanup
          streamRef.current = stream;
          
          const audioContext = new AudioContext();
          audioContextRef.current = audioContext;
          
          const analyser = audioContext.createAnalyser();
          const microphone = audioContext.createMediaStreamSource(stream);
          microphoneRef.current = microphone;
          
          microphone.connect(analyser);
          analyser.fftSize = 256;
          
          const dataArray = new Uint8Array(analyser.frequencyBinCount);
          
          const updateVoiceLevel = () => {
            if (!isListening) return;
            
            analyser.getByteFrequencyData(dataArray);
            // Get average volume
            const average = dataArray.reduce((acc, val) => acc + val, 0) / dataArray.length;
            // Normalize to 0-100
            setVoiceLevel(Math.min(100, average * 1.5));
            
            requestAnimationFrame(updateVoiceLevel);
          };
          
          updateVoiceLevel();
        })
        .catch(err => {
          console.error('Error accessing microphone:', err);
        });
    } catch (error) {
      console.error('Audio context not supported:', error);
    }
    
    recognition.onresult = (event: any) => {
      const lastResult = event.results[event.results.length - 1];
      if (lastResult.isFinal) {
        const transcript = lastResult[0].transcript;
        onVoiceInput(transcript);
        // Use a slight delay before stopping to ensure the transcript is processed
        setTimeout(() => {
          stopListening();
        }, 500);
      }
    };
    
    recognition.onerror = () => {
      stopListening();
    };
    
    recognition.onend = () => {
      // Sometimes onend fires before we get results, only stop if we're still listening
      if (isListening) {
        stopListening();
      }
    };
    
    // Start recognition
    try {
      recognition.start();
    } catch (error) {
      console.error("Error starting speech recognition:", error);
      stopListening();
    }
  };
  
  const stopListening = () => {
    // Only proceed if we're actually listening
    if (!isListening && !recognitionRef.current) return;
    
    // Update state immediately
    setIsListening(false);
    setVoiceLevel(0);
    
    // Stop animations
    if (micPulseRef.current) {
      micPulseRef.current.pause();
      micPulseRef.current = null;
    }
    
    if (rainbowBorderRef.current) {
      rainbowBorderRef.current.pause();
      rainbowBorderRef.current = null;
    }
    
    // Manually reset mic button styles to ensure they're removed
    if (micButtonRef.current) {
      micButtonRef.current.style.backgroundColor = '';
      micButtonRef.current.style.transform = '';
      micButtonRef.current.style.opacity = '';
    }
    
    // Stop recognition
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (error) {
        console.log("Recognition already stopped");
      }
      recognitionRef.current = null;
    }
    
    // Clean up audio context and stream
    if (microphoneRef.current) {
      microphoneRef.current.disconnect();
      microphoneRef.current = null;
    }
    
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    
    // Stop all audio tracks from the stream
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
  };
  
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    // Don't submit if disabled
    if (isDisabled) return;
    
    // Ensure we're not listening when submitting
    if (isListening) {
      stopListening();
    }
    
    onSubmit(e);
  };
  
  return (
    <form 
      ref={searchBarRef}
      onSubmit={handleSubmit} 
      className={`relative transition-all duration-300 ${focused ? 'scale-[1.02]' : 'scale-100'} ${isPulsing ? 'pulse-highlight' : ''}`}
    >
      {/* Rainbow border when listening */}
      {isListening && (
        <div className="rainbow-border absolute -inset-[2px] rounded-xl z-0 overflow-hidden"
             style={{
               background: 'linear-gradient(90deg, #f87171, #d946ef, #8b5cf6, #3b82f6, #2dd4bf, #a3e635, #fcd34d, #f87171)',
               backgroundSize: '200% 200%'
             }}>
        </div>
      )}
      
      <div className="flex items-center relative">
        {/* Voice level indicator - shows when listening */}
        {isListening && (
          <div className="absolute inset-0 rounded-lg overflow-hidden pointer-events-none z-0">
            <div 
              className="h-full bg-gradient-to-r from-indigo-600/20 to-purple-600/20 transition-all duration-100"
              style={{ width: `${voiceLevel}%` }}
            ></div>
          </div>
        )}
        
        {/* Search icon */}
        <div className="absolute left-4 text-gray-400 z-10">
          <IconSearch size={18} />
        </div>
        
        {/* Search input */}
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={onChange}
          placeholder={isListening ? "Listening..." : "Ask anything..."}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          disabled={isListening}
          className={`w-full py-3.5 pl-12 pr-28 text-white rounded-xl transition-all duration-300 focus:outline-none focus:ring-2 focus:shadow-lg relative z-10 ${
            isListening 
              ? 'bg-gray-800/70 border-transparent ring-2 ring-purple-500/30 shadow-purple-600/10 cursor-not-allowed placeholder-purple-300/50'
              : isPulsing
                ? 'bg-gray-800/70 border border-purple-500/30 ring-2 ring-purple-500/20 placeholder-purple-300/50'
                : isDisabled && value.trim()
                  ? 'bg-gray-800/70 border border-gray-700/50 opacity-70 cursor-not-allowed'
                  : 'bg-gray-800/70 border border-gray-700/50 focus:border-indigo-500/30 focus:ring-indigo-500/20'
          }`}
        />
        
        {/* Action buttons */}
        <div className="absolute right-3 flex gap-2 z-10">
          {/* Voice input button */}
          <button
            ref={micButtonRef}
            type="button"
            onClick={startListening}
            className={`mic-button flex items-center justify-center p-2 rounded-lg transition-all duration-200 ${
              isListening 
                ? 'bg-red-500 text-white shadow-md shadow-red-600/30' 
                : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
            }`}
            aria-label={isListening ? 'Stop listening' : 'Voice input'}
          >
            {isListening ? (
              <IconMicrophoneOff size={18} className="text-white" />
            ) : (
              <IconMicrophone size={18} />
            )}
          </button>
          
          {/* Submit button */}
          <button
            type="submit"
            disabled={isListening || !value.trim() || isDisabled}
            className={`flex items-center justify-center p-2 rounded-lg transition-all duration-200 shadow-sm ${
              value.trim() && !isListening && !isDisabled
                ? 'bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-600 text-white shadow-md shadow-indigo-600/20' 
                : 'bg-gray-700/80 text-gray-400 cursor-not-allowed'
            }`}
            aria-label="Submit query"
          >
            {value.trim() ? <IconSend size={18} /> : <IconArrowRight size={18} />}
          </button>
        </div>
      </div>
    </form>
  );
};

export default SearchBar; 