import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authAPI } from '../services/api';
import { useNavigate } from 'react-router-dom';

interface User {
  id: number;
  name: string;
  email: string;
  username: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  signup: (userData: any) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  // Fetch user profile function
  const fetchUserProfile = async () => {
    try {
      const token = localStorage.getItem('accessToken');
      if (token) {
        // Call the API to get user profile
        const userData = await authAPI.getUserProfile();
        
        if (userData) {
          setUser(userData);
          return true;
        } else {
          // If user data couldn't be fetched, clear token
          localStorage.removeItem('accessToken');
          return false;
        }
      }
      return false;
    } catch (error) {
      console.error('Authentication check failed:', error);
      localStorage.removeItem('accessToken');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  // Check if user is already logged in
  useEffect(() => {
    fetchUserProfile();
  }, []);

  const login = async (username: string, password: string) => {
    setIsLoading(true);
    try {
      await authAPI.login(username, password);
      // After successful login, fetch user profile
      const success = await fetchUserProfile();
      
      if (success) {
        navigate('/chat');
      } else {
        throw new Error('Failed to get user profile after login');
      }
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const signup = async (userData: any) => {
    setIsLoading(true);
    try {
      await authAPI.signup(userData);
      // After signup, user still needs to login
    } catch (error) {
      console.error('Signup failed:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      await authAPI.logout();
      setUser(null);
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
      // Even if server logout fails, clear local session
      localStorage.removeItem('accessToken');
      setUser(null);
      navigate('/login');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        signup,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext; 