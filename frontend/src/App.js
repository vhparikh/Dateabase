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
          
          {/* Redirect root to login if not authenticated */}
          <Route path="/" element={
            <AppWrapper>
              <MainLayout />
            </AppWrapper>
          }>
            <Route index element={<Home />} />
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