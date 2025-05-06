import React, { useState, useEffect, useContext } from 'react';
import { Link } from 'react-router-dom';
import { useCSRFToken } from '../App'
import axios from 'axios';
import { API_URL } from '../config';
import AuthContext from '../context/AuthContext';
import { GoogleMap, LoadScript, Marker } from '@react-google-maps/api';

// Define libraries array outside component to prevent recreation on each render
const libraries = ["places"];

// UserProfileModal component for displaying a user's full profile
const UserProfileModal = ({ userId, isOpen, onClose, backgroundImage }) => {
  const [userProfile, setUserProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('photos');

  const csrfToken = useCSRFToken();

  useEffect(() => {
    if (isOpen && userId) {
      fetchUserProfile();
    }
  }, [isOpen, userId, fetchUserProfile, csrfToken]);

  const fetchUserProfile = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.get(`${API_URL}/api/users/${userId}/profile`, { withCredentials: true, headers: { 'X-CsrfToken': csrfToken } });
      
      if (response.status !== 200) {
        throw new Error('Failed to fetch user profile');
      }
      
      const data = response.data;
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
              {backgroundImage ? (
                <div className="h-40 overflow-hidden">
                  <img
                    src={backgroundImage}
                    alt="Experience background"
                    className="w-full h-full object-cover"
                  />
                </div>
              ) : (
                <div className="h-40 bg-gradient-to-r from-orange-start to-orange-end"></div>
              )}
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

// ContactInfoModal component for displaying a user's contact information
const ContactInfoModal = ({ user, isOpen, onClose }) => {
  const [contactInfo, setContactInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const csrfToken = useCSRFToken();
  
  useEffect(() => {
    if (isOpen && user) {
      fetchContactInfo();
    }
  }, [isOpen, user, fetchContactInfo, csrfToken]);

  const fetchContactInfo = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.get(`${API_URL}/api/users/${user.id}/contact`, { withCredentials: true, headers: { 'X-CsrfToken': csrfToken }});
      const data = await response.data;
      setContactInfo(data);
    } catch (err) {
      console.error('Error fetching contact info:', err);
      setError('Failed to load contact information. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-md w-full">
        <div className="border-b border-gray-200 p-4 flex justify-between items-center">
          <h2 className="text-xl font-bold text-gray-800">Contact Information</h2>
          <button 
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div className="p-6">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-t-4 border-b-4 border-orange-500"></div>
            </div>
          ) : error ? (
            <div className="bg-red-50 border-l-4 border-red-500 text-red-700 p-4 mb-6 rounded-md" role="alert">
              <p>{error}</p>
              <button 
                onClick={fetchContactInfo} 
                className="mt-2 px-4 py-2 bg-orange-500 text-white rounded-lg"
              >
                Try Again
              </button>
            </div>
          ) : contactInfo ? (
            <>
              <div className="flex items-center mb-6">
                <div className="w-12 h-12 rounded-full overflow-hidden mr-4">
                  <img 
                    src={contactInfo.profile_image || `https://ui-avatars.com/api/?name=${contactInfo.name}&background=orange&color=fff`} 
                    alt={contactInfo.name} 
                    className="w-full h-full object-cover"
                  />
                </div>
                <div>
                  <h3 className="font-bold text-lg text-gray-800">{contactInfo.name}</h3>
                  <p className="text-gray-600">Class of {contactInfo.class_year || 'N/A'}</p>
                </div>
              </div>
              
              <div className="space-y-4">
                {/* Email */}
                <div className="bg-orange-50 rounded-lg p-4">
                  <div className="flex items-center mb-2">
                    <svg className="w-5 h-5 text-orange-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                    <h4 className="font-medium text-gray-800">Email</h4>
                  </div>
                  
                  {(() => {
                    if (contactInfo.preferred_email && contactInfo.preferred_email.trim() !== '') {
                      return (
                        <p className="text-gray-700 font-medium">
                          {contactInfo.preferred_email.trim()}
                        </p>
                      );
                    } else if (contactInfo.netid && contactInfo.netid.trim() !== '') {
                      const princetonEmail = `${contactInfo.netid.trim()}@princeton.edu`;
                      return (
                        <p className="text-gray-700 font-medium">
                          {princetonEmail}
                          <span className="block text-xs text-gray-500 mt-1">
                            Princeton email address
                          </span>
                        </p>
                      );
                    } else {
                      return (
                        <p className="text-gray-700">
                          Not available
                        </p>
                      );
                    }
                  })()}
                  
                  {(() => {
                    let emailAddress = null;
                    
                    if (contactInfo.preferred_email && contactInfo.preferred_email.trim() !== '') {
                      emailAddress = contactInfo.preferred_email.trim();
                    } else if (contactInfo.netid && contactInfo.netid.trim() !== '') {
                      emailAddress = `${contactInfo.netid.trim()}@princeton.edu`;
                    }
                    
                    if (emailAddress) {
                      return (
                        <a 
                          href={`mailto:${emailAddress}`}
                          className="mt-2 text-sm text-orange-600 hover:text-orange-800 inline-flex items-center"
                        >
                          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                          </svg>
                          Open in mail app
                        </a>
                      );
                    }
                    return null;
                  })()}
                </div>
                
                {/* Phone Number */}
                <div className="bg-orange-50 rounded-lg p-4">
                  <div className="flex items-center mb-2">
                    <svg className="w-5 h-5 text-orange-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                    </svg>
                    <h4 className="font-medium text-gray-800">Phone Number</h4>
                  </div>
                  <p className="text-gray-700 font-medium">
                    {contactInfo.phone_number ? contactInfo.phone_number : 'Not given'}
                  </p>
                  {contactInfo.phone_number && (
                    <a 
                      href={`tel:${contactInfo.phone_number.replace(/\D/g, '')}`}
                      className="mt-2 text-sm text-orange-600 hover:text-orange-800 inline-flex items-center"
                    >
                      <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                      </svg>
                      Call
                    </a>
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center py-8">
              <p className="text-gray-500">No contact information available</p>
            </div>
          )}
        </div>
      </div>
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

// Updated Match Card with orange gradient theme - Grouped by user
const GroupedMatchCard = ({ user, experiences }) => {
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [showContactModal, setShowContactModal] = useState(false);
  const [activeExperience, setActiveExperience] = useState(experiences[0]);
  const [showMap, setShowMap] = useState(false);
  const [locationImages, setLocationImages] = useState({});

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

  // Load location images on component mount
  useEffect(() => {
    const loadImages = async () => {
      const images = {...locationImages};
      
      for (const exp of experiences) {
        try {
          // Fetch fresh image URL from the API for each experience
          const response = await axios.get(`${API_URL}/api/experiences/get-image/${exp.experience.id}`, { 
            withCredentials: true 
          });
          
          if (response.data && response.data.image_url) {
            images[exp.experience.id] = response.data.image_url;
          } else if (exp.experience.location_image) {
            // Fallback to stored image if API call doesn't return a valid URL
            images[exp.experience.id] = exp.experience.location_image;
          } else if (exp.experience.location) {
            const locationForImage = exp.experience.location.split(',')[0].trim();
            images[exp.experience.id] = `https://source.unsplash.com/random/800x600/?${locationForImage.replace(/\s+/g, '+')}`;
          }
        } catch (error) {
          console.error('Error fetching image URL:', error);
          if (exp.experience.location_image) {
            images[exp.experience.id] = exp.experience.location_image;
          } else if (exp.experience.location) {
            const locationForImage = exp.experience.location.split(',')[0].trim();
            images[exp.experience.id] = `https://source.unsplash.com/random/800x600/?${locationForImage.replace(/\s+/g, '+')}`;
          }
        }
      }
      
      setLocationImages(images);
      
      // Set the active experience
      if (experiences.length > 0 && !activeExperience) {
        setActiveExperience(experiences[0]);
      }
    };
    
    loadImages();
  }, [experiences]);

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
        {locationImages[activeExperience.experience.id] ? (
          <div className="h-40 overflow-hidden">
            <img
              src={locationImages[activeExperience.experience.id]}
              alt={activeExperience.experience.location}
              className="w-full h-full object-cover"
            />
          </div>
        ) : (
          <div className="h-40 bg-gradient-to-r from-orange-start to-orange-end"></div>
        )}
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
              {exp.experience.location}
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
              {activeExperience.experience.latitude && activeExperience.experience.longitude ? (
                <LoadScript googleMapsApiKey={process.env.REACT_APP_GOOGLE_MAPS_API_KEY || ""} libraries={libraries}>
                  <GoogleMap
                    mapContainerStyle={mapContainerStyle}
                    center={mapCenter}
                    zoom={15}
                    options={mapOptions}
                  >
                    <Marker position={mapCenter} />
                  </GoogleMap>
                </LoadScript>
              ) : (
                <iframe title = "map_keys"
                  width="100%"
                  height="200px"
                  className="rounded-lg"
                  loading="lazy"
                  src={`https://www.google.com/maps/embed/v1/place?key=${process.env.REACT_APP_GOOGLE_MAPS_API_KEY}&q=${encodeURIComponent(activeExperience.experience.location)}`}
                ></iframe>
              )}
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
              onClick={() => setShowContactModal(true)}
              className="px-3 py-1.5 border border-orange-300 text-orange-700 rounded-md text-sm hover:bg-orange-100 transition-colors"
            >
              Contact Info
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
          backgroundImage={locationImages[activeExperience.experience.id]}
        />
      )}
      
      {/* Contact Info Modal */}
      {showContactModal && (
        <ContactInfoModal 
          user={user}
          isOpen={showContactModal}
          onClose={() => setShowContactModal(false)}
        />
      )}
    </div>
  );
};

// Updated Potential Match Card - Remove contact info button for potential matches
const GroupedPotentialMatchCard = ({ user, experiences, onAccept, onReject }) => {
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [expandedExperience, setExpandedExperience] = useState(null);
  const [locationImages, setLocationImages] = useState({});
  const csrfToken = useCSRFToken();
  
  // Load location images on component mount
  useEffect(() => {
    const loadImages = async () => {
      const images = {...locationImages};
      
      for (const exp of experiences) {
        try {
          // Fetch fresh image URL from the API for each experience
          const response = await axios.get(`${API_URL}/api/experiences/get-image/${exp.experience.id}`, { 
            withCredentials: true 
          });
          
          if (response.data && response.data.image_url) {
            images[exp.experience.id] = response.data.image_url;
          } else if (exp.experience.location_image) {
            // Fallback to stored image if API call doesn't return a valid URL
            images[exp.experience.id] = exp.experience.location_image;
          } else if (exp.experience.location) {
            // Last resort fallback to Unsplash
            const locationForImage = exp.experience.location.split(',')[0].trim();
            images[exp.experience.id] = `https://source.unsplash.com/random/800x600/?${locationForImage.replace(/\s+/g, '+')}`;
          }
        } catch (error) {
          console.error('Error fetching image URL:', error);
          // Fallback to the stored URL if there's an error
          if (exp.experience.location_image) {
            images[exp.experience.id] = exp.experience.location_image;
          } else if (exp.experience.location) {
            const locationForImage = exp.experience.location.split(',')[0].trim();
            images[exp.experience.id] = `https://source.unsplash.com/random/800x600/?${locationForImage.replace(/\s+/g, '+')}`;
          }
        }
      }
      
      setLocationImages(images);
      
      // Set the active experience if not already set
      if (experiences.length > 0 && !expandedExperience) {
        setExpandedExperience(experiences[0].experience.id);
      }
    };
    
    loadImages();
  }, [experiences]);
  
  return (
    <div className="bg-white rounded-xl overflow-hidden shadow-card mb-4">
      {/* Header */}
      <div className="relative">
        <div className="h-32 bg-orange-50">
          {locationImages[expandedExperience] ? (
            <img 
              src={locationImages[expandedExperience]} 
              alt="Experience"
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full bg-gradient-to-r from-orange-500 to-orange-600"></div>
          )}
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
                    backgroundImage: locationImages[exp.experience.id] ? 
                      `url(${locationImages[exp.experience.id]})` : 
                      'linear-gradient(to right, #f97316, #fb923c)',
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

// Pending Sent Match Card
const GroupedPendingSentMatchCard = ({ user, experiences }) => {
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [expandedExperience, setExpandedExperience] = useState(null);
  const [locationImages, setLocationImages] = useState({});

  const csrfToken = useCSRFToken();
  
  // Load location images on component mount
  useEffect(() => {
    const loadImages = async () => {
      const images = {...locationImages};
      
      for (const exp of experiences) {
        try {
          // Fetch fresh image URL from the API for each experience
          const response = await axios.get(`${API_URL}/api/experiences/get-image/${exp.experience.id}`, { 
            withCredentials: true 
          });
          
          if (response.data && response.data.image_url) {
            images[exp.experience.id] = response.data.image_url;
          } else if (exp.experience.location_image) {
            // Fallback to stored image if API call doesn't return a valid URL
            images[exp.experience.id] = exp.experience.location_image;
          } else if (exp.experience.location) {
            // Last resort fallback to Unsplash
            const locationForImage = exp.experience.location.split(',')[0].trim();
            images[exp.experience.id] = `https://source.unsplash.com/random/800x600/?${locationForImage.replace(/\s+/g, '+')}`;
          }
        } catch (error) {
          console.error('Error fetching image URL:', error);
          // Fallback to the stored URL if there's an error
          if (exp.experience.location_image) {
            images[exp.experience.id] = exp.experience.location_image;
          } else if (exp.experience.location) {
            const locationForImage = exp.experience.location.split(',')[0].trim();
            images[exp.experience.id] = `https://source.unsplash.com/random/800x600/?${locationForImage.replace(/\s+/g, '+')}`;
          }
        }
      }
      
      setLocationImages(images);
      
      // Set the active experience if not already set
      if (experiences.length > 0 && !expandedExperience) {
        setExpandedExperience(experiences[0].experience.id);
      }
    };
    
    loadImages();
  }, [experiences]);
  
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
      
      <div className="p-4 flex items-center justify-between">
        <div className="flex items-center">
          <div className="w-12 h-12 rounded-full overflow-hidden mr-3">
            <img 
              src={user.profile_image || `https://ui-avatars.com/api/?name=${user.name}&background=orange&color=fff`}
              alt={user.name}
              className="w-full h-full object-cover"
            />
          </div>
          
          <div>
            <h3 className="font-medium text-gray-800">{user.name}</h3>
            <p className="text-sm text-gray-500">Class of {user.class_year || 'N/A'}</p>
          </div>
        </div>
        
        <span className="px-2 py-0.5 bg-amber-100 text-amber-700 text-xs rounded-full">
          {experiences.length} {experiences.length === 1 ? 'request' : 'requests'}
        </span>
      </div>
      
      <div className="px-4 pb-4">
        <div className="flex mb-3">
          <button 
            onClick={() => setShowProfileModal(true)} 
            className="text-sm text-orange-600 hover:text-orange-800 transition-colors inline-flex items-center"
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
            View Profile
          </button>
        </div>
        
        <h4 className="text-sm font-medium text-gray-700 mb-2">Pending Experiences</h4>
        
        {/* Pending Experience Cards */}
        <div className="space-y-2">
          {experiences.map((exp) => (
            <div 
              key={exp.match_id} 
              className="border border-gray-200 rounded-lg overflow-hidden bg-gray-50"
            >
              <div 
                className="flex items-center p-3 cursor-pointer hover:bg-gray-100 transition-colors"
                onClick={() => setExpandedExperience(
                  expandedExperience === exp.experience.id ? null : exp.experience.id
                )}
              >
                <div 
                  className="w-10 h-10 rounded-lg flex-shrink-0 bg-amber-100 mr-3 overflow-hidden"
                  style={{
                    backgroundImage: locationImages[exp.experience.id] ? 
                      `url(${locationImages[exp.experience.id]})` : 
                      'linear-gradient(to right, #f97316, #fb923c)',
                    backgroundSize: 'cover',
                    backgroundPosition: 'center'
                  }}
                ></div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h5 className="font-medium text-gray-800 text-sm truncate">
                      {exp.experience.experience_type}
                    </h5>
                    <div className="text-xs text-gray-500 ml-2 whitespace-nowrap">
                      {new Date(exp.created_at).toLocaleDateString()}
                    </div>
                  </div>
                  
                  <div className="flex items-center text-xs text-gray-600 mt-1">
                    <svg className="w-3 h-3 text-gray-500 mr-1 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    <span className="truncate">{exp.experience.location}</span>
                  </div>
                </div>
                
                <div className="ml-2">
                  {expandedExperience === exp.experience.id ? (
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 15l7-7 7 7" />
                    </svg>
                  ) : (
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                    </svg>
                  )}
                </div>
              </div>
              
              {/* Expanded details */}
              {expandedExperience === exp.experience.id && (
                <div className="px-3 pb-3 pt-0">
                  <div className="text-sm text-gray-700 mb-2 mt-1">
                    {exp.experience.description || "No description provided."}
                  </div>
                  
                  <div className="text-xs text-amber-600 flex items-center">
                    <svg className="w-3.5 h-3.5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Waiting for {user.name} to respond
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

const Matches = () => {
  const [pendingReceivedMatches, setPendingReceivedMatches] = useState([]);
  const [groupedConfirmedMatches, setGroupedConfirmedMatches] = useState({});
  const [groupedPendingReceivedMatches, setGroupedPendingReceivedMatches] = useState({});
  const [groupedPendingSentMatches, setGroupedPendingSentMatches] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('confirmed');
  const csrfToken = useCSRFToken();
  
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
      
      const response = await axios.get(`${API_URL}/api/matches/${user.id}`, { withCredentials: true,
        headers: {
          'Content-Type': 'application/json',
          'X-CsrfToken': csrfToken
        }});
      
      if (response.status !== 200) {
        throw new Error(`Failed to fetch matches: ${response.status}`);
      }
      
      const data = response.data;
      console.log('Matches data:', data);
      
      // Set the matches by category
      setPendingReceivedMatches(data.pending_received || []);
      
      // Group matches by user
      setGroupedConfirmedMatches(groupMatchesByUser(data.confirmed || []));
      setGroupedPendingReceivedMatches(groupMatchesByUser(data.pending_received || []));
      setGroupedPendingSentMatches(groupMatchesByUser(data.pending_sent || []));
      
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
      
      const response = await axios.put(`${API_URL}/api/matches/${matchId}/accept`, {}, { withCredentials: true,
        headers: {
          'Content-Type': 'application/json',
          'X-CsrfToken': csrfToken
        }
      });
      
      if (response.status !== 200) {
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
      
      const response = await axios.put(`${API_URL}/api/matches/${matchId}/reject`, {}, { withCredentials: true,
        headers: {
          'Content-Type': 'application/json',
          'X-CsrfToken': csrfToken
        }
      });
      
      if (response.status !== 200) {
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
  }, [user, csrfToken]);
  
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
            {Object.keys(groupedPendingReceivedMatches).length === 0 && Object.keys(groupedPendingSentMatches).length === 0 ? (
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
                
                {Object.keys(groupedPendingSentMatches).length > 0 && (
                  <div>
                    <h2 className="text-lg font-bold text-gray-800 mb-3">Experiences you're interested in</h2>
                    <div className="grid gap-4">
                      {Object.values(groupedPendingSentMatches).map(groupedMatch => (
                        <GroupedPendingSentMatchCard 
                          key={groupedMatch.user.id} 
                          user={groupedMatch.user} 
                          experiences={groupedMatch.experiences}
                        />
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