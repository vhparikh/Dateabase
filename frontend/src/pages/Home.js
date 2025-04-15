import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { API_URL } from '../config';
import axios from 'axios';
import AuthContext from '../context/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';
import { GoogleMap, LoadScript, Marker, InfoWindow } from '@react-google-maps/api';

// Experience card component with improved design
const ExperienceCard = ({ experience, onSwipe, style, zIndex = 0 }) => {
  const [startX, setStartX] = useState(0);
  const [offsetX, setOffsetX] = useState(0);
  const [direction, setDirection] = useState(null);
  const [showDetails, setShowDetails] = useState(false);
  const [locationImage, setLocationImage] = useState(null);
  
  // Google Maps configuration
  const mapContainerStyle = {
    width: '100%',
    height: '160px',
    borderRadius: '8px',
  };
  
  const mapCenter = {
    lat: experience.latitude || 40.3431, // Default to Princeton's latitude
    lng: experience.longitude || -74.6551, // Default to Princeton's longitude
  };
  
  const mapOptions = {
    disableDefaultUI: true,
    zoomControl: true,
  };
  
  // Load location image on component mount
  useEffect(() => {
    if (experience.location_image) {
      setLocationImage(experience.location_image);
    } else if (experience.location) {
      // Fallback to Unsplash if no location image is provided
      setLocationImage(`https://source.unsplash.com/random/800x600/?${experience.location.replace(/\s+/g, '+')}`);
    }
  }, [experience.location, experience.location_image]);
  
  // Handle touch/mouse events for swiping
  const handleTouchStart = (e) => {
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    setStartX(clientX);
  };
  
  const handleTouchMove = (e) => {
    if (!startX) return;
    
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const diff = clientX - startX;
    
    setOffsetX(diff);
    
    if (diff > 50) {
      setDirection('right');
    } else if (diff < -50) {
      setDirection('left');
    } else {
      setDirection(null);
    }
  };
  
  const handleTouchEnd = () => {
    if (direction === 'right') {
      onSwipe(experience.id, 'right');
    } else if (direction === 'left') {
      onSwipe(experience.id, 'left');
    }
    
    setStartX(0);
    setOffsetX(0);
    setDirection(null);
  };
  
  const toggleDetails = (e) => {
    e.stopPropagation();
    setShowDetails(!showDetails);
  };
  
  // Calculate dynamic styles based on swipe
  const cardStyle = {
    transform: `translateX(${offsetX}px) rotate(${offsetX * 0.05}deg)`,
    transition: startX ? 'none' : 'transform 0.5s ease',
    opacity: 1 - Math.min(0.5, Math.abs(offsetX) / 500),
    ...style,
    zIndex,
  };
  
  // Visual feedback for swipe direction
  const getSwipeIndicatorStyle = () => {
    if (direction === 'right') {
      return 'border-green-500 bg-green-50 text-green-700';
    } else if (direction === 'left') {
      return 'border-red-500 bg-red-50 text-red-700';
    }
    return 'border-gray-300 bg-gray-50 text-gray-500';
  };
  
  const getActionText = () => {
    if (direction === 'right') return 'Like';
    if (direction === 'left') return 'Pass';
    return 'Swipe';
  };
  
  return (
    <div
      className="absolute top-0 left-0 right-0 mx-auto w-full max-w-sm"
      style={cardStyle}
      onMouseDown={handleTouchStart}
      onMouseMove={handleTouchMove}
      onMouseUp={handleTouchEnd}
      onMouseLeave={handleTouchEnd}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      <div className="card overflow-hidden">
        <div className="relative">
          {/* Swipe indicator */}
          <div 
            className={`absolute top-4 right-4 px-3 py-1 rounded-full text-sm font-medium border ${getSwipeIndicatorStyle()} transition-opacity z-10 ${direction ? 'opacity-100' : 'opacity-0'}`}
          >
            {getActionText()}
          </div>
          
          {/* Experience type badge */}
          <div className="absolute top-4 left-4 z-10">
            <span className="px-3 py-1 bg-white/90 rounded-full shadow-sm text-sm font-medium bg-clip-text text-transparent bg-gradient-to-r from-orange-start to-orange-end">
              {experience.experience_type}
            </span>
          </div>
          
          {/* Location image */}
          <div className="h-48 overflow-hidden relative">
            {locationImage ? (
              <img 
                src={locationImage} 
                alt={experience.location || 'Princeton'} 
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="h-48 bg-gradient-to-br from-orange-400 to-orange-600 flex items-center justify-center">
                <div className="text-white font-bold text-2xl opacity-80">
                  {experience.location || "Princeton"}
                </div>
              </div>
            )}
            
            {/* Semi-transparent overlay to ensure text readability */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent"></div>
            
            {/* Location name overlay */}
            <div className="absolute bottom-0 left-0 right-0 p-3 text-white font-medium">
              {experience.location || "Princeton"}
            </div>
          </div>
          
          {/* Content */}
          <div className="p-5">
            <div className="flex justify-between items-start mb-4">
              <h2 className="text-xl font-bold text-gray-800">
                {experience.experience_type}
              </h2>
              
              <button 
                onClick={toggleDetails}
                className="p-1 hover:bg-orange-50 rounded-full transition-colors"
              >
                <svg className="w-5 h-5 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
              </button>
            </div>
            
            <div className="flex items-center text-sm text-gray-600 mb-3">
              <svg className="w-4 h-4 mr-1 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
              </svg>
              {experience.location || 'Princeton University'}
            </div>
            
            <p className="text-gray-600 text-sm mb-4">
              {experience.description?.length > 120 ? 
                `${experience.description.substring(0, 120)}...` : 
                experience.description || 'No description provided'}
            </p>
            
            {/* Created by */}
            <div className="flex items-center justify-between pt-3 border-t border-gray-100">
              <div className="flex items-center">
                {experience.creator?.profile_image ? (
                  <div className="w-8 h-8 rounded-full overflow-hidden">
                    <img 
                      src={experience.creator.profile_image} 
                      alt={experience.creator?.username || 'User'} 
                      className="w-full h-full object-cover"
                    />
                  </div>
                ) : (
                  <div className="w-8 h-8 rounded-full bg-gradient-to-r from-orange-start to-orange-end flex items-center justify-center text-white font-medium">
                    {experience.creator?.username?.charAt(0).toUpperCase() || 'U'}
                  </div>
                )}
                <div className="ml-2">
                  <p className="text-sm font-medium text-gray-700">
                    {experience.creator?.username || 'Anonymous'}
                  </p>
                </div>
              </div>
              
              {/* Swipe instructions */}
              <div className="text-xs text-gray-500 flex items-center">
                <span>Swipe or use buttons</span>
              </div>
            </div>
          </div>
          
          {/* Expanded details */}
          {showDetails && (
            <div className="p-5 bg-orange-50 border-t border-orange-100">
              <h3 className="font-medium text-gray-800 mb-2">Experience Details</h3>
              <p className="text-gray-600 text-sm mb-4">
                {experience.description || 'No description provided'}
              </p>
              
              {/* Google Maps integration */}
              <div className="mb-4">
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
              
              <button 
                onClick={toggleDetails}
                className="w-full py-2 text-sm text-orange-600 hover:bg-orange-100 rounded-lg transition-colors"
              >
                Close Details
              </button>
            </div>
          )}
        </div>
      </div>
      
      {/* Action buttons */}
      <div className="flex justify-center mt-4 space-x-3">
        <button
          onClick={() => onSwipe(experience.id, 'left')}
          className="w-10 h-10 rounded-full bg-white border border-gray-200 shadow flex items-center justify-center hover:border-red-400 transition-colors"
        >
          <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
        
        <button
          onClick={() => onSwipe(experience.id, 'right')}
          className="w-10 h-10 rounded-full bg-white border border-gray-200 shadow flex items-center justify-center hover:border-green-400 transition-colors"
        >
          <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path>
          </svg>
        </button>
      </div>
    </div>
  );
};

const NoMoreExperiences = ({ refresh }) => {
  return (
    <div className="paper-effect text-center max-w-md mx-auto py-10 px-6">
      <div className="w-20 h-20 mx-auto mb-6 bg-orange-100 rounded-full flex items-center justify-center">
        <svg className="w-10 h-10 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
        </svg>
      </div>
      <h3 className="text-2xl font-bold mb-2 text-gray-800">No More Experiences</h3>
      <p className="text-gray-600 mb-8">You've seen all experiences currently available. Check back later for more!</p>
      
      <button 
        onClick={refresh} 
        className="btn-primary w-full mb-4"
      >
        Refresh Experiences
      </button>
      
      <button 
        onClick={() => refresh(true)} 
        className="btn-outline w-full"
      >
        Reset Demo Data
      </button>
    </div>
  );
};

const MatchModal = ({ match, onClose }) => {
  const [currentSection, setCurrentSection] = useState(0);
  const [locationImage, setLocationImage] = useState(null);
  
  // Create sections for Hinge-like profile
  const profileSections = [
    {
      type: 'match',
      title: "It's a Match!",
      content: `You and ${match.other_user.name} both want to experience ${match.experience.experience_type}!`
    },
    {
      type: 'profile',
      title: 'About',
      content: match.other_user.name
    },
    {
      type: 'location',
      title: match.experience.experience_type,
      content: match.experience.location,
      description: match.experience.description,
      image: locationImage
    }
  ];
  
  useEffect(() => {
    // Get location image from Unsplash
    if (match.experience.location) {
      setLocationImage(`https://source.unsplash.com/random/800x600/?${match.experience.location.replace(/\s+/g, '+')}`);
    }
  }, [match.experience.location]);
  
  const navigateSection = (direction) => {
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
  
  const renderProfileSection = (section, index) => {
    switch (section.type) {
      case 'match':
        return (
          <div className="text-center py-8 px-4">
            <div className="w-20 h-20 mx-auto bg-orange-gradient rounded-full flex items-center justify-center mb-6">
              <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold mb-2 text-gray-800">{section.title}</h2>
            <p className="text-gray-600">{section.content}</p>
            
            <div className="flex items-center justify-center mt-6 space-x-3">
              <div className="flex flex-col items-center">
                <div className="w-16 h-16 rounded-full bg-orange-100 flex items-center justify-center text-orange-600 text-xl font-bold">
                  {match.current_user.name.charAt(0)}
                </div>
                <p className="mt-2 text-sm font-medium text-gray-600">{match.current_user.name}</p>
              </div>
              
              <div className="w-10 flex items-center justify-center">
                <svg className="w-8 h-8 text-orange-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clipRule="evenodd"></path>
                </svg>
              </div>
              
              <div className="flex flex-col items-center">
                <div className="w-16 h-16 rounded-full bg-orange-100 flex items-center justify-center text-orange-600 text-xl font-bold">
                  {match.other_user.name.charAt(0)}
                </div>
                <p className="mt-2 text-sm font-medium text-gray-600">{match.other_user.name}</p>
              </div>
            </div>
          </div>
        );
        
      case 'profile':
        return (
          <div className="px-4 py-6">
            <div className="mb-6 text-center">
              <div className="w-24 h-24 mx-auto rounded-full bg-orange-gradient flex items-center justify-center mb-4 text-white text-3xl font-bold">
                {match.other_user.name.charAt(0)}
              </div>
              <h3 className="text-2xl font-bold text-gray-800">{match.other_user.name}</h3>
            </div>
            
            <div className="space-y-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm text-gray-500 mb-1">About the match</div>
                <div className="text-gray-800">
                  This person also wants to experience {match.experience.experience_type} at {match.experience.location}.
                </div>
              </div>
            </div>
          </div>
        );
        
      case 'location':
        return (
          <div className="px-4 py-6">
            <h3 className="text-xl font-bold text-gray-800 mb-4">{section.title}</h3>
            
            {/* Location image */}
            <div className="relative rounded-lg overflow-hidden mb-4">
              <div className="aspect-video bg-gray-200">
                {locationImage ? (
                  <img 
                    src={locationImage} 
                    alt={section.content} 
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center bg-orange-50 text-orange-800">
                    {section.content}
                  </div>
                )}
              </div>
              
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent"></div>
              
              <div className="absolute bottom-0 left-0 right-0 p-4 text-white">
                <div className="text-xs uppercase tracking-wide mb-1">Location</div>
                <div className="text-xl font-bold">{section.content}</div>
                
                <button 
                  onClick={openGoogleMaps}
                  className="mt-2 flex items-center text-xs font-medium bg-white/20 hover:bg-white/30 backdrop-blur-sm rounded-full px-3 py-1.5 transition-colors"
                >
                  <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" />
                  </svg>
                  View on Google Maps
                </button>
              </div>
            </div>
            
            {/* Description */}
            <div className="bg-gray-50 rounded-lg p-4 mb-4">
              <div className="text-sm text-gray-500 mb-1">Description</div>
              <div className="text-gray-800">
                {section.description || "No description provided."}
              </div>
            </div>
          </div>
        );
        
      default:
        return null;
    }
  };
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-xl overflow-hidden w-full max-w-md animate-scale-in">
        {/* Close button */}
        <button 
          onClick={onClose}
          className="absolute top-4 right-4 z-50 bg-white/80 rounded-full p-1 shadow-md text-gray-700 hover:text-gray-900"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
        
        {/* Content */}
        <div className="relative">
          {/* Current section */}
          {renderProfileSection(profileSections[currentSection], currentSection)}
          
          {/* Navigation dots */}
          <div className="flex justify-center space-x-1 py-3 border-t border-gray-100">
            {profileSections.map((_, index) => (
              <button 
                key={index} 
                onClick={() => setCurrentSection(index)}
                className={`w-2 h-2 rounded-full ${index === currentSection ? 'bg-orange-500' : 'bg-gray-300'}`}
                aria-label={`Go to slide ${index + 1}`}
              />
            ))}
          </div>
        </div>
        
        {/* Action buttons */}
        <div className="flex border-t border-gray-200">
          <button 
            onClick={onClose}
            className="flex-1 py-4 text-gray-600 hover:bg-gray-50 transition-colors font-medium"
          >
            Maybe Later
          </button>
          <button 
            onClick={onClose}
            className="flex-1 py-4 bg-orange-gradient text-white font-medium hover:opacity-90 transition-opacity"
          >
            Send Message
          </button>
        </div>
      </div>
    </div>
  );
};

const Home = () => {
  const navigate = useNavigate();
  const handleCreateExperienceClick = () => {
    navigate('/experiences', { state: { shouldCallAddExperience: true }});
  };
  const { user } = useContext(AuthContext);
  const [experiences, setExperiences] = useState([]);
  const [popularExperiences, setPopularExperiences] = useState([]);
  const [visibleExperiences, setVisibleExperiences] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showMatch, setShowMatch] = useState(false);
  const [matchDetails, setMatchDetails] = useState(null);
  
  // States for matches section
  const [matches, setMatches] = useState([]);
  const [matchesLoading, setMatchesLoading] = useState(true);
  const [matchesError, setMatchesError] = useState(null);
  
  // Fetch experiences when component mounts
  useEffect(() => {
    fetchExperiences();
    fetchMatches();
  }, [/* eslint-disable-line react-hooks/exhaustive-deps */]);
  
  // Fetch user matches
  const fetchMatches = async () => {
    try {
      setMatchesLoading(true);
      setMatchesError(null);
      
      // Only fetch matches if user is logged in
      if (!user?.id && !user?.sub) {
        setMatches([]);
        setMatchesLoading(false);
        return;
      }
      
      const response = await axios.get(`${API_URL}/api/matches/${user?.id || user?.sub}`, {
        withCredentials: true
      });
      
      if (response.data && Array.isArray(response.data)) {
        setMatches(response.data.slice(0, 3)); // Only show up to 3 matches
      } else if (response.data && response.data.matches) {
        // Handle case where matches are nested in an object
        setMatches(response.data.matches.slice(0, 3));
      } else {
        setMatches([]);
      }
    } catch (err) {
      console.error('Error fetching matches:', err);
      setMatchesError('Failed to load matches');
    } finally {
      setMatchesLoading(false);
    }
  };
  
  const fetchExperiences = async () => {
    try {
      setLoading(true);
      setError('');
      
      // Only fetch experiences if the user is logged in
      if (!user?.id && !user?.sub) {
        setExperiences([]);
        setPopularExperiences([]);
        setVisibleExperiences([]);
        setLoading(false);
        return;
      }
      
      const url = `${API_URL}/api/recommendations/${user?.id || user?.sub}`;
      const response = await axios.get(url, {
        withCredentials: true
      });
      
      if (response.data && Array.isArray(response.data)) {
        const fetchedExperiences = response.data;
        setExperiences(fetchedExperiences);
        setPopularExperiences(fetchedExperiences);
        setVisibleExperiences(fetchedExperiences);
      } else {
        setExperiences([]);
        setPopularExperiences([]);
        setVisibleExperiences([]);
      }
      
      setCurrentIndex(0);
    } catch (err) {
      console.error('Error fetching experiences:', err);
      setError('Failed to load experiences. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  // Refresh experiences
  const resetExperiences = () => {
    fetchExperiences();
  };
  
  const handleSwipe = async (experienceId, direction) => {
    try {
      // Optimistically update UI
      const newVisibleExperiences = [...visibleExperiences];
      const swipedExperience = newVisibleExperiences.shift();
      setVisibleExperiences(newVisibleExperiences);
      
      // Convert string direction to boolean expected by the backend
      // 'right' = true, 'left' = false
      const directionBool = direction === 'right';
      
      // Call API to record swipe
      const response = await axios.post(`${API_URL}/api/swipes`, {
        user_id: user?.id || user?.sub,
        experience_id: experienceId,
        direction: directionBool
      });
      
      // Handle match
      if (response.data && response.data.match) {
        // Format match data for display
        const matchData = {
          current_user: {
            name: user?.username || 'You',
            id: user?.id || user?.sub
          },
          other_user: {
            name: response.data.match.other_user?.username || 'Someone',
            id: response.data.match.other_user?.id
          },
          experience: {
            experience_type: swipedExperience.experience_type,
            description: swipedExperience.description,
            location: swipedExperience.location
          }
        };
        
        setMatchDetails(matchData);
        setShowMatch(true);
      }
    } catch (err) {
      console.error('Error recording swipe:', err);
      // Add experience back if there was an error
      fetchExperiences();
    }
  };
  
  const handleLikeClick = () => {
    if (visibleExperiences.length > 0) {
      handleSwipe(visibleExperiences[0].id, 'right');
    }
  };
  
  const handlePassClick = () => {
    if (visibleExperiences.length > 0) {
      handleSwipe(visibleExperiences[0].id, 'left');
    }
  };
  
  return (
    <div className="py-6">
      {/* Hero Section */}
      <section className="mb-12">
        <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-3xl overflow-hidden shadow-sm">
          <div className="px-6 py-12 md:px-12 md:py-16 max-w-5xl mx-auto">
            <div className="text-center md:text-left md:max-w-lg">
              <h1 className="text-4xl md:text-5xl font-extrabold mb-4 text-transparent bg-clip-text bg-gradient-to-r from-orange-start to-orange-end">
                Find Your Next Experience
              </h1>
              <p className="text-gray-700 mb-8 text-lg">
                Connect with others who share your interest in experiencing new activities and places around Princeton.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center md:justify-start">
                <a 
                  href="/swipe" 
                  className="px-6 py-3 bg-gradient-to-r from-orange-start to-orange-end text-white font-medium rounded-lg shadow-md hover:shadow-lg transition-all"
                >
                  Start Swiping
                </a>
                <button 
                  onClick={handleCreateExperienceClick}
                  className="px-6 py-3 bg-white text-orange-600 font-medium rounded-lg shadow border border-orange-100 hover:bg-orange-50 transition-colors"
                >
                  Create Experience
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>
      
      {/* Match Modal */}
      <AnimatePresence>
        {showMatch && matchDetails && (
          <MatchModal
            match={matchDetails}
            onClose={() => setShowMatch(false)}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

export default Home; 