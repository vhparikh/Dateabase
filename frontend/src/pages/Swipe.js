import React, { useState, useEffect, useContext } from 'react';
import AuthContext from '../context/AuthContext';
import { API_URL } from '../config';
import { motion, AnimatePresence } from 'framer-motion';
import './Swipe.css'; // Import the CSS file
import { Link } from 'react-router-dom';

const Swipe = () => {
  const [experiences, setExperiences] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [swipeDirection, setSwipeDirection] = useState(null);
  const [currentPosition, setCurrentPosition] = useState({ x: 0, y: 0 });
  const [animationStep, setAnimationStep] = useState(0); // Track animation progress
  const { user, authTokens } = useContext(AuthContext);

  const fetchExperiences = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Check if user is logged in
      if (!user?.id) {
        setExperiences([]);
        setError('Please log in to view experiences');
        setLoading(false);
        return;
      }
      
      const response = await fetch(`${API_URL}/api/swipe-experiences`, {
        credentials: 'include'
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch experiences: ${response.status}`);
      }
      
      const data = await response.json();
      setExperiences(data);
      setCurrentIndex(0);
    } catch (err) {
      console.error('Error fetching experiences:', err);
      setError('Failed to load experiences. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExperiences();
  }, [user.id, authTokens]);

  const handleSwipe = async (isLike) => {
    try {
      const currentExperience = experiences[currentIndex];
      if (!currentExperience) return;

      // Set animation direction for swipe-out
      setSwipeDirection(isLike ? 'right' : 'left');
      
      // Start multi-step animation
      animateSwipe(isLike);

    } catch (err) {
      console.error('Error handling swipe:', err);
      // Ensure we still reset state on error
      setCurrentPosition({ x: 0, y: 0 });
      setSwipeDirection(null);
      setAnimationStep(0);
    }
  };
  
  const animateSwipe = (isLike) => {
    // Define the total animation steps
    const totalSteps = 16;
    // Define the max distance the card should move
    const maxDistance = isLike ? 500 : -500;
    // Define the max rotation
    const maxRotation = isLike ? 30 : -30;
    
    // Set initial animation step
    setAnimationStep(1);
    
    // Create an animation sequence
    const animationInterval = setInterval(() => {
      setAnimationStep(prevStep => {
        const nextStep = prevStep + 1;
        
        // Calculate progress ratio (0 to 1)
        const progress = nextStep / totalSteps;
        
        // Apply easing function for more natural movement
        // Using cubic-bezier like easing for smooth acceleration and deceleration
        const easedProgress = progress < 0.5 
          ? 4 * progress * progress * progress 
          : 1 - Math.pow(-2 * progress + 2, 3) / 2;
          
        // Calculate new position and rotation with easing
        const newX = maxDistance * easedProgress;
        const newRotation = maxRotation * easedProgress;
        
        // Update card position with easing
        setCurrentPosition({ 
          x: newX, 
          y: 0 
        });
        
        // If we've completed all steps, clear the interval and finish the swipe
        if (nextStep >= totalSteps) {
          clearInterval(animationInterval);
          finishSwipe(isLike);
          return 0; // Reset step counter
        }
        
        return nextStep;
      });
    }, 20); // Run every 20ms instead of 30ms for a more fluid animation (all 16 steps in ~320ms)
  };
  
  const finishSwipe = async (isLike) => {
    try {
      const currentExperience = experiences[currentIndex];
      if (!currentExperience) return;
      
      // Send swipe to backend
      const response = await fetch(`${API_URL}/api/swipes`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({
          user_id: user.id,
          experience_id: currentExperience.id,
          is_like: isLike
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to record swipe');
      }

      // Give more time for the animation to complete visually before transitioning
      setTimeout(() => {
        // Move to next experience
        setCurrentIndex(prev => prev + 1);
        
        // Reset the position and swipe direction
        setCurrentPosition({ x: 0, y: 0 });
        setSwipeDirection(null);
        
        // If we're about to run out of experiences, fetch new ones
        if (currentIndex >= experiences.length - 2) {
          fetchExperiences();
        }
      }, 450); // Increased from 150ms to 450ms to allow full visual of animation
      
    } catch (err) {
      console.error('Error in swipe handling:', err);
      // Even if there's an error, we should still move to the next card
      setTimeout(() => {
        setCurrentIndex(prev => prev + 1);
        setCurrentPosition({ x: 0, y: 0 });
        setSwipeDirection(null);
      }, 450); // Increased from 150ms to match the success case
    }
  };

  const handleRetry = () => {
    fetchExperiences();
  };

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

  if (experiences.length === 0 || currentIndex >= experiences.length) {
    return (
      <div className="py-8 bg-gradient-to-br from-orange-50 to-orange-100 min-h-[80vh]">
        <div className="bg-white rounded-xl shadow-lg p-8 max-w-md mx-auto text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-orange-100 rounded-full mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-orange-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold mb-3 text-orange-800">No more experiences</h2>
          <p className="text-gray-600 mb-6">Looks like you've seen all available experiences! Check back later or create your own.</p>
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
      {/* Match modal - Commented out but preserved for future use
      <AnimatePresence>
        {false && (
          <motion.div 
            className="fixed inset-0 flex items-center justify-center z-50 p-4 bg-black/60 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div 
              className="bg-white rounded-2xl shadow-2xl overflow-hidden max-w-md w-full"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              transition={{ type: "spring", damping: 25 }}
            >
              <div className="p-6 text-center">
                <div className="text-5xl mb-6">🎉</div>
                <h3 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-orange-start to-orange-end mb-4">It's a Match!</h3>
                
                <div className="flex justify-center items-center space-x-4 mb-6">
                  <div className="w-16 h-16 rounded-full bg-gradient-to-r from-orange-start to-orange-end flex items-center justify-center text-white text-2xl font-bold">
                    {user.username?.charAt(0).toUpperCase() || 'U'}
                  </div>
                  
                  <div className="w-8 h-8 flex items-center justify-center">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-red-500" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                    </svg>
                  </div>
                  
                  <div className="w-16 h-16 rounded-full bg-gradient-to-r from-orange-end to-orange-start flex items-center justify-center text-white text-2xl font-bold">
                    M
                  </div>
                </div>
                
                <p className="text-gray-700 mb-6">You both want to try an experience at a location!</p>
                
                <div className="grid grid-cols-2 gap-4">
                  <button 
                    className="py-3 px-4 border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50 transition-colors"
                  >
                    Keep Swiping
                  </button>
                  
                  <Link 
                    to="/matches"
                    className="py-3 px-4 bg-gradient-to-r from-orange-start to-orange-end rounded-lg text-white font-medium shadow-md hover:shadow-lg transition-all text-center"
                  >
                    View Matches
                  </Link>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
      */}
      
      <div className="max-w-md mx-auto px-4">
        {/* Swipe indicators - Like */}
        <div 
          className={`absolute top-32 right-6 transform rotate-12 bg-green-500/90 text-white py-2 px-6 rounded-lg font-bold tracking-wider z-30 text-xl border-2 border-white transition-all ${getLikeIndicatorClass()}`}
          style={{ 
            boxShadow: '0 4px 10px rgba(0, 0, 0, 0.15)',
            transformOrigin: 'center',
            zIndex: 20
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
            zIndex: 20
          }}
        >
          PASS
        </div>
        
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
            {currentExperience.location_image ? (
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
                {currentExperience.location}
              </h2>
              
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
            className="w-16 h-16 rounded-full bg-white flex items-center justify-center shadow-lg border border-gray-200 hover:border-red-400 transition-colors action-button"
            aria-label="Pass"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
          
          <button
            onClick={handleRetry}
            className="w-12 h-12 rounded-full bg-white flex items-center justify-center shadow-lg border border-gray-200 hover:border-blue-400 transition-colors action-button"
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
            className="w-16 h-16 rounded-full bg-white flex items-center justify-center shadow-lg border border-gray-200 hover:border-green-400 transition-colors action-button"
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
