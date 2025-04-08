import React, { createContext, useState, useEffect, useCallback, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { API_URL } from '../config';

const AuthContext = createContext();

// Custom hook to use the auth context
export const useAuth = () => useContext(AuthContext);

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
    // Return null instead of fallback tokens
    return null;
  });
  
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authLoading, setAuthLoading] = useState(true);
  const [casAuthenticated, setCasAuthenticated] = useState(false);
  
  // Check CAS authentication status on mount
  useEffect(() => {
    const checkAuthStatus = async () => {
      setLoading(true);
      setAuthLoading(true);
      try {
        // Check if the user is authenticated with CAS
        const response = await fetch(`${API_URL}/api/cas/status`, {
          credentials: 'include' // Important for session cookies
        });
        
        if (response.ok) {
          const data = await response.json();
          setCasAuthenticated(data.authenticated);
          
          // If authenticated, load user profile
          if (data.authenticated) {
            const profileResponse = await fetch(`${API_URL}/api/users/me`, {
              credentials: 'include'
            });
            
            if (profileResponse.ok) {
              const profileData = await profileResponse.json();
              console.log('User profile loaded');
              setUser(profileData);
              
              // Generate tokens if needed
              if (!authTokens) {
                const tokenResponse = await fetch(`${API_URL}/api/token/refresh`, {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json'
                  },
                  credentials: 'include',
                  body: JSON.stringify({})
                });
                
                if (tokenResponse.ok) {
                  const tokenData = await tokenResponse.json();
                  setAuthTokens(tokenData);
                  localStorage.setItem('authTokens', JSON.stringify(tokenData));
                }
              }
            }
          } else {
            // Not authenticated with CAS, clear any stored tokens
            console.log('Not authenticated with CAS, redirecting to login');
            setUser(null);
            setAuthTokens(null);
            localStorage.removeItem('authTokens');
          }
        } else {
          // Failed to check authentication status
          console.log('Failed to check authentication status');
          setUser(null);
          setAuthTokens(null);
          localStorage.removeItem('authTokens');
        }
      } catch (err) {
        console.error('Auth status check error:', err);
        setUser(null);
        setAuthTokens(null);
        localStorage.removeItem('authTokens');
      } finally {
        setLoading(false);
        setAuthLoading(false);
      }
    };
    
    checkAuthStatus();
  }, []);
  
  // Load user profile - gets current user profile from backend
  const loadUserProfile = useCallback(async () => {
    try {
      console.log('Loading user profile...');
      // Use our API service with the new endpoint
      const { getCurrentUser } = await import('../services/api');
      const response = await getCurrentUser();
      
      if (response && response.data) {
        console.log('Profile loaded successfully');
        setUser(response.data);
        return response.data;
      } else {
        console.log('Error loading profile: No data returned');
        // Don't return a fallback profile, signal error instead
        setUser(null);
        return null;
      }
    } catch (error) {
      console.error('Error loading user profile:', error.response?.data?.detail || error.message);
      setUser(null);
      return null;
    }
  }, []);

  // Initiate CAS login
  const loginWithCAS = async (callback_url = '/') => {
    try {
      const response = await fetch(`${API_URL}/api/cas/login?callback_url=${encodeURIComponent(callback_url)}`);
      if (response.ok) {
        const data = await response.json();
        // Redirect to CAS login URL
        window.location.href = data.login_url;
        return true;
      }
      return false;
    } catch (error) {
      console.error('Error initiating CAS login:', error);
      return false;
    }
  };
  
  // Handle CAS callback with ticket
  const handleCASCallback = async (ticket, params) => {
    try {
      // Get needs_onboarding from URL params if available
      const needsOnboarding = params?.get('needs_onboarding') === 'true';
      
      // First, check if the user is authenticated with CAS
      const statusResponse = await fetch(`${API_URL}/api/cas/status`, {
        credentials: 'include'
      });
      
      if (statusResponse.ok) {
        const statusData = await statusResponse.json();
        
        if (statusData.authenticated) {
          setCasAuthenticated(true);
          
          // Load user profile
          const userProfile = await loadUserProfile();
          
          if (userProfile) {
            // Generate access token
            const tokenResponse = await fetch(`${API_URL}/api/token/refresh`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              credentials: 'include',
              body: JSON.stringify({})
            });
            
            if (tokenResponse.ok) {
              const tokenData = await tokenResponse.json();
              setAuthTokens(tokenData);
              localStorage.setItem('authTokens', JSON.stringify(tokenData));
            }
            
            // Check if onboarding is needed (from URL param or user profile)
            const needsOnboardingFromProfile = userProfile.onboarding_completed === false;
            const redirectToOnboarding = needsOnboarding || needsOnboardingFromProfile;
            
            return {
              success: true,
              callback_url: redirectToOnboarding ? '/onboarding' : '/',
              needs_onboarding: redirectToOnboarding
            };
          }
        }
      }
      
      return { success: false, message: 'Authentication failed' };
    } catch (error) {
      console.error('Error handling CAS callback:', error);
      return { success: false, message: error.message || 'Authentication error' };
    }
  };
  
  // Logout from CAS and the application
  const logoutUser = async () => {
    try {
      // Logout from backend session
      const response = await fetch(`${API_URL}/api/cas/logout`, {
        credentials: 'include'
      });
      
      // Clear local storage and state
      localStorage.removeItem('authTokens');
      setAuthTokens(null);
      setUser(null);
      setCasAuthenticated(false);
      
      // Get the CAS logout URL from response
      if (response.ok) {
        const data = await response.json();
        return data;  // Return data containing logout_url
      }
      
      return true;
    } catch (error) {
      console.error('Error logging out:', error);
      return false;
    }
  };

  const contextData = {
    user,
    authTokens,
    setAuthTokens,
    setUser,
    loading,
    authLoading,
    logoutUser,
    loadUserProfile,
    loginWithCAS,
    handleCASCallback,
    casAuthenticated
  };

  return (
    <AuthContext.Provider value={contextData}>
      {children}
    </AuthContext.Provider>
  );
}; 