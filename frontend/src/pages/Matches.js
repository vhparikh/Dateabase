import React, { useState, useEffect, useContext } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { API_URL } from '../config';
import AuthContext from '../context/AuthContext';
import { GoogleMap, LoadScript, Marker } from '@react-google-maps/api';

// UserProfileModal component for displaying a user's full profile
const UserProfileModal = ({ userId, isOpen, onClose }) => {
  const [userProfile, setUserProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('photos');

  useEffect(() => {
    if (isOpen && userId) {
      fetchUserProfile();
    }
  }, [isOpen, userId]);

  const fetchUserProfile = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`${API_URL}/api/users/${userId}/profile`, {
        credentials: 'include'
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch user profile');
      }
      
      const data = await response.json();
      setUserProfile(data);
    } catch (err) {
      console.error('Error fetching user profile:', err);
      setError('Failed to load profile. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Format the interests from JSON string to an array of selected interests
  const renderInterests = () => {
    if (!userProfile?.interests) return null;
    
    let interestsObj = {};
    try {
      // Try to parse if it's a JSON string
      interestsObj = typeof userProfile.interests === 'string' ? 
        JSON.parse(userProfile.interests) : userProfile.interests;
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
    
    if (interestNames.length === 0) return null;
    
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

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 p-4 flex justify-between items-center z-10">
          <h2 className="text-xl font-bold text-gray-800">User Profile</h2>
          <button 
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        {loading ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-orange-500 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading profile...</p>
          </div>
        ) : error ? (
          <div className="p-8 text-center">
            <p className="text-red-500 mb-4">{error}</p>
            <button 
              onClick={fetchUserProfile} 
              className="px-4 py-2 bg-orange-500 text-white rounded-lg"
            >
              Try Again
            </button>
          </div>
        ) : userProfile ? (
          <div>
            {/* Profile Header */}
            <div className="relative">
              <div className="h-40 bg-gradient-to-r from-orange-start to-orange-end"></div>
              <div className="absolute -bottom-16 left-6">
                <div className="w-32 h-32 rounded-full border-4 border-white overflow-hidden">
                  <img 
                    src={userProfile.profile_image || `https://ui-avatars.com/api/?name=${userProfile.name}&background=orange&color=fff`} 
                    alt={userProfile.name} 
                    className="w-full h-full object-cover"
                  />
                </div>
              </div>
            </div>
            
            {/* Profile Basic Info */}
            <div className="pt-20 px-6 pb-6">
              <h3 className="text-2xl font-bold text-gray-800">{userProfile.name}</h3>
              <p className="text-gray-600">
                {userProfile.gender && `${userProfile.gender}`}
                {userProfile.class_year && ` • Class of ${userProfile.class_year}`}
                {userProfile.major && ` • ${userProfile.major}`}
              </p>
              
              {/* Tabs */}
              <div className="mt-6 border-b border-gray-200">
                <div className="flex">
                  <button 
                    onClick={() => setActiveTab('photos')} 
                    className={`pb-2 px-4 text-sm font-medium border-b-2 ${
                      activeTab === 'photos' 
                        ? 'border-orange-500 text-orange-600' 
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    Photos
                  </button>
                  <button 
                    onClick={() => setActiveTab('about')} 
                    className={`pb-2 px-4 text-sm font-medium border-b-2 ${
                      activeTab === 'about' 
                        ? 'border-orange-500 text-orange-600' 
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    About
                  </button>
                  <button 
                    onClick={() => setActiveTab('interests')} 
                    className={`pb-2 px-4 text-sm font-medium border-b-2 ${
                      activeTab === 'interests' 
                        ? 'border-orange-500 text-orange-600' 
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    Interests
                  </button>
                </div>
              </div>
              
              {/* Tab Content */}
              <div className="mt-6">
                {activeTab === 'photos' && (
                  <div>
                    <h4 className="text-lg font-medium text-gray-800 mb-4">Photos</h4>
                    
                    {userProfile.images && userProfile.images.length > 0 ? (
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                        {userProfile.images.map(image => (
                          <div key={image.id} className="aspect-square rounded-lg overflow-hidden">
                            <img 
                              src={image.url} 
                              alt={`${userProfile.name}'s photo`} 
                              className="w-full h-full object-cover"
                            />
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-gray-500">No photos available</p>
                    )}
                  </div>
                )}
                
                {activeTab === 'about' && (
                  <div>
                    <h4 className="text-lg font-medium text-gray-800 mb-4">About</h4>
                    
                    <div className="space-y-6">
                      {userProfile.prompt1 && userProfile.answer1 && (
                        <div className="bg-orange-50 rounded-lg p-4">
                          <p className="font-medium text-orange-800 mb-2">{userProfile.prompt1}</p>
                          <p className="text-gray-700">{userProfile.answer1}</p>
                        </div>
                      )}
                      
                      {userProfile.prompt2 && userProfile.answer2 && (
                        <div className="bg-orange-50 rounded-lg p-4">
                          <p className="font-medium text-orange-800 mb-2">{userProfile.prompt2}</p>
                          <p className="text-gray-700">{userProfile.answer2}</p>
                        </div>
                      )}
                      
                      {userProfile.prompt3 && userProfile.answer3 && (
                        <div className="bg-orange-50 rounded-lg p-4">
                          <p className="font-medium text-orange-800 mb-2">{userProfile.prompt3}</p>
                          <p className="text-gray-700">{userProfile.answer3}</p>
                        </div>
                      )}
                      
                      {!userProfile.prompt1 && !userProfile.prompt2 && !userProfile.prompt3 && (
                        <p className="text-gray-500">No prompts answered yet</p>
                      )}
                    </div>
                    
                    <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                      {userProfile.hometown && (
                        <div className="border border-gray-200 rounded-lg p-4">
                          <p className="text-sm text-gray-500 mb-1">Hometown</p>
                          <p className="font-medium">{userProfile.hometown}</p>
                        </div>
                      )}
                      
                      {userProfile.location && (
                        <div className="border border-gray-200 rounded-lg p-4">
                          <p className="text-sm text-gray-500 mb-1">Current Location</p>
                          <p className="font-medium">{userProfile.location}</p>
                        </div>
                      )}
                      
                      {userProfile.height && (
                        <div className="border border-gray-200 rounded-lg p-4">
                          <p className="text-sm text-gray-500 mb-1">Height</p>
                          <p className="font-medium">
                            {userProfile.height} cm 
                            ({Math.floor(userProfile.height / 30.48)} ft {Math.round(userProfile.height % 30.48 / 2.54)} in)
                          </p>
                        </div>
                      )}
                      
                      {userProfile.sexuality && (
                        <div className="border border-gray-200 rounded-lg p-4">
                          <p className="text-sm text-gray-500 mb-1">Sexuality</p>
                          <p className="font-medium">{userProfile.sexuality}</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
                
                {activeTab === 'interests' && (
                  <div>
                    <h4 className="text-lg font-medium text-gray-800 mb-4">Interests</h4>
                    
                    {renderInterests() || (
                      <p className="text-gray-500">No interests specified</p>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="p-8 text-center">
            <p className="text-gray-500">User not found</p>
          </div>
        )}
      </div>
    </div>
  );
};

// Updated Match Card with orange gradient theme - Grouped by user
const GroupedMatchCard = ({ user, experiences }) => {
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [activeExperience, setActiveExperience] = useState(experiences[0]);
  const [showMap, setShowMap] = useState(false);

  // Google Maps configuration
  const mapContainerStyle = {
    width: '100%',
    height: '200px',
    borderRadius: '8px',
  };
  
  const mapCenter = {
    lat: activeExperience.experience.latitude || 40.3431, // Default to Princeton's latitude
    lng: activeExperience.experience.longitude || -74.6551, // Default to Princeton's longitude
  };
  
  const mapOptions = {
    disableDefaultUI: true,
    zoomControl: true,
  };

  const openGoogleMaps = () => {
    if (activeExperience.experience.latitude && activeExperience.experience.longitude) {
      window.open(`https://www.google.com/maps/search/?api=1&query=${activeExperience.experience.latitude},${activeExperience.experience.longitude}`, '_blank');
    } else {
      window.open(`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(activeExperience.experience.location)}`, '_blank');
    }
  };

  return (
    <div className="bg-white rounded-xl overflow-hidden shadow-card mb-4">
      {/* User Profile Header */}
      <div className="relative">
        <div className="h-40 bg-gradient-to-r from-orange-start to-orange-end"></div>
        <div className="absolute -bottom-16 left-6">
          <div className="w-32 h-32 rounded-full border-4 border-white overflow-hidden">
            <img 
              src={user.profile_image || `https://ui-avatars.com/api/?name=${user.name}&background=orange&color=fff`} 
              alt={user.name} 
              className="w-full h-full object-cover"
            />
          </div>
        </div>
      </div>
      
      {/* User Profile Info */}
      <div className="pt-20 px-6 pb-4">
        <div className="flex justify-between items-start">
          <div>
            <h3 className="text-2xl font-bold text-gray-800">{user.name}</h3>
            <p className="text-gray-600">
              {user.gender && `${user.gender}`}
              {user.class_year && ` • Class of ${user.class_year}`}
            </p>
          </div>
          <span className="px-3 py-1 bg-orange-100 text-orange-700 text-sm rounded-full">
            {experiences.length} {experiences.length === 1 ? 'match' : 'matches'}
          </span>
        </div>
        
        <div className="flex mt-4">
          <button 
            onClick={() => setShowProfileModal(true)} 
            className="px-4 py-2 bg-gradient-to-r from-orange-start to-orange-end text-white rounded-lg text-sm font-medium shadow-sm hover:shadow-md transition-all"
          >
            View Profile
          </button>
        </div>
      </div>
      
      {/* Experiences List */}
      <div className="px-6 pb-6">
        <h4 className="text-lg font-semibold text-gray-800 mb-3">Matched Experiences</h4>
        
        {/* Experience Selector */}
        <div className="flex flex-wrap gap-2 mb-4">
          {experiences.map((exp, index) => (
            <button
              key={exp.experience.id}
              onClick={() => setActiveExperience(exp)}
              className={`px-3 py-1 rounded-full text-sm ${
                activeExperience.experience.id === exp.experience.id
                  ? 'bg-gradient-to-r from-orange-start to-orange-end text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {exp.experience.experience_type}
            </button>
          ))}
        </div>
        
        {/* Selected Experience Details */}
        <div className="bg-orange-50 rounded-lg p-4 mb-4">
          <div className="flex justify-between items-start mb-3">
            <div>
              <h5 className="font-medium text-gray-800">{activeExperience.experience.location}</h5>
              <p className="text-sm text-gray-600">{activeExperience.experience.experience_type}</p>
            </div>
            <button
              onClick={() => setShowMap(!showMap)}
              className="p-2 bg-white rounded-full text-orange-600 hover:bg-orange-100 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
              </svg>
            </button>
          </div>
          
          <p className="text-gray-700 text-sm mb-4">
            {activeExperience.experience.description || "No description provided."}
          </p>
          
          {/* Conditionally show Google Map */}
          {showMap && (
            <div className="mb-4">
              <LoadScript googleMapsApiKey="YOUR_GOOGLE_MAPS_API_KEY">
                <GoogleMap
                  mapContainerStyle={mapContainerStyle}
                  center={mapCenter}
                  zoom={15}
                  options={mapOptions}
                >
                  <Marker position={mapCenter} />
                </GoogleMap>
              </LoadScript>
              
              <div className="mt-2 flex justify-end">
                <button
                  onClick={openGoogleMaps}
                  className="text-sm text-blue-600 flex items-center"
                >
                  <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                  Open in Google Maps
                </button>
              </div>
            </div>
          )}
          
          <div className="flex justify-between">
            <button
              onClick={() => window.location.href = `mailto:${user.netid}@princeton.edu`}
              className="px-3 py-1.5 border border-orange-300 text-orange-700 rounded-md text-sm hover:bg-orange-100 transition-colors"
            >
              Email
            </button>
            
            <button
              onClick={openGoogleMaps}
              className="px-3 py-1.5 bg-gradient-to-r from-orange-start to-orange-end text-white rounded-md text-sm"
            >
              Get Directions
            </button>
          </div>
        </div>
      </div>
      
      {/* User Profile Modal */}
      {showProfileModal && (
        <UserProfileModal 
          userId={user.id}
          isOpen={showProfileModal}
          onClose={() => setShowProfileModal(false)}
        />
      )}
    </div>
  );
};

// Updated Potential Match Card - Grouped by user with individual experience selection
const GroupedPotentialMatchCard = ({ user, experiences, onAccept, onReject }) => {
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [expandedExperience, setExpandedExperience] = useState(null);
  const [locationImages, setLocationImages] = useState({});
  
  // Load location images on component mount
  useEffect(() => {
    const images = {};
    experiences.forEach(exp => {
      if (exp.experience.location_image) {
        images[exp.experience.id] = exp.experience.location_image;
      } else if (exp.experience.location) {
        // Fallback to Unsplash if no location image is provided
        images[exp.experience.id] = `https://source.unsplash.com/random/800x600/?${exp.experience.location.replace(/\s+/g, '+')}`;
      }
    });
    setLocationImages(images);
    
    // Set the first experience as expanded by default
    if (experiences.length > 0 && !expandedExperience) {
      setExpandedExperience(experiences[0].experience.id);
    }
  }, [experiences]);
  
  return (
    <div className="bg-white rounded-xl overflow-hidden shadow-card mb-4">
      {/* Header */}
      <div className="relative">
        <div className="h-32 bg-orange-50">
          <img 
            src={locationImages[expandedExperience] || `https://source.unsplash.com/random/800x600/?experience`} 
            alt="Experience"
            className="w-full h-full object-cover"
          />
        </div>
        
        <div className="absolute -bottom-12 left-4">
          <div className="w-24 h-24 rounded-full border-4 border-white overflow-hidden bg-gradient-to-r from-orange-start to-orange-end">
            <img 
              src={user.profile_image || `https://ui-avatars.com/api/?name=${user.name}&background=orange&color=fff`} 
              alt={user.name} 
              className="w-full h-full object-cover"
            />
          </div>
        </div>
      </div>
      
      {/* Content */}
      <div className="pt-14 px-4 pb-4">
        <div className="flex justify-between items-start">
          <div>
            <h3 className="text-lg font-bold text-gray-800">{user.name}</h3>
            <p className="text-sm text-gray-500 mb-2">Class of {user.class_year || 'N/A'}</p>
          </div>
          <span className="px-2 py-0.5 bg-orange-100 text-orange-700 text-xs rounded-full">
            {experiences.length} {experiences.length === 1 ? 'request' : 'requests'}
          </span>
        </div>
        
        <div className="flex mt-2 mb-4">
          <button 
            onClick={() => setShowProfileModal(true)} 
            className="px-3 py-1.5 bg-orange-100 text-orange-700 rounded-md text-sm hover:bg-orange-200 transition-colors"
          >
            View Profile
          </button>
        </div>
        
        <h4 className="text-sm font-medium text-gray-700 mb-2">Potential Experiences</h4>
        
        {/* Experience Cards - Each with individual accept/reject buttons */}
        <div className="space-y-3">
          {experiences.map((exp) => (
            <div 
              key={exp.match_id} 
              className="border border-gray-200 rounded-lg overflow-hidden"
            >
              <div className="flex border-b border-gray-100">
                <div 
                  className="w-20 h-20 flex-shrink-0 bg-orange-50"
                  style={{
                    backgroundImage: `url(${locationImages[exp.experience.id] || ''})`,
                    backgroundSize: 'cover',
                    backgroundPosition: 'center'
                  }}
                ></div>
                
                <div className="p-3 flex-1">
                  <div className="flex items-center justify-between">
                    <h5 className="font-medium text-gray-800 text-sm">{exp.experience.experience_type}</h5>
                    {/* Expand/collapse button */}
                    <button 
                      onClick={() => setExpandedExperience(
                        expandedExperience === exp.experience.id ? null : exp.experience.id
                      )}
                      className="text-gray-500 hover:text-gray-700"
                    >
                      {expandedExperience === exp.experience.id ? (
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 15l7-7 7 7" />
                        </svg>
                      ) : (
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                        </svg>
                      )}
                    </button>
                  </div>
                  
                  <div className="flex items-center text-sm text-gray-600 mt-1">
                    <svg className="w-3.5 h-3.5 text-gray-500 mr-1 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    <span className="truncate">{exp.experience.location}</span>
                  </div>
                </div>
              </div>
              
              {/* Expanded content */}
              {expandedExperience === exp.experience.id && (
                <div className="p-3 bg-gray-50 border-t border-gray-100">
                  <p className="text-sm text-gray-700 mb-3">
                    {exp.experience.description || "No description provided."}
                  </p>
                  
                  <div className="flex space-x-2">
                    <button 
                      onClick={() => onReject(exp.match_id)}
                      className="flex-1 py-1.5 px-3 border border-gray-300 rounded-lg text-gray-700 text-sm font-medium hover:bg-gray-50 transition-colors"
                    >
                      Decline
                    </button>
                    <button 
                      onClick={() => onAccept(exp.match_id)}
                      className="flex-1 py-1.5 px-3 bg-gradient-to-r from-orange-start to-orange-end text-white rounded-lg text-sm font-medium hover:shadow-md transition-all"
                    >
                      Accept
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
      
      {/* User Profile Modal */}
      {showProfileModal && (
        <UserProfileModal 
          userId={user.id}
          isOpen={showProfileModal}
          onClose={() => setShowProfileModal(false)}
        />
      )}
    </div>
  );
};

// Empty state component
const EmptyState = () => (
  <div className="bg-white rounded-xl shadow-card border border-orange-100 p-8 text-center max-w-md mx-auto">
    <div className="inline-flex items-center justify-center w-16 h-16 bg-orange-100 rounded-full mb-4">
      <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-orange-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
      </svg>
    </div>
    <h3 className="text-xl font-bold text-gray-800 mb-2">No matches yet</h3>
    <p className="text-gray-600 mb-6">Start swiping to find people who share your interests!</p>
    <Link 
      to="/swipe" 
      className="px-6 py-3 bg-gradient-to-r from-orange-start to-orange-end text-white font-medium rounded-lg shadow-md hover:shadow-lg transition-all inline-block"
    >
      Start Swiping
    </Link>
  </div>
);

// Pending Match Card (matches you've sent that are waiting for response)
const PendingSentMatchCard = ({ match }) => {
  const [locationImage, setLocationImage] = useState(null);
  
  // Load location image on component mount
  useEffect(() => {
    if (match.experience.location_image) {
      setLocationImage(match.experience.location_image);
    } else if (match.experience.location) {
      setLocationImage(`https://source.unsplash.com/random/800x600/?${match.experience.location.replace(/\s+/g, '+')}`);
    }
  }, [match.experience.location, match.experience.location_image]);
  
  return (
    <div className="bg-white rounded-xl overflow-hidden shadow-card mb-4">
      <div className="border-l-4 border-amber-400 px-4 py-3">
        <div className="flex items-center">
          <div className="h-8 w-8 rounded-full bg-amber-100 flex items-center justify-center mr-2">
            <svg className="w-4 h-4 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <span className="text-sm font-medium text-gray-700">Waiting for response</span>
        </div>
      </div>
      
      <div className="p-4 flex items-center">
        <div className="w-12 h-12 rounded-full overflow-hidden mr-3">
          <img 
            src={match.other_user.profile_image || `https://ui-avatars.com/api/?name=${match.other_user.name}&background=orange&color=fff`}
            alt={match.other_user.name}
            className="w-full h-full object-cover"
          />
        </div>
        
        <div>
          <h3 className="font-medium text-gray-800">{match.other_user.name}</h3>
          <p className="text-sm text-gray-500">Class of {match.other_user.class_year || 'N/A'}</p>
        </div>
      </div>
      
      <div className="px-4 pb-4">
        <div className="flex items-center mb-2">
          <svg className="w-4 h-4 text-gray-600 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <span className="text-sm text-gray-700">{match.experience.location}</span>
        </div>
        
        <div className="text-xs text-gray-500">
          Sent on {new Date(match.created_at).toLocaleDateString()}
        </div>
      </div>
    </div>
  );
};

const Matches = () => {
  const [confirmedMatches, setConfirmedMatches] = useState([]);
  const [pendingReceivedMatches, setPendingReceivedMatches] = useState([]);
  const [pendingSentMatches, setPendingSentMatches] = useState([]);
  const [groupedConfirmedMatches, setGroupedConfirmedMatches] = useState({});
  const [groupedPendingReceivedMatches, setGroupedPendingReceivedMatches] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('confirmed');
  
  const { user } = useContext(AuthContext);
  
  // Helper function to group matches by user
  const groupMatchesByUser = (matches) => {
    const grouped = {};
    
    matches.forEach(match => {
      const userId = match.other_user.id;
      
      if (!grouped[userId]) {
        grouped[userId] = {
          user: match.other_user,
          experiences: []
        };
      }
      
      grouped[userId].experiences.push(match);
    });
    
    return grouped;
  };
  
  const fetchMatches = async () => {
    try {
      setLoading(true);
      setError(null);
      
      if (!user || !user.id) {
        throw new Error('User not authenticated');
      }
      
      const response = await fetch(`${API_URL}/api/matches/${user.id}`, {
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include'
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch matches: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Matches data:', data);
      
      // Set the matches by category
      setConfirmedMatches(data.confirmed || []);
      setPendingReceivedMatches(data.pending_received || []);
      setPendingSentMatches(data.pending_sent || []);
      
      // Group matches by user
      setGroupedConfirmedMatches(groupMatchesByUser(data.confirmed || []));
      setGroupedPendingReceivedMatches(groupMatchesByUser(data.pending_received || []));
      
    } catch (err) {
      console.error('Error fetching matches:', err);
      setError('Failed to load matches. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  const handleAcceptMatch = async (matchId) => {
    try {
      setError(null);
      
      const response = await fetch(`${API_URL}/api/matches/${matchId}/accept`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include'
      });
      
      if (!response.ok) {
        throw new Error(`Failed to accept match: ${response.status}`);
      }
      
      // Refresh matches
      fetchMatches();
      
    } catch (err) {
      console.error('Error accepting match:', err);
      setError('Failed to accept match. Please try again.');
    }
  };
  
  const handleRejectMatch = async (matchId) => {
    try {
      setError(null);
      
      const response = await fetch(`${API_URL}/api/matches/${matchId}/reject`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include'
      });
      
      if (!response.ok) {
        throw new Error(`Failed to reject match: ${response.status}`);
      }
      
      // Refresh matches
      fetchMatches();
      
    } catch (err) {
      console.error('Error rejecting match:', err);
      setError('Failed to reject match. Please try again.');
    }
  };
  
  useEffect(() => {
    if (user) {
      fetchMatches();
    }
  }, [user]);
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-orange-100 py-6">
      <div className="max-w-3xl mx-auto px-4 sm:px-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-800">Your Matches</h1>
          <button 
            className="p-2 text-orange-600 hover:bg-orange-100 rounded-full transition-colors"
            onClick={fetchMatches}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>
        
        {/* Tabs */}
        <div className="bg-white rounded-xl mb-6 border border-orange-100 p-1 shadow-sm">
          <div className="flex">
            <button 
              onClick={() => setActiveTab('confirmed')} 
              className={`flex-1 py-3 px-4 rounded-lg text-center transition-colors ${
                activeTab === 'confirmed' 
                  ? 'bg-gradient-to-r from-orange-start to-orange-end text-white font-medium' 
                  : 'text-gray-700 hover:bg-orange-50'
              }`}
            >
              Confirmed Matches
            </button>
            <button 
              onClick={() => setActiveTab('potential')} 
              className={`flex-1 py-3 px-4 rounded-lg text-center transition-colors ${
                activeTab === 'potential' 
                  ? 'bg-gradient-to-r from-orange-start to-orange-end text-white font-medium' 
                  : 'text-gray-700 hover:bg-orange-50'
              }`}
            >
              Potential Matches
              {pendingReceivedMatches.length > 0 && (
                <span className="ml-2 px-2 py-0.5 bg-orange-100 text-orange-700 text-xs rounded-full">
                  {pendingReceivedMatches.length}
                </span>
              )}
            </button>
          </div>
        </div>
        
        {/* Matches content */}
        {loading ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-orange-500 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading your matches...</p>
          </div>
        ) : error ? (
          <div className="bg-red-50 border-l-4 border-red-500 text-red-700 p-4 rounded">
            <p>{error}</p>
            <button 
              className="mt-2 px-4 py-2 bg-white border border-red-300 rounded-lg hover:bg-red-50 transition-colors"
              onClick={fetchMatches}
            >
              Try Again
            </button>
          </div>
        ) : activeTab === 'confirmed' ? (
          Object.keys(groupedConfirmedMatches).length === 0 ? (
            <EmptyState />
          ) : (
            <div className="grid gap-4">
              {Object.values(groupedConfirmedMatches).map(groupedMatch => (
                <GroupedMatchCard 
                  key={groupedMatch.user.id} 
                  user={groupedMatch.user} 
                  experiences={groupedMatch.experiences} 
                />
              ))}
            </div>
          )
        ) : (
          <div>
            {Object.keys(groupedPendingReceivedMatches).length === 0 && pendingSentMatches.length === 0 ? (
              <div className="text-center py-10 bg-white rounded-xl shadow-sm">
                <div className="mx-auto w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mb-4">
                  <svg className="w-8 h-8 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </div>
                <h3 className="text-xl font-bold text-gray-800 mb-2">No potential matches yet</h3>
                <p className="text-gray-600 mb-6">When someone shows interest in your experiences, you'll see them here</p>
                <Link to="/experiences" className="px-4 py-2 bg-gradient-to-r from-orange-start to-orange-end text-white rounded-lg font-medium shadow-md hover:shadow-lg transition-all">
                  Browse Experiences
                </Link>
              </div>
            ) : (
              <div>
                {Object.keys(groupedPendingReceivedMatches).length > 0 && (
                  <div className="mb-6">
                    <h2 className="text-lg font-bold text-gray-800 mb-3">People interested in your experiences</h2>
                    <div className="grid gap-4">
                      {Object.values(groupedPendingReceivedMatches).map(groupedMatch => (
                        <GroupedPotentialMatchCard 
                          key={groupedMatch.user.id}
                          user={groupedMatch.user}
                          experiences={groupedMatch.experiences}
                          onAccept={handleAcceptMatch}
                          onReject={handleRejectMatch}
                        />
                      ))}
                    </div>
                  </div>
                )}
                
                {pendingSentMatches.length > 0 && (
                  <div>
                    <h2 className="text-lg font-bold text-gray-800 mb-3">Experiences you're interested in</h2>
                    <div className="grid gap-4">
                      {pendingSentMatches.map(match => (
                        <PendingSentMatchCard key={match.match_id} match={match} />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Matches;