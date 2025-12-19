import { createContext, useContext, useState, useEffect } from 'react';
import { authService } from '../services/authService';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  // Check authentication on mount
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const storedToken = localStorage.getItem('token');
    if (!storedToken) {
      setLoading(false);
      return;
    }

    try {
      // Decode token to get role info
      const tokenParts = storedToken.split('.');
      if (tokenParts.length === 3) {
        const payload = JSON.parse(atob(tokenParts[1]));

        // Fetch user data from backend
        const userData = await authService.getCurrentUser();

        // Merge token data with user data (role is in token)
        const completeUserData = {
          ...userData,
          role: payload.role,
          user_type: payload.user_type
        };

        setUser(completeUserData);
        setIsAuthenticated(true);
      } else {
        throw new Error('Invalid token format');
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      localStorage.removeItem('token');
      setToken(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    const data = await authService.login(username, password);
    const accessToken = data.access_token;

    localStorage.setItem('token', accessToken);
    setToken(accessToken);

    // Decode token to get role info
    const tokenParts = accessToken.split('.');
    const payload = JSON.parse(atob(tokenParts[1]));

    // Fetch user data
    const userData = await authService.getCurrentUser();

    // Merge token data with user data
    const completeUserData = {
      ...userData,
      role: payload.role,
      user_type: payload.user_type
    };

    setUser(completeUserData);
    setIsAuthenticated(true);

    return completeUserData;
  };

  const logout = () => {
    authService.logout();
    setUser(null);
    setToken(null);
    setIsAuthenticated(false);
  };

  const value = {
    user,
    token,
    isAuthenticated,
    loading,
    login,
    logout,
    checkAuth
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
