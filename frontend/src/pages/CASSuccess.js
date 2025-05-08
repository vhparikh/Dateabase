import React, { useEffect, useContext, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import AuthContext from '../context/AuthContext';

const CASSuccess = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { loadUserProfile } = useContext(AuthContext);
  const [error, setError] = useState('');

  useEffect(() => {
    // Reload the user profile to ensure we have the latest data
    const loadProfile = async () => {
      try {
        // Get callback URL from state if available
        const callbackUrl = location.state?.callbackUrl || '/';
        
        // Load the user profile
        const profileData = await loadUserProfile();
        
        if (profileData) {
          // console.log('Profile loaded successfully after CAS login');
          // Redirect to home or the callback URL
          navigate(callbackUrl);
        } else {
          setError('Failed to load your profile. Please try again.');
        }
      } catch (err) {
        // console.error('Error loading user profile after CAS login:', err);
        setError('An error occurred while loading your profile. Please try again.');
      }
    };
    
    loadProfile();
  }, [navigate, loadUserProfile, location.state]);
  
  return (
    <div className="flex items-center justify-center min-h-screen bg-white-gradient px-4 py-12">
      <div className="w-full max-w-md z-10 text-center">
        {error ? (
          <>
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
              <p>{error}</p>
            </div>
            <button 
              onClick={() => navigate('/login')} 
              className="bg-orange-500 text-white px-4 py-2 rounded hover:bg-orange-600 transition-colors"
            >
              Return to Login
            </button>
          </>
        ) : (
          <>
            <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-orange-500 mx-auto mb-4"></div>
            <p className="text-gray-700 text-lg font-medium">Loading your profile...</p>
          </>
        )}
      </div>
    </div>
  );
};

export default CASSuccess; 