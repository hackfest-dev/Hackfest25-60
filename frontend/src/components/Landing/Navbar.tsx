"use client";
import { cn } from "../../lib/utils";
import { IconMenu2, IconX } from "@tabler/icons-react";
import { Search } from "lucide-react";
import {
  motion,
  AnimatePresence,
  useScroll,
  useMotionValueEvent,
} from "motion/react";

import React, { useRef, useState } from "react";

interface NavbarProps {
  children: React.ReactNode;
  className?: string;
}

interface NavBodyProps {
  children: React.ReactNode;
  className?: string;
  visible?: boolean;
}

interface NavItemsProps {
  items: {
    name: string;
    link: string;
  }[];
  className?: string;
  onItemClick?: () => void;
}

interface MobileNavProps {
  children: React.ReactNode;
  className?: string;
  visible?: boolean;
}

interface MobileNavHeaderProps {
  children: React.ReactNode;
  className?: string;
}

interface MobileNavMenuProps {
  children: React.ReactNode;
  className?: string;
  isOpen: boolean;
  onClose: () => void;
}

export const Navbar = ({ children, className }: NavbarProps) => {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollY } = useScroll({
    target: ref,
    offset: ["start start", "end start"],
  });
  const [visible, setVisible] = useState<boolean>(false);
  const [isHovering, setIsHovering] = useState(false);

  useMotionValueEvent(scrollY, "change", (latest) => {
    if (latest > 100) {
      setVisible(true);
    } else {
      setVisible(false);
    }
  });

  return (
    <>
      {/* Add the rainbow border styles */}
      <style>
        {`
          @keyframes rotate {
            0% { background-position: 0% 0%; }
            100% { background-position: 400% 0%; }
          }

          .rainbow-border-container {
            position: relative;
            z-index: 40;
          }

          .rainbow-border {
            position: absolute;
            content: "";
            top: -2px;
            left: -2px;
            right: -2px;
            bottom: -2px;
            z-index: -1;
            border-radius: 9999px;
            background: linear-gradient(90deg, 
              #ff0000, #ff9900, #ffff00, #00ff00, 
              #0099ff, #6633ff, #ff0066, #ff0000, 
              #ff9900, #ffff00, #00ff00, #0099ff);
            background-size: 400% 100%;
            animation: rotate 6s linear infinite;
            opacity: 0;
            transition: opacity 0.7s ease;
          }

          .rainbow-border-active {
            opacity: 0.25;
            filter: blur(4px);
          }

          /* Add rainbow effect to entire page */
          .global-rainbow-trail {
            pointer-events: none;
            position: fixed;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: linear-gradient(90deg, #ff0000, #ff9900, #ffff00, #00ff00, #0099ff, #6633ff, #ff0066);
            background-size: 400% 400%;
            animation: rotate 2s linear infinite;
            opacity: 0.15;
            filter: blur(10px);
            z-index: 9999;
            transition: width 0.2s, height 0.2s;
          }
        `}
      </style>
      
      <motion.div
        ref={ref}
        className={cn("fixed inset-x-0 top-0 z-40 w-full", className)}
        onMouseEnter={() => setIsHovering(true)}
        onMouseLeave={() => setIsHovering(false)}
      >
        {React.Children.map(children, (child) =>
          React.isValidElement(child)
            ? React.cloneElement(
                child as React.ReactElement<{ visible?: boolean; isHovering?: boolean }>,
                { visible, isHovering },
              )
            : child,
        )}
      </motion.div>


      <GlobalRainbowTrail />
    </>
  );
};

const GlobalRainbowTrail = () => {
  const [position, setPosition] = useState({ x: -100, y: -100 });
  
  React.useEffect(() => {
    const updatePosition = (e: MouseEvent) => {
      setPosition({ x: e.clientX - 20, y: e.clientY - 20 });
    };
    
    window.addEventListener('mousemove', updatePosition);
    return () => window.removeEventListener('mousemove', updatePosition);
  }, []);
  
  return (
    <div 
      className="global-rainbow-trail"
      style={{
        left: `${position.x}px`,
        top: `${position.y}px`
      }}
    />
  );
};

export const NavBody = ({
  children,
  className,
  visible,
  isHovering,
}: NavBodyProps & { isHovering?: boolean }) => {
  return (
    <motion.div
      animate={{
        backdropFilter: visible ? "blur(10px)" : "none",
        boxShadow: visible
          ? "0 0 24px rgba(34, 42, 53, 0.06), 0 1px 1px rgba(0, 0, 0, 0.05), 0 0 0 1px rgba(34, 42, 53, 0.04), 0 0 4px rgba(34, 42, 53, 0.08), 0 16px 68px rgba(47, 48, 55, 0.05), 0 1px 0 rgba(255, 255, 255, 0.1) inset"
          : "none",
        width: visible ? "40%" : "100%",
        y: visible ? 20 : 0,
      }}
      transition={{
        type: "spring",
        stiffness: 200,
        damping: 50,
      }}
      style={{
        minWidth: "800px",
        position: "relative",
      }}
      className={cn(
        "rainbow-border-container relative z-[60] mx-auto hidden w-full max-w-7xl flex-row items-center justify-between self-start rounded-full px-[3px] py-[3px] lg:flex",
        visible ? "bg-gray-900/90 backdrop-blur-md" : "bg-gray-900/60 backdrop-blur-sm",
        className,
      )}
    >
      {/* Rainbow border (same as before) */}
      <div
        className={cn(
          "rainbow-border",
          isHovering && "rainbow-border-active"
        )}
      />

      {/* Actual content wrapper to inset everything slightly */}
      <div className="flex w-full flex-row items-center justify-between rounded-full bg-gray-900/90 px-6 py-2">
        {children}
      </div>
    </motion.div>
  );
};



export const NavItems = ({ items, className, onItemClick }: NavItemsProps) => {
  const [hovered, setHovered] = useState<number | null>(null);

  return (
    <motion.div
      onMouseLeave={() => setHovered(null)}
      className={cn(
        "absolute inset-0 hidden flex-1 flex-row items-center justify-center space-x-2 text-sm font-medium text-gray-300 transition duration-200 hover:text-white lg:flex lg:space-x-2",
        className,
      )}
    >
      {items.map((item, idx) => (
        <a
          onMouseEnter={() => setHovered(idx)}
          onClick={onItemClick}
          className="relative px-4 py-2 text-gray-300 hover:text-white"
          key={`link-${idx}`}
          href={item.link}
        >
          {hovered === idx && (
            <motion.div
              layoutId="hovered"
              className="absolute inset-0 h-full w-full rounded-full bg-indigo-500/20"
            />
          )}
          <span className="relative z-20">{item.name}</span>
        </a>
      ))}
    </motion.div>
  );
};

export const MobileNav = ({ children, className, visible }: MobileNavProps) => {
  return (
    <motion.div
      animate={{
        backdropFilter: visible ? "blur(10px)" : "none",
        boxShadow: visible
          ? "0 0 24px rgba(34, 42, 53, 0.06), 0 1px 1px rgba(0, 0, 0, 0.05), 0 0 0 1px rgba(34, 42, 53, 0.04), 0 0 4px rgba(34, 42, 53, 0.08), 0 16px 68px rgba(47, 48, 55, 0.05), 0 1px 0 rgba(255, 255, 255, 0.1) inset"
          : "none",
        width: visible ? "90%" : "100%",
        paddingRight: visible ? "12px" : "0px",
        paddingLeft: visible ? "12px" : "0px",
        borderRadius: visible ? "4px" : "2rem",
        y: visible ? 20 : 0,
      }}
      transition={{
        type: "spring",
        stiffness: 200,
        damping: 50,
      }}
      className={cn(
        "relative z-50 mx-auto flex w-full max-w-[calc(100vw-2rem)] flex-col items-center justify-between bg-transparent px-0 py-2 lg:hidden",
        visible && "bg-gray-900/90 backdrop-blur-md",
        className,
      )}
    >
      {children}
    </motion.div>
  );
};

