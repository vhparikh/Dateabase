import React, { useState, useEffect, useContext } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { API_URL } from '../config';
import AuthContext from '../context/AuthContext';
import { GoogleMap, LoadScript, Marker } from '@react-google-maps/api';

// Updated Match Card with orange gradient theme
const MatchCard = ({ match }) => {
  const [showMap, setShowMap] = useState(false);
  const [locationImage, setLocationImage] = useState(null);
  const [currentSection, setCurrentSection] = useState(0);
  
  // Create profile sections for Hinge-style UI
  const profileSections = [
    {
      type: 'profile',
      title: 'Basic Info',
      content: {
        name: match.other_user.name,
        avatar: match.other_user.profile_image || `https://ui-avatars.com/api/?name=${match.other_user.name}&background=orange&color=fff`,
        classYear: match.other_user.class_year || 'N/A'
      }
    },
    {
      type: 'bio',
      title: 'About me',
      content: match.other_user.bio || `I'm interested in ${match.experience.experience_type}.`
    },
    {
      type: 'education',
      title: 'Education',
      content: 'Princeton University'
    },
    {
      type: 'location',
      title: match.experience.experience_type,
      subtitle: 'Experience Location',
      content: match.experience.location,
      description: match.experience.description || 'No description provided',
      image: locationImage
    }
  ];
  
  // Google Maps configuration
  const mapContainerStyle = {
    width: '100%',
    height: '200px',
    borderRadius: '8px',
  };
  
  const mapCenter = {
    lat: match.experience.latitude || 40.3431, // Default to Princeton's latitude
    lng: match.experience.longitude || -74.6551, // Default to Princeton's longitude
  };
  
  const mapOptions = {
    disableDefaultUI: true,
    zoomControl: true,
  };
  
  // Load location image on component mount
  useEffect(() => {
    if (match.experience.location_image) {
      setLocationImage(match.experience.location_image);
    } else if (match.experience.location) {
      // Fallback to Unsplash if no location image is provided
      setLocationImage(`https://source.unsplash.com/random/800x600/?${match.experience.location.replace(/\s+/g, '+')}`);
    }
  }, [match.experience.location, match.experience.location_image]);
  
  const navigateSections = (direction) => {
    if (direction === 'next') {
      setCurrentSection((prev) => 
        prev === profileSections.length - 1 ? 0 : prev + 1
      );
    } else {
      setCurrentSection((prev) => 
        prev === 0 ? profileSections.length - 1 : prev - 1
      );
    }
  };
  
  const openGoogleMaps = () => {
    if (match.experience.latitude && match.experience.longitude) {
      window.open(`https://www.google.com/maps/search/?api=1&query=${match.experience.latitude},${match.experience.longitude}`, '_blank');
    } else {
      window.open(`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(match.experience.location)}`, '_blank');
    }
  };
  
  const renderSection = (section) => {
    switch (section.type) {
      case 'profile':
        return (
          <div className="bg-white rounded-xl overflow-hidden shadow-card mb-4">
            {/* Header with avatar and name */}
            <div className="relative">
              <div className="aspect-square bg-orange-50">
                <img 
                  src={section.content.avatar} 
                  alt={section.content.name} 
                  className="w-full h-full object-cover"
                />
              </div>
              
              <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/70 to-transparent">
                <h3 className="text-2xl font-bold text-white">{section.content.name}</h3>
                <p className="text-sm text-white/80">Class of {section.content.classYear}</p>
              </div>
            </div>
            
            {/* Basic info panels */}
            <div className="p-4">
              <div className="flex justify-between items-center mb-4">
                <span className="text-sm text-gray-500">{section.title}</span>
                <span className="px-2 py-0.5 bg-orange-100 text-orange-700 text-xs rounded-full">Match!</span>
              </div>
              
              <div className="flex justify-between mt-2">
                <button className="px-4 py-2 bg-gradient-to-r from-orange-start to-orange-end text-white rounded-lg text-sm font-medium shadow-sm hover:shadow-md transition-all">Message</button>
                <button 
                  onClick={() => navigateSections('next')}
                  className="text-orange-600 text-sm flex items-center"
                >
                  View more info
                  <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        );
      
      case 'bio':
      case 'education':
        return (
          <div className="bg-white rounded-xl overflow-hidden shadow-card mb-4">
            <div className="p-4 border-b border-orange-100">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold text-gray-800">{section.title}</h3>
                <span className="w-6 h-6 bg-orange-100 rounded-full flex items-center justify-center text-orange-600">
                  {section.type === 'bio' ? (
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                  ) : (
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 14l9-5-9-5-9 5 9 5z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 14l9-5-9-5-9 5 9 5zm0 0l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998a12.078 12.078 0 01.665-6.479L12 14zm-4 6v-7.5l4-2.222" />
                    </svg>
                  )}
                </span>
              </div>
            </div>
            <div className="p-4">
              <p className="text-gray-700">{section.content}</p>
              
              <div className="flex justify-between mt-4">
                <button 
                  onClick={() => navigateSections('prev')}
                  className="text-orange-600 text-sm flex items-center"
                >
                  <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7" />
                  </svg>
                  Previous
                </button>
                <button 
                  onClick={() => navigateSections('next')}
                  className="text-orange-600 text-sm flex items-center"
                >
                  Next
                  <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        );
      
      case 'location':
        return (
          <div className="bg-white rounded-xl overflow-hidden shadow-card mb-4">
            <div className="p-4 border-b border-orange-100">
              <div className="flex justify-between items-center">
                <div>
                  <h3 className="text-lg font-semibold text-gray-800">{section.title}</h3>
                  <p className="text-sm text-gray-500">{section.subtitle}</p>
                </div>
                <span className="w-6 h-6 bg-orange-100 rounded-full flex items-center justify-center text-orange-600">
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </span>
              </div>
            </div>
            
            {/* Location image */}
            <div className="relative">
              <div className="aspect-video bg-gray-200">
                {section.image ? (
                  <img 
                    src={section.image} 
                    alt={section.content} 
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-orange-400 to-orange-600 text-white">
                    {section.content}
                  </div>
                )}
              </div>
              
              <div className="absolute bottom-0 left-0 right-0 p-3 bg-gradient-to-t from-black/60 to-transparent">
                <div className="text-white text-lg font-bold truncate">{section.content}</div>
                <button 
                  onClick={openGoogleMaps}
                  className="mt-1 flex items-center text-xs font-medium bg-white/20 hover:bg-white/30 backdrop-blur-sm rounded-full px-2 py-1 transition-colors"
                >
                  <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" />
                  </svg>
                  Maps
                </button>
              </div>
            </div>
            
            {/* Description */}
            <div className="p-4">
              <div className="text-sm text-gray-500 mb-1">Description</div>
              <p className="text-gray-700 mb-4">{section.description}</p>
              
              <div className="flex justify-between">
                <button 
                  onClick={() => navigateSections('prev')}
                  className="text-orange-600 text-sm flex items-center"
                >
                  <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7" />
                  </svg>
                  Previous
                </button>
                <button 
                  onClick={() => setShowMap(!showMap)}
                  className="text-orange-600 text-sm flex items-center"
                >
                  {showMap ? 'Hide Map' : 'Show Map'}
                  <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                  </svg>
                </button>
              </div>
              
              {/* Google Maps */}
              {showMap && (
                <div className="mt-4">
                  <LoadScript googleMapsApiKey={process.env.REACT_APP_GOOGLE_MAPS_API_KEY || ""}>
                    <GoogleMap
                      mapContainerStyle={mapContainerStyle}
                      center={mapCenter}
                      zoom={14}
                      options={mapOptions}
                    >
                      <Marker position={mapCenter} />
                    </GoogleMap>
                  </LoadScript>
                </div>
              )}
            </div>
          </div>
        );
        
      default:
        return null;
    }
  };
  
  // Render dots for navigation
  const renderDots = () => (
    <div className="flex justify-center space-x-1 mt-2">
      {profileSections.map((_, index) => (
        <button 
          key={index} 
          onClick={() => setCurrentSection(index)}
          className={`w-2 h-2 rounded-full transition-colors ${index === currentSection ? 'bg-orange-500' : 'bg-gray-300'}`}
          aria-label={`Go to section ${index + 1}`}
        />
      ))}
    </div>
  );
  
  return (
    <div className="w-full mb-6 mx-auto max-w-sm">
      {renderSection(profileSections[currentSection])}
      {renderDots()}
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

// Potential Match Card component
const PotentialMatchCard = ({ match, onAccept, onReject }) => {
  const [locationImage, setLocationImage] = useState(null);
  
  // Load location image on component mount
  useEffect(() => {
    if (match.experience.location_image) {
      setLocationImage(match.experience.location_image);
    } else if (match.experience.location) {
      // Fallback to Unsplash if no location image is provided
      setLocationImage(`https://source.unsplash.com/random/800x600/?${match.experience.location.replace(/\s+/g, '+')}`);
    }
  }, [match.experience.location, match.experience.location_image]);
  
  return (
    <div className="bg-white rounded-xl overflow-hidden shadow-card mb-4">
      {/* Header */}
      <div className="relative">
        <div className="h-32 bg-orange-50">
          <img 
            src={locationImage || `https://source.unsplash.com/random/800x600/?experience`} 
            alt={match.experience.location} 
            className="w-full h-full object-cover"
          />
        </div>
        
        <div className="absolute -bottom-12 left-4">
          <div className="w-24 h-24 rounded-full border-4 border-white overflow-hidden bg-gradient-to-r from-orange-start to-orange-end">
            <img 
              src={match.other_user.profile_image || `https://ui-avatars.com/api/?name=${match.other_user.name}&background=orange&color=fff`} 
              alt={match.other_user.name} 
              className="w-full h-full object-cover"
            />
          </div>
        </div>
      </div>
      
      {/* Content */}
      <div className="pt-14 px-4 pb-4">
        <h3 className="text-lg font-bold text-gray-800">{match.other_user.name}</h3>
        <p className="text-sm text-gray-500 mb-2">Class of {match.other_user.class_year || 'N/A'}</p>
        
        <div className="p-3 bg-orange-50 rounded-lg mb-3">
          <div className="text-sm font-medium text-orange-800">Interested in your experience:</div>
          <div className="flex items-center mt-1">
            <svg className="w-4 h-4 text-orange-700 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <span className="text-gray-700 font-medium">{match.experience.location}</span>
          </div>
          <div className="mt-2 text-gray-600 text-sm">
            {match.experience.description ? (
              <div className="line-clamp-2">{match.experience.description}</div>
            ) : (
              <div>{match.experience.experience_type}</div>
            )}
          </div>
        </div>
        
        <div className="flex space-x-2">
          <button 
            onClick={() => onReject(match.match_id)}
            className="flex-1 py-2 px-4 border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50 transition-colors"
          >
            Decline
          </button>
          <button 
            onClick={() => onAccept(match.match_id)}
            className="flex-1 py-2 px-4 bg-gradient-to-r from-orange-start to-orange-end text-white rounded-lg font-medium hover:shadow-md transition-all"
          >
            Accept
          </button>
        </div>
      </div>
    </div>
  );
};

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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('confirmed');
  
  const { user } = useContext(AuthContext);
  
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
          confirmedMatches.length === 0 ? (
            <EmptyState />
          ) : (
            <div className="grid gap-4">
              {confirmedMatches.map(match => (
                <MatchCard key={match.match_id} match={match} />
              ))}
            </div>
          )
        ) : (
          <div>
            {pendingReceivedMatches.length === 0 && pendingSentMatches.length === 0 ? (
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
                {pendingReceivedMatches.length > 0 && (
                  <div className="mb-6">
                    <h2 className="text-lg font-bold text-gray-800 mb-3">People interested in your experiences</h2>
                    <div className="grid gap-4">
                      {pendingReceivedMatches.map(match => (
                        <PotentialMatchCard 
                          key={match.match_id} 
                          match={match} 
                          onAccept={handleAcceptMatch} 
                          onReject={handleRejectMatch} 
                        />
                      ))}
                    </div>
                  </div>
                )}
                
                {pendingSentMatches.length > 0 && (
                  <div>
                    <h2 className="text-lg font-bold text-gray-800 mb-3">Your pending requests</h2>
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