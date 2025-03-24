import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

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

// Context Provider
import { AuthProvider } from './context/AuthContext';

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          {/* Public paths */}
          <Route path="/" element={<MainLayout />}>
            <Route path="/" element={<Home />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/profile/edit" element={<EditProfile />} />
            <Route path="/experiences" element={<Experiences />} />
            <Route path="/experiences/add" element={<AddExperience />} />
            <Route path="/swipe" element={<Swipe />} />
            <Route path="/matches" element={<Matches />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App; 