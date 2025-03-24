import React, { createContext, useState, useEffect, useCallback } from 'react';
import { API_URL } from '../config';

const AuthContext = createContext();

export default AuthContext;

export const AuthProvider = ({ children }) => {
  const [authTokens, setAuthTokens] = useState(() => {
    const savedTokens = localStorage.getItem('authTokens');
    if (savedTokens) {
      try {
        return JSON.parse(savedTokens);
      } catch (e) {
        console.error('Error parsing auth tokens from localStorage:', e);
      }
    }
    // Fallback to demo tokens
    const demoTokens = {
      access: 'demo_access_token',
      refresh: 'demo_refresh_token'
    };
    localStorage.setItem('authTokens', JSON.stringify(demoTokens));
    return demoTokens;
  });
  
  const [user, setUser] = useState(() => {
    // Always provide a default demo user to avoid undefined user issues
    return {
      id: 1,
      username: 'demo_user',
      name: 'Demo User'
    };
  });
  
  const [loading, setLoading] = useState(true);
  
  // Auto-login as demo user on component mount
  useEffect(() => {
    const loginDemoUser = async () => {
      setLoading(true);
      try {
        console.log('Auto-logging in as demo user...');
        const response = await fetch(`${API_URL}/api/token`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            username: 'demo_user',
            password: 'demo123'
          })
        });
        
        if (response.ok) {
          const data = await response.json();
          console.log('Demo login successful');
          setAuthTokens(data);
          setUser({
            id: 1, // Ensure we always have a user ID
            username: 'demo_user',
            name: 'Demo User'
          });
          localStorage.setItem('authTokens', JSON.stringify(data));
        } else {
          console.error('Failed to auto-login as demo user:', await response.text());
        }
      } catch (err) {
        console.error('Auto-login error:', err);
      } finally {
        setLoading(false);
      }
    };
    
    loginDemoUser();
  }, []);
  
  // Load user profile with demo data backup
  const loadUserProfile = useCallback(async () => {
    const demoProfile = {
      id: 1,
      username: 'demo_user',
      name: 'Demo User',
      gender: 'Other',
      class_year: 2024,
      interests: '{"hiking": true, "dining": true, "movies": true, "study": true}',
      profile_image: 'https://ui-avatars.com/api/?name=Demo+User&background=orange&color=fff'
    };
    
    try {
      console.log('Loading user profile...');
      const response = await fetch(`${API_URL}/api/users/me`, {
        headers: {
          'Authorization': `Bearer ${authTokens?.access}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('Profile loaded successfully');
        return data;
      } else {
        console.log('Falling back to demo profile');
      }
    } catch (error) {
      console.error('Error loading user profile:', error);
    }
    
    return demoProfile;
  }, [authTokens]);

  // Dummy logout function (not needed but kept for compatibility)
  const logoutUser = () => {
    // Do nothing, we don't want to log out of the demo user
    console.log('Logout attempted but ignored to keep demo user logged in');
  };

  const contextData = {
    user,
    authTokens,
    setAuthTokens,
    setUser,
    loading,
    logoutUser,
    loadUserProfile
  };

  return (
    <AuthContext.Provider value={contextData}>
      {children}
    </AuthContext.Provider>
  );
}; 