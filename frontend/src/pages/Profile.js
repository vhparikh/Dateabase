import React, { useContext, useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import AuthContext from '../context/AuthContext';
import { getExperiences, getCurrentUser } from '../services/api';
import ProfileImageUpload from '../components/ProfileImageUpload';
import { API_URL } from '../config';

const Profile = () => {
  const { user, logoutUser, loadUserProfile } = useContext(AuthContext);
  const navigate = useNavigate();
  const [userExperiences, setUserExperiences] = useState([]);
  const [userProfile, setUserProfile] = useState(user); // Initialize with current context user
  const [loading, setLoading] = useState(true);
  const [profileLoading, setProfileLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Fetch user profile directly from the API to ensure latest data
  useEffect(() => {
    const fetchUserProfile = async () => {
      try {
        setProfileLoading(true);
        const response = await getCurrentUser();
        
        // Fetch user images
        try {
          const imagesResponse = await fetch(`${API_URL}/api/users/images`, {
            method: 'GET',
            credentials: 'include'
          });
          
          if (imagesResponse.ok) {
            const imagesData = await imagesResponse.json();
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
        
        setProfileLoading(false);
      } catch (err) {
        console.error('Failed to load user profile', err);
        setProfileLoading(false);
      }
    };
    
    fetchUserProfile();
  }, []);
  
  // Fetch user experiences
  useEffect(() => {
    const fetchUserExperiences = async () => {
      if (!userProfile || !userProfile.id) return;
      
      try {
        setLoading(true);
        const response = await getExperiences();
        // Filter experiences created by this user
        const filteredExperiences = response.data.filter(exp => exp.user_id === userProfile.id);
        setUserExperiences(filteredExperiences);
        setLoading(false);
      } catch (err) {
        setError('Failed to load your experiences');
        setLoading(false);
      }
    };
    
    fetchUserExperiences();
  }, [userProfile]);
  
  const handleLogout = async () => {
    try {
      const result = await logoutUser();
      if (result && result.logout_url) {
        // Redirect to CAS logout URL which will then redirect back to login page
        window.location.href = result.logout_url;
      } else {
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
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-orange-100 py-6">
      <div className="max-w-5xl mx-auto px-4 sm:px-6">
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
              
              <div className="mt-6 flex flex-wrap gap-3 justify-center md:justify-start">
                <button 
                  onClick={handleLogout} 
                  className="px-4 py-2 bg-white text-gray-700 rounded-lg border border-gray-300 shadow-sm hover:bg-gray-50 transition-colors flex items-center"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path>
                  </svg>
                  Logout
                </button>
                
                <Link 
                  to="/profile/edit" 
                  className="px-4 py-2 bg-white text-orange-600 border border-orange-300 rounded-lg font-medium shadow-sm hover:bg-orange-50 transition-colors flex items-center"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                  </svg>
                  Edit Profile
                </Link>
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