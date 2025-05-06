import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

// Layouts and Pages
import MainLayout from './components/layouts/MainLayout';
import Profile from './pages/Profile';
import EditProfile from './pages/EditProfile';
import Experiences from './pages/Experiences';
import AddExperience from './pages/AddExperience';
import Swipe from './pages/Swipe';
import Matches from './pages/Matches';
import NotFound from './pages/NotFound';
import Login from './pages/Login';
import CASCallback from './pages/CASCallback';
import CASSuccess from './pages/CASSuccess';
import Onboarding from './pages/Onboarding';
import Preferences from './pages/Preferences';
import axios from 'axios';

// Context Provider
import { AuthProvider, useAuth } from './context/AuthContext';
import { API_URL } from './config'

// Create CSRF Token Context
const CSRFTokenContext = React.createContext(null);
export const useCSRFToken = () => React.useContext(CSRFTokenContext);

// Wrapper component that enforces authentication
const AppWrapper = ({ children }) => {
  const { user, authLoading, loadUserProfile } = useAuth();
  
  // While checking authentication status, show loading
  if (authLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gradient-to-br from-orange-50 to-orange-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-orange-500 mx-auto mb-4"></div>
          <p className="text-orange-800 font-medium">Loading your profile...</p>
        </div>
      </div>
    );
  }
  
  // If not authenticated, redirect to login
  if (!user) {
    return <Navigate to="/login" />;
  }
  
  // Check if user needs to complete onboarding
  // Using explicit check for false to avoid issues with undefined/null
  if (user.onboarding_completed === false) {
    console.log("User needs to complete onboarding, redirecting...");
    return <Navigate to="/onboarding" />;
  }
  
  // Otherwise, render the children
  return children;
};

function App() {
  const [csrfToken, setCSRFToken] = useState(null);
  const [tokenLoading, setTokenLoading] = useState(true);

  // Fetch CSRF token when component mounts
  useEffect(() => {
    const fetchCSRFToken = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/csrf-token`)
        if (response.status === 200) {
          setCSRFToken(response.data.csrf_token);
        } else {
          console.error('Failed to fetch CSRF token');
        }
      } catch (error) {
        console.error('Error fetching CSRF token:', error);
      } finally {
        setTokenLoading(false);
      }
    };

    fetchCSRFToken();
  }, []);

  // Show loading state while fetching token
  if (tokenLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gradient-to-br from-orange-50 to-orange-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-orange-500 mx-auto mb-4"></div>
          <p className="text-orange-800 font-medium">Loading application...</p>
        </div>
      </div>
    );
  }

  return (
    <Router>
      <CSRFTokenContext.Provider value={csrfToken}>
        <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/cas/callback" element={<CASCallback />} />
          <Route path="/cas/success" element={<CASSuccess />} />
          <Route path="/onboarding" element={<Onboarding />} />
          
          {/* Redirect root to login if not authenticated */}
          <Route path="/" element={
            <AppWrapper>
              <MainLayout />
            </AppWrapper>
          }>
            {/* Redirect root path to swipe for authenticated users */}
            <Route index element={<Navigate to="/swipe" replace />} />
            <Route path="profile" element={<Profile />} />
            <Route path="profile/edit" element={<EditProfile />} />
            <Route path="profile/preferences" element={<Preferences />} />
            <Route path="experiences" element={<Experiences />} />
            <Route path="experiences/add" element={<AddExperience />} />
            <Route path="swipe" element={<Swipe />} />
            <Route path="matches" element={<Matches />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </AuthProvider>
      </CSRFTokenContext.Provider>
    </Router>
  );
}

export default App; 