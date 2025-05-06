import React, { createContext, useState, useEffect, useCallback, useContext } from 'react';
import { API_URL } from '../config';
import { useCSRFToken } from '../App';
import axios from 'axios';

const AuthContext = createContext();

// custom hook to use the auth context
export const useAuth = () => useContext(AuthContext);

export default AuthContext;

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authLoading, setAuthLoading] = useState(true);
  const [casAuthenticated, setCasAuthenticated] = useState(false);

  const csrfToken = useCSRFToken()
  
  // Check CAS authentication status 
  useEffect(() => {
    const checkAuthStatus = async () => {
      setLoading(true);
      setAuthLoading(true);
      try {
        // Check if the user is authenticated with CAS
        const response = await axios.get(`${API_URL}/api/cas/status`, {
          withCredentials: true, // important for session cookies
          headers: {
            'Content-Type': 'application/json',
            'X-CsrfToken': csrfToken
          }
        });
        
        if (response.status === 200) {
          const data = response.data;
          setCasAuthenticated(data.authenticated);
          
          // If authenticated, load user profile
          if (data.authenticated) {
            const profileResponse = await axios.get(`${API_URL}/api/me`, {
              withCredentials: true,
              headers: {
                'Content-Type': 'application/json',
                'X-CsrfToken': csrfToken
              }
            });
            
            if (profileResponse.status === 200) {
              const profileData = profileResponse.data;
              console.log('User profile loaded');
              setUser(profileData);
            }
          } else {
            // Not authenticated with CAS, clear user data
            console.log('Not authenticated with CAS, redirecting to login');
            setUser(null);
          }
        } else {
          // Failed to check authentication status
          console.log('Failed to check authentication status');
          setUser(null);
        }
      } catch (err) {
        console.error('Auth status check error:', err);
        setUser(null);
      } finally {
        setLoading(false);
        setAuthLoading(false);
      }
    };
    
    checkAuthStatus();
  }, []);
  
  // load user profile - gets current user profile from backend
  const loadUserProfile = useCallback(async () => {
    try {
      console.log('Loading user profile...');
      // Use our API service with the new endpoint
      const { getCurrentUser } = await import('../services/api');
      const response = await getCurrentUser();
      
      if (response && response.data) {
        console.log('Profile loaded successfully:', response.data);
        // ake sure we have the onboarding_completed status
        if (response.data.onboarding_completed === undefined) {
          console.warn('onboarding_completed status missing in user profile');
        }
        // ensure we update the user state with the complete profile data
        setUser(response.data);
        return response.data;
      } else {
        console.log('Error loading profile: No data returned');
        // earlier, returning a fallback profile, now show error instead
        setUser(null);
        return null;
      }
    } catch (error) {
      console.error('Error loading user profile:', error.response?.data?.detail || error.message);
      setUser(null);
      return null;
    }
  }, []);

  // initiate CAS login
  const loginWithCAS = async (callback_url = '/') => {
    try {
      const response = await axios.get(`${API_URL}/api/cas/login?callback_url=${encodeURIComponent(callback_url)}`, {
        headers: {
          'Content-Type': 'application/json',
          'X-CsrfToken': csrfToken
        }
      });
      if (response.status === 200) {
        const data = response.data;
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
      const casSuccess = params?.get('cas_success') === 'true';
      
      // If we have cas_success=true, we know the backend has already authenticated the user
      // This happens when redirected from the backend CAS callback
      if (casSuccess) {
        console.log('Authentication already confirmed by backend');
        setCasAuthenticated(true);
      } else if (!ticket) {
        console.warn('No CAS ticket and no success confirmation found');
      }
      
      // First, check if the user is authenticated with CAS
      const statusResponse = await axios.get(`${API_URL}/api/cas/status`, {
        headers: {
          'Content-Type': 'application/json',
          'X-CsrfToken': csrfToken
        }
      });
      
      if (statusResponse.status === 200) {
        const statusData = statusResponse.data;
        
        if (statusData.authenticated) {
          setCasAuthenticated(true);
          
          // Load user profile
          const userProfile = await loadUserProfile();
          
          if (userProfile) {
            // Check if onboarding is needed (from URL param or user profile)
            const needsOnboardingFromProfile = userProfile.onboarding_completed === false;
            const redirectToOnboarding = needsOnboarding || needsOnboardingFromProfile;
            
            return {
              success: true,
              callback_url: redirectToOnboarding ? '/onboarding' : '/swipe',
              needs_onboarding: redirectToOnboarding
            };
          }
        } else {
          console.error('Backend reports user is not authenticated');
        }
      } else {
        console.error('Failed to check authentication status with backend');
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
      // Determine our current frontend URL for redirecting after CAS logout
      const currentUrl = window.location.origin;
      const loginUrl = `${currentUrl}/login`;
      
      // Logout from backend session
      const response = await axios.get(`${API_URL}/api/cas/logout?frontend_url=${encodeURIComponent(currentUrl)}`, {
        headers: {
          'Content-Type': 'application/json',
          'X-CsrfToken': csrfToken
        }
      });
      
      // Clear state
      setUser(null);
      setCasAuthenticated(false);
      
      // Get the CAS logout URL from response
      if (response.status === 200) {
        const data = response.data;
        console.log('Logout successful, received logout URL:', data.logout_url);
        return data;  // Return data containing logout_url
      }
      
      return { logout_url: loginUrl }; // Fallback to direct login URL
    } catch (error) {
      console.error('Error logging out:', error);
      // Even on error, try to redirect to login
      return { logout_url: window.location.origin + '/login' };
    }
  };

  const contextData = {
    user,
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