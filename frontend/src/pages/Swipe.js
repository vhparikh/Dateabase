import React, { useState, useEffect, useContext, useRef, useCallback } from 'react';
import AuthContext from '../context/AuthContext';
import { API_URL } from '../config';
import axios from 'axios';
import { useCSRFToken } from '../App';
import { motion } from 'framer-motion';
import './Swipe.css'; // Import the CSS file
import { Link } from 'react-router-dom';

const Swipe = () => {
  const [experiences, setExperiences] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [swipeDirection, setSwipeDirection] = useState(null);
  const [currentPosition, setCurrentPosition] = useState({ x: 0, y: 0 });
  const [isInitialLoad, setIsInitialLoad] = useState(true); // Track initial page load
  const [isAnimating, setIsAnimating] = useState(false); // Track if animation is in progress
  const [allExperiencesCompleted, setAllExperiencesCompleted] = useState(false); // Track if user has swiped through all experiences
  const [freshLocationImage, setFreshLocationImage] = useState(null); // Store the fresh image URL
  const [isLoadingImage, setIsLoadingImage] = useState(false); // Track image loading state
  const originalExperiencesRef = useRef([]); // Keep original experiences order for cycling
  const animationStepRef = useRef(0); // Track animation progress
  const { user } = useContext(AuthContext);
  const csrfToken = useCSRFToken();

  const fetchExperiences = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Reset the current state when fetching new experiences
      setExperiences([]);
      setCurrentIndex(0);
      setCurrentPosition({ x: 0, y: 0 });
      setSwipeDirection(null);
      animationStepRef.current = 0;
      
      // Check if user is logged in
      if (!user?.id) {
        setExperiences([]);
        setError('Please log in to view experiences');
        setLoading(false);
        return;
      }
      
      const response = await axios.get(`${API_URL}/api/swipe-experiences`, { withCredentials: true, headers: { 'X-CsrfToken': csrfToken }});
      
      if (response.status !== 200) {
        throw new Error(`Failed to fetch experiences: ${response.status}`);
      }
      
      const data = response.data;
      
      if (data && data.length > 0) {
        console.log(`Received ${data.length} experiences from API`);
        setExperiences(data);
        // Store the original experiences order
        originalExperiencesRef.current = [...data];
        setCurrentIndex(0);
      } else {
        // If no experiences are returned, but we've completed a cycle, we should try again with include_swiped=true
        console.log("No experiences found, showing empty state");
        setExperiences([]);
        originalExperiencesRef.current = [];
      }
    } catch (err) {
      console.error('Error fetching experiences:', err);
      setError('Failed to load experiences. Please try again.');
    } finally {
      setLoading(false);
      // After initial data load, mark as no longer the initial page load
      setIsInitialLoad(false);
    }
  }, [user?.id, csrfToken]);

  useEffect(() => {
    fetchExperiences();
  }, [fetchExperiences]);
  
  // Make sure swipeDirection is properly initialized as null
  useEffect(() => {
    // Reset swipe direction when loading experiences
    setSwipeDirection(null);
  }, [experiences]);

  const handleSwipe = async (isLike) => {
    // Prevent multiple animations from running simultaneously
    if (isAnimating) return;
    
    try {
      const currentExperience = experiences[currentIndex];
      if (!currentExperience) return;

      // Set animation in progress
      setIsAnimating(true);
      
      // Set animation direction for swipe-out
      setSwipeDirection(isLike ? 'right' : 'left');
      
      // Start multi-step animation
      animateSwipe(isLike);

    } catch (err) {
      console.error('Error handling swipe:', err);
      // Ensure we still reset state on error
      setCurrentPosition({ x: 0, y: 0 });
      setSwipeDirection(null);
      animationStepRef.current = 0;
      setIsAnimating(false); // Reset animation state on error
    }
  };
  
  const animateSwipe = (isLike) => {
    // Define the total animation steps
    const totalSteps = 16;
    // Define the max distance the card should move
    const maxDistance = isLike ? 500 : -500;
    
    // Set initial animation step
    animationStepRef.current = 1;
    
    // Create an animation sequence
    const animationInterval = setInterval(() => {
      animationStepRef.current += 1;
      
      // Calculate progress ratio (0 to 1)
      const progress = animationStepRef.current / totalSteps;
      
      // Apply easing function for more natural movement
      // Using cubic-bezier like easing for smooth acceleration and deceleration
      const easedProgress = progress < 0.5 
        ? 4 * progress * progress * progress 
        : 1 - Math.pow(-2 * progress + 2, 3) / 2;
        
      // Calculate new position with easing
      const newX = maxDistance * easedProgress;
      
      // Update card position with easing
      setCurrentPosition({ 
        x: newX, 
        y: 0 
      });
      
      // If we've completed all steps, clear the interval and finish the swipe
      if (animationStepRef.current >= totalSteps) {
        clearInterval(animationInterval);
        finishSwipe(isLike);
        animationStepRef.current = 0; // Reset step counter
      }
    }, 15); // Run even faster at 15ms for quicker animation
  };
  
  const finishSwipe = async (isLike) => {
    try {
      const currentExperience = experiences[currentIndex];
      if (!currentExperience) return;
      
      // Send swipe to backend
      const response = await axios.post(`${API_URL}/api/swipes`, { experience_id: currentExperience.id, is_like: isLike }, { withCredentials: true,
        headers: {
          'Content-Type': 'application/json',
          'X-CsrfToken': csrfToken
        }
      });

      if (response.status !== 200) {
        const errorData = response.data;
        throw new Error(errorData.detail || 'Failed to record swipe');
      }
      
      // Parse response data
      const responseData = response.data;
      console.log('Swipe response:', responseData);
      
      // Remove the match modal functionality
      if (responseData && responseData.match) {
        console.log('Match created with ID:', responseData.match.id, 'with user:', responseData.match.other_user.username);
        // No longer show the match modal
      }

      // Give more time for the animation to complete visually before transitioning
      setTimeout(() => {
        // Calculate the next index
        let nextIndex = currentIndex + 1;
        
        // Check if we've reached the end of available experiences
        if (experiences.length === 0) {
          // No experiences at all
          setAllExperiencesCompleted(true);
        } else if (nextIndex >= experiences.length) {
          // Reached the end of available experiences
          setAllExperiencesCompleted(true);
          console.log("Reached end of experiences, showing completion message");
        } else {
          // Still have more experiences to show
          setCurrentIndex(nextIndex);
        }
        
        // Reset the position and swipe direction
        setCurrentPosition({ x: 0, y: 0 });
        setSwipeDirection(null);
        setIsAnimating(false); // Reset animation state when complete
        
      }, 350); // Reduced from 450ms to 350ms for faster transition
      
    } catch (err) {
      console.error('Error in swipe handling:', err.toJSON());
      // Even if there's an error, we should still move to the next card if possible
      setTimeout(() => {
        // Calculate the next index
        let nextIndex = currentIndex + 1;
        
        // Check if we've reached the end of available experiences
        if (experiences.length === 0) {
          // No experiences at all
          setAllExperiencesCompleted(true);
        } else if (nextIndex >= experiences.length) {
          // Reached the end of available experiences
          setAllExperiencesCompleted(true);
          console.log("Reached end of experiences, showing completion message");
        } else {
          // Still have more experiences to show
          setCurrentIndex(nextIndex);
        }
        
        setCurrentPosition({ x: 0, y: 0 });
        setSwipeDirection(null);
        setIsAnimating(false); // Reset animation state on error
      }, 350); // Reduced from 450ms to 350ms for faster transition
    }
  };

  const handleRetry = () => {
    // Reset current index to 0 to avoid any out-of-bounds issues
    setCurrentIndex(0);
    // Reset the completed state
    setAllExperiencesCompleted(false);
    console.log("User clicked retry - resetting and fetching fresh experiences");
    // Fetch fresh experiences
    fetchExperiences();
  };

  // Fetch fresh location image 
  const fetchFreshLocationImage = useCallback(async (experienceId) => {
    if (!experienceId) return;
    
    try {
      setIsLoadingImage(true);
      const response = await axios.get(`${API_URL}/api/experiences/get-image/${experienceId}`, { 
        withCredentials: true 
      });
      
      if (response.data && response.data.image_url) {
        setFreshLocationImage(response.data.image_url);
      } else {
        // If API doesn't return a fresh image, clear the state
        setFreshLocationImage(null);
      }
    } catch (error) {
      console.error('Error fetching fresh location image:', error);
      // Clear the image state on error
      setFreshLocationImage(null);
    } finally {
      setIsLoadingImage(false);
    }
  }, []);

  // Load fresh image when current experience changes
  useEffect(() => {
    if (experiences.length > 0 && currentIndex < experiences.length) {
      const currentExperience = experiences[currentIndex];
      if (currentExperience && currentExperience.id) {
        // Fetch a fresh image for the current experience
        fetchFreshLocationImage(currentExperience.id);
      }
    }
  }, [experiences, currentIndex, fetchFreshLocationImage]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[80vh] bg-gradient-to-br from-orange-50 to-orange-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-orange-500 mx-auto mb-4"></div>
          <p className="text-orange-800 font-medium">Finding experiences for you...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-8 bg-gradient-to-br from-orange-50 to-orange-100 min-h-[80vh]">
        <div className="bg-white rounded-xl shadow-lg p-6 max-w-md mx-auto">
          <div className="text-center text-orange-500 mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-center mb-4">Oops! Something went wrong</h2>
          <p className="text-gray-600 text-center mb-6">{error}</p>
          <button 
            onClick={handleRetry}
            className="w-full py-3 bg-gradient-to-r from-orange-start to-orange-end text-white rounded-lg font-medium shadow-md hover:shadow-lg transition-all"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (allExperiencesCompleted) {
    return (
      <div className="py-8 bg-gradient-to-br from-orange-50 to-orange-100 min-h-[80vh]">
        <div className="bg-white rounded-xl shadow-lg p-8 max-w-md mx-auto text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold mb-3 text-orange-800">You've seen all available experiences!</h2>
          <p className="text-gray-600 mb-6">Please check back later for new ones. You can also create your own experiences for others to discover.</p>
          <div className="flex flex-col space-y-3">
            <button 
              onClick={handleRetry}
              className="px-6 py-3 bg-gradient-to-r from-orange-start to-orange-end text-white rounded-lg font-medium shadow-md hover:shadow-lg transition-all"
            >
              Check for New Experiences
            </button>
            <Link
              to="/experiences"
              className="px-6 py-3 bg-white text-orange-500 border border-orange-500 rounded-lg font-medium shadow-sm hover:shadow-md transition-all"
            >
              Create an Experience
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (experiences.length === 0) {
    return (
      <div className="py-8 bg-gradient-to-br from-orange-50 to-orange-100 min-h-[80vh]">
        <div className="bg-white rounded-xl shadow-lg p-8 max-w-md mx-auto text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-orange-100 rounded-full mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-orange-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold mb-3 text-orange-800">No experiences found</h2>
          <p className="text-gray-600 mb-6">We couldn't find any experiences for you right now. Check back later or create your own.</p>
          <button 
            onClick={handleRetry}
            className="px-6 py-3 bg-gradient-to-r from-orange-start to-orange-end text-white rounded-lg font-medium shadow-md hover:shadow-lg transition-all"
          >
            Refresh
          </button>
        </div>
      </div>
    );
  }

  const currentExperience = experiences[currentIndex];
  
  // Calculate rotation and opacity based on swipe position
  const cardRotation = currentPosition.x * 0.06;
  const cardOpacity = Math.max(0.5, 1 - Math.abs(currentPosition.x) / 500);

  // Get classes for the like/pass indicators
  const getLikeIndicatorClass = () => {
    return swipeDirection === 'right' 
      ? 'opacity-100 scale-110 like-indicator' 
      : 'opacity-0 scale-90';
  };
  
  const getPassIndicatorClass = () => {
    return swipeDirection === 'left' 
      ? 'opacity-100 scale-110 pass-indicator' 
      : 'opacity-0 scale-90';
  };

  return (
    <div className="pt-6 pb-8 bg-gradient-to-br from-orange-50 to-orange-100 min-h-[90vh]">
      <div className="max-w-md mx-auto px-4">
        {/* Swipe indicators - Like */}
        {!isInitialLoad && (
          <>
            <div 
              className={`absolute top-32 right-6 transform rotate-12 bg-green-500/90 text-white py-2 px-6 rounded-lg font-bold tracking-wider z-30 text-xl border-2 border-white transition-all ${getLikeIndicatorClass()}`}
              style={{ 
                boxShadow: '0 4px 10px rgba(0, 0, 0, 0.15)',
                transformOrigin: 'center',
                zIndex: 20,
                opacity: swipeDirection === 'right' ? 1 : 0, // Ensure it's only visible during swipe
                display: swipeDirection === 'right' ? 'block' : 'none' // Completely hide it when not needed
              }}
            >
              LIKE
            </div>
            
            {/* Swipe indicators - Pass */}
            <div 
              className={`absolute top-32 left-6 transform -rotate-12 bg-red-500/90 text-white py-2 px-6 rounded-lg font-bold tracking-wider z-30 text-xl border-2 border-white transition-all ${getPassIndicatorClass()}`}
              style={{ 
                boxShadow: '0 4px 10px rgba(0, 0, 0, 0.15)',
                transformOrigin: 'center',
                zIndex: 20,
                opacity: swipeDirection === 'left' ? 1 : 0, // Ensure it's only visible during swipe
                display: swipeDirection === 'left' ? 'block' : 'none' // Completely hide it when not needed
              }}
            >
              PASS
            </div>
          </>
        )}
        
        {/* Experience Card - Hinge Style */}
        <motion.div 
          className={`hinge-card ${swipeDirection === 'right' ? 'swipe-right-exit' : swipeDirection === 'left' ? 'swipe-left-exit' : ''}`}
          style={{
            x: currentPosition.x,
            y: currentPosition.y,
            rotate: cardRotation,
            opacity: cardOpacity,
            zIndex: 10
          }}
          whileHover={{ scale: 1.02 }}
          transition={{ 
            type: "spring",
            stiffness: 300,
            damping: 30,
            mass: 2
          }}
        >
          {/* Card Background Image */}
          <div className="hinge-card-image">
            {isLoadingImage ? (
              <div className="w-full h-full bg-gradient-to-br from-orange-400 to-orange-600 flex items-center justify-center">
                <div className="text-white text-xl font-medium">Loading...</div>
              </div>
            ) : freshLocationImage ? (
              <img
                src={freshLocationImage}
                alt={currentExperience.location}
                className="w-full h-full object-cover"
                onError={(e) => {
                  e.target.onerror = null;
                  e.target.src = currentExperience.location_image || `https://source.unsplash.com/featured/?${encodeURIComponent(currentExperience.location || 'restaurant')}`;
                }}
              />
            ) : currentExperience.location_image ? (
              <img
                src={currentExperience.location_image}
                alt={currentExperience.location}
                className="w-full h-full object-cover"
                onError={(e) => {
                  e.target.onerror = null;
                  e.target.src = `https://source.unsplash.com/featured/?${encodeURIComponent(currentExperience.location || 'restaurant')}`;
                }}
              />
            ) : (
              <div className="w-full h-full bg-gradient-to-br from-orange-400 to-orange-600 flex items-center justify-center">
                <div className="text-white text-2xl font-medium text-center px-4">
                  {currentExperience.location || "Mystery Location"}
                </div>
              </div>
            )}
            
            {/* Experience Type Badge */}
            <div className="absolute top-5 left-5 px-3 py-1 bg-white/90 rounded-full shadow-md">
              <span className="text-sm font-medium bg-clip-text text-transparent bg-gradient-to-r from-orange-start to-orange-end">
                {currentExperience.experience_type}
              </span>
            </div>
            
            {/* Gradient Overlay */}
            <div className="card-gradient-overlay"></div>
            
            {/* Card Info Section */}
            <div className="card-info-section">
              <h2 className="text-3xl font-bold text-white mb-1">
                {currentExperience.experience_name || currentExperience.place_name || currentExperience.location}
              </h2>
              
              {/* Always show the location below the name */}
              <p className="text-white/90 text-base mb-2">
                <svg className="inline-block w-4 h-4 mr-1 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
                </svg>
                {currentExperience.location}
              </p>
              
              <div className="creator-info mb-3">
                <div className="flex items-center">
                  {currentExperience.creator_profile_image ? (
                    <div className="w-10 h-10 rounded-full overflow-hidden mr-3 border-2 border-white shadow-md">
                      <img
                        src={currentExperience.creator_profile_image}
                        alt={currentExperience.creator_name || 'User'}
                        className="w-full h-full object-cover"
                      />
                    </div>
                  ) : (
                    <div className="w-10 h-10 rounded-full bg-gradient-to-r from-orange-start to-orange-end flex items-center justify-center mr-3 border-2 border-white shadow-md">
                      <span className="text-white font-bold">
                        {currentExperience.creator_name?.charAt(0).toUpperCase() || 'U'}
                      </span>
                    </div>
                  )}
                  <div>
                    <p className="text-white font-bold text-lg">
                      {currentExperience.creator_name || 'Anonymous'}
                    </p>
                    <p className="text-white/80 text-sm">
                      {currentExperience.creator_netid || 'Experience Creator'}
                    </p>
                  </div>
                </div>
              </div>
              
              {/* Prompt/Description Section */}
              <div className="prompt-section">
                <div className="text-white/90 text-base">
                  <span className="font-semibold">About this experience: </span>
                  {currentExperience.description || "No description provided."}
                </div>
              </div>
            </div>
          </div>
        </motion.div>
        
        {/* Controls */}
        <div className="flex justify-center items-center space-x-6 mt-8">
          <button 
            onClick={() => {
              // Trigger the full multi-step animation
              handleSwipe(false);
            }}
            disabled={isAnimating}
            className={`w-16 h-16 rounded-full bg-white flex items-center justify-center shadow-lg border border-gray-200 hover:border-red-400 transition-colors action-button ${isAnimating ? 'opacity-50 cursor-not-allowed' : ''}`}
            aria-label="Pass"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
          
          <button
            onClick={handleRetry}
            disabled={isAnimating}
            className={`w-12 h-12 rounded-full bg-white flex items-center justify-center shadow-lg border border-gray-200 hover:border-blue-400 transition-colors action-button ${isAnimating ? 'opacity-50 cursor-not-allowed' : ''}`}
            aria-label="Refresh"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
          
          <button 
            onClick={() => {
              // Trigger the full multi-step animation
              handleSwipe(true);
            }}
            disabled={isAnimating}
            className={`w-16 h-16 rounded-full bg-white flex items-center justify-center shadow-lg border border-gray-200 hover:border-green-400 transition-colors action-button ${isAnimating ? 'opacity-50 cursor-not-allowed' : ''}`}
            aria-label="Like"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
            </svg>
          </button>
        </div>
      </div>
      
      <div className="max-w-md mx-auto mt-6 text-center px-4">
        <p className="text-sm text-orange-800">
          Click the buttons to like or pass
        </p>
      </div>
    </div>
  );
};

export default Swipe;