export const MobileNavHeader = ({
  children,
  className,
}: MobileNavHeaderProps) => {
  return (
    <div
      className={cn(
        "flex w-full flex-row items-center justify-between",
        className,
      )}
    >
      {children}
    </div>
  );
};

export const MobileNavMenu = ({
  children,
  className,
  isOpen,
  onClose,
}: MobileNavMenuProps) => {
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className={cn(
            "absolute inset-x-0 top-16 z-50 flex w-full flex-col items-start justify-start gap-4 rounded-lg bg-gray-900/90 backdrop-blur-md px-4 py-8 shadow-[0_0_24px_rgba(34,_42,_53,_0.06),_0_1px_1px_rgba(0,_0,_0,_0.05),_0_0_0_1px_rgba(34,_42,_53,_0.04),_0_0_4px_rgba(34,_42,_53,_0.08),_0_16px_68px_rgba(47,_48,_55,_0.05),_0_1px_0_rgba(255,_255,_255,_0.1)_inset] border border-gray-800/50",
            className,
          )}
        >
          {children}
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export const MobileNavToggle = ({
  isOpen,
  onClick,
}: {
  isOpen: boolean;
  onClick: () => void;
}) => {
  return isOpen ? (
    <IconX className="text-white" onClick={onClick} />
  ) : (
    <IconMenu2 className="text-white" onClick={onClick} />
  );
};

export const NavbarLogo = () => {
  return (
    <a
      href="#"
      className="relative z-20 mr-4 flex items-center space-x-2 px-2 py-1 text-sm font-normal text-black group"
    >
      <div className="w-8 h-8 flex items-center justify-center rounded-full bg-indigo-500/20 border border-indigo-500/40 transition-all duration-300 group-hover:bg-indigo-500/30 group-hover:border-indigo-500/60 group-hover:scale-110 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/10 to-purple-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
        <Search className="w-4 h-4 text-indigo-400 relative z-10 transition-all duration-300 group-hover:text-indigo-300" />
      </div>
      <span className="font-medium text-white">
        <span className="transition-all duration-300 group-hover:text-indigo-300">Searchify</span>
        <span className="text-indigo-400 transition-all duration-300 group-hover:text-indigo-300">.AI</span>
      </span>
    </a>
  );
};

export const NavbarButton = ({
  href,
  as: Tag = "a",
  children,
  className,
  variant = "primary",
  ...props
}: {
  href?: string;
  as?: React.ElementType;
  children: React.ReactNode;
  className?: string;
  variant?: "primary" | "secondary" | "dark" | "gradient";
} & (
  | React.ComponentPropsWithoutRef<"a">
  | React.ComponentPropsWithoutRef<"button">
)) => {
  const baseStyles =
    "px-4 py-2 rounded-md text-sm font-bold relative cursor-pointer hover:-translate-y-0.5 transition-all duration-300 inline-block text-center overflow-hidden";

  const variantStyles = {
    primary:
      "bg-indigo-500 text-white hover:bg-indigo-600 shadow-lg shadow-indigo-500/20 hover:shadow-xl hover:shadow-indigo-500/30",
    secondary: "bg-transparent text-gray-300 hover:text-white",
    dark: "bg-gray-800 text-white hover:bg-gray-700 border border-gray-700",
    gradient:
      "bg-gradient-to-r from-indigo-600 to-violet-600 text-white shadow-lg shadow-indigo-500/20 hover:shadow-xl hover:shadow-indigo-500/30",
  };

  return (
    <Tag
      href={href || undefined}
      className={cn(baseStyles, variantStyles[variant], className)}
      {...props}
    >
      <span className="relative z-10">{children}</span>
      {(variant === "primary" || variant === "gradient") && (
        <span className="absolute inset-0 opacity-0 hover:opacity-100 transition-opacity duration-300 bg-gradient-to-tr from-indigo-600/80 to-violet-600/80"></span>
      )}
    </Tag>
  );
};
