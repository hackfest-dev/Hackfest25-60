"use client";
import React from "react";
import { SparklesCore } from "../ui/sparkles";

export default function SparklesBackground() {
  return (
    <div className="absolute inset-0 w-full h-full overflow-hidden">
      {/* Core component - with much higher particle density and larger size for visibility */}
      <SparklesCore
        background="transparent"
        minSize={0.2}             // Larger minimum size
        maxSize={1}             // Much larger maximum size
        particleDensity={60}   // Dramatically increased particle density
        className="w-full h-full"
        particleColor="#FFFFFF"   // Pure white color
        speed={0.4}               // Medium speed for better visibility
      />
     
      
      {/* Lighter vignette overlay to allow more sparkles to show through */}
      <div className="absolute inset-0 bg-gradient-to-b from-gray-950 via-transparent to-gray-950 opacity-30"></div>
    </div>
  );
}
