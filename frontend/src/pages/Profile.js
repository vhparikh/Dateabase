import React, { useContext, useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import AuthContext from '../context/AuthContext';
import { getExperiences } from '../services/api';
import ProfileImageUpload from '../components/ProfileImageUpload';
import { API_URL } from '../config';
import axios from 'axios';
import { useCSRFToken } from '../App';

const Profile = () => {
  const { user, logoutUser } = useContext(AuthContext);
  const navigate = useNavigate();
  const [userProfile, setUserProfile] = useState(user); // Initialize with current context user
  const [activeTab, setActiveTab] = useState('profile'); // New state for tab management
  const csrfToken = useCSRFToken();
  
  // Fetch user profile directly from the API to ensure latest data
  useEffect(() => {
    const fetchUserProfile = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/me`, {withCredentials: true, headers: {
          'Content-Type': 'application/json',
          'X-CsrfToken': csrfToken
        }});
        
        // Fetch user images
        try {
          const imagesResponse = await axios.get(`${API_URL}/api/users/images`, { withCredentials: true, headers: {'X-CsrfToken': csrfToken}});
          
          if (imagesResponse.status === 200) {
            const imagesData = imagesResponse.data;
            // Update user profile with images
            setUserProfile({
              ...response.data,
              images: imagesData
            });
          } else {
            // Still set user profile even if images fetch fails
            setUserProfile(response.data);
          }
        } catch (imgErr) {
          console.error('Failed to load user images', imgErr);
          // Still set user profile even if images fetch fails
          setUserProfile(response.data);
        }
      } catch (err) {
        console.error('Failed to load user profile', err);
      }
    };
    
    fetchUserProfile();
  }, [csrfToken]);
  
  // Fetch user experiences
  useEffect(() => {
    const fetchUserExperiences = async () => {
      if (!userProfile || !userProfile.id) return;
      
      try {
        const response = await getExperiences();
        // We don't need to store experiences in this component anymore
      } catch (err) {
        console.error('Failed to load experiences', err);
      }
    };
    
    fetchUserExperiences();
  }, [userProfile]);
  
  const handleLogout = async () => {
    try {
      const result = await logoutUser();
      if (result && result.logout_url) {
        console.log('Redirecting to CAS logout URL with redirect to login page:', result.logout_url);
        // Add a local redirect first to ensure we clean up local state
        localStorage.removeItem('lastAuthenticated'); // Clear any auth timestamps
        
        // Redirect to CAS logout URL which will then redirect back to login page
        window.location.href = result.logout_url;
      } else {
        console.log('No logout URL returned, redirecting directly to login page');
        // Fallback to just redirecting to login page
        navigate('/login');
      }
    } catch (error) {
      console.error('Error during logout:', error);
      // Fallback to just redirecting to login page
      navigate('/login');
    }
  };
  
  // Function to parse and render interest badges
  const renderInterests = () => {
    if (!userProfile?.interests) return null;
    
    let interestsObj = {};
    try {
      // Try to parse if it's a JSON string
      interestsObj = JSON.parse(userProfile.interests);
    } catch (e) {
      // If it's not valid JSON, try a different approach
      try {
        // Try to parse as comma-separated values
        const interests = userProfile.interests.split(',').map(item => item.trim());
        interests.forEach(interest => {
          interestsObj[interest] = true;
        });
      } catch (err) {
        return null;
      }
    }
    
    // Convert to array of interest names - only ones that are true
    const interestNames = Object.keys(interestsObj).filter(key => interestsObj[key] === true);
    
    return (
      <div className="flex flex-wrap gap-2 mt-3">
        {interestNames.map(interest => (
          <span 
            key={interest} 
            className="px-3 py-1 bg-orange-50 text-orange-800 rounded-full text-sm font-medium"
          >
            {interest.charAt(0).toUpperCase() + interest.slice(1)}
          </span>
        ))}
      </div>
    );
  };
  
  // Function to get a random gradient for experience cards
  const getRandomGradient = () => {
    const gradients = [
      'border-t-orange-500',
      'border-t-orange-400',
      'border-t-orange-600',
      'border-t-accent-light',
    ];
    return gradients[Math.floor(Math.random() * gradients.length)];
  };
  
  // Determine if we have a profile image to show
  const hasProfileImage = userProfile?.profile_image || 
    (userProfile?.images && userProfile.images.length > 0 && 
    userProfile.images.find(img => img.position === 0));
  
  // Get profile image URL (prefer the main profile image URL if it exists)
  const getProfileImageUrl = () => {
    if (userProfile?.profile_image) {
      return userProfile.profile_image;
    }
    
    if (userProfile?.images && userProfile.images.length > 0) {
      const mainImage = userProfile.images.find(img => img.position === 0);
      if (mainImage) return mainImage.url;
      
      // If no main image but we have images, use the first one
      return userProfile.images[0].url;
    }
    
    return null;
  };
  
  // Function to handle tab switching
  const handleTabChange = (tab) => {
    if (tab === 'preferences') {
      navigate('/profile/preferences');
    } else {
      setActiveTab(tab);
    }
  };
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-orange-100 py-6">
      <div className="max-w-5xl mx-auto px-4 sm:px-6">
        <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <h1 className="text-3xl font-bold text-gray-900 mb-2 sm:mb-0">Your Profile</h1>
          <div className="flex space-x-2">
            <Link 
              to="/profile/edit" 
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-full shadow-sm text-white bg-orange-600 hover:bg-orange-700 focus:outline-none"
            >
              Edit Profile
            </Link>
            <button
              onClick={handleLogout}
              className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-full shadow-sm text-gray-700 bg-white hover:bg-gray-50 focus:outline-none"
            >
              Logout
            </button>
          </div>
        </div>
        
        {/* Tab navigation */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-6">
            <button
              onClick={() => handleTabChange('profile')}
              className={`pb-3 px-1 font-medium text-sm ${
                activeTab === 'profile'
                  ? 'border-b-2 border-orange-500 text-orange-600'
                  : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Profile
            </button>
            <button
              onClick={() => handleTabChange('preferences')}
              className={`pb-3 px-1 font-medium text-sm ${
                activeTab === 'preferences'
                  ? 'border-b-2 border-orange-500 text-orange-600'
                  : 'text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Preferences
            </button>
          </nav>
        </div>
        
        {/* Profile Header */}
        <div className="bg-white rounded-xl shadow-card mb-8 p-6">
          <div className="flex flex-col md:flex-row items-center">
            {hasProfileImage ? (
              <div className="w-28 h-28 md:w-32 md:h-32 rounded-full overflow-hidden shadow-md">
                <img 
                  src={getProfileImageUrl()} 
                  alt={`${userProfile?.name || 'User'}'s profile`}
                  className="w-full h-full object-cover" 
                />
              </div>
            ) : (
              <div className="w-28 h-28 md:w-32 md:h-32 bg-gradient-to-r from-orange-start to-orange-end rounded-full flex items-center justify-center text-white text-4xl font-bold shadow-md">
                {userProfile?.name ? userProfile.name.charAt(0).toUpperCase() : 'U'}
              </div>
            )}
            
            <div className="ml-0 md:ml-8 mt-6 md:mt-0 text-center md:text-left">
              <h1 className="text-3xl font-bold text-gray-800">{userProfile?.name || 'User'}</h1>
              
              <div className="mt-4 flex flex-wrap gap-2 justify-center md:justify-start">
                {renderInterests()}
              </div>
            </div>
          </div>
        </div>
        
        {/* Profile Information */}
        <div className="bg-white rounded-xl shadow-card p-6">
          <h2 className="text-2xl font-bold mb-6 text-gray-800">Profile Information</h2>
          
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-gray-700 mb-2">Name</h3>
              <p className="bg-orange-50 rounded-lg p-3 border border-orange-100 text-gray-800">{userProfile?.name || 'Not set'}</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-lg font-medium text-gray-700 mb-2">Gender</h3>
                <p className="bg-orange-50 rounded-lg p-3 border border-orange-100 text-gray-800">{userProfile?.gender || 'Not set'}</p>
              </div>
              
              <div>
                <h3 className="text-lg font-medium text-gray-700 mb-2">Sexuality</h3>
                <p className="bg-orange-50 rounded-lg p-3 border border-orange-100 text-gray-800">{userProfile?.sexuality || 'Not set'}</p>
              </div>
            </div>
            
            <div>
              <h3 className="text-lg font-medium text-gray-700 mb-2">Height</h3>
              <p className="bg-orange-50 rounded-lg p-3 border border-orange-100 text-gray-800">
                {userProfile?.height ? 
                  `${userProfile.height} cm (${Math.floor(userProfile.height / 30.48)} ft ${Math.round(userProfile.height % 30.48 / 2.54)} in)` 
                  : 'Not set'}
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-lg font-medium text-gray-700 mb-2">NetID</h3>
                <p className="bg-orange-50 rounded-lg p-3 border border-orange-100 text-gray-800">{userProfile?.netid || 'Not set'}</p>
              </div>
              
              <div>
                <h3 className="text-lg font-medium text-gray-700 mb-2">Class Year</h3>
                <p className="bg-orange-50 rounded-lg p-3 border border-orange-100 text-gray-800">{userProfile?.class_year || 'Not set'}</p>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-lg font-medium text-gray-700 mb-2">Current Location</h3>
                <p className="bg-orange-50 rounded-lg p-3 border border-orange-100 text-gray-800">{userProfile?.location || 'Not set'}</p>
              </div>
              
              <div>
                <h3 className="text-lg font-medium text-gray-700 mb-2">Hometown</h3>
                <p className="bg-orange-50 rounded-lg p-3 border border-orange-100 text-gray-800">{userProfile?.hometown || 'Not set'}</p>
              </div>
            </div>

            <div>
              <h3 className="text-lg font-medium text-gray-700 mb-2">Major</h3>
              <p className="bg-orange-50 rounded-lg p-3 border border-orange-100 text-gray-800">{userProfile?.major || 'Not set'}</p>
            </div>
            
            <div>
              <h3 className="text-lg font-medium text-gray-700 mb-2">Interests</h3>
              {renderInterests() || (
                <p className="bg-orange-50 rounded-lg p-3 border border-orange-100 text-gray-800">No interests added yet</p>
              )}
            </div>

            {/* Contact Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-6 border-t border-gray-200">
              <div>
                <h3 className="text-lg font-medium text-gray-700 mb-2">Phone Number</h3>
                <p className="bg-orange-50 rounded-lg p-3 border border-orange-100 text-gray-800">
                  {userProfile?.phone_number || 'Not set'}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Visible only to confirmed matches
                </p>
              </div>
              
              <div>
                <h3 className="text-lg font-medium text-gray-700 mb-2">Email</h3>
                <p className="bg-orange-50 rounded-lg p-3 border border-orange-100 text-gray-800">
                  {userProfile?.preferred_email || 'Not set'}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Visible only to confirmed matches
                </p>
              </div>
            </div>

            {/* Profile Images */}
            <div className="pt-6 border-t border-gray-200">
              <ProfileImageUpload 
                userId={userProfile?.id} 
                onImageUploaded={(image) => {
                  // Update profile image in state if it's the main photo
                  if (image.position === 0) {
                    setUserProfile({
                      ...userProfile,
                      profile_image: image.url
                    });
                  }
                }}
              />
            </div>
            
            {/* Prompt Responses */}
            <div className="mt-8">
              <h3 className="text-xl font-bold text-gray-800 mb-4">About Me</h3>
              
              {userProfile?.prompt1 && userProfile?.answer1 && (
                <div className="bg-gradient-to-r from-orange-50 to-amber-50 rounded-lg p-4 mb-4 border border-orange-100">
                  <h4 className="font-medium text-orange-700 mb-2">{userProfile.prompt1}</h4>
                  <p className="text-gray-800">{userProfile.answer1}</p>
                </div>
              )}
              
              {userProfile?.prompt2 && userProfile?.answer2 && (
                <div className="bg-gradient-to-r from-orange-50 to-amber-50 rounded-lg p-4 mb-4 border border-orange-100">
                  <h4 className="font-medium text-orange-700 mb-2">{userProfile.prompt2}</h4>
                  <p className="text-gray-800">{userProfile.answer2}</p>
                </div>
              )}
              
              {userProfile?.prompt3 && userProfile?.answer3 && (
                <div className="bg-gradient-to-r from-orange-50 to-amber-50 rounded-lg p-4 border border-orange-100">
                  <h4 className="font-medium text-orange-700 mb-2">{userProfile.prompt3}</h4>
                  <p className="text-gray-800">{userProfile.answer3}</p>
                </div>
              )}
              
              {(!userProfile?.prompt1 || !userProfile?.answer1) && 
               (!userProfile?.prompt2 || !userProfile?.answer2) && 
               (!userProfile?.prompt3 || !userProfile?.answer3) && (
                <p className="text-gray-500 italic bg-orange-50 rounded-lg p-3 border border-orange-100">No prompt responses added yet. Edit your profile to add more about yourself!</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile; 