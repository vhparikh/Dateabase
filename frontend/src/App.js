import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

// Layouts and Pages
import MainLayout from './components/layouts/MainLayout';
import Home from './pages/Home';
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

// Context Provider
import { AuthProvider, useAuth } from './context/AuthContext';

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { user } = useAuth();
  
  if (!user) {
    // Redirect to login if not authenticated
    return <Navigate to="/login" />;
  }
  
  return children;
};

// Wrapper component that enforces authentication
const AppWrapper = ({ children }) => {
  const { user, authLoading } = useAuth();
  
  // While checking authentication status, show nothing
  if (authLoading) {
    return <div className="flex h-screen items-center justify-center">Loading...</div>;
  }
  
  // If not authenticated, redirect to login
  if (!user) {
    return <Navigate to="/login" />;
  }
  
  // Check if user needs to complete onboarding
  // First check the user object from the server, which takes priority
  if (user && user.onboarding_completed === false) {
    console.log("User needs to complete onboarding (based on server data), redirecting...");
    return <Navigate to="/onboarding" />;
  }
  
  // Only use localStorage as a fallback if user object doesn't have onboarding status
  const onboardingCompleted = localStorage.getItem('onboardingCompleted') === 'true';
  if (user && user.onboarding_completed === undefined && !onboardingCompleted) {
    console.log("User needs to complete onboarding (based on localStorage), redirecting...");
    return <Navigate to="/onboarding" />;
  }
  
  // Otherwise, render the children
  return children;
};

function App() {
  return (
    <Router>
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
            <Route path="experiences" element={<Experiences />} />
            <Route path="experiences/add" element={<AddExperience />} />
            <Route path="swipe" element={<Swipe />} />
            <Route path="matches" element={<Matches />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App; 