import { useState, useEffect } from 'react';
import { authAPI } from '../services/api';

interface AuthState {
  isAuthenticated: boolean;
  user: any | null;
}

export const useAuth = () => {
  const [authState, setAuthState] = useState<AuthState>({
    isAuthenticated: false,
    user: null,
  });

  useEffect(() => {
    // Check authentication status when the hook is mounted
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const userData = await authAPI.verify();
      
      if (userData) {
        setAuthState({
          isAuthenticated: true,
          user: userData,
        });
      } else {
        setAuthState({
          isAuthenticated: false,
          user: null,
        });
      }
    } catch (error) {
      console.error('Auth status check failed:', error);
      setAuthState({
        isAuthenticated: false,
        user: null,
      });
    }
  };

  const login = async (credentials: { email: string; password: string }) => {
    try {
      // Use the API service for login
      const userData = await authAPI.login(credentials.email, credentials.password);
      
      if (userData) {
        setAuthState({
          isAuthenticated: true,
          user: userData,
        });
        return true;
      }
      return false;
    } catch (error) {
      console.error('Login failed:', error);
      return false;
    }
  };

  const signup = async (userData: { email: string; password: string; username: string; name: string }) => {
    try {
      const user = await authAPI.signup(userData);
      
      if (user) {
        setAuthState({
          isAuthenticated: true,
          user,
        });
        return true;
      }
      return false;
    } catch (error) {
      console.error('Signup failed:', error);
      return false;
    }
  };

  const logout = async () => {
    try {
      await authAPI.logout();
      setAuthState({
        isAuthenticated: false,
        user: null,
      });
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return {
    ...authState,
    login,
    signup,
    logout,
  };
}; 